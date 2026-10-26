import math
import hashlib
import random
from api_service import get_nhl_stats_live

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
    "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

# Base estadística ponderada (2025-2026 / 2026-2027)
# Formato: (xGF/60, xGA/60, SV% Portero Titular, PP%, PK%, Elo)
STATS_NHL_MULTI = {
    "BOS": (3.35, 2.58, 0.916, 23.4, 82.5, 1545),
    "FLA": (3.48, 2.62, 0.912, 24.1, 83.0, 1560),
    "CAR": (3.52, 2.45, 0.908, 26.0, 84.8, 1570),
    "DAL": (3.40, 2.65, 0.915, 23.8, 81.5, 1550),
    "COL": (3.62, 2.95, 0.904, 25.5, 80.2, 1555),
    "EDM": (3.65, 2.88, 0.905, 27.2, 81.0, 1565),
    "NYR": (3.28, 2.68, 0.918, 24.5, 84.1, 1548),
    "VGK": (3.32, 2.75, 0.910, 22.8, 81.2, 1540),
    "TOR": (3.45, 3.05, 0.902, 25.0, 78.5, 1535),
    "CGY": (2.88, 3.12, 0.906, 18.5, 80.0, 1480),
    "LAK": (3.02, 2.58, 0.911, 19.8, 83.5, 1520),
    "DEFAULT": (3.00, 3.00, 0.905, 21.0, 80.0, 1500)
}

def poisson_pmf(k, lamb):
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def simular_partido_nhl(local, visitante, c_ml_loc, c_ml_vis, l_pl_loc, c_pl_loc, l_pl_vis, c_pl_vis, l_total, c_over, c_under, iteraciones=10000):
    abbr_loc = MAPEO_NHL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NHL.get(visitante, visitante[:3].upper())

    s_loc = STATS_NHL_MULTI.get(abbr_loc, STATS_NHL_MULTI["DEFAULT"])
    s_vis = STATS_NHL_MULTI.get(abbr_vis, STATS_NHL_MULTI["DEFAULT"])

    # Elo Dinámico con ventaja local (+50 Elo)
    elo_diff = (s_loc[5] + 50) - s_vis[5]
    prob_elo_loc = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))

    # Ajuste de portero sobre promedio de liga (0.905)
    sv_factor_loc = (1.0 - s_loc[2]) / 0.095
    sv_factor_vis = (1.0 - s_vis[2]) / 0.095

    # Interacción de Equipos Especiales (Power Play vs Penalty Kill)
    pp_pk_loc = 1.0 + ((s_loc[3] - s_vis[4]) / 500.0)
    pp_pk_vis = 1.0 + ((s_vis[3] - s_loc[4]) / 500.0)

    lambda_loc = round(((s_loc[0] + s_vis[1]) / 2.0) * sv_factor_vis * pp_pk_loc + 0.12, 2)
    lambda_vis = round(((s_vis[0] + s_loc[1]) / 2.0) * sv_factor_loc * pp_pk_vis - 0.12, 2)
    total_esperado = round(lambda_loc + lambda_vis, 2)

    # Semilla determinista: 10,000 iteraciones estables y reproducibles
    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_pl_loc}_{l_pl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    prob_loc_weights = [poisson_pmf(i, lambda_loc) for i in range(12)]
    prob_vis_weights = [poisson_pmf(i, lambda_vis) for i in range(12)]

    wins_loc, wins_vis = 0, 0
    covers_pl_loc, covers_pl_vis = 0, 0
    overs, unders = 0, 0

    for _ in range(iteraciones):
        g_loc = rng.choices(range(12), weights=prob_loc_weights)[0]
        g_vis = rng.choices(range(12), weights=prob_vis_weights)[0]

        fin_loc, fin_vis = g_loc, g_vis
        if fin_loc == fin_vis:
            if rng.random() < prob_elo_loc: fin_loc += 1
            else: fin_vis += 1

        if fin_loc > fin_vis: wins_loc += 1
        else: wins_vis += 1

        # Puck Line exacto con signos respetados
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
        "resumen_explicado": f"FROST-IA: Monte Carlo (10,000 iteraciones). Modelo xG Poisson + Goaltender SV% ({s_loc[2]}/{s_vis[2]}) + Special Teams + Elo ({s_loc[5]}/{s_vis[5]}). Proyección: {total_esperado} goles."
    }
