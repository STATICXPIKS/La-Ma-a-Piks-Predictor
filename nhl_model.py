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

# =========================================================
# CONECTOR A APIs GRATUITAS (NHL OFFICIAL & ESPN)
# =========================================================
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

    # 1. Consulta Estadísticas Recientes vía API Oficial de la NHL
    try:
        url_nhl = f"https://api-web.nhle.com/v1/club-stats/{abbr}/now"
        r = requests.get(url_nhl, timeout=4)
        if r.status_code == 200:
            data = r.json()
            skaters = data.get("skaters", [])
            goalies = data.get("goalies", [])

            # Calcular SV% promedio del cuerpo de porteros
            if goalies:
                svs = [float(g.get("savePercentage", 0.910)) for g in goalies if float(g.get("savePercentage", 0)) > 0.850]
                if svs:
                    stats["sv_pct"] = round(sum(svs) / len(svs), 3)

            # Estimar volumen de tiros (SOG)
            if skaters:
                shots = [int(s.get("shots", 0)) for s in skaters]
                games = max([int(s.get("gamesPlayed", 1)) for s in skaters] or [1])
                tot_shots = sum(shots)
                stats["sog_f"] = round(max(24.0, min(40.0, tot_shots / max(1, games / 3.0))), 1)
    except Exception as e:
        print(f"⚠️ Aviso: Usando fallback API ESPN para {nombre_equipo}: {e}")

    # 2. Consulta Calendario y Detección de Fatiga B2B vía API ESPN
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

                            # Detección B2B: si jugó ayer
                            hoy = datetime.now()
                            ayer_str = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")
                            if ayer_str in fechas_partidos:
                                stats["b2b"] = True
                    break
    except Exception as e:
        print(f"⚠️ Error recuperando calendario para {nombre_equipo}: {e}")

    # Estimar Corsi% y Fenwick% basados en relación de xG Favor vs Contra
    rel_xg = stats["xg_f"] / max(1.0, (stats["xg_f"] + stats["xg_a"]))
    stats["corsi"] = round(rel_xg * 100, 1)
    stats["fenwick"] = round(rel_xg * 99.0, 1)

    return stats

# =========================================
# MOTOR MONTE CARLO Y POISSON MODIFICADO
# =========================================
def ejecutar_modelo_nhl_completo(
    loc_nombre, vis_nombre,
    cuota_ml_loc, cuota_ml_vis,
    linea_pl_loc, cuota_pl_loc, linea_pl_vis, cuota_pl_vis,
    linea_total, cuota_over, cuota_under,
    linea_sog, cuota_sog_over, cuota_sog_under
):
    print(f"🔄 Conectando a APIs públicas de la NHL para {loc_nombre} vs {vis_nombre}...")
    loc_st = obtener_estadisticas_nhl_api_gratis(loc_nombre)
    vis_st = obtener_estadisticas_nhl_api_gratis(vis_nombre)

    # 1. Factor Porteros (SV% y GSAX estimado)
    mod_goalie_loc = (PROMEDIO_LIGA_SV / vis_st["sv_pct"]) if vis_st["sv_pct"] > 0 else 1.0
    mod_goalie_vis = (PROMEDIO_LIGA_SV / loc_st["sv_pct"]) if loc_st["sv_pct"] > 0 else 1.0

    # 2. Factor Posesión (Corsi/Fenwick)
    mod_pos_loc = (loc_st["corsi"] / 50.0) * 0.5 + (loc_st["fenwick"] / 50.0) * 0.5
    mod_pos_vis = (vis_st["corsi"] / 50.0) * 0.5 + (vis_st["fenwick"] / 50.0) * 0.5

    # 3. Factor Fatiga B2B y HCA
    mod_rest_loc = 0.92 if loc_st["b2b"] else 1.0
    mod_rest_vis = 0.92 if vis_st["b2b"] else 1.0
    HCA_GOALS = 0.18

    # 4. Cálculo de xG Lambda Final
    lambda_loc = max(1.1, ((loc_st["xg_f"] + vis_st["xg_a"]) / 2.0) * mod_pos_loc * mod_goalie_loc * mod_rest_loc + HCA_GOALS)
    lambda_vis = max(1.1, ((vis_st["xg_f"] + loc_st["xg_a"]) / 2.0) * mod_pos_vis * mod_goalie_vis * mod_rest_vis)

    # 5. SIMULACIÓN MONTE CARLO (10,000 ITERACIONES)
    N_SIM = 10000
    sim_loc = np.random.poisson(lambda_loc, N_SIM)
    sim_vis = np.random.poisson(lambda_vis, N_SIM)

    # Desempate Overtime / Shootout
    empates = (sim_loc == sim_vis)
    ot_winners = np.random.rand(np.sum(empates)) < 0.52 # Ligero sesgo al local en OT
    sim_loc_final = sim_loc.copy()
    sim_vis_final = sim_vis.copy()
    sim_loc_final[empates] += ot_winners
    sim_vis_final[empates] += (~ot_winners)

    # CALCULOS DE MERCADOS
    # M1: Moneyline (ML)
    prob_ml_loc = round((np.sum(sim_loc_final > sim_vis_final) / N_SIM) * 100, 1)
    prob_ml_vis = round(100.0 - prob_ml_loc, 1)

    ev_ml_loc = round(prob_ml_loc - ((1.0 / float(cuota_ml_loc)) * 100), 1)
    ev_ml_vis = round(prob_ml_vis - ((1.0 / float(cuota_ml_vis)) * 100), 1)

    # M2: Totales (Over/Under)
    totales_sim = sim_loc + sim_vis
    l_tot = float(linea_total)
    prob_over = round((np.sum(totales_sim > l_tot) / N_SIM) * 100, 1)
    prob_under = round(100.0 - prob_over, 1)

    ev_over = round(prob_over - ((1.0 / float(cuota_over)) * 100), 1)
    ev_under = round(prob_under - ((1.0 / float(cuota_under)) * 100), 1)

    # M3: Puck Line (-1.5 / +1.5)
    dif_goles = sim_loc_final - sim_vis_final
    prob_pl_loc = round((np.sum(dif_goles > -float(linea_pl_loc)) / N_SIM) * 100, 1)
    prob_pl_vis = round((np.sum((-dif_goles) > -float(linea_pl_vis)) / N_SIM) * 100, 1)

    ev_pl_loc = round(prob_pl_loc - ((1.0 / float(cuota_pl_loc)) * 100), 1)
    ev_pl_vis = round(prob_pl_vis - ((1.0 / float(cuota_pl_vis)) * 100), 1)

    # M4: Props de Tiros a Gol (SOG)
    sog_proyectados = round((loc_st["sog_f"] + vis_st["sog_f"]) * (mod_pos_loc + mod_pos_vis) / 2.0, 1)
    prob_sog_over = round((1.0 - poisson.cdf(float(linea_sog), sog_proyectados)) * 100, 1)
    prob_sog_under = round(100.0 - prob_sog_over, 1)

    # SELECCIÓN DEL PICK CON MAYOR +EV
    opciones_ev = [
        ("ML Local", f"{loc_nombre} ML @ {cuota_ml_loc}", cuota_ml_loc, prob_ml_loc, ev_ml_loc),
        ("ML Visitante", f"{vis_nombre} ML @ {cuota_ml_vis}", cuota_ml_vis, prob_ml_vis, ev_ml_vis),
        ("Totales Over", f"OVER {l_tot} Goles @ {cuota_over}", cuota_over, prob_over, ev_over),
        ("Totales Under", f"UNDER {l_tot} Goles @ {cuota_under}", cuota_under, prob_under, ev_under),
        ("Puck Line Local", f"{loc_nombre} {linea_pl_loc:+g} @ {cuota_pl_loc}", cuota_pl_loc, prob_pl_loc, ev_pl_loc),
        ("Puck Line Visitante", f"{vis_nombre} {linea_pl_vis:+g} @ {cuota_pl_vis}", cuota_pl_vis, prob_pl_vis, ev_pl_vis)
    ]

    opciones_ev.sort(key=lambda x: x[4], reverse=True)
    best_pick = opciones_ev[0]

    # GUARDAR EN SUPABASE PARA DESPLIEGUE EN NETLIFY
    registro = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "deporte": "NHL",
        "modelo_nombre": "NASH IA",
        "equipo_local": loc_nombre,
        "logo_local": f"https://a.espncdn.com/i/teamlogos/nhl/500/{loc_st['abbr']}.png",
        "equipo_visitante": vis_nombre,
        "logo_visitante": f"https://a.espncdn.com/i/teamlogos/nhl/500/{vis_st['abbr']}.png",
        "pick_recomendado": best_pick[1],
        "cuota": float(best_pick[2]),
        "probabilidad": int(best_pick[3]),
        "ev_porcentaje": float(best_pick[4]),
        "estado": "PENDING"
    }

    try:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/picks", headers=HEADERS_SUPABASE, json=registro, timeout=5)
        if res.status_code in [200, 201]:
            print(f"✅ Predicción enviada a Supabase/Netlify: {best_pick[1]} (+{best_pick[4]}% EV)")
    except Exception as e:
        print(f"Error guardando en Supabase: {e}")

    return {
        "xG_Proyectados": f"{loc_nombre}: {lambda_loc:.2f} xG | {vis_nombre}: {lambda_vis:.2f} xG",
        "Moneyline": f"{loc_nombre}: {prob_ml_loc}% (EV: +{ev_ml_loc}%) | {vis_nombre}: {prob_ml_vis}% (EV: +{ev_ml_vis}%)",
        "Totales": f"OVER {l_tot}: {prob_over}% | UNDER {l_tot}: {prob_under}%",
        "PuckLine": f"{loc_nombre} {linea_pl_loc:+g}: {prob_pl_loc}% | {vis_nombre} {linea_pl_vis:+g}: {prob_pl_vis}%",
        "Tiros_SOG": f"Proyección: {sog_proyectados} SOG (Over {linea_sog}: {prob_sog_over}%)",
        "Pick_Mas_Valor": f"{best_pick[1]} (EV: +{best_pick[4]}%)"
    }

if __name__ == "__main__":
    res = ejecutar_modelo_nhl_completo(
        loc_nombre="Florida Panthers",
        vis_nombre="Edmonton Oilers",
        cuota_ml_loc=1.85, cuota_ml_vis=1.95,
        linea_pl_loc=-1.5, cuota_pl_loc=2.85, linea_pl_vis=1.5, cuota_pl_vis=1.45,
        linea_total=6.0, cuota_over=1.90, cuota_under=1.90,
        linea_sog=62.5, cuota_sog_over=1.85, cuota_sog_under=1.85
    )
    print("\n📊 RESULTADOS DEL MODELO EN VIVO:")
    for k, v in res.items():
        print(f"  • {k}: {v}")
