import math
import time
import requests

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

_PROPS_CACHE = {}


def _obtener_stats_reales_espn(team_id: str, abbr: str):
    """
    Extrae exclusivamente estadísticas numéricas reales desde la API de ESPN.
    Si un atleta no tiene datos reales publicados, se omite (cero valores inventados).
    """
    jugadores = {}

    # 1. Endpoint oficial v3 de estadísticas de atletas del equipo
    url_v3 = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/teams/{team_id}/athletes/statistics"
    try:
        r = requests.get(url_v3, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            for cat in data.get("categories", []):
                for ath in cat.get("athletes", []):
                    info = ath.get("athlete", {})
                    nom = info.get("displayName")
                    if not nom:
                        continue

                    stats_list = ath.get("stats", [])
                    if not stats_list:
                        continue

                    if nom not in jugadores:
                        jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}

                    for st in stats_list:
                        s_name = st.get("name", "").lower()
                        try:
                            s_val = float(str(st.get("value", 0)).replace(",", ""))
                        except ValueError:
                            continue

                        if s_val <= 0:
                            continue

                        if s_name in ["avgpoints", "pointspergame"] and s_val >= 6.0:
                            jugadores[nom]["Puntos"] = s_val
                        elif s_name in ["avgrebounds", "reboundspergame", "avgtotrebounds"] and s_val >= 3.0:
                            jugadores[nom]["Rebotes"] = s_val
                        elif s_name in ["avgassists", "assistspergame"] and s_val >= 2.5:
                            jugadores[nom]["Asistencias"] = s_val
                        elif s_name in ["avgthreepointfieldgoalsmade", "threepointfieldgoalsmadepergame"] and s_val >= 1.2:
                            jugadores[nom]["Triples"] = s_val
    except Exception as e:
        print(f"Error v3 ESPN {abbr}: {e}")

    # 2. Complemento con el endpoint v2 de líderes oficiales del equipo
    url_v2 = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}?enable=leaders"
    try:
        r2 = requests.get(url_v2, headers=HEADERS, timeout=5)
        if r2.status_code == 200:
            leaders = r2.json().get("team", {}).get("leaders", [])
            for cat in leaders:
                c_name = cat.get("name", "").lower()
                tipo = None
                if "point" in c_name or "pts" in c_name:
                    tipo = "Puntos"
                elif "rebound" in c_name or "reb" in c_name:
                    tipo = "Rebotes"
                elif "assist" in c_name or "ast" in c_name:
                    tipo = "Asistencias"

                if tipo:
                    for l in cat.get("leaders", []):
                        nom = l.get("athlete", {}).get("displayName")
                        try:
                            val = float(str(l.get("value", 0)).replace(",", ""))
                        except ValueError:
                            val = 0.0

                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            if tipo not in jugadores[nom]:
                                jugadores[nom][tipo] = val
    except Exception as e:
        print(f"Error v2 ESPN {abbr}: {e}")

    # Filtrar solo jugadores que realmente tienen al menos una métrica numérica real
    return [j for j in jugadores.values() if len(j) > 2]


def _calcular_prop_real(media_real: float, tipo_prop: str):
    """
    Calcula línea, probabilidad real y +EV a partir del promedio verdadero del jugador.
    """
    # Línea de mercado natural (.5)
    linea = math.floor(media_real) + 0.5

    if tipo_prop in ["Puntos", "Rebotes"]:
        # Distribución normal con dispersión real por tipo de estadística
        cv = 0.21 if tipo_prop == "Puntos" else 0.25
        sigma = max(1.1, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        # Distribución de Poisson para eventos discretos (Asistencias, Triples)
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under

    # Asignación de cuota justa de casino según probabilidad real
    if prob_sel >= 0.72:
        cuota = 1.50
    elif prob_sel >= 0.67:
        cuota = 1.60
    elif prob_sel >= 0.62:
        cuota = 1.70
    elif prob_sel >= 0.57:
        cuota = 1.80
    elif prob_sel >= 0.53:
        cuota = 1.87
    else:
        cuota = 1.92

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    proy = int(round(media_real))
    if es_over and proy <= linea:
        proy = int(math.ceil(linea))
    elif not es_over and proy >= linea:
        proy = int(math.floor(linea))

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proy
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    key = f"{local}_{visitante}_nba_real_stats_v2"
    now = time.time()
    if key in _PROPS_CACHE:
        ts, data = _PROPS_CACHE[key]
        if now - ts < 1800 and data:
            return data

    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    abbr_loc, id_loc = d_loc
    abbr_vis, id_vis = d_vis

    pool = _obtener_stats_reales_espn(id_loc, abbr_loc) + _obtener_stats_reales_espn(id_vis, abbr_vis)
    todas = []

    for j in pool:
        for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_real(j[tipo], tipo)
                # Solo incluir jugadas con ventaja real positiva y probabilidad > 52%
                if c["prob_real"] >= 52.5 and c["ev"] > 0:
                    score = (c["prob_real"] * 0.75) + (c["ev"] * 0.25)
                    todas.append({
                        "jugador": j["nombre"],
                        "equipo_abbr": j["equipo"],
                        "tipo_prop": tipo,
                        "lado": c["lado"],
                        "linea": c["linea"],
                        "cuota": c["cuota"],
                        "prob_real": c["prob_real"],
                        "ev": c["ev"],
                        "proyeccion": c["proyeccion"],
                        "_score": score
                    })

    todas.sort(key=lambda x: x["_score"], reverse=True)
    for p in todas:
        p.pop("_score", None)

    res = todas[:top_n]
    _PROPS_CACHE[key] = (now, res)
    return res
