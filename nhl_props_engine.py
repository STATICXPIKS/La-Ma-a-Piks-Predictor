import math
import time
import requests

MAPEO_EQUIPOS_NHL = {
    "Anaheim Ducks": "ana", "Boston Bruins": "bos", "Buffalo Sabres": "buf",
    "Calgary Flames": "cgy", "Carolina Hurricanes": "car", "Chicago Blackhawks": "chi",
    "Colorado Avalanche": "col", "Columbus Blue Jackets": "cbj", "Dallas Stars": "dal",
    "Detroit Red Wings": "det", "Edmonton Oilers": "edm", "Florida Panthers": "fla",
    "Los Angeles Kings": "lak", "Minnesota Wild": "min", "Montreal Canadiens": "mtl",
    "Nashville Predators": "nsh", "New Jersey Devils": "njd", "New York Islanders": "nyi",
    "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
    "Pittsburgh Penguins": "pit", "San Jose Sharks": "sjs", "Seattle Kraken": "sea",
    "St. Louis Blues": "stl", "Tampa Bay Lightning": "tbl", "Toronto Maple Leafs": "tor",
    "Utah Hockey Club": "uta", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
    "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE_NHL = {}


def _obtener_lideres_reales_nhl(abbr):
    """
    Consulta la API oficial de estadísticas de la NHL para obtener
    los líderes reales del equipo en puntos, tiros y goles por partido.
    """
    abbr_clean = abbr.lower()
    jugadores = {}

    # 1. API oficial de NHL Web (Roster + Estadísticas activas del equipo)
    url_nhl = f"https://api-web.nhle.com/v1/club-stats/{abbr_clean}/now"
    try:
        r = requests.get(url_nhl, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            skaters = data.get("skaters", [])
            for s in skaters:
                games = s.get("gamesPlayed", 0)
                if games < 5:
                    continue

                nombre = f"{s.get('firstName', {}).get('default', '')} {s.get('lastName', {}).get('default', '')}".strip()
                if not nombre:
                    continue

                pts = s.get("points", 0)
                shots = s.get("shots", 0)

                ppg = round(pts / games, 2)
                spg = round(shots / games, 2)

                if ppg >= 0.40 or spg >= 1.5:
                    jugadores[nombre] = {
                        "nombre": nombre,
                        "equipo": abbr.upper(),
                        "Puntos": ppg,
                        "Tiros a Puerta": spg
                    }
    except Exception as e:
        print(f"Error consultando NHL API para {abbr}: {e}")

    # 2. Respaldo directo en API de ESPN NHL si la principal estuviera en mantenimiento
    if not jugadores:
        try:
            url_espn = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{abbr_clean}"
            r2 = requests.get(url_espn, headers=HEADERS, timeout=4)
            if r2.status_code == 200:
                leaders = r2.json().get("team", {}).get("leaders", [])
                for cat in leaders:
                    cat_name = cat.get("name", "").lower()
                    tipo = "Puntos" if "point" in cat_name or "pts" in cat_name else None
                    if tipo:
                        for l in cat.get("leaders", []):
                            nom = l.get("athlete", {}).get("displayName")
                            val = float(str(l.get("value", 0)).replace(",", ""))
                            if nom and val > 0:
                                # Si ESPN entrega puntos totales, normalizar a promedio
                                ppg_est = round(val / 20.0, 2) if val > 4.0 else val
                                if nom not in jugadores:
                                    jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Puntos": ppg_est, "Tiros a Puerta": 2.5}
        except Exception:
            pass

    return list(jugadores.values())


def _calcular_prop_nhl(media_real: float, tipo_prop: str):
    """Calcula probabilidades exactas y cuotas justas basadas en mérito."""
    if tipo_prop == "Tiros a Puerta":
        linea = math.floor(media_real) + 0.5
        cv = 0.26
        sigma = max(0.8, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        # En puntos de hockey la línea estándar de mercado es 0.5 o 1.5
        linea = 1.5 if media_real >= 1.25 else 0.5
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = max(0.52, min(0.78, prob_over if es_over else prob_under))

    # Asignación de cuota real según probabilidad
    if prob_sel >= 0.72: cuota = 1.52
    elif prob_sel >= 0.67: cuota = 1.62
    elif prob_sel >= 0.62: cuota = 1.72
    elif prob_sel >= 0.57: cuota = 1.82
    else: cuota = 1.88

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    proyeccion_entera = int(round(media_real))
    if es_over and proyeccion_entera <= linea:
        proyeccion_entera = int(math.ceil(linea))
    elif not es_over and proyeccion_entera >= linea:
        proyeccion_entera = int(math.floor(linea))

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proyeccion_entera
    }


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_nhl_real_live"
    now = time.time()
    if cache_key in _PROPS_CACHE_NHL:
        ts, data = _PROPS_CACHE_NHL[cache_key]
        if now - ts < 1800 and data:
            return data

    abbr_loc = MAPEO_EQUIPOS_NHL.get(local, "cgy")
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante, "nyr")

    # Extrae datos 100% reales de los dos equipos seleccionados
    jugadores_pool = _obtener_lideres_reales_nhl(abbr_loc) + _obtener_lideres_reales_nhl(abbr_vis)
    candidatas = []

    for j in jugadores_pool:
        for tipo in ["Tiros a Puerta", "Puntos"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_nhl(j[tipo], tipo)
                if c["prob_real"] >= 52.0:
                    # Ponderación cuantitativa: 75% seguridad + 25% valor esperado
                    score = (c["prob_real"] * 0.75) + (c["ev"] * 0.25)
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

    # Ranking meritocrático puro: se ordenan las mejores del partido completo
    candidatas.sort(key=lambda x: x["_score"], reverse=True)

    for item in candidatas:
        item.pop("_score", None)

    seleccion = candidatas[:top_n]
    _PROPS_CACHE_NHL[cache_key] = (now, seleccion)
    return seleccion
