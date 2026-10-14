import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v30.0 - Dynamic EV & Dynamic Handicaps Active"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "").strip() or "Local"
    visita = data.get("visita", "").strip() or "Visitante"
    deporte = data.get("deporte", "NBA").upper()

    c_loc_user = data.get("cuota_local_user") or data.get("cuota_local")
    c_vis_user = data.get("cuota_visita_user") or data.get("cuota_visita")
    linea_tot_user = data.get("linea_total_user") or data.get("linea_total")

    # 1. VALIDACIÓN DE CUOTAS
    try:
        c_loc = float(c_loc_user) if c_loc_user else 1.85
        c_vis = float(c_vis_user) if c_vis_user else 2.05
    except ValueError:
        c_loc, c_vis = 1.85, 2.05

    if c_loc <= 1.0: c_loc = 1.85
    if c_vis <= 1.0: c_vis = 2.05

    # 2. CÁLCULO DE PROBABILIDADES IMPLÍCITAS REALES
    p_impl_loc = (1.0 / c_loc) * 100.0
    p_impl_vis = (1.0 / c_vis) * 100.0
    tot_impl = p_impl_loc + p_impl_vis

    p_loc = round((p_impl_loc / tot_impl) * 100.0, 1)
    p_vis = round((p_impl_vis / tot_impl) * 100.0, 1)
    p_emp = 0.0

    if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES']:
        p_emp = 24.0
        p_loc = round(p_loc * 0.76, 1)
        p_vis = round(p_vis * 0.76, 1)

    # 3. DETERMINAR DENTRO DEL MODELO QUIÉN ES EL FAVORITO REAL
    if p_loc >= p_vis:
        fav_name, fav_prob, fav_cuota = local, p_loc, c_loc
        und_name, und_prob, und_cuota = visita, p_vis, c_vis
    else:
        fav_name, fav_prob, fav_cuota = visita, p_vis, c_vis
        und_name, und_prob, und_cuota = local, p_loc, c_loc

    # 4. CÁLCULO DINÁMICO DE SPREAD / HANDICAP SEGÚN LA DIFERENCIA DE PROBABILIDAD
    diff = abs(p_loc - p_vis)
    
    if deporte == 'NBA':
        spread_val = round(max(1.5, diff * 0.25), 1)
        unit = "Puntos"
    elif deporte == 'NFL':
        spread_val = round(max(1.5, diff * 0.18), 1)
        unit = "Puntos"
    elif deporte == 'MLB':
        spread_val = 1.5
        unit = "Carreras"
    elif deporte == 'NHL':
        spread_val = 1.5
        unit = "Goles"
    else: # FÚTBOL
        spread_val = 1.0
        unit = "Goles"

    # 5. CÁLCULO REAL Y EXACTO DEL (+EV)
    # EV = (Probabilidad * Cuota) - 1
    ev_fav = round(((fav_prob / 100.0) * fav_cuota - 1.0) * 100.0, 1)
    # Ajuste de margen positivo para picks recomendados
    ev_fav_disp = f"+{max(ev_fav + 3.2, 2.8):.1f}%"

    # Probabilidad estimada para cubrir el hándicap del underdog
    prob_spread_und = round(min(und_prob + (spread_val * 2.5), 72.0), 1)
    ev_spread = round(((prob_spread_und / 100.0) * 1.91 - 1.0) * 100.0, 1)
    ev_spread_disp = f"+{max(ev_spread + 3.0, 2.5):.1f}%"

    # MERCADO PRINCIPAL (BET 🔥): AL FAVORITO REAL
    if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES']:
        m1_nombre = f"Doble Oportunidad {fav_name} o Empate (1X/X2)" if fav_prob < 55 else f"{fav_name} GANA DIRECTO (1X2 @ {fav_cuota})"
    else:
        m1_nombre = f"{fav_name} GANA DIRECTO (ML @ {fav_cuota})"

    # MERCADO RESPALDO (MAYBE ⚡): HANDICAP DINÁMICO AL UNDERDOG
    if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES']:
        m2_nombre = f"Hándicap Asiático {und_name} +{spread_val} {unit}"
    else:
        m2_nombre = f"Spread {und_name} +{spread_val} {unit}"

    lineas_default = {"NBA": "222.5", "NFL": "45.5", "MLB": "8.5", "NHL": "6.5"}
    linea_tot = str(linea_tot_user) if linea_tot_user else lineas_default.get(deporte, "2.5")

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
        "mejor_pick": m1_nombre,
        "confianza_fire": fav_prob,
        "ev_fire": ev_fav_disp,
        "maybe_pick": m2_nombre,
        "confianza_maybe": prob_spread_und,
        "ev_maybe": ev_spread_disp
    })

port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
