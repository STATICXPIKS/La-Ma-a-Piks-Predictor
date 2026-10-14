import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY", "826e995b77fba63fd42c2915877b1037")
WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

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

# Coordenadas principales de ciudades para clima
ESTADIOS_CIUDADES = {
    "tampa bay": "Tampa", "cleveland": "Cleveland", "los angeles": "Los Angeles",
    "philadelphia": "Philadelphia", "seattle": "Seattle", "denver": "Denver",
    "madrid": "Madrid", "london": "London", "barcelona": "Barcelona", "rome": "Rome"
}

def obtener_clima_real(ciudad):
    """Consulta el clima en vivo para ajustar líneas de Over/Under."""
    if not WEATHER_API_KEY or not ciudad:
        return {"temp": 20, "viento_mph": 5, "descripcion": "Normal"}
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return {
                "temp": data["main"]["temp"],
                "viento_mph": round(data["wind"]["speed"] * 2.237, 1),
                "descripcion": data["weather"][0]["description"]
            }
    except Exception as e:
        print(f"Error consultando Clima: {e}")
    return {"temp": 20, "viento_mph": 5, "descripcion": "Normal"}

def consultar_odds_vivas(deporte, mercados="h2h,spreads,totals"):
    """Consulta cuotas y props en vivo."""
    if not ODDS_API_KEY: return None
    sport_key = SPORT_KEYS.get(deporte, "soccer_epl")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets={mercados}&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=4)
        if res.status_code == 200: return res.json()
    except Exception: pass
    return None

def analizar_mlb_avanzado(local, visita, ev_data):
    ciudad = ESTADIOS_CIUDADES.get(local.lower(), "Tampa")
    clima = obtener_clima_real(ciudad)
    
    # Impacto del viento en Over/Under de MLB
    ajuste_over = -5.0 if clima["viento_mph"] > 12 else 2.0
    
    c_loc, c_vis = 1.75, 2.15
    tot_car = "8.5"
    p_loc, p_vis = 57.0, 43.0

    if ev_data and ev_data.get("bookmakers"):
        bm = ev_data["bookmakers"][0]
        for m in bm.get("markets", []):
            if m["key"] == "h2h":
                for o in m.get("outcomes", []):
                    if local.lower() in o["name"].lower(): c_loc = o["price"]
                    elif visita.lower() in o["name"].lower(): c_vis = o["price"]
            elif m["key"] == "totals":
                for o in m.get("outcomes", []):
                    if o["name"] == "Over": tot_car = str(o.get("point", 8.5))

    prob_nrfi = 62.0
    prob_over = round(54.0 + ajuste_over, 1)

    mercados = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 3.9},
        {"nombre": f"NRFI (No Carrera en 1ª Entrada)", "prob": prob_nrfi, "ev": 4.8},
        {"nombre": f"Primeras 5 Entradas (F5) - {local} ML", "prob": 58.5, "ev": 4.1},
        {"nombre": f"Prop: Pitcher Abstr. OVER 5.5 Ponches (K's)", "prob": 59.0, "ev": 4.3},
        {"nombre": f"OVER {tot_car} Carreras Totales (Viento: {clima['viento_mph']} mph)", "prob": prob_over, "ev": 3.2}
    ]
    sorted_m = sorted(mercados, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return p_loc, p_vis, sorted_m[0], sorted_m[1], tot_car, clima

def analizar_nfl_avanzado(local, visita, ev_data):
    ciudad = ESTADIOS_CIUDADES.get(local.lower(), "Philadelphia")
    clima = obtener_clima_real(ciudad)
    
    c_loc, c_vis = 1.65, 2.30
    sp_loc = "-3.5 Pts"
    tot_pts = "47.5"
    p_loc, p_vis = 62.0, 38.0

    if ev_data and ev_data.get("bookmakers"):
        bm = ev_data["bookmakers"][0]
        for m in bm.get("markets", []):
            if m["key"] == "h2h":
                for o in m.get("outcomes", []):
                    if local.lower() in o["name"].lower(): c_loc = o["price"]
                    elif visita.lower() in o["name"].lower(): c_vis = o["price"]
            elif m["key"] == "spreads":
                for o in m.get("outcomes", []):
                    pt = o.get("point", 0)
                    if local.lower() in o["name"].lower(): sp_loc = f"{pt:+g} Pts"
            elif m["key"] == "totals":
                for o in m.get("outcomes", []):
                    if o["name"] == "Over": tot_pts = str(o.get("point", 47.5))

    mercados = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 4.2},
        {"nombre": f"Spread {local} {sp_loc}", "prob": 54.5, "ev": 3.8},
        {"nombre": f"Prop: QB Pasar OVER 245.5 Yards", "prob": 58.0, "ev": 4.5},
        {"nombre": f"OVER {tot_pts} Puntos Totales (Temp: {clima['temp']}°C)", "prob": 55.0, "ev": 3.5}
    ]
    sorted_m = sorted(mercados, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return p_loc, p_vis, sorted_m[0], sorted_m[1], tot_pts, clima

def analizar_futbol_avanzado(local, visita, ev_data):
    c_loc, c_vis = 2.10, 3.40
    p_loc, p_emp, p_vis = 46.0, 26.0, 28.0

    if ev_data and ev_data.get("bookmakers"):
        bm = ev_data["bookmakers"][0]
        for m in bm.get("markets", []):
            if m["key"] == "h2h":
                for o in m.get("outcomes", []):
                    if local.lower() in o["name"].lower(): c_loc = o["price"]
                    elif visita.lower() in o["name"].lower(): c_vis = o["price"]

    mercados = [
        {"nombre": f"{local} GANA DIRECTO (1X2 @ {c_loc})", "prob": p_loc, "ev": 3.8},
        {"nombre": f"Doble Oportunidad {local} o Empate (1X)", "prob": round(p_loc + p_emp, 1), "ev": 4.6},
        {"nombre": f"AMBOS EQUIPOS ANOTAN (BTTS - SÍ)", "prob": 58.0, "ev": 4.1},
        {"nombre": f"OVER 9.5 Córners Totales", "prob": 57.0, "ev": 3.9},
        {"nombre": f"OVER 4.5 Tarjetas Totales", "prob": 54.0, "ev": 2.8}
    ]
    sorted_m = sorted(mercados, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return p_loc, p_emp, p_vis, sorted_m[0], sorted_m[1], "2.5", {"temp": 18, "viento_mph": 4}

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v14.0 - Live Weather & Props Active"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "Local")
    visita = data.get("visita", "Visitante")
    deporte = data.get("deporte", "MLB")

    eventos = consultar_odds_vivas(deporte)
    ev_data = None
    if eventos:
        for ev in eventos:
            if local.lower() in ev.get("home_team", "").lower() or visita.lower() in ev.get("away_team", "").lower():
                ev_data = ev
                break

    p_emp = 0
    if deporte == 'NFL':
        p_loc, p_vis, top1, top2, linea_tot, clima = analizar_nfl_avanzado(local, visita, ev_data)
    elif deporte == 'MLB':
        p_loc, p_vis, top1, top2, linea_tot, clima = analizar_mlb_avanzado(local, visita, ev_data)
    else:
        p_loc, p_emp, p_vis, top1, top2, linea_tot, clima = analizar_futbol_avanzado(local, visita, ev_data)

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "prob_local": p_loc,
        "prob_empate": p_emp,
        "prob_visita": p_vis,
        "linea_total": linea_tot,
        "clima": clima,
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
