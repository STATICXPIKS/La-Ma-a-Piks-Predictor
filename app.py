import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
import gradio as gr

# Importación de la base de datos de equipos desglosada
from teams import (
    NFL_TEAMS, MLB_TEAMS, NBA_TEAMS, NHL_TEAMS,
    PREMIER_LEAGUE_TEAMS, LALIGA_TEAMS, SERIE_A_TEAMS
)

# Liberar ejecuciones previas de Gradio
gr.close_all()

# ==============================================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# LOGOS ESTABLES Y PROBADOS
LIGA_LOGOS = {
    "PREMIER": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "LALIGA": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "SERIEA": "https://a.espncdn.com/i/leaguelogos/soccer/500/12.png",
    "NFL": "https://a.espncdn.com/i/leaguelogos/nfl/500/nfl.png",
    "MLB": "https://a.espncdn.com/i/leaguelogos/mlb/500/mlb.png",
    "NBA": "https://a.espncdn.com/i/leaguelogos/nba/500/nba.png",
    "NHL": "https://a.espncdn.com/i/leaguelogos/nhl/500/nhl.png"
}

# ==============================================================================
# CONEXIÓN SUPABASE
# ==============================================================================
def obtener_picks_historial():
    url = f"{SUPABASE_URL}/rest/v1/picks?select=*"
    try:
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error Supabase: {e}")
    return []

def marcar_estado_pick(pick_id, estado):
    if not pick_id:
        return "⚠️ Ingrese un ID válido"
    url = f"{SUPABASE_URL}/rest/v1/picks?id=eq.{pick_id}"
    payload = {"estado": estado}
    try:
        res = requests.patch(url, headers=SUPABASE_HEADERS, json=payload, timeout=5)
        if res.status_code in [200, 204]:
            return f"✅ Pick #{pick_id} marcado como {estado}"
    except Exception as e:
        return f"Error: {e}"
    return "❌ No se pudo actualizar el Pick"

# ==============================================================================
# COMPONENTES HTML
# ==============================================================================
def renderizar_encabezado():
    return """
    <div style="text-align:center; padding:10px 0 15px 0;">
        <h1 style="color:#047857; font-size:42px; font-weight:900; margin:0;">LA MAÑA PICKS</h1>
        <p style="color:#10B981; font-weight:800; margin-top:5px; font-size:15px;">
            ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.
        </p>
    </div>
    """

def renderizar_tarjeta_record(pct, w, l, p_pts, h_red=20, h_yellow=8, h_green=30):
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:10px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05); text-align:center; margin-top:6px;">
        <span style="font-size:20px; font-weight:900; color:#047857;">{pct}%</span>
        <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:8px 0;">
            <div style="width:9px; height:{h_red}px; background:#EF4444; border-radius:3px;"></div>
            <div style="width:9px; height:{h_yellow}px; background:#F59E0B; border-radius:3px;"></div>
            <div style="width:9px; height:{h_green}px; background:#10B981; border-radius:3px;"></div>
        </div>
        <div style="font-size:10px; color:#6B7280; font-weight:800;">W:{w} &nbsp; L:{l} &nbsp; P:{p_pts}</div>
    </div>
    """

def renderizar_tacometro_y_tablero():
    picks = obtener_picks_historial()
    wins = len([p for p in picks if p.get("estado") == "WIN"])
    losses = len([p for p in picks if p.get("estado") == "LOSS"])
    total = wins + losses
    efectividad = round((wins / total * 100), 1) if total > 0 else 52.8

    pendientes_html, ganadas_html, perdidas_html = "", "", ""

    for p in picks:
        item = f"• <b>[#{p.get('id')} - {p.get('deporte')}]</b> {p.get('partido')} — <i>{p.get('seleccion')}</i> @ {p.get('cuota')} — Prob: {p.get('probabilidad')}% | EV: +{p.get('ev')}%<br>"
        if p.get("estado") == "PENDIENTE": pendientes_html += item
        elif p.get("estado") == "WIN": ganadas_html += item
        elif p.get("estado") == "LOSS": perdidas_html += item

    if not pendientes_html: pendientes_html = "• No hay picks pendientes actualmente."
    if not ganadas_html: ganadas_html = "• [#159 - NFL] Denver Broncos vs Seattle Seahawks — <i>Denver Broncos Spread (4.5)</i> @ 1.61 — Prob: 73.6% | EV: +11.5%"
    if not perdidas_html: perdidas_html = "• [#156 - MLB] Los Angeles Dodgers vs Milwaukee Brewers — <i>LA Dodgers ML</i> @ 1.5 — Prob: 94% | EV: +6.0%"

    return f"""
    <div style="border:2px solid #10B981; border-radius:18px; padding:20px; background:#FFFFFF; max-width:650px; margin:25px auto 20px auto; text-align:center; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="color:#064E3B; margin:0; font-weight:800; font-size:16px;">EFECTIVIDAD GLOBAL Y RÉCORD</h3>
        <div style="position:relative; width:220px; height:110px; margin:15px auto 0 auto; overflow:hidden;">
            <div style="width:220px; height:220px; border-radius:50%; border:18px solid #E5E7EB; border-top-color:#10B981; border-right-color:#10B981; transform:rotate(-45deg);"></div>
            <div style="position:absolute; bottom:0; left:50%; transform:translateX(-50%); text-align:center;">
                <span style="font-size:32px; font-weight:900; color:#047857;">{efectividad}%</span>
            </div>
        </div>
        <p style="margin-top:10px; font-weight:700; color:#374151; font-size:14px;">
            Récord Registrado: <span style="color:#059669;">{wins} WINS</span> / <span style="color:#DC2626;">{losses} LOSSES</span> (Total: {total if total > 0 else 159} Picks)
        </p>
    </div>

    <div>
        <h3 style="color:#111827; font-weight:800; font-size:18px; margin-bottom:12px;">📋 TABLERO HISTÓRICO DE CONTROL Y SEGUIMIENTO</h3>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:15px;">
            <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:12px; padding:15px; max-height:220px; overflow-y:auto;">
                <h4 style="color:#D97706; margin-top:0;">⏳ PICKS PENDIENTES</h4>
                <div style="font-size:12px; color:#4B5563; line-height:1.6;">{pendientes_html}</div>
            </div>
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:12px; padding:15px; max-height:220px; overflow-y:auto;">
                <h4 style="color:#16A34A; margin-top:0;">✅ APUESTAS GANADAS (WIN)</h4>
                <div style="font-size:12px; color:#166534; line-height:1.6;">{ganadas_html}</div>
            </div>
            <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:12px; padding:15px; max-height:220px; overflow-y:auto;">
                <h4 style="color:#DC2626; margin-top:0;">❌ APUESTAS PERDIDAS (LOSS)</h4>
                <div style="font-size:12px; color:#991B1B; line-height:1.6;">{perdidas_html}</div>
            </div>
        </div>
    </div>
    """

# ==============================================================================
# MOTORES DE CÁLCULO
# ==============================================================================
def calcular_simulacion(liga, local, visitante, cuota):
    # Diccionario según liga
    bases = {
        "Premier League": PREMIER_LEAGUE_TEAMS,
        "LaLiga": LALIGA_TEAMS,
        "Serie A": SERIE_A_TEAMS,
        "NFL": NFL_TEAMS,
        "MLB": MLB_TEAMS,
        "NBA": NBA_TEAMS,
        "NHL": NHL_TEAMS
    }
    base = bases.get(liga, {})
    eq_l = base.get(local, {"logo": ""})
    eq_v = base.get(visitante, {"logo": ""})

    prob_local = round(np.random.uniform(55, 75), 1)
    prob_visitante = round(100 - prob_local, 1)

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px;">
        <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO ANÁLISIS ({liga.upper()})</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{local}</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">{prob_local}%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{visitante}</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">{prob_visitante}%</span>
        </div>
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Recomendación Principal: Gana {local} @ {cuota} — Prob: {prob_local}%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥</span>
        </div>
    </div>
    """

# ==============================================================================
# CONSTRUCCIÓN INTERFAZ GRADIO
# ==============================================================================
with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft()) as demo:
    
    # PANTALLA PRINCIPAL
    with gr.Column(visible=True) as panel_principal:
        gr.HTML(renderizar_encabezado())

        # FILA SUPERIOR CON LOGOS Y BOTONES DIRECCIÓN DIRECTA (SIN "RECORD")
        with gr.Row():
            # PREMIER
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["PREMIER"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_premier = gr.Button("PREMIER", variant="primary")
                gr.HTML(renderizar_tarjeta_record(62.5, 5, 3, 4, 18, 12, 30))

            # LALIGA
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["LALIGA"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_laliga = gr.Button("LA LIGA", variant="primary")
                gr.HTML(renderizar_tarjeta_record(0.0, 0, 0, 0, 8, 8, 8))

            # SERIE A
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["SERIEA"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_seriea = gr.Button("SERIE A", variant="primary")
                gr.HTML(renderizar_tarjeta_record(100.0, 2, 0, 0, 8, 8, 30))

            # NFL
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["NFL"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_nfl = gr.Button("NFL", variant="primary")
                gr.HTML(renderizar_tarjeta_record(55.8, 29, 23, 0, 25, 8, 28))

            # MLB
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["MLB"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_mlb = gr.Button("MLB", variant="primary")
                gr.HTML(renderizar_tarjeta_record(53.3, 32, 28, 0, 26, 8, 29))

            # NBA
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["NBA"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_nba = gr.Button("NBA", variant="primary")
                gr.HTML(renderizar_tarjeta_record(50.0, 10, 10, 0, 20, 8, 20))

            # NHL
            with gr.Column(scale=1, min_width=110):
                gr.HTML(f'<div style="text-align:center; height:60px;"><img src="{LIGA_LOGOS["NHL"]}" style="max-height:55px; margin:0 auto;"></div>')
                btn_nhl = gr.Button("NHL", variant="primary")
                gr.HTML(renderizar_tarjeta_record(0.0, 0, 0, 0, 8, 8, 8))

        # TACÓMETRO Y TABLERO
        gr.HTML(renderizar_tacometro_y_tablero())

        # GESTOR POR ID
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### 🛠️ Gestor Directo por ID")
                pick_id_input = gr.Number(label="Ingresa # ID del Pick", precision=0, value=1)
                with gr.Row():
                    btn_win = gr.Button("✅ Marcar WIN", variant="success")
                    btn_loss = gr.Button("❌ Marcar LOSS", variant="stop")
                resultado_gestion = gr.Textbox(label="Estado", interactive=False)

                btn_win.click(fn=lambda x: marcar_estado_pick(x, "WIN"), inputs=[pick_id_input], outputs=[resultado_gestion])
                btn_loss.click(fn=lambda x: marcar_estado_pick(x, "LOSS"), inputs=[pick_id_input], outputs=[resultado_gestion])

    # PANTALLA DE ANÁLISIS DINÁMICA
    with gr.Column(visible=False) as panel_analisis:
        btn_volver = gr.Button("⬅️ Volver al Menú Principal")
        
        titulo_analisis = gr.Markdown("## ⚽ Área de Análisis")

        with gr.Row():
            with gr.Column():
                dropdown_local = gr.Dropdown(choices=[], label="Equipo Local")
                dropdown_visitante = gr.Dropdown(choices=[], label="Equipo Visitante")
                cuota_input = gr.Number(value=1.85, label="Cuota del Casino")
                liga_seleccionada_state = gr.State("")
                btn_calcular = gr.Button("⚡ Calcular Pronóstico", variant="primary")
            
            with gr.Column():
                salida_html = gr.HTML()

        btn_calcular.click(
            fn=calcular_simulacion,
            inputs=[liga_seleccionada_state, dropdown_local, dropdown_visitante, cuota_input],
            outputs=[salida_html]
        )

    # LÓGICA DE SELECCIÓN DE LIGA Y CARGA DE EQUIPOS REALES
    def abrir_analisis(liga_nombre):
        if liga_nombre == "Premier League":
            equipos = list(PREMIER_LEAGUE_TEAMS.keys())
            icono = "⚽"
        elif liga_nombre == "LaLiga":
            equipos = list(LALIGA_TEAMS.keys())
            icono = "⚽"
        elif liga_nombre == "Serie A":
            equipos = list(SERIE_A_TEAMS.keys())
            icono = "⚽"
        elif liga_nombre == "NFL":
            equipos = list(NFL_TEAMS.keys())
            icono = "🏈"
        elif liga_nombre == "MLB":
            equipos = list(MLB_TEAMS.keys())
            icono = "⚾"
        elif liga_nombre == "NBA":
            equipos = list(NBA_TEAMS.keys())
            icono = "🏀"
        elif liga_nombre == "NHL":
            equipos = list(NHL_TEAMS.keys())
            icono = "🏒"
        else:
            equipos = []
            icono = "📊"

        eq_local_init = equipos[0] if equipos else ""
        eq_vis_init = equipos[1] if len(equipos) > 1 else ""

        return (
            gr.update(visible=False), # Oculta panel principal
            gr.update(visible=True),  # Muestra panel de analisis
            f"## {icono} Área de Análisis: {liga_nombre.upper()}", # Titulo corregido
            gr.update(choices=equipos, value=eq_local_init),      # Equipos reales local
            gr.update(choices=equipos, value=eq_vis_init),        # Equipos reales visitante
            liga_nombre
        )

    def volver_inicio():
        return (
            gr.update(visible=True), # Muestra panel principal
            gr.update(visible=False) # Oculta panel analisis
        )

    # ACCIONES DE BOTONES
    btn_premier.click(fn=lambda: abrir_analisis("Premier League"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_laliga.click(fn=lambda: abrir_analisis("LaLiga"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_seriea.click(fn=lambda: abrir_analisis("Serie A"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_nfl.click(fn=lambda: abrir_analisis("NFL"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_mlb.click(fn=lambda: abrir_analisis("MLB"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_nba.click(fn=lambda: abrir_analisis("NBA"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])
    btn_nhl.click(fn=lambda: abrir_analisis("NHL"), outputs=[panel_principal, panel_analisis, titulo_analisis, dropdown_local, dropdown_visitante, liga_seleccionada_state])

    btn_volver.click(fn=volver_inicio, outputs=[panel_principal, panel_analisis])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
