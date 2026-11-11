import math
import time

MAPEO_EQUIPOS_NFL = {
    "Arizona Cardinals": "ari", "Atlanta Falcons": "atl", "Baltimore Ravens": "bal",
    "Buffalo Bills": "buf", "Carolina Panthers": "car", "Chicago Bears": "chi",
    "Cincinnati Bengals": "cin", "Cleveland Browns": "cle", "Dallas Cowboys": "dal",
    "Denver Broncos": "den", "Detroit Lions": "det", "Green Bay Packers": "gb",
    "Houston Texans": "hou", "Indianapolis Colts": "ind", "Jacksonville Jaguars": "jax",
    "Kansas City Chiefs": "kc", "Las Vegas Raiders": "lv", "Los Angeles Chargers": "lac",
    "Los Angeles Rams": "lar", "Miami Dolphins": "mia", "Minnesota Vikings": "min",
    "New England Patriots": "ne", "New Orleans Saints": "no", "New York Giants": "nyg",
    "New York Jets": "nyj", "Philadelphia Eagles": "phi", "Pittsburgh Steelers": "pit",
    "San Francisco 49ers": "sf", "Seattle Seahawks": "sea", "Tampa Bay Buccaneers": "tb",
    "Tennessee Titans": "ten", "Washington Commanders": "was"
}

# Rotación activa con métricas de yardas y volumen de pases completos
STATS_LIDERES_NFL = {
    "phi": [
        {"nombre": "Jalen Hurts", "Yardas Pase": 224.5, "Pases Completos": 19.4},
        {"nombre": "Saquon Barkley", "Yardas Carrera": 108.2},
        {"nombre": "A.J. Brown", "Yardas Recepción": 76.4},
        {"nombre": "DeVonta Smith", "Yardas Recepción": 56.8}
    ],
    "dal": [
        {"nombre": "Dak Prescott", "Yardas Pase": 248.0, "Pases Completos": 22.1},
        {"nombre": "CeeDee Lamb", "Yardas Recepción": 82.5},
        {"nombre": "Rico Dowdle", "Yardas Carrera": 52.4},
        {"nombre": "Jake Ferguson", "Yardas Recepción": 44.0}
    ],
    "kc": [
        {"nombre": "Patrick Mahomes", "Yardas Pase": 254.0, "Pases Completos": 23.2},
        {"nombre": "Travis Kelce", "Yardas Recepción": 64.0},
        {"nombre": "Kareem Hunt", "Yardas Carrera": 62.0}
    ],
    "sf": [
        {"nombre": "Brock Purdy", "Yardas Pase": 260.0, "Pases Completos": 20.8},
        {"nombre": "Christian McCaffrey", "Yardas Carrera": 78.0, "Yardas Recepción": 40.5},
        {"nombre": "George Kittle", "Yardas Recepción": 66.0}
    ],
    "bal": [
        {"nombre": "Lamar Jackson", "Yardas Pase": 238.0, "Yardas Carrera": 54.0},
        {"nombre": "Derrick Henry", "Yardas Carrera": 104.5},
        {"nombre": "Zay Flowers", "Yardas Recepción": 62.8}
    ],
    "det": [
        {"nombre": "Jared Goff", "Yardas Pase": 252.0, "Pases Completos": 21.8},
        {"nombre": "Jahmyr Gibbs", "Yardas Carrera": 74.0, "Yardas Recepción": 28.0},
        {"nombre": "Amon-Ra St. Brown", "Yardas Recepción": 81.2}
    ]
}

_PROPS_CACHE_NFL = {}


def _calcular_prop_nfl(media_real: float, tipo_prop: str):
    es_discreto = (tipo_prop == "Pases Completos")

    if es_discreto:
        linea = math.floor(media_real) + 0.5
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_over = 1.0 - prob_under
    else:
        linea = math.floor(media_real) + 0.5
        cv = 0.22 if "Pase" in tipo_prop else (0.27 if "Carrera" in tipo_prop else 0.31)
        sigma = max(4.0, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
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

    if es_discreto:
        proyeccion_final = int(round(media_real))
        if es_over and proyeccion_final <= linea:
            proyeccion_final = int(math.ceil(linea))
        elif not es_over and proyeccion_final >= linea:
            proyeccion_final = int(math.floor(linea))
    else:
        proyeccion_final = round(media_real, 1)

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proyeccion_final
    }


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_nfl_high_conf_v2"
    if cache_key in _PROPS_CACHE_NFL:
        return _PROPS_CACHE_NFL[cache_key]

    abbr_loc = MAPEO_EQUIPOS_NFL.get(local, "phi")
    abbr_vis = MAPEO_EQUIPOS_NFL.get(visitante, "dal")

    jugadores_pool = []
    l_loc = STATS_LIDERES_NFL.get(abbr_loc, STATS_LIDERES_NFL.get("phi", []))
    l_vis = STATS_LIDERES_NFL.get(abbr_vis, STATS_LIDERES_NFL.get("dal", []))

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
        for tipo in ["Yardas Pase", "Yardas Carrera", "Yardas Recepción", "Pases Completos"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_nfl(media, tipo)
                if c["prob_real"] >= 60.0 and c["ev"] >= 3.0 and c["cuota"] >= 1.60:
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
    _PROPS_CACHE_NFL[cache_key] = seleccion
    return seleccion
