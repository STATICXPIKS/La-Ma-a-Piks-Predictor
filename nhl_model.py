import math
import hashlib
import random

# MAPEO COMPLETO DE EQUIPOS NHL
MAPEO_NHL = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH", "New Jersey Devils": "NJ", "New York Islanders": "NYI",
    "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJ", "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL", "Tampa Bay Lightning": "TB", "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTAH", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

# RATINGS xG A FAVOR Y EN CONTRA POR PARTIDO
RATINGS_NHL = {
    "BOS": (3.4, 2.6), "FLA": (3.5, 2.7), "CAR": (3.4, 2.6), "DAL": (3.5, 2.8),
    "COL": (3.6, 3.0), "EDM": (3.6, 2.9), "NYR": (3.3, 2.7), "VGK": (3.3, 2.8),
    "VAN": (3.4, 2.8), "TOR": (3.5, 3.1), "TB":  (3.4, 3.1), "NJ":  (3.3, 2.9),
    "WPG": (3.1, 2.5), "MIN": (3.1, 3.0), "LAK": (3.0, 2.6), "NSH": (3.1, 3.0),
    "DET": (3.0, 3.3), "STL": (2.8, 3.1), "CGY": (2.9, 3.2), "SEA": (2.8, 3.1),
    "UTAH": (2.9, 3.2), "BUF": (2.9, 3.3), "PIT": (3.0, 3.4), "PHI": (2.8, 3.2),
    "OTT": (3.1, 3.4), "MTL": (2.7, 3.5), "CHI": (2.6, 3.5), "ANA": (2.5, 3.5),
    "CBJ": (2.8, 3.6), "SJ":  (2.4, 3.8), "WSH": (2.9, 3.1), "NYI": (2.8, 3.0),
    "DEFAULT": (3.0, 3.0)
}

def poisson_pmf(k: int, lamb: float) -> float:
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def simular_partido_nhl(
    local: str,
    visitante: str,
    c_ml_loc: float,
    c_ml_vis: float,
    l_pl_loc: float,
    c_pl_loc: float,
    l_pl_vis: float,
    c_pl_vis: float,
    l_total: float,
    c_over: float,
    c_under: float,
    iteraciones: int = 15000
):
    abbr_loc = MAPEO_NHL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NHL.get(visitante, visitante[:3].upper())

    # FIJAR SEMILLA DETERMINISTA BASADA EN EL DUELO (Elimina variabilidad al reanalizar)
    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_pl_loc}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    xg_off_loc, xg_def_loc = RATINGS_NHL.get(abbr_loc, RATINGS_NHL["DEFAULT"])
    xg_off_vis, xg_def_vis = RATINGS_NHL.get(abbr_vis, RATINGS_NHL["DEFAULT"])

    # Goles esperados con factor localía (0.22 goles)
    lambda_loc = round(((xg_off_loc + xg_def_vis) / 2.0) + 0.11, 2)
    lambda_vis = round(((xg_off_vis + xg_def_loc) / 2.0) - 0.11, 2)
    total_esperado = round(lambda_loc + lambda_vis, 2)

    wins_loc, wins_vis = 0, 0
    covers_pl_loc, covers_pl_vis = 0, 0
    overs, unders = 0, 0

    # Simulación Monte Carlo determinista
    for _ in range(iteraciones):
        goles_loc = rng.choices(range(10), weights=[poisson_pmf(i, lambda_loc) for i in range(10)])[0]
        goles_vis = rng.choices(range(10), weights=[poisson_pmf(i, lambda_vis) for i in range(10)])[0]

        # En hockey siempre hay ganador (Tiempo extra / Shootouts)
        if goles_loc == goles_vis:
            if rng.random() < 0.53: goles_loc += 1
            else: goles_vis += 1

        if goles_loc > goles_vis: wins_loc += 1
        else: wins_vis += 1

        # Puck Line exacto con signos respetados
        if (goles_loc + l_pl_loc) > goles_vis: covers_pl_loc += 1
        if (goles_vis + l_pl_vis) > goles_loc: covers_pl_vis += 1

        total_sim = goles_loc + goles_vis
        if total_sim > l_total: overs += 1
        elif total_sim < l_total: unders += 1
        else:
            # Empate en línea exacta (Push) se divide equitativamente
            overs += 0.5
            unders += 0.5

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)
    prob_pl_loc = round((covers_pl_loc / iteraciones) * 100, 1)
    prob_pl_vis = round((covers_pl_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_goles": f"{lambda_loc} - {lambda_vis}",
        "total_goles_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "pl_local": {"linea": l_pl_loc, "prob": prob_pl_loc},
        "pl_visitante": {"linea": l_pl_vis, "prob": prob_pl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"FROST-IA ejecutó 15,000 iteraciones Poisson deterministas para {abbr_loc} ({lambda_loc}) vs {abbr_vis} ({lambda_vis}). Total proyectado: {total_esperado} goles."
    }
