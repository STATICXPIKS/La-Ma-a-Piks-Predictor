import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

EQUIPOS_NBA_ESPN = {
    "Atlanta Hawks": ("atl", "1"), "Boston Celtics": ("bos", "2"), "Brooklyn Nets": ("bkn", "17"),
    "Charlotte Hornets": ("cha", "30"), "Chicago Bulls": ("chi", "4"), "Cleveland Cavaliers": ("cle", "5"),
    "Dallas Mavericks": ("dal", "6"), "Denver Nuggets": ("den", "7"), "Detroit Pistons": ("det", "8"),
    "Golden State Warriors": ("gsw", "9"), "Houston Rockets": ("hou", "10"), "Indiana Pacers": ("ind", "11"),
    "LA Clippers": ("lac", "12"), "Los Angeles Clippers": ("lac", "12"), "Los Angeles Lakers": ("lal", "13"),
    "Memphis Grizzlies": ("mem", "29"), "Miami Heat": ("mia", "14"), "Milwaukee Bucks": ("mil", "15"),
    "Minnesota Timberwolves": ("min", "16"), "New Orleans Pelicans": ("nop", "3"), "New York Knicks": ("nyk", "18"),
    "Oklahoma City Thunder": ("okc", "25"), "Orlando Magic": ("orl", "19"), "Philadelphia 76ers": ("phi", "20"),
    "Phoenix Suns": ("phx", "21"), "Portland Trail Blazers": ("por", "22"), "Sacramento Kings": ("sac", "23"),
    "San Antonio Spurs": ("sas", "24"), "Toronto Raptors": ("tor", "28"), "Utah Jazz": ("uta", "26"),
    "Washington Wizards": ("was", "27")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_CACHE_STATS_NBA = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_promedios_reales_nba(team_id: str, abbr: str):
    """Extrae promedios reales de los últimos partidos jugados desde los boxscores oficiales de ESPN."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 1800):
        return _CACHE_STATS_NBA[team_id][1]

    acumulado = {}
    url_sched = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"

    try:
        r = requests.get(url_sched, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            eventos = r.json().get("events", [])
            finalizados = [
                ev.get("id") for ev in eventos
                if ev.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("completed") is True
            ]
            # Analiza los últimos 5 juegos reales disputados
            for ev_id in finalizados[-5:]:
                url_box = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={ev_id}"
                rb = requests.get(url_box, headers=HEADERS, timeout=5)
                if rb.status_code != 200:
                    continue

                for team_box in rb.json().get("boxscore", {}).get("players", []):
                    if str(team_box.get("team", {}).get("id")) != str(team_id):
                        continue

                    stats_block = team_box.get("statistics", [{}])[0]
                    headers_cols = [h.upper() for h in stats_block.get("names", [])]
                    if "PTS" not in headers_cols:
                        continue

                    idx_pts = headers_cols.index("PTS")
                    idx_reb = headers_cols.index("REB") if "REB" in headers_cols else -1
                    idx_ast = headers_cols.index("AST") if "AST" in headers_cols else -1
                    idx_3pt = headers_cols.index("3PT") if "3PT" in headers_cols else -1

                    for ath in stats_block.get("athletes", []):
                        if ath.get("didNotPlay"):
                            continue
                        nom = ath.get("athlete", {}).get("displayName")
                        vals = ath.get("stats", [])
                        if not nom or len(vals) <= idx_pts:
                            continue

                        try:
                            pts = float(vals[idx_pts])
                            reb = float(vals[idx_reb]) if idx_reb >= 0 else 0.0
                            ast = float(vals[idx_ast]) if idx_ast >= 0 else 0.0
                            triples = float(str(vals[idx_3pt]).split("-")[0]) if idx_3pt >= 0 and "-" in str(vals[idx_3pt]) else 0.0
                        except ValueError:
                            continue

                        key = _normalizar_nombre(nom)
                        if key not in acumulado:
                            acumulado[key] = {"nombre": nom, "equipo": abbr.upper(), "pj": 0, "pts": 0.0, "reb": 0.0, "ast": 0.0, "3pm": 0.0}

                        acumulado[key]["pj"] += 1
                        acumulado[key]["pts"] += pts
                        acumulado[key]["reb"] += reb
                        acumulado[key]["ast"] += ast
                        acumulado[key]["3pm"] += triples
    except Exception as e:
        print(f"Error boxscores NBA {abbr}: {e}")

    jugadores = {}
    for k, v in acumulado.items():
        if v["pj"] >= 2:
            jugadores[k] = {
                "nombre": v["nombre"],
                "equipo": v["equipo"],
                "Puntos": round(v["pts"] / v["pj"], 1),
                "Rebotes": round(v["reb"] / v["pj"], 1),
                "Asistencias": round(v["ast"] / v["pj"], 1),
                "Triples": round(v["3pm"] / v["pj"], 1)
            }

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nba(media_real: float, tipo_prop: str, linea_casino=None, cuota_over=None, cuota_under=None):
    if linea_casino is None:
        # Línea conservadora segura para buscar probabilidades altas
        if tipo_prop == "Puntos":
            if media_real < 10.0: return None
            linea = math.floor(media_real * 0.88) + 0.5
        elif tipo_prop == "Rebotes":
            if media_real < 4.5: return None
            linea = math.floor(media_real * 0.85) + 0.5
        elif tipo_prop == "Asistencias":
            if media_real < 3.5: return None
            linea = math.floor(media_real * 0.85) + 0.5
        else:
            if media_real < 1.8: return None
            linea = math.floor(media_real) - 0.5
    else:
        linea = linea_casino

    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.21 if tipo_prop == "Puntos" else 0.25
        sigma = max(1.1, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
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


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    stats_totales = {**_obtener_promedios_reales_nba(d_loc[1], d_loc[0]), **_obtener_promedios_reales_nba(d_vis[1], d_vis[0])}
    if not stats_totales:
        return []

    candidatas = []
    props_casino = obtener_player_props_kambi("nba", local, visitante)

    if props_casino:
        for p in props_casino:
            datos_atleta = stats_totales.get(_normalizar_nombre(p["jugador"]))
            if not datos_atleta:
                continue
            tipo = p["tipo_prop"]
            media_real = datos_atleta.get(tipo)
            if not media_real or media_real <= 0:
                continue

            res = _evaluar_prop_nba(media_real, tipo, p["linea"], p["cuota_over"], p["cuota_under"])
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
            for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
                media_real = datos_atleta.get(tipo)
                if not media_real or media_real <= 0:
                    continue
                res = _evaluar_prop_nba(media_real, tipo)
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
