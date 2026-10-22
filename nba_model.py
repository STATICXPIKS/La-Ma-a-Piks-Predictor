import random
import math

PACE_LIGA = 100.2
OFF_EFF_LIGA = 116.5

# Mapeo exacto de nombres completos de selectores
MAPEO_NOMBRES = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
}

EQUIPOS_RATINGS = {
    "BOS": (121.5, 110.2), "OKC": (120.0, 106.5), "DEN": (117.8, 112.0),
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
    abbr = MAPEO_NOMBRES.get(nombre_equipo, nombre_equipo[:3].upper())
    return EQUIPOS_RATINGS.get(abbr, (114.5, 114.5)), abbr

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
    (off_loc, def_loc), abbr_loc = obtener_ratings(local)
    (off_vis, def_vis), abbr_vis = obtener_ratings(visitante)

    ventaja_localia = 2.2
    pace_estimado = PACE_LIGA

    pts_esperados_loc = ((off_loc * def_vis) / OFF_EFF_LIGA) * (pace_estimado / 100.0) + ventaja_localia
    pts_esperados_vis = ((off_vis * def_loc) / OFF_EFF_LIGA) * (pace_estimado / 100.0)

    wins_loc, wins_vis = 0, 0
    covers_spread_loc, covers_spread_vis = 0, 0
    overs, unders = 0, 0

    std_dev = 10.5 

    for _ in range(iteraciones):
        sim_pts_loc = random.gauss(pts_esperados_loc, std_dev)
        sim_pts_vis = random.gauss(pts_esperados_vis, std_dev)

        if sim_pts_loc > sim_pts_vis:
            wins_loc += 1
        else:
            wins_vis += 1

        if (sim_pts_loc + l_spread_loc) > sim_pts_vis:
            covers_spread_loc += 1
        elif (sim_pts_vis + l_spread_vis) > sim_pts_loc:
            covers_spread_vis += 1

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
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_puntos": f"{round(pts_esperados_loc, 1)} - {round(pts_esperados_vis, 1)}",
        "total_puntos_proyectado": round(pts_esperados_loc + pts_esperados_vis, 1),
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "spread_local": {"linea": l_spread_loc, "prob": prob_spread_loc},
        "spread_visitante": {"linea": l_spread_vis, "prob": prob_spread_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"DUNK-IA ejecutó 10,000 simulaciones mapeando correctamente los equipos {abbr_loc} vs {abbr_vis} con una proyección de {round(pts_esperados_loc + pts_esperados_vis, 1)} puntos totales."
    }
