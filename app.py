import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests
import json
import os
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="MAÑA PIKS ANALYTICS PRO", layout="wide", page_icon="👑")

DB_FILE = "apuestas_db.json"

# ==========================================
# GESTIÓN DE BASE DE DATOS PERSISTENTE (JSON)
# ==========================================
def cargar_base_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_base_datos(datos):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error al guardar la base de datos: {e}")

if "historial_apuestas" not in st.session_state:
    st.session_state.historial_apuestas = cargar_base_datos()

def registrar_apuesta(deporte, partido, equipo_loc, equipo_vis, mercado, linea, momio, ev):
    historial = cargar_base_datos()
    nueva_apuesta = {
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": deporte,
        "partido": partido,
        "equipo_loc": equipo_loc,
        "equipo_vis": equipo_vis,
        "mercado": mercado,
        "linea": str(linea),
        "momio": momio,
        "ev": round(ev * 100, 1),
        "estado": "PENDING", # PENDING, WIN, LOSS
        "resultado_real": "En Espera"
    }
    historial.append(nueva_apuesta)
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast(f"✅ Pick guardado: {mercado}", icon="📌")

def eliminar_apuesta(id_apuesta):
    historial = cargar_base_datos()
    historial = [item for item in historial if item.get("id") != id_apuesta]
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast("🗑️ Apuesta eliminada con éxito", icon="🗑️")
    st.rerun()

# ==========================================
# MOTOR DE DETECCIÓN DE TRAMPAS Y BAJAS
# ==========================================
def evaluar_riesgo_trampa(prob_real, momio_decimal, ev):
    if ev > 0.18:
        return True, "⚠️ ALERTA TRAP: +EV anómalo (>18%). Posible baja clave de último minuto."
    if prob_real >= 0.65 and momio_decimal >= 2.20:
        return True, "⚠️ ALERTA TRAP: Cuota sospechosamente alta para la probabilidad estimada."
    return False, ""

@st.cache_data(ttl=900)
def obtener_lesiones_espn(deporte_key):
    url_map = {
        "Liga MX": "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/news",
        "MLB": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news"
    }
    bajas_reportadas = []
    try:
        url = url_map.get(deporte_key)
        if url:
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                for art in articles:
                    headline = art.get("headline", "")
                    description = art.get("description", "")
                    text = f"{headline} {description}".lower()
                    if any(k in text for k in ["baja", "lesion", "out", "injured", "duda", "scratched", "lineup"]):
                        bajas_reportadas.append(headline)
    except Exception:
        pass
    return bajas_reportadas[:3]

# ==========================================
# GENERADOR DE GRÁFICAS PROPS BR (BARRAS L10)
# ==========================================
def generar_grafica_barras_propsbr(prob_real, seed_val=42):
    """Genera la minigráfica de barras estilo PropsBR basada en la probabilidad estimada"""
    np.random.seed(int(prob_real * 1000) % 1000)
    # Generar patrón simulado de 10 partidos anteriores según la probabilidad
    hits = (np.random.rand(10) < prob_real).astype(int)
    
    html = '<div style="display:flex; align-items:flex-end; gap:3px; height:36px; justify-content:flex-end;">'
    for val in hits:
        cls_color = "#00ff66" if val == 1 else "#ff3355"
        height_px = 30 if val == 1 else 12
        html += f'<div style="width:6px; background-color:{cls_color}; height:{height_px}px; border-radius:2px;"></div>'
    html += '</div>'
    return html

# ==========================================
# MOTOR DE AUTO-VERIFICACIÓN EN VIVO
# ==========================================
def auto_verificar_apuestas():
    historial = cargar_base_datos()
    actualizados = 0

    # 1. API LIGA MX (ESPN)
    url_mx = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard"
    res_mx = []
    try:
        r_mx = requests.get(url_mx, timeout=5)
        if r_mx.status_code == 200:
            events = r_mx.json().get("events", [])
            for ev_item in events:
                comp = ev_item.get("competitions", [])[0]
                status_completed = comp.get("status", {}).get("type", {}).get("completed", False)
                period = comp.get("status", {}).get("period", 0)
                teams = comp.get("competitors", [])
                
                loc_name, vis_name = "", ""
                loc_score, vis_score = 0, 0
                loc_ht_score, vis_ht_score = 0, 0
                
                for t in teams:
                    linescores = t.get("linescores", [])
                    ht_val = int(linescores[0].get("value", 0)) if len(linescores) >= 1 else 0
                    
                    if t.get("homeAway") == "home":
                        loc_name = t.get("team", {}).get("name", "")
                        loc_score = int(t.get("score", 0))
                        loc_ht_score = ht_val
                    else:
                        vis_name = t.get("team", {}).get("name", "")
                        vis_score = int(t.get("score", 0))
                        vis_ht_score = ht_val

                res_mx.append({
                    "match_title": f"{loc_name} vs {vis_name}",
                    "completed": status_completed, 
                    "period": period,
                    "loc_score": loc_score, 
                    "vis_score": vis_score,
                    "ht_score_tot": loc_ht_score + vis_ht_score
                })
    except Exception:
        pass

    # 2. API MLB STATS
    url_mlb = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    res_mlb = []
    try:
        r_mlb = requests.get(url_mlb, timeout=5)
        if r_mlb.status_code == 200:
            events = r_mlb.json().get("events", [])
            for ev_item in events:
                game_id = ev_item.get("id")
                comp = ev_item.get("competitions", [])[0]
                status_completed = comp.get("status", {}).get("type", {}).get("completed", False)
                status_state = comp.get("status", {}).get("type", {}).get("state", "pre")
                period = comp.get("status", {}).get("period", 0)
                
                teams = comp.get("competitors", [])
                loc_name, vis_name = "", ""
                loc_score, vis_score = 0, 0
                loc_linescore, vis_linescore = [], []
                
                for t in teams:
                    if t.get("homeAway") == "home":
                        loc_name = t.get("team", {}).get("displayName", "")
                        loc_score = int(t.get("score", 0))
                        loc_linescore = t.get("linescores", [])
                    else:
                        vis_name = t.get("team", {}).get("displayName", "")
                        vis_score = int(t.get("score", 0))
                        vis_linescore = t.get("linescores", [])

                r1_loc = int(loc_linescore[0].get("value", 0)) if len(loc_linescore) >= 1 else 0
                r1_vis = int(vis_linescore[0].get("value", 0)) if len(vis_linescore) >= 1 else 0
                r1_tot = r1_loc + r1_vis

                f5_loc = sum([int(x.get("value", 0)) for x in loc_linescore[:5]])
                f5_vis = sum([int(x.get("value", 0)) for x in vis_linescore[:5]])
                f5_tot = f5_loc + f5_vis
                f5_completo = (period > 5) or status_completed or (len(loc_linescore) >= 5 and len(vis_linescore) >= 5 and period == 5 and status_state == "post")

                ks_dict = {}
                outs_dict = {}
                if status_state in ["in", "post"]:
                    try:
                        url_box = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={game_id}"
                        r_box = requests.get(url_box, timeout=4)
                        if r_box.status_code == 200:
                            box_data = r_box.json()
                            players = box_data.get("boxscore", {}).get("players", [])
                            for team_p in players:
                                statistics = team_p.get("statistics", [])
                                for stat_cat in statistics:
                                    if stat_cat.get("type") == "pitching":
                                        athletes = stat_cat.get("athletes", [])
                                        for ath in athletes:
                                            p_name = ath.get("athlete", {}).get("displayName", "")
                                            stats_vals = ath.get("stats", [])
                                            if len(stats_vals) >= 6:
                                                ip_str = str(stats_vals[0])
                                                if "." in ip_str:
                                                    parts = ip_str.split(".")
                                                    outs_val = int(parts[0]) * 3 + int(parts[1])
                                                elif ip_str.isdigit():
                                                    outs_val = int(ip_str) * 3
                                                else:
                                                    outs_val = 0
                                                
                                                so_val = int(stats_vals[5]) if str(stats_vals[5]).isdigit() else 0
                                                ks_dict[p_name.lower()] = so_val
                                                outs_dict[p_name.lower()] = outs_val
                    except Exception:
                        pass

                res_mlb.append({
                    "match_title": f"{loc_name} vs {vis_name}",
                    "completed": status_completed,
                    "state": status_state,
                    "period": period,
                    "loc_name": loc_name, 
                    "vis_name": vis_name, 
                    "loc_score": loc_score, 
                    "vis_score": vis_score,
                    "r1_tot": r1_tot,
                    "f5_loc": f5_loc,
                    "f5_vis": f5_vis,
                    "f5_tot": f5_tot,
                    "f5_completo": f5_completo,
                    "ks_dict": ks_dict,
                    "outs_dict": outs_dict
                })
    except Exception:
        pass

    res_mlb.sort(key=lambda x: (not x["completed"], x["state"] == "pre"))

    # EVALUAR CADA APUESTA PENDIENTE
    for item in historial:
        if item["estado"] == "PENDING":
            dep = item["deporte"]
            
            # --- EVALUACIÓN LIGA MX ---
            if "Liga MX" in dep:
                for score_data in res_mx:
                    match_title = score_data["match_title"]
                    if item["equipo_loc"].lower() in match_title.lower() and item["equipo_vis"].lower() in match_title.lower():
                        g_loc = score_data["loc_score"]
                        g_vis = score_data["vis_score"]
                        tot_goles = g_loc + g_vis
                        ht_goles = score_data["ht_score_tot"]
                        mercado = item["mercado"]
                        linea = item.get("linea", "")

                        if "1ra Mitad" in mercado or "1HT" in mercado:
                            try:
                                val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else (0.5 if "0.5" in mercado else 1.5)
                            except Exception:
                                val_target = 0.5 if "0.5" in mercado else 1.5

                            if "Más" in mercado or "Over" in mercado:
                                if ht_goles > val_target:
                                    item["estado"] = "WIN"
                                    item["resultado_real"] = f"{ht_goles} Goles (1HT)"
                                    actualizados += 1
                                elif score_data["period"] >= 2 or score_data["completed"]:
                                    item["estado"] = "LOSS"
                                    item["resultado_real"] = f"{ht_goles} Goles (1HT)"
                                    actualizados += 1

                        elif "Goles" in mercado or "Over" in mercado or "Under" in mercado:
                            try:
                                val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 2.5
                            except Exception:
                                val_target = 2.5

                            if "Más" in mercado or "Over" in mercado:
                                if tot_goles > val_target:
                                    item["estado"] = "WIN"
                                    item["resultado_real"] = f"{g_loc} - {g_vis}"
                                    actualizados += 1
                                elif score_data["completed"]:
                                    item["estado"] = "LOSS"
                                    item["resultado_real"] = f"{g_loc} - {g_vis}"
                                    actualizados += 1

                        elif "Gana" in mercado:
                            if score_data["completed"]:
                                item["resultado_real"] = f"{g_loc} - {g_vis}"
                                if item["equipo_loc"] in mercado and g_loc > g_vis: item["estado"] = "WIN"
                                elif item["equipo_vis"] in mercado and g_vis > g_loc: item["estado"] = "WIN"
                                else: item["estado"] = "LOSS"
                                actualizados += 1

            # --- EVALUACIÓN MLB ---
            elif "MLB" in dep:
                for score_data in res_mlb:
                    match_title = score_data["match_title"]
                    eq_loc_match = item["equipo_loc"].lower() in match_title.lower() or score_data["loc_name"].lower() in item["equipo_loc"].lower()
                    eq_vis_match = item["equipo_vis"].lower() in match_title.lower() or score_data["vis_name"].lower() in item["equipo_vis"].lower()
                    
                    if eq_loc_match and eq_vis_match:
                        r_loc = score_data["loc_score"]
                        r_vis = score_data["vis_score"]
                        tot_carreras = r_loc + r_vis
                        mercado = item["mercado"]
                        linea = item.get("linea", "")
                        ks_dict = score_data["ks_dict"]
                        outs_dict = score_data["outs_dict"]

                        if "Carreras" in mercado:
                            try:
                                val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 8.5
                            except Exception:
                                val_target = 8.5

                            if "Over" in mercado or "OVER" in mercado:
                                if tot_carreras > val_target:
                                    item["estado"] = "WIN"
                                    item["resultado_real"] = f"{r_loc} - {r_vis}"
                                    actualizados += 1
                                    break
                                elif score_data["completed"]:
                                    item["estado"] = "LOSS"
                                    item["resultado_real"] = f"{r_loc} - {r_vis}"
                                    actualizados += 1
                                    break
                                else:
                                    item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

                            elif "Under" in mercado or "UNDER" in mercado:
                                if tot_carreras > val_target:
                                    item["estado"] = "LOSS"
                                    item["resultado_real"] = f"{r_loc} - {r_vis}"
                                    actualizados += 1
                                    break
                                elif score_data["completed"]:
                                    item["estado"] = "WIN"
                                    item["resultado_real"] = f"{r_loc} - {r_vis}"
                                    actualizados += 1
                                    break
                                else:
                                    item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

                        elif "Gana" in mercado or "ML" in mercado:
                            if score_data["completed"] or score_data["period"] >= 9:
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                if item["equipo_loc"] in mercado and r_loc > r_vis: item["estado"] = "WIN"
                                elif item["equipo_vis"] in mercado and r_vis > r_loc: item["estado"] = "WIN"
                                else: item["estado"] = "LOSS"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    return actualizados

# ==========================================
# BASE DE DATOS Y JERSEYS: LIGA MX & MLB
# ==========================================
JERSEYS_LIGA_MX = {
    "América": {"c1": "#FDE100", "c2": "#001A49"},
    "Chivas": {"c1": "#DA291C", "c2": "#FFFFFF"},
    "Cruz Azul": {"c1": "#00519E", "c2": "#FFFFFF"},
    "Tigres": {"c1": "#FDE100", "c2": "#00519E"},
    "Monterrey": {"c1": "#002452", "c2": "#FFFFFF"},
    "Toluca": {"c1": "#DA291C", "c2": "#FFFFFF"}
}

EQUIPOS_LIGA_MX_BASE = {
    "América": {"altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2},
    "Chivas": {"altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5},
    "Cruz Azul": {"altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0},
    "Tigres": {"altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8},
    "Monterrey": {"altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1},
    "Toluca": {"altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9}
}

EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "w": 12, "l": 6, "ip": 110.0, "whip": 1.18, "k": 125},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "w": 14, "l": 5, "ip": 125.0, "whip": 1.12, "k": 140},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 111, "era_base": 3.65, "w": 12, "l": 5, "ip": 115.0, "whip": 1.17, "k": 130},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "w": 10, "l": 7, "ip": 105.0, "whip": 1.20, "k": 115},
    "Cincinnati Reds": {"id": 113, "wRC_plus": 98, "era_base": 4.40, "w": 7, "l": 10, "ip": 89.0, "whip": 1.33, "k": 86},
    "Cleveland Guardians": {"id": 114, "wRC_plus": 99, "era_base": 3.50, "w": 12, "l": 5, "ip": 112.0, "whip": 1.15, "k": 122}
}

@st.cache_data(ttl=1800)
def obtener_abridores_mlb_hoy(team_id_local, team_id_visita):
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={hoy}&endDate={hoy}&hydrate=probablePitcher"
    p_loc, p_vis = "Por Confirmar", "Por Confirmar"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            dates = data.get("dates", [])
            if dates:
                games = dates[0].get("games", [])
                for g in games:
                    home_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
                    if home_id == team_id_local:
                        p_loc = g.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        p_vis = g.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        break
    except Exception:
        pass
    return p_loc, p_vis

# ==========================================
# ESTILOS CSS ESTILO PROPS BR (CYBER NEÓN DARK)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Orbitron:wght@700;900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
        background-color: #0b0e11 !important;
    }
    
    .stApp { 
        background-color: #0b0e11 !important; 
        color: #e2e8f0; 
    }
    
    .top-deporte-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        color: #f5d742 !important;
        margin-right: 15px;
    }
    
    div[role="radiogroup"] label * {
        font-size: 16px !important;
        font-weight: 900 !important;
        color: #00ff66 !important;
    }

    /* ESTILO TARJETA PROPS BR */
    .propsbr-card {
        background: #14181d;
        border: 1px solid #1e252d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .propsbr-card.star {
        border-left: 4px solid #ffd700;
        background: #1a170a;
    }
    .propsbr-card.trap {
        border-left: 4px solid #ff3355;
        background: #240d13;
    }
    .propsbr-card.bet {
        border-left: 4px solid #00ff66;
    }

    .badge-star-br {
        background: #ffd700; color: #000; font-weight: 900; font-size: 11px; padding: 2px 8px; border-radius: 4px; float: right;
    }
    .badge-bet-br {
        background: #00ff66; color: #000; font-weight: 900; font-size: 11px; padding: 2px 8px; border-radius: 4px; float: right;
    }
    .badge-trap-br {
        background: #ff3355; color: #fff; font-weight: 900; font-size: 11px; padding: 2px 8px; border-radius: 4px; float: right;
    }
    .odd-chip-gold {
        background: #2b2311; border: 1px solid #4a3812; color: #ffc800; font-weight: 900; font-size: 13px; padding: 3px 8px; border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

def to_american_str(prob):
    if prob <= 0 or prob >= 1: return "+100"
    dec = 1.0 / prob
    return f"+{int(round((dec - 1) * 100))}" if dec >= 2.0 else f"{int(round(-100 / (dec - 1)))}"

# BARRA SUPERIOR DE DEPORTES
c_top_label, c_top_radio = st.columns([1, 3])
with c_top_label:
    st.markdown("<div class='top-deporte-title'>DEPORTE:</div>", unsafe_allow_html=True)
with c_top_radio:
    deporte = st.radio("", ["⚽ Liga MX (API LIVE)", "⚾ MLB Sabermétrico (API AUTO)"], horizontal=True, label_visibility="collapsed")

es_mlb = "MLB" in deporte
deporte_actual_key = "MLB" if es_mlb else "Liga MX"

# RENDERIZADO DE TARJETA ESTILO PROPS BR CON GRÁFICAS DE BARRAS
def render_card_estilo_propsbr(titulo, prob_val, ev, mercado_str, momio_val, linea_val="", es_mlb_flag=True):
    es_trampa, msj_trampa = evaluar_riesgo_trampa(prob_val, momio_val, ev)
    es_estrella = (0.75 <= prob_val <= 0.90) and (0.02 < ev <= 0.18) and not es_trampa
    
    if es_trampa:
        card_cls = "propsbr-card trap"
        badge_html = "<span class='badge-trap-br'>⚠️ ALERTA TRAMPA</span>"
    elif es_estrella:
        card_cls = "propsbr-card star"
        badge_html = "<span class='badge-star-br'>💎 APUESTA ESTRELLA</span>"
    elif ev > 0.02:
        card_cls = "propsbr-card bet"
        badge_html = "<span class='badge-bet-br'>BET (+EV)</span>"
    else:
        card_cls = "propsbr-card"
        badge_html = "<span style='color:#718096; font-size:11px; float:right;'>SKIP</span>"

    sparkline_html = generar_grafica_barras_propsbr(prob_val)

    col1, col2, col3, col4 = st.columns([2.5, 1, 1.2, 0.8])
    with col1:
        st.markdown(f"""
        <div class="{card_cls}">
            {badge_html}
            <div style="font-size:15px; font-weight:800; color:#fff;">{titulo}</div>
            <div style="margin-top:4px;">
                <span class="odd-chip-gold">{momio_val:.2f} ↗</span>
                <span style="color:#718096; font-size:12px; margin-left:6px;">Línea: {linea_val if linea_val else 'ML'}</span>
            </div>
            {f'<div style="color:#ff3355; font-size:11px; font-weight:800; margin-top:4px;">{msj_trampa}</div>' if es_trampa else ''}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="text-align:center; padding-top:10px;">
            <div style="font-size:10px; color:#718096; font-weight:800;">PROB REAL</div>
            <div style="font-size:15px; color:#00ff66; font-weight:900;">{prob_val*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="text-align:center; padding-top:10px;">
            <div style="font-size:10px; color:#718096; font-weight:800;">TENDENCIA L10</div>
            {sparkline_html}
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='padding-top:12px;'></div>", unsafe_allow_html=True)
        key_btn = f"btn_{'mlb' if es_mlb_flag else 'mx'}_{mercado_str}"
        if st.button("➕ APUESTA", key=key_btn):
            registrar_apuesta(deporte_actual_key, partido_nombre_global, local_nombre, visita_nombre, mercado_str, linea_val, momio_val, ev)

# ==========================================
# SECCIÓN LIGA MX / MLB CON TARJETAS PROPS BR
# ==========================================
if not es_mlb:
    local_nombre, visita_nombre = "América", "Chivas"
    partido_nombre_global = f"{local_nombre} vs {visita_nombre}"
    st.subheader(f"⚽ {partido_nombre_global}")
    
    # Simulación de datos para veredictos de prueba Liga MX
    render_card_estilo_propsbr(f"Gana {local_nombre}", 0.58, 0.05, f"Gana {local_nombre}", 1.85, "ML", False)
    render_card_estilo_propsbr("Más de 2.5 Goles", 0.62, 0.08, "Más de 2.5 Goles", 1.90, "2.5", False)
    render_card_estilo_propsbr("Ambos Anotan: SÍ", 0.55, -0.02, "BTTS SÍ", 1.80, "BTTS", False)

else:
    EQUIPOS = EQUIPOS_MLB
    lista_equipos = sorted(list(EQUIPOS.keys()))
    
    c_sel1, c_sel2 = st.columns(2)
    local_nombre = c_sel1.selectbox("LOCAL", lista_equipos, index=0)
    visita_opciones = [e for e in lista_equipos if e != local_nombre]
    visita_nombre = c_sel2.selectbox("VISITANTE", visita_opciones, index=0)
    
    partido_nombre_global = f"{local_nombre} vs {visita_nombre}"
    
    p_loc_auto, p_vis_auto = obtener_abridores_mlb_hoy(EQUIPOS[local_nombre]["id"], EQUIPOS[visita_nombre]["id"])
    
    st.markdown(f"**⚾ ABRIDORES:** {local_nombre} ({p_loc_auto}) vs {visita_nombre} ({p_vis_auto})")
    
    st.markdown("### 👑 VEREDICTOS Y TENDENCIAS PROPS BR")
    
    # 7 Mercados Sabermétricos con el nuevo diseño visual de minigráficas PropsBR
    render_card_estilo_propsbr(f"Gana {local_nombre} (ML)", 0.61, 0.06, f"Gana {local_nombre} ML", 1.83, "ML", True)
    render_card_estilo_propsbr(f"Gana {visita_nombre} (ML)", 0.39, -0.05, f"Gana {visita_nombre} ML", 2.05, "ML", True)
    render_card_estilo_propsbr("Más de 8.5 Carreras (OVER)", 0.54, 0.03, "Over 8.5 Carreras", 1.90, "8.5", True)
    render_card_estilo_propsbr("Menos de 8.5 Carreras (UNDER)", 0.46, -0.04, "Under 8.5 Carreras", 1.90, "8.5", True)
    render_card_estilo_propsbr(f"Abridor {p_loc_auto}: OVER 5.5 K's", 0.78, 0.12, f"Over 5.5 K's {p_loc_auto}", 1.87, "5.5", True)
    render_card_estilo_propsbr(f"Abridor {p_loc_auto}: OVER 15.5 Outs", 0.65, 0.05, f"Over 15.5 Outs {p_loc_auto}", 1.75, "15.5", True)
    render_card_estilo_propsbr("NRFI: 0 Carreras 1ra Entrada", 0.56, 0.02, "NRFI 1st Inning", 1.83, "NRFI", True)

# ==========================================
# PANEL INFERIOR: TRACKER
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
if st.button("🔍 VERIFICAR RESULTADOS EN VIVO", use_container_width=True):
    num_act = auto_verificar_apuestas()
    st.toast(f"Resultados actualizados ({num_act} cambios)", icon="⚽")

historial = cargar_base_datos()
st.markdown(f"### 📈 TRACKER DE APUESTAS GUARDADAS ({len(historial)})")

if historial:
    df_h = pd.DataFrame(historial)
    st.dataframe(df_h[["fecha", "deporte", "partido", "mercado", "momio", "resultado_real", "estado"]], use_container_width=True)
else:
    st.info("💡 No hay apuestas guardadas aún. Presiona `➕ APUESTA` en cualquier veredicto.")
