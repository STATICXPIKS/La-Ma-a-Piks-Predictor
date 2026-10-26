import math
import hashlib
import random

MAPEO_NFL = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
}

# Ratings de Eficiencia Ofensiva y Defensiva (Puntos promedio esperados)
EQUIPOS_NFL = {
    "KC": (28.2, 18.5), "SF": (27.0, 19.0), "BAL": (27.8, 19.5), "BUF": (26.5, 20.8),
    "DET": (27.5, 21.8), "PHI": (25.5, 20.2), "GB":  (24.5, 20.5), "HOU": (24.0, 20.8),
    "DAL": (25.0, 22.0), "CIN": (24.8, 22.5), "MIA": (24.0, 23.0), "LAR": (23.8, 22.2),
    "DEFAULT": (22.5, 22.5)
}

def simular_partido_nfl(
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
    abbr_loc = MAPEO_NFL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NFL.get(visitante, visitante[:3].upper())

    # Semilla fija determinista por duelo para evitar variación en reanálisis
    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_spread_loc}_{l_spread_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    pts_off_loc, pts_def_loc = EQUIPOS_NFL.get(abbr_loc, EQUIPOS_NFL["DEFAULT"])
    pts_off_vis, pts_def_vis = EQUIPOS_NFL.get(abbr_vis, EQUIPOS_NFL["DEFAULT"])

    ventaja_localia = 2.1
    pts_esperados_loc = round(((pts_off_loc + pts_def_vis) / 2.0) + (ventaja_localia / 2.0), 1)
    pts_esperados_vis = round(((pts_off_vis + pts_def_loc) / 2.0) - (ventaja_localia / 2.0), 1)
    total_esperado = round(pts_esperados_loc + pts_esperados_vis, 1)

    wins_loc, wins_vis = 0, 0
    covers_sp_loc, covers_sp_vis = 0, 0
    overs, unders = 0, 0

    std_dev = 13.8

    for _ in range(iteraciones):
        sim_pts_loc = rng.gauss(pts_esperados_loc, std_dev)
        sim_pts_vis = rng.gauss(pts_esperados_vis, std_dev)

        # En NFL no hay empates de temporada regular
        if sim_pts_loc == sim_pts_vis:
            if rng.random() < 0.52: sim_pts_loc += 3
            else: sim_pts_vis += 3

        if sim_pts_loc > sim_pts_vis: wins_loc += 1
        else: wins_vis += 1

        # Spread algebraicamente estricto con signos respetados
        if (sim_pts_loc + l_spread_loc) > sim_pts_vis: covers_sp_loc += 1
        if (sim_pts_vis + l_spread_vis) > sim_pts_loc: covers_sp_vis += 1

        tot_sim = sim_pts_loc + sim_pts_vis
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
        "resumen_explicado": f"BLITZ-IA ejecutó 25,000 iteraciones deterministas para {abbr_loc} ({pts_esperados_loc}) vs {abbr_vis} ({pts_esperados_vis}). Total esperado: {total_esperado} pts."
    }
