import random
import math

# Mapeo completo de equipos de NHL
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

# Ratings de xG (Goles Esperados) a Favor y en Contra por partido
RATINGS_NHL = {
    "BOS": (3.4, 2.6), "FLA": (3.5, 2.7), "CAR": (3.4, 2.6), "DAL": (3.5, 2.8),
    "COL": (3.6, 3.0), "EDM": (3.6, 2.9), "NYR": (3.3, 2.7), "VGK": (3.3, 2.8),
    "VAN": (3.4, 2.8), "TOR": (3.5, 3.1), "TB":  (3.4, 3.1), "NJ":  (3.3, 2.9),
    "WPG": (3.1, 2.5), "MIN": (3.1, 3.0), "LAK": (3.0, 2.6), "NSH": (3.1, 3.0),
    "DET": (3.0, 3.3), "STL": (2.8, 3.1), "CGY": (2.9, 3.2), "SEA": (2.8, 3.1),
    "UTAH": (2.9, 3.2), "BUF": (2.9, 3.3), "PIT": (3.0, 3.4), "PHI": (2.8, 3.2),
    "OTT": (3.1, 3.4), "MTL": (2.7, 3.5), "CHI": (2.6, 3.5), "ANA": (2.5, 3.5),
    "CBJ": (2.8, 3.6), "SJ":  (2.4, 3.8), "WSH": (2.9, 3.1), "NYI": (2.8, 3.0)
}

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
    iteraciones: int = 10000
):
    abbr_loc = MAPEO_NHL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NHL.get(visitante, visitante[:3].upper())

    xg_f_loc, xg_c_loc = RATINGS_NHL.get(abbr_loc, (3.0, 3.0))
    xg_f_vis, xg_c_vis = RATINGS_NHL.get(abbr_vis, (3.0, 3.0))

    ventaja_localia = 0.22
    exp_goles_loc = ((xg_f_loc + xg_c_vis) / 2.0) + (ventaja_localia / 2.0)
    exp_goles_vis = ((xg_f_vis + xg_c_loc) / 2.0) - (ventaja_localia / 2.0)

    wins_loc, wins_vis = 0, 0
    covers_pl_loc, covers_pl_vis = 0, 0
    overs, unders = 0, 0

    std_dev = 1.65 

    for _ in range(iteraciones):
        goles_loc = max(0, round(random.gauss(exp_goles_loc, std_dev)))
        goles_vis = max(0, round(random.gauss(exp_goles_vis, std_dev)))

        if goles_loc == goles_vis:
            if random.random() < 0.54:
                goles_loc += 1
            else:
                goles_vis += 1

        if goles_loc > goles_vis:
            wins_loc += 1
        else:
            wins_vis += 1

        if (goles_loc + l_pl_loc) > goles_vis:
            covers_pl_loc += 1
        if (goles_vis + l_pl_vis) > goles_loc:
            covers_pl_vis += 1

        total_sim = goles_loc + goles_vis
        if total_sim > l_total:
            overs += 1
        elif total_sim < l_total:
            unders += 1

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)

    prob_pl_loc = round((covers_pl_loc / iteraciones) * 100, 1)
    prob_pl_vis = round((covers_pl_vis / iteraciones) * 100, 1)

    prob_over = round((overs / iteraciones) * 100, 1)
    prob_under = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_goles": f"{round(exp_goles_loc, 2)} - {round(exp_goles_vis, 2)}",
        "total_goles_proyectado": round(exp_goles_loc + exp_goles_vis, 2),
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "pl_local": {"linea": l_pl_loc, "prob": prob_pl_loc},
        "pl_visitante": {"linea": l_pl_vis, "prob": prob_pl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"FROST-IA simuló 10,000 iteraciones con marcadores discretos para {abbr_loc} vs {abbr_vis}, proyectando {round(exp_goles_loc + exp_goles_vis, 2)} goles totales."
    }
