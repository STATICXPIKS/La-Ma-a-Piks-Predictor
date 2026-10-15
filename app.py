import os
import math
import random
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==========================================
# CONFIGURACIÓN DE APIS DESDE ENTORNO
# ==========================================
ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "")
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

ODDS_API_URL = "https://api.the-odds-api.com/v4/sports"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "version": "Engine Pro v33.0 - Live Real-Time Integration",
        "keys_configured": {
            "odds_api": bool(ODDS_API_KEY),
            "api_sports": bool(API_SPORTS_KEY),
            "openweather": bool(OPENWEATHER_API_KEY)
        }
    }), 200

# ==========================================
# FUNCIONES MATEMÁTICAS & SIMULACIÓN
# ==========================================

def poisson_pmf(k, lambda_param):
    if lambda_param <= 0:
        return 0.0
    return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)

def calculate_ev(prob_win, decimal_odds):
    if decimal_odds <= 1.0:
        return 0.0
    return round((prob_win * (decimal_odds - 1)) - (1 - prob_win), 4)

def simulate_matchup(lambda_home, lambda_away, iterations=10000):
    """Simulación Monte Carlo (10,000 iteraciones)."""
    h_wins, a_wins, draws = 0, 0, 0
    total_h, total_a = 0, 0
    
    for _ in range(iterations):
        sh = random.choices(range(12), [poisson_pmf(i, lambda_home) for i in range(12)])[0]
        sa = random.choices(range(12), [poisson_pmf(i, lambda_away) for i in range(12)])[0]
        
        total_h += sh
        total_a += sa
        
        if sh > sa: h_wins += 1
        elif sa > sh: a_wins += 1
        else: draws += 1

    return {
        "prob_home": round(h_wins / iterations, 4),
        "prob_away": round(a_wins / iterations, 4),
        "prob_draw": round(draws / iterations, 4),
        "proj_home": round(total_h / iterations, 2),
        "proj_away": round(total_a / iterations, 2),
        "proj_total": round((total_h + total_a) / iterations, 2)
    }

# ==========================================
# LECTURA DE DATOS EN VIVO DE THE ODDS API
# ==========================================

def fetch_live_odds(sport_key):
    """Consulta los partidos reales del día y sus cuotas en tiempo real."""
    if not ODDS_API_KEY:
        return []
    
    url = f"{ODDS_API_URL}/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error consultando Odds API: {e}")
    return []

# ==========================================
# ENDPOINT PRINCIPAL CON PARTIDOS REALES
# ==========================================

@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    sport_param = request.args.get("sport", "ICEHOCKEY_NHL").lower()
    
    # Mapeo de deportes a The Odds API
    sport_keys = {
        "nhl": "icehockey_nhl",
        "mlb": "baseball_mlb",
        "nba": "basketball_nba",
        "nfl": "americanfootball_nfl",
        "soccer": "soccer_epl"
    }
    
    key = sport_keys.get(sport_param, "icehockey_nhl")
    live_matches = fetch_live_odds(key)
    
    processed_games = []
    
    if live_matches:
        for match in live_matches[:10]: # Procesamos los partidos agendados
            home_team = match.get("home_team", "Local")
            away_team = match.get("away_team", "Visita")
            
            # Obtención de cuotas reales de la primera casa de apuestas disponible
            odds_h, odds_a = 1.90, 1.90
            bookmakers = match.get("bookmakers", [])
            if bookmakers:
                markets = bookmakers[0].get("markets", [])
                if markets:
                    outcomes = markets[0].get("outcomes", [])
                    for out in outcomes:
                        if out.get("name") == home_team:
                            odds_h = out.get("price", 1.90)
                        elif out.get("name") == away_team:
                            odds_a = out.get("price", 1.90)

            # Promedios de anotación estimados por deporte para simulación Poisson
            l_home = 3.2 if "icehockey" in key else (4.5 if "baseball" in key else 1.5)
            l_away = 2.9 if "icehockey" in key else (4.1 if "baseball" in key else 1.2)

            sim = simulate_matchup(l_home, l_away, iterations=10000)
            
            ev_home = calculate_ev(sim["prob_home"], odds_h)
            ev_away = calculate_ev(sim["prob_away"], odds_a)

            processed_games.append({
                "id": match.get("id"),
                "home_team": home_team,
                "away_team": away_team,
                "commence_time": match.get("commence_time"),
                "odds": {"home": odds_h, "away": odds_a},
                "simulation": sim,
                "ev_analysis": {
                    "home_ev": ev_home,
                    "away_ev": ev_away,
                    "best_pick": home_team if ev_home > ev_away else away_team
                }
            })

    return jsonify({
        "status": "success",
        "sport": sport_param.upper(),
        "total_games_today": len(processed_games),
        "games": processed_games
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
