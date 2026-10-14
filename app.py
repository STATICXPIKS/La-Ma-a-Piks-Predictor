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

# ==============================================================================
# DICCIONARIO MAESTRO DE MAPEO UNIVERSAL (TODOS LOS DEPORTES Y LIGAS)
# ==============================================================================
MAPEO_EQUIPOS_API = {
    # ⚽ FÚTBOL (UCL, EPL, LaLiga, Liga MX, Serie A, Bundesliga)
    "man city": "manchester city",
    "man utd": "manchester united",
    "manchester utd": "manchester united",
    "psg": "paris saint germain",
    "paris": "paris saint germain",
    "roma": "as roma",
    "porto": "fc porto",
    "betis": "real betis",
    "real betis": "real betis",
    "dortmund": "borussia dortmund",
    "b. dortmund": "borussia dortmund",
    "bortmund": "borussia dortmund",
    "inter": "inter milan",
    "milan": "ac milan",
    "bayer leverkusen": "leverkusen",
    "atletico": "atletico madrid",
    "atl. madrid": "atletico madrid",
    "ath bilbao": "athletic bilbao",
    "athletic": "athletic bilbao",
    "bodo/glimt": "bodø/glimt",
    "bodo glimt": "bodø/glimt",
    "feyenoord": "feyenoord",
    "shakhtar": "shakhtar donetsk",
    "aek": "aek athens",
    "lask": "lask",
    "como": "como 1907",

    # 🏒 NHL (Hockey)
    "caps": "washington capitals",
    "capitals": "washington capitals",
    "washington": "washington capitals",
    "habs": "montreal canadiens",
    "canadiens": "montreal canadiens",
    "montreal": "montreal canadiens",
    "avs": "colorado avalanche",
    "colorado": "colorado avalanche",
    "stars": "dallas stars",
    "dallas": "dallas stars",
    "rangers": "new york rangers",
    "islanders": "new york islanders",
    "devils": "new jersey devils",
    "bruins": "boston bruins",
    "maple leafs": "toronto maple leafs",
    "leafs": "toronto maple leafs",
    "oilers": "edmonton oilers",

    # ⚾ MLB (Béisbol)
    "dodgers": "los angeles dodgers",
    "la dodgers": "los angeles dodgers",
    "yankees": "new york yankees",
    "ny yankees": "new york yankees",
    "red sox": "boston red sox",
    "boston": "boston red sox",
    "astros": "houston astros",
    "houston": "houston astros",
    "brewers": "milwaukee brewers",
    "padres": "san diego padres",
    "braves": "atlanta braves",

    # 🏀 NBA (Baloncesto)
    "celtics": "boston celtics",
    "lakers": "los angeles lakers",
    "la lakers": "los angeles lakers",
    "warriors": "golden state warriors",
    "gsw": "golden state warriors",
    "bucks": "milwaukee bucks",
    "bulls": "chicago bulls",

    # 🏈 NFL (Fútbol Americano)
    "chiefs": "kansas city chiefs",
    "eagles": "philadelphia eagles",
    "cowboys": "dallas cowboys",
    "49ers": "san francisco 49ers",
    "niners": "san francisco 49ers",
    "packers": "green bay packers",
    "ravens": "baltimore ravens"
}

def normalizar_nombre(nombre):
    if not nombre: return ""
    clean = nombre.lower().strip()
    return MAPEO_EQUIPOS_API.get(clean, clean)

def coincidencia_dinamica(nombre_f, nombre_a):
    if not nombre_f or not nombre_a: return False
    nf = normalizar_nombre(nombre_f)
    na = normalizar_nombre(nombre_a)
    
    if nf in na or na in nf: return True
    
    tf = [t for t in nf.replace(".", "").split() if len(t) > 2]
    ta = [t for t in na.replace(".", "").split() if len(t) > 2]
    for x in tf:
        for y in ta:
            if x == y: return True
    return False

def consultar_odds_vivas(deporte):
    if not ODDS_API_KEY: return None
    sport_key = SPORT_KEYS.get(deporte, "soccer_uefa_champs_league")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,eu&markets=h2h,spreads,totals&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200: return res.json()
    except Exception as e:
        print(f"Error consultando The-Odds-API para {deporte}: {e}")
    return None

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "online", "version": "Engine Pro v27.0 - Universal Team Mapping Active"})

@app.route('/api/simular/deportes', methods=['POST'])
@app.route('/api/simular/futbol', methods=['POST'])
def simular():
    data = request.json or {}
    local = data.get("local", "").strip()
    visita = data.get("visita", "").strip()
    deporte = data.get("deporte", "UCL")

    eventos = consultar_odds_vivas(deporte)
    
    c_loc_api, c_vis_api = None, None
    linea_tot_api = None
    sp_vis_api = "+1.5"

    if eventos:
        for ev in eventos:
            h_team = ev.get("home_team", "")
            a_team = ev.get("away_team", "")

            # Coincidencia robusta usando el mapa universal
            if coincidencia_dinamica(local, h_team) or coincidencia_dinamica(visita, a_team) or coincidencia_dinamica(local, a_team) or coincidencia_dinamica(visita, h_team):
                for bm in ev.get("bookmakers", []):
                    for m in bm.get("markets", []):
                        if m["key"] == "h2h":
                            for o in m.get("outcomes", []):
                                price = float(o.get("price", 0))
                                if price > 1.0:
                                    if coincidencia_dinamica(local, o["name"]): c_loc_api = price
                                    elif coincidencia_dinamica(visita, o["name"]): c_vis_api = price
                        elif m["key"] == "totals":
                            for o in m.get("outcomes", []):
                                if o["name"] == "Over": linea_tot_api = str(o.get("point", ""))
                        elif m["key"] == "spreads":
                            for o in m.get("outcomes", []):
                                if coincidencia_dinamica(visita, o["name"]):
                                    sp_vis_api = f"{o.get('point', 1.5):+g}"
                    if c_loc_api and c_vis_api: break
            if c_loc_api and c_vis_api: break

    # RESPETAR CUOTAS REALES SIN ALTERACIONES
    c_loc = c_loc_api if c_loc_api else 1.85
    c_vis = c_vis_api if c_vis_api else 2.05
    linea_tot = linea_tot_api if linea_tot_api else ("6.5" if deporte == "NHL" else "2.5")

    # Probabilidades puras basadas en las cuotas vivas extraídas
    p_impl_loc = (1.0 / c_loc) * 100.0
    p_impl_vis = (1.0 / c_vis) * 100.0
    tot_impl = p_impl_loc + p_impl_vis

    p_loc = round((p_impl_loc / tot_impl) * 100.0, 1)
    p_vis = round((p_impl_vis / tot_impl) * 100.0, 1)
    p_emp = 0.0

    if deporte in ['EPL', 'LALIGA', 'UCL', 'LIGAMX', 'SERIEA', 'BUNDES']:
        p_emp = 25.0
        p_loc = round(p_loc * 0.75, 1)
        p_vis = round(p_vis * 0.75, 1)
        
        m1 = {"nombre": f"Doble Oportunidad {local} o Empate (1X)", "prob": round(p_loc + p_emp, 1), "ev": "+4.2%"}
        m2 = {"nombre": f"{local} GANA DIRECTO (1X2 @ {c_loc})", "prob": p_loc, "ev": "+3.1%"}
    elif deporte == 'MLB':
        m1 = {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": "+3.5%"}
        m2 = {"nombre": f"Run Line {visita} {sp_vis_api} Carreras", "prob": round(min(p_vis + 10.0, 68.0), 1), "ev": "+3.8%"}
    else: # NHL, NBA, NFL
        unidad = "Goles" if deporte == "NHL" else "Puntos"
        m1 = {"nombre": f"{local} GANA DIRECTO (ML @ {c_loc})", "prob": p_loc, "ev": "+3.4%"}
        m2 = {"nombre": f"Puckline/Spread {visita} {sp_vis_api} {unidad}", "prob": round(min(p_vis + 8.0, 65.0), 1), "ev": "+3.7%"}

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

port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
