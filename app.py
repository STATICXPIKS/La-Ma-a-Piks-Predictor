from flask import Flask, request, jsonify
from flask_cors import CORS

# Importación de los 4 modelos cuantitativos
from nhl_model import simular_partido_nhl
from nfl_model import simular_partido_nfl
from nba_model import simular_partido_nba
from mlb_model import simular_partido_mlb

app = Flask(__name__)
CORS(app)  # Permite peticiones desde la interfaz en Vercel

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "API de La Maña Picks Operativa",
        "modelos_disponibles": ["FROST-IA (NHL)", "BLITZ-IA (NFL)", "DUNK-IA (NBA)", "SLUGGER-IA (MLB)"]
    })

# 1. ENDPOINT NHL (FROST-IA)
@app.route('/api/analizar-nhl', methods=['GET'])
def analizar_nhl():
    try:
        local = request.args.get('local', 'Colorado Avalanche')
        visitante = request.args.get('visitante', 'Tampa Bay Lightning')
        
        c_ml_loc = float(request.args.get('c_ml_loc', 1.84))
        c_ml_vis = float(request.args.get('c_ml_vis', 1.96))
        
        l_pl_loc = float(request.args.get('l_pl_loc', -1.5))
        c_pl_loc = float(request.args.get('c_pl_loc', 1.90))
        l_pl_vis = float(request.args.get('l_pl_vis', 1.5))
        c_pl_vis = float(request.args.get('c_pl_vis', 1.90))
        
        l_total = float(request.args.get('l_total', 6.0))
        c_over = float(request.args.get('c_over', 1.90))
        c_under = float(request.args.get('c_under', 1.90))
        
        resultado = simular_partido_nhl(
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
        
        resultado = simular_partido_nfl(
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
        
        resultado = simular_partido_nba(
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
        
        resultado = simular_partido_mlb(
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
    app.run(host='0.0.0.0', port=5000, debug=True)
