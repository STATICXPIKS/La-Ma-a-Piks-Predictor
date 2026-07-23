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

def auto_verificar_apuestas():
    historial = cargar_base_datos()
    actualizados = 0

    url_mx = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard"
    res_mx = {}
    try:
        r_mx = requests.get(url_mx, timeout=5)
        if r_mx.status_code == 200:
            events = r_mx.json().get("events", [])
            for ev_item in events:
                comp = ev_item.get("competitions", [])[0]
                status = comp.get("status", {}).get("type", {}).get("completed", False)
                if status:
                    teams = comp.get("competitors", [])
                    loc_name, vis_name = "", ""
                    loc_score, vis_score = 0, 0
                    for t in teams:
                        if t.get("homeAway") == "home":
                            loc_name = t.get("team", {}).get("name", "")
                            loc_score = int(t.get("score", 0))
                        else:
                            vis_name = t.get("team", {}).get("name", "")
                            vis_score = int(t.get("score", 0))
                    res_mx[f"{loc_name} vs {vis_name}"] = {"loc_score": loc_score, "vis_score": vis_score}
    except Exception:
        pass

    for item in historial:
        if item["estado"] == "PENDING":
            dep = item["deporte"]
            if "Liga MX" in dep:
                for match_title, score_data in res_mx.items():
                    if item["equipo_loc"].lower() in match_title.lower() and item["equipo_vis"].lower() in match_title.lower():
                        g_loc = score_data["loc_score"]
                        g_vis = score_data["vis_score"]
                        tot_goles = g_loc + g_vis
                        mercado = item["mercado"]
                        item["resultado_real"] = f"{g_loc} - {g_vis}"

                        if "Gana" in mercado:
                            if item["equipo_loc"] in mercado and g_loc > g_vis: item["estado"] = "WIN"
                            elif item["equipo_vis"] in mercado and g_vis > g_loc: item["estado"] = "WIN"
                            else: item["estado"] = "LOSS"
                        elif "1X" in mercado:
                            item["estado"] = "WIN" if g_loc >= g_vis else "LOSS"
                        elif "X2" in mercado:
                            item["estado"] = "WIN" if g_vis >= g_loc else "LOSS"
                        elif "2.5 Goles" in mercado:
                            item["estado"] = "WIN" if tot_goles > 2.5 else "LOSS"
                        elif "BTTS" in mercado:
                            item["estado"] = "WIN" if (g_loc > 0 and g_vis > 0) else "LOSS"
                        actualizados += 1

    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    return actualizados

# ==========================================
# BASE DE DATOS Y JERSEYS: LIGA MX
# ==========================================
JERSEYS_LIGA_MX = {
    "América": {"c1": "#FDE100", "c2": "#001A49"},
    "Atlante": {"c1": "#002B49", "c2": "#C8102E"},
    "Atlas": {"c1": "#000000", "c2": "#DA291C"},
    "Chivas": {"c1": "#DA291C", "c2": "#FFFFFF"},
    "Cruz Azul": {"c1": "#00519E", "c2": "#FFFFFF"},
    "Juárez": {"c1": "#78BE20", "c2": "#000000"},
    "León": {"c1": "#007A33", "c2": "#FDE100"},
    "Monterrey": {"c1": "#002452", "c2": "#FFFFFF"},
    "Necaxa": {"c1": "#DA291C", "c2": "#FFFFFF"},
    "Pachuca": {"c1": "#002B49", "c2": "#FFFFFF"},
    "Puebla": {"c1": "#003366", "c2": "#FFFFFF"},
    "Pumas": {"c1": "#002B49", "c2": "#C8A062"},
    "Querétaro": {"c1": "#00519E", "c2": "#000000"},
    "San Luis": {"c1": "#DA291C", "c2": "#002B49"},
    "Santos": {"c1": "#007A33", "c2": "#FFFFFF"},
    "Tigres": {"c1": "#FDE100", "c2": "#00519E"},
    "Tijuana": {"c1": "#DA291C", "c2": "#000000"},
    "Toluca": {"c1": "#DA291C", "c2": "#FFFFFF"}
}

EQUIPOS_LIGA_MX_BASE = {
    "América": {"altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2},
    "Atlante": {"altitud": 2240, "att": 1.35, "def": 1.20, "corners": 5.0},
    "Atlas": {"altitud": 1560, "att": 1.25, "def": 1.30, "corners": 4.5},
    "Chivas": {"altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5},
    "Cruz Azul": {"altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0},
    "Juárez": {"altitud": 1130, "att": 1.25, "def": 1.40, "corners": 4.4},
    "León": {"altitud": 1815, "att": 1.45, "def": 1.25, "corners": 5.1},
    "Monterrey": {"altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1},
    "Necaxa": {"altitud": 1800, "att": 1.40, "def": 1.25, "corners": 4.7},
    "Pachuca": {"altitud": 2400, "att": 1.70, "def": 1.20, "corners": 5.4},
    "Puebla": {"altitud": 2230, "att": 1.15, "def": 1.50, "corners": 4.2},
    "Pumas": {"altitud": 2240, "att": 1.50, "def": 1.15, "corners": 5.2},
    "Querétaro": {"altitud": 1820, "att": 1.10, "def": 1.35, "corners": 4.0},
    "San Luis": {"altitud": 1850, "att": 1.20, "def": 1.40, "corners": 4.1},
    "Santos": {"altitud": 1120, "att": 1.35, "def": 1.45, "corners": 4.9},
    "Tigres": {"altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8},
    "Tijuana": {"altitud": 60, "att": 1.30, "def": 1.35, "corners": 4.8},
    "Toluca": {"altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9}
}

@st.cache_data(ttl=3600)
def obtener_stats_liga_mx_api():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/standings"
    stats_actualizadas = EQUIPOS_LIGA_MX_BASE.copy()
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", [])
            if children:
                standings = children[0].get("standings", {}).get("entries", [])
                for entry in standings:
                    team_name = entry.get("team", {}).get("name", "")
                    stats = entry.get("stats", [])
                    mp, gf, ga = 1, 0, 0
                    for s in stats:
                        if s.get("name") == "gamesPlayed": mp = s.get("value", 1)
                        if s.get("name") == "pointsFor": gf = s.get("value", 0)
                        if s.get("name") == "pointsAgainst": ga = s.get("value", 0)
                    if mp > 0:
                        att_calc = max(0.8, gf / mp)
                        def_calc = max(0.7, ga / mp)
                        for eq in stats_actualizadas:
                            if eq.lower() in team_name.lower() or team_name.lower() in eq.lower():
                                stats_actualizadas[eq]["att"] = round(att_calc, 2)
                                stats_actualizadas[eq]["def"] = round(def_calc, 2)
    except Exception:
        pass
    return stats_actualizadas

# ==========================================
# BASE DE DATOS Y JERSEYS: MLB
# ==========================================
JERSEYS_MLB = {
    "NY Yankees": {"c1": "#001C43", "c2": "#FFFFFF"},
    "LA Dodgers": {"c1": "#005A9C", "c2": "#FFFFFF"},
    "Boston Red Sox": {"c1": "#BD3039", "c2": "#0C2340"},
    "Houston Astros": {"c1": "#002D62", "c2": "#EB6E1F"},
    "Atlanta Braves": {"c1": "#13274F", "c2": "#CE1141"},
    "SD Padres": {"c1": "#2F241D", "c2": "#FFC425"},
    "Chicago Cubs": {"c1": "#0E3386", "c2": "#CC3433"},
    "SF Giants": {"c1": "#FD5A1E", "c2": "#000000"},
    "NY Mets": {"c1": "#002D72", "c2": "#FF5910"},
    "Philadelphia Phillies": {"c1": "#E81828", "c2": "#002D72"},
    "Texas Rangers": {"c1": "#003278", "c2": "#C0111F"},
    "Toronto Blue Jays": {"c1": "#134A8E", "c2": "#1D2D5C"},
    "Seattle Mariners": {"c1": "#0C2340", "c2": "#005C5C"},
    "Baltimore Orioles": {"c1": "#DF4601", "c2": "#000000"},
    "Tampa Bay Rays": {"c1": "#092C5C", "c2": "#8FBCE6"},
    "Arizona Diamondbacks": {"c1": "#A71930", "c2": "#E3D4AD"},
    "Milwaukee Brewers": {"c1": "#12284C", "c2": "#FFC52F"},
    "St. Louis Cardinals": {"c1": "#C41E3A", "c2": "#0C2340"},
    "Cleveland Guardians": {"c1": "#0C2340", "c2": "#E31937"},
    "Minnesota Twins": {"c1": "#002B5C", "c2": "#D31145"},
    "Detroit Tigers": {"c1": "#0C2340", "c2": "#FA4616"},
    "Chicago White Sox": {"c1": "#27251F", "c2": "#FFFFFF"},
    "KC Royals": {"c1": "#004687", "c2": "#74B4E7"},
    "LA Angels": {"c1": "#003263", "c2": "#BA0021"},
    "Cincinnati Reds": {"c1": "#C6011F", "c2": "#000000"},
    "Colorado Rockies": {"c1": "#333366", "c2": "#C4CED4"},
    "Miami Marlins": {"c1": "#00A3E0", "c2": "#EF3340"},
    "Pittsburgh Pirates": {"c1": "#FDB827", "c2": "#000000"},
    "Washington Nationals": {"c1": "#AB0003", "c2": "#14225A"},
    "Oakland Athletics": {"c1": "#003831", "c2": "#EFB21E"}
}

EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "w": 12, "l": 6, "ip": 110.0, "whip": 1.18, "k": 125, "bb": 35},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "w": 14, "l": 5, "ip": 125.0, "whip": 1.12, "k": 140, "bb": 30},
    "Boston Red Sox": {"id": 111, "wRC_plus": 105, "era_base": 4.10, "w": 8, "l": 8, "ip": 98.0, "whip": 1.28, "k": 102, "bb": 40},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "w": 10, "l": 7, "ip": 105.0, "whip": 1.20, "k": 115, "bb": 36},
    "Atlanta Braves": {"id": 144, "wRC_plus": 114, "era_base": 3.80, "w": 11, "l": 6, "ip": 108.0, "whip": 1.22, "k": 118, "bb": 38},
    "SD Padres": {"id": 135, "wRC_plus": 106, "era_base": 3.70, "w": 9, "l": 8, "ip": 102.0, "whip": 1.19, "k": 110, "bb": 34},
    "Chicago Cubs": {"id": 112, "wRC_plus": 102, "era_base": 3.95, "w": 8, "l": 9, "ip": 95.0, "whip": 1.25, "k": 98, "bb": 42},
    "SF Giants": {"id": 137, "wRC_plus": 96, "era_base": 3.85, "w": 7, "l": 9, "ip": 92.0, "whip": 1.21, "k": 90, "bb": 35},
    "NY Mets": {"id": 121, "wRC_plus": 108, "era_base": 3.80, "w": 10, "l": 7, "ip": 104.0, "whip": 1.22, "k": 112, "bb": 37},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 111, "era_base": 3.65, "w": 12, "l": 5, "ip": 115.0, "whip": 1.17, "k": 130, "bb": 32},
    "Texas Rangers": {"id": 140, "wRC_plus": 104, "era_base": 4.20, "w": 7, "l": 10, "ip": 90.0, "whip": 1.30, "k": 88, "bb": 44},
    "Toronto Blue Jays": {"id": 141, "wRC_plus": 101, "era_base": 3.90, "w": 8, "l": 8, "ip": 96.0, "whip": 1.24, "k": 95, "bb": 39},
    "Seattle Mariners": {"id": 136, "wRC_plus": 95, "era_base": 3.40, "w": 11, "l": 6, "ip": 120.0, "whip": 1.10, "k": 135, "bb": 28},
    "Baltimore Orioles": {"id": 110, "wRC_plus": 112, "era_base": 3.85, "w": 11, "l": 6, "ip": 106.0, "whip": 1.21, "k": 114, "bb": 36},
    "Tampa Bay Rays": {"id": 139, "wRC_plus": 98, "era_base": 3.60, "w": 9, "l": 8, "ip": 100.0, "whip": 1.16, "k": 108, "bb": 31},
    "Arizona Diamondbacks": {"id": 109, "wRC_plus": 105, "era_base": 4.25, "w": 8, "l": 9, "ip": 94.0, "whip": 1.31, "k": 92, "bb": 45},
    "Milwaukee Brewers": {"id": 158, "wRC_plus": 100, "era_base": 3.60, "w": 10, "l": 6, "ip": 103.0, "whip": 1.18, "k": 109, "bb": 33},
    "St. Louis Cardinals": {"id": 138, "wRC_plus": 97, "era_base": 4.10, "w": 7, "l": 9, "ip": 91.0, "whip": 1.27, "k": 85, "bb": 40},
    "Cleveland Guardians": {"id": 114, "wRC_plus": 99, "era_base": 3.50, "w": 12, "l": 5, "ip": 112.0, "whip": 1.15, "k": 122, "bb": 30},
    "Minnesota Twins": {"id": 142, "wRC_plus": 104, "era_base": 3.90, "w": 9, "l": 8, "ip": 99.0, "whip": 1.23, "k": 105, "bb": 38},
    "Detroit Tigers": {"id": 116, "wRC_plus": 96, "era_base": 3.80, "w": 8, "l": 8, "ip": 95.0, "whip": 1.20, "k": 96, "bb": 35},
    "Chicago White Sox": {"id": 145, "wRC_plus": 82, "era_base": 4.90, "w": 4, "l": 14, "ip": 80.0, "whip": 1.42, "k": 72, "bb": 50},
    "KC Royals": {"id": 118, "wRC_plus": 102, "era_base": 3.90, "w": 9, "l": 7, "ip": 101.0, "whip": 1.24, "k": 100, "bb": 37},
    "LA Angels": {"id": 108, "wRC_plus": 94, "era_base": 4.50, "w": 6, "l": 11, "ip": 88.0, "whip": 1.35, "k": 82, "bb": 46},
    "Cincinnati Reds": {"id": 113, "wRC_plus": 98, "era_base": 4.40, "w": 7, "l": 10, "ip": 89.0, "whip": 1.33, "k": 86, "bb": 43},
    "Colorado Rockies": {"id": 115, "wRC_plus": 90, "era_base": 5.40, "w": 4, "l": 13, "ip": 78.0, "whip": 1.50, "k": 68, "bb": 52},
    "Miami Marlins": {"id": 146, "wRC_plus": 88, "era_base": 4.30, "w": 5, "l": 12, "ip": 85.0, "whip": 1.32, "k": 80, "bb": 44},
    "Pittsburgh Pirates": {"id": 134, "wRC_plus": 92, "era_base": 4.00, "w": 8, "l": 9, "ip": 93.0, "whip": 1.26, "k": 91, "bb": 41},
    "Washington Nationals": {"id": 120, "wRC_plus": 93, "era_base": 4.60, "w": 6, "l": 11, "ip": 86.0, "whip": 1.36, "k": 78, "bb": 47},
    "Oakland Athletics": {"id": 133, "wRC_plus": 95, "era_base": 4.50, "w": 6, "l": 11, "ip": 87.0, "whip": 1.34, "k": 81, "bb": 45}
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
                    away_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
                    if home_id == team_id_local or away_id == team_id_local:
                        p_loc = g.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        p_vis = g.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        break
    except Exception:
        pass
    return p_loc, p_vis

# ESTILOS CSS GENERALES
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0b0e14; color: #ffffff; }
    
    label { color: #38bdf8 !important; font-weight: 700 !important; font-size: 13px !important; }
    .stSelectbox label, .stNumberInput label, .stRadio label, .stSlider label { color: #38bdf8 !important; }
    
    input, div[data-baseweb="select"] span, div[data-baseweb="select"] input {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stNumberInput input { color: #000000 !important; font-weight: 800 !important; }
    
    .card-pro {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    
    .badge-bet { background: #10b981; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    .badge-skip { background: #ef4444; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    
    .market-title { font-size: 14px; font-weight: 700; color: #38bdf8; margin-top: 14px; margin-bottom: 6px; }
    .subtext { color: #cbd5e1; font-size: 12px; margin-top: 3px; }
    
    .team-badge-card {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }

    .header-big-left, .header-big-right {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .header-text-left, .header-text-right {
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        letter-spacing: -1px;
        line-height: 1;
    }
    
    .pitcher-box {
        background: #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        font-size: 13px;
    }

    div.stButton > button {
        background-color: #38bdf8 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 13px !important;
        border-radius: 6px !important;
        border: none !important;
    }
    div.stButton > button:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def generar_jersey_svg(equipo_nombre, diccionario_jerseys):
    col = diccionario_jerseys.get(equipo_nombre, {"c1": "#333333", "c2": "#666666"})
    c1, c2 = col["c1"], col["c2"]
    
    svg = f"""
    <svg width="42" height="42" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M30 20 L40 10 L60 10 L70 20 L85 30 L75 45 L68 40 L68 85 L32 85 L32 40 L25 45 L15 30 Z" fill="{c1}" stroke="#ffffff" stroke-width="3"/>
        <path d="M50 10 L50 85" stroke="{c2}" stroke-width="12"/>
        <path d="M30 20 L40 10 L60 10 L70 20" fill="none" stroke="#ffffff" stroke-width="3"/>
    </svg>
    """
    return svg

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

def to_american_str(prob):
    if prob <= 0 or prob >= 1: return "+100"
    dec = 1.0 / prob
    if dec >= 2.0:
        am = int(round((dec - 1) * 100))
        return f"+{am}"
    else:
        am = int(round(-100 / (dec - 1)))
        return f"{am}"

# BARRA SUPERIOR DE NAVEGACIÓN
c_top1, c_top2, _ = st.columns([2, 3, 5])
with c_top1:
    st.markdown("<span style='font-size:12px; color:#38bdf8; font-weight:800;'>SELECCIONAR DEPORTE:</span>", unsafe_allow_html=True)
    deporte = st.radio("", ["⚽ Liga MX (API LIVE)", "⚾ MLB Sabermétrico (API AUTO)"], horizontal=True, label_visibility="collapsed")

es_mlb = "MLB" in deporte
deporte_actual_key = "MLB" if es_mlb else "Liga MX"

col_izq, col_der = st.columns([1, 1], gap="large")

# ==========================================
# SECCIÓN LIGA MX
# ==========================================
if not es_mlb:
    EQUIPOS = obtener_stats_liga_mx_api()
    JERSEYS = JERSEYS_LIGA_MX
    
    with col_izq:
        st.markdown("""
        <div class="header-big-left">
            <img src="https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/22.png" style="height: 75px; margin-right: 15px; object-fit: contain;">
            <span class="header-text-left">ANALISIS PRO-LIGA MX</span>
        </div>
        """, unsafe_allow_html=True)

        c_sel1, c_sel2 = st.columns(2)
        lista_equipos = sorted(list(EQUIPOS.keys()))
        
        local_nombre = c_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Tijuana") if "Tijuana" in lista_equipos else 0)
        visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
        visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("León") if "León" in visita_opciones else 0)

        eq_local_base, eq_visita_base = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

        with st.expander("📊 AJUSTAR ESTADÍSTICAS DEL PARTIDO (LIGA MX)", expanded=False):
            c_mx1, c_mx2 = st.columns(2)
            with c_mx1:
                att_loc = c_mx1.number_input(f"Ataque (xG Base) {local_nombre[:3]}", value=float(eq_local_base["att"]), step=0.05, format="%.2f")
                def_loc = c_mx1.number_input(f"Defensa (Concedido) {local_nombre[:3]}", value=float(eq_local_base["def"]), step=0.05, format="%.2f")
                corn_loc = c_mx1.number_input(f"Córners Promedio {local_nombre[:3]}", value=float(eq_local_base["corners"]), step=0.1, format="%.1f")
            with c_mx2:
                att_vis = c_mx2.number_input(f"Ataque (xG Base) {visita_nombre[:3]}", value=float(eq_visita_base["att"]), step=0.05, format="%.2f")
                def_vis = c_mx2.number_input(f"Defensa (Concedido) {visita_nombre[:3]}", value=float(eq_visita_base["def"]), step=0.05, format="%.2f")
                corn_vis = c_mx2.number_input(f"Córners Promedio {visita_nombre[:3]}", value=float(eq_visita_base["corners"]), step=0.1, format="%.1f")

        diff_altitud = max(0, eq_local_base["altitud"] - eq_visita_base["altitud"])
        penal_altitud = diff_altitud * 0.00015

        xg_local = (att_loc * def_vis) * 1.15
        xg_visita = max(0.2, (att_vis * def_loc) * (1 - penal_altitud))

        max_goles = 6
        matrix = np.zeros((max_goles, max_goles))
        for x in range(max_goles):
            for y in range(max_goles):
                matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
        matrix /= np.sum(matrix)

        xg_local_1ht, xg_visita_1ht = xg_local * 0.45, xg_visita * 0.45
        matrix_1ht = np.zeros((max_goles, max_goles))
        for x in range(max_goles):
            for y in range(max_goles):
                matrix_1ht[x, y] = poisson.pmf(x, xg_local_1ht) * poisson.pmf(y, xg_visita_1ht)
        matrix_1ht /= np.sum(matrix_1ht)

        c_esc1, c_esc2 = st.columns(2)
        with c_esc1:
            st.markdown(f"""
            <div class="team-badge-card">
                <div style="margin-right: 12px;">{generar_jersey_svg(local_nombre, JERSEYS)}</div>
                <div>
                    <div style="font-weight: 800; color: #fff; font-size: 16px;">{local_nombre}</div>
                    <div style="color: #10b981; font-weight: 800; font-size: 14px;">{xg_local:.2f} <span style="font-size: 11px; color: #38bdf8;">xG Esperado</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_esc2:
            st.markdown(f"""
            <div class="team-badge-card">
                <div style="margin-right: 12px;">{generar_jersey_svg(visita_nombre, JERSEYS)}</div>
                <div>
                    <div style="font-weight: 800; color: #fff; font-size: 16px;">{visita_nombre}</div>
                    <div style="color: #38bdf8; font-weight: 800; font-size: 14px;">{xg_visita:.2f} <span style="font-size: 11px; color: #38bdf8;">xG Esperado</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        cg1, cg2 = st.columns(2)
        minutos = [0, 20, 40, 60, 80]
        xg_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xg_local))
        xg_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xg_visita))

        fig_xg = go.Figure()
        fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_local, mode='lines', name=local_nombre, line=dict(color='#10b981', width=2.5)))
        fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_visita, mode='lines', name=visita_nombre, line=dict(color='#38bdf8', width=2.5)))
        fig_xg.update_layout(
            title=dict(text="xG Progresión por Minuto", font=dict(size=12, color="#ffffff")),
            height=190, paper_bgcolor='#121721', plot_bgcolor='#121721', font=dict(color='#ffffff', size=9),
            xaxis=dict(gridcolor='#1e2638'), yaxis=dict(gridcolor='#1e2638'), margin=dict(l=25, r=15, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        prob_1 = np.sum(np.tril(matrix, -1))
        prob_x = np.sum(np.diag(matrix))
        prob_2 = np.sum(np.triu(matrix, 1))

        fig_pie = go.Figure(data=[go.Pie(
            labels=[local_nombre, 'Empate', visita_nombre], values=[prob_1, prob_x, prob_2], hole=.55,
            marker=dict(colors=['#10b981', '#f59e0b', '#38bdf8'])
        )])
        fig_pie.update_layout(
            title=dict(text="Distribución 1X2", font=dict(size=12, color="#ffffff")),
            height=190, paper_bgcolor='#121721', font=dict(color='#ffffff', size=9),
            margin=dict(l=15, r=15, t=30, b=15), showlegend=False
        )

        with cg1: st.plotly_chart(fig_xg, use_container_width=True)
        with cg2: st.plotly_chart(fig_pie, use_container_width=True)

        with st.expander("⚙️ MOMIOS DE TU CASA DE APUESTAS (CALCULADORA EV)", expanded=True):
            formato_m = st.radio("Formato:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True)
            es_dec = "Decimal" in formato_m
            tipo_str = "Decimal" if es_dec else "Americano"
            
            f1_1, f1_2, f1_3 = st.columns(3)
            m_1_in = f1_1.number_input(f"GANA {local_nombre.upper()}", value=4.800 if es_dec else 380, format="%.3f" if es_dec else "%d")
            m_x_in = f1_2.number_input("EMPATE", value=3.750 if es_dec else 275, format="%.3f" if es_dec else "%d")
            m_2_in = f1_3.number_input(f"GANA {visita_nombre.upper()}", value=1.710 if es_dec else -141, format="%.3f" if es_dec else "%d")
            
            f_do1, f_do2, f_do3 = st.columns(3)
            m_1x_in = f_do1.number_input(f"1X ({local_nombre[:3].upper()}/EMP)", value=2.100 if es_dec else 110, format="%.3f" if es_dec else "%d")
            m_12_in = f_do2.number_input("12 (LOCAL/VISITA)", value=1.280 if es_dec else -357, format="%.3f" if es_dec else "%d")
            m_x2_in = f_do3.number_input(f"X2 (EMP/{visita_nombre[:3].upper()})", value=1.180 if es_dec else -555, format="%.3f" if es_dec else "%d")

            f2_1, f2_2, f2_3 = st.columns(3)
            linea_goles = f2_1.selectbox("GOLES (90 Min)", ["O/U 2.5", "O/U 1.5"])
            m_over_in = f2_2.number_input("OVER 2.5", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
            m_under_in = f2_3.number_input("UNDER 2.5", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

            f3_1, f3_2, f3_3 = st.columns(3)
            linea_goles_1ht = f3_1.selectbox("GOLES (1HT)", ["1HT O/U 0.5", "1HT O/U 1.5"])
            es_1ht_05 = "0.5" in linea_goles_1ht
            
            m_over_1ht_in = f3_2.number_input(
                "1HT OVER 0.5" if es_1ht_05 else "1HT OVER 1.5", 
                value=(1.360 if es_1ht_05 else 2.650) if es_dec else (-278 if es_1ht_05 else 165), 
                format="%.3f" if es_dec else "%d"
            )
            m_under_1ht_in = f3_3.number_input(
                "1HT UNDER 0.5" if es_1ht_05 else "1HT UNDER 1.5", 
                value=(2.880 if es_1ht_05 else 1.450) if es_dec else (188 if es_1ht_05 else -222), 
                format="%.3f" if es_dec else "%d"
            )
            
            f4_1, f4_2, _ = st.columns(3)
            m_btts_s_in = f4_1.number_input("BTTS SÍ", value=1.770 if es_dec else -130, format="%.3f" if es_dec else "%d")
            m_btts_n_in = f4_2.number_input("BTTS NO", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>PROPS DE CÓRNERS (7 A 11 ENTEROS EXACTOS)</p>", unsafe_allow_html=True)
            f5_1, f5_2, f5_3 = st.columns(3)
            linea_corners_sel = f5_1.selectbox("Línea Córners", ["7", "8", "9", "10", "11"], index=1)
            m_corners_over_in = f5_2.number_input(f"Momio OVER ({linea_corners_sel})", value=1.850 if es_dec else -118, format="%.3f" if es_dec else "%d")
            m_corners_under_in = f5_3.number_input(f"Momio UNDER ({linea_corners_sel})", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")

            st.button("🔄 RECALCULAR VEREDICTOS LIGA MX", use_container_width=True)

            m_1 = to_decimal(m_1_in, tipo_str)
            m_2 = to_decimal(m_2_in, tipo_str)
            m_1x = to_decimal(m_1x_in, tipo_str)
            m_x2 = to_decimal(m_x2_in, tipo_str)
            m_over25 = to_decimal(m_over_in, tipo_str)
            m_over_1ht = to_decimal(m_over_1ht_in, tipo_str)
            m_btts_s = to_decimal(m_btts_s_in, tipo_str)
            m_corners_over = to_decimal(m_corners_over_in, tipo_str)
            m_corners_under = to_decimal(m_corners_under_in, tipo_str)

    with col_der:
        st.markdown("""
        <div class="header-big-right">
            <span style="font-size: 38px; margin-right: 12px; line-height:1;">👑</span>
            <span class="header-text-right">VEREDICTO MAÑA PIKS</span>
        </div>
        """, unsafe_allow_html=True)
        
        prob_1x = prob_1 + prob_x
        prob_x2 = prob_2 + prob_x
        prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
        prob_btts_si = np.sum(matrix[1:, 1:])
        
        if es_1ht_05:
            prob_1ht_target = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 0.5])
            texto_1ht_target = "1ra Mitad: Más de 0.5 Goles"
        else:
            prob_1ht_target = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 1.5])
            texto_1ht_target = "1ra Mitad: Más de 1.5 Goles"

        prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])
        prob_ha_visita = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (y - x) > 1])

        c_target = int(linea_corners_sel)
        lambda_corners = corn_loc + corn_vis
        prob_over_corners = 1.0 - poisson.cdf(c_target, lambda_corners)
        prob_under_corners = poisson.cdf(c_target - 1, lambda_corners)

        ev_1 = (prob_1 * m_1) - 1
        ev_2 = (prob_2 * m_2) - 1
        ev_1x = (prob_1x * m_1x) - 1
        ev_x2 = (prob_x2 * m_x2) - 1
        ev_over25 = (prob_over25 * m_over25) - 1
        ev_1ht = (prob_1ht_target * m_over_1ht) - 1
        ev_btts_si = (prob_btts_si * m_btts_s) - 1
        ev_corners_over = (prob_over_corners * m_corners_over) - 1
        ev_corners_under = (prob_under_corners * m_corners_under) - 1

        partido_nombre_mx = f"{local_nombre} vs {visita_nombre}"

        def render_card_pro_con_tracker(titulo, subtitulo, ev, badge, mercado_str, momio_val, linea_val=""):
            badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
            c_card1, c_card2 = st.columns([4, 1])
            with c_card1:
                st.markdown(f"""
                <div class="card-pro">
                    {badge_html}
                    <div style="font-weight: 800; font-size: 15px; color: #ffffff;">{titulo}</div>
                    <div class="subtext">{subtitulo} · <b>EV {ev*100:+.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            with c_card2:
                if st.button("➕ APUESTA", key=f"btn_mx_{mercado_str}"):
                    registrar_apuesta("Liga MX", partido_nombre_mx, local_nombre, visita_nombre, mercado_str, linea_val, momio_val, ev)

        st.markdown("<div class='market-title'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker(f"Gana {local_nombre} (1)", f"Prob. Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP", f"Gana {local_nombre}", m_1, "ML")
        render_card_pro_con_tracker(f"Gana {visita_nombre} (2)", f"Prob. Real: {prob_2*100:.1f}%", ev_2, "BET" if ev_2 > 0.03 else "SKIP", f"Gana {visita_nombre}", m_2, "ML")

        st.markdown("<div class='market-title'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker(f"{local_nombre} o Empate (1X)", f"Prob. Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP", f"{local_nombre} 1X", m_1x, "1X")
        render_card_pro_con_tracker(f"Empate o {visita_nombre} (X2)", f"Prob. Real: {prob_x2*100:.1f}%", ev_x2, "BET" if ev_x2 > 0.02 else "SKIP", f"{visita_nombre} X2", m_x2, "X2")

        st.markdown("<div class='market-title'>3. Total de Goles (Partido Completo)</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker("Más de 2.5 Goles", f"Prob. Real: {prob_over25*100:.1f}%", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP", "Más de 2.5 Goles", m_over25, "2.5")

        st.markdown("<div class='market-title'>4. Total de Goles 1ra Mitad (1HT)</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker(texto_1ht_target, f"Prob. Real: {prob_1ht_target*100:.1f}%", ev_1ht, "BET" if ev_1ht > 0.03 else "SKIP", texto_1ht_target, m_over_1ht, "1HT")

        st.markdown("<div class='market-title'>5. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker("Ambos Anotan: SÍ", f"Prob. Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP", "BTTS SÍ", m_btts_s, "BTTS")

        st.markdown("<div class='market-title'>6. Córners (Over / Under)</div>", unsafe_allow_html=True)
        render_card_pro_con_tracker(f"Más de {c_target} Córners (OVER)", f"Prob. Real: {prob_over_corners*100:.1f}%", ev_corners_over, "BET" if ev_corners_over > 0.03 else "SKIP", f"Córners Over {c_target}", m_corners_over, str(c_target))
        render_card_pro_con_tracker(f"Menos de {c_target} Córners (UNDER)", f"Prob. Real: {prob_under_corners*100:.1f}%", ev_corners_under, "BET" if ev_corners_under > 0.03 else "SKIP", f"Córners Under {c_target}", m_corners_under, str(c_target))

# ==========================================
# SECCIÓN MLB SABERMETRÍA EXCLUSIVA
# ==========================================
else:
    EQUIPOS = EQUIPOS_MLB
    JERSEYS = JERSEYS_MLB
    
    with col_izq:
        st.markdown("""
        <div class="header-big-left">
            <span style="font-size:50px; margin-right:15px; line-height:1;">⚾</span>
            <span class="header-text-left">ANALISIS SABERMÉTRICO MLB</span>
        </div>
        """, unsafe_allow_html=True)
        
        c_sel1, c_sel2 = st.columns(2)
        lista_equipos = sorted(list(EQUIPOS.keys()))
        
        local_nombre = c_sel1.selectbox("EQUIPO LOCAL (HOME)", lista_equipos, index=lista_equipos.index("Philadelphia Phillies") if "Philadelphia Phillies" in lista_equipos else 0)
        visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
        visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE (AWAY)", visita_opciones, index=visita_opciones.index("LA Dodgers") if "LA Dodgers" in visita_opciones else 0)

        eq_local_base, eq_visita_base = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

        pitcher_loc_auto, pitcher_vis_auto = obtener_abridores_mlb_hoy(eq_local_base["id"], eq_visita_base["id"])

        st.markdown(f"""
        <div class="pitcher-box">
            <b>⚾ ABRIDORES HOY (MLB API AUTO-FETCH):</b><br>
            • {local_nombre}: <b>{pitcher_loc_auto}</b><br>
            • {visita_nombre}: <b>{pitcher_vis_auto}</b>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📊 PARÁMETROS DE ABRIDORES Y CLIMA", expanded=True):
            st.markdown(f"<p style='color:#38bdf8; font-weight:800;'>ESTADÍSTICAS ABRIDOR LOCAL: {local_nombre[:3].upper()}</p>", unsafe_allow_html=True)
            pl1, pl2, pl3, pl4, pl5, pl6 = st.columns(6)
            w_loc = pl1.number_input("W", value=int(eq_local_base["w"]), step=1, key="w_loc")
            l_loc = pl2.number_input("L", value=int(eq_local_base["l"]), step=1, key="l_loc")
            ip_loc = pl3.number_input("IP", value=float(eq_local_base["ip"]), step=0.1, key="ip_loc")
            era_loc = pl4.number_input("ERA", value=float(eq_local_base["era_base"]), step=0.01, format="%.2f", key="era_loc")
            whip_loc = pl5.number_input("WHIP", value=float(eq_local_base["whip"]), step=0.01, format="%.2f", key="whip_loc")
            k_loc = pl6.number_input("K Total", value=int(eq_local_base["k"]), step=1, key="k_loc")

            st.markdown(f"<p style='color:#38bdf8; font-weight:800; margin-top:10px;'>ESTADÍSTICAS ABRIDOR VISITANTE: {visita_nombre[:3].upper()}</p>", unsafe_allow_html=True)
            pv1, pv2, pv3, pv4, pv5, pv6 = st.columns(6)
            w_vis = pv1.number_input("W", value=int(eq_visita_base["w"]), step=1, key="w_vis")
            l_vis = pv2.number_input("L", value=int(eq_visita_base["l"]), step=1, key="l_vis")
            ip_vis = pv3.number_input("IP", value=float(eq_visita_base["ip"]), step=0.1, key="ip_vis")
            era_vis = pv4.number_input("ERA", value=float(eq_visita_base["era_base"]), step=0.01, format="%.2f", key="era_vis")
            whip_vis = pv5.number_input("WHIP", value=float(eq_visita_base["whip"]), step=0.01, format="%.2f", key="whip_vis")
            k_vis = pv6.number_input("K Total", value=int(eq_visita_base["k"]), step=1, key="k_vis")

            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:10px;'>CONDICIONES DEL CLIMA</p>", unsafe_allow_html=True)
            cw1, cw2, cw3, cw4 = st.columns(4)
            viento_kmh = cw1.number_input("Viento (km/h)", value=16, step=1)
            viento_dir = cw2.selectbox("Dirección Viento", ["A favor (Out)", "En contra (In)", "Cruzado (Cross)"])
            temp_c = cw3.number_input("Temperatura (°C)", value=24, step=1)
            precip_pct = cw4.number_input("Precipitación (%)", value=0, step=5)

        mult_viento = 1.0
        if "favor" in viento_dir:
            mult_viento += (viento_kmh * 0.006)
        elif "contra" in viento_dir:
            mult_viento -= (viento_kmh * 0.006)
            
        mult_temp = 1.0 + ((temp_c - 21) * 0.003)
        mult_clima = mult_viento * mult_temp

        xr_local = ((eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * (whip_vis / 1.25) * 4.30) * mult_clima
        xr_visita = ((eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * (whip_loc / 1.25) * 4.10) * mult_clima

        max_c = 16
        matrix_mlb = np.zeros((max_c, max_c))
        for x in range(max_c):
            for y in range(max_c):
                matrix_mlb[x, y] = poisson.pmf(x, xr_local) * poisson.pmf(y, xr_visita)
        matrix_mlb /= np.sum(matrix_mlb)

        xr_loc_f5 = (eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * 2.35 * mult_clima
        xr_vis_f5 = (eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * 2.20 * mult_clima
        matrix_f5 = np.zeros((max_c, max_c))
        for x in range(max_c):
            for y in range(max_c):
                matrix_f5[x, y] = poisson.pmf(x, xr_loc_f5) * poisson.pmf(y, xr_vis_f5)
        matrix_f5 /= np.sum(matrix_f5)

        id_loc = eq_local_base.get("id", 147)
        id_vis = eq_visita_base.get("id", 119)
        logo_url_loc = f"https://www.mlbstatic.com/team-logos/{id_loc}.svg"
        logo_url_vis = f"https://www.mlbstatic.com/team-logos/{id_vis}.svg"

        c_esc1, c_esc2 = st.columns(2)
        with c_esc1:
            st.markdown(f"""
            <div class="team-badge-card">
                <img src="{logo_url_loc}" width="42" height="42" style="margin-right:12px; object-fit:contain;">
                <div>
                    <div style="font-weight: 800; color: #ffffff; font-size: 15px;">{local_nombre} (HOME)</div>
                    <div style="color: #10b981; font-weight: 800; font-size: 14px;">{xr_local:.2f} <span style="font-size: 11px; color: #38bdf8;">xR Carreras</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_esc2:
            st.markdown(f"""
            <div class="team-badge-card">
                <img src="{logo_url_vis}" width="42" height="42" style="margin-right:12px; object-fit:contain;">
                <div>
                    <div style="font-weight: 800; color: #ffffff; font-size: 15px;">{visita_nombre} (AWAY)</div>
                    <div style="color: #38bdf8; font-weight: 800; font-size: 14px;">{xr_visita:.2f} <span style="font-size: 11px; color: #38bdf8;">xR Carreras</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        cg1, cg2 = st.columns(2)
        innings = [1, 3, 5, 7, 9]
        xr_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xr_local))
        xr_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xr_visita))

        fig_xr = go.Figure()
        fig_xr.add_trace(go.Scatter(x=innings, y=xr_acc_local, mode='lines', name=local_nombre, line=dict(color='#10b981', width=2.5)))
        fig_xr.add_trace(go.Scatter(x=innings, y=xr_acc_visita, mode='lines', name=visita_nombre, line=dict(color='#38bdf8', width=2.5)))
        fig_xr.update_layout(
            title=dict(text="xR Progresión por Inning", font=dict(size=12, color="#ffffff")),
            height=190, paper_bgcolor='#121721', plot_bgcolor='#121721', font=dict(color='#ffffff', size=9),
            xaxis=dict(gridcolor='#1e2638'), yaxis=dict(gridcolor='#1e2638'), margin=dict(l=25, r=15, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        prob_ml_local = np.sum(np.tril(matrix_mlb, -1))
        prob_ml_visita = np.sum(np.triu(matrix_mlb, 1))

        fig_pie_mlb = go.Figure(data=[go.Pie(
            labels=[local_nombre, visita_nombre], values=[prob_ml_local, prob_ml_visita], hole=.55,
            marker=dict(colors=['#10b981', '#38bdf8'])
        )])
        fig_pie_mlb.update_layout(
            title=dict(text="Moneyline % Probabilidad", font=dict(size=12, color="#ffffff")),
            height=190, paper_bgcolor='#121721', font=dict(color='#ffffff', size=9),
            margin=dict(l=15, r=15, t=30, b=15), showlegend=False
        )

        with cg1: st.plotly_chart(fig_xr, use_container_width=True)
        with cg2: st.plotly_chart(fig_pie_mlb, use_container_width=True)

        with st.expander("⚙️ CAPTURA DE MOMIOS MLB (CASAS DE APUESTAS)", expanded=True):
            formato_m = st.radio("Formato Momios:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True, key="f_mlb")
            es_dec = "Decimal" in formato_m
            tipo_str = "Decimal" if es_dec else "Americano"
            
            # 1. MONEYLINE
            st.markdown("<p style='color:#38bdf8; font-weight:800;'>1. MONEYLINE (GANADOR DIRECTO)</p>", unsafe_allow_html=True)
            f1_1, f1_2 = st.columns(2)
            m_ml_loc_in = f1_1.number_input(f"ML {local_nombre.upper()}", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
            m_ml_vis_in = f1_2.number_input(f"ML {visita_nombre.upper()}", value=2.050 if es_dec else 105, format="%.3f" if es_dec else "%d")
            
            # 2. TOTAL DE CARRERAS
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>2. TOTAL DE CARRERAS (O/U)</p>", unsafe_allow_html=True)
            f2_1, f2_2, f2_3 = st.columns(3)
            linea_tot_mlb = f2_1.selectbox("LINEA TOTAL", ["8.5", "7.5", "9.5"])
            m_over_tot_in = f2_2.number_input("OVER TOTAL", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")
            m_under_tot_in = f2_3.number_input("UNDER TOTAL", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")

            # 3. RUN LINE (+1.5 Y -1.5 PARA AMBOS)
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>3. RUN LINE (+1.5 Y -1.5 AMBOS EQUIPOS)</p>", unsafe_allow_html=True)
            f3_1, f3_2, f3_3, f3_4 = st.columns(4)
            m_rl_loc_minus_in = f3_1.number_input(f"RL {local_nombre[:3]} -1.5", value=2.450 if es_dec else 145, format="%.3f" if es_dec else "%d")
            m_rl_loc_plus_in = f3_2.number_input(f"RL {local_nombre[:3]} +1.5", value=1.500 if es_dec else -200, format="%.3f" if es_dec else "%d")
            m_rl_vis_minus_in = f3_3.number_input(f"RL {visita_nombre[:3]} -1.5", value=2.600 if es_dec else 160, format="%.3f" if es_dec else "%d")
            m_rl_vis_plus_in = f3_4.number_input(f"RL {visita_nombre[:3]} +1.5", value=1.600 if es_dec else -166, format="%.3f" if es_dec else "%d")

            # 4. F5 ML Y F5 OVER/UNDER (3.5 A 5.5)
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>4. PRIMERAS 5 ENTRADAS (F5 ML Y OVER/UNDER 3.5 A 5.5)</p>", unsafe_allow_html=True)
            f4_1, f4_2, f4_3, f4_4, f4_5 = st.columns(5)
            m_f5_loc_in = f4_1.number_input(f"F5 ML {local_nombre[:3]}", value=1.800 if es_dec else -125, format="%.3f" if es_dec else "%d")
            m_f5_vis_in = f4_2.number_input(f"F5 ML {visita_nombre[:3]}", value=2.050 if es_dec else 105, format="%.3f" if es_dec else "%d")
            linea_f5_sel = f4_3.selectbox("Línea F5 O/U", ["3.5", "4.5", "5.5"], index=1)
            m_f5_over_in = f4_4.number_input(f"F5 OVER {linea_f5_sel}", value=1.850 if es_dec else -118, format="%.3f" if es_dec else "%d")
            m_f5_under_in = f4_5.number_input(f"F5 UNDER {linea_f5_sel}", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

            # 5. PONCHES (K'S) ABRIDORES DESDE 0.5 A 8.5 CON OVER Y UNDER
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>5. PROPS DE PONCHES (K'S - LÍNEA 0.5 A 8.5 OVER/UNDER)</p>", unsafe_allow_html=True)
            opciones_ks = ["0.5", "1.5", "2.5", "3.5", "4.5", "5.5", "6.5", "7.5", "8.5"]
            fk_1, fk_2, fk_3, fk_4, fk_5, fk_6 = st.columns(6)
            linea_k_loc = fk_1.selectbox(f"K's ({local_nombre[:3]})", opciones_ks, index=5)
            m_k_loc_over_in = fk_2.number_input(f"Over {linea_k_loc} K's ({local_nombre[:3]})", value=1.870 if es_dec else -115, format="%.3f" if es_dec else "%d")
            m_k_loc_under_in = fk_3.number_input(f"Under {linea_k_loc} K's ({local_nombre[:3]})", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")
            
            linea_k_vis = fk_4.selectbox(f"K's ({visita_nombre[:3]})", opciones_ks, index=5)
            m_k_vis_over_in = fk_5.number_input(f"Over {linea_k_vis} K's ({visita_nombre[:3]})", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")
            m_k_vis_under_in = fk_6.number_input(f"Under {linea_k_vis} K's ({visita_nombre[:3]})", value=1.870 if es_dec else -115, format="%.3f" if es_dec else "%d")

            # 6. OUTS ABRIDORES CON OVER Y UNDER
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>6. PROPS DE OUTS REGISTRADOS (OVER Y UNDER)</p>", unsafe_allow_html=True)
            fo_1, fo_2, fo_3, fo_4, fo_5, fo_6 = st.columns(6)
            linea_outs_loc = fo_1.selectbox(f"Outs ({local_nombre[:3]})", ["13.5", "14.5", "15.5", "17.5", "18.5"], index=2)
            m_outs_loc_over_in = fo_2.number_input(f"Over {linea_outs_loc} Outs ({local_nombre[:3]})", value=1.750 if es_dec else -133, format="%.3f" if es_dec else "%d")
            m_outs_loc_under_in = fo_3.number_input(f"Under {linea_outs_loc} Outs ({local_nombre[:3]})", value=2.000 if es_dec else 100, format="%.3f" if es_dec else "%d")
            
            linea_outs_vis = fo_4.selectbox(f"Outs ({visita_nombre[:3]})", ["13.5", "14.5", "15.5", "17.5", "18.5"], index=2)
            m_outs_vis_over_in = fo_5.number_input(f"Over {linea_outs_vis} Outs ({visita_nombre[:3]})", value=1.800 if es_dec else -125, format="%.3f" if es_dec else "%d")
            m_outs_vis_under_in = fo_6.number_input(f"Under {linea_outs_vis} Outs ({visita_nombre[:3]})", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

            # 7. MERCADO 1ER INNING: NRFI Y YRFI
            st.markdown("<p style='color:#38bdf8; font-weight:800; margin-top:8px;'>7. MERCADO 1ER INNING (NRFI / YRFI)</p>", unsafe_allow_html=True)
            fn1, fn2 = st.columns(2)
            m_nrfi_in = fn1.number_input("NRFI - No Run 1st Inning (Under 0.5)", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
            m_yrfi_in = fn2.number_input("YRFI - Yes Run 1st Inning (Over 0.5)", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

            st.button("🔄 RECALCULAR VEREDICTOS MLB", use_container_width=True)

            m_ml_loc = to_decimal(m_ml_loc_in, tipo_str)
            m_ml_vis = to_decimal(m_ml_vis_in, tipo_str)
            m_over_tot = to_decimal(m_over_tot_in, tipo_str)
            m_under_tot = to_decimal(m_under_tot_in, tipo_str)
            m_rl_loc_minus = to_decimal(m_rl_loc_minus_in, tipo_str)
            m_rl_loc_plus = to_decimal(m_rl_loc_plus_in, tipo_str)
            m_rl_vis_minus = to_decimal(m_rl_vis_minus_in, tipo_str)
            m_rl_vis_plus = to_decimal(m_rl_vis_plus_in, tipo_str)
            m_f5_loc = to_decimal(m_f5_loc_in, tipo_str)
            m_f5_vis = to_decimal(m_f5_vis_in, tipo_str)
            m_f5_over = to_decimal(m_f5_over_in, tipo_str)
            m_f5_under = to_decimal(m_f5_under_in, tipo_str)
            m_k_loc_over = to_decimal(m_k_loc_over_in, tipo_str)
            m_k_loc_under = to_decimal(m_k_loc_under_in, tipo_str)
            m_k_vis_over = to_decimal(m_k_vis_over_in, tipo_str)
            m_k_vis_under = to_decimal(m_k_vis_under_in, tipo_str)
            m_outs_loc_over = to_decimal(m_outs_loc_over_in, tipo_str)
            m_outs_loc_under = to_decimal(m_outs_loc_under_in, tipo_str)
            m_outs_vis_over = to_decimal(m_outs_vis_over_in, tipo_str)
            m_outs_vis_under = to_decimal(m_outs_vis_under_in, tipo_str)
            m_nrfi = to_decimal(m_nrfi_in, tipo_str)
            m_yrfi = to_decimal(m_yrfi_in, tipo_str)

    with col_der:
        st.markdown("""
        <div class="header-big-right">
            <span style="font-size: 38px; margin-right: 12px; line-height:1;">👑</span>
            <span class="header-text-right">VEREDICTO MAÑA PIKS MLB</span>
        </div>
        """, unsafe_allow_html=True)

        prob_ml_loc = np.sum(np.tril(matrix_mlb, -1))
        prob_ml_vis = np.sum(np.triu(matrix_mlb, 1))

        # TOTALES
        tot_target = float(linea_tot_mlb)
        prob_tot_over = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if x + y > tot_target])
        prob_tot_under = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if x + y < tot_target])

        # RUN LINE (+1.5 Y -1.5)
        prob_rl_loc_minus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (x - y) >= 2])
        prob_rl_loc_plus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (x - y) >= -1])
        prob_rl_vis_minus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (y - x) >= 2])
        prob_rl_vis_plus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (y - x) >= -1])

        # K'S OVER Y UNDER
        k_target_loc = float(linea_k_loc)
        k_rate_loc = (k_loc / ip_loc) if ip_loc > 0 else 1.0
        outs_exp_loc_val = 17.5
        lambda_k_loc = k_rate_loc * (outs_exp_loc_val / 3.0)
        prob_k_loc_over = 1.0 - poisson.cdf(int(k_target_loc), lambda_k_loc)
        prob_k_loc_under = poisson.cdf(int(k_target_loc), lambda_k_loc)

        k_target_vis = float(linea_k_vis)
        k_rate_vis = (k_vis / ip_vis) if ip_vis > 0 else 1.0
        outs_exp_vis_val = 16.5
        lambda_k_vis = k_rate_vis * (outs_exp_vis_val / 3.0)
        prob_k_vis_over = 1.0 - poisson.cdf(int(k_target_vis), lambda_k_vis)
        prob_k_vis_under = poisson.cdf(int(k_target_vis), lambda_k_vis)

        # OUTS OVER Y UNDER
        outs_target_loc = float(linea_outs_loc)
        prob_outs_loc_over = 1.0 - poisson.cdf(int(outs_target_loc), outs_exp_loc_val)
        prob_outs_loc_under = poisson.cdf(int(outs_target_loc), outs_exp_loc_val)

        outs_target_vis = float(linea_outs_vis)
        prob_outs_vis_over = 1.0 - poisson.cdf(int(outs_target_vis), outs_exp_vis_val)
        prob_outs_vis_under = poisson.cdf(int(outs_target_vis), outs_exp_vis_val)

        # F5
        prob_f5_loc = np.sum(np.tril(matrix_f5, -1))
        prob_f5_vis = np.sum(np.triu(matrix_f5, 1))
        f5_target = float(linea_f5_sel)
        prob_f5_over = np.sum([matrix_f5[x, y] for x in range(max_c) for y in range(max_c) if x + y > f5_target])
        prob_f5_under = np.sum([matrix_f5[x, y] for x in range(max_c) for y in range(max_c) if x + y < f5_target])

        # 1ER INNING (NRFI / YRFI)
        xr_1st_inn = (xr_local + xr_visita) * 0.13
        prob_nrfi = poisson.pmf(0, xr_1st_inn)
        prob_yrfi = 1.0 - prob_nrfi

        # CÁLCULO DE VALOR ESPERADO (+EV%)
        ev_ml_loc = (prob_ml_loc * m_ml_loc) - 1
        ev_ml_vis = (prob_ml_vis * m_ml_vis) - 1
        ev_tot_over = (prob_tot_over * m_over_tot) - 1
        ev_tot_under = (prob_tot_under * m_under_tot) - 1
        ev_rl_loc_minus = (prob_rl_loc_minus * m_rl_loc_minus) - 1
        ev_rl_loc_plus = (prob_rl_loc_plus * m_rl_loc_plus) - 1
        ev_rl_vis_minus = (prob_rl_vis_minus * m_rl_vis_minus) - 1
        ev_rl_vis_plus = (prob_rl_vis_plus * m_rl_vis_plus) - 1
        ev_f5_loc = (prob_f5_loc * m_f5_loc) - 1
        ev_f5_vis = (prob_f5_vis * m_f5_vis) - 1
        ev_f5_over = (prob_f5_over * m_f5_over) - 1
        ev_f5_under = (prob_f5_under * m_f5_under) - 1
        ev_k_loc_over = (prob_k_loc_over * m_k_loc_over) - 1
        ev_k_loc_under = (prob_k_loc_under * m_k_loc_under) - 1
        ev_k_vis_over = (prob_k_vis_over * m_k_vis_over) - 1
        ev_k_vis_under = (prob_k_vis_under * m_k_vis_under) - 1
        ev_outs_loc_over = (prob_outs_loc_over * m_outs_loc_over) - 1
        ev_outs_loc_under = (prob_outs_loc_under * m_outs_loc_under) - 1
        ev_outs_vis_over = (prob_outs_vis_over * m_outs_vis_over) - 1
        ev_outs_vis_under = (prob_outs_vis_under * m_outs_vis_under) - 1
        ev_nrfi = (prob_nrfi * m_nrfi) - 1
        ev_yrfi = (prob_yrfi * m_yrfi) - 1

        partido_nombre_mlb = f"{local_nombre} vs {visita_nombre}"

        def render_card_mlb_con_tracker(titulo, prob_real, ev, badge, mercado_str, momio_val, linea_val=""):
            momio_justo = 1.0 / prob_real if prob_real > 0 else 99.0
            momio_am = to_american_str(prob_real)
            badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
            c_card1, c_card2 = st.columns([4, 1])
            with c_card1:
                st.markdown(f"""
                <div class="card-pro">
                    {badge_html}
                    <div style="font-weight: 800; font-size: 15px; color: #ffffff;">{titulo}</div>
                    <div class="subtext">
                        Prob. Real: <b>{prob_real*100:.1f}%</b> · Momio Justo: <b>{momio_justo:.3f} ({momio_am})</b> · <b>EV {ev*100:+.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c_card2:
                if st.button("➕ APUESTA", key=f"btn_mlb_{mercado_str}"):
                    registrar_apuesta("MLB", partido_nombre_mlb, local_nombre, visita_nombre, mercado_str, linea_val, momio_val, ev)

        st.markdown("<div class='market-title'>1. Moneyline (Ganador Directo - 9 Innings)</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"Gana {local_nombre} (ML)", prob_ml_loc, ev_ml_loc, "BET" if ev_ml_loc > 0.03 else "SKIP", f"Gana {local_nombre} ML", m_ml_loc, "ML")
        render_card_mlb_con_tracker(f"Gana {visita_nombre} (ML)", prob_ml_vis, ev_ml_vis, "BET" if ev_ml_vis > 0.03 else "SKIP", f"Gana {visita_nombre} ML", m_ml_vis, "ML")

        st.markdown("<div class='market-title'>2. Total de Carreras (Over / Under)</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"Más de {tot_target} Carreras (OVER)", prob_tot_over, ev_tot_over, "BET" if ev_tot_over > 0.03 else "SKIP", f"Over {tot_target} Carreras", m_over_tot, str(tot_target))
        render_card_mlb_con_tracker(f"Menos de {tot_target} Carreras (UNDER)", prob_tot_under, ev_tot_under, "BET" if ev_tot_under > 0.03 else "SKIP", f"Under {tot_target} Carreras", m_under_tot, str(tot_target))

        st.markdown("<div class='market-title'>3. Run Line / Hándicap (+1.5 y -1.5)</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"{local_nombre} Run Line -1.5", prob_rl_loc_minus, ev_rl_loc_minus, "BET" if ev_rl_loc_minus > 0.03 else "SKIP", f"{local_nombre} RL -1.5", m_rl_loc_minus, "-1.5")
        render_card_mlb_con_tracker(f"{local_nombre} Run Line +1.5", prob_rl_loc_plus, ev_rl_loc_plus, "BET" if ev_rl_loc_plus > 0.03 else "SKIP", f"{local_nombre} RL +1.5", m_rl_loc_plus, "+1.5")
        render_card_mlb_con_tracker(f"{visita_nombre} Run Line -1.5", prob_rl_vis_minus, ev_rl_vis_minus, "BET" if ev_rl_vis_minus > 0.03 else "SKIP", f"{visita_nombre} RL -1.5", m_rl_vis_minus, "-1.5")
        render_card_mlb_con_tracker(f"{visita_nombre} Run Line +1.5", prob_rl_vis_plus, ev_rl_vis_plus, "BET" if ev_rl_vis_plus > 0.03 else "SKIP", f"{visita_nombre} RL +1.5", m_rl_vis_plus, "+1.5")

        st.markdown("<div class='market-title'>4. Props de Pitcheo: Ponches (K's)</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"Abridor {local_nombre}: OVER {linea_k_loc} K's", prob_k_loc_over, ev_k_loc_over, "BET" if ev_k_loc_over > 0.03 else "SKIP", f"Abridor {local_nombre[:3]} Over {linea_k_loc} K's", m_k_loc_over, linea_k_loc)
        render_card_mlb_con_tracker(f"Abridor {local_nombre}: UNDER {linea_k_loc} K's", prob_k_loc_under, ev_k_loc_under, "BET" if ev_k_loc_under > 0.03 else "SKIP", f"Abridor {local_nombre[:3]} Under {linea_k_loc} K's", m_k_loc_under, linea_k_loc)
        render_card_mlb_con_tracker(f"Abridor {visita_nombre}: OVER {linea_k_vis} K's", prob_k_vis_over, ev_k_vis_over, "BET" if ev_k_vis_over > 0.03 else "SKIP", f"Abridor {visita_nombre[:3]} Over {linea_k_vis} K's", m_k_vis_over, linea_k_vis)
        render_card_mlb_con_tracker(f"Abridor {visita_nombre}: UNDER {linea_k_vis} K's", prob_k_vis_under, ev_k_vis_under, "BET" if ev_k_vis_under > 0.03 else "SKIP", f"Abridor {visita_nombre[:3]} Under {linea_k_vis} K's", m_k_vis_under, linea_k_vis)

        st.markdown("<div class='market-title'>5. Props de Pitcheo: Outs Registrados</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"Abridor {local_nombre}: OVER {linea_outs_loc} Outs", prob_outs_loc_over, ev_outs_loc_over, "BET" if ev_outs_loc_over > 0.03 else "SKIP", f"Abridor {local_nombre[:3]} Over {linea_outs_loc} Outs", m_outs_loc_over, linea_outs_loc)
        render_card_mlb_con_tracker(f"Abridor {local_nombre}: UNDER {linea_outs_loc} Outs", prob_outs_loc_under, ev_outs_loc_under, "BET" if ev_outs_loc_under > 0.03 else "SKIP", f"Abridor {local_nombre[:3]} Under {linea_outs_loc} Outs", m_outs_loc_under, linea_outs_loc)
        render_card_mlb_con_tracker(f"Abridor {visita_nombre}: OVER {linea_outs_vis} Outs", prob_outs_vis_over, ev_outs_vis_over, "BET" if ev_outs_vis_over > 0.03 else "SKIP", f"Abridor {visita_nombre[:3]} Over {linea_outs_vis} Outs", m_outs_vis_over, linea_outs_vis)
        render_card_mlb_con_tracker(f"Abridor {visita_nombre}: UNDER {linea_outs_vis} Outs", prob_outs_vis_under, ev_outs_vis_under, "BET" if ev_outs_vis_under > 0.03 else "SKIP", f"Abridor {visita_nombre[:3]} Under {linea_outs_vis} Outs", m_outs_vis_under, linea_outs_vis)

        st.markdown("<div class='market-title'>6. Primeras 5 Entradas (F5 ML y Over/Under)</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker(f"F5 Ganador {local_nombre}", prob_f5_loc, ev_f5_loc, "BET" if ev_f5_loc > 0.03 else "SKIP", f"F5 ML {local_nombre}", m_f5_loc, "F5 ML")
        render_card_mlb_con_tracker(f"F5 Ganador {visita_nombre}", prob_f5_vis, ev_f5_vis, "BET" if ev_f5_vis > 0.03 else "SKIP", f"F5 ML {visita_nombre}", m_f5_vis, "F5 ML")
        render_card_mlb_con_tracker(f"F5: OVER {f5_target} Carreras", prob_f5_over, ev_f5_over, "BET" if ev_f5_over > 0.03 else "SKIP", f"F5 Over {f5_target}", m_f5_over, str(f5_target))
        render_card_mlb_con_tracker(f"F5: UNDER {f5_target} Carreras", prob_f5_under, ev_f5_under, "BET" if ev_f5_under > 0.03 else "SKIP", f"F5 Under {f5_target}", m_f5_under, str(f5_target))

        st.markdown("<div class='market-title'>7. Mercado 1er Inning: NRFI / YRFI</div>", unsafe_allow_html=True)
        render_card_mlb_con_tracker("NRFI: 0 Carreras en la 1ra Entrada (UNDER 0.5)", prob_nrfi, ev_nrfi, "BET" if ev_nrfi > 0.03 else "SKIP", "NRFI 1st Inning", m_nrfi, "NRFI")
        render_card_mlb_con_tracker("YRFI: 1+ Carreras en la 1ra Entrada (OVER 0.5)", prob_yrfi, ev_yrfi, "BET" if ev_yrfi > 0.03 else "SKIP", "YRFI 1st Inning", m_yrfi, "YRFI")

# ==========================================
# PANEL INFERIOR: AUTO-TRACKING SEPARADO POR DEPORTE
# ==========================================
st.markdown("<br><hr style='border:1px solid #1e2638;'><br>", unsafe_allow_html=True)
c_head1, c_head2 = st.columns([3, 1])
with c_head1: 
    st.markdown(f"### 📈 TRACKER DE APUESTAS: **{deporte_actual_key.upper()}**")
with c_head2:
    if st.button("🔍 VERIFICAR RESULTADOS EN VIVO", use_container_width=True):
        num_act = auto_verificar_apuestas()
        st.toast(f"Resultados actualizados desde la API ({num_act} cambios)", icon="⚽")

historial = cargar_base_datos()

filtro_dep = st.radio("Filtrar Tracker Por:", ["Pestaña Actual (" + deporte_actual_key + ")", "Sólo Liga MX", "Sólo MLB", "Ver Todo (Global)"], horizontal=True)

if "Pestaña Actual" in filtro_dep:
    historial_filtrado = [x for x in historial if x.get("deporte") == deporte_actual_key]
elif "Liga MX" in filtro_dep:
    historial_filtrado = [x for x in historial if x.get("deporte") == "Liga MX"]
elif "MLB" in filtro_dep:
    historial_filtrado = [x for x in historial if x.get("deporte") == "MLB"]
else:
    historial_filtrado = historial

if len(historial_filtrado) == 0:
    st.info(f"💡 No hay apuestas registradas para {filtro_dep}. Selecciona un partido arriba y presiona `➕ APUESTA` para comenzar la contabilización.")
else:
    df = pd.DataFrame(historial_filtrado)
    wins = len(df[df["estado"] == "WIN"])
    losses = len(df[df["estado"] == "LOSS"])
    pending = len(df[df["estado"] == "PENDING"])
    totales_resueltas = wins + losses
    win_rate = (wins / totales_resueltas * 100) if totales_resueltas > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Picks Guardados", len(df))
    m2.metric("Efectividad (Win Rate)", f"{win_rate:.1f}%", f"{wins} Ganadas - {losses} Perdidas")
    m3.metric("En Espera (Pendientes)", pending)
    m4.metric("Estatus Deporte", f"🟢 Filtrado: {filtro_dep}")

    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Ganadas (WIN)', 'Perdidas (LOSS)', 'Pendientes (PENDING)'],
            values=[wins, losses, pending],
            hole=.5,
            marker=dict(colors=['#10b981', '#ef4444', '#64748b'])
        )])
        fig_pie.update_layout(
            title=f"Gráfica de Aciertos ({filtro_dep})", 
            height=250, 
            paper_bgcolor='#121721', 
            font=dict(color='#ffffff')
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown(f"**Historial Registrado ({filtro_dep}):**")
        st.dataframe(df[["fecha", "deporte", "partido", "mercado", "momio", "resultado_real", "estado"]], use_container_width=True)
