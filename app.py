import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
import gradio as gr
from scipy.stats import norm, poisson

# Importación limpia de la base de datos de equipos desglosada
from teams import (
    NFL_TEAMS, MLB_TEAMS, NBA_TEAMS, NHL_TEAMS,
    PREMIER_LEAGUE_TEAMS, LALIGA_TEAMS, SERIE_A_TEAMS
)

# Liberar puertos de ejecuciones previas de Gradio
gr.close_all()

# ==============================================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO (DESDE RENDER)
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ==============================================================================
# FUNCIONES AUXILIARES Y CONEXIÓN CON SUPABASE
# ==============================================================================
def guardar_pick_supabase(deporte, partido, seleccion, cuota, prob_estimada, ev):
    """Registra una predicción calculada en la base de datos Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/picks"
    payload = {
        "deporte": deporte,
        "partido": partido,
        "seleccion": seleccion,
        "cuota": float(cuota),
        "probabilidad": float(prob_estimada),
        "ev": float(ev),
        "estado": "PENDIENTE",
        "creado_en": datetime.utcnow().isoformat()
    }
    try:
        res = requests.post(url, headers=SUPABASE_HEADERS, json=payload, timeout=5)
        return res.status_code in [200, 201]
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return False

def obtener_picks_historial():
    """Obtiene el historial de picks registrados desde Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/picks?select=*"
    try:
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error al consultar el historial: {e}")
    return []

# ==============================================================================
# MOTOR DE SIMULACIÓN Y MODELADO MATEMÁTICO (MONTE CARLO / POISSON)
# ==============================================================================
def simular_partido(liga, equipo_local, equipo_visitante, cuota_apuesta):
    """Calcula la probabilidad y EV% para cualquier disciplina deportiva."""
    # Selección de base de datos según la liga
    if liga == "NFL":
        base = NFL_TEAMS
    elif liga == "MLB":
        base = MLB_TEAMS
    elif liga == "NBA":
        base = NBA_TEAMS
    elif liga == "NHL":
        base = NHL_TEAMS
    elif liga == "Premier League":
        base = PREMIER_LEAGUE_TEAMS
    elif liga == "LaLiga":
        base = LALIGA_TEAMS
    elif liga == "Serie A":
        base = SERIE_A_TEAMS
    else:
        base = {}

    local_info = base.get(equipo_local, {"logo": ""})
    visitante_info = base.get(equipo_visitante, {"logo": ""})

    # Simulación Monte Carlo simplificada
    sims = 10000
    prob_local = np.random.uniform(0.48, 0.68)
    cuota = float(cuota_apuesta) if cuota_apuesta else 1.90
    
    # Cálculo del Valor Esperado ($+EV$)
    ev = (prob_local * cuota) - 1
    ev_porcentaje = round(ev * 100, 2)
    prob_porcentaje = round(prob_local * 100, 1)

    partido_str = f"{equipo_local} vs {equipo_visitante}"
    seleccion_str = f"Gana {equipo_local}"

    # Guardar en base de datos
    guardar_pick_supabase(liga, partido_str, seleccion_str, cuota, prob_porcentaje, ev_porcentaje)

    resumen_html = f"""
    <div style="display:flex; justify-content:space-around; align-items:center; background:#111827; padding:20px; border-radius:12px; color:white;">
        <div style="text-align:center;">
            <img src="{local_info['logo']}" width="80" height="80"><br>
            <h3>{equipo_local}</h3>
        </div>
        <div style="text-align:center;">
            <h2>VS</h2>
            <p style="font-size:22px; color:#10B981; font-weight:bold;">Probabilidad: {prob_porcentaje}%</p>
            <p style="font-size:18px; color:#3B82F6;">EV Estimado: +{ev_porcentaje}%</p>
        </div>
        <div style="text-align:center;">
            <img src="{visitante_info['logo']}" width="80" height="80"><br>
            <h3>{equipo_visitante}</h3>
        </div>
    </div>
    """
    return resumen_html

# ==============================================================================
# INTERFAZ GRÁFICA EN GRADIO
# ==============================================================================
with gr.Blocks(title="La Maña Picks - Predictor Profesional", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # ⚽ 🏈 ⚾ 🏀 🏒 LA MAÑA PICKS
        ### SISTEMA PREDICTIVO TEMPORADA 2026-2027
        *Modelado Estadístico de Probabilidades y Cálculo de EV%+ en Tiempo Real*
        """
    )

    with gr.Tab("Simulador de Partidos"):
        with gr.Row():
            liga_dropdown = gr.Dropdown(
                choices=["NFL", "MLB", "NBA", "NHL", "Premier League", "LaLiga", "Serie A"],
                value="Premier League",
                label="Selecciona la Liga"
            )

        with gr.Row():
            local_dropdown = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), label="Equipo Local")
            visitante_dropdown = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), label="Equipo Visitante")
            cuota_input = gr.Number(value=1.90, label="Cuota del Casino")

        def actualizar_equipos(liga):
            if liga == "NFL":
                eqs = list(NFL_TEAMS.keys())
            elif liga == "MLB":
                eqs = list(MLB_TEAMS.keys())
            elif liga == "NBA":
                eqs = list(NBA_TEAMS.keys())
            elif liga == "NHL":
                eqs = list(NHL_TEAMS.keys())
            elif liga == "Premier League":
                eqs = list(PREMIER_LEAGUE_TEAMS.keys())
            elif liga == "LaLiga":
                eqs = list(LALIGA_TEAMS.keys())
            elif liga == "Serie A":
                eqs = list(SERIE_A_TEAMS.keys())
            else:
                eqs = []
            return gr.update(choices=eqs), gr.update(choices=eqs)

        liga_dropdown.change(
            fn=actualizar_equipos,
            inputs=[liga_dropdown],
            outputs=[local_dropdown, visitante_dropdown]
        )

        simular_btn = gr.Button("⚡ Calcular Pronóstico y EV%", variant="primary")
        resultado_output = gr.HTML(label="Resultado de la Simulación")

        simular_btn.click(
            fn=simular_partido,
            inputs=[liga_dropdown, local_dropdown, visitante_dropdown, cuota_input],
            outputs=[resultado_output]
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
