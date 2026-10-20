import os
import math
import requests
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import poisson

# =========================================================
# CONFIGURACIÓN DE SUPABASE
# =========================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

HEADERS_SUPABASE = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# MAPEO DE ABREVIATURAS OFICIALES DE LA NHL
NHL_TEAM_ABBRS = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI",
    "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

PROMEDIO_LIGA_GOLES = 3.05
PROMEDIO_LIGA_SOG = 30.5
PROMEDIO_LIGA_SV = 0.905

def obtener_estadisticas_nhl_api_gratis(nombre_equipo):
    abbr = NHL_TEAM_ABBRS.get(nombre_equipo, "FLA")
    stats = {
        "abbr": abbr.lower(),
        "xg_f": 3.20, "xg_a": 2.80,
        "sog_f": 31.0, "sog_a": 30.0,
        "corsi": 51.5, "fenwick": 51.0,
        "pp_pct": 22.0, "pk_pct": 81.0,
        "sv_pct": 0.910, "b2b": False
    }

    try:
        url_nhl = f"https://api-web.nhle.com/v1/club-stats/{abbr}/now"
        r = requests.get(url_nhl, timeout=4)
        if r.status_code == 200:
            data = r.json()
            skaters = data.get("skaters", [])
            goalies = data.get("goalies", [])

            if goalies:
                svs = [float(g.get("savePercentage", 0.910)) for g in goalies if float(g.get("savePercentage", 0)) > 0.850]
                if svs:
                    stats["sv_pct"] = round(sum(svs) / len(svs), 3)

            if skaters:
                shots = [int(s.get("shots", 0)) for s in skaters]
                games = max([int(s.get("gamesPlayed", 1)) for s in skaters] or [1])
                tot_shots = sum(shots)
                stats["sog_f"] = round(max(24.0, min(40.0, tot_shots / max(1, games / 3.0))), 1)
    except Exception as e:
        print(f"⚠️ Aviso API NHL para {nombre_equipo}: {e}")

    try:
        url_espn = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams"
        r_espn = requests.get(url_espn, timeout=4)
        if r_espn.status_code == 200:
            teams = r_espn.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
            for t in teams:
                t_info = t.get("team", {})
                if nombre_equipo.lower() in t_info.get("displayName", "").lower():
                    t_id = t_info.get("id")
                    if t_id:
                        r_sched = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{t_id}/schedule", timeout=3)
                        if r_sched.status_code == 200:
                            events = r_sched.json().get("events", [])
                            gf_list, gc_list = [], []
                            fechas_partidos = []

                            for ev in events[-6:]:
                                date_str = ev.get("date", "")[:10]
                                if date_str:
                                    fechas_partidos.append(date_str)

                                comps = ev.get("competitions", [])
                                if comps and comps[0].get("status", {}).get("type", {}).get("completed", False):
                                    for c in comps[0].get("competitors", []):
                                        if str(c.get("id")) == str(t_id):
                                            gf_list.append(float(c.get("score", {}).get("value", 3.0)))
                                        else:
                                            gc_list.append(float(c.get("score", {}).get("value", 3.0)))

                            if gf_list:
                                stats["xg_f"] = round(sum(gf_list) / len(gf_list), 2)
                            if gc_list:
                                stats["xg_a"] = round(sum(gc_list) / len(gc_list), 2)

                            hoy = datetime.now()
                            ayer_str = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")
                            if ayer_str in fechas_partidos:
                                stats["b2b"] = True
                    break
    except Exception as e:
        print(f"⚠️ Aviso API ESPN para {nombre_equipo}: {e}")

    rel_xg = stats["xg_f"] / max(1.0, (stats["xg_f"] + stats["xg_a"]))
    stats["corsi"] = round(rel_xg * 100, 1)
    stats["fenwick"] = round(rel_xg * 99.0, 1)

    return stats


def ejecutar_modelo_nhl_completo(
    loc_nombre, vis_nombre,
    cuota_ml_loc=1.85, cuota_ml_vis=1.95,
    linea_pl_loc=-1.5, cuota_pl_loc=2.85, linea_pl_vis=1.5, cuota_pl_vis=1.45,
    linea_total=6.0, cuota_over=1.90, cuota_under=1.90,
    linea_sog=62.5, cuota_sog_over=1.85, cuota_sog_under=1.85
):
    print(f"🔄 Ejecutando modelo NHL para {loc_nombre} vs {vis_nombre}...")
    loc_st = obtener_estadisticas_nhl_api_gratis(loc_nombre)
    vis_st = obtener_estadisticas_nhl_api_gratis(vis_nombre)

    mod_goalie_loc = (PROMEDIO_LIGA_SV / vis_st["sv_pct"]) if vis_st["sv_pct"] > 0 else 1.0
    mod_goalie_vis = (PROMEDIO_LIGA_SV / loc_st["sv_pct"]) if loc_st["sv_pct"] > 0 else 1.0

    mod_pos_loc = (loc_st["corsi"] / 50.0) * 0.5 + (loc_st["fenwick"] / 50.0) * 0.5
    mod_pos_vis = (vis_st["corsi"] / 50.0) * 0.5 + (vis_st["fenwick"] / 50.0) * 0.5

    mod_rest_loc = 0.92 if loc_st["b2b"] else 1.0
    mod_rest_vis = 0.92 if vis_st["b2b"] else 1.0
    HCA_GOALS = 0.18

    lambda_loc = max(1.1, ((loc_st["xg_f"] + vis_st["xg_a"]) / 2.0) * mod_pos_loc * mod_goalie_loc * mod_rest_loc + HCA_GOALS)
    lambda_vis = max(1.1, ((vis_st["xg_f"] + loc_st["xg_a"]) / 2.0) * mod_pos_vis * mod_goalie_vis * mod_rest_vis)

    N_SIM = 10000
    sim_loc = np.random.poisson(lambda_loc, N_SIM)
    sim_vis = np.random.poisson(lambda_vis, N_SIM)

    empates = (sim_loc == sim_vis)
    ot_winners = np.random.rand(np.sum(empates)) < 0.52
    sim_loc_final = sim_loc.copy()
    sim_vis_final = sim_vis.copy()
    sim_loc_final[empates] += ot_winners
    sim_vis_final[empates] += (~ot_winners)

    # Probabilidades reales de todos los mercados
    prob_ml_loc = round((np.sum(sim_loc_final > sim_vis_final) / N_SIM) * 100, 1)
    prob_ml_vis = round(100.0 - prob_ml_loc, 1)
    ev_ml_loc = round(prob_ml_loc - ((1.0 / float(cuota_ml_loc)) * 100), 1)
    ev_ml_vis = round(prob_ml_vis - ((1.0 / float(cuota_ml_vis)) * 100), 1)

    totales_sim = sim_loc + sim_vis
    l_tot = float(linea_total)
    prob_over = round((np.sum(totales_sim > l_tot) / N_SIM) * 100, 1)
    prob_under = round(100.0 - prob_over, 1)
    ev_over = round(prob_over - ((1.0 / float(cuota_over)) * 100), 1)
    ev_under = round(prob_under - ((1.0 / float(cuota_under)) * 100), 1)

    dif_goles = sim_loc_final - sim_vis_final
    prob_pl_loc = round((np.sum(dif_goles > -float(linea_pl_loc)) / N_SIM) * 100, 1)
    prob_pl_vis = round((np.sum((-dif_goles) > -float(linea_pl_vis)) / N_SIM) * 100, 1)
    ev_pl_loc = round(prob_pl_loc - ((1.0 / float(cuota_pl_loc)) * 100), 1)
    ev_pl_vis = round(prob_pl_vis - ((1.0 / float(cuota_pl_vis)) * 100), 1)

    # Cuotas justas
    cuota_j_ml_loc = round(100.0 / prob_ml_loc, 2) if prob_ml_loc > 0 else 2.0
    cuota_j_ml_vis = round(100.0 / prob_ml_vis, 2) if prob_ml_vis > 0 else 2.0
    cuota_j_pl_loc = round(100.0 / prob_pl_loc, 2) if prob_pl_loc > 0 else 2.0
    cuota_j_pl_vis = round(100.0 / prob_pl_vis, 2) if prob_pl_vis > 0 else 2.0
    cuota_j_over = round(100.0 / prob_over, 2) if prob_over > 0 else 2.0
    cuota_j_under = round(100.0 / prob_under, 2) if prob_under > 0 else 2.0

    # =========================================================
    # EVALUACIÓN DINÁMICA DE LOS 6 MERCADOS POR SU VALOR (+EV)
    # =========================================================
    todos_los_mercados = [
        {"nombre": f"{loc_nombre} ML @ {cuota_ml_loc}", "ev": ev_ml_loc, "tipo": "ML"},
        {"nombre": f"{vis_nombre} ML @ {cuota_ml_vis}", "ev": ev_ml_vis, "tipo": "ML"},
        {"nombre": f"{loc_nombre} {linea_pl_loc:+g} @ {cuota_pl_loc}", "ev": ev_pl_loc, "tipo": "PL"},
        {"nombre": f"{vis_nombre} {linea_pl_vis:+g} @ {cuota_pl_vis}", "ev": ev_pl_vis, "tipo": "PL"},
        {"nombre": f"OVER {l_tot} Goles @ {cuota_over}", "ev": ev_over, "tipo": "TOTAL"},
        {"nombre": f"UNDER {l_tot} Goles @ {cuota_under}", "ev": ev_under, "tipo": "TOTAL"}
    ]

    # Ordenar estrictamente de mayor a menor según el % de EV
    todos_los_mercados.sort(key=lambda x: x["ev"], reverse=True)

    # El de mayor EV se asigna a BET 🔥
    top_1 = todos_los_mercados[0]
    bet_principal = top_1["nombre"]
    bet_ev = f"{'+' if top_1['ev'] >= 0 else ''}{top_1['ev']}%"

    # El segundo de mayor EV se asigna a MAYBE ⚡
    top_2 = todos_los_mercados[1]
    maybe_principal = top_2["nombre"]
    maybe_ev = f"{'+' if top_2['ev'] >= 0 else ''}{top_2['ev']}%"

    resumen_texto = f"{loc_nombre} vs {vis_nombre}: Proyección de {lambda_loc:.2f} a {lambda_vis:.2f} goles (Total proyectado: {lambda_loc + lambda_vis:.2f}). La mejor relación de valor cuantificada por FROST-IA enfoca la apuesta principal en {bet_principal}."

    return {
        "equipo_local_abbr": loc_st["abbr"].upper(),
        "equipo_visitante_abbr": vis_st["abbr"].upper(),
        "proyeccion_goles": f"{lambda_loc:.2f} - {lambda_vis:.2f}",
        "total_goles_proyectado": round(lambda_loc + lambda_vis, 2),
        "bet_fire": bet_principal,
        "bet_ev": bet_ev,
        "maybe_lightning": maybe_principal,
        "maybe_ev": maybe_ev,
        "ml_local": {"prob": prob_ml_loc, "cuota_justa": cuota_j_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": cuota_j_ml_vis},
        "pl_local": {"linea": linea_pl_loc, "prob": prob_pl_loc, "cuota_justa": cuota_j_pl_loc},
        "pl_visitante": {"linea": linea_pl_vis, "prob": prob_pl_vis, "cuota_justa": cuota_j_pl_vis},
        "total_over": {"linea": l_tot, "prob": prob_over, "cuota_justa": cuota_j_over},
        "total_under": {"linea": l_tot, "prob": prob_under, "cuota_justa": cuota_j_under},
        "resumen_explicado": resumen_texto
    }
