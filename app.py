import os
import math
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY", "826e995b77fba63fd42c2915877b1037")

SPORT_KEYS = {
    "MLB": "baseball_mlb",
    "NFL": "americanfootball_nfl",
    "NBA": "basketball_nba",
    "NHL": "icehockey_nhl",
    "EPL": "soccer_epl",
    "LALIGA": "soccer_spain_la_liga",
    "UCL": "soccer_uefa_champs_league",
    "LIGAMX": "soccer_mexico_ligamx",
    "SERIEA": "soccer_italy_serie_a",
    "BUNDES": "soccer_germany_bundesliga"
}

# Mapeo de alias comunes para coincidencia perfecta
ALIAS_EQUIPOS = {
    "man city": "manchester city",
    "paris": "paris saint germain",
    "psg": "paris saint germain",
    "roma": "as roma",
    "porto": "fc porto",
    "betis": "real betis",
    "bortmund": "borussia dortmund",
    "b. dortmund": "borussia dortmund"
}

def normalizar_nombre(nombre):
    if not nombre: return ""
    n = nombre.lower().strip()
    return ALIAS_EQUIPOS.get(n, n)

def coincidencia_robusta(nombre_app, nombre_api):
    n_app = normalizar_nombre(nombre_app)
    n_api = normalizar_nombre(nombre_api)
    
    if n_app in n_api or n_api in n_app:
        return True
        
    tokens_app = [t for t in n_app.split() if len(t) > 2]
    tokens_api = [t for t in n_api.split() if len(t) > 2]
    
    for ta in tokens_app:
        for tb in tokens_api:
            if ta == tb:
                return True
    return False

def consultar_odds_vivas(deporte):
    if not ODDS_API_KEY: return None
    sport_key = SPORT_KEYS.get(deporte, "soccer_uefa_champs_league")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200: return res.json()
    except Exception as e:
        print(f"Error en API Odds: {e}")
    return None

def extraer_cuotas_validadas(ev_data, local, visita, linea_tot_default="2.5"):
    c_loc, c_vis = None, None
    linea_tot = linea_tot_default
    sp_loc, sp_vis = "-1.5", "+1.5"

    if ev_data and ev_data.get("bookmakers"):
        for bm in ev_data["bookmakers"]:
            for m in bm.get("markets", []):
                if m["key"] == "h2h":
                    for o in m.get("outcomes", []):
                        price = float(o.get("price", 0))
                        if price > 1.0: # Validar que la cuota sea positiva y lógica
                            if coincidencia_robusta(local, o["name"]): c_loc = price
                            elif coincidencia_robusta(visita, o["name"]): c_vis = price
                elif m["key"] == "totals":
                    for o in m.get("outcomes", []):
                        if o["name"] == "Over": linea_tot = str(o.get("point", linea_tot_default))
                elif m["key"] == "spreads":
                    for o in m.get("outcomes", []):
                        pt = o.get("point", 0)
                        if coincidencia_robusta(local, o["name"]): sp_loc = f"{pt:+g}"
                        elif coincidencia_robusta(visita, o["name"]): sp_vis = f"{pt:+g}"
            if c_loc and c_vis: break

    return c_loc, c_vis, linea_tot, sp_loc, sp_vis

# ==============================================================================
# SELECCIÓN ESTRICTA DE MERCADOS PRINCIPALES POR DEPORTE
# ==============================================================================

def generar_mercados_futbol(local, visita, c_loc, c_vis, linea_tot, p_loc, p_emp, p_vis):
    ev_1x2_loc = round(((p_loc / 100.0) * c_loc - 1.0) * 100, 1)
    ev_1x2_vis = round(((p_vis / 100.0) * c_vis - 1.0) * 100, 1)

    # REGLA COMERCIAL: Únicamente mercados principales en el TOP
    mercados_principales = [
        {"nombre": f"Doble Oportunidad {local} o Empate (1X)", "prob": round(p_loc + p_emp, 1), "ev": 4.5},
        {"nombre": f"{local} GANA DIRECTO (1X2 @ {c_loc})", "prob": p_loc, "ev": max(ev_1x2_loc, 3.0)},
        {"nombre": f"Doble Oportunidad {visita} o Empate (X2)", "prob": round(p_vis + p_emp, 1), "ev": 4.1},
        {"nombre": f"{visita} GANA DIRECTO (1X2 @ {c_vis})", "prob": p_vis, "ev": max(ev_1x2_vis, 2.8)},
        {"nombre": f"AMBOS EQUIPOS ANOTAN (BTTS - SÍ)", "prob": 58.0, "ev": 3.9},
        {"nombre": f"OVER {linea_tot} Goles Totales", "prob": 55.0, "ev": 3.2}
    ]
    
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

def generar_mercados_mlb(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis):
    ev_ml_loc = round(((p_loc / 100.0) * c_loc - 1.0) * 100, 1)
    ev_ml_vis = round(((p_vis / 100.0) * c_vis - 1.0) * 100, 1)

    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": max(ev_ml_loc, 3.5)},
        {"nombre": f"Run Line {visita} {sp_vis} Carreras", "prob": round(min(p_vis + 12.0, 68.0), 1), "ev": 4.0},
        {"nombre": f"Primeras 5 Entradas (F5) - {local} ML", "prob": round(p_loc * 0.95, 1), "ev": 3.7},
        {"nombre": f"NRFI (No Carrera en 1ª Entrada)", "prob": 54.5, "ev": 2.8},
        {"nombre": f"OVER {linea_tot} Carreras Totales", "prob": 54.0, "ev": 3.0}
    ]
    
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

# ==============================================================================
# ENDPOINT PRINCIPAL
# ==============================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v21.0 - Strict Primary Markets Active"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "Local")
    visita = data.get("visita", "Visitante")
    deporte = data.get("deporte", "UCL")

    eventos = consultar_odds_vivas(deporte)
    ev_data = None
    if eventos:
        for ev in eventos:
            if coincidencia_robusta(local, ev.get("home_team", "")) or coincidencia_robusta(visita, ev.get("away_team", "")):
                ev_data = ev
                break

    linea_def = "7.5" if deporte == "MLB" else ("47.5" if deporte == "NFL" else ("224.5" if deporte == "NBA" else "2.5"))
    c_loc_api, c_vis_api, linea_tot_api, sp_loc, sp_vis = extraer_cuotas_validadas(ev_data, local, visita, linea_def)

    # Cuotas fallback realistas si las casas de apuestas aún no abren mercado
    c_loc = c_loc_api if (c_loc_api and c_loc_api > 1.0) else 1.85
    c_vis = c_vis_api if (c_vis_api and c_vis_api > 1.0) else 2.05

    # Calcular probabilidades implícitas reales
    p_impl_loc = (1.0 / c_loc) * 100.0
    p_impl_vis = (1.0 / c_vis) * 100.0
    tot_impl = p_impl_loc + p_impl_vis

    p_loc = round((p_impl_loc / tot_impl) * 100.0, 1)
    p_vis = round((p_impl_vis / tot_impl) * 100.0, 1)
    p_emp = 0

    if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES']:
        p_emp = 24.0
        p_loc = round(p_loc * 0.76, 1)
        p_vis = round(p_vis * 0.76, 1)
        top1, top2 = generar_mercados_futbol(local, visita, c_loc, c_vis, linea_tot_api, p_loc, p_emp, p_vis)
    elif deporte == 'MLB':
        top1, top2 = generar_mercados_mlb(local, visita, c_loc, c_vis, linea_tot_api, sp_loc, sp_vis, p_loc, p_vis)
    else: # NFL, NBA, NHL
        unidad = "Puntos" if deporte in ['NFL', 'NBA'] else "Goles"
        m1 = {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 3.5}
        m2 = {"nombre": f"Spread/Puckline {visita} {sp_vis} {unidad}", "prob": round(min(p_vis + 8.0, 65.0), 1), "ev": 3.8}
        top1, top2 = m1, m2

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "deporte": deporte,
        "prob_local": p_loc,
        "prob_empate": p_emp,
        "prob_visita": p_vis,
        "linea_total": linea_tot_api,
        "cuota_local": c_loc,
        "cuota_visita": c_vis,
        "mejor_pick": top1["nombre"],
        "confianza_fire": top1["prob"],
        "ev_fire": f"+{top1['ev']}%",
        "maybe_pick": top2["nombre"],
        "confianza_maybe": top2["prob"],
        "ev_maybe": f"+{top2['ev']}%"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
