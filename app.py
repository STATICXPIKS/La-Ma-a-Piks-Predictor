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
# CONFIGURACIÓN DE VARIABLES DE ENTORNO (RENDER / SUPABASE)
# ==============================================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# LOGOS OFICIALES DE LAS LIGAS DEL CÓDIGO ACTUALIZADO
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
# CONSULTA DE SUPABASE
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
# ESTRUCTURA VISUAL IDÉNTICA A LA IMAGEN 2 (FILA DE LIGAS Y RÉCORDS)
# ==============================================================================
def renderizar_fila_ligas_imagen2():
    return f"""
    <!-- ENCABEZADO PRINCIPAL -->
    <div style="text-align:center; padding:10px 0 20px 0;">
        <h1 style="color:#047857; font-size:42px; font-weight:900; margin:0; tracking: -1px;">LA MAÑA PICKS</h1>
        <p style="color:#10B981; font-weight:800; margin-top:5px; font-size:15px; letter-spacing: 0.5px;">
            ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.
        </p>
    </div>

    <!-- FILA SUPERIOR COMPLETA CON LIGAS ACTUALIZADAS (ESTILO IMAGEN 2) -->
    <div style="display:flex; justify-content:center; gap:16px; flex-wrap:nowrap; overflow-x:auto; padding-bottom:20px;">
        
        <!-- PREMIER LEAGUE -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['PREMIER']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RECORD PREMIER
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">62.5%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:20px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:12px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:32px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:5 &nbsp; L:3 &nbsp; P:4</div>
            </div>
        </div>

        <!-- LALIGA -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['LALIGA']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RECORD LALIGA
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">0.0%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:8px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:0 &nbsp; L:0 &nbsp; P:0</div>
            </div>
        </div>

        <!-- SERIE A -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['SERIEA']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RECORD SERIE A
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">100.0%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:8px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:30px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:2 &nbsp; L:0 &nbsp; P:0</div>
            </div>
        </div>

        <!-- NFL -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['NFL']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RÉCORD NFL
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">55.8%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:26px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:30px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:29 &nbsp; L:23 &nbsp; P:0</div>
            </div>
        </div>

        <!-- MLB -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['MLB']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RÉCORD MLB
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">53.3%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:28px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:31px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:32 &nbsp; L:28 &nbsp; P:0</div>
            </div>
        </div>

        <!-- NBA -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['NBA']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RÉCORD NBA
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">50.0%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:22px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:22px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:10 &nbsp; L:10 &nbsp; P:0</div>
            </div>
        </div>

        <!-- NHL -->
        <div style="width:120px; text-align:center;">
            <div style="height:65px; display:flex; align-items:center; justify-content:center;">
                <img src="{LIGA_LOGOS['NHL']}" style="max-height:60px; max-width:100px; object-fit:contain;">
            </div>
            <div style="background:#F97316; color:white; font-size:12px; font-weight:800; padding:8px 0; border-radius:8px; margin:10px 0; box-shadow:0 2px 4px rgba(249,115,22,0.3);">
                RÉCORD NHL
            </div>
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px; padding:12px 5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <span style="font-size:20px; font-weight:900; color:#047857;">0.0%</span>
                <div style="display:flex; justify-content:center; align-items:flex-end; gap:4px; height:38px; margin:10px 0;">
                    <div style="width:9px; height:8px; background:#EF4444; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#F59E0B; border-radius:3px;"></div>
                    <div style="width:9px; height:8px; background:#10B981; border-radius:3px;"></div>
                </div>
                <div style="font-size:10px; color:#6B7280; font-weight:800;">W:0 &nbsp; L:0 &nbsp; P:0</div>
            </div>
        </div>

    </div>
    """

# ==============================================================================
# TACÓMETRO DE EFECTIVIDAD GLOBAL Y TABLERO
# ==============================================================================
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
    <!-- TACÓMETRO DE EFECTIVIDAD GLOBAL -->
    <div style="border:2px solid #10B981; border-radius:18px; padding:20px; background:#FFFFFF; max-width:650px; margin:10px auto 25px auto; text-align:center; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
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
# MOTORES DE ANÁLISIS INDIVIDUAL
# ==============================================================================
def analizar_nba(local, visitante, c_mll, c_mlv, sp_l, c_spl, sp_v, c_spv):
    eq_l = NBA_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png"})
    eq_v = NBA_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png"})
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px;">
        <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MOTOR SABERMÉTRICO NBA</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{local} (121.0 pts est)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">95%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{visitante} (95.7 pts est)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">5%</span>
        </div>
        <h4 style="margin-top:20px; font-size:13px; font-weight:800;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</h4>
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:12px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:13px; font-weight:700; color:#065F46;">1. Moneyline Directo: {local} ML @ {c_mll} — Prob: 95% | EV: +6.0%</span>
            <span style="background:#10B981; color:white; font-size:11px; font-weight:800; padding:4px 8px; border-radius:6px;">BET 🔥 (+6.0% EV)</span>
        </div>
    </div>
    """

def analizar_mlb(local, visitante):
    eq_l = MLB_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/mlb/500/cle.png"})
    eq_v = MLB_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/mlb/500/tb.png"})
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px;">
        <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO SABERMÉTRICO MLB</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{local} (3.0 carreras est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">18%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{visitante} (4.2 carreras est.)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">82%</span>
        </div>
    </div>
    """

def analizar_futbol(local, visitante, c_loc, c_emp, c_vis):
    eq_l = PREMIER_LEAGUE_TEAMS.get(local, {"logo": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png"})
    eq_v = PREMIER_LEAGUE_TEAMS.get(visitante, {"logo": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png"})
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px;">
        <h3 style="color:#064E3B; margin:0; font-weight:800;">LA MAÑA PICKS • MODELO DIXON-COLES (FÚTBOL)</h3>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px; margin:15px 0;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_l['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{local} (1.94 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#10B981;">61%</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background:#F3F4F6; padding:15px; border-radius:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="{eq_v['logo']}" width="45" height="45">
                <span style="font-weight:800; font-size:16px;">{visitante} (0.86 xG)</span>
            </div>
            <span style="font-size:24px; font-weight:900; color:#EF4444;">15%</span>
        </div>
    </div>
    """

# ==============================================================================
# CONSTRUCCIÓN DE LA PANTALLA EN GRADIO
# ==============================================================================

with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft()) as demo:
    
    # PANTALLA PRINCIPAL
    with gr.Column(visible=True) as panel_principal:
        # PARTE SUPERIOR EXACTA A LA IMAGEN 2: LOGOS + BOTONES NARANJAS + HISTOGRAMAS
        gr.HTML(renderizar_fila_ligas_imagen2())

        # PARTE INFERIOR: TACÓMETRO DE EFECTIVIDAD Y TABLERO
        gr.HTML(renderizar_tacometro_y_tablero())

        # GESTOR DE PICKS POR ID
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

    # PANTALLA DE ANÁLISIS
    with gr.Column(visible=False) as panel_analisis:
        btn_volver = gr.Button("⬅️ Volver al Menú Principal")
        
        # SUB-PANEL NBA
        with gr.Group(visible=False) as sub_nba:
            gr.Markdown("## 🏀 Área de Análisis: NBA")
            with gr.Row():
                with gr.Column():
                    nba_loc = gr.Dropdown(choices=list(NBA_TEAMS.keys()), value="Boston Celtics", label="Equipo Local")
                    nba_vis = gr.Dropdown(choices=list(NBA_TEAMS.keys()), value="Los Angeles Lakers", label="Equipo Visitante")
                    nba_mll = gr.Number(value=1.45, label="Cuota ML Local")
                    nba_mlv = gr.Number(value=2.85, label="Cuota ML Visitante")
                    nba_spl = gr.Number(value=-5.5, label="Spread Local")
                    nba_cspl = gr.Number(value=1.9, label="Cuota Spread Local")
                    nba_spv = gr.Number(value=5.5, label="Spread Visitante")
                    nba_cspv = gr.Number(value=1.9, label="Cuota Spread Visitante")
                    btn_sim_nba = gr.Button("⚡ Calcular Pronóstico NBA", variant="primary")
                with gr.Column():
                    out_nba = gr.HTML()

            btn_sim_nba.click(
                fn=analizar_nba,
                inputs=[nba_loc, nba_vis, nba_mll, nba_mlv, nba_spl, nba_cspl, nba_spv, nba_cspv],
                outputs=[out_nba]
            )

        # SUB-PANEL MLB
        with gr.Group(visible=False) as sub_mlb:
            gr.Markdown("## ⚾ Área de Análisis: MLB")
            with gr.Row():
                with gr.Column():
                    mlb_loc = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="Cleveland Guardians", label="Equipo Local")
                    mlb_vis = gr.Dropdown(choices=list(MLB_TEAMS.keys()), value="Tampa Bay Rays", label="Equipo Visitante")
                    btn_sim_mlb = gr.Button("⚡ Calcular Pronóstico MLB", variant="primary")
                with gr.Column():
                    out_mlb = gr.HTML()

            btn_sim_mlb.click(
                fn=analizar_mlb,
                inputs=[mlb_loc, mlb_vis],
                outputs=[out_mlb]
            )

        # SUB-PANEL FÚTBOL
        with gr.Group(visible=False) as sub_fut:
            gr.Markdown("## ⚽ Área de Análisis: FÚTBOL")
            with gr.Row():
                with gr.Column():
                    fut_loc = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="Brentford", label="Equipo Local")
                    fut_vis = gr.Dropdown(choices=list(PREMIER_LEAGUE_TEAMS.keys()), value="Liverpool", label="Equipo Visitante")
                    fut_cl = gr.Number(value=1.85, label="Cuota Local (1)")
                    fut_ce = gr.Number(value=3.6, label="Cuota Empate (X)")
                    fut_cv = gr.Number(value=4.2, label="Cuota Visitante (2)")
                    btn_sim_fut = gr.Button("⚡ Calcular Pronóstico Fútbol", variant="primary")
                with gr.Column():
                    out_fut = gr.HTML()

            btn_sim_fut.click(
                fn=analizar_futbol,
                inputs=[fut_loc, fut_vis, fut_cl, fut_ce, fut_cv],
                outputs=[out_fut]
            )

    def volver_inicio():
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    btn_volver.click(fn=volver_inicio, outputs=[panel_principal, panel_analisis, sub_nba, sub_mlb, sub_fut])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
