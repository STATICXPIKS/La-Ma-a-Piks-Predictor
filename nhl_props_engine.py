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
    # En tiros a puerta la línea natural es con .5
    if tipo_prop == "Tiros a Puerta":
        linea = math.floor(media_real) + 0.5
        cv = 0.28
        sigma = max(0.8, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        # En puntos de hockey la línea estándar de casino es 0.5 o 1.5
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

    # Asignación de cuotas realistas desde 1.62
    if prob_sel >= 0.67:
        cuota = 1.65
    elif prob_sel >= 0.63:
        cuota = 1.72
    elif prob_sel >= 0.59:
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
        "proyeccion": media_real
    }


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_nhl_fixed_v2"
    if cache_key in _PROPS_CACHE_NHL:
        return _PROPS_CACHE_NHL[cache_key]

    abbr_loc = MAPEO_EQUIPOS_NHL.get(local, "buf")
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante, "tb")

    jugadores_pool = []

    # 1. Intentar Scoreboard en vivo de ESPN para NHL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        url_espn = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
        r = requests.get(url_espn, headers=headers, timeout=4)
        if r.status_code == 200:
            events = r.json().get("events", [])
            for ev in events:
                comps = ev.get("competitions", [])[0].get("competitors", [])
                abbrs = [c.get("team", {}).get("abbreviation", "").lower() for c in comps]
                if abbr_loc in abbrs and abbr_vis in abbrs:
                    for comp in comps:
                        eq_ab = comp.get("team", {}).get("abbreviation", "").lower()
                        for leader in comp.get("leaders", []):
                            cat_name = leader.get("displayName", "")
                            prop_name = "Puntos" if "Point" in cat_name else ("Tiros a Puerta" if "Shot" in cat_name else None)
                            if prop_name and leader.get("leaders"):
                                l_obj = leader["leaders"][0]
                                at_name = l_obj.get("athlete", {}).get("displayName", "")
                                val = float(l_obj.get("value", 0))
                                if at_name and val > 0:
                                    jugadores_pool.append({
                                        "nombre": at_name,
                                        "equipo": eq_ab.upper(),
                                        prop_name: val
                                    })
    except Exception:
        pass

    # 2. Respaldo directo si no hay partido en vivo o hay timeout
    if not jugadores_pool:
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

    # 3. Filtrar picks con valor positivo y probabilidad sólida
    candidatas = []
    for j in jugadores_pool:
        for tipo in ["Tiros a Puerta", "Puntos"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_nhl(media, tipo)
                if c["prob_real"] >= 55.0 and c["ev"] >= 2.0:
                    score_confianza = round((c["prob_real"] * 0.70) + (c["ev"] * 0.30), 2)
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
                        "_score": score_confianza
                    })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)

    for item in candidatas:
        item.pop("_score", None)

    seleccion = candidatas[:top_n]
    _PROPS_CACHE_NHL[cache_key] = seleccion
    return seleccion
