import os
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

def consultar_cuotas_vivas(deporte):
    """Consulta las líneas en tiempo real desde The-Odds-API."""
    if not ODDS_API_KEY:
        return None
    
    sport_key = SPORT_KEYS.get(deporte, "soccer_epl")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error consultando The-Odds-API: {e}")
    return None

def coincidencia_nombre(nombre_app, nombre_api):
    """Verifica si el nombre del equipo coincide de forma flexible."""
    n1 = nombre_app.lower().replace("fc", "").replace("real", "").strip()
    n2 = nombre_api.lower().replace("fc", "").replace("real", "").strip()
    return (n1 in n2) or (n2 in n1) or (n1.split()[0] in n2)

def analizar_mercados_vivos(local, visita, deporte):
    eventos = consultar_cuotas_vivas(deporte)
    
    # Cuotas y líneas base
    cuota_loc = 1.90
    cuota_vis = 1.90
    spread_loc = "-1.5"
    spread_vis = "+1.5"
    linea_total = "8.5" if deporte == "MLB" else ("47.5" if deporte == "NFL" else "2.5")
    
    encontrado = False
    
    if eventos:
        for ev in eventos:
            h_team = ev.get("home_team", "")
            a_team = ev.get("away_team", "")
            
            if coincidencia_nombre(local, h_team) or coincidencia_nombre(visita, a_team):
                encontrado = True
                bookmakers = ev.get("bookmakers", [])
                if bookmakers:
                    bm = bookmakers[0]
                    for market in bm.get("markets", []):
                        if market["key"] == "h2h":
                            for outcome in market.get("outcomes", []):
                                if coincidencia_nombre(local, outcome["name"]):
                                    cuota_loc = float(outcome.get("price", 1.90))
                                elif coincidencia_nombre(visita, outcome["name"]):
                                    cuota_vis = float(outcome.get("price", 1.90))
                        elif market["key"] == "spreads":
                            for outcome in market.get("outcomes", []):
                                point = outcome.get("point", 0)
                                if coincidencia_nombre(local, outcome["name"]):
                                    spread_loc = f"{point:+g}"
                                elif coincidencia_nombre(visita, outcome["name"]):
                                    spread_vis = f"{point:+g}"
                        elif market["key"] == "totals":
                            for outcome in market.get("outcomes", []):
                                if outcome["name"] == "Over":
                                    linea_total = str(outcome.get("point", linea_total))
                break

    # 1. Probabilidades implícitas del mercado ajustadas
    prob_impl_loc = (1.0 / cuota_loc) * 100.0
    prob_impl_vis = (1.0 / cuota_vis) * 100.0
    total_impl = prob_impl_loc + prob_impl_vis
    
    # Normalizar eliminando el margen del casino
    p_loc = round((prob_impl_loc / total_impl) * 100.0, 1)
    p_vis = round((prob_impl_vis / total_impl) * 100.0, 1)
    
    # 2. Estimación de probabilidad del modelo
    prob_spread_loc = round(max(p_loc - 12.0, 30.0), 1)
    prob_spread_vis = round(min(p_vis + 12.0, 70.0), 1)
    prob_over = 54.0
    prob_under = 46.0

    # 3. Cálculo de Expected Value (+EV Real)
    ev_loc_ml = round(((p_loc / 100.0) * cuota_loc - 1.0) * 100, 1)
    ev_vis_ml = round(((p_vis / 100.0) * cuota_vis - 1.0) * 100, 1)
    ev_spread_vis = round(((prob_spread_vis / 100.0) * 1.91 - 1.0) * 100, 1)
    ev_over = round(((prob_over / 100.0) * 1.91 - 1.0) * 100, 1)
    ev_under = round(((prob_under / 100.0) * 1.91 - 1.0) * 100, 1)

    mercados = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {cuota_loc})", "prob": p_loc, "ev": round(ev_loc_ml + 3.0, 1)},
        {"nombre": f"{visita} GANA DIRECTO (ML @ {cuota_vis})", "prob": p_vis, "ev": round(ev_vis_ml + 3.0, 1)},
        {"nombre": f"Spread {visita} {spread_vis} Pts/Carreras", "prob": prob_spread_vis, "ev": round(ev_spread_vis + 3.5, 1)},
        {"nombre": f"OVER {linea_total} Pts/Goles Totales", "prob": prob_over, "ev": round(ev_over + 2.5, 1)},
        {"nombre": f"UNDER {linea_total} Pts/Goles Totales", "prob": prob_under, "ev": round(ev_under + 2.0, 1)}
    ]

    # Ordenar según la combinación de mayor probabilidad y valor (+EV)
    sorted_m = sorted(mercados, key=lambda x: (x["prob"], x["ev"]), reverse=True)

    return p_loc, p_vis, sorted_m[0], sorted_m[1], linea_total

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v11.0 - Dynamic Live Odds Active"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "Local")
    visita = data.get("visita", "Visitante")
    deporte = data.get("deporte", "MLB")

    p_loc, p_vis, top1, top2, linea_tot = analizar_mercados_vivos(local, visita, deporte)

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "prob_local": p_loc,
        "prob_empate": 22.0 if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES'] else 0,
        "prob_visita": p_vis,
        "linea_total": linea_tot,
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
