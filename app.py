import os
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import uvicorn

from kambi_feed import obtener_cuotas_partido_kambi
from nfl_props_engine import obtener_mejores_props_nfl
from nba_props_engine import obtener_mejores_props_nba
from nhl_props_engine import obtener_mejores_props_nhl
from mlb_props_engine import obtener_mejores_props_mlb

from nfl_model import simular_partido_nfl
from nba_model import simular_partido_nba
from nhl_model import simular_partido_nhl
from mlb_model import simular_partido_mlb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "826e995b77fba63fd42c2915877b1037").strip()

DEPORTE_TO_SPORT_KEY = {
    "nba": "basketball_nba",
    "nhl": "icehockey_nhl",
    "nfl": "americanfootball_nfl",
    "mlb": "baseball_mlb"
}


def _consultar_the_odds_api(deporte: str, local: str, visitante: str):
    sport_key = DEPORTE_TO_SPORT_KEY.get(deporte.lower())
    if not sport_key or not ODDS_API_KEY:
        return None

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        # Si da 401 (sin créditos/inválida) o 429 (límite), retorna None para activar Kambi
        if r.status_code != 200:
            return None

        eventos = r.json()
        evento_encontrado = None

        def simplificar(txt):
            return "".join(c for c in txt.lower() if c.isalnum())

        loc_s = simplificar(local)
        vis_s = simplificar(visitante)

        for ev in eventos:
            home = simplificar(ev.get("home_team", ""))
            away = simplificar(ev.get("away_team", ""))
            if (loc_s in home or home in loc_s) and (vis_s in away or away in vis_s):
                evento_encontrado = ev
                break

        if not evento_encontrado:
            return None

        bookmakers = evento_encontrado.get("bookmakers", [])
        if not bookmakers:
            return None

        bm = bookmakers[0]
        for b in bookmakers:
            if b.get("key") in ["draftkings", "fanduel", "pinnacle", "bovada", "betonlineag"]:
                bm = b
                break

        datos_cuotas = {
            "bookmaker": f"{bm.get('title', 'Casino')} (Odds API)",
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

            if m_key == "h2h":
                for out in outcomes:
                    t_name = simplificar(out.get("name", ""))
                    if loc_s in t_name or t_name in loc_s:
                        datos_cuotas["cuota_ml_local"] = out.get("price")
                    elif vis_s in t_name or t_name in vis_s:
                        datos_cuotas["cuota_ml_visitante"] = out.get("price")

            elif m_key == "spreads":
                for out in outcomes:
                    t_name = simplificar(out.get("name", ""))
                    if loc_s in t_name or t_name in loc_s:
                        datos_cuotas["linea_spread_local"] = out.get("point")
                        datos_cuotas["cuota_spread_local"] = out.get("price")
                    elif vis_s in t_name or t_name in vis_s:
                        datos_cuotas["linea_spread_visitante"] = out.get("point")
                        datos_cuotas["cuota_spread_visitante"] = out.get("price")

            elif m_key == "totals":
                for out in outcomes:
                    lado = out.get("name", "").lower()
                    if lado == "over":
                        datos_cuotas["linea_total"] = out.get("point")
                        datos_cuotas["cuota_total_over"] = out.get("price")
                    elif lado == "under":
                        datos_cuotas["cuota_total_under"] = out.get("price")

        if datos_cuotas["cuota_ml_local"] or datos_cuotas["linea_total"]:
            return {"success": True, "data": datos_cuotas}
        return None
    except Exception:
        return None


@app.get("/api/live-odds")
def api_live_odds(deporte: str = Query(...), local: str = Query(...), visitante: str = Query(...)):
    # 1. Intenta primero con The Odds API (si hay créditos disponibles)
    res_odds_api = _consultar_the_odds_api(deporte, local, visitante)
    if res_odds_api:
        return res_odds_api

    # 2. Si Odds API no tiene créditos (401/429) o no encuentra el juego, cae directo a Kambi gratis
    return obtener_cuotas_partido_kambi(deporte, local, visitante)


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
    except Exception as e:
        print(f"Error props NBA: {e}")
        data["props_jugadores"] = []
    return data


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
    except Exception as e:
        print(f"Error props NFL: {e}")
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
    except Exception as e:
        print(f"Error props NHL: {e}")
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
    except Exception as e:
        print(f"Error props MLB: {e}")
        data["props_jugadores"] = []
    return data


with gr.Blocks(title="La Maña Picks Engine") as demo:
    gr.Markdown("### La Maña Picks - API Backend Activa")

app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
