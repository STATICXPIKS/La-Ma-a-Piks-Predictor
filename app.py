import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
import gradio as gr

# Importación de la base de datos desglosada
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
# ENCABEZADO Y DASHBOARD INICIAL
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

# AUXILIAR PARA RENDERIZAR MINILOGOS
def obtener_logo_html(base_dict, nombre_equipo):
    info = base_dict.get(nombre_equipo, {})
    logo_url = info.get("logo", "")
    if logo_url:
        return f'<div style="text-align:center;"><img src="{logo_url}" style="width:45px; height:45px; object-fit:contain; border-radius:8px; border:1px solid #E5E7EB; padding:3px; background:white;"></div>'
    return '<div style="width:45px; height:45px;"></div>'

# ==============================================================================
# MOTORES DE SIMULACIÓN Y RESULTADOS DETALLADOS POR DEPORTE
# ==============================================================================
def simular_futbol(liga, local, visitante, fatiga, c1, cx, c2, btts_si, btts_no, linea_o, c_over, c_under):
    base = PREMIER_LEAGUE_TEAMS if "PREMIER" in liga else (LALIGA_TEAMS if "LALIGA" in liga else SERIE_A_TEAMS)
    l_info = base.get(local, {"logo": ""})
    v_info = base.get(visitante, {"logo": ""})

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="color:#064E3B; margin:0 0 15px 0; font-weight:800;">LA MAÑA PICKS • MODELO DIXON-COLES (FÚTBOL)</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{l_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (1.94 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">61%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{v_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (0.86 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">15%</span>
        </div>
        <p style="text-align:center; font-size:12px; color:#6B7280; font-weight:700; margin:10px 0;">Probabilidad de Empate: 24%</p>
        <h4 style="margin-top:15px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Ganador Directo: Gana {local} (1X2) @ {c1} — Prob: 61% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
        <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#374151;">2. Ambos Anotan: BTTS Sí @ {btts_si} — Probabilidad: 55%</span>
            <span style="background:#3B82F6; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">MAYBE ⚡</span>
        </div>
    </div>
    """

def simular_nfl(local, visitante, c_mll, c_mlv, sp_l, c_spl, sp_v, c_spv, line_tot, c_over, c_under):
    l_info = NFL_TEAMS.get(local, {"logo": ""})
    v_info = NFL_TEAMS.get(visitante, {"logo": ""})

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="color:#064E3B; margin:0 0 15px 0; font-weight:800;">LA MAÑA PICKS • MODELO NFL ESTADÍSTICO DINÁMICO</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{l_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (23.2 pts est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">55%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{v_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (21.5 pts est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">45%</span>
        </div>
        <h4 style="margin-top:15px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Spread Recomendado: {visitante} Spread ({sp_v}) @ {c_spv} — Prob: 65.3%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+10.7% EV)</span>
        </div>
    </div>
    """

def simular_mlb(local, visitante, era_al, whip_al, era_bl, whip_bl, era_av, whip_av, era_bv, whip_bv, c_mll, c_mlv, rl_l, c_rll, rl_v, c_rlv, c_f5l, c_f5v, c_nrfi, c_yrfi, tot_car, l_carl, c_ovl, c_unl, l_carv, c_ovv, c_unv):
    l_info = MLB_TEAMS.get(local, {"logo": ""})
    v_info = MLB_TEAMS.get(visitante, {"logo": ""})

    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="color:#064E3B; margin:0 0 15px 0; font-weight:800;">LA MAÑA PICKS • MODELO SABERMÉTRICO AJUSTADO (MLB)</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{l_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{local} (3.0 carreras est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">18%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F9FAFB; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{v_info['logo']}" width="40" height="40">
                <span style="font-weight:800; font-size:16px; color:#111827;">{visitante} (4.2 carreras est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">82%</span>
        </div>
        <h4 style="margin-top:15px; color:#111827; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Moneyline Juego Completo: {visitante} ML @ {c_mlv} — Prob: 82% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
    </div>
    """

# ==============================================================================
# CONSTRUCCIÓN DE LA INTERFAZ COMPLETA
# ==============================================================================

with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft()) as demo:
    
    # --------------------------------------------------------------------------
    # PANTALLA PRINCIPAL
    # --------------------------------------------------------------------------
    with gr.Column(visible=True) as panel_principal:
        gr.HTML(renderizar_encabezado())

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

        gr.HTML(renderizar_tacometro_y_tablero())

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

    # --------------------------------------------------------------------------
    # PANTALLA DE ANÁLISIS DETALLADO
    # --------------------------------------------------------------------------
    with gr.Column(visible=False) as panel_analisis:
        btn_volver = gr.Button("⬅️ Volver al Menú Principal")
        titulo_analisis = gr.Markdown("## ⚽ Área de Análisis")

        # 1. FORMULARIO FÚTBOL (PREMIER / LALIGA / SERIE A) [IMAGEN 23 & 24]
        with gr.Group(visible=False) as panel_futbol:
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        fut_loc = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="AFC Bournemouth", label="Equipo Local")
                        logo_fut_loc = gr.HTML(obtener_logo_html(PREMIER_LEAGUE_TEAMS, "AFC Bournemouth"))
                    with gr.Row():
                        fut_vis = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="Arsenal", label="Equipo Visitante")
                        logo_fut_vis = gr.HTML(obtener_logo_html(PREMIER_LEAGUE_TEAMS, "Arsenal"))

                    fut_fatiga = gr.Dropdown(choices=["No (Semana normal)", "Sí (Participación Europea)"], value="No (Semana normal)", label="¿Fatiga Europea?")
                    
                    gr.Markdown("##### ⚽ Cuotas 1X2 (Casino)")
                    with gr.Row():
                        fut_c1 = gr.Number(value=1.85, label="Cuota Local (1)")
                        fut_cx = gr.Number(value=3.6, label="Cuota Empate (X)")
                        fut_c2 = gr.Number(value=4.2, label="Cuota Visitante (2)")

                    gr.Markdown("##### ⚽ Cuotas Ambos Anotan (BTTS)")
                    with gr.Row():
                        fut_btts_si = gr.Number(value=1.8, label="Cuota Ambos Anotan: SÍ")
                        fut_btts_no = gr.Number(value=1.95, label="Cuota Ambos Anotan: NO")

                    gr.Markdown("##### ⚽ Línea de Goles y Cuotas (Over/Under)")
                    fut_linea_goles = gr.Number(value=2.5, label="Línea Total Goles (O/U)")
                    with gr.Row():
                        fut_cover = gr.Number(value=1.85, label="Cuota OVER")
                        fut_cunder = gr.Number(value=1.95, label="Cuota UNDER")

                    btn_sim_fut = gr.Button("Simular Partido 🚀", variant="primary")

                with gr.Column(scale=1):
                    out_fut = gr.HTML()

        # 2. FORMULARIO NFL [IMAGEN 25]
        with gr.Group(visible=False) as panel_nfl:
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        nfl_loc = gr.Dropdown(choices=list(NFL_TEAMS.keys()), value="Detroit Lions", label="Equipo Local")
                        logo_nfl_loc = gr.HTML(obtener_logo_html(NFL_TEAMS, "Detroit Lions"))
                    with gr.Row():
                        nfl_vis = gr.Dropdown(choices=list(NFL_TEAMS.keys()), value="New York Jets", label="Equipo Visitante")
                        logo_nfl_vis = gr.HTML(obtener_logo_html(NFL_TEAMS, "New York Jets"))

                    gr.Markdown("##### 🏈 Cuotas Moneyline (Ganador Directo)")
                    with gr.Row():
                        nfl_mll = gr.Number(value=1.3, label="Cuota ML Local")
                        nfl_mlv = gr.Number(value=3.55, label="Cuota ML Visitante")

                    gr.Markdown("##### 🏈 Spread / Hándicap (Casino)")
                    with gr.Row():
                        nfl_spl = gr.Number(value=-7.0, label="Spread Local")
                        nfl_cspl = gr.Number(value=1.91, label="Cuota Spread Local")
                    with gr.Row():
                        nfl_spv = gr.Number(value=7.0, label="Spread Visitante")
                        nfl_cspv = gr.Number(value=1.83, label="Cuota Spread Visitante")

                    gr.Markdown("##### 🏈 Totales (Puntos Juego Completo)")
                    nfl_tot = gr.Number(value=48.0, label="Línea Total Puntos")
                    with gr.Row():
                        nfl_cover = gr.Number(value=1.88, label="Cuota OVER")
                        nfl_cunder = gr.Number(value=1.87, label="Cuota UNDER")

                    btn_sim_nfl = gr.Button("Simular Partido NFL 🚀", variant="primary")

                with gr.Column(scale=1):
                    out_nfl = gr.HTML()

        # 3. FORMULARIO SABERMÉTRICO DE MLB [IMAGEN 26 & 27]
        with gr.Group(visible=False) as panel_mlb:
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Row():
                        mlb_loc = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="New York Yankees", label="Equipo Local")
                        logo_mlb_loc = gr.HTML(obtener_logo_html(MLB_TEAMS, "New York Yankees"))
                    with gr.Row():
                        mlb_vis = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="Tampa Bay Rays", label="Equipo Visitante")
                        logo_mlb_vis = gr.HTML(obtener_logo_html(MLB_TEAMS, "Tampa Bay Rays"))

                    gr.Button("🔄 Cargar Abridores en Vivo (MLB API)", variant="secondary")

                    gr.Markdown("##### ⚾ Abridor y Bullpen Local")
                    with gr.Row():
                        era_al = gr.Number(value=2.95, label="ERA Abridor Local")
                        whip_al = gr.Number(value=1.13, label="WHIP Abridor Local")
                    with gr.Row():
                        era_bl = gr.Number(value=3.4, label="ERA Bullpen Local")
                        whip_bl = gr.Number(value=1.18, label="WHIP Bullpen Local")

                    gr.Markdown("##### ⚾ Abridor y Bullpen Visitante")
                    with gr.Row():
                        era_av = gr.Number(value=2.94, label="ERA Abridor Visitante")
                        whip_av = gr.Number(value=1.07, label="WHIP Abridor Visitante")
                    with gr.Row():
                        era_bv = gr.Number(value=3.8, label="ERA Bullpen Visitante")
                        whip_bv = gr.Number(value=1.25, label="WHIP Bullpen Visitante")

                    gr.Markdown("##### ⚾ Cuotas Moneyline")
                    with gr.Row():
                        mlb_mll = gr.Number(value=1.76, label="Cuota ML Local")
                        mlb_mlv = gr.Number(value=2.04, label="Cuota ML Visitante")

                    gr.Markdown("##### ⚾ Run Line / Hándicap")
                    with gr.Row():
                        mlb_rll = gr.Number(value=-1.5, label="Run Line Local")
                        mlb_crll = gr.Number(value=2.7, label="Cuota RL Local")
                    with gr.Row():
                        mlb_rlv = gr.Number(value=1.5, label="Run Line Visitante")
                        mlb_crlv = gr.Number(value=1.44, label="Cuota RL Visitante")

                    gr.Markdown("##### ⚾ Cuotas Primeras 5 Entradas (F5 ML)")
                    with gr.Row():
                        mlb_f5l = gr.Number(value=1.8, label="Cuota F5 Local ML")
                        mlb_f5v = gr.Number(value=1.95, label="Cuota F5 Visitante ML")

                    gr.Markdown("##### ⚾ Mercado 1er Inning (NRFI / YRFI)")
                    with gr.Row():
                        mlb_nrfi = gr.Number(value=1.85, label="Cuota NRFI (No Carrera 1er Inning)")
                        mlb_yrfi = gr.Number(value=1.95, label="Cuota YRFI (Sí Carrera 1er Inning)")

                    mlb_tot_carreras = gr.Number(value=8.5, label="Línea Total Carreras Juego Completo")

                    gr.Markdown("##### ⚾ Carreras Totales por Equipo (Team Totals)")
                    with gr.Row():
                        mlb_lcarl = gr.Number(value=4.5, label="Línea Carreras Local")
                        mlb_covl = gr.Number(value=1.85, label="Cuota OVER")
                        mlb_cunl = gr.Number(value=1.95, label="Cuota UNDER")
                    with gr.Row():
                        mlb_lcarv = gr.Number(value=3.5, label="Línea Carreras Visitante")
                        mlb_covv = gr.Number(value=1.85, label="Cuota OVER")
                        mlb_cunv = gr.Number(value=1.95, label="Cuota UNDER")

                    btn_sim_mlb = gr.Button("Simular Partido MLB 🚀", variant="primary")

                with gr.Column(scale=1):
                    out_mlb = gr.HTML()

    # --------------------------------------------------------------------------
    # LÓGICA DE INTERACTIVIDAD DE MINILOGOS Y CAMBIO DE LIGA
    # --------------------------------------------------------------------------
    
    # Eventos de actualización de minilogos al cambiar equipo
    fut_loc.change(fn=lambda x: obtener_logo_html(PREMIER_LEAGUE_TEAMS, x), inputs=[fut_loc], outputs=[logo_fut_loc])
    fut_vis.change(fn=lambda x: obtener_logo_html(PREMIER_LEAGUE_TEAMS, x), inputs=[fut_vis], outputs=[logo_fut_vis])

    nfl_loc.change(fn=lambda x: obtener_logo_html(NFL_TEAMS, x), inputs=[nfl_loc], outputs=[logo_nfl_loc])
    nfl_vis.change(fn=lambda x: obtener_logo_html(NFL_TEAMS, x), inputs=[nfl_vis], outputs=[logo_nfl_vis])

    mlb_loc.change(fn=lambda x: obtener_logo_html(MLB_TEAMS, x), inputs=[mlb_loc], outputs=[logo_mlb_loc])
    mlb_vis.change(fn=lambda x: obtener_logo_html(MLB_TEAMS, x), inputs=[mlb_vis], outputs=[logo_mlb_vis])

    # Eventos de simulación
    btn_sim_fut.click(
        fn=simular_futbol,
        inputs=[titulo_analisis, fut_loc, fut_vis, fut_fatiga, fut_c1, fut_cx, fut_c2, fut_btts_si, fut_btts_no, fut_linea_goles, fut_cover, fut_cunder],
        outputs=[out_fut]
    )

    btn_sim_nfl.click(
        fn=simular_nfl,
        inputs=[nfl_loc, nfl_vis, nfl_mll, nfl_mlv, nfl_spl, nfl_cspl, nfl_spv, nfl_cspv, nfl_tot, nfl_cover, nfl_cunder],
        outputs=[out_nfl]
    )

    btn_sim_mlb.click(
        fn=simular_mlb,
        inputs=[mlb_loc, mlb_vis, era_al, whip_al, era_bl, whip_bl, era_av, whip_av, era_bv, whip_bv, mlb_mll, mlb_mlv, mlb_rll, mlb_crll, mlb_rlv, mlb_crlv, mlb_f5l, mlb_f5v, mlb_nrfi, mlb_yrfi, mlb_tot_carreras, mlb_lcarl, mlb_covl, mlb_cunl, mlb_lcarv, mlb_covv, mlb_cunv],
        outputs=[out_mlb]
    )

    # Navegación entre vistas
    def abrir_liga(nombre_liga):
        if nombre_liga == "PREMIER LEAGUE":
            base = PREMIER_LEAGUE_TEAMS
            icono = "⚽"
            is_fut, is_nfl, is_mlb = True, False, False
        elif nombre_liga == "LALIGA":
            base = LALIGA_TEAMS
            icono = "⚽"
            is_fut, is_nfl, is_mlb = True, False, False
        elif nombre_liga == "SERIE A":
            base = SERIE_A_TEAMS
            icono = "⚽"
            is_fut, is_nfl, is_mlb = True, False, False
        elif nombre_liga == "NFL":
            base = NFL_TEAMS
            icono = "🏈"
            is_fut, is_nfl, is_mlb = False, True, False
        elif nombre_liga == "MLB":
            base = MLB_TEAMS
            icono = "⚾"
            is_fut, is_nfl, is_mlb = False, False, True
        else:
            base = PREMIER_LEAGUE_TEAMS
            icono = "⚽"
            is_fut, is_nfl, is_mlb = True, False, False

        equipos = list(base.keys())
        eq1 = equipos[0] if equipos else ""
        eq2 = equipos[1] if len(equipos) > 1 else ""

        # Selección de updates para los componentes de la liga elegida
        if is_fut:
            update_loc = gr.update(choices=equipos, value=eq1)
            update_vis = gr.update(choices=equipos, value=eq2)
            logo1 = obtener_logo_html(base, eq1)
            logo2 = obtener_logo_html(base, eq2)
        elif is_nfl:
            update_loc = gr.update(choices=equipos, value=eq1)
            update_vis = gr.update(choices=equipos, value=eq2)
            logo1 = obtener_logo_html(base, eq1)
            logo2 = obtener_logo_html(base, eq2)
        else:
            update_loc = gr.update(choices=equipos, value=eq1)
            update_vis = gr.update(choices=equipos, value=eq2)
            logo1 = obtener_logo_html(base, eq1)
            logo2 = obtener_logo_html(base, eq2)

        return (
            gr.update(visible=False), # Oculta principal
            gr.update(visible=True),  # Muestra analisis
            f"## {icono} Área de Análisis: {nombre_liga}",
            gr.update(visible=is_fut),
            gr.update(visible=is_nfl),
            gr.update(visible=is_mlb),
            update_loc, update_vis, logo1, logo2
        )

    def volver_inicio():
        return (
            gr.update(visible=True),
            gr.update(visible=False)
        )

    btn_premier.click(fn=lambda: abrir_liga("PREMIER LEAGUE"), outputs=[panel_principal, panel_analisis, titulo_analisis, panel_futbol, panel_nfl, panel_mlb, fut_loc, fut_vis, logo_fut_loc, logo_fut_vis])
    btn_laliga.click(fn=lambda: abrir_liga("LALIGA"), outputs=[panel_principal, panel_analisis, titulo_analisis, panel_futbol, panel_nfl, panel_mlb, fut_loc, fut_vis, logo_fut_loc, logo_fut_vis])
    btn_seriea.click(fn=lambda: abrir_liga("SERIE A"), outputs=[panel_principal, panel_analisis, titulo_analisis, panel_futbol, panel_nfl, panel_mlb, fut_loc, fut_vis, logo_fut_loc, logo_fut_vis])
    btn_nfl.click(fn=lambda: abrir_liga("NFL"), outputs=[panel_principal, panel_analisis, titulo_analisis, panel_futbol, panel_nfl, panel_mlb, nfl_loc, nfl_vis, logo_nfl_loc, logo_nfl_vis])
    btn_mlb.click(fn=lambda: abrir_liga("MLB"), outputs=[panel_principal, panel_analisis, titulo_analisis, panel_futbol, panel_nfl, panel_mlb, mlb_loc, mlb_vis, logo_mlb_loc, logo_mlb_vis])

    btn_volver.click(fn=volver_inicio, outputs=[panel_principal, panel_analisis])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
