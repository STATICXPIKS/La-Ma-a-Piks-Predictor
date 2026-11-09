import json
import math
import os
from datetime import datetime
import gradio as gr
import numpy as np
import pandas as pd
import requests
from scipy.stats import norm, poisson

from props_engine import obtener_mejores_props_nfl
from nfl_model import simular_partido_nfl, MAPEO_NFL
from nba_model import simular_partido_nba, MAPEO_NBA
from nhl_model import simular_partido_nhl, MAPEO_NHL
from mlb_model import simular_partido_mlb, MAPEO_MLB

# ==========================================
# CONFIGURACIÓN DE APIS Y SUPABASE
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
API_SPORT_KEY = os.environ.get("API_SPORT_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ==========================================
# GESTIÓN DE HISTORIAL EN SUPABASE
# ==========================================
def guardar_apuesta_supabase(deporte, partido, tipo_apuesta, linea, cuota, prob_modelo, ev):
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_apuestas"
        payload = {
            "fecha": datetime.utcnow().strftime("%Y-%m-%d"),
            "deporte": deporte,
            "partido": partido,
            "tipo_apuesta": tipo_apuesta,
            "linea": str(linea),
            "cuota": float(cuota),
            "probabilidad_modelo": float(prob_modelo),
            "ev": float(ev),
            "estado": "PENDIENTE"
        }
        r = requests.post(url, headers=SUPABASE_HEADERS, json=payload, timeout=5)
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Error al guardar apuesta en Supabase: {e}")
        return False

def obtener_historial_supabase():
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_apuestas?select=*&order=id.desc&limit=100"
        r = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []

def renderizar_historial_html(filtro_deporte="TODOS"):
    apuestas = obtener_historial_supabase()
    if filtro_deporte != "TODOS":
        apuestas = [a for a in apuestas if a.get("deporte") == filtro_deporte]

    if not apuestas:
        return "<p style='color: #64748b; text-align: center; padding: 20px;'>No hay apuestas registradas en esta categoría.</p>"

    html = "<div style='display: flex; flex-direction: column; gap: 10px; max-height: 480px; overflow-y: auto; padding-right: 5px;'>"
    for ap in apuestas:
        estado = ap.get("estado", "PENDIENTE")
        if estado == "GANADA":
            color_bg = "rgba(0, 230, 118, 0.12)"
            color_border = "#00e676"
            badge = "<span style='color: #00e676; font-weight: bold;'>GANADA ✅</span>"
        elif estado == "PERDIDA":
            color_bg = "rgba(255, 23, 68, 0.12)"
            color_border = "#ff1744"
            badge = "<span style='color: #ff1744; font-weight: bold;'>PERDIDA ❌</span>"
        else:
            color_bg = "rgba(255, 171, 0, 0.10)"
            color_border = "#ffab00"
            badge = "<span style='color: #ffab00; font-weight: bold;'>PENDIENTE ⏳</span>"

        html += f"""
        <div style="background: {color_bg}; border: 1px solid {color_border}; border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 2px;">
                    #{ap.get('id', '0')} • {ap.get('fecha', '')} • <b>{ap.get('deporte', '')}</b>
                </div>
                <div style="font-size: 0.95rem; font-weight: 800; color: #ffffff;">
                    {ap.get('partido', '')}
                </div>
                <div style="font-size: 0.85rem; color: #00e676; font-family: monospace; margin-top: 2px;">
                    {ap.get('tipo_apuesta', '')} {ap.get('linea', '')} @ {ap.get('cuota', '')}
                </div>
            </div>
            <div style="font-size: 0.85rem;">
                {badge}
            </div>
        </div>
        """
    html += "</div>"
    return html

# ==========================================
# GENERADOR VISUAL DE TARJETAS (+EV CARDS)
# ==========================================
def generar_tarjeta_resultado(titulo, cuota, prob_real, ev, deporte, partido, tipo_apuesta, linea):
    if ev >= 12.0 and (1.65 <= cuota <= 2.35):
        categoria = "BET 🔥 VALOR DETECTADO"
        color_fondo = "linear-gradient(180deg, rgba(0, 230, 118, 0.12) 0%, rgba(13, 19, 31, 0.95) 100%)"
        color_borde = "#00e676"
        color_badge = "#00e676"
    elif ev > 2.0:
        categoria = "MAYBE ⚡ VALOR MODERADO"
        color_fondo = "linear-gradient(180deg, rgba(255, 171, 0, 0.08) 0%, rgba(13, 19, 31, 0.95) 100%)"
        color_borde = "#ffab00"
        color_badge = "#ffab00"
    else:
        categoria = "SIN VALOR ⚠️"
        color_fondo = "rgba(15, 23, 42, 0.6)"
        color_borde = "#334155"
        color_badge = "#64748b"

    html = f"""
    <div style="background: {color_fondo}; border: 1.5px solid {color_borde}; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 8px 16px -4px rgba(0,0,0,0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.08em; color: {color_badge}; text-transform: uppercase;">
                {categoria}
            </span>
            <span style="font-size: 1.05rem; font-weight: 900; color: {color_badge}; font-family: monospace;">
                {'+' if ev > 0 else ''}{ev}% EV
            </span>
        </div>
        <div style="font-size: 1.25rem; font-weight: 900; color: #ffffff; margin-bottom: 8px; letter-spacing: -0.02em;">
            {titulo} @ {cuota}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
            <span>Probabilidad Real:</span>
            <span style="font-weight: 800; color: #f8fafc; font-family: monospace;">{prob_real}%</span>
        </div>
    </div>
    """
    return html

# ==========================================
# CONTROLADORES DE SIMULACIÓN POR DEPORTE
# ==========================================
def ejecutar_simulacion_nfl(local, visitante, c_ml_loc, c_ml_vis, l_sp_loc, c_sp_loc, l_sp_vis, c_sp_vis, l_tot, c_over, c_under):
    partido_label = f"{local} vs {visitante}"
    data = simular_partido_nfl(
        local, visitante,
        float(c_ml_loc), float(c_ml_vis),
        float(l_sp_loc), float(c_sp_loc),
        float(l_sp_vis), float(c_sp_vis),
        float(l_tot), float(c_over), float(c_under)
    )

    ev_ml_loc = round(((data["ml_local"]["prob"] / 100.0) * float(c_ml_loc) - 1.0) * 100, 1)
    ev_sp_loc = round(((data["spread_local"]["prob"] / 100.0) * float(c_sp_loc) - 1.0) * 100, 1)
    ev_over   = round(((data["total_over"]["prob"] / 100.0) * float(c_over) - 1.0) * 100, 1)

    cards = []
    cards.append((ev_over, generar_tarjeta_resultado(f"OVER {l_tot}", c_over, data["total_over"]["prob"], ev_over, "NFL", partido_label, "OVER", l_tot)))
    cards.append((ev_ml_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} ML", c_ml_loc, data["ml_local"]["prob"], ev_ml_loc, "NFL", partido_label, "ML", "0")))
    cards.append((ev_sp_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} {l_sp_loc}", c_sp_loc, data["spread_local"]["prob"], ev_sp_loc, "NFL", partido_label, "SPREAD", l_sp_loc)))

    cards.sort(key=lambda x: x[0], reverse=True)
    html_cards = "".join([c[1] for c in cards])

    # OBTENCIÓN AUTOMÁTICA DE LAS 4 MEJORES PROPS DE JUGADORES
    html_props = ""
    try:
        props_nfl = obtener_mejores_props_nfl(local, visitante, top_n=4)
        if props_nfl:
            html_props += """
            <div style="margin-top: 25px; border-top: 1px solid #1f293d; padding-top: 20px;">
                <h3 style="color: #00e5ff; font-family: monospace; font-size: 1.15rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    🎯 TOP 4 PROPS DE JUGADORES RECOMENDADAS (+EV)
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
            """
            for p in props_nfl:
                color_badge = "#00e676" if p["ev"] >= 10.0 else "#ffab00"
                html_props += f"""
                    <div style="background: #0d131f; border: 1px solid #1e293b; border-radius: 10px; padding: 14px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: bold; color: #fff; font-size: 0.95rem;">🏈 {p['jugador']}</span>
                            <span style="background: rgba(0,230,118,0.1); color: {color_badge}; border: 1px solid {color_badge}; padding: 2px 7px; border-radius: 6px; font-size: 0.8rem; font-weight: bold;">
                                +{p['ev']}% EV
                            </span>
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 6px;">
                            {p['lado']} <b>{p['linea']}</b> {p['tipo_prop']} @ <b style="color: #f8fafc;">{p['cuota']}</b>
                        </div>
                        <div style="display: flex; justify-content: space-between; color: #64748b; font-size: 0.8rem; border-top: 1px dashed #1e293b; padding-top: 6px; margin-top: 6px;">
                            <span>Proy: <b style="color: #cbd5e1;">{p['proyeccion']}</b></span>
                            <span>Prob. Real: <b style="color: #cbd5e1;">{p['prob_real']}%</b></span>
                        </div>
                    </div>
                """
            html_props += """
                </div>
            </div>
            """
    except Exception as e:
        print(f"Error cargando props automáticas: {e}")

    return html_cards + html_props, data["resumen_explicado"]

def ejecutar_simulacion_nba(local, visitante, c_ml_loc, c_ml_vis, l_sp_loc, c_sp_loc, l_sp_vis, c_sp_vis, l_tot, c_over, c_under):
    partido_label = f"{local} vs {visitante}"
    data = simular_partido_nba(
        local, visitante,
        float(c_ml_loc), float(c_ml_vis),
        float(l_sp_loc), float(c_sp_loc),
        float(l_sp_vis), float(c_sp_vis),
        float(l_tot), float(c_over), float(c_under)
    )

    ev_ml_loc = round(((data["ml_local"]["prob"] / 100.0) * float(c_ml_loc) - 1.0) * 100, 1)
    ev_sp_loc = round(((data["spread_local"]["prob"] / 100.0) * float(c_sp_loc) - 1.0) * 100, 1)
    ev_over   = round(((data["total_over"]["prob"] / 100.0) * float(c_over) - 1.0) * 100, 1)

    cards = []
    cards.append((ev_over, generar_tarjeta_resultado(f"OVER {l_tot}", c_over, data["total_over"]["prob"], ev_over, "NBA", partido_label, "OVER", l_tot)))
    cards.append((ev_ml_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} ML", c_ml_loc, data["ml_local"]["prob"], ev_ml_loc, "NBA", partido_label, "ML", "0")))
    cards.append((ev_sp_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} {l_sp_loc}", c_sp_loc, data["spread_local"]["prob"], ev_sp_loc, "NBA", partido_label, "SPREAD", l_sp_loc)))

    cards.sort(key=lambda x: x[0], reverse=True)
    html_cards = "".join([c[1] for c in cards])
    return html_cards, data["resumen_explicado"]

def ejecutar_simulacion_nhl(local, visitante, c_ml_loc, c_ml_vis, l_pl_loc, c_pl_loc, l_pl_vis, c_pl_vis, l_tot, c_over, c_under):
    partido_label = f"{local} vs {visitante}"
    data = simular_partido_nhl(
        local, visitante,
        float(c_ml_loc), float(c_ml_vis),
        float(l_pl_loc), float(c_pl_loc),
        float(l_pl_vis), float(c_pl_vis),
        float(l_tot), float(c_over), float(c_under)
    )

    ev_ml_loc = round(((data["ml_local"]["prob"] / 100.0) * float(c_ml_loc) - 1.0) * 100, 1)
    ev_pl_loc = round(((data["pl_local"]["prob"] / 100.0) * float(c_pl_loc) - 1.0) * 100, 1)
    ev_under  = round(((data["total_under"]["prob"] / 100.0) * float(c_under) - 1.0) * 100, 1)

    cards = []
    cards.append((ev_ml_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} ML", c_ml_loc, data["ml_local"]["prob"], ev_ml_loc, "NHL", partido_label, "ML", "0")))
    cards.append((ev_under, generar_tarjeta_resultado(f"UNDER {l_tot}", c_under, data["total_under"]["prob"], ev_under, "NHL", partido_label, "UNDER", l_tot)))
    cards.append((ev_pl_loc, generar_tarjeta_resultado(f"{data['equipo_local_abbr']} {l_pl_loc}", c_pl_loc, data["pl_local"]["prob"], ev_pl_loc, "NHL", partido_label, "PUCKLINE", l_pl_loc)))

    cards.sort(key=lambda x: x[0], reverse=True)
    html_cards = "".join([c[1] for c in cards])
    return html_cards, data["resumen_explicado"]

# ==========================================
# INTERFAZ GRADIO PROFESIONAL
# ==========================================
CSS_CUSTOM = """
body, .gradio-container {
    background-color: #080c14 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #e2e8f0 !important;
}
.custom-card {
    background: #0d131f;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
}
button.primary-btn {
    background: linear-gradient(135deg, #00e676 0%, #00b0ff 100%) !important;
    color: #080c14 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 14px rgba(0, 230, 118, 0.3) !important;
}
input, select {
    background: #101726 !important;
    border: 1px solid #1e293b !important;
    color: #f8fafc !important;
    border-radius: 8px !important;
}
"""

with gr.Blocks(css=CSS_CUSTOM, title="LA MAÑA PICKS • Predictor Cuantitativo") as demo:
    gr.HTML("""
    <div style="text-align: center; padding: 25px 0 15px 0;">
        <h1 style="font-size: 2.2rem; font-weight: 900; letter-spacing: -0.04em; color: #ffffff; margin: 0;">
            LA MAÑA <span style="background: linear-gradient(135deg, #00e676, #00b0ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PICKS</span>
        </h1>
        <p style="color: #64748b; font-size: 0.95rem; margin-top: 6px;">
            Simulaciones Monte Carlo • Machine Learning XGBoost • Auditoría de Valor Esperado (+EV)
        </p>
    </div>
    """)

    with gr.Tabs():
        # --- TAB NFL ---
        with gr.TabItem("NFL • BLITZ-IA"):
            with gr.Row():
                with gr.Column(scale=1):
                    nfl_loc = gr.Dropdown(choices=list(MAPEO_NFL.keys()), value="Minnesota Vikings", label="Equipo Local 🏠")
                    nfl_vis = gr.Dropdown(choices=list(MAPEO_NFL.keys()), value="Buffalo Bills", label="Equipo Visitante ✈️")
                    
                    gr.Markdown("##### 1. Moneyline (ML)")
                    with gr.Row():
                        nfl_c_ml_loc = gr.Number(value=2.45, label="Cuota ML Local")
                        nfl_c_ml_vis = gr.Number(value=1.55, label="Cuota ML Visitante")
                    
                    gr.Markdown("##### 2. Point Spread (Hándicap)")
                    with gr.Row():
                        nfl_l_sp_loc = gr.Number(value=3.5, label="Línea Local (+/-)")
                        nfl_c_sp_loc = gr.Number(value=1.91, label="Cuota Local")
                    with gr.Row():
                        nfl_l_sp_vis = gr.Number(value=-3.5, label="Línea Visitante (+/-)")
                        nfl_c_sp_vis = gr.Number(value=1.91, label="Cuota Visitante")

                    gr.Markdown("##### 3. Total de Puntos (Over / Under)")
                    with gr.Row():
                        nfl_l_tot = gr.Number(value=44.5, label="Línea Total")
                        nfl_c_over = gr.Number(value=1.87, label="Cuota Over")
                        nfl_c_under = gr.Number(value=1.87, label="Cuota Under")

                    btn_nfl = gr.Button("EJECUTAR SIMULACIÓN CON MONTE CARLO 🚀", elem_classes=["primary-btn"])

                with gr.Column(scale=1):
                    nfl_out_html = gr.HTML(label="Tarjetas de Valor")
                    nfl_out_resumen = gr.Textbox(label="Auditoría Cuantitativa", lines=3)

            btn_nfl.click(
                ejecutar_simulacion_nfl,
                inputs=[nfl_loc, nfl_vis, nfl_c_ml_loc, nfl_c_ml_vis, nfl_l_sp_loc, nfl_c_sp_loc, nfl_l_sp_vis, nfl_c_sp_vis, nfl_l_tot, nfl_c_over, nfl_c_under],
                outputs=[nfl_out_html, nfl_out_resumen]
            )

        # --- TAB NBA ---
        with gr.TabItem("NBA • DUNK-IA"):
            with gr.Row():
                with gr.Column(scale=1):
                    nba_loc = gr.Dropdown(choices=list(MAPEO_NBA.keys()), value="Dallas Mavericks", label="Equipo Local 🏠")
                    nba_vis = gr.Dropdown(choices=list(MAPEO_NBA.keys()), value="Indiana Pacers", label="Equipo Visitante ✈️")
                    
                    gr.Markdown("##### 1. Moneyline (ML)")
                    with gr.Row():
                        nba_c_ml_loc = gr.Number(value=1.62, label="Cuota ML Local")
                        nba_c_ml_vis = gr.Number(value=2.23, label="Cuota ML Visitante")
                    
                    gr.Markdown("##### 2. Point Spread (Hándicap)")
                    with gr.Row():
                        nba_l_sp_loc = gr.Number(value=-3.5, label="Línea Local (+/-)")
                        nba_c_sp_loc = gr.Number(value=1.91, label="Cuota Local")
                    with gr.Row():
                        nba_l_sp_vis = gr.Number(value=3.5, label="Línea Visitante (+/-)")
                        nba_c_sp_vis = gr.Number(value=1.91, label="Cuota Visitante")

                    gr.Markdown("##### 3. Total de Puntos (Over / Under)")
                    with gr.Row():
                        nba_l_tot = gr.Number(value=226.5, label="Línea Total")
                        nba_c_over = gr.Number(value=1.89, label="Cuota Over")
                        nba_c_under = gr.Number(value=1.84, label="Cuota Under")

                    btn_nba = gr.Button("EJECUTAR SIMULACIÓN CON MONTE CARLO 🚀", elem_classes=["primary-btn"])

                with gr.Column(scale=1):
                    nba_out_html = gr.HTML(label="Tarjetas de Valor")
                    nba_out_resumen = gr.Textbox(label="Auditoría Cuantitativa", lines=3)

            btn_nba.click(
                ejecutar_simulacion_nba,
                inputs=[nba_loc, nba_vis, nba_c_ml_loc, nba_c_ml_vis, nba_l_sp_loc, nba_c_sp_loc, nba_l_sp_vis, nba_c_sp_vis, nba_l_tot, nba_c_over, nba_c_under],
                outputs=[nba_out_html, nba_out_resumen]
            )

        # --- TAB NHL ---
        with gr.TabItem("NHL • FROST-IA"):
            with gr.Row():
                with gr.Column(scale=1):
                    nhl_loc = gr.Dropdown(choices=list(MAPEO_NHL.keys()), value="Vancouver Canucks", label="Equipo Local 🏠")
                    nhl_vis = gr.Dropdown(choices=list(MAPEO_NHL.keys()), value="Philadelphia Flyers", label="Equipo Visitante ✈️")
                    
                    gr.Markdown("##### 1. Moneyline (ML)")
                    with gr.Row():
                        nhl_c_ml_loc = gr.Number(value=2.14, label="Cuota ML Local")
                        nhl_c_ml_vis = gr.Number(value=1.71, label="Cuota ML Visitante")
                    
                    gr.Markdown("##### 2. Puck Line (Hándicap -1.5 / +1.5)")
                    with gr.Row():
                        nhl_l_pl_loc = gr.Number(value=1.5, label="Línea Local")
                        nhl_c_pl_loc = gr.Number(value=1.43, label="Cuota Local")
                    with gr.Row():
                        nhl_l_pl_vis = gr.Number(value=-1.5, label="Línea Visitante")
                        nhl_c_pl_vis = gr.Number(value=2.75, label="Cuota Visitante")

                    gr.Markdown("##### 3. Total de Goles (Over / Under)")
                    with gr.Row():
                        nhl_l_tot = gr.Number(value=6.5, label="Línea Total")
                        nhl_c_over = gr.Number(value=1.98, label="Cuota Over")
                        nhl_c_under = gr.Number(value=1.77, label="Cuota Under")

                    btn_nhl = gr.Button("EJECUTAR SIMULACIÓN CON MONTE CARLO 🚀", elem_classes=["primary-btn"])

                with gr.Column(scale=1):
                    nhl_out_html = gr.HTML(label="Tarjetas de Valor")
                    nhl_out_resumen = gr.Textbox(label="Auditoría Cuantitativa", lines=3)

            btn_nhl.click(
                ejecutar_simulacion_nhl,
                inputs=[nhl_loc, nhl_vis, nhl_c_ml_loc, nhl_c_ml_vis, nhl_l_pl_loc, nhl_c_pl_loc, nhl_l_pl_vis, nhl_c_pl_vis, nhl_l_tot, nhl_c_over, nhl_c_under],
                outputs=[nhl_out_html, nhl_out_resumen]
            )

        # --- TAB HISTORIAL AUDITADO ---
        with gr.TabItem("HISTORIAL AUDITADO"):
            filtro_hist = gr.Radio(choices=["TODOS", "NFL", "NBA", "NHL", "MLB"], value="TODOS", label="Filtrar Historial por Liga")
            historial_display = gr.HTML(value=renderizar_historial_html("TODOS"))
            btn_refresh = gr.Button("ACTUALIZAR HISTORIAL 🔄")

            filtro_hist.change(renderizar_historial_html, inputs=[filtro_hist], outputs=[historial_display])
            btn_refresh.click(renderizar_historial_html, inputs=[filtro_hist], outputs=[historial_display])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
