import os
import json
import math
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import requests
import uvicorn

from nfl_props_engine import obtener_mejores_props_nfl
from nba_props_engine import obtener_mejores_props_nba
from nhl_props_engine import obtener_mejores_props_nhl
from mlb_props_engine import obtener_mejores_props_mlb

from nfl_model import simular_partido_nfl, MAPEO_NFL
from nba_model import simular_partido_nba, MAPEO_NBA
from nhl_model import simular_partido_nhl, MAPEO_NHL
from mlb_model import simular_partido_mlb, MAPEO_MLB

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CONSTANTES DE THE ODDS API
# ==========================================
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

DEPORTE_TO_SPORT_KEY = {
    "nba": "basketball_nba",
    "nhl": "icehockey_nhl",
    "nfl": "americanfootball_nfl",
    "mlb": "baseball_mlb"
}

# ==========================================
# ENDPOINT PARA CARGA DE CUOTAS EN VIVO
# ==========================================

@app.get("/api/live-odds")
def api_live_odds(deporte: str = Query(...), local: str = Query(...), visitante: str = Query(...)):
    if not ODDS_API_KEY:
        return {
            "success": False,
            "error": "Falta configurar la variable ODDS_API_KEY en el entorno de Render."
        }

    sport_key = DEPORTE_TO_SPORT_KEY.get(deporte.lower())
    if not sport_key:
        return {"success": False, "error": f"Deporte '{deporte}' no soportado."}

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }

    try:
        r = requests.get(url, params=params, timeout=6)
        if r.status_code != 200:
            return {"success": False, "error": f"Respuesta no válida de Odds API: Código {r.status_code}"}

        eventos = r.json()
        evento_encontrado = None

        def limpiar_nombre(n):
            return n.lower().replace("la ", "").replace("los angeles ", "").replace("new york ", "").strip()

        loc_clean = limpiar_nombre(local)
        vis_clean = limpiar_nombre(visitante)

        for ev in eventos:
            home = ev.get("home_team", "").lower()
            away = ev.get("away_team", "").lower()

            match_loc = (loc_clean in home) or (home in loc_clean) or (local.lower() in home)
            match_vis = (vis_clean in away) or (away in vis_clean) or (visitante.lower() in away)

            if match_loc and match_vis:
                evento_encontrado = ev
                break

        if not evento_encontrado:
            return {
                "success": False,
                "error": f"No hay líneas activas de mercado para {local} vs {visitante} en este momento."
            }

        bookmakers = evento_encontrado.get("bookmakers", [])
        if not bookmakers:
            return {"success": False, "error": "No se encontraron casas de apuestas con líneas abiertas para este juego."}

        # Priorizar casas con volumen de mercado
        bm = bookmakers[0]
        for b in bookmakers:
            if b.get("key") in ["draftkings", "fanduel", "pinnacle", "bovada", "betonlineag"]:
                bm = b
                break

        datos_cuotas = {
            "bookmaker": bm.get("title", "Línea de Casino"),
            "cuota_ml_local": None,
            "cuota_ml_visitante": None,
            "linea_spread_local": None,
            "cuota_spread_local": None,
            "linea_spread_visitante": None,
            "cuota_spread_visitante": None,
            "linea_total": None,
            "cuota_total_over": None,
            "cuota_total_under": None
        }

        for market in bm.get("markets", []):
            m_key = market.get("key")
            outcomes = market.get("outcomes", [])

            # Moneyline (h2h)
            if m_key == "h2h":
                for out in outcomes:
                    t_name = out.get("name", "").lower()
                    if (loc_clean in t_name) or (local.lower() in t_name):
                        datos_cuotas["cuota_ml_local"] = out.get("price")
                    elif (vis_clean in t_name) or (visitante.lower() in t_name):
                        datos_cuotas["cuota_ml_visitante"] = out.get("price")

            # Handicap / Spreads
            elif m_key == "spreads":
                for out in outcomes:
                    t_name = out.get("name", "").lower()
                    if (loc_clean in t_name) or (local.lower() in t_name):
                        datos_cuotas["linea_spread_local"] = out.get("point")
                        datos_cuotas["cuota_spread_local"] = out.get("price")
                    elif (vis_clean in t_name) or (visitante.lower() in t_name):
                        datos_cuotas["linea_spread_visitante"] = out.get("point")
                        datos_cuotas["cuota_spread_visitante"] = out.get("price")

            # Totales (Over/Under)
            elif m_key == "totals":
                for out in outcomes:
                    lado = out.get("name", "").lower()
                    if lado == "over":
                        datos_cuotas["linea_total"] = out.get("point")
                        datos_cuotas["cuota_total_over"] = out.get("price")
                    elif lado == "under":
                        datos_cuotas["cuota_total_under"] = out.get("price")

        return {"success": True, "data": datos_cuotas}

    except Exception as e:
        return {"success": False, "error": f"Excepción interna: {str(e)}"}

# ==========================================
# ENDPOINTS REST API PARA FRONTEND EN VERCEL
# ==========================================

@app.get("/api/analizar-nfl")
def api_analizar_nfl(
    local: str, visitante: str,
    c_ml_loc: float = 1.90, c_ml_vis: float = 1.90,
    l_spread_loc: float = -2.5, c_spread_loc: float = 1.90,
    l_spread_vis: float = 2.5, c_spread_vis: float = 1.90,
    l_total: float = 46.5, c_over: float = 1.90, c_under: float = 1.90
):
    data = simular_partido_nfl(
        local, visitante,
        c_ml_loc, c_ml_vis,
        l_spread_loc, c_spread_loc,
        l_spread_vis, c_spread_vis,
        l_total, c_over, c_under
    )
    try:
        data["props_jugadores"] = obtener_mejores_props_nfl(local, visitante, top_n=6)
    except Exception:
        data["props_jugadores"] = []
    return data

@app.get("/api/analizar-nhl")
def api_analizar_nhl(
    local: str, visitante: str,
    c_ml_loc: float = 1.73, c_ml_vis: float = 2.10,
    l_rl_loc: float = -1.5, c_rl_loc: float = 2.85,
    l_rl_vis: float = 1.5, c_rl_vis: float = 1.40,
    l_total: float = 5.5, c_over: float = 1.79, c_under: float = 1.98
):
    data = simular_partido_nhl(
        local, visitante,
        c_ml_loc, c_ml_vis,
        l_rl_loc, c_rl_loc,
        l_rl_vis, c_rl_vis,
        l_total, c_over, c_under
    )
    try:
        data["props_jugadores"] = obtener_mejores_props_nhl(local, visitante, top_n=6)
    except Exception:
        data["props_jugadores"] = []
    return data

@app.get("/api/analizar-nba")
def api_analizar_nba(
    local: str, visitante: str,
    c_ml_loc: float = 1.90, c_ml_vis: float = 1.90,
    l_spread_loc: float = -2.5, c_spread_loc: float = 1.90,
    l_spread_vis: float = 2.5, c_spread_vis: float = 1.90,
    l_total: float = 224.5, c_over: float = 1.90, c_under: float = 1.90
):
    data = simular_partido_nba(
        local, visitante,
        c_ml_loc, c_ml_vis,
        l_spread_loc, c_spread_loc,
        l_spread_vis, c_spread_vis,
        l_total, c_over, c_under
    )
    try:
        data["props_jugadores"] = obtener_mejores_props_nba(local, visitante, top_n=6)
    except Exception:
        data["props_jugadores"] = []
    return data

@app.get("/api/analizar-mlb")
def api_analizar_mlb(
    local: str, visitante: str,
    c_ml_loc: float = 1.90, c_ml_vis: float = 1.90,
    l_rl_loc: float = -1.5, c_rl_loc: float = 2.10,
    l_rl_vis: float = 1.5, c_rl_vis: float = 1.75,
    l_total: float = 8.5, c_over: float = 1.90, c_under: float = 1.90
):
    data = simular_partido_mlb(
        local, visitante,
        c_ml_loc, c_ml_vis,
        l_rl_loc, c_rl_loc,
        l_rl_vis, c_rl_vis,
        l_total, c_over, c_under
    )
    try:
        data["props_jugadores"] = obtener_mejores_props_mlb(local, visitante, top_n=6)
    except Exception:
        data["props_jugadores"] = []
    return data

with gr.Blocks(title="La Maña Picks Engine") as demo:
    gr.Markdown("### La Maña Picks - API Backend Activa")

app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
