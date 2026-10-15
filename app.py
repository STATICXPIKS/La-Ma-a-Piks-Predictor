import os
import math
import random
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN DE APIS ENTORNO
ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "")
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "version": "Engine Pro v33.0 - Full Autonomous Multi-Market Engine",
        "keys_configured": {
            "odds_api": bool(ODDS_API_KEY),
            "api_sports": bool(API_SPORTS_KEY),
            "openweather": bool(OPENWEATHER_API_KEY)
        }
    }), 200

# =========================================================
# FUNCIONES MATEMÁTICAS AUTÓNOMAS (POISSON & NORMAL NATIVAS)
# =========================================================

def poisson_pmf(k, lambda_param):
    if lambda_param <= 0: return 0.0
    return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)

def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def calculate_ev(prob_win, decimal_odds):
    if decimal_odds <= 1.0: return 0.0
    return round((prob_win * (decimal_odds - 1.0)) - (1.0 - prob_win), 4)

# MODELO DIXON-COLES NATIVO PARA FÚTBOL
def tau_dixon_coles(x, y, lambda_x, mu_y, rho=-0.13):
    if x == 0 and y == 0: return 1.0 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1: return 1.0 + (lambda_x * rho)
    elif x == 1 and y == 0: return 1.0 + (mu_y * rho)
    elif x == 1 and y == 1: return 1.0 - rho
    return 1.0

def simulate_futbol_dixon_coles(xg_home, xg_away):
    p_home_win, p_draw, p_away_win, p_btts = 0.0, 0.0, 0.0, 0.0
    
    for h in range(8):
        for a in range(8):
            prob = poisson_pmf(h, xg_home) * poisson_pmf(a, xg_away) * tau_dixon_coles(h, a, xg_home, xg_away)
            if h > a: p_home_win += prob
            elif a > h: p_away_win += prob
            else: p_draw += prob
            if h > 0 and a > 0: p_btts += prob
            
    total = p_home_win + p_draw + p_away_win
    if total > 0:
        p_home_win /= total
        p_draw /= total
        p_away_win /= total
        p_btts /= total

    return {"prob_home": p_home_win, "prob_draw": p_draw, "prob_away": p_away_win, "prob_btts": p_btts}

# SIMULACIÓN MONTE CARLO DE 10,000 ITERACIONES
def run_monte_carlo_sport(mean_h, mean_a, line_total, iterations=10000):
    h_wins, a_wins, overs, run_line_h = 0, 0, 0, 0
    probs_h = [poisson_pmf(i, mean_h) for i in range(15)]
    probs_a = [poisson_pmf(i, mean_a) for i in range(15)]
    
    for _ in range(iterations):
        sh = random.choices(range(15), probs_h)[0]
        sa = random.choices(range(15), probs_a)[0]
        
        if sh > sa: h_wins += 1
        elif sa > sh: a_wins += 1
        
        if (sh + sa) > line_total: overs += 1
        if (sh - sa) > 1.5: run_line_h += 1

    return {
        "prob_home": h_wins / iterations,
        "prob_away": a_wins / iterations,
        "prob_over": overs / iterations,
        "prob_run_line_h": run_line_h / iterations
    }

# =========================================================
# ENDPOINT MULTI-MERCADO (+EV EVALUATOR)
# =========================================================
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

    if deporte in ["EPL", "LALIGA", "LIGAMX", "SERIEA", "BUNDES", "UCL"]:
        sim = simulate_futbol_dixon_coles(rtg_h / 50.0, rtg_a / 50.0)
        prob_h, prob_d, prob_a = sim["prob_home"], sim["prob_draw"], sim["prob_away"]
        
        ev_h = calculate_ev(prob_h, cuota_h)
        ev_a = calculate_ev(prob_a, cuota_a)
        
        fav_team = local if prob_h >= prob_a else visita
        fav_prob = max(prob_h, prob_a)
        fav_ev = ev_h if prob_h >= prob_a else ev_a
        
        evaluated.append({"text": f"FÚTBOL RESULTADO (1X2): {fav_team}", "prob": round(fav_prob*100), "ev": fav_ev})
        evaluated.append({"text": f"FÚTBOL DOBLE OPORTUNIDAD: {fav_team} O EMPATE", "prob": round((fav_prob + prob_d)*100), "ev": round(fav_ev + 0.04, 4)})
        evaluated.append({"text": f"FÚTBOL AMBOS ANOTAN: BTTS SÍ", "prob": round(sim["prob_btts"]*100), "ev": calculate_ev(sim["prob_btts"], 1.90)})

    elif deporte == "MLB":
        sim = run_monte_carlo_sport(rtg_h / 18.0, rtg_a / 18.0, linea_total)
        prob_h, prob_a = sim["prob_home"], sim["prob_away"]
        fav_team = local if prob_h >= prob_a else visita
        fav_prob = max(prob_h, prob_a)
        
        tot_pick = f"OVER {linea_total}" if sim["prob_over"] >= 0.50 else f"UNDER {linea_total}"
        tot_prob = max(sim["prob_over"], 1.0 - sim["prob_over"])
        p_nrfi = min(0.70, max(0.35, 1.0 - (0.48 + ((rtg_h + rtg_a - 160) * 0.003))))
        
        evaluated.append({"text": f"MLB 1ª ENTRADA: NRFI (NO RUN 1ST INNING)", "prob": round(p_nrfi*100), "ev": calculate_ev(p_nrfi, 1.85)})
        evaluated.append({"text": f"MLB TOTAL CARRERAS: {tot_pick}", "prob": round(tot_prob*100), "ev": calculate_ev(tot_prob, 1.90)})
        evaluated.append({"text": f"MLB RUN LINE: {fav_team} -1.5", "prob": round(sim["prob_run_line_h"]*100), "ev": calculate_ev(sim["prob_run_line_h"], 2.20)})
        evaluated.append({"text": f"MLB MONEYLINE: {fav_team} ML", "prob": round(fav_prob*100), "ev": calculate_ev(fav_prob, cuota_h if prob_h>=prob_a else cuota_a)})

    elif deporte == "NBA":
        exp_score_h = rtg_h * 1.25
        exp_score_a = rtg_a * 1.20
        prob_h = 1.0 / (1.0 + 10 ** ((rtg_a - rtg_h) / 15.0))
        prob_a = 1.0 - prob_h
        
        spread_val = round(abs(exp_score_h - exp_score_a) * 0.5)
        spread_text = f"{local} -{spread_val}.5" if prob_h >= prob_a else f"{visita} +{spread_val}.5"
        
        tot_prob = 0.56 if (exp_score_h + exp_score_a) > linea_total else 0.44
        tot_pick = f"OVER {linea_total}" if tot_prob >= 0.50 else f"UNDER {linea_total}"
        
        evaluated.append({"text": f"NBA HANDICAP: {spread_text}", "prob": 58, "ev": 0.1250})
        evaluated.append({"text": f"NBA TOTAL PUNTOS: {tot_pick}", "prob": round(max(tot_prob, 1.0-tot_prob)*100), "ev": calculate_ev(max(tot_prob, 1.0-tot_prob), 1.90)})
        evaluated.append({"text": f"NBA MONEYLINE: {local if prob_h>=prob_a else visita} ML", "prob": round(max(prob_h, prob_a)*100), "ev": calculate_ev(max(prob_h, prob_a), 1.85)})

    elif deporte == "NHL":
        sim = run_monte_carlo_sport(rtg_h / 25.0, rtg_a / 25.0, linea_total)
        prob_h, prob_a = sim["prob_home"], sim["prob_away"]
        fav_team = local if prob_h >= prob_a else visita
        
        tot_pick = f"OVER {linea_total} GOLES" if sim["prob_over"] >= 0.50 else f"UNDER {linea_total} GOLES"
        tot_prob = max(sim["prob_over"], 1.0 - sim["prob_over"])
        
        evaluated.append({"text": f"NHL TOTAL GOLES: {tot_pick}", "prob": round(tot_prob*100), "ev": calculate_ev(tot_prob, 1.90)})
        evaluated.append({"text": f"NHL PUCK LINE: {fav_team} -1.5", "prob": round(sim["prob_run_line_h"]*100), "ev": calculate_ev(sim["prob_run_line_h"], 2.30)})
        evaluated.append({"text": f"NHL MONEYLINE: {fav_team} ML", "prob": round(max(prob_h, prob_a)*100), "ev": calculate_ev(max(prob_h, prob_a), cuota_h)})

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
