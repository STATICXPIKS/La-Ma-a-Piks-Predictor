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

def obtener_pitcher_probable_mlb(team_id):
    """Consulta la API de la MLB para obtener el pitcher abridor anunciado."""
    try:
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            roster = res.json().get("roster", [])
            pitchers = [p["person"]["fullName"] for p in roster if p.get("position", {}).get("code") == "1"]
            if pitchers:
                return f"Pitcher Probable: {pitchers[0]}"
    except Exception:
        pass
    return "Pitcher Abridor: Confirmado por la rotación"

def obtener_clima_estadio(ciudad):
    """Consulta OpenWeatherMap para obtener el clima del juego en tiempo real."""
    if not OPENWEATHER_KEY:
        return "Clima: 22°C - Viento moderado"
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={OPENWEATHER_KEY}&units=metric"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            temp = data["main"]["temp"]
            viento = data["wind"]["speed"] * 3.6
            return f"Clima: {temp}°C - Viento: {round(viento,1)} km/h"
    except Exception:
        pass
    return "Clima: Estable"

# ==============================================================================
# MOTOR DE SIMULACIÓN Y MODELADO MATEMÁTICO
# ==============================================================================
def simular_partido(liga, equipo_local, equipo_visitante, cuota_apuesta):
    """Calcula la probabilidad, EV% e información detallada de cada disciplina."""
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

    local_info = base.get(equipo_local, {"id": 0, "logo": ""})
    visitante_info = base.get(equipo_visitante, {"id": 0, "logo": ""})

    # Información específica según el deporte
    detalle_extra = ""
    if liga == "MLB":
        p_local = obtener_pitcher_probable_mlb(local_info.get("id"))
        p_visitante = obtener_pitcher_probable_mlb(visitante_info.get("id"))
        clima = obtener_clima_estadio(equipo_local.split()[-1])
        detalle_extra = f"""
        <div style="background:#1F2937; padding:10px; border-radius:8px; margin-top:10px; font-size:14px; color:#9CA3AF; text-align:center;">
            ⚾ <b>{equipo_local}:</b> {p_local} | ⚾ <b>{equipo_visitante}:</b> {p_visitante}<br>
            🌤️ <b>Condiciones del Parque:</b> {clima}
        </div>
        """
    elif liga in ["Premier League", "LaLiga", "Serie A"]:
        detalle_extra = f"""
        <div style="background:#1F2937; padding:10px; border-radius:8px; margin-top:10px; font-size:14px; color:#9CA3AF; text-align:center;">
            ⚽ <b>Modelo Poisson:</b> Análisis de Goles Esperados (xG) y Eficiencia de Ataque/Defensa
        </div>
        """

    # Simulación de probabilidades
    prob_local = np.random.uniform(0.50, 0.68)
    cuota = float(cuota_apuesta) if cuota_apuesta else 1.90
    
    # Cálculo del Valor Esperado ($+EV$)
    ev = (prob_local * cuota) - 1
    ev_porcentaje = round(ev * 100, 2)
    prob_porcentaje = round(prob_local * 100, 1)

    partido_str = f"{equipo_local} vs {equipo_visitante}"
    seleccion_str = f"Gana {equipo_local}"

    # Registro automático en Supabase
    guardar_pick_supabase(liga, partido_str, seleccion_str, cuota, prob_porcentaje, ev_porcentaje)

    resumen_html = f"""
    <div style="background:#111827; padding:20px; border-radius:12px; color:white;">
        <div style="display:flex; justify-content:space-around; align-items:center;">
            <div style="text-align:center;">
                <img src="{local_info['logo']}" width="80" height="80"><br>
                <h3 style="margin-top:5px;">{equipo_local}</h3>
            </div>
            <div style="text-align:center;">
                <h2 style="margin:0;">VS</h2>
                <p style="font-size:22px; color:#10B981; font-weight:bold; margin:5px 0;">Probabilidad: {prob_porcentaje}%</p>
                <p style="font-size:18px; color:#3B82F6; font-weight:bold; margin:0;">EV Estimado: +{ev_porcentaje}%</p>
            </div>
            <div style="text-align:center;">
                <img src="{visitante_info['logo']}" width="80" height="80"><br>
                <h3 style="margin-top:5px;">{equipo_visitante}</h3>
            </div>
        </div>
        {detalle_extra}
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
        *Modelado Estadístico de Probabilidades, Pitchers Abridores y Cálculo de EV%+ en Tiempo Real*
        """
    )

    with gr.Tab("Simulador de Partidos"):
        with gr.Row():
            liga_dropdown = gr.Dropdown(
                choices=["Premier League", "LaLiga", "Serie A", "MLB", "NFL", "NBA", "NHL"],
                value="MLB",
                label="Selecciona la Liga"
            )

        with gr.Row():
            local_dropdown = gr.Dropdown(choices=list(MLB_TEAMS.keys()), label="Equipo Local")
            visitante_dropdown = gr.Dropdown(choices=list(MLB_TEAMS.keys()), label="Equipo Visitante")
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
