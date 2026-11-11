import math
import time

MAPEO_EQUIPOS_MLB = {
    "Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal",
    "Boston Red Sox": "bos", "Chicago Cubs": "chc", "Chicago White Sox": "chw",
    "Cincinnati Reds": "cin", "Cleveland Guardians": "cle", "Colorado Rockies": "col",
    "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc",
    "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia",
    "Milwaukee Brewers": "mil", "Minnesota Twins": "min", "New York Mets": "nym",
    "New York Yankees": "nyy", "Oakland Athletics": "oak", "Philadelphia Phillies": "phi",
    "Pittsburgh Pirates": "pit", "San Diego Padres": "sd", "San Francisco Giants": "sf",
    "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb",
    "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh"
}

STATS_LIDERES_MLB = {
    "lad": [
        {"nombre": "Shohei Ohtani", "Hits": 1.3, "Bases Totales": 2.6},
        {"nombre": "Mookie Betts", "Hits": 1.2, "Bases Totales": 2.1},
        {"nombre": "Freddie Freeman", "Hits": 1.1, "Bases Totales": 1.9},
        {"nombre": "Tyler Glasnow", "Ponches (K's)": 7.4}
    ],
    "nyy": [
        {"nombre": "Aaron Judge", "Hits": 1.2, "Bases Totales": 2.7},
        {"nombre": "Juan Soto", "Hits": 1.1, "Bases Totales": 2.2},
        {"nombre": "Gerrit Cole", "Ponches (K's)": 6.8}
    ],
    "atl": [
        {"nombre": "Ronald Acuña Jr.", "Hits": 1.2, "Bases Totales": 2.2},
        {"nombre": "Spencer Strider", "Ponches (K's)": 8.2},
        {"nombre": "Matt Olson", "Hits": 1.0, "Bases Totales": 2.0}
    ],
    "phi": [
        {"nombre": "Bryce Harper", "Hits": 1.1, "Bases Totales": 2.1},
        {"nombre": "Zack Wheeler", "Ponches (K's)": 7.1},
        {"nombre": "Trea Turner", "Hits": 1.3, "Bases Totales": 2.0}
    ]
}

_PROPS_CACHE_MLB = {}


def _calcular_prop_mlb(media_real: float, tipo_prop: str):
    linea = math.floor(media_real) + 0.5
    
    if "Ponches" in tipo_prop:
        sigma = max(1.1, media_real * 0.24)
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

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": round(media_real, 1)
    }


def obtener_mejores_props_mlb(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_mlb_props_v1"
    if cache_key in _PROPS_CACHE_MLB:
        return _PROPS_CACHE_MLB[cache_key]

    abbr_loc = MAPEO_EQUIPOS_MLB.get(local, "lad")
    abbr_vis = MAPEO_EQUIPOS_MLB.get(visitante, "nyy")

    jugadores_pool = []
    l_loc = STATS_LIDERES_MLB.get(abbr_loc, STATS_LIDERES_MLB.get("lad", []))
    l_vis = STATS_LIDERES_MLB.get(abbr_vis, STATS_LIDERES_MLB.get("nyy", []))

    for j in l_loc:
        copia = dict(j)
        copia["equipo"] = abbr_loc.upper()
        jugadores_pool.append(copia)
    for j in l_vis:
        copia = dict(j)
        copia["equipo"] = abbr_vis.upper()
        jugadores_pool.append(copia)

    candidatas = []
    for j in jugadores_pool:
        for tipo in ["Ponches (K's)", "Hits", "Bases Totales"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_mlb(media, tipo)
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
    _PROPS_CACHE_MLB[cache_key] = seleccion
    return seleccion
