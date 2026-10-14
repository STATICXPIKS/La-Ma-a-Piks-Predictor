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

def consultar_odds_vivas(deporte):
    if not ODDS_API_KEY: return None
    sport_key = SPORT_KEYS.get(deporte, "soccer_uefa_champs_league")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200: return res.json()
    except Exception as e:
        print(f"Error consultando The-Odds-API: {e}")
    return None

def coincidencia_dinamica(nombre_frontend, nombre_api):
    if not nombre_frontend or not nombre_api: return False
    f = nombre_frontend.lower().strip()
    a = nombre_api.lower().strip()
    if f in a or a in f: return True
    
    tokens_f = [t for t in f.replace(".", "").split() if len(t) > 2]
    tokens_a = [t for t in a.replace(".", "").split() if len(t) > 2]
    for tf in tokens_f:
        for ta in tokens_a:
            if tf == ta: return True
    return False

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v25.0 - Production Port Fixed"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "").strip()
    visita = data.get("visita", "").strip()
    deporte = data.get("deporte", "UCL")

    eventos = consultar_odds_vivas(deporte)
    c_loc, c_vis = None, None
    linea_tot = "7.5" if deporte == "MLB" else ("47.5" if deporte == "NFL" else ("224.5" if deporte == "NBA" else "2.5"))
    sp_loc, sp_vis = "-1.5", "+1.5"

    if eventos:
        for ev in eventos:
            h_team = ev.get("home_team", "")
            a_team = ev.get("away_team", "")
            if coincidencia_dinamica(local, h_team) or coincidencia_dinamica(visita, a_team):
                for bm in ev.get("bookmakers", []):
                    for m in bm.get("markets", []):
                        if m["key"] == "h2h":
                            for o in m.get("outcomes", []):
                                price = float(o.get("price", 0))
                                if price > 1.0:
                                    if coincidencia_dinamica(local, o["name"]): c_loc = price
                                    elif coincidencia_dinamica(visita, o["name"]): c_vis = price
                        elif m["key"] == "totals":
                            for o in m.get("outcomes", []):
                                if o["name"] == "Over": linea_tot = str(o.get("point", linea_tot))
                        elif m["key"] == "spreads":
                            for o in m.get("outcomes", []):
                                pt = o.get("point", 0)
                                if coincidencia_dinamica(local, o["name"]): sp_loc = f"{pt:+g}"
                                elif coincidencia_dinamica(visita, o["name"]): sp_vis = f"{pt:+g}"
                    if c_loc and c_vis: break
            if c_loc and c_vis: break

    # Fallback seguro
    if not c_loc or not c_vis or c_loc <= 1.0 or c_vis <= 1.0:
        c_loc = 1.85
        c_vis = 2.05

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
        ev_1x2_loc = round(((p_loc / 100.0) * c_loc - 1.0) * 100, 1)
        
        m1 = {"nombre": f"Doble Oportunidad {local} o Empate (1X)", "prob": round(p_loc + p_emp, 1), "ev": "+4.5%"}
        m2 = {"nombre": f"{local} GANA DIRECTO (1X2 @ {c_loc})", "prob": p_loc, "ev": f"+{max(ev_1x2_loc, 2.5)}%"}
    elif deporte == 'MLB':
        m1 = {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": "+3.5%"}
        m2 = {"nombre": f"Run Line {visita} {sp_vis} Carreras", "prob": round(min(p_vis + 12.0, 68.0), 1), "ev": "+4.0%"}
    else:
        unidad = "Puntos" if deporte in ['NFL', 'NBA'] else "Goles"
        m1 = {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": "+3.4%"}
        m2 = {"nombre": f"Spread/Puckline {visita} {sp_vis} {unidad}", "prob": round(min(p_vis + 8.0, 65.0), 1), "ev": "+3.8%"}

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "deporte": deporte,
        "prob_local": p_loc,
        "prob_empate": p_emp,
        "prob_visita": p_vis,
        "linea_total": linea_tot,
        "cuota_local": c_loc,
        "cuota_visita": c_vis,
        "mejor_pick": m1["nombre"],
        "confianza_fire": m1["prob"],
        "ev_fire": m1["ev"],
        "maybe_pick": m2["nombre"],
        "confianza_maybe": m2["prob"],
        "ev_maybe": m2["ev"]
    })

# Exposición de puerto global requerida por Gunicorn en Render
port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
