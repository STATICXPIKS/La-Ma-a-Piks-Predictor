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
    """Obtiene en 1 sola llamada rápida los promedios reales de los jugadores activos en el roster."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 1800):
        return _CACHE_STATS_NBA[team_id][1]

    jugadores = {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster?enable=stats"

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            atletas = r.json().get("athletes", [])
            for ath in atletas:
                # Omitir jugadores descartados por lesión (Out)
                injuries = ath.get("injuries", [])
                if any("out" in str(inj.get("status", "")).lower() for inj in injuries):
                    continue

                nom = ath.get("displayName")
                if not nom:
                    continue

                # Buscar el bloque de estadísticas de temporada regular (per game)
                stats_categories = ath.get("statistics", {}).get("splits", {}).get("categories", [])
                if not stats_categories:
                    stats_categories = ath.get("statsSummary", {}).get("statistics", [])

                datos_j = {"nombre": nom, "equipo": abbr.upper()}

                # Formato 1: splits.categories
                for cat in stats_categories:
                    for st in cat.get("stats", []):
                        s_name = str(st.get("name", "")).lower()
                        try:
                            val = float(str(st.get("value", 0)).replace(",", ""))
                        except ValueError:
                            continue
                        if val <= 0:
                            continue
                        if s_name in ["avgpoints", "pointspergame"] and val >= 8.0:
                            datos_j["Puntos"] = round(val, 1)
                        elif s_name in ["avgrebounds", "reboundspergame", "avgtotrebounds"] and val >= 4.0:
                            datos_j["Rebotes"] = round(val, 1)
                        elif s_name in ["avgassists", "assistspergame"] and val >= 3.0:
                            datos_j["Asistencias"] = round(val, 1)
                        elif s_name in ["avgthreepointfieldgoalsmade", "threepointfieldgoalsmadepergame"] and val >= 1.5:
                            datos_j["Triples"] = round(val, 1)

                # Formato 2: statsSummary directo si splits vino vacío
                if len(datos_j) == 2:
                    for st in ath.get("statsSummary", {}).get("statistics", []):
                        s_name = str(st.get("name", "")).lower()
                        try:
                            val = float(str(st.get("value", 0)).replace(",", ""))
                        except ValueError:
                            continue
                        if s_name == "avgpoints" and val >= 8.0:
                            datos_j["Puntos"] = round(val, 1)
                        elif s_name == "avgrebounds" and val >= 4.0:
                            datos_j["Rebotes"] = round(val, 1)
                        elif s_name == "avgassists" and val >= 3.0:
                            datos_j["Asistencias"] = round(val, 1)

                if len(datos_j) > 2:
                    jugadores[_normalizar_nombre(nom)] = datos_j
    except Exception as e:
        print(f"Error roster stats NBA {abbr}: {e}")

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nba(media_real: float, tipo_prop: str, linea_casino=None, cuota_over=None, cuota_under=None):
    if linea_casino is None:
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
            linea = max(1.5, math.floor(media_real) - 0.5)
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


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    stats_totales = {**_obtener_stats_reales_nba(d_loc[1], d_loc[0]), **_obtener_stats_reales_nba(d_vis[1], d_vis[0])}
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
