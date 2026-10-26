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
    "COL": 1.36, "BOS": 1.11, "CIN": 1.08, "PHI": 1.05, "NYY": 1.04,
    "LAD": 1.02, "ATL": 1.01, "HOU": 1.00, "CHC": 1.00, "TOR": 0.98,
    "SD":  0.94, "SEA": 0.91, "SF":  0.89, "OAK": 0.88
}

# Base Sabermétrica ponderada: (wRC+, Bullpen xFIP, Starter xERA, Starter K/9)
SABERMETRICS_MLB = {
    "LAD": (118, 3.45, 2.95, 10.8),
    "NYY": (115, 3.55, 3.10, 10.2),
    "ATL": (112, 3.60, 3.20, 9.8),
    "PHI": (110, 3.65, 3.15, 9.5),
    "BAL": (108, 3.70, 3.40, 9.2),
    "HOU": (106, 3.75, 3.45, 8.9),
    "DEFAULT": (100, 4.10, 4.15, 8.5)
}

def poisson_prob(k, lamb):
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)

def simular_partido_mlb(local, visitante, c_ml_loc, c_ml_vis, l_rl_loc, c_rl_loc, l_rl_vis, c_rl_vis, l_total, c_over, c_under, iteraciones=10000):
    abbr_loc = MAPEO_MLB.get(local, local[:3].upper())
    abbr_vis = MAPEO_MLB.get(visitante, visitante[:3].upper())

    # 1. Consulta meteorológica en tiempo real vía OpenWeatherMap
    ciudad = CIUDADES_MLB.get(abbr_loc, "New York")
    clima = get_live_weather(ciudad)
    temp_f = clima.get("temp_f", 72.0)
    viento_mph = clima.get("viento_mph", 0.0)

    pf = PARK_FACTORS.get(abbr_loc, 1.00)
    densidad_aire = 1.0 + ((temp_f - 72.0) * 0.0016) + (viento_mph * 0.007)
    factor_entorno = pf * densidad_aire

    s_loc = SABERMETRICS_MLB.get(abbr_loc, SABERMETRICS_MLB["DEFAULT"])
    s_vis = SABERMETRICS_MLB.get(abbr_vis, SABERMETRICS_MLB["DEFAULT"])

    # Carreras esperadas (5 innings Starter + 4 innings Bullpen)
    exp_loc = (((s_vis[2] / 9.0) * 5.0 + (s_vis[1] / 9.0) * 4.0) * (s_loc[0] / 100.0) * 0.52) * factor_entorno
    exp_vis = (((s_loc[2] / 9.0) * 5.0 + (s_loc[1] / 9.0) * 4.0) * (s_vis[0] / 100.0) * 0.48) * factor_entorno
    exp_loc = round(exp_loc, 2)
    exp_vis = round(exp_vis, 2)
    total_esperado = round(exp_loc + exp_vis, 2)

    # 2. Modelo Primera Entrada (NRFI / YRFI)
    lambda_1st_loc = (exp_loc / 9.0) * 1.15
    lambda_1st_vis = (exp_vis / 9.0) * 1.15
    prob_nrfi = round(math.exp(-lambda_1st_loc) * math.exp(-lambda_1st_vis) * 100, 1)

    # 3. Proyección de Ponches de Abridores (K's) con Poisson sobredispersa
    k_proj_loc_starter = round(s_loc[3] * (5.5 / 9.0), 1)
    k_proj_vis_starter = round(s_vis[3] * (5.5 / 9.0), 1)

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_rl_loc}_{l_rl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    prob_loc_weights = [poisson_prob(i, exp_loc) for i in range(16)]
    prob_vis_weights = [poisson_prob(i, exp_vis) for i in range(16)]

    wins_loc, wins_vis = 0, 0
    covers_rl_loc, covers_rl_vis = 0, 0
    overs, unders = 0, 0

    for _ in range(iteraciones):
        c_loc = rng.choices(range(16), weights=prob_loc_weights)[0]
        c_vis = rng.choices(range(16), weights=prob_vis_weights)[0]

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
        "proyeccion_carreras": f"{exp_loc} - {exp_vis}",
        "total_carreras_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "runline_local": {"linea": l_rl_loc, "prob": prob_rl_loc},
        "runline_visitante": {"linea": l_rl_vis, "prob": prob_rl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "nrfi_prob": prob_nrfi,
        "k_props": f"Ks Abridores: {abbr_loc} ~{k_proj_loc_starter} | {abbr_vis} ~{k_proj_vis_starter}",
        "resumen_explicado": f"SLUGGER-IA: Monte Carlo (10,000 iteraciones). Sabermetría (wRC+, Starter xERA, Bullpen xFIP) + Clima ({temp_f}°F, {viento_mph}mph) + Park Factor ({pf}). NRFI: {prob_nrfi}%. Proyección: {total_esperado} carreras."
    }
