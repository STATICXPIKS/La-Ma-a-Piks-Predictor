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
    """Consulta el endpoint de líderes de equipo y estadísticas de jugadores de ESPN."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 1800):
        return _CACHE_STATS_NBA[team_id][1]

    jugadores = {}

    # 1. Endpoint de estadísticas del equipo (líderes reales por categoría)
    url_stats = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    try:
        r = requests.get(url_stats, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            cats = data.get("results", {}).get("stats", {}).get("categories", [])
            if not cats:
                cats = data.get("stats", {}).get("categories", [])
            mapeo = {
                "avgPoints": "Puntos",
                "avgRebounds": "Rebotes",
                "avgAssists": "Asistencias",
                "avgThreePointFieldGoalsMade": "Triples"
            }
            for c in cats:
                tipo = mapeo.get(c.get("name"))
                if tipo:
                    for lead in c.get("leaders", []):
                        nom = lead.get("athlete", {}).get("displayName")
                        val_raw = lead.get("displayValue") or lead.get("value", 0)
                        try:
                            val = float(str(val_raw).replace(",", ""))
                        except ValueError:
                            val = 0.0
                        if nom and val > 0:
                            key = _normalizar_nombre(nom)
                            if key not in jugadores:
                                jugadores[key] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[key][tipo] = val
    except Exception as e:
        print(f"Error ESPN stats NBA {abbr}: {e}")

    # 2. Endpoint alternativo v3 de estadísticas de plantilla si el primero vino vacío
    if not jugadores:
        url_v3 = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/teams/{team_id}/athletes/statistics"
        try:
            r3 = requests.get(url_v3, headers=HEADERS, timeout=6)
            if r3.status_code == 200:
                for cat in r3.json().get("categories", []):
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
                            if "avgpoints" in s_name and s_val >= 6.0:
                                jugadores[key]["Puntos"] = s_val
                            elif "avgrebounds" in s_name and s_val >= 3.0:
                                jugadores[key]["Rebotes"] = s_val
                            elif "avgassists" in s_name and s_val >= 2.5:
                                jugadores[key]["Asistencias"] = s_val
                            elif "avgthreepointfieldgoalsmade" in s_name and s_val >= 1.2:
                                jugadores[key]["Triples"] = s_val
        except Exception:
            pass

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nba(media_real: float, tipo_prop: str, linea_casino=None, cuota_over=None, cuota_under=None):
    linea = linea_casino if linea_casino is not None else (math.floor(media_real) + 0.5)

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
        prob_sel = max(0.52, min(0.76, prob_over if es_over else prob_under))
        lado = "MÁS DE" if es_over else "MENOS DE"
        cuota_justa = 1.0 / prob_sel
        cuota_sel = round(max(1.45, min(1.95, cuota_justa * 1.04)), 2)
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

    stats_loc = _obtener_stats_equipo_espn(d_loc[1], d_loc[0])
    stats_vis = _obtener_stats_equipo_espn(d_vis[1], d_vis[0])
    stats_totales = {**stats_loc, **stats_vis}
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
            if res and res["prob_real"] >= 53.0 and res["ev"] > 0:
                score = (res["prob_real"] * 0.75) + (res["ev"] * 0.25)
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
                if res and res["prob_real"] >= 53.0 and res["ev"] > 0:
                    score = (res["prob_real"] * 0.75) + (res["ev"] * 0.25)
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
