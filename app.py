import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Importación del servicio de APIs en vivo (The Odds API, API-Sports, OpenWeather)
from api_service import get_live_odds, get_live_weather

# Importación de los 4 motores deportivos
import nhl_model
import nfl_model
import nba_model
import mlb_model

app = Flask(__name__)
CORS(app)  # Permite peticiones seguras desde la interfaz alojada en Vercel

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "API de La Maña Picks Operativa",
        "apis_conectadas": {
            "odds_api": bool(os.environ.get("ODDS_API_KEY")),
            "api_sports": bool(os.environ.get("API_SPORTS_KEY")),
            "openweather": bool(os.environ.get("OPENWEATHER_KEY")),
            "supabase": bool(os.environ.get("SUPABASE_KEY"))
        },
        "modelos_disponibles": ["FROST-IA (NHL)", "BLITZ-IA (NFL)", "DUNK-IA (NBA)", "SLUGGER-IA (MLB)"]
    })

# 0. ENDPOINT DE CUOTAS EN VIVO (THE ODDS API)
@app.route('/api/live-odds', methods=['GET'])
def live_odds():
    try:
        deporte = request.args.get('deporte', 'icehockey_nhl')
        data = get_live_odds(deporte)
        if data:
            return jsonify(data)
        return jsonify({"error": "No se pudieron obtener cuotas en vivo o límite alcanzado"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 1. ENDPOINT NHL (FROST-IA)
@app.route('/api/analizar-nhl', methods=['GET'])
def analizar_nhl():
    try:
        local = request.args.get('local', 'Calgary Flames')
        visitante = request.args.get('visitante', 'Toronto Maple Leafs')
        
        c_ml_loc = float(request.args.get('c_ml_loc', 2.23))
        c_ml_vis = float(request.args.get('c_ml_vis', 1.66))
        
        l_pl_loc = float(request.args.get('l_pl_loc', 1.5))
        c_pl_loc = float(request.args.get('c_pl_loc', 1.47))
        l_pl_vis = float(request.args.get('l_pl_vis', -1.5))
        c_pl_vis = float(request.args.get('c_pl_vis', 2.55))
        
        l_total = float(request.args.get('l_total', 6.5))
        c_over = float(request.args.get('c_over', 1.81))
        c_under = float(request.args.get('c_under', 1.94))
        
        func_nhl = getattr(nhl_model, 'simular_partido_nhl', getattr(nhl_model, 'simular_partido', None))
        if func_nhl is None:
            return jsonify({"error": "No se encontró la función en nhl_model"}), 500

        resultado = func_nhl(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_pl_loc, c_pl_loc,
            l_pl_vis, c_pl_vis,
            l_total, c_over, c_under
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. ENDPOINT NFL (BLITZ-IA)
@app.route('/api/analizar-nfl', methods=['GET'])
def analizar_nfl():
    try:
        local = request.args.get('local', 'Kansas City Chiefs')
        visitante = request.args.get('visitante', 'San Francisco 49ers')
        
        c_ml_loc = float(request.args.get('c_ml_loc', 1.80))
        c_ml_vis = float(request.args.get('c_ml_vis', 2.00))
        
        l_spread_loc = float(request.args.get('l_spread_loc', -3.5))
        c_spread_loc = float(request.args.get('c_spread_loc', 1.90))
        l_spread_vis = float(request.args.get('l_spread_vis', 3.5))
        c_spread_vis = float(request.args.get('c_spread_vis', 1.90))
        
        l_total = float(request.args.get('l_total', 47.5))
        c_over = float(request.args.get('c_over', 1.90))
        c_under = float(request.args.get('c_under', 1.90))
        
        func_nfl = getattr(nfl_model, 'simular_partido_nfl', getattr(nfl_model, 'simular_partido', None))
        if func_nfl is None:
            return jsonify({"error": "No se encontró la función en nfl_model"}), 500

        resultado = func_nfl(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_spread_loc, c_spread_loc,
            l_spread_vis, c_spread_vis,
            l_total, c_over, c_under
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. ENDPOINT NBA (DUNK-IA)
@app.route('/api/analizar-nba', methods=['GET'])
def analizar_nba():
    try:
        local = request.args.get('local', 'Boston Celtics')
        visitante = request.args.get('visitante', 'Denver Nuggets')
        
        c_ml_loc = float(request.args.get('c_ml_loc', 1.84))
        c_ml_vis = float(request.args.get('c_ml_vis', 1.96))
        
        l_spread_loc = float(request.args.get('l_spread_loc', -2.5))
        c_spread_loc = float(request.args.get('c_spread_loc', 1.90))
        l_spread_vis = float(request.args.get('l_spread_vis', 2.5))
        c_spread_vis = float(request.args.get('c_spread_vis', 1.90))
        
        l_total = float(request.args.get('l_total', 224.5))
        c_over = float(request.args.get('c_over', 1.90))
        c_under = float(request.args.get('c_under', 1.90))
        
        func_nba = getattr(nba_model, 'simular_partido_nba', getattr(nba_model, 'simular_partido', None))
        if func_nba is None:
            return jsonify({"error": "No se encontró la función en nba_model"}), 500

        resultado = func_nba(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_spread_loc, c_spread_loc,
            l_spread_vis, c_spread_vis,
            l_total, c_over, c_under
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. ENDPOINT MLB (SLUGGER-IA)
@app.route('/api/analizar-mlb', methods=['GET'])
def analizar_mlb():
    try:
        local = request.args.get('local', 'Los Angeles Dodgers')
        visitante = request.args.get('visitante', 'New York Yankees')
        
        c_ml_loc = float(request.args.get('c_ml_loc', 1.80))
        c_ml_vis = float(request.args.get('c_ml_vis', 2.00))
        
        l_rl_loc = float(request.args.get('l_rl_loc', -1.5))
        c_rl_loc = float(request.args.get('c_rl_loc', 2.10))
        l_rl_vis = float(request.args.get('l_rl_vis', 1.5))
        c_rl_vis = float(request.args.get('c_rl_vis', 1.75))
        
        l_total = float(request.args.get('l_total', 8.5))
        c_over = float(request.args.get('c_over', 1.90))
        c_under = float(request.args.get('c_under', 1.90))
        
        func_mlb = getattr(mlb_model, 'simular_partido_mlb', getattr(mlb_model, 'simular_partido', None))
        if func_mlb is None:
            return jsonify({"error": "No se encontró la función en mlb_model"}), 500

        resultado = func_mlb(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_rl_loc, c_rl_loc,
            l_rl_vis, c_rl_vis,
            l_total, c_over, c_under
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=False)
