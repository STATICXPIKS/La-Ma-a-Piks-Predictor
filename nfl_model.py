import math
import random
import requests

# CONFIGURACIÓN DE SUPABASE
SUPABASE_URL = "https://tuywqyjsaubcxmbzxwlg.supabase.co"
SUPABASE_KEY = "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj"
HEADERS_SUPABASE = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# BASE DE DATOS DE EQUIPOS NFL (ABREVIATURA Y ELO BASE TEMPORADAS 2025-2027)
EQUIPOS_NFL = {
    "Arizona Cardinals": {"abbr": "ARI", "elo": 1450, "off_epa": 0.02, "def_epa": -0.04, "qb_factor": 1.0},
    "Atlanta Falcons": {"abbr": "ATL", "elo": 1510, "off_epa": 0.05, "def_epa": -0.01, "qb_factor": 1.0},
    "Baltimore Ravens": {"abbr": "BAL", "elo": 1620, "off_epa": 0.18, "def_epa": 0.08, "qb_factor": 1.15},
    "Buffalo Bills": {"abbr": "BUF", "elo": 1610, "off_epa": 0.16, "def_epa": 0.07, "qb_factor": 1.12},
    "Carolina Panthers": {"abbr": "CAR", "elo": 1380, "off_epa": -0.12, "def_epa": -0.10, "qb_factor": 0.90},
    "Chicago Bears": {"abbr": "CHI", "elo": 1480, "off_epa": 0.01, "def_epa": 0.02, "qb_factor": 0.98},
    "Cincinnati Bengals": {"abbr": "CIN", "elo": 1550, "off_epa": 0.12, "def_epa": -0.03, "qb_factor": 1.10},
    "Cleveland Browns": {"abbr": "CLE", "elo": 1490, "off_epa": -0.05, "def_epa": 0.11, "qb_factor": 0.95},
    "Dallas Cowboys": {"abbr": "DAL", "elo": 1540, "off_epa": 0.10, "def_epa": 0.03, "qb_factor": 1.05},
    "Denver Broncos": {"abbr": "DEN", "elo": 1470, "off_epa": -0.02, "def_epa": 0.04, "qb_factor": 0.96},
    "Detroit Lions": {"abbr": "DET", "elo": 1630, "off_epa": 0.19, "def_epa": 0.06, "qb_factor": 1.08},
    "Green Bay Packers": {"abbr": "GB", "elo": 1560, "off_epa": 0.11, "def_epa": 0.04, "qb_factor": 1.06},
    "Houston Texans": {"abbr": "HOU", "elo": 1570, "off_epa": 0.10, "def_epa": 0.09, "qb_factor": 1.07},
    "Indianapolis Colts": {"abbr": "IND", "elo": 1490, "off_epa": 0.03, "def_epa": -0.02, "qb_factor": 0.97},
    "Jacksonville Jaguars": {"abbr": "JAX", "elo": 1460, "off_epa": 0.00, "def_epa": -0.05, "qb_factor": 0.98},
    "Kansas City Chiefs": {"abbr": "KC", "elo": 1660, "off_epa": 0.17, "def_epa": 0.12, "qb_factor": 1.20},
    "Las Vegas Raiders": {"abbr": "LV", "elo": 1430, "off_epa": -0.06, "def_epa": -0.02, "qb_factor": 0.92},
    "Los Angeles Chargers": {"abbr": "LAC", "elo": 1520, "off_epa": 0.04, "def_epa": 0.05, "qb_factor": 1.04},
    "Los Angeles Rams": {"abbr": "LAR", "elo": 1530, "off_epa": 0.08, "def_epa": 0.01, "qb_factor": 1.05},
    "Miami Dolphins": {"abbr": "MIA", "elo": 1520, "off_epa": 0.13, "def_epa": -0.04, "qb_factor": 1.06},
    "Minnesota Vikings": {"abbr": "MIN", "elo": 1550, "off_epa": 0.09, "def_epa": 0.07, "qb_factor": 1.02},
    "New England Patriots": {"abbr": "NE", "elo": 1410, "off_epa": -0.10, "def_epa": 0.01, "qb_factor": 0.91},
    "New Orleans Saints": {"abbr": "NO", "elo": 1460, "off_epa": 0.02, "def_epa": -0.03, "qb_factor": 0.96},
    "New York Giants": {"abbr": "NYG", "elo": 1400, "off_epa": -0.09, "def_epa": -0.01, "qb_factor": 0.90},
    "New York Jets": {"abbr": "NYJ", "elo": 1470, "off_epa": -0.01, "def_epa": 0.08, "qb_factor": 0.99},
    "Philadelphia Eagles": {"abbr": "PHI", "elo": 1600, "off_epa": 0.14, "def_epa": 0.06, "qb_factor": 1.09},
    "Pittsburgh Steelers": {"abbr": "PIT", "elo": 1530, "off_epa": -0.01, "def_epa": 0.10, "qb_factor": 0.98},
    "San Francisco 49ers": {"abbr": "SF", "elo": 1610, "off_epa": 0.17, "def_epa": 0.05, "qb_factor": 1.08},
    "Seattle Seahawks": {"abbr": "SEA", "elo": 1500, "off_epa": 0.04, "def_epa": 0.01, "qb_factor": 1.00},
    "Tampa Bay Buccaneers": {"abbr": "TB", "elo": 1520, "off_epa": 0.07, "def_epa": 0.00, "qb_factor": 1.02},
    "Tennessee Titans": {"abbr": "TEN", "elo": 1420, "off_epa": -0.08, "def_epa": 0.01, "qb_factor": 0.91},
    "Washington Commanders": {"abbr": "WAS", "elo": 1540, "off_epa": 0.11, "def_epa": -0.02, "qb_factor": 1.05}
}

def obtener_clima_estadio_nfl():
    # Retorna factor de ajuste climático simulado/vía API (viento y temperatura)
    return {"viento_mph": 8.5, "factor_puntos": 0.98}

def simular_monte_carlo_nfl(loc, vis, factor_qb_loc=1.0, factor_qb_vis=1.0, iteraciones=10000):
    d_loc = EQUIPOS_NFL.get(loc, {"elo": 1500, "off_epa": 0.0, "def_epa": 0.0, "abbr": "LOC"})
    d_vis = EQUIPOS_NFL.get(vis, {"elo": 1500, "off_epa": 0.0, "def_epa": 0.0, "abbr": "VIS"})

    # Ventaja de localia en la NFL (~2.1 puntos)
    ventaja_casa = 2.1
    
    # Expectativa de puntos base en NFL (Promedio ~22.5 por equipo)
    base_puntos = 22.5
    
    exp_loc = base_puntos + (d_loc["off_epa"] * 18) - (d_vis["def_epa"] * 15) + (ventaja_casa / 2)
    exp_vis = base_puntos + (d_vis["off_epa"] * 18) - (d_loc["def_epa"] * 15) - (ventaja_casa / 2)

    exp_loc *= factor_qb_loc
    exp_vis *= factor_qb_vis

    wins_loc, wins_vis = 0, 0
    puntos_loc_total, puntos_vis_total = 0, 0

    for _ in range(iteraciones):
        pts_l = max(0, int(random.gauss(exp_loc, 10.5)))
        pts_v = max(0, int(random.gauss(exp_vis, 10.5)))
        
        if pts_l == pts_v:
            pts_l += random.choice([3, 6]) # Tiempo extra NFL
            
        if pts_l > pts_v:
            wins_loc += 1
        else:
            wins_vis += 1

        puntos_loc_total += pts_l
        puntos_vis_total += pts_v

    prob_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_vis = round((wins_vis / iteraciones) * 100, 1)
    
    prom_loc = round(puntos_loc_total / iteraciones, 2)
    prom_vis = round(puntos_vis_total / iteraciones, 2)

    return {
        "prob_loc": prob_loc,
        "prob_vis": prob_vis,
        "prom_loc": prom_loc,
        "prom_vis": prom_vis,
        "total_proyectado": round(prom_loc + prom_vis, 2),
        "spread_proyectado": round(prom_vis - prom_loc, 1),
        "abbr_loc": d_loc["abbr"],
        "abbr_vis": d_vis["abbr"]
    }

def ejecutar_modelo_nfl_completo(
    loc_nombre, vis_nombre,
    cuota_ml_loc=1.90, cuota_ml_vis=1.90,
    linea_spread_loc=-3.5, cuota_spread_loc=1.90,
    linea_spread_vis=3.5, cuota_spread_vis=1.90,
    linea_total=45.5, cuota_over=1.90, cuota_under=1.90
):
    sim = simular_monte_carlo_nfl(loc_nombre, vis_nombre)
    
    prob_ml_loc = sim["prob_loc"]
    prob_ml_vis = sim["prob_vis"]

    cj_ml_loc = round(100 / max(prob_ml_loc, 1), 2)
    cj_ml_vis = round(100 / max(prob_ml_vis, 1), 2)

    ev_ml_loc = round((prob_ml_loc / 100 * cuota_ml_loc - 1) * 100, 1)
    ev_ml_vis = round((prob_ml_vis / 100 * cuota_ml_vis - 1) * 100, 1)

    # Probabilidad estimada de Spread
    prob_spread_loc = round(50 + (sim["spread_proyectado"] - linea_spread_loc) * 3.5, 1)
    prob_spread_loc = max(10, min(90, prob_spread_loc))
    prob_spread_vis = round(100 - prob_spread_loc, 1)

    ev_spread_loc = round((prob_spread_loc / 100 * cuota_spread_loc - 1) * 100, 1)
    ev_spread_vis = round((prob_spread_vis / 100 * cuota_spread_vis - 1) * 100, 1)

    # Probabilidad estimada de Totales
    prob_over = round(50 + (sim["total_proyectado"] - linea_total) * 4.0, 1)
    prob_over = max(10, min(90, prob_over))
    prob_under = round(100 - prob_over, 1)

    ev_over = round((prob_over / 100 * cuota_over - 1) * 100, 1)
    ev_under = round((prob_under / 100 * cuota_under - 1) * 100, 1)

    # Evaluación de los 6 mercados para extraer BET y MAYBE
    candidatos = [
        {"desc": f"{loc_nombre} ML", "ev": ev_ml_loc, "cuota": cuota_ml_loc},
        {"desc": f"{vis_nombre} ML", "ev": ev_ml_vis, "cuota": cuota_ml_vis},
        {"desc": f"{loc_nombre} {linea_spread_loc:+}", "ev": ev_spread_loc, "cuota": cuota_spread_loc},
        {"desc": f"{vis_nombre} {linea_spread_vis:+}", "ev": ev_spread_vis, "cuota": cuota_spread_vis},
        {"desc": f"OVER {linea_total} Puntos", "ev": ev_over, "cuota": cuota_over},
        {"desc": f"UNDER {linea_total} Puntos", "ev": ev_under, "cuota": cuota_under}
    ]

    candidatos.sort(key=lambda x: x["ev"], reverse=True)

    bet_fire = f"{candidatos[0]['desc']} @ {candidatos[0]['cuota']}"
    bet_ev = f"+{candidatos[0]['ev']}%" if candidatos[0]['ev'] >= 0 else f"{candidatos[0]['ev']}%"

    maybe_lightning = f"{candidatos[1]['desc']} @ {candidatos[1]['cuota']}"
    maybe_ev = f"+{candidatos[1]['ev']}%" if candidatos[1]['ev'] >= 0 else f"{candidatos[1]['ev']}%"

    return {
        "deporte": "NFL",
        "modelo": "BLITZ-IA",
        "equipo_local_abbr": sim["abbr_loc"],
        "equipo_visitante_abbr": sim["abbr_vis"],
        "proyeccion_puntos": f"{sim['prom_loc']} - {sim['prom_vis']}",
        "total_puntos_proyectado": sim["total_proyectado"],
        "spread_proyectado": sim["spread_proyectado"],
        "bet_fire": bet_fire,
        "bet_ev": bet_ev,
        "maybe_lightning": maybe_lightning,
        "maybe_ev": maybe_ev,
        "ml_local": {"prob": prob_ml_loc, "cuota_justa": cj_ml_loc, "ev": ev_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": cj_ml_vis, "ev": ev_ml_vis},
        "spread_local": {"linea": linea_spread_loc, "prob": prob_spread_loc, "cuota_justa": round(100/prob_spread_loc, 2), "ev": ev_spread_loc},
        "spread_visitante": {"linea": linea_spread_vis, "prob": prob_spread_vis, "cuota_justa": round(100/prob_spread_vis, 2), "ev": ev_spread_vis},
        "total_over": {"linea": linea_total, "prob": prob_over, "cuota_justa": round(100/prob_over, 2), "ev": ev_over},
        "total_under": {"linea": linea_total, "prob": prob_under, "cuota_justa": round(100/prob_under, 2), "ev": ev_under},
        "resumen_explicado": f"{loc_nombre} vs {vis_nombre}: Proyección de {sim['prom_loc']} a {sim['prom_vis']} puntos. BLITZ-IA recomienda como selección principal {bet_fire} con valor esperado ({bet_ev} EV)."
    }
