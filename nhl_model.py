import math
import hashlib
import random
from api_service import get_nhl_team_live_stats

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

# Respaldo estadístico en caso de timeout de API-Sports
RATINGS_RESPALDO = {
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

def poisson_prob(k: int, lamb: float) -> float:
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
    iteraciones: int = 25000
):
    abbr_loc = MAPEO_NHL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NHL.get(visitante, visitante[:3].upper())

    # 1. Consulta estadísticas reales en vivo desde API-Sports
    live_stats_loc = get_nhl_team_live_stats(local)
    live_stats_vis = get_nhl_team_live_stats(visitante)

    xg_off_loc, xg_def_loc = live_stats_loc if live_stats_loc else RATINGS_RESPALDO.get(abbr_loc, RATINGS_RESPALDO["DEFAULT"])
    xg_off_vis, xg_def_vis = live_stats_vis if live_stats_vis else RATINGS_RESPALDO.get(abbr_vis, RATINGS_RESPALDO["DEFAULT"])

    # 2. Cálculo estricto de medias esperadas (Poisson Lambda)
    lambda_loc = round(((xg_off_loc + xg_def_vis) / 2.0) + 0.12, 2)
    lambda_vis = round(((xg_off_vis + xg_def_loc) / 2.0) - 0.12, 2)
    total_esperado = round(lambda_loc + lambda_vis, 2)

    # Semilla fija determinista para que no cambie entre clics
    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_pl_loc}_{l_pl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    prob_loc_weights = [poisson_prob(i, lambda_loc) for i in range(12)]
    prob_vis_weights = [poisson_prob(i, lambda_vis) for i in range(12)]

    wins_loc, wins_vis = 0, 0
    covers_pl_loc, covers_pl_vis = 0, 0
    overs, unders = 0, 0

    for _ in range(iteraciones):
        g_loc = rng.choices(range(12), weights=prob_loc_weights)[0]
        g_vis = rng.choices(range(12), weights=prob_vis_weights)[0]

        # Desempate reglamentario (OT/SO)
        fin_loc, fin_vis = g_loc, g_vis
        if fin_loc == fin_vis:
            if rng.random() < 0.52: fin_loc += 1
            else: fin_vis += 1

        if fin_loc > fin_vis: wins_loc += 1
        else: wins_vis += 1

        # Puck Line exacto con signos algebraicos reales
        if (fin_loc + l_pl_loc) > fin_vis: covers_pl_loc += 1
        if (fin_vis + l_pl_vis) > fin_loc: covers_pl_vis += 1

        tot = fin_loc + fin_vis
        if tot > l_total: overs += 1
        elif tot < l_total: unders += 1
        else:
            overs += 0.5
            unders += 0.5

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)
    prob_pl_loc = round((covers_pl_loc / iteraciones) * 100, 1)
    prob_pl_vis = round((covers_pl_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    origen = "API-Sports (Live)" if live_stats_loc else "Métricas Históricas"
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
        "resumen_explicado": f"FROST-IA consultó {origen}. Simulación determinista de 25,000 escenarios. Proyección: {total_esperado} goles totales."
    }
