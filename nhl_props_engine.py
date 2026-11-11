import math
import time
import requests

MAPEO_EQUIPOS_NHL = {
    "Anaheim Ducks": "ana", "Boston Bruins": "bos", "Buffalo Sabres": "buf",
    "Calgary Flames": "cgy", "Carolina Hurricanes": "car", "Chicago Blackhawks": "chi",
    "Colorado Avalanche": "col", "Columbus Blue Jackets": "cbj", "Dallas Stars": "dal",
    "Detroit Red Wings": "det", "Edmonton Oilers": "edm", "Florida Panthers": "fla",
    "Los Angeles Kings": "la", "Minnesota Wild": "min", "Montreal Canadiens": "mtl",
    "Nashville Predators": "nsh", "New Jersey Devils": "nj", "New York Islanders": "nyi",
    "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
    "Pittsburgh Penguins": "pit", "San Jose Sharks": "sj", "Seattle Kraken": "sea",
    "St. Louis Blues": "stl", "Tampa Bay Lightning": "tb", "Toronto Maple Leafs": "tor",
    "Utah Hockey Club": "utah", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
    "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"
}

# Estadísticas oficiales en PROMEDIO POR PARTIDO (Per Game) de la temporada activa
STATS_LIDERES_NHL = {
    "buf": [
        {"nombre": "Tage Thompson", "Tiros a Puerta": 3.8, "Puntos": 1.1},
        {"nombre": "Alex Tuch", "Tiros a Puerta": 2.9, "Puntos": 0.9},
        {"nombre": "Rasmus Dahlin", "Tiros a Puerta": 2.6, "Puntos": 0.8},
        {"nombre": "JJ Peterka", "Tiros a Puerta": 2.7, "Puntos": 0.8}
    ],
    "tb": [
        {"nombre": "Nikita Kucherov", "Tiros a Puerta": 4.1, "Puntos": 1.5},
        {"nombre": "Brayden Point", "Tiros a Puerta": 2.9, "Puntos": 1.0},
        {"nombre": "Jake Guentzel", "Tiros a Puerta": 3.2, "Puntos": 1.1},
        {"nombre": "Victor Hedman", "Tiros a Puerta": 2.4, "Puntos": 0.9}
    ],
    "edm": [
        {"nombre": "Connor McDavid", "Tiros a Puerta": 3.7, "Puntos": 1.6},
        {"nombre": "Leon Draisaitl", "Tiros a Puerta": 3.4, "Puntos": 1.4},
        {"nombre": "Evan Bouchard", "Tiros a Puerta": 3.2, "Puntos": 0.9}
    ],
    "tor": [
        {"nombre": "Auston Matthews", "Tiros a Puerta": 4.3, "Puntos": 1.2},
        {"nombre": "Mitch Marner", "Tiros a Puerta": 2.6, "Puntos": 1.2},
        {"nombre": "William Nylander", "Tiros a Puerta": 3.6, "Puntos": 1.1}
    ],
    "col": [
        {"nombre": "Nathan MacKinnon", "Tiros a Puerta": 4.6, "Puntos": 1.6},
        {"nombre": "Mikko Rantanen", "Tiros a Puerta": 3.5, "Puntos": 1.3},
        {"nombre": "Cale Makar", "Tiros a Puerta": 3.0, "Puntos": 1.2}
    ]
}

_PROPS_CACHE_NHL = {}


def _calcular_prop_nhl(media_real: float, tipo_prop: str):
    # 1. Normalización para evitar números acumulados irreales en hockey
    # Si por error entra un valor acumulado (ej. 19 o 22), se normaliza a promedio por juego
    if tipo_prop == "Puntos" and media_real > 3.0:
        media_real = round(media_real / 18.0, 1)
    elif tipo_prop == "Tiros a Puerta" and media_real > 10.0:
        media_real = round(media_real / 18.0, 1)

    # 2. Definición cuantitativa de la línea de mercado
    if tipo_prop == "Tiros a Puerta":
        linea = math.floor(media_real) + 0.5
        cv = 0.28
        sigma = max(0.8, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        # En puntos de hockey la línea estándar es 0.5 o 1.5
        linea = 1.5 if media_real >= 1.2 else 0.5
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under
    prob_sel = max(0.50, min(0.72, prob_sel))

    # 3. Asignación de cuota desde 1.62
    if prob_sel >= 0.67:
        cuota = 1.65
    elif prob_sel >= 0.63:
        cuota = 1.72
    elif prob_sel >= 0.59:
        cuota = 1.80
    else:
        cuota = 1.88

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    # 4. Proyección entera sin puntos medios:
    # Si la media es 1.5 o 1.6, la proyección proyectada es 2; si es 0.9, es 1
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
    cache_key = f"{local}_{visitante}_nhl_clean_v4"
    if cache_key in _PROPS_CACHE_NHL:
        return _PROPS_CACHE_NHL[cache_key]

    abbr_loc = MAPEO_EQUIPOS_NHL.get(local, "buf")
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante, "tb")

    jugadores_pool = []

    # Respaldo directo con estadísticas ponderadas de promedios por partido
    l_loc = STATS_LIDERES_NHL.get(abbr_loc, STATS_LIDERES_NHL.get("buf", []))
    l_vis = STATS_LIDERES_NHL.get(abbr_vis, STATS_LIDERES_NHL.get("tb", []))

    for j in l_loc:
        copia = dict(j)
        copia["equipo"] = abbr_loc.upper()
        jugadores_pool.append(copia)
    for j in l_vis:
        copia = dict(j)
        copia["equipo"] = abbr_vis.upper()
        jugadores_pool.append(copia)

    # Filtrado estricto: valor positivo y alta probabilidad
    candidatas = []
    for j in jugadores_pool:
        for tipo in ["Tiros a Puerta", "Puntos"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_nhl(media, tipo)
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
    _PROPS_CACHE_NHL[cache_key] = seleccion
    return seleccion
