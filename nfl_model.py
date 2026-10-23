import random
import math

# Mapeo exacto de la NFL
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

# Ratings EPA/Drive y Puntos Eficiencia
EQUIPOS_NFL = {
    "KC": (27.5, 18.2), "SF": (26.8, 19.5), "BAL": (28.1, 20.0), "BUF": (26.5, 21.0),
    "PHI": (25.5, 20.5), "DET": (27.0, 22.5), "DAL": (25.0, 21.5), "MIA": (24.8, 23.0),
    "GB": (24.0, 21.0), "HOU": (23.5, 20.8), "CIN": (24.5, 22.8), "LA": (23.8, 22.0),
    "DEFAULT": (22.0, 22.0)
}

def calibrar_probabilidad(prob_mc: float, cuota: float, peso_mc: float = 0.20) -> float:
    if not cuota or cuota <= 1.0:
        return round(prob_mc, 1)
    prob_impl = (1.0 / cuota) * 100.0
    return round((prob_mc * peso_mc) + (prob_impl * (1.0 - peso_mc)), 1)

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
    iteraciones: int = 10000
):
    abbr_loc = MAPEO_NFL.get(local, local[:3].upper())
    abbr_vis = MAPEO_NFL.get(visitante, visitante[:3].upper())

    pts_off_loc, pts_def_loc = EQUIPOS_NFL.get(abbr_loc, EQUIPOS_NFL["DEFAULT"])
    pts_off_vis, pts_def_vis = EQUIPOS_NFL.get(abbr_vis, EQUIPOS_NFL["DEFAULT"])

    ventaja_localia = 2.0
    pts_esperados_loc = ((pts_off_loc + pts_def_vis) / 2.0) + (ventaja_localia / 2.0)
    pts_esperados_vis = ((pts_off_vis + pts_def_loc) / 2.0) - (ventaja_localia / 2.0)

    wins_loc, wins_vis = 0, 0
    covers_sp_loc, covers_sp_vis = 0, 0
    overs, unders = 0, 0

    std_dev = 13.5 

    for _ in range(iteraciones):
        sim_pts_loc = random.gauss(pts_esperados_loc, std_dev)
        sim_pts_vis = random.gauss(pts_esperados_vis, std_dev)

        if sim_pts_loc > sim_pts_vis: wins_loc += 1
        else: wins_vis += 1

        if (sim_pts_loc + l_spread_loc) > sim_pts_vis: covers_sp_loc += 1
        if (sim_pts_vis + l_spread_vis) > sim_pts_loc: covers_sp_vis += 1

        total_sim = sim_pts_loc + sim_pts_vis
        if total_sim > l_total: overs += 1
        else: unders += 1

    prob_ml_loc = calibrar_probabilidad((wins_loc / iteraciones) * 100, c_ml_loc)
    prob_ml_vis = calibrar_probabilidad((wins_vis / iteraciones) * 100, c_ml_vis)
    prob_sp_loc = calibrar_probabilidad((covers_sp_loc / iteraciones) * 100, c_spread_loc)
    prob_sp_vis = calibrar_probabilidad((covers_sp_vis / iteraciones) * 100, c_spread_vis)
    prob_over   = calibrar_probabilidad((overs / iteraciones) * 100, c_over)
    prob_under  = calibrar_probabilidad((unders / iteraciones) * 100, c_under)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_puntos": f"{round(pts_esperados_loc, 1)} - {round(pts_esperados_vis, 1)}",
        "total_puntos_proyectado": round(pts_esperados_loc + pts_esperados_vis, 1),
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "spread_local": {"linea": l_spread_loc, "prob": prob_sp_loc},
        "spread_visitante": {"linea": l_spread_vis, "prob": prob_sp_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": f"BLITZ-IA ejecutó 10,000 simulaciones para {abbr_loc} vs {abbr_vis}."
    }
