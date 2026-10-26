import math
import hashlib
import random

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

# Base de Ritmo (Pace) y Eficiencia por 100 posesiones + Elo: (Pace, OffRating, DefRating, Elo)
EQUIPOS_NBA_STATS = {
    "BOS": (100.8, 122.8, 110.5, 1680),
    "OKC": (101.5, 121.2, 108.8, 1665),
    "DEN": (99.2,  119.5, 112.8, 1640),
    "MIN": (98.5,  116.0, 109.2, 1625),
    "NYK": (97.8,  118.2, 112.5, 1610),
    "DAL": (100.5, 118.8, 114.0, 1620),
    "MIL": (101.2, 118.5, 115.2, 1605),
    "PHI": (99.0,  117.0, 113.0, 1590),
    "LAL": (101.0, 116.8, 113.8, 1585),
    "DEFAULT": (100.0, 115.0, 115.0, 1500)
}

def simular_partido_nba(local, visitante, c_ml_loc, c_ml_vis, l_spread_loc, c_spread_loc, l_spread_vis, c_spread_vis, l_total, c_over, c_under, iteraciones=10000):
    abbr_loc = MAPEO_NBA.get(local, local[:3].upper())
    abbr_vis = MAPEO_NBA.get(visitante, visitante[:3].upper())

    s_loc = EQUIPOS_NBA_STATS.get(abbr_loc, EQUIPOS_NBA_STATS["DEFAULT"])
    s_vis = EQUIPOS_NBA_STATS.get(abbr_vis, EQUIPOS_NBA_STATS["DEFAULT"])

    # Ritmo esperado del juego
    pace_esperado = (s_loc[0] + s_vis[0]) / 2.0

    # Rating ofensivo/defensivo cruzado
    eff_loc = (s_loc[1] + s_vis[2]) / 2.0
    eff_vis = (s_vis[1] + s_loc[2]) / 2.0

    # Elo Dinámico con localía (+60 Elo)
    elo_diff = (s_loc[3] + 60) - s_vis[3]
    prob_elo_loc = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))

    pts_esperados_loc = round((eff_loc * (pace_esperado / 100.0)) + 1.8, 1)
    pts_esperados_vis = round((eff_vis * (pace_esperado / 100.0)) - 1.8, 1)
    total_esperado = round(pts_esperados_loc + pts_esperados_vis, 1)

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_spread_loc}_{l_spread_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    wins_loc, wins_vis = 0, 0
    covers_sp_loc, covers_sp_vis = 0, 0
    overs, unders = 0, 0
    std_dev = 11.2

    for _ in range(iteraciones):
        p_loc = rng.gauss(pts_esperados_loc, std_dev)
        p_vis = rng.gauss(pts_esperados_vis, std_dev)

        if p_loc == p_vis:
            if rng.random() < prob_elo_loc: p_loc += 2
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
        "resumen_explicado": f"DUNK-IA: Monte Carlo (10,000 iteraciones). Modelo Posesión a Posesión (Pace {pace_esperado}) + Off/Def Rating + Elo ({s_loc[3]}/{s_vis[3]}). Proyección: {total_esperado} pts."
    }
