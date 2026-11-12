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


def _obtener_stats_reales_nfl(team_id: str, abbr: str):
    """Obtiene en 1 sola llamada rápida los promedios reales de yardas y recepciones del roster activo."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NFL and (ahora - _CACHE_STATS_NFL[team_id][0] < 1800):
        return _CACHE_STATS_NFL[team_id][1]

    jugadores = {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster?enable=stats"

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            # En NFL el roster viene agrupado por offense, defense, specialTeam
            grupos = r.json().get("athletes", [])
            lista_atletas = []
            for g in grupos:
                if "items" in g:
                    lista_atletas.extend(g["items"])
                else:
                    lista_atletas.append(g)

            for ath in lista_atletas:
                injuries = ath.get("injuries", [])
                if any("out" in str(inj.get("status", "")).lower() for inj in injuries):
                    continue

                nom = ath.get("displayName")
                if not nom:
                    continue

                datos_j = {"nombre": nom, "equipo": abbr.upper()}
                cats = ath.get("statistics", {}).get("splits", {}).get("categories", [])

                for cat in cats:
                    for st in cat.get("stats", []):
                        s_name = str(st.get("name", "")).lower()
                        try:
                            val = float(str(st.get("value", 0)).replace(",", ""))
                        except ValueError:
                            continue
                        if val <= 0:
                            continue
                        if ("passingyardspergame" in s_name or "avgpassingyards" in s_name) and val >= 120.0:
                            datos_j["Yardas Pase"] = round(val, 1)
                        elif ("rushingyardspergame" in s_name or "avgrushingyards" in s_name) and val >= 25.0:
                            datos_j["Yardas Acarreo"] = round(val, 1)
                        elif ("receivingyardspergame" in s_name or "avgreceivingyards" in s_name) and val >= 25.0:
                            datos_j["Yardas Recepción"] = round(val, 1)
                        elif ("receptionspergame" in s_name or "avgreceptions" in s_name) and val >= 2.5:
                            datos_j["Recepciones"] = round(val, 1)

                if len(datos_j) > 2:
                    jugadores[_normalizar_nombre(nom)] = datos_j
    except Exception as e:
        print(f"Error roster stats NFL {abbr}: {e}")

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
        if prob_sel < 0.57:
            return None
        lado = "MÁS DE" if es_over else "MENOS DE"
        cuota_sel = round(max(1.32, (1.0 / prob_sel) * 1.04), 2)
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

    stats_totales = {**_obtener_stats_reales_nfl(d_loc[1], d_loc[0]), **_obtener_stats_reales_nfl(d_vis[1], d_vis[0])}
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
