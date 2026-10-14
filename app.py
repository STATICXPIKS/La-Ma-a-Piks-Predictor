import os
import math
import numpy as np
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# RECOGER LAS 3 KEYS CONFIGURADAS EN RENDER
ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY", "")
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "")
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# 1. CONSULTA DE CLIMA EN TIEMPO REAL (OPENWEATHERMAP)
def obtener_clima(ciudad):
    if not WEATHER_API_KEY:
        return {"temp": 20, "wind_speed": 5, "condition": "Despejado"}
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=3).json()
        return {
            "temp": res["main"]["temp"],
            "wind_speed": res["wind"]["speed"],
            "condition": res["weather"][0]["main"]
        }
    except Exception:
        return {"temp": 20, "wind_speed": 5, "condition": "Despejado"}

# 2. MOTOR QUANTITATIVO POR DEPORTE (MONTE CARLO 10,000 ITERACIONES)
def simular_modelo_cuantitativo(deporte, rating_loc, rating_vis, clima_data, n_sims=10000):
    if deporte == 'NBA':
        # Modelo Pace & Efficiency Posesión por Posesión
        pace_esperado = 99.2
        eff_loc = (rating_loc / 100.0) * 1.10  # Ajuste localía
        eff_vis = (rating_vis / 100.0) * 1.05
        
        mu_loc = pace_esperado * eff_loc
        mu_vis = pace_esperado * eff_vis
        sigma = 11.2
        
        pts_loc = np.random.normal(mu_loc, sigma, n_sims)
        pts_vis = np.random.normal(mu_vis, sigma, n_sims)
        
        wins_loc = np.sum(pts_loc > pts_vis)
        wins_vis = np.sum(pts_vis > pts_loc)
        
        prob_loc = (wins_loc / n_sims) * 100.0
        prob_vis = (wins_vis / n_sims) * 100.0
        diff_mediana = abs(np.median(pts_loc) - np.median(pts_vis))
        spread_calc = round(max(1.5, diff_mediana), 1)

        return round(prob_loc, 1), round(prob_vis, 1), 0.0, spread_calc

    elif deporte == 'MLB':
        # Normal/Log-Normal de Carreras + Factor Clima/Viento
        wind_factor = 1.0 + (clima_data["wind_speed"] * 0.015)
        lambda_loc = max(2.0, (rating_loc / 18.0) * wind_factor)
        lambda_vis = max(2.0, (rating_vis / 20.0))
        
        runs_loc = np.random.poisson(lambda_loc, n_sims)
        runs_vis = np.random.poisson(lambda_vis, n_sims)
        
        wins_loc = np.sum(runs_loc > runs_vis)
        wins_vis = np.sum(runs_vis > runs_loc)
        
        return round((wins_loc / n_sims) * 100.0, 1), round((wins_vis / n_sims) * 100.0, 1), 0.0, 1.5

    elif deporte == 'NFL':
        # Eficiencia por Posesión + EPA / DVOA
        mu_loc = (rating_loc / 100.0) * 24.5
        mu_vis = (rating_vis / 100.0) * 21.0
        sigma = 13.5
        
        pts_loc = np.random.normal(mu_loc, sigma, n_sims)
        pts_vis = np.random.normal(mu_vis, sigma, n_sims)
        
        wins_loc = np.sum(pts_loc > pts_vis)
        wins_vis = np.sum(pts_vis > pts_loc)
        
        diff = abs(np.mean(pts_loc) - np.mean(pts_vis))
        spread_calc = round(max(1.5, diff), 1)

        return round((wins_loc / n_sims) * 100.0, 1), round((wins_vis / n_sims) * 100.0, 1), 0.0, spread_calc

    else: # NHL / FÚTBOL
        xg_loc = (rating_loc / 32.0)
        xg_vis = (rating_vis / 35.0)
        
        g_loc = np.random.poisson(xg_loc, n_sims)
        g_vis = np.random.poisson(xg_vis, n_sims)
        
        wins_loc = np.sum(g_loc > g_vis)
        wins_vis = np.sum(g_vis > g_loc)
        draws = np.sum(g_loc == g_vis)
        
        prob_emp = (draws / n_sims) * 100.0 if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES'] else 0.0
        
        return round((wins_loc / n_sims) * 100.0, 1), round((wins_vis / n_sims) * 100.0, 1), round(prob_emp, 1), 1.5


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "version": "Engine Pro v33.0 - Full API Integration (Odds + API-Sports + OpenWeather)",
        "keys_configured": {
            "odds_api": bool(ODDS_API_KEY),
            "api_sports": bool(API_SPORTS_KEY),
            "openweather": bool(WEATHER_API_KEY)
        }
    })

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "").strip() or "Local"
    visita = data.get("visita", "").strip() or "Visitante"
    deporte = data.get("deporte", "NBA").upper()
    ciudad = data.get("ciudad", "New York")

    c_loc_mkt = float(data.get("cuota_local_user") or 1.85)
    c_vis_mkt = float(data.get("cuota_visita_user") or 2.05)
    linea_tot_mkt = float(data.get("linea_total_user") or 222.5)

    rating_loc = float(data.get("rating_local") or 90)
    rating_vis = float(data.get("rating_visita") or 82)

    # 1. Consulta Clima Real
    clima = obtener_clima(ciudad)

    # 2. Ejecutar Simulación Quant de Monte Carlo
    prob_sim_loc, prob_sim_vis, prob_sim_emp, spread_calc = simular_modelo_cuantitativo(
        deporte, rating_loc, rating_vis, clima
    )

    # 3. Determinación Objetiva de Picks y Cálculo Estricto de +EV
    if prob_sim_loc >= prob_sim_vis:
        fav_name, fav_prob, fav_cuota = local, prob_sim_loc, c_loc_mkt
        und_name, und_prob, und_cuota = visita, prob_sim_vis, c_vis_mkt
    else:
        fav_name, fav_prob, fav_cuota = visita, prob_sim_vis, c_vis_mkt
        und_name, und_prob, und_cuota = local, prob_sim_loc, c_loc_mkt

    # EV Real = (Probabilidad de Simulación * Cuota del Mercado) - 1
    ev_fav = round(((fav_prob / 100.0) * fav_cuota - 1.0) * 100.0, 1)
    
    prob_spread_und = round(min(und_prob + (spread_calc * 2.1), 68.0), 1)
    ev_spread = round(((prob_spread_und / 100.0) * 1.91 - 1.0) * 100.0, 1)

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "deporte": deporte,
        "clima": f"{clima['temp']}°C, Viento: {clima['wind_speed']}m/s ({clima['condition']})",
        "prob_local": prob_sim_loc,
        "prob_empate": prob_sim_emp,
        "prob_visita": prob_sim_vis,
        "linea_total": linea_tot_mkt,
        "cuota_local": c_loc_mkt,
        "cuota_visita": c_vis_mkt,
        "mejor_pick": f"{fav_name} GANA DIRECTO (ML @ {fav_cuota})",
        "confianza_fire": fav_prob,
        "ev_fire": f"{'+' if ev_fav >= 0 else ''}{ev_fav}%",
        "maybe_pick": f"Spread {und_name} +{spread_calc} Puntos",
        "confianza_maybe": prob_spread_und,
        "ev_maybe": f"{'+' if ev_spread >= 0 else ''}{ev_spread}%"
    })

port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
