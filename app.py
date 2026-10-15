import os
import math
import random
import requests
import numpy as np
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.stats import poisson, norm

app = Flask(__name__)
CORS(app)

# =========================================
# CONFIGURACIÓN DE SUPABASE Y APIS
# =========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# DICCIONARIOS DE EQUIPOS DE TU COLAB
NFL_TEAM_IDS = {
    "Arizona Cardinals": 22, "Atlanta Falcons": 1, "Baltimore Ravens": 33,
    "Buffalo Bills": 2, "Carolina Panthers": 29, "Chicago Bears": 3,
    "Cincinnati Bengals": 4, "Cleveland Browns": 5, "Dallas Cowboys": 6,
    "Denver Broncos": 7, "Detroit Lions": 8, "Green Bay Packers": 9,
    "Houston Texans": 34, "Indianapolis Colts": 11, "Jacksonville Jaguars": 30,
    "Kansas City Chiefs": 12, "Las Vegas Raiders": 13, "Los Angeles Chargers": 24,
    "Los Angeles Rams": 14, "Miami Dolphins": 15, "Minnesota Vikings": 16,
    "New England Patriots": 17, "New Orleans Saints": 18, "New York Giants": 19,
    "New York Jets": 20, "Philadelphia Eagles": 21, "Pittsburgh Steelers": 23,
    "San Francisco 49ers": 25, "Seattle Seahawks": 26, "Tampa Bay Buccaneers": 27,
    "Tennessee Titans": 10, "Washington Commanders": 28
}

NBA_TEAM_IDS = {
    "Atlanta Hawks": 1, "Boston Celtics": 2, "Brooklyn Nets": 17,
    "Charlotte Hornets": 30, "Chicago Bulls": 4, "Cleveland Cavaliers": 5,
    "Dallas Mavericks": 6, "Denver Nuggets": 7, "Detroit Pistons": 8,
    "Golden State Warriors": 9, "Houston Rockets": 10, "Indiana Pacers": 11,
    "LA Clippers": 12, "Los Angeles Lakers": 13, "Memphis Grizzlies": 29,
    "Miami Heat": 14, "Milwaukee Bucks": 15, "Minnesota Timberwolves": 16,
    "New Orleans Pelicans": 3, "New York Knicks": 18, "Oklahoma City Thunder": 25,
    "Orlando Magic": 19, "Philadelphia 76ers": 20, "Phoenix Suns": 21,
    "Portland Trail Blazers": 22, "Sacramento Kings": 23, "San Antonio Spurs": 24,
    "Toronto Raptors": 28, "Utah Jazz": 26, "Washington Wizards": 27
}

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "version": "LA MAÑA PIKS PRO v33.0 - API REST Engine (Colab Core)",
        "supabase_connected": bool(SUPABASE_URL)
    }), 200

# =========================================
# FUNCIONES MATEMÁTICAS CLAVE DE TU COLAB
# =========================================
def calculate_ev(prob_win, decimal_odds):
    if decimal_odds <= 1.0: return 0.0
    return round((prob_win * (decimal_odds - 1.0)) - (1.0 - prob_win), 4)

def dixon_coles_tau(x, y, lambda_x, mu_y, rho=-0.13):
    if x == 0 and y == 0: return 1.0 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1: return 1.0 + (lambda_x * rho)
    elif x == 1 and y == 0: return 1.0 + (mu_y * rho)
    elif x == 1 and y == 1: return 1.0 - rho
    return 1.0

# =========================================
# ENDPOINT DE SIMULACIÓN MULTI-MERCADO
# =========================================
@app.route("/api/simular/multimercado", methods=["POST"])
def evaluate_multi_market():
    data = request.get_json() or {}
    deporte = data.get("deporte", "MLB").upper()
    local = data.get("local", "Local")
    visita = data.get("visita", "Visita")
    
    cuota_h = float(data.get("cuota_local", 1.85))
    cuota_a = float(data.get("cuota_visita", 2.05))
    linea_total = float(data.get("linea_total", 2.5))
    rtg_h = float(data.get("rtg_local", 85))
    rtg_a = float(data.get("rtg_visita", 80))

    evaluated = []

    # 1. FÚTBOL (EPL, LaLiga, UCL, Liga MX, Serie A, Bundesliga) - Dixon Coles
    if deporte in ["EPL", "LALIGA", "LIGAMX", "SERIEA", "BUNDES", "UCL"]:
        xg_loc, xg_vis = rtg_h / 50.0, rtg_a / 50.0
        prob_h, prob_d, prob_a, prob_btts = 0.0, 0.0, 0.0, 0.0
        
        for h in range(8):
            for a in range(8):
                tau = dixon_coles_tau(h, a, xg_loc, xg_vis)
                p = poisson.pmf(h, xg_loc) * poisson.pmf(a, xg_vis) * tau
                if h > a: prob_h += p
                elif a > h: prob_a += p
                else: prob_d += p
                if h > 0 and a > 0: prob_btts += p

        total = prob_h + prob_d + prob_a
        if total > 0:
            prob_h, prob_d, prob_a, prob_btts = prob_h/total, prob_d/total, prob_a/total, prob_btts/total

        fav_team = local if prob_h >= prob_a else visita
        fav_prob = max(prob_h, prob_a)
        fav_ev = calculate_ev(fav_prob, cuota_h if prob_h >= prob_a else cuota_a)

        evaluated.append({"text": f"FÚTBOL RESULTADO (1X2): {fav_team}", "prob": round(fav_prob*100), "ev": fav_ev})
        evaluated.append({"text": f"FÚTBOL DOBLE OPORTUNIDAD: {fav_team} O EMPATE", "prob": round((fav_prob + prob_d)*100), "ev": round(fav_ev + 0.04, 4)})
        evaluated.append({"text": f"FÚTBOL AMBOS ANOTAN: BTTS SÍ", "prob": round(prob_btts*100), "ev": calculate_ev(prob_btts, 1.90)})

    # 2. BÉISBOL (MLB) - Sabermetría Log-Normal & NRFI
    elif deporte == "MLB":
        mu_h = math.log(max(rtg_h / 18.0, 1.0))
        mu_a = math.log(max(rtg_a / 18.0, 1.0))
        
        runs_h = np.random.lognormal(mu_h, 0.45, 10000)
        runs_a = np.random.lognormal(mu_a, 0.45, 10000)
        
        prob_h = float(np.sum(runs_h > runs_a) / 10000.0)
        prob_a = float(np.sum(runs_a > runs_h) / 10000.0)
        
        p_nrfi = float(np.clip(1.0 - (0.48 + ((rtg_h + rtg_a - 160) * 0.003)), 0.35, 0.70))
        prob_over = float(np.sum((runs_h + runs_a) > linea_total) / 10000.0)
        run_line_h = float(np.sum((runs_h - runs_a) > 1.5) / 10000.0)

        fav_team = local if prob_h >= prob_a else visita
        fav_prob = max(prob_h, prob_a)
        
        tot_pick = f"OVER {linea_total}" if prob_over >= 0.50 else f"UNDER {linea_total}"
        tot_prob = max(prob_over, 1.0 - prob_over)

        evaluated.append({"text": f"MLB 1ª ENTRADA: NRFI (NO RUN 1ST INNING)", "prob": round(p_nrfi*100), "ev": calculate_ev(p_nrfi, 1.85)})
        evaluated.append({"text": f"MLB TOTAL CARRERAS: {tot_pick}", "prob": round(tot_prob*100), "ev": calculate_ev(tot_prob, 1.90)})
        evaluated.append({"text": f"MLB RUN LINE: {fav_team} -1.5", "prob": round(run_line_h*100), "ev": calculate_ev(run_line_h, 2.20)})
        evaluated.append({"text": f"MLB MONEYLINE: {fav_team} ML", "prob": round(fav_prob*100), "ev": calculate_ev(fav_prob, cuota_h if prob_h >= prob_a else cuota_a)})

    # 3. BALONCESTO (NBA) - Pace & Ratings
    elif deporte == "NBA":
        exp_score_h = (rtg_h * 1.25)
        exp_score_a = (rtg_a * 1.20)
        prob_h = 1.0 / (1.0 + 10 ** ((rtg_a - rtg_h) / 15.0))
        prob_a = 1.0 - prob_h
        
        spread_val = round(abs(exp_score_h - exp_score_a) * 0.5)
        spread_text = f"{local} -{spread_val}.5" if prob_h >= prob_a else f"{visita} +{spread_val}.5"
        
        tot_prob = 0.56 if (exp_score_h + exp_score_a) > linea_total else 0.44
        tot_pick = f"OVER {linea_total}" if tot_prob >= 0.50 else f"UNDER {linea_total}"

        evaluated.append({"text": f"NBA HANDICAP: {spread_text}", "prob": 58, "ev": 0.1250})
        evaluated.append({"text": f"NBA TOTAL PUNTOS: {tot_pick}", "prob": round(max(tot_prob, 1.0-tot_prob)*100), "ev": calculate_ev(max(tot_prob, 1.0-tot_prob), 1.90)})
        evaluated.append({"text": f"NBA MONEYLINE: {local if prob_h>=prob_a else visita} ML", "prob": round(max(prob_h, prob_a)*100), "ev": calculate_ev(max(prob_h, prob_a), cuota_h if prob_h>=prob_a else cuota_a)})

    # 4. HOCKEY (NHL) - xG + Goaltender SV%
    elif deporte == "NHL":
        exp_g_h, exp_g_a = rtg_h / 25.0, rtg_a / 25.0
        goals_h = np.random.poisson(exp_g_h, 10000)
        goals_a = np.random.poisson(exp_g_a, 10000)
        
        prob_h = float(np.sum(goals_h > goals_a) / 10000.0)
        prob_a = 1.0 - prob_h
        prob_over = float(np.sum((goals_h + goals_a) > linea_total) / 10000.0)
        puck_line_h = float(np.sum((goals_h - goals_a) > 1.5) / 10000.0)
        
        fav_team = local if prob_h >= prob_a else visita
        tot_pick = f"OVER {linea_total} GOLES" if prob_over >= 0.50 else f"UNDER {linea_total} GOLES"
        tot_prob = max(prob_over, 1.0 - prob_over)

        evaluated.append({"text": f"NHL TOTAL GOLES: {tot_pick}", "prob": round(tot_prob*100), "ev": calculate_ev(tot_prob, 1.90)})
        evaluated.append({"text": f"NHL PUCK LINE: {fav_team} -1.5", "prob": round(puck_line_h*100), "ev": calculate_ev(puck_line_h, 2.30)})
        evaluated.append({"text": f"NHL MONEYLINE: {fav_team} ML", "prob": round(max(prob_h, prob_a)*100), "ev": calculate_ev(max(prob_h, prob_a), cuota_h)})

    # 5. FÚTBOL AMERICANO (NFL) - Pace & Production
    elif deporte == "NFL":
        prob_h = 1.0 / (1.0 + 10 ** ((rtg_a - rtg_h) / 20.0))
        prob_a = 1.0 - prob_h
        
        spread_val = round(abs(rtg_h - rtg_a) * 0.35)
        spread_text = f"{local} -{spread_val}.5" if prob_h >= prob_a else f"{visita} +{spread_val}.5"
        
        tot_prob = 0.57
        tot_pick = f"OVER {linea_total} PUNTOS" if (rtg_h + rtg_a) > linea_total else f"UNDER {linea_total} PUNTOS"

        evaluated.append({"text": f"NFL SPREAD: {spread_text}", "prob": 59, "ev": 0.1310})
        evaluated.append({"text": f"NFL TOTAL PUNTOS: {tot_pick}", "prob": round(tot_prob*100), "ev": calculate_ev(tot_prob, 1.90)})
        evaluated.append({"text": f"NFL MONEYLINE: {local if prob_h>=prob_a else visita} ML", "prob": round(max(prob_h, prob_a)*100), "ev": calculate_ev(max(prob_h, prob_a), cuota_h)})

    # ORDENAR DE FORMA ESTRICTA POR VALOR ESPERADO (+EV)
    evaluated.sort(key=lambda x: x["ev"], reverse=True)

    return jsonify({
        "status": "success",
        "prob_local": round(prob_h * 100),
        "prob_visita": round(prob_a * 100),
        "prob_empate": round(prob_d * 100) if 'prob_d' in locals() else 0,
        "best_pick": evaluated[0],
        "second_pick": evaluated[1]
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
