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
    "SD":  0.95, "SEA": 0.91, "SF":  0.90, "OAK": 0.88
}

PITCHERS_STATS = {
    "LAD_ACE": {"xERA": 2.85, "FIP": 2.90, "WHIP": 1.02, "K_9": 11.2, "outs_prom": 18.2},
    "NYY_ACE": {"xERA": 3.10, "FIP": 3.15, "WHIP": 1.08, "K_9": 10.5, "outs_prom": 17.5},
    "DEFAULT": {"xERA": 4.15, "FIP": 4.20, "WHIP": 1.28, "K_9": 8.5,  "outs_prom": 15.5}
}

EQUIPOS_SABERMETRICS = {
    "LAD": {"wRC_vs_R": 122, "bullpen_xERA": 3.40},
    "NYY": {"wRC_vs_R": 112, "bullpen_xERA": 3.55},
    "DEFAULT": {"wRC_vs_R": 100, "bullpen_xERA": 4.10}
}

def poisson_prob(k: int, lamb: float) -> float:
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
    iteraciones: int = 25000
):
    abbr_loc = MAPEO_MLB.get(local, local[:3].upper())
    abbr_vis = MAPEO_MLB.get(visitante, visitante[:3].upper())

    # 1. Consulta clima en vivo desde OpenWeatherMap
    ciudad = CIUDADES_MLB.get(abbr_loc, "New York")
    clima = get_live_weather(ciudad)
    temp_f = clima.get("temp_f", 72.0)
    viento_mph = clima.get("viento_mph", 0.0)

    pf = PARK_FACTORS.get(abbr_loc, 1.00)
    factor_clima = 1.0 + ((temp_f - 72.0) * 0.0015) + (viento_mph * 0.008)

    p_loc = PITCHERS_STATS.get(f"{abbr_loc}_ACE", PITCHERS_STATS["DEFAULT"])
    p_vis = PITCHERS_STATS.get(f"{abbr_vis}_ACE", PITCHERS_STATS["DEFAULT"])
    off_loc = EQUIPOS_SABERMETRICS.get(abbr_loc, EQUIPOS_SABERMETRICS["DEFAULT"])
    off_vis = EQUIPOS_SABERMETRICS.get(abbr_vis, EQUIPOS_SABERMETRICS["DEFAULT"])

    exp_carreras_loc = round(((p_vis["xERA"] / 9.0) * (off_loc["wRC_vs_R"] / 100.0) * 4.5) * pf * factor_clima, 2)
    exp_carreras_vis = round(((p_loc["xERA"] / 9.0) * (off_vis["wRC_vs_R"] / 100.0) * 4.5) * pf * factor_clima, 2)
    total_esperado = round(exp_carreras_loc + exp_carreras_vis, 2)

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_rl_loc}_{l_rl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    prob_loc_weights = [poisson_prob(i, exp_carreras_loc) for i in range(15)]
    prob_vis_weights = [poisson_prob(i, exp_carreras_vis) for i in range(15)]

    wins_loc, wins_vis = 0, 0
    covers_rl_loc, covers_rl_vis = 0, 0
    overs, unders = 0, 0

    for _ in range(iteraciones):
        c_loc = rng.choices(range(15), weights=prob_loc_weights)[0]
        c_vis = rng.choices(range(15), weights=prob_vis_weights)[0]

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
        "proyeccion_carreras": f"{exp_carreras_loc} - {exp_carreras_vis}",
        "total_carreras_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "runline_local": {"linea": l_rl_loc, "prob": prob_rl_loc},
        "runline_visitante": {"linea": l_rl_vis, "prob": prob_rl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"SLUGGER-IA conectó OpenWeather ({ciudad}: {temp_f}°F, viento {viento_mph} mph). Simulación de 25,000 iteraciones con Park Factor ({pf}). Proyección: {total_esperado} carreras."
    }
