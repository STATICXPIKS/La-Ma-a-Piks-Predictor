import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

EQUIPOS_NFL_ESPN = {
    "Arizona Cardinals": ("ari", "22"), "Atlanta Falcons": ("atl", "1"), "Baltimore Ravens": ("bal", "33"),
    "Buffalo Bills": ("buf", "2"), "Carolina Panthers": ("car", "29"), "Chicago Bears": ("chi", "3"),
    "Cincinnati Bengals": ("cin", "4"), "Cleveland Browns": ("cle", "5"), "Dallas Cowboys": ("dal", "6"),
    "Denver Broncos": ("den", "7"), "Detroit Lions": ("det", "8"), "Green Bay Packers": ("gb", "9"),
    "Houston Texans": ("hou", "34"), "Indianapolis Colts": ("ind", "11"), "Jacksonville Jaguars": ("jax", "30"),
    "Kansas City Chiefs": ("kc", "12"), "Las Vegas Raiders": ("lv", "13"), "Los Angeles Chargers": ("lac", "24"),
    "Los Angeles Rams": ("lar", "14"), "Miami Dolphins": ("mia", "15"), "Minnesota Vikings": ("min", "16"),
    "New England Patriots": ("ne", "17"), "New Orleans Saints": ("no", "18"), "New York Giants": ("nyg", "19"),
    "New York Jets": ("nyj", "20"), "Philadelphia Eagles": ("phi", "21"), "Pittsburgh Steelers": ("pit", "23"),
    "San Francisco 49ers": ("sf", "25"), "Seattle Seahawks": ("sea", "26"), "Tampa Bay Buccaneers": ("tb", "27"),
    "Tennessee Titans": ("ten", "10"), "Washington Commanders": ("was", "28")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_CACHE_STATS_NFL = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_promedios_reales_nfl(team_id: str, abbr: str):
    """Extrae promedios reales de yardas y recepciones desde los últimos partidos jugados en ESPN."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NFL and (ahora - _CACHE_STATS_NFL[team_id][0] < 1800):
        return _CACHE_STATS_NFL[team_id][1]

    acumulado = {}
    url_sched = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"

    try:
        r = requests.get(url_sched, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            eventos = r.json().get("events", [])
            finalizados = [
                ev.get("id") for ev in eventos
                if ev.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("completed") is True
            ]
            for ev_id in finalizados[-4:]:
                url_box = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={ev_id}"
                rb = requests.get(url_box, headers=HEADERS, timeout=5)
                if rb.status_code != 200:
                    continue

                for team_box in rb.json().get("boxscore", {}).get("players", []):
                    if str(team_box.get("team", {}).get("id")) != str(team_id):
                        continue

                    for cat in team_box.get("statistics", []):
                        cat_name = cat.get("name", "").lower()
                        cols = [h.upper() for h in cat.get("names", [])]
                        if "YDS" not in cols:
                            continue
                        idx_yds = cols.index("YDS")
                        idx_rec = cols.index("REC") if "REC" in cols else -1

                        for ath in cat.get("athletes", []):
                            nom = ath.get("athlete", {}).get("displayName")
                            vals = ath.get("stats", [])
                            if not nom or len(vals) <= idx_yds:
                                continue
                            try:
                                yds = float(vals[idx_yds])
                                rec = float(vals[idx_rec]) if idx_rec >= 0 else 0.0
                            except ValueError:
                                continue

                            key = _normalizar_nombre(nom)
                            if key not in acumulado:
                                acumulado[key] = {"nombre": nom, "equipo": abbr.upper(), "pass_g": 0, "pass_y": 0.0, "rush_g": 0, "rush_y": 0.0, "rec_g": 0, "rec_y": 0.0, "recs": 0.0}

                            if cat_name == "passing":
                                acumulado[key]["pass_g"] += 1
                                acumulado[key]["pass_y"] += yds
                            elif cat_name == "rushing":
                                acumulado[key]["rush_g"] += 1
                                acumulado[key]["rush_y"] += yds
                            elif cat_name == "receiving":
                                acumulado[key]["rec_g"] += 1
                                acumulado[key]["rec_y"] += yds
                                acumulado[key]["recs"] += rec
    except Exception as e:
        print(f"Error boxscores NFL {abbr}: {e}")

    jugadores = {}
    for k, v in acumulado.items():
        d = {"nombre": v["nombre"], "equipo": v["equipo"]}
        if v["pass_g"] >= 2 and (v["pass_y"] / v["pass_g"]) >= 120:
            d["Yardas Pase"] = round(v["pass_y"] / v["pass_g"], 1)
        if v["rush_g"] >= 2 and (v["rush_y"] / v["rush_g"]) >= 25:
            d["Yardas Acarreo"] = round(v["rush_y"] / v["rush_g"], 1)
        if v["rec_g"] >= 2 and (v["rec_y"] / v["rec_g"]) >= 25:
            d["Yardas Recepción"] = round(v["rec_y"] / v["rec_g"], 1)
            d["Recepciones"] = round(v["recs"] / v["rec_g"], 1)
        if len(d) > 2:
            jugadores[k] = d

    if jugadores:
        _CACHE_STATS_NFL[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nfl(media_real: float, tipo_prop: str, linea_casino=None, cuota_over=None, cuota_under=None):
    if linea_casino is None:
        if tipo_prop == "Recepciones":
            if media_real < 3.0: return None
            linea = math.floor(media_real) - 0.5
        else:
            linea = math.floor(media_real * 0.86) + 0.5
    else:
        linea = linea_casino

    sigma = max(2.5, media_real * 0.27)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    if cuota_over and cuota_under:
        ev_over = (prob_over * cuota_over) - 1.0
        ev_under = (prob_under * cuota_under) - 1.0
        if prob_over >= prob_under and ev_over > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, cuota_over, ev_over
        elif prob_under > prob_over and ev_under > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, cuota_under, ev_under
        elif ev_over >= ev_under and ev_over > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, cuota_over, ev_over
        elif ev_under > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, cuota_under, ev_under
        else:
            return None
    else:
        es_over = prob_over >= prob_under
        prob_sel = min(0.82, prob_over if es_over else prob_under)
        if prob_sel < 0.58:
            return None
        lado = "MÁS DE" if es_over else "MENOS DE"
        cuota_sel = round(max(1.30, (1.0 / prob_sel) * 1.04), 2)
        ev_sel = (prob_sel * cuota_sel) - 1.0

    proy = int(round(media_real))
    if lado == "MÁS DE" and proy <= linea:
        proy = int(math.ceil(linea))
    elif lado == "MENOS DE" and proy >= linea:
        proy = int(math.floor(linea))

    return {
        "lado": lado,
        "linea": linea,
        "cuota": cuota_sel,
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy
    }


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NFL_ESPN.get(local)
    d_vis = EQUIPOS_NFL_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    stats_totales = {**_obtener_promedios_reales_nfl(d_loc[1], d_loc[0]), **_obtener_promedios_reales_nfl(d_vis[1], d_vis[0])}
    if not stats_totales:
        return []

    candidatas = []
    props_casino = obtener_player_props_kambi("nfl", local, visitante)

    if props_casino:
        for p in props_casino:
            datos_atleta = stats_totales.get(_normalizar_nombre(p["jugador"]))
            if not datos_atleta:
                continue
            tipo = p["tipo_prop"]
            media_real = datos_atleta.get(tipo)
            if not media_real or media_real <= 0:
                continue

            res = _evaluar_prop_nfl(media_real, tipo, p["linea"], p["cuota_over"], p["cuota_under"])
            if res and res["prob_real"] >= 55.0 and res["ev"] > 0:
                score = (res["prob_real"] * 0.80) + (res["ev"] * 0.20)
                candidatas.append({
                    "jugador": datos_atleta["nombre"],
                    "equipo_abbr": datos_atleta["equipo"],
                    "tipo_prop": tipo,
                    "lado": res["lado"],
                    "linea": res["linea"],
                    "cuota": res["cuota"],
                    "prob_real": res["prob_real"],
                    "ev": res["ev"],
                    "proyeccion": res["proyeccion"],
                    "_score": score
                })

    if not candidatas:
        for datos_atleta in stats_totales.values():
            for tipo in ["Yardas Pase", "Yardas Acarreo", "Yardas Recepción", "Recepciones"]:
                media_real = datos_atleta.get(tipo)
                if not media_real or media_real <= 0:
                    continue
                res = _evaluar_prop_nfl(media_real, tipo)
                if res:
                    score = (res["prob_real"] * 0.80) + (res["ev"] * 0.20)
                    candidatas.append({
                        "jugador": datos_atleta["nombre"],
                        "equipo_abbr": datos_atleta["equipo"],
                        "tipo_prop": tipo,
                        "lado": res["lado"],
                        "linea": res["linea"],
                        "cuota": res["cuota"],
                        "prob_real": res["prob_real"],
                        "ev": res["ev"],
                        "proyeccion": res["proyeccion"],
                        "_score": score
                    })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
