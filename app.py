import os
import json
import math
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import requests
import uvicorn

from nfl_props_engine import obtener_mejores_props_nfl
from nba_props_engine import obtener_mejores_props_nba
from nhl_props_engine import obtener_mejores_props_nhl
from nfl_model import simular_partido_nfl, MAPEO_NFL
from nba_model import simular_partido_nba, MAPEO_NBA
from nhl_model import simular_partido_nhl, MAPEO_NHL
from mlb_model import simular_partido_mlb, MAPEO_MLB

app = FastAPI()

# Habilitar CORS para permitir peticiones desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return simular_partido_mlb(
        local, visitante,
        c_ml_loc, c_ml_vis,
        l_rl_loc, c_rl_loc,
        l_rl_vis, c_rl_vis,
        l_total, c_over, c_under
    )

with gr.Blocks(title="La Maña Picks Engine") as demo:
    gr.Markdown("### La Maña Picks - API Backend Activa")

app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
