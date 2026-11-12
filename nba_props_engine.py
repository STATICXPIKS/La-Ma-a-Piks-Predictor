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


def _obtener_stats_equipo_espn(team_id: str, abbr: str):
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 1800):
        return _CACHE_STATS_NBA[team_id][1]

    jugadores = {}
    url_v3 = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/teams/{team_id}/athletes/statistics"
    try:
        r = requests.get(url_v3, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            for cat in r.json().get("categories", []):
                for ath in cat.get("athletes", []):
                    nom = ath.get("athlete", {}).get("displayName")
                    if not nom:
                        continue
                    key = _normalizar_nombre(nom)
                    if key not in jugadores:
                        jugadores[key] = {"nombre": nom, "equipo": abbr.upper()}
                    for st in ath.get("stats", []):
                        s_name = st.get("name", "").lower()
                        try:
                            s_val = float(str(st.get("value", 0)).replace(",", ""))
                        except ValueError:
                            continue
                        if s_val <= 0:
                            continue
                        if s_name in ["avgpoints", "pointspergame"]:
                            jugadores[key]["Puntos"] = s_val
                        elif s_name in ["avgrebounds", "reboundspergame", "avgtotrebounds"]:
                            jugadores[key]["Rebotes"] = s_val
                        elif s_name in ["avgassists", "assistspergame"]:
                            jugadores[key]["Asistencias"] = s_val
                        elif s_name in ["avgthreepointfieldgoalsmade", "threepointfieldgoalsmadepergame"]:
                            jugadores[key]["Triples"] = s_val
    except Exception:
        pass

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_contra_casino(media_real: float, linea_casino: float, cuota_over: float, cuota_under: float, tipo_prop: str):
    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.22 if tipo_prop == "Puntos" else 0.25
        sigma = max(1.2, media_real * cv)
        z = (linea_casino - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea_casino))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    ev_over = (prob_over * cuota_over) - 1.0
    ev_under = (prob_under * cuota_under) - 1.0

    # Elegir el lado con mayor certeza y EV positivo
    if prob_over >= prob_under and ev_over > 0:
        lado = "MÁS DE"
        prob_sel = prob_over
        cuota_sel = cuota_over
        ev_sel = ev_over
    elif prob_under > prob_over and ev_under > 0:
        lado = "MENOS DE"
        prob_sel = prob_under
        cuota_sel = cuota_under
        ev_sel = ev_under
    elif ev_over >= ev_under and ev_over > 0:
        lado = "MÁS DE"
        prob_sel = prob_over
        cuota_sel = cuota_over
        ev_sel = ev_over
    elif ev_under > 0:
        lado = "MENOS DE"
        prob_sel = prob_under
        cuota_sel = cuota_under
        ev_sel = ev_under
    else:
        return None

    proy = int(round(media_real))
    if lado == "MÁS DE" and proy <= linea_casino:
        proy = int(math.ceil(linea_casino))
    elif lado == "MENOS DE" and proy >= linea_casino:
        proy = int(math.floor(linea_casino))

    return {
        "lado": lado,
        "linea": linea_casino,
        "cuota": cuota_sel,
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    # 1. Extraer líneas y momios reales publicados en Kambi/Rushbet
    props_casino = obtener_player_props_kambi("nba", local, visitante)
    if not props_casino:
        return []

    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    # 2. Descargar estadísticas reales de ambos equipos desde ESPN
    stats_loc = _obtener_stats_equipo_espn(d_loc[1], d_loc[0])
    stats_vis = _obtener_stats_equipo_espn(d_vis[1], d_vis[0])
    stats_totales = {**stats_loc, **stats_vis}

    candidatas = []
    for p in props_casino:
        key_jug = _normalizar_nombre(p["jugador"])
        datos_atleta = stats_totales.get(key_jug)
        if not datos_atleta:
            continue

        tipo = p["tipo_prop"]
        media_real = datos_atleta.get(tipo)
        if not media_real or media_real <= 0:
            continue

        eval_res = _evaluar_prop_contra_casino(
            media_real, p["linea"], p["cuota_over"], p["cuota_under"], tipo
        )
        if eval_res and eval_res["prob_real"] >= 54.0 and eval_res["ev"] >= 1.5:
            score = (eval_res["prob_real"] * 0.75) + (eval_res["ev"] * 0.25)
            candidatas.append({
                "jugador": datos_atleta["nombre"],
                "equipo_abbr": datos_atleta["equipo"],
                "tipo_prop": tipo,
                "lado": eval_res["lado"],
                "linea": eval_res["linea"],
                "cuota": eval_res["cuota"],
                "prob_real": eval_res["prob_real"],
                "ev": eval_res["ev"],
                "proyeccion": eval_res["proyeccion"],
                "_score": score
            })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
