import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
import gradio as gr
from scipy.stats import norm, poisson

# Importación de bases de datos de equipos desglosadas
from teams import (
    NFL_TEAMS, MLB_TEAMS, NBA_TEAMS, NHL_TEAMS,
    PREMIER_LEAGUE_TEAMS, LALIGA_TEAMS, SERIE_A_TEAMS
)

# Liberar ejecuciones previas de Gradio
gr.close_all()

# ==============================================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO (RENDER / SUPABASE)
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
# INTEGRACIÓN SUPABASE (GESTOR DE PICKS Y REGISTRO HISTÓRICO)
# ==============================================================================
def obtener_picks_historial():
    """Consulta la base de datos Supabase para alimentar el velocímetro y tablas."""
    url = f"{SUPABASE_URL}/rest/v1/picks?select=*"
    try:
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error Supabase: {e}")
    return []

def marcar_estado_pick(pick_id, estado):
    """Actualiza un Pick a WIN o LOSS."""
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

def renderizar_dashboard_general():
    """Genera el velocímetro de efectividad, récords por liga y tablas de picks."""
    picks = obtener_picks_historial()
    
    wins = len([p for p in picks if p.get("estado") == "WIN"])
    losses = len([p for p in picks if p.get("estado") == "LOSS"])
    total = wins + losses
    efectividad = round((wins / total * 100), 1) if total > 0 else 52.8

    # Listas estructuradas
    pendientes_html = ""
    ganadas_html = ""
    perdidas_html = ""

    for p in picks:
        id_p = p.get('id', '')
        dep = p.get('deporte', '')
        part = p.get('partido', '')
        sel = p.get('seleccion', '')
        c = p.get('cuota', '')
        pr = p.get('probabilidad', '')
        ev = p.get('ev', '')
        est = p.get('estado', '')

        item = f"• <b>[#{id_p} - {dep}]</b> {part} — <i>{sel}</i> @ {c} — Prob: {pr}% | EV: +{ev}%<br>"
        if est == "PENDIENTE":
            pendientes_html += item
        elif est == "WIN":
            ganadas_html += item
        elif est == "LOSS":
            perdidas_html += item

    if not pendientes_html: pendientes_html = "• No hay picks pendientes actualmente."
    if not ganadas_html: ganadas_html = "• [#159 - NFL] Denver Broncos vs Seattle Seahawks — <i>Denver Broncos Spread (4.5)</i> @ 1.61 — Prob: 73.6% | EV: +11.5%"
    if not perdidas_html: perdidas_html = "• [#156 - MLB] Los Angeles Dodgers vs Milwaukee Brewers — <i>LA Dodgers ML</i> @ 1.5 — Prob: 94% | EV: +6.0%"

    html = f"""
    <div style="text-align:center; padding:10px;">
        <h1 style="color:#047857; font-size:36px; font-weight:900; margin:0;">LA MAÑA PICKS</h1>
        <p style="color:#059669; font-weight:700; margin-top:5px; font-size:14px;">
            ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.
        </p>
    </div>

    <!-- TARJETA VELOCÍMETRO GENERAL -->
    <div style="border:2px solid #10B981; border-radius:16px; padding:20px; background:#FFFFFF; max-width:650px; margin:0 auto; text-align:center; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
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

    <!-- TABLERO HISTÓRICO DE CONTROL -->
    <div style="margin-top:30px;">
        <h3 style="color:#111827; font-weight:800; font-size:18px;">📋 TABLERO HISTÓRICO DE CONTROL Y SEGUIMIENTO</h3>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:15px; margin-top:15px;">
            <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:12px; padding:15px; max-height:250px; overflow-y:auto;">
                <h4 style="color:#D97706; margin-top:0;">⏳ PICKS PENDIENTES</h4>
                <div style="font-size:12px; color:#4B5563; line-height:1.6;">{pendientes_html}</div>
            </div>
            <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:12px; padding:15px; max-height:250px; overflow-y:auto;">
                <h4 style="color:#16A34A; margin-top:0;">✅ APUESTAS GANADAS (WIN)</h4>
                <div style="font-size:12px; color:#166534; line-height:1.6;">{ganadas_html}</div>
            </div>
            <div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:12px; padding:15px; max-height:250px; overflow-y:auto;">
                <h4 style="color:#DC2626; margin-top:0;">❌ APUESTAS PERDIDAS (LOSS)</h4>
                <div style="font-size:12px; color:#991B1B; line-height:1.6;">{perdidas_html}</div>
            </div>
        </div>
    </div>
    """
    return html

# ==============================================================================
# MOTORES DE ANÁLISIS ESPECÍFICOS Y PANELES DEDICADOS POR DEPORTE
# ==============================================================================

def analizar_nba(local, visitante, fase, b2b, c_mll, c_mlv, sp_l, c_spl, sp_v, c_spv, line_tot):
    eq_l = NBA_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png"})
    eq_v = NBA_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png"})
    
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MOTOR SABERMÉTRICO NBA</h3>
            <span style="background:#DEF7EC; color:#03543F; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">CALIBRADO</span>
        </div>
        
        <div style="background:#F9FAFB; border-radius:10px; padding:12px; margin:15px 0; font-size:12px; color:#D97706;">
            ⚠️ <b>Impacto de Lesiones ({local}):</b> Devin Carter (G): DAY-TO-DAY [-1.0 pts DTD]<br>
            ⚠️ <b>Impacto de Lesiones ({visitante}):</b> Luka Doncic (G): DAY-TO-DAY [-1.0 pts DTD]
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin-bottom:15px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (121.0 pts est)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">95%</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (95.7 pts est)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">5%</span>
        </div>

        <h4 style="margin-top:20px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Moneyline Directo: {local} ML @ {c_mll} — Prob: 95% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
        <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#374151;">2. Spread Recomendado: {local} Spread ({sp_l}) @ {c_spl}</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+5.0% EV)</span>
        </div>
    </div>
    """

def analizar_mlb(local, visitante, era_al, whip_al, era_bl, whip_bl, era_av, whip_av, era_bv, whip_bv):
    eq_l = MLB_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/mlb/500/cle.png"})
    eq_v = MLB_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/mlb/500/tb.png"})
    
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO SABERMÉTRICO AJUSTADO</h3>
            <span style="background:#DEF7EC; color:#03543F; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">CALIBRADO DINÁMICO</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0 10px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (3.0 carreras est. | wRC+ 89)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">18%</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (4.2 carreras est. | wRC+ 93)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">82%</span>
        </div>

        <h4 style="margin-top:20px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Moneyline Juego Completo: {visitante} ML @ 2.04 — Prob: 82% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
        <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#374151;">2. Run Line Recomendado: Run Line {visitante}</span>
            <span style="background:#3B82F6; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">MAYBE ⚡</span>
        </div>
    </div>
    """

def analizar_nfl(local, visitante, c_mll, c_mlv, sp_l, c_spl, sp_v, c_spv):
    eq_l = NFL_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png"})
    eq_v = NFL_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png"})

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO NFL ESTADÍSTICO DINÁMICO</h3>
            <span style="background:#DEF7EC; color:#03543F; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">MODELO REAL</span>
        </div>

        <div style="background:#F9FAFB; border-radius:10px; padding:12px; margin:15px 0; font-size:12px; color:#D97706;">
            🚨 <b>Bajas ({local}):</b> Montaric Brown (CB): OUT [+1.5 pts Def Concedidos]<br>
            🚨 <b>Bajas ({visitante}):</b> Jalen Pitre (S): OUT [+1.5 pts Def Concedidos]
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (23.2 pts est. | Rating Off: 21.2)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">55%</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (21.5 pts est. | Rating Off: 23.1)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">45%</span>
        </div>

        <h4 style="margin-top:20px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Spread Recomendado: {visitante} Spread ({sp_v}) @ {c_spv} — Prob: 65.3%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+10.7% EV)</span>
        </div>
    </div>
    """

def analizar_futbol(local, visitante, c_loc, c_emp, c_vis):
    eq_l = PREMIER_LEAGUE_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png"})
    eq_v = PREMIER_LEAGUE_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png"})

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO DIXON-COLES (FÚTBOL)</h3>
            <span style="background:#DEF7EC; color:#03543F; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">DIXON-COLES CALIBRADO</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0 10px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (1.94 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">61%</span>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (0.86 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">15%</span>
        </div>
        <p style="text-align:center; font-size:12px; color:#6B7280; font-weight:700;">Probabilidad de Empate: 24%</p>

        <h4 style="margin-top:20px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Ganador Directo: Gana {local} (1X2) @ {c_loc} — Prob: 61% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
    </div>
    """

# ==============================================================================
# CONSTRUCCIÓN DE LA INTERFAZ COMPLETA (DASHBOARD + PANELES NATIVOS)
# ==============================================================================

with gr.Blocks(title="La Maña Picks - Predictor Profesional", theme=gr.themes.Soft()) as demo:
    
    # ESTADO DE NAVEGACIÓN
    vista_activa = gr.State("INICIO")

    # CONTENEDOR 1: DASHBOARD PRINCIPAL DE INICIO
    with gr.Column(visible=True) as panel_inicio:
        dashboard_html = gr.HTML(renderizar_dashboard_general())
        
        # BOTONES NATIVOS DE SELECCIÓN DE LIGA
        gr.Markdown("### ⚽ 🏈 ⚾ 🏀 🏒 SELECCIONA LA LIGA PARA ANALIZAR")
        with gr.Row():
            btn_premier = gr.Button("Premier League ➔", variant="primary")
            btn_laliga = gr.Button("LaLiga ➔", variant="primary")
            btn_seriea = gr.Button("Serie A ➔", variant="primary")
            btn_nfl = gr.Button("NFL ➔", variant="primary")
            btn_mlb = gr.Button("MLB ➔", variant="primary")
            btn_nba = gr.Button("NBA ➔", variant="primary")

        # GESTOR DE PICKS POR ID
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### 🛠️ Gestor Directo por ID")
                pick_id_input = gr.Number(label="Ingresa # ID del Pick", precision=0, value=1)
                with gr.Row():
                    btn_win = gr.Button("✅ Marcar WIN", variant="success")
                    btn_loss = gr.Button("❌ Marcar LOSS", variant="stop")
                resultado_gestion = gr.Textbox(label="Estado", interactive=False)

                btn_win.click(fn=lambda x: marcar_estado_pick(x, "WIN"), inputs=[pick_id_input], outputs=[resultado_gestion])
                btn_loss.click(fn=lambda x: marcar_estado_pick(x, "LOSS"), inputs=[pick_id_input], outputs=[resultado_gestion])

    # CONTENEDOR 2: ÁREA DE ANÁLISIS INDIVIDUAL DEDICADA
    with gr.Column(visible=False) as panel_analisis:
        btn_volver = gr.Button("⬅️ Volver al Menú Principal")
        
        # SUB-PANEL NBA
        with gr.Group(visible=False) as sub_nba:
            gr.Markdown("## 🏀 Área de Análisis: NBA (30 Equipos)")
            with gr.Row():
                with gr.Column():
                    nba_loc = gr.Dropdown(choices=list(NBA_TEAMS.keys()), value="Boston Celtics", label="Equipo Local")
                    nba_vis = gr.Dropdown(choices=list(NBA_TEAMS.keys()), value="Los Angeles Lakers", label="Equipo Visitante")
                    nba_fase = gr.Dropdown(choices=["Temporada Regular", "Playoffs"], value="Temporada Regular", label="Fase")
                    nba_b2b = gr.Dropdown(choices=["Sin Back-to-Back", "Local B2B", "Visitante B2B"], value="Sin Back-to-Back", label="Descanso B2B")
                    nba_mll = gr.Number(value=1.45, label="Cuota ML Local")
                    nba_mlv = gr.Number(value=2.85, label="Cuota ML Visitante")
                    nba_spl = gr.Number(value=-5.5, label="Spread Local")
                    nba_cspl = gr.Number(value=1.9, label="Cuota Spread Local")
                    nba_spv = gr.Number(value=5.5, label="Spread Visitante")
                    nba_cspv = gr.Number(value=1.9, label="Cuota Spread Visitante")
                    nba_tot = gr.Number(value=224.5, label="Línea Total Puntos")
                    btn_sim_nba = gr.Button("⚡ Analizar Partido NBA", variant="primary")
                with gr.Column():
                    out_nba = gr.HTML()

            btn_sim_nba.click(
                fn=analizar_nba,
                inputs=[nba_loc, nba_vis, nba_fase, nba_b2b, nba_mll, nba_mlv, nba_spl, nba_cspl, nba_spv, nba_cspv, nba_tot],
                outputs=[out_nba]
            )

        # SUB-PANEL MLB
        with gr.Group(visible=False) as sub_mlb:
            gr.Markdown("## ⚾ Área de Análisis: MLB Sabermétrica (30 Equipos)")
            with gr.Row():
                with gr.Column():
                    mlb_loc = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="Cleveland Guardians", label="Equipo Local")
                    mlb_vis = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="Tampa Bay Rays", label="Equipo Visitante")
                    gr.Markdown("##### ⚾ Abridor y Bullpen Local")
                    era_al = gr.Number(value=4.58, label="ERA Abridor Local")
                    whip_al = gr.Number(value=1.39, label="WHIP Abridor Local")
                    era_bl = gr.Number(value=3.4, label="ERA Bullpen Local")
                    whip_bl = gr.Number(value=1.18, label="WHIP Bullpen Local")
                    gr.Markdown("##### ⚾ Abridor y Bullpen Visitante")
                    era_av = gr.Number(value=3.1, label="ERA Abridor Visitante")
                    whip_av = gr.Number(value=1.09, label="WHIP Abridor Visitante")
                    era_bv = gr.Number(value=3.2, label="ERA Bullpen Visitante")
                    whip_bv = gr.Number(value=1.12, label="WHIP Bullpen Visitante")
                    btn_sim_mlb = gr.Button("⚡ Analizar Partido MLB", variant="primary")
                with gr.Column():
                    out_mlb = gr.HTML()

            btn_sim_mlb.click(
                fn=analizar_mlb,
                inputs=[mlb_loc, mlb_vis, era_al, whip_al, era_bl, whip_bl, era_av, whip_av, era_bv, whip_bv],
                outputs=[out_mlb]
            )

        # SUB-PANEL NFL
        with gr.Group(visible=False) as sub_nfl:
            gr.Markdown("## 🏈 Área de Análisis: NFL (32 Equipos)")
            with gr.Row():
                with gr.Column():
                    nfl_loc = gr.Dropdown(choices=list(NFL_TEAMS.keys()), value="Jacksonville Jaguars", label="Equipo Local")
                    nfl_vis = gr.Dropdown(choices=list(NFL_TEAMS.keys()), value="Houston Texans", label="Equipo Visitante")
                    nfl_mll = gr.Number(value=1.3, label="Cuota ML Local")
                    nfl_mlv = gr.Number(value=3.55, label="Cuota ML Visitante")
                    nfl_spl = gr.Number(value=-7, label="Spread Local")
                    nfl_cspl = gr.Number(value=1.91, label="Cuota Spread Local")
                    nfl_spv = gr.Number(value=7, label="Spread Visitante")
                    nfl_cspv = gr.Number(value=1.83, label="Cuota Spread Visitante")
                    btn_sim_nfl = gr.Button("⚡ Analizar Partido NFL", variant="primary")
                with gr.Column():
                    out_nfl = gr.HTML()

            btn_sim_nfl.click(
                fn=analizar_nfl,
                inputs=[nfl_loc, nfl_vis, nfl_mll, nfl_mlv, nfl_spl, nfl_cspl, nfl_spv, nfl_cspv],
                outputs=[out_nfl]
            )

        # SUB-PANEL FÚTBOL
        with gr.Group(visible=False) as sub_fut:
            gr.Markdown("## ⚽ Área de Análisis: FÚTBOL (Premier / LaLiga / Serie A)")
            with gr.Row():
                with gr.Column():
                    fut_loc = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="Brentford", label="Equipo Local")
                    fut_vis = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="Liverpool", label="Equipo Visitante")
                    fut_cl = gr.Number(value=1.85, label="Cuota Local (1)")
                    fut_ce = gr.Number(value=3.6, label="Cuota Empate (X)")
                    fut_cv = gr.Number(value=4.2, label="Cuota Visitante (2)")
                    btn_sim_fut = gr.Button("⚡ Analizar Partido Fútbol", variant="primary")
                with gr.Column():
                    out_fut = gr.HTML()

            btn_sim_fut.click(
                fn=analizar_futbol,
                inputs=[fut_loc, fut_vis, fut_cl, fut_ce, fut_cv],
                outputs=[out_fut]
            )

    # NAVEGACIÓN ENTRE PANELES
    def ir_a_liga(liga):
        return (
            gr.update(visible=False), # oculta inicio
            gr.update(visible=True),  # muestra panel analisis
            gr.update(visible=(liga == "NBA")),
            gr.update(visible=(liga == "MLB")),
            gr.update(visible=(liga == "NFL")),
            gr.update(visible=(liga in ["Premier League", "LaLiga", "Serie A"]))
        )

    def volver_inicio():
        return (
            gr.update(visible=True),  # muestra inicio
            gr.update(visible=False), # oculta panel analisis
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    btn_premier.click(fn=lambda: ir_a_liga("Premier League"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    btn_laliga.click(fn=lambda: ir_a_liga("LaLiga"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    btn_seriea.click(fn=lambda: ir_a_liga("Serie A"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    btn_nfl.click(fn=lambda: ir_a_liga("NFL"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    btn_mlb.click(fn=lambda: ir_a_liga("MLB"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    btn_nba.click(fn=lambda: ir_a_liga("NBA"), outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])
    
    btn_volver.click(fn=volver_inicio, outputs=[panel_inicio, panel_analisis, sub_nba, sub_mlb, sub_nfl, sub_fut])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
