import math
import hashlib
import random
from api_service import get_live_weather

MAPEO_MLB = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS", "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL",
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD", "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK", "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT", "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL", "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR", "Washington Nationals": "WSH"
}

CIUDADES_MLB = {
    "ARI": "Phoenix", "ATL": "Atlanta", "BAL": "Baltimore", "BOS": "Boston",
    "CHC": "Chicago", "CWS": "Chicago", "CIN": "Cincinnati", "CLE": "Cleveland",
    "COL": "Denver", "DET": "Detroit", "HOU": "Houston", "KC": "Kansas City",
    "LAA": "Anaheim", "LAD": "Los Angeles", "MIA": "Miami", "MIL": "Milwaukee",
    "MIN": "Minneapolis", "NYM": "New York", "NYY": "New York", "OAK": "Oakland",
    "PHI": "Philadelphia", "PIT": "Pittsburgh", "SD": "San Diego", "SF": "San Francisco",
    "SEA": "Seattle", "STL": "St. Louis", "TB": "St. Petersburg", "TEX": "Arlington",
    "TOR": "Toronto", "WSH": "Washington"
}

PARK_FACTORS = {
    "COL": 1.35, "BOS": 1.12, "CIN": 1.08, "PHI": 1.06, "NYY": 1.05,
    "LAD": 1.02, "ATL": 1.01, "HOU": 1.00, "CHC": 1.00, "TOR": 0.99,
    "MIL": 1.01, "TB":  0.95, "MIN": 0.98, "BAL": 0.99, "DET": 0.97,
    "KC":  1.02, "CWS": 0.99, "CLE": 0.98, "TEX": 1.00, "LAA": 0.98,
    "OAK": 0.89, "SEA": 0.91, "SF":  0.90, "SD":  0.94, "ARI": 1.03,
    "MIA": 0.93, "NYM": 0.96, "WSH": 1.01, "STL": 0.97, "PIT": 0.96
}

# BASE DE DATOS SABERMÉTRICA DESACOPLADA:
# - Ofensiva: 70% reciente / 30% anterior (wRC+ vs RHP, wRC+ vs LHP, OBP)
# - Abridores: 60% reciente / 40% anterior (Mano Abridor 'R'/'L', xERA, K/9)
# - Bullpen: 50% reciente / 50% anterior con regresión a la media (xFIP)
# Formato: (wRC+_vs_RHP, wRC+_vs_LHP, OBP, Mano_Abridor, xERA_Abridor, K9_Abridor, xFIP_Bullpen)
SABERMETRICS_DESACOPLADA = {
    "ARI": (103, 99,  0.319, "R", 3.98, 8.7, 3.90),
    "ATL": (112, 107, 0.331, "R", 3.47, 9.6, 3.67),
    "BAL": (109, 105, 0.327, "R", 3.63, 9.3, 3.77),
    "BOS": (106, 100, 0.323, "R", 3.92, 8.8, 3.91),
    "CHC": (102, 98,  0.317, "L", 3.82, 8.6, 3.81),
    "CWS": (82,  85,  0.287, "R", 4.68, 7.7, 4.56),
    "CIN": (98,  95,  0.311, "R", 4.12, 9.1, 4.07),
    "CLE": (100, 96,  0.314, "R", 3.72, 8.8, 3.47),
    "COL": (89,  86,  0.304, "R", 5.13, 7.1, 4.87),
    "DET": (101, 97,  0.315, "L", 3.63, 9.6, 3.59),
    "HOU": (107, 104, 0.325, "R", 3.77, 8.9, 3.71),
    "KC":  (104, 101, 0.319, "L", 3.72, 8.7, 3.81),
    "LAA": (93,  90,  0.305, "R", 4.37, 8.1, 4.27),
    "LAD": (121, 117, 0.343, "R", 3.07, 10.7, 3.39),
    "MIA": (88,  91,  0.301, "R", 4.42, 8.0, 4.31),
    "MIL": (107, 103, 0.323, "R", 3.62, 9.2, 3.59),
    "MIN": (106, 102, 0.323, "R", 3.87, 9.2, 3.81),
    "NYM": (110, 106, 0.328, "L", 3.72, 9.5, 3.73),
    "NYY": (118, 114, 0.339, "R", 3.32, 10.2, 3.49),
    "OAK": (96,  93,  0.310, "R", 4.22, 8.5, 4.13),
    "PHI": (114, 110, 0.335, "R", 3.27, 9.9, 3.53),
    "PIT": (90,  93,  0.303, "R", 3.82, 9.5, 3.97),
    "SD":  (109, 105, 0.326, "R", 3.62, 9.6, 3.63),
    "SF":  (98,  95,  0.311, "L", 3.77, 8.8, 3.81),
    "SEA": (97,  94,  0.309, "R", 3.37, 10.0, 3.49),
    "STL": (99,  96,  0.312, "R", 4.07, 8.2, 3.97),
    "TB":  (102, 97,  0.315, "R", 3.62, 9.2, 3.67),
    "TEX": (103, 100, 0.319, "R", 3.87, 8.7, 3.91),
    "TOR": (101, 98,  0.317, "R", 3.97, 8.5, 3.87),
    "WSH": (93,  90,  0.304, "L", 4.32, 8.2, 4.21)
}

def poisson_prob(k, lamb):
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def simular_partido_mlb(
    local: str,
    visitante: str,
    c_ml_loc: float,
    c_ml_vis: float,
    l_rl_loc: float,
    c_rl_loc: float,
    l_rl_vis: float,
    c_rl_vis: float,
    l_total: float,
    c_over: float,
    c_under: float,
    iteraciones: int = 10000
):
    abbr_loc = MAPEO_MLB.get(local, "TB")
    abbr_vis = MAPEO_MLB.get(visitante, "MIL")

    # 1. Clima en tiempo real (OpenWeather)
    ciudad = CIUDADES_MLB.get(abbr_loc, "St. Petersburg")
    clima = get_live_weather(ciudad)
    temp_f = clima.get("temp_f", 72.0)
    viento_mph = clima.get("viento_mph", 0.0)

    pf = PARK_FACTORS.get(abbr_loc, 1.00)
    densidad_aire = 1.0 + ((temp_f - 72.0) * 0.0018) + (viento_mph * 0.006)
    factor_entorno = pf * densidad_aire

    s_loc = SABERMETRICS_DESACOPLADA.get(abbr_loc, (100, 100, 0.315, "R", 4.00, 8.5, 4.00))
    s_vis = SABERMETRICS_DESACOPLADA.get(abbr_vis, (100, 100, 0.315, "R", 4.00, 8.5, 4.00))

    # 2. Platoon Splits: Selección de wRC+ según la mano del abridor rival
    mano_abridor_vis = s_vis[3]
    mano_abridor_loc = s_loc[3]
    wrc_loc = s_loc[1] if mano_abridor_vis == "L" else s_loc[0]
    wrc_vis = s_vis[1] if mano_abridor_loc == "L" else s_vis[0]

    # 3. Carreras Esperadas Ponderadas (5.5 innings Starter + 3.5 innings Bullpen)
    runs_allowed_vis = ((s_vis[4] / 9.0) * 5.5) + ((s_vis[6] / 9.0) * 3.5)
    runs_allowed_loc = ((s_loc[4] / 9.0) * 5.5) + ((s_loc[6] / 9.0) * 3.5)

    lambda_loc = round((runs_allowed_vis * (wrc_loc / 100.0) * 1.03) * factor_entorno, 2)
    lambda_vis = round((runs_allowed_loc * (wrc_vis / 100.0) * 0.97) * factor_entorno, 2)
    total_esperado = round(lambda_loc + lambda_vis, 2)

    # 4. Modelo Primera Entrada (NRFI / YRFI con Poisson bivariado)
    lambda_1st_loc = (lambda_loc / 9.0) * 1.22
    lambda_1st_vis = (lambda_vis / 9.0) * 1.22
    prob_nrfi = round(math.exp(-lambda_1st_loc) * math.exp(-lambda_1st_vis) * 100, 1)

    # 5. Proyección de Ponches de Abridores (K's) ajustada por el bateo rival
    k_proj_loc = round(s_loc[5] * (5.5 / 9.0) * (100.0 / wrc_vis), 1)
    k_proj_vis = round(s_vis[5] * (5.5 / 9.0) * (100.0 / wrc_loc), 1)

    # 6. Monte Carlo a 10,000 iteraciones deterministas
    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_rl_loc}_{l_rl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    prob_loc_weights = [poisson_prob(i, lambda_loc) for i in range(20)]
    prob_vis_weights = [poisson_prob(i, lambda_vis) for i in range(20)]

    wins_loc, wins_vis = 0, 0
    covers_rl_loc, covers_rl_vis = 0, 0
    overs, unders = 0, 0

    for _ in range(iteraciones):
        c_loc = rng.choices(range(20), weights=prob_loc_weights)[0]
        c_vis = rng.choices(range(20), weights=prob_vis_weights)[0]

        if c_loc == c_vis:
            if rng.random() < 0.53: c_loc += 1
            else: c_vis += 1

        if c_loc > c_vis: wins_loc += 1
        else: wins_vis += 1

        if (c_loc + l_rl_loc) > c_vis: covers_rl_loc += 1
        if (c_vis + l_rl_vis) > c_loc: covers_rl_vis += 1

        tot = c_loc + c_vis
        if tot > l_total: overs += 1
        elif tot < l_total: unders += 1
        else:
            overs += 0.5
            unders += 0.5

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)
    prob_rl_loc = round((covers_rl_loc / iteraciones) * 100, 1)
    prob_rl_vis = round((covers_rl_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_carreras": f"{lambda_loc} - {lambda_vis}",
        "total_carreras_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "runline_local": {"linea": l_rl_loc, "prob": prob_rl_loc},
        "runline_visitante": {"linea": l_rl_vis, "prob": prob_rl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "nrfi_prob": prob_nrfi,
        "k_props": f"Ks Abridores: {abbr_loc} ({s_loc[3]}HP) ~{k_proj_loc} | {abbr_vis} ({s_vis[3]}HP) ~{k_proj_vis}",
        "resumen_explicado": f"SLUGGER-IA: Sabermetría Desacoplada + Platoon Splits ({mano_abridor_vis}HP vs {mano_abridor_loc}HP). Clima ({temp_f}°F, {viento_mph}mph) + PF ({pf}). NRFI: {prob_nrfi}%. Ks: {abbr_loc} ~{k_proj_loc} / {abbr_vis} ~{k_proj_vis}. Proyección: {total_esperado} carreras."
    }
