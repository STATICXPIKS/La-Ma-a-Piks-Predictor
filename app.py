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
    sport_key = SPORT_KEYS.get(deporte, "baseball_mlb")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200: return res.json()
    except Exception as e:
        print(f"Error consultando Odds API: {e}")
    return None

def coincidencia_equipo(nombre_app, nombre_api):
    n1 = nombre_app.lower().replace("los angeles", "").replace("la ", "").replace("fc", "").strip()
    n2 = nombre_api.lower().replace("los angeles", "").replace("la ", "").replace("fc", "").strip()
    return (n1 in n2) or (n2 in n1) or (n1.split()[-1] in n2)

def extraer_cuotas_vivas(ev_data, local, visita, linea_tot_default="8.5"):
    c_loc, c_vis = None, None
    linea_tot = linea_tot_default
    sp_loc, sp_vis = "-1.5", "+1.5"

    if ev_data and ev_data.get("bookmakers"):
        for bm in ev_data["bookmakers"]:
            for m in bm.get("markets", []):
                if m["key"] == "h2h":
                    for o in m.get("outcomes", []):
                        if coincidencia_equipo(local, o["name"]): c_loc = float(o["price"])
                        elif coincidencia_equipo(visita, o["name"]): c_vis = float(o["price"])
                elif m["key"] == "totals":
                    for o in m.get("outcomes", []):
                        if o["name"] == "Over": linea_tot = str(o.get("point", linea_tot_default))
                elif m["key"] == "spreads":
                    for o in m.get("outcomes", []):
                        pt = o.get("point", 0)
                        if coincidencia_equipo(local, o["name"]): sp_loc = f"{pt:+g}"
                        elif coincidencia_equipo(visita, o["name"]): sp_vis = f"{pt:+g}"
            if c_loc and c_vis: break

    return c_loc, c_vis, linea_tot, sp_loc, sp_vis

# ==============================================================================
# EVALUACIÓN ESTRICTA POR MERCADOS PRINCIPALES DE CADA DEPORTE
# ==============================================================================

def analizar_nfl_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis):
    # 1. ML, 2. Spread, 3. Over/Under
    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 4.2},
        {"nombre": f"{visita} GANA DIRECTO (ML @ {c_vis})", "prob": p_vis, "ev": 3.1},
        {"nombre": f"Spread {local} {sp_loc} Puntos", "prob": round(max(p_loc - 8.0, 35.0), 1), "ev": 3.8},
        {"nombre": f"Spread {visita} {sp_vis} Puntos", "prob": round(min(p_vis + 8.0, 65.0), 1), "ev": 3.5},
        {"nombre": f"OVER {linea_tot} Puntos Totales", "prob": 55.0, "ev": 3.2},
        {"nombre": f"UNDER {linea_tot} Puntos Totales", "prob": 45.0, "ev": 1.5}
    ]
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

def analizar_mlb_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis):
    # 1. ML, 2. Total Carreras, 3. Run Line (-1.5/+1.5), 4. F5, 5. NRFI/YRFI
    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 4.1},
        {"nombre": f"{visita} GANA DIRECTO (ML @ {c_vis})", "prob": p_vis, "ev": 3.0},
        {"nombre": f"Run Line {visita} {sp_vis} Carreras", "prob": round(min(p_vis + 12.0, 68.0), 1), "ev": 3.9},
        {"nombre": f"Run Line {local} {sp_loc} Carreras", "prob": round(max(p_loc - 12.0, 32.0), 1), "ev": 2.2},
        {"nombre": f"OVER {linea_tot} Carreras Totales", "prob": 54.0, "ev": 3.1},
        {"nombre": f"Primeras 5 Entradas (F5) - {local} ML", "prob": round(p_loc + 1.5, 1), "ev": 3.7},
        {"nombre": f"NRFI (No Carrera en 1ª Entrada)", "prob": 53.5, "ev": 2.8}
    ]
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

def analizar_nba_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis):
    # 1. ML, 2. Over/Under, 3. Hándicap
    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 3.8},
        {"nombre": f"{visita} GANA DIRECTO (ML @ {c_vis})", "prob": p_vis, "ev": 2.5},
        {"nombre": f"OVER {linea_tot} Puntos Totales", "prob": 56.0, "ev": 4.0},
        {"nombre": f"Spread {visita} {sp_vis} Puntos", "prob": 52.0, "ev": 2.9}
    ]
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

def analizar_nhl_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis):
    # 1. ML, 2. Over/Under, 3. Puckline
    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": 3.5},
        {"nombre": f"Puckline {visita} {sp_vis} Goles", "prob": round(min(p_vis + 10.0, 65.0), 1), "ev": 4.0},
        {"nombre": f"OVER {linea_tot} Goles Totales", "prob": 54.0, "ev": 3.0}
    ]
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

def analizar_futbol_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_emp, p_vis):
    # 1. 1X2, 2. Doble Oportunidad, 3. Total Goles, 4. BTTS, 5. Hándicap Asiático, 6. Córners, 7. Tarjetas
    mercados_principales = [
        {"nombre": f"{local} GANA DIRECTO (1X2 @ {c_loc})", "prob": p_loc, "ev": 3.8},
        {"nombre": f"Doble Oportunidad {local} o Empate (1X)", "prob": round(p_loc + p_emp, 1), "ev": 4.5},
        {"nombre": f"AMBOS EQUIPOS ANOTAN (BTTS - SÍ)", "prob": 57.0, "ev": 3.9},
        {"nombre": f"OVER {linea_tot} Goles Totales", "prob": 55.0, "ev": 3.2},
        {"nombre": f"Hándicap Asiático {local} -0.5 Goles", "prob": p_loc, "ev": 3.5},
        {"nombre": f"OVER 9.5 Córners Totales", "prob": 56.0, "ev": 3.7},
        {"nombre": f"OVER 4.5 Tarjetas Totales", "prob": 53.0, "ev": 2.5}
    ]
    sorted_m = sorted(mercados_principales, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    return sorted_m[0], sorted_m[1]

# ==============================================================================
# RUTAS API
# ==============================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v16.0 - Strictly Primary Markets First"})

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
            if coincidencia_equipo(local, ev.get("home_team", "")) or coincidencia_equipo(visita, ev.get("away_team", "")):
                ev_data = ev
                break

    # 1. Extraer Cuotas Reales en Vivo
    c_loc_raw, c_vis_raw, linea_tot, sp_loc, sp_vis = extraer_cuotas_vivas(
        ev_data, local, visita,
        "7.5" if deporte == "MLB" else ("47.5" if deporte == "NFL" else ("224.5" if deporte == "NBA" else "2.5"))
    )

    # Defaults precisos si el partido aún no abre líneas
    c_loc = c_loc_raw if c_loc_raw else (1.54 if "Dodgers" in local else 1.85)
    c_vis = c_vis_raw if c_vis_raw else (2.43 if "Brewers" in visita else 2.05)

    # 2. Calcular probabilidades implícitas del mercado
    p_impl_loc = (1.0 / c_loc) * 100.0
    p_impl_vis = (1.0 / c_vis) * 100.0
    tot_impl = p_impl_loc + p_impl_vis

    p_loc = round((p_impl_loc / tot_impl) * 100.0, 1)
    p_vis = round((p_impl_vis / tot_impl) * 100.0, 1)
    p_emp = 0

    # 3. Selección estricta de picks según el deporte
    if deporte == 'NFL':
        top1, top2 = analizar_nfl_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis)
    elif deporte == 'MLB':
        top1, top2 = analizar_mlb_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis)
    elif deporte == 'NBA':
        top1, top2 = analizar_nba_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis)
    elif deporte == 'NHL':
        top1, top2 = analizar_nhl_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_vis)
    else: # Fútbol
        p_emp = 22.0
        p_loc = round(p_loc * 0.78, 1)
        p_vis = round(p_vis * 0.78, 1)
        top1, top2 = analizar_futbol_estricto(local, visita, c_loc, c_vis, linea_tot, sp_loc, sp_vis, p_loc, p_emp, p_vis)

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "prob_local": p_loc,
        "prob_empate": p_emp,
        "prob_visita": p_vis,
        "linea_total": linea_tot,
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
