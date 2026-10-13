import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.stats import norm, poisson
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Esto permite que tu HTML en Netlify pueda conectarse a este servidor de Render sin ser bloqueado
CORS(app) 

# =========================================
# CONFIGURACIÓN DE SUPABASE Y DICCIONARIOS
# =========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# (Mantenemos tus variables de control estadístico)
FACTOR_AJUSTE_AUTO = {
    "NFL": 1.0, "MLB": 1.0, "NBA": 1.0, "PREMIER LEAGUE": 1.0, 
    "LALIGA": 1.0, "BUNDESLIGA": 1.0, "SERIE A": 1.0, 
    "CHAMPIONS LEAGUE": 1.0, "NATIONS LEAGUE": 1.0
}

# =========================================
# FUNCIONES DE BASE DE DATOS E HISTORIAL
# =========================================
def cargar_historial_db():
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_picks?select=*&order=id.asc"
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error HTTP leyendo Supabase: {e}")
    return []

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {
        "NFL": {"wins": 0, "losses": 0, "pending": 0},
        "MLB": {"wins": 0, "losses": 0, "pending": 0},
        "NBA": {"wins": 0, "losses": 0, "pending": 0},
        "PREMIER LEAGUE": {"wins": 0, "losses": 0, "pending": 0},
        "LALIGA": {"wins": 0, "losses": 0, "pending": 0},
        "BUNDESLIGA": {"wins": 0, "losses": 0, "pending": 0},
        "SERIE A": {"wins": 0, "losses": 0, "pending": 0},
        "CHAMPIONS LEAGUE": {"wins": 0, "losses": 0, "pending": 0},
        "NATIONS LEAGUE": {"wins": 0, "losses": 0, "pending": 0}
    }
    
    for item in historial:
        dep = str(item.get("deporte", "")).upper()
        est = item.get("estado", "PENDING")
        
        if "NFL" in dep: key = "NFL"
        elif "MLB" in dep: key = "MLB"
        elif "NBA" in dep: key = "NBA"
        elif "PREMIER" in dep: key = "PREMIER LEAGUE"
        elif "LALIGA" in dep: key = "LALIGA"
        elif "BUNDESLIGA" in dep: key = "BUNDESLIGA"
        elif "SERIE A" in dep: key = "SERIE A"
        elif "CHAMPIONS" in dep: key = "CHAMPIONS LEAGUE"
        elif "NATIONS" in dep: key = "NATIONS LEAGUE"
        else: key = "PREMIER LEAGUE"
            
        if est == "WIN": stats[key]["wins"] += 1
        elif est == "LOSS": stats[key]["losses"] += 1
        elif est == "PENDING": stats[key]["pending"] += 1

    tot_wins = sum(s["wins"] for s in stats.values())
    tot_loss = sum(s["losses"] for s in stats.values())
    tot_global = tot_wins + tot_loss
    pct_global = round((tot_wins / tot_global) * 100, 1) if tot_global > 0 else 0.0
    return stats, tot_wins, tot_loss, tot_global, pct_global

# =========================================
# RUTAS WEB (ENDPOINTS DE LA API)
# =========================================

# Esta es la ruta principal. Si entras a tu URL de Render verás este mensaje.
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "mensaje": "El Cerebro de La Maña Picks está conectado y corriendo perfectamente en Render."
    })

# Esta ruta le enviará las estadísticas reales a tu diseño HTML
@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()
    return jsonify({
        "efectividad_global": pct_global,
        "wins": tot_wins,
        "losses": tot_loss,
        "total_picks": tot_global,
        "estadisticas_por_liga": stats
    })

# Aquí estará la simulación. En el futuro, tu HTML llamará a esta ruta
@app.route('/api/simular/nfl', methods=['POST'])
def api_simular_nfl():
    data = request.json
    local = data.get("local", "")
    visita = data.get("visita", "")
    # Aquí irá la lógica de norm.cdf y matemáticas (simplificado para probar conexión hoy)
    
    return jsonify({
        "mensaje": f"Simulando {local} vs {visita} con modelo Quants",
        "prob_local": 65,
        "prob_visita": 35,
        "mejor_pick": f"{local} Handicap -3.5",
        "ev": "+4.5%"
    })

# =========================================
# INICIO DEL SERVIDOR FLASK
# =========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
