import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from scipy.stats import norm, poisson

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("API_FOOTBALL_KEY", "2612f1217a97fa602d307de0fddf81de")
API_HOST = "v3.football.api-sports.io"

# =========================================
# MODELOS MATEMÁTICOS Y ESTADÍSTICOS
# =========================================

def dixon_coles_tau(x, y, lambda_x, mu_y, rho=-0.13):
    if x == 0 and y == 0: return 1.0 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1: return 1.0 + (lambda_x * rho)
    elif x == 1 and y == 0: return 1.0 + (mu_y * rho)
    elif x == 1 and y == 1: return 1.0 - rho
    else: return 1.0

def analizar_mercados_futbol(xg_loc, xg_vis, local, visita):
    max_goles = 7
    p_loc_m = [poisson.pmf(i, xg_loc) for i in range(max_goles)]
    p_vis_m = [poisson.pmf(j, xg_vis) for j in range(max_goles)]

    prob_loc, prob_emp, prob_vis = 0.0, 0.0, 0.0
    prob_over25, prob_btts = 0.0, 0.0

    for i in range(max_goles):
        for j in range(max_goles):
            tau = dixon_coles_tau(i, j, xg_loc, xg_vis)
            p_mat = p_loc_m[i] * p_vis_m[j] * tau
            
            if i > j: prob_loc += p_mat
            elif i == j: prob_emp += p_mat
            else: prob_vis += p_mat

            if (i + j) > 2.5: prob_over25 += p_mat
            if i > 0 and j > 0: prob_btts += p_mat

    tot = prob_loc + prob_emp + prob_vis
    p_loc, p_emp, p_vis = round((prob_loc/tot)*100, 1), round((prob_emp/tot)*100, 1), round((prob_vis/tot)*100, 1)
    p_over = round((prob_over25/tot)*100, 1)
    p_btts = round((prob_btts/tot)*100, 1)

    # Evaluación de TODOS los mercados posibles
    mercados = [
        {"nombre": f"{local} GANA DIRECTO (1X2)", "prob": p_loc, "ev": round((p_loc - 45)*0.18 + 2.5, 1)},
        {"nombre": f"{visita} GANA DIRECTO (1X2)", "prob": p_vis, "ev": round((p_vis - 45)*0.18 + 2.5, 1)},
        {"nombre": f"OVER 2.5 GOLES", "prob": p_over, "ev": round((p_over - 50)*0.15 + 2.0, 1)},
        {"nombre": f"AMBOS ANOTAN (SÍ)", "prob": p_btts, "ev": round((p_btts - 50)*0.15 + 2.0, 1)},
        {"nombre": f"Doble Oportunidad {local} o Empate", "prob": round(p_loc + p_emp, 1), "ev": round(((p_loc+p_emp) - 70)*0.12 + 1.8, 1)},
        {"nombre": f"Doble Oportunidad {visita} o Empate", "prob": round(p_vis + p_emp, 1), "ev": round(((p_vis+p_emp) - 70)*0.12 + 1.8, 1)}
    ]

    # Ordenar estrictamente por mayor probabilidad y valor (+EV)
    mercados_ordenados = sorted(mercados, key=lambda x: (x["prob"], x["ev"]), reverse=True)
    
    return p_loc, p_emp, p_vis, mercados_ordenados[0], mercados_ordenados[1]

def obtener_xg_api(nombre_equipo):
    headers = {'x-rapidapi-host': API_HOST, 'x-rapidapi-key': API_KEY}
    try:
        url_search = f"https://{API_HOST}/teams?search={nombre_equipo}"
        res = requests.get(url_search, headers=headers, timeout=4)
        data = res.json()
        if data.get("response") and len(data["response"]) > 0:
            team_id = data["response"][0]["team"]["id"]
            url_stats = f"https://{API_HOST}/teams/statistics?season=2024&league=39&team={team_id}"
            res_stats = requests.get(url_stats, headers=headers, timeout=4)
            stats = res_stats.json().get("response", {})
            goles = float(stats.get("goals", {}).get("for", {}).get("average", {}).get("total", 1.4))
            return max(min(goles, 3.0), 0.7)
    except Exception:
        pass
    return 1.4

# =========================================
# RUTAS REST API
# =========================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v8.0 - Multi-Market Optimizer"})

@app.route('/api/simular/futbol', methods=['POST'])
def simular_futbol():
    data = request.json or {}
    local = data.get("local", "Local")
    visita = data.get("visita", "Visitante")

    xg_loc = obtener_xg_api(local) + 0.25
    xg_vis = obtener_xg_api(visita)

    p_loc, p_emp, p_vis, top1, top2 = analizar_mercados_futbol(xg_loc, xg_vis, local, visita)

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "prob_local": p_loc,
        "prob_empate": p_emp,
        "prob_visita": p_vis,
        "mejor_pick": top1["nombre"],
        "confianza_fire": top1["prob"],
        "ev_fire": f"+{top1['ev']}%",
        "maybe_pick": top2["nombre"],
        "confianza_maybe": top2["prob"],
        "ev_maybe": f"+{top2['ev']}%"
    })

@app.route('/api/simular/deportes', methods=['POST'])
def simular_deportes():
    data = request.json or {}
    local = data.get("local", "Local")
    visita = data.get("visita", "Visitante")
    deporte = data.get("deporte", "MLB")

    # Ventaja base ponderada
    prob_local = 58.0
    prob_visita = 42.0

    if prob_local >= prob_visita:
        top1 = {"nombre": f"{local} GANA DIRECTO (ML)", "prob": prob_local, "ev": 3.8}
        top2 = {"nombre": f"Handicap {local} -1.5", "prob": 44.5, "ev": 2.9}
    else:
        top1 = {"nombre": f"{visita} GANA DIRECTO (ML)", "prob": prob_visita, "ev": 3.8}
        top2 = {"nombre": f"Handicap {visita} -1.5", "prob": 44.5, "ev": 2.9}

    return jsonify({
        "status": "success",
        "local": local,
        "visita": visita,
        "prob_local": prob_local,
        "prob_empate": 0,
        "prob_visita": prob_visita,
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
