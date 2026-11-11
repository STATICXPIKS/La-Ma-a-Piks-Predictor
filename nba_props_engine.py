import math
import time
import requests

# Mapeo oficial de ID numérico y abreviatura de ESPN para los 30 equipos
EQUIPOS_ESPN_NBA = {
    "Atlanta Hawks": ("atl", "1"),
    "Boston Celtics": ("bos", "2"),
    "Brooklyn Nets": ("bkn", "17"),
    "Charlotte Hornets": ("cha", "30"),
    "Chicago Bulls": ("chi", "4"),
    "Cleveland Cavaliers": ("cle", "5"),
    "Dallas Mavericks": ("dal", "6"),
    "Denver Nuggets": ("den", "7"),
    "Detroit Pistons": ("det", "8"),
    "Golden State Warriors": ("gsw", "9"),
    "Houston Rockets": ("hou", "10"),
    "Indiana Pacers": ("ind", "11"),
    "LA Clippers": ("lac", "12"),
    "Los Angeles Clippers": ("lac", "12"),
    "Los Angeles Lakers": ("lal", "13"),
    "Memphis Grizzlies": ("mem", "29"),
    "Miami Heat": ("mia", "14"),
    "Milwaukee Bucks": ("mil", "15"),
    "Minnesota Timberwolves": ("min", "16"),
    "New Orleans Pelicans": ("nop", "3"),
    "New York Knicks": ("nyk", "18"),
    "Oklahoma City Thunder": ("okc", "25"),
    "Orlando Magic": ("orl", "19"),
    "Philadelphia 76ers": ("phi", "20"),
    "Phoenix Suns": ("phx", "21"),
    "Portland Trail Blazers": ("por", "22"),
    "Sacramento Kings": ("sac", "23"),
    "San Antonio Spurs": ("sas", "24"),
    "Toronto Raptors": ("tor", "28"),
    "Utah Jazz": "uta", "26",
    "Washington Wizards": ("was", "27")
}

HEADERS_ESPN = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE = {}
_STATS_TEAM_CACHE = {}


def _obtener_lideres_reales_equipo_espn(team_id: str, abbr: str):
    """
    Descarga en 1 sola llamada la tabla oficial de promedios de toda la plantilla viva.
    Cero nombres fijos: lee directamente lo que ESPN reporte hoy.
    """
    now = time.time()
    if team_id in _STATS_TEAM_CACHE:
        ts, data = _STATS_TEAM_CACHE[team_id]
        if now - ts < 1800 and data:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    jugadores_dict = {}

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=5)
        if r.status_code == 200:
            res = r.json()
            cats = res.get("results", {}).get("stats", {}).get("categories", [])
            
            # Mapeo de métricas clave por partido
            metricas_clave = {
                "avgPoints": "Puntos",
                "avgRebounds": "Rebotes",
                "avgAssists": "Asistencias",
                "avgThreePointFieldGoalsMade": "Triples"
            }

            for cat in cats:
                cat_name = cat.get("name", "")
                if cat_name in metricas_clave:
                    tipo_nombre = metricas_clave[cat_name]
                    for atleta in cat.get("leaders", []):
                        nombre = atleta.get("athlete", {}).get("displayName", "")
                        val = float(atleta.get("displayValue", "0").replace(",", ""))
                        if nombre and val > 0:
                            if nombre not in jugadores_dict:
                                jugadores_dict[nombre] = {
                                    "nombre": nombre,
                                    "equipo": abbr.upper()
                                }
                            jugadores_dict[nombre][tipo_nombre] = val
    except Exception as e:
        print(f"Error consultando estadísticas vivas de {abbr} en ESPN: {e}")

    resultado = list(jugadores_dict.values())
    _STATS_TEAM_CACHE[team_id] = (now, resultado)
    return resultado


def _calcular_prop_cuantitativa(media_real: float, tipo_prop: str):
    linea = math.floor(media_real) + 0.5

    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.22 if tipo_prop == "Puntos" else 0.26
        sigma = max(1.2, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under
    prob_sel = max(0.50, min(0.74, prob_sel))

    if prob_sel >= 0.68:
        cuota = 1.65
    elif prob_sel >= 0.64:
        cuota = 1.72
    elif prob_sel >= 0.60:
        cuota = 1.80
    else:
        cuota = 1.88

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    # Proyección entera discreta sin fracciones
    proyeccion_final = int(round(media_real))
    if es_over and proyeccion_final <= linea:
        proyeccion_final = int(math.ceil(linea))
    elif not es_over and proyeccion_final >= linea:
        proyeccion_final = int(math.floor(linea))

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proyeccion_final
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_live_espn_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < 900 and data_cached:
            return data_cached

    datos_loc = EQUIPOS_ESPN_NBA.get(local, ("ind", "11"))
    datos_vis = EQUIPOS_ESPN_NBA.get(visitante, ("was", "27"))

    abbr_loc, id_loc = (datos_loc[0], str(datos_loc[1])) if isinstance(datos_loc, tuple) else ("ind", "11")
    abbr_vis, id_vis = (datos_vis[0], str(datos_vis[1])) if isinstance(datos_vis, tuple) else ("was", "27")

    # Extrae en tiempo real de ESPN
    jugadores_loc = _obtener_lideres_reales_equipo_espn(id_loc, abbr_loc)
    jugadores_vis = _obtener_lideres_reales_equipo_espn(id_vis, abbr_vis)

    jugadores_pool = jugadores_loc + jugadores_vis

    candidatas = []
    for j in jugadores_pool:
        for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_cuantitativa(media, tipo)
                if c["prob_real"] >= 58.0 and c["ev"] >= 2.5:
                    score = round((c["prob_real"] * 0.70) + (c["ev"] * 0.30), 2)
                    candidatas.append({
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

    candidatas.sort(key=lambda x: x["_score"], reverse=True)

    for item in candidatas:
        item.pop("_score", None)

    seleccion = candidatas[:top_n]
    _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
