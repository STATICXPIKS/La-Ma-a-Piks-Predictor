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


def _obtener_stats_reales_nba(team_id: str, abbr: str):
    """Extrae promedios reales por partido y roster activo de ESPN."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 1800):
        return _CACHE_STATS_NBA[team_id][1]

    jugadores = {}

    # 1. Cargar roster activo para identificar a qué equipo pertenece cada jugador
    url_roster = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
    try:
        r_ros = requests.get(url_roster, headers=HEADERS, timeout=5)
        if r_ros.status_code == 200:
            for ath in r_ros.json().get("athletes", []):
                nom = ath.get("displayName")
                if nom:
                    jugadores[_normalizar_nombre(nom)] = {"nombre": nom, "equipo": abbr.upper()}
    except Exception:
        pass

    # 2. Cargar promedios reales por partido desde líderes de equipo
    url_leaders = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/leaders"
    try:
        r = requests.get(url_leaders, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            for cat in r.json().get("leaders", []):
                c_name = str(cat.get("name", "")).lower()
                tipo = None
                if "pointspergame" in c_name or c_name == "points":
                    tipo = "Puntos"
                elif "reboundspergame" in c_name or c_name == "rebounds":
                    tipo = "Rebotes"
                elif "assistspergame" in c_name or c_name == "assists":
                    tipo = "Asistencias"
                elif "3point" in c_name or "threepoint" in c_name:
                    tipo = "Triples"

                if not tipo:
                    continue

                for lead in cat.get("leaders", []):
                    ath = lead.get("athlete", {})
                    nom = ath.get("displayName")
                    try:
                        val = float(str(lead.get("value", 0)).replace(",", ""))
                    except ValueError:
                        continue

                    if nom and val > 0:
                        key = _normalizar_nombre(nom)
                        if key not in jugadores:
                            jugadores[key] = {"nombre": nom, "equipo": abbr.upper()}
                        jugadores[key][tipo] = round(val, 1)
    except Exception as e:
        print(f"Error stats NBA {abbr}: {e}")

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nba(p_casino: dict, stats_totales: dict):
    jugador_raw = p_casino["jugador"]
    tipo = p_casino["tipo_prop"]
    linea = float(p_casino["linea"])
    c_over = float(p_casino["cuota_over"])
    c_under = float(p_casino.get("cuota_under") or 1.90)

    datos_atleta = stats_totales.get(_normalizar_nombre(jugador_raw))
    # Exigir que el jugador pertenezca activamente al roster de uno de los dos equipos
    if not datos_atleta:
        return None

    equipo_abbr = datos_atleta["equipo"]
    nombre_final = datos_atleta["nombre"]

    imp_over = 1.0 / c_over
    imp_under = 1.0 / c_under
    suma_imp = imp_over + imp_under
    prob_mkt_over = imp_over / suma_imp
    prob_mkt_under = imp_under / suma_imp

    media_real = datos_atleta.get(tipo, 0)
    if media_real > 0:
        if tipo in ["Puntos", "Rebotes"]:
            cv = 0.22 if tipo == "Puntos" else 0.26
            sigma = max(1.1, media_real * cv)
            z = (linea - media_real) / sigma
            p_stat_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
            p_stat_over = 1.0 - p_stat_under
        else:
            lamb = media_real
            k_max = int(math.floor(linea))
            p_stat_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
            p_stat_over = 1.0 - p_stat_under

        prob_over = (p_stat_over * 0.65) + (prob_mkt_over * 0.35)
        prob_under = (p_stat_under * 0.65) + (prob_mkt_under * 0.35)
        proy_num = media_real
    else:
        # Jugador activo del roster sin liderato Top-3 en ESPN: evaluar con probabilidad No-Vig + ventaja de cuota
        prob_over = prob_mkt_over * 1.04 if c_over >= 1.85 else prob_mkt_over
        prob_under = prob_mkt_under * 1.04 if c_under >= 1.85 else prob_mkt_under
        proy_num = linea + (1.0 if prob_over >= prob_under else -1.0)

    ev_over = (prob_over * c_over) - 1.0
    ev_under = (prob_under * c_under) - 1.0

    if ev_over >= ev_under and ev_over > 0.005 and prob_over >= 0.52:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    elif ev_under > 0.005 and prob_under >= 0.52:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under
    else:
        return None

    proy = int(round(proy_num))
    if lado == "MÁS DE" and proy <= linea:
        proy = int(math.ceil(linea))
    elif lado == "MENOS DE" and proy >= linea:
        proy = int(math.floor(linea))

    return {
        "jugador": nombre_final,
        "equipo_abbr": equipo_abbr,
        "tipo_prop": tipo,
        "lado": lado,
        "linea": linea,
        "cuota": cuota_sel,
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy,
        "_score": (prob_sel * 100 * 0.65) + (ev_sel * 100 * 0.35)
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    props_casino = obtener_player_props_kambi("nba", local, visitante)
    if not props_casino:
        return []

    stats_totales = {**_obtener_stats_reales_nba(d_loc[1], d_loc[0]), **_obtener_stats_reales_nba(d_vis[1], d_vis[0])}
    if not stats_totales:
        return []

    candidatas = []
    for p in props_casino:
        res = _evaluar_prop_nba(p, stats_totales)
        if res:
            candidatas.append(res)

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
