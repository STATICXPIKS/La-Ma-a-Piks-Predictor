import math
import hashlib
import random

PACE_LIGA = 100.2
OFF_EFF_LIGA = 116.5

MAPEO_NBA = {
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

# Ratings de Eficiencia Ofensiva y Defensiva por 100 posesiones
EQUIPOS_RATINGS = {
    "BOS": (122.5, 110.2), "OKC": (121.0, 108.5), "DEN": (118.8, 112.5),
    "MIN": (115.5, 109.0), "MIL": (118.5, 114.5), "NYK": (117.5, 112.0),
    "DAL": (118.0, 113.8), "PHI": (116.8, 112.5), "PHX": (116.2, 113.5),
    "LAL": (116.5, 113.2), "LAC": (115.0, 111.5), "MIA": (114.5, 111.8),
    "IND": (120.0, 118.5), "SAC": (117.0, 115.5), "CLE": (116.0, 111.0),
    "DEFAULT": (114.0, 114.0)
}

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
    iteraciones: int = 25000
):
    abbr_loc = MAPEO_NBA.get(local, local[:3].upper())
    abbr_vis = MAPEO_NBA.get(visitante, visitante[:3].upper())

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_spread_loc}_{l_spread_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    off_loc, def_loc = EQUIPOS_RATINGS.get(abbr_loc, EQUIPOS_RATINGS["DEFAULT"])
    off_vis, def_vis = EQUIPOS_RATINGS.get(abbr_vis, EQUIPOS_RATINGS["DEFAULT"])

    ventaja_cancha_pts = 2.4
    pts_esperados_loc = round((((off_loc + def_vis) / 2.0) * (PACE_LIGA / 100.0)) + (ventaja_cancha_pts / 2.0), 1)
    pts_esperados_vis = round((((off_vis + def_loc) / 2.0) * (PACE_LIGA / 100.0)) - (ventaja_cancha_pts / 2.0), 1)
    total_esperado = round(pts_esperados_loc + pts_esperados_vis, 1)

    wins_loc, wins_vis = 0, 0
    covers_sp_loc, covers_sp_vis = 0, 0
    overs, unders = 0, 0

    std_dev = 11.5

    for _ in range(iteraciones):
        p_loc = rng.gauss(pts_esperados_loc, std_dev)
        p_vis = rng.gauss(pts_esperados_vis, std_dev)

        if p_loc == p_vis:
            if rng.random() < 0.52: p_loc += 2
            else: p_vis += 2

        if p_loc > p_vis: wins_loc += 1
        else: wins_vis += 1

        if (p_loc + l_spread_loc) > p_vis: covers_sp_loc += 1
        if (p_vis + l_spread_vis) > p_loc: covers_sp_vis += 1

        tot_sim = p_loc + p_vis
        if tot_sim > l_total: overs += 1
        elif tot_sim < l_total: unders += 1
        else:
            overs += 0.5
            unders += 0.5

    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)
    prob_sp_loc = round((covers_sp_loc / iteraciones) * 100, 1)
    prob_sp_vis = round((covers_sp_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_puntos": f"{pts_esperados_loc} - {pts_esperados_vis}",
        "total_puntos_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "spread_local": {"linea": l_spread_loc, "prob": prob_sp_loc},
        "spread_visitante": {"linea": l_spread_vis, "prob": prob_sp_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"DUNK-IA procesó Pace ({PACE_LIGA}) y Eficiencia Of/Def para {abbr_loc} ({pts_esperados_loc}) vs {abbr_vis} ({pts_esperados_vis}). Total proyectado: {total_esperado} pts."
    }
