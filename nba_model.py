import random
import math

# Parámetros calibrados con la liga actual de la NBA
PACE_LIGA = 100.2
OFF_EFF_LIGA = 116.5

# Base de eficiencias aproximadas por equipo (ORtg / DRtg)
EQUIPOS_RATINGS = {
    "BOS": (121.5, 110.2), "OKC": (118.5, 107.5), "DEN": (117.8, 112.0),
    "MIN": (115.0, 108.5), "MIL": (118.0, 114.5), "PHI": (116.5, 111.5),
    "DAL": (117.5, 113.5), "NYK": (117.0, 111.0), "PHX": (116.0, 113.0),
    "LAL": (116.2, 112.8), "LAC": (114.5, 110.8), "MIA": (114.0, 111.2),
    "IND": (119.5, 118.0), "SAC": (116.8, 115.0), "CLE": (115.5, 111.0),
    "NOP": (114.2, 112.0), "GSW": (115.0, 112.5), "HOU": (114.0, 110.5),
    "ORL": (112.5, 109.5), "MEM": (114.5, 112.0), "ATL": (116.0, 116.5),
    "CHI": (112.0, 115.5), "TOR": (113.0, 114.8), "BKN": (111.5, 115.5),
    "UTA": (113.5, 117.0), "SAS": (112.0, 114.5), "CHA": (110.5, 116.0),
    "WAS": (110.0, 118.5), "DET": (109.5, 115.0), "POR": (109.0, 116.5)
}

def obtener_ratings(nombre_equipo: str):
    abbr = nombre_equipo[:3].upper()
    return EQUIPOS_RATINGS.get(abbr, (114.5, 114.5))

def simular_partido_nba(
    local: str,
    visitante: str,
    c_ml_loc: float,
    c_ml_vis: float,
    l_spread_loc: float,
    c_spread_loc: float,
    l_spread_vis: float,
    c_spread_vis: float,
    l_total: float,
    c_over: float,
    c_under: float,
    iteraciones: int = 10000
):
    """
    Simulación Monte Carlo Calibrada para la NBA.
    Ajusta proyecciones con ritmos de juego reales e incrementa precisión en Totales.
    """
    off_loc, def_loc = obtener_ratings(local)
    off_vis, def_vis = obtener_ratings(visitante)

    # Ventaja de Localía típica en NBA (+2.4 puntos)
    ventaja_localia = 2.4
    pace_estimado = PACE_LIGA

    # Puntos esperados refinados
    pts_esperados_loc = ((off_loc * def_vis) / OFF_EFF_LIGA) * (pace_estimado / 100.0) + ventaja_localia
    pts_esperados_vis = ((off_vis * def_loc) / OFF_EFF_LIGA) * (pace_estimado / 100.0)

    wins_loc = 0
    wins_vis = 0
    covers_spread_loc = 0
    covers_spread_vis = 0
    overs = 0
    unders = 0

    # Desviación estándar ajustada para baloncesto competitivo
    std_dev = 9.8 

    for _ in range(iteraciones):
        sim_pts_loc = random.gauss(pts_esperados_loc, std_dev)
        sim_pts_vis = random.gauss(pts_esperados_vis, std_dev)

        # Moneyline
        if sim_pts_loc > sim_pts_vis:
            wins_loc += 1
        else:
            wins_vis += 1

        # Point Spread
        if (sim_pts_loc + l_spread_loc) > sim_pts_vis:
            covers_spread_loc += 1
        elif (sim_pts_vis + l_spread_vis) > sim_pts_loc:
            covers_spread_vis += 1

        # Totales Over/Under
        total_sim = sim_pts_loc + sim_pts_vis
        if total_sim > l_total:
            overs += 1
        else:
            unders += 1

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)

    prob_spread_loc = round((covers_spread_loc / iteraciones) * 100, 1)
    prob_spread_vis = round((covers_spread_vis / iteraciones) * 100, 1)

    prob_over = round((overs / iteraciones) * 100, 1)
    prob_under = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": local[:3].upper(),
        "equipo_visitante_abbr": visitante[:3].upper(),
        "proyeccion_puntos": f"{round(pts_esperados_loc, 1)} - {round(pts_esperados_vis, 1)}",
        "total_puntos_proyectado": round(pts_esperados_loc + pts_esperados_vis, 1),
        "ml_local": {"prob": prob_ml_loc, "cuota_justa": round(100 / max(prob_ml_loc, 0.1), 2)},
        "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": round(100 / max(prob_ml_vis, 0.1), 2)},
        "spread_local": {"linea": l_spread_loc, "prob": prob_spread_loc, "cuota_justa": round(100 / max(prob_spread_loc, 0.1), 2)},
        "spread_visitante": {"linea": l_spread_vis, "prob": prob_spread_vis, "cuota_justa": round(100 / max(prob_spread_vis, 0.1), 2)},
        "total_over": {"linea": l_total, "prob": prob_over, "cuota_justa": round(100 / max(prob_over, 0.1), 2)},
        "total_under": {"linea": l_total, "prob": prob_under, "cuota_justa": round(100 / max(prob_under, 0.1), 2)},
        "resumen_explicado": f"DUNK-IA ejecutó 10,000 simulaciones calibradas con un ritmo de {pace_estimado} posesiones y eficiencias ofensivas de la liga actual."
    }
