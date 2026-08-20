import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página con Sidebar visible por defecto
st.set_page_config(
    page_title="LA MAÑA PICKS - PANEL DE APUESTAS",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚽"
)

# ESTILOS CSS CLAROS / ANALÍTICOS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f4f2 !important;
        color: #1a2b22 !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    header {visibility: hidden;}

    .brand-title-top {
        font-size: 2.8rem;
        font-weight: 900;
        color: #0b4f30 !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 20px;
    }

    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #d8e4df;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 15px;
    }
    .kpi-header {
        font-size: 0.78rem;
        font-weight: 800;
        color: #537065;
        text-transform: uppercase;
    }
    .kpi-metric-main {
        font-size: 1.1rem;
        font-weight: 900;
        color: #0b4f30;
        text-align: center;
        margin-top: 8px;
    }

    .match-row-card {
        background-color: #ffffff;
        border: 1px solid #e1ebe6;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }

    .dot-form-container {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    .dot-g { width: 10px; height: 10px; border-radius: 50%; background-color: #10b981; }
    .dot-e { width: 10px; height: 10px; border-radius: 50%; background-color: #f59e0b; }
    .dot-p { width: 10px; height: 10px; border-radius: 50%; background-color: #ef4444; }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #10b981 !important;
        border-radius: 6px !important;
        color: #0b4f30 !important;
        font-weight: 800 !important;
    }

    .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid #10b981 !important;
        border-radius: 5px !important;
        color: #0b4f30 !important;
        font-weight: 800 !important;
    }

    .stButton>button {
        background-color: #059669 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        width: 100% !important;
        text-transform: uppercase !important;
    }
    .stButton>button:hover {
        background-color: #047857 !important;
    }
</style>
""", unsafe_allow_html=True)

# 1. BASE DE DATOS EXACTA 20 EQUIPOS PREMIER LEAGUE
PREMIER_LEAGUE_DATA = {
    "Bournemouth": {"logo": "https://crests.football-data.org/1044.png", "xg": 1.40, "xga": 1.55, "ppda": 10.5, "aereos": 48, "corners": 4.9, "tarjetas": 2.3, "forma": ["P","E","G","P","P","G","E","P","G","E"], "l10_corners": [4, 5, 6, 4, 3, 5, 6, 4, 5, 4]},
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4, "forma": ["G","G","E","G","G","P","G","G","E","G"], "l10_corners": [7, 8, 6, 9, 5, 8, 10, 6, 4, 7]},
    "Aston Villa": {"logo": "https://crests.football-data.org/58.png", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1, "forma": ["G","P","G","E","G","P","G","E","G","P"], "l10_corners": [5, 6, 4, 7, 5, 6, 8, 5, 4, 6]},
    "Brentford": {"logo": "https://crests.football-data.org/402.png", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6, "tarjetas": 1.8, "forma": ["G","P","E","P","G","E","P","G","P","G"], "l10_corners": [3, 5, 8, 6, 8, 6, 10, 8, 4, 4]},
    "Brighton": {"logo": "https://crests.football-data.org/397.png", "xg": 1.65, "xga": 1.40, "ppda": 9.5, "aereos": 47, "corners": 5.8, "tarjetas": 2.0, "forma": ["E","G","P","G","E","P","G","G","P","E"], "l10_corners": [6, 5, 7, 6, 5, 8, 6, 7, 5, 6]},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6, "forma": ["G","G","P","E","G","G","P","E","G","G"], "l10_corners": [6, 7, 5, 8, 6, 9, 4, 7, 5, 6]},
    "Coventry City": {"logo": "https://crests.football-data.org/1070.png", "xg": 1.30, "xga": 1.50, "ppda": 11.5, "aereos": 50, "corners": 4.8, "tarjetas": 1.9, "forma": ["G","E","P","G","E","P","G","P","E","G"], "l10_corners": [5, 4, 6, 5, 4, 6, 5, 4, 5, 4]},
    "Crystal Palace": {"logo": "https://crests.football-data.org/354.png", "xg": 1.35, "xga": 1.30, "ppda": 11.8, "aereos": 53, "corners": 4.8, "tarjetas": 2.2, "forma": ["E","P","G","E","P","P","G","E","P","G"], "l10_corners": [4, 5, 4, 6, 3, 5, 6, 4, 5, 4]},
    "Everton": {"logo": "https://crests.football-data.org/62.png", "xg": 1.30, "xga": 1.40, "ppda": 12.5, "aereos": 58, "corners": 4.7, "tarjetas": 2.1, "forma": ["P","E","E","G","P","E","P","G","E","P"], "l10_corners": [5, 4, 6, 3, 5, 4, 6, 5, 4, 5]},
    "Fulham": {"logo": "https://crests.football-data.org/63.png", "xg": 1.40, "xga": 1.50, "ppda": 11.0, "aereos": 50, "corners": 5.1, "tarjetas": 2.0, "forma": ["G","P","E","G","P","G","E","P","P","G"], "l10_corners": [5, 6, 4, 5, 6, 5, 7, 4, 5, 6]},
    "Hull City": {"logo": "https://crests.football-data.org/322.png", "xg": 1.22, "xga": 1.58, "ppda": 12.0, "aereos": 47, "corners": 4.3, "tarjetas": 1.7, "forma": ["P","E","P","G","E","P","P","E","G","P"], "l10_corners": [4, 3, 5, 4, 5, 3, 4, 5, 3, 4]},
    "Ipswich Town": {"logo": "https://crests.football-data.org/349.png", "xg": 1.20, "xga": 1.60, "ppda": 13.0, "aereos": 48, "corners": 4.2, "tarjetas": 2.4, "forma": ["P","P","E","P","E","G","P","P","E","P"], "l10_corners": [4, 3, 5, 4, 3, 6, 4, 3, 5, 4]},
    "Leeds": {"logo": "https://crests.football-data.org/341.png", "xg": 1.45, "xga": 1.40, "ppda": 9.2, "aereos": 51, "corners": 5.5, "tarjetas": 2.1, "forma": ["G","E","G","P","E","G","P","G","E","P"], "l10_corners": [6, 5, 7, 5, 6, 4, 6, 7, 5, 6]},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5, "forma": ["G","G","G","E","G","G","P","G","G","E"], "l10_corners": [8, 9, 7, 10, 6, 8, 11, 7, 5, 8]},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3, "forma": ["G","G","E","G","G","G","P","G","E","G"], "l10_corners": [9, 8, 10, 7, 11, 8, 6, 9, 7, 10]},
    "Manchester United": {"logo": "https://crests.football-data.org/66.png", "xg": 1.60, "xga": 1.45, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2, "forma": ["P","G","E","P","G","E","P","G","P","E"], "l10_corners": [6, 5, 7, 6, 8, 5, 6, 7, 5, 6]},
    "Newcastle": {"logo": "https://crests.football-data.org/67.png", "xg": 1.70, "xga": 1.20, "ppda": 9.9, "aereos": 53, "corners": 6.1, "tarjetas": 1.9, "forma": ["G","P","G","E","G","P","G","G","E","P"], "l10_corners": [7, 6, 8, 5, 7, 6, 7, 6, 5, 7]},
    "Nottingham Forest": {"logo": "https://crests.football-data.org/351.png", "xg": 1.25, "xga": 1.50, "ppda": 13.2, "aereos": 51, "corners": 4.1, "tarjetas": 2.3, "forma": ["E","G","P","G","E","P","G","P","E","P"], "l10_corners": [4, 3, 5, 4, 4, 5, 3, 4, 3, 5]},
    "Sunderland": {"logo": "https://crests.football-data.org/71.png", "xg": 1.28, "xga": 1.52, "ppda": 12.2, "aereos": 50, "corners": 4.4, "tarjetas": 2.0, "forma": ["G","P","E","P","G","P","E","P","G","E"], "l10_corners": [4, 5, 4, 6, 3, 5, 4, 5, 3, 4]},
    "Tottenham": {"logo": "https://crests.football-data.org/73.png", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49, "corners": 6.3, "tarjetas": 2.1, "forma": ["G","P","G","G","E","P","G","P","G","E"], "l10_corners": [5, 7, 8, 6, 9, 5, 7, 8, 4, 6]}
}

# 2. BASE DE DATOS EXACTA 20 EQUIPOS LALIGA
LALIGA_DATA = {
    "Deportivo Alavés": {"logo": "https://crests.football-data.org/263.png", "xg": 1.25, "xga": 1.45, "ppda": 12.0, "aereos": 56, "corners": 4.4, "tarjetas": 2.5, "forma": ["P","E","G","P","P","E","G","P","P","G"], "l10_corners": [4, 5, 4, 5, 4, 5, 4, 5, 3, 4]},
    "Espanyol": {"logo": "https://crests.football-data.org/80.png", "xg": 1.15, "xga": 1.60, "ppda": 13.0, "aereos": 48, "corners": 4.1, "tarjetas": 2.6, "forma": ["P","P","E","P","G","P","P","E","P","P"], "l10_corners": [3, 4, 5, 3, 4, 5, 3, 4, 3, 4]},
    "Sevilla": {"logo": "https://crests.football-data.org/559.png", "xg": 1.45, "xga": 1.40, "ppda": 10.5, "aereos": 51, "corners": 5.3, "tarjetas": 2.7, "forma": ["P","G","E","P","G","P","E","G","P","E"], "l10_corners": [5, 6, 4, 6, 5, 6, 5, 6, 4, 5]},
    "Deportivo La Coruña": {"logo": "https://crests.football-data.org/560.png", "xg": 1.20, "xga": 1.45, "ppda": 11.8, "aereos": 49, "corners": 4.2, "tarjetas": 2.2, "forma": ["G","P","E","P","G","E","P","G","E","P"], "l10_corners": [4, 3, 5, 4, 3, 5, 4, 3, 4, 5]},
    "Elche CF": {"logo": "https://crests.football-data.org/285.png", "xg": 1.18, "xga": 1.50, "ppda": 12.4, "aereos": 47, "corners": 4.0, "tarjetas": 2.3, "forma": ["P","E","P","E","G","P","P","E","P","G"], "l10_corners": [3, 4, 3, 5, 4, 3, 4, 3, 4, 3]},
    "Racing Santander": {"logo": "https://crests.football-data.org/457.png", "xg": 1.22, "xga": 1.40, "ppda": 11.2, "aereos": 50, "corners": 4.5, "tarjetas": 2.1, "forma": ["G","G","P","E","G","P","G","E","P","G"], "l10_corners": [5, 4, 6, 4, 5, 4, 5, 4, 3, 5]},
    "Villarreal": {"logo": "https://crests.football-data.org/102.png", "xg": 1.80, "xga": 1.50, "ppda": 10.0, "aereos": 49, "corners": 5.6, "tarjetas": 2.2, "forma": ["G","P","G","G","E","P","G","E","G","P"], "l10_corners": [6, 5, 7, 6, 6, 7, 5, 6, 5, 7]},
    "Athletic": {"logo": "https://crests.football-data.org/77.png", "xg": 1.60, "xga": 1.10, "ppda": 9.0, "aereos": 54, "corners": 5.9, "tarjetas": 2.0, "forma": ["G","E","G","G","P","G","E","G","G","P"], "l10_corners": [6, 5, 7, 6, 5, 8, 6, 7, 5, 6]},
    "Atlético de Madrid": {"logo": "https://crests.football-data.org/78.png", "xg": 1.85, "xga": 0.90, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4, "forma": ["G","G","P","G","E","G","G","E","G","G"], "l10_corners": [6, 7, 5, 8, 6, 7, 5, 8, 6, 7]},
    "Osasuna": {"logo": "https://crests.football-data.org/79.png", "xg": 1.35, "xga": 1.35, "ppda": 11.5, "aereos": 53, "corners": 4.7, "tarjetas": 2.3, "forma": ["E","G","P","G","E","P","G","E","P","G"], "l10_corners": [5, 4, 6, 4, 5, 4, 6, 5, 4, 5]},
    "Celta de Vigo": {"logo": "https://crests.football-data.org/558.png", "xg": 1.40, "xga": 1.45, "ppda": 10.8, "aereos": 47, "corners": 4.8, "tarjetas": 2.1, "forma": ["P","G","E","P","G","E","P","G","P","E"], "l10_corners": [4, 5, 6, 4, 5, 4, 6, 5, 4, 5]},
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg": 2.30, "xga": 0.95, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9, "forma": ["G","G","G","G","P","G","G","E","G","G"], "l10_corners": [7, 8, 6, 9, 7, 8, 10, 6, 5, 8]},
    "Málaga": {"logo": "https://crests.football-data.org/84.png", "xg": 1.25, "xga": 1.42, "ppda": 11.6, "aereos": 48, "corners": 4.3, "tarjetas": 2.2, "forma": ["P","E","G","P","E","P","G","P","E","G"], "l10_corners": [4, 3, 5, 4, 5, 3, 4, 5, 3, 4]},
    "Betis": {"logo": "https://crests.football-data.org/90.png", "xg": 1.50, "xga": 1.30, "ppda": 11.0, "aereos": 49, "corners": 5.2, "tarjetas": 2.4, "forma": ["E","G","P","E","G","P","G","E","G","P"], "l10_corners": [5, 6, 4, 5, 6, 5, 7, 4, 5, 6]},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg": 2.35, "xga": 0.80, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6, "forma": ["G","G","G","E","G","G","P","G","G","G"], "l10_corners": [8, 9, 7, 10, 8, 9, 11, 7, 6, 8]},
    "Real Sociedad": {"logo": "https://crests.football-data.org/92.png", "xg": 1.65, "xga": 1.15, "ppda": 9.1, "aereos": 52, "corners": 5.7, "tarjetas": 2.0, "forma": ["G","P","E","G","P","G","E","G","P","G"], "l10_corners": [6, 5, 7, 6, 5, 8, 6, 7, 5, 6]},
    "Valencia CF": {"logo": "https://crests.football-data.org/95.png", "xg": 1.25, "xga": 1.45, "ppda": 11.8, "aereos": 50, "corners": 4.6, "tarjetas": 2.5, "forma": ["P","P","E","G","P","E","P","G","P","E"], "l10_corners": [4, 5, 4, 5, 3, 5, 4, 5, 3, 4]},
    "Rayo Vallecano": {"logo": "https://crests.football-data.org/87.png", "xg": 1.30, "xga": 1.40, "ppda": 9.4, "aereos": 48, "corners": 5.0, "tarjetas": 2.6, "forma": ["P","E","G","E","P","G","E","P","P","G"], "l10_corners": [5, 6, 4, 5, 6, 5, 6, 4, 5, 6]},
    "Getafe": {"logo": "https://crests.football-data.org/82.png", "xg": 1.10, "xga": 1.20, "ppda": 12.8, "aereos": 58, "corners": 4.0, "tarjetas": 3.1, "forma": ["E","E","P","G","E","P","E","P","G","E"], "l10_corners": [4, 3, 5, 4, 3, 5, 4, 3, 4, 5]},
    "Levante": {"logo": "https://crests.football-data.org/88.png", "xg": 1.22, "xga": 1.55, "ppda": 12.1, "aereos": 49, "corners": 4.2, "tarjetas": 2.4, "forma": ["P","G","P","E","P","G","E","P","P","E"], "l10_corners": [3, 4, 5, 3, 4, 3, 5, 4, 3, 4]}
}

ARBITROS = {
    "Chris Kavanagh": 3.9,
    "Anthony Taylor": 4.2,
    "Michael Oliver": 3.6,
    "Ricardo De Burgos": 4.1
}

def parse_odds_to_decimal(val_str, format_type):
    try:
        val = float(val_str)
        if format_type == "Decimales": return val
        return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def calcular_ev(prob, cuota_decimal):
    return (prob * cuota_decimal) - 1.0

def clasificar_opcion(prob, ev):
    prob_pct = prob * 100.0
    if prob_pct >= 75.0:
        return ("💎 APUESTA ESTRELLA", "card-star", "badge-star") if ev > 0.0 else ("HIGH CONFIDENCE", "card-high", "badge-high")
    elif 60.0 <= prob_pct < 75.0:
        return "MEDIUM PROBABILITY", "card-medium", "badge-medium"
    return "LOW PROBABILITY", "card-low", "badge-low"

def render_dots_forma(forma_list):
    html = '<div class="dot-form-container">'
    for res in forma_list[-5:]:
        cls = "dot-g" if res == "G" else ("dot-e" if res == "E" else "dot-p")
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

# ==============================================================================
# SIDEBAR IZQUIERDA: SELECCIÓN DE COMPETICIÓN
# ==============================================================================
st.sidebar.markdown("<h3 style='color:#0b4f30; font-size:1.0rem; font-weight:900;'>🏆 NAVEGACIÓN DE COMPETICIÓN</h3>", unsafe_allow_html=True)

competicion = st.sidebar.radio(
    "Selecciona la Liga a Analizar:",
    ["⚽ Premier League (Inglaterra)", "🔴 LaLiga EA Sports (España)"],
    index=0
)

if "Premier League" in competicion:
    TEAMS_DATA = PREMIER_LEAGUE_DATA
    nombre_liga = "PREMIER LEAGUE"
else:
    TEAMS_DATA = LALIGA_DATA
    nombre_liga = "LALIGA EA SPORTS"

# ==============================================================================
# ENCABEZADO
# ==============================================================================
st.markdown("<h1 class='brand-title-top'>LA MAÑA PICKS - PANEL DE APUESTAS</h1>", unsafe_allow_html=True)

# ==============================================================================
# ENCUENTRO SELECCIONADO
# ==============================================================================
st.markdown(f"<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900;'>⚡ ENCUENTRO SELECCIONADO ({nombre_liga})</h3>", unsafe_allow_html=True)

col_local, col_visita, col_referee = st.columns([3, 3, 2])

with col_local:
    equipo_loc = st.selectbox("Equipo Local:", list(TEAMS_DATA.keys()), index=0, key="select_local")
with col_visita:
    equipo_vis = st.selectbox("Equipo Visitante:", list(TEAMS_DATA.keys()), index=1 if len(TEAMS_DATA) > 1 else 0, key="select_visita")
with col_referee:
    arbitro_sel = st.selectbox("Árbitro Asignado:", list(ARBITROS.keys()), index=0, key="select_arbitro")

d_loc = TEAMS_DATA[equipo_loc]
d_vis = TEAMS_DATA[equipo_vis]

# TARJETAS KPI DINÁMICAS
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">⚽ MAYOR MEDIA GOLEADORA</div>
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:8px;">
            <img src="{d_loc['logo']}" width="30">
            <span style="font-weight:800; font-size:0.8rem;">VS</span>
            <img src="{d_vis['logo']}" width="30">
        </div>
        <div class="kpi-metric-main">{(d_loc['xg'] + d_vis['xg']):.2f} xG / partido</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📈 TENDENCIA MÁS FUERTE</div>
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:8px;">
            <img src="{d_loc['logo']}" width="30">
            <span style="font-weight:800; font-size:0.8rem;">{equipo_loc}</span>
        </div>
        <div class="kpi-metric-main">+{d_loc['corners']} Córners L10</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">🟨 RIESGO DE TARJETAS</div>
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:8px;">
            <span style="font-weight:800; font-size:0.8rem;">{arbitro_sel}</span>
        </div>
        <div class="kpi-metric-main">{ARBITROS[arbitro_sel]} amarillas / partido</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">⭐ IMPACTO DE PRESIÓN</div>
        <div style="display:flex; justify-content:space-around; align-items:center; margin-top:8px;">
            <span style="font-weight:800; font-size:0.85rem;">{equipo_loc}</span>
        </div>
        <div class="kpi-metric-main">{d_loc['ppda']} PPDA (Intensidad)</div>
    </div>
    """, unsafe_allow_html=True)

# FILA DESGLOSE DE ENCUENTRO CON LOGOS ORIGINALES
st.markdown(f"""
<div class="match-row-card">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #edf4f0; padding-bottom:10px; margin-bottom:10px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <img src="{d_loc['logo']}" width="35">
            <span style="font-weight:900; font-size:1.1rem; color:#0b4f30;">{equipo_loc}</span>
        </div>
        <div style="font-weight:900; font-size:1rem; color:#059669;">VS</div>
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-weight:900; font-size:1.1rem; color:#0b4f30;">{equipo_vis}</span>
            <img src="{d_vis['logo']}" width="35">
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; text-align:center;">
        <div><b>Forma:</b> {render_dots_forma(d_loc['forma'])}</div>
        <div><b>xG / xGA:</b> {d_loc['xg']} / {d_loc['xga']}</div>
        <div><b>Córners L10:</b> {d_loc['corners']}</div>
        <div><b>Tarjetas:</b> {d_loc['tarjetas']}</div>
        <div><b>Árbitro Promedio:</b> <span style="background-color:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; font-weight:800;">🟨 {ARBITROS[arbitro_sel]}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# CAPTURA DE MOMIOS REALES DE TU CASA DE APUESTAS
# ==============================================================================
st.markdown("<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900; margin-top:15px;'>🎲 INGRESA LOS MOMIOS DE TU CASA DE APUESTAS</h3>", unsafe_allow_html=True)

col_fm, col_m1, col_m2, col_m3 = st.columns([2, 2, 2, 2])

with col_fm:
    tipo_momio = st.radio("Formato de Cuota:", ["Decimales", "Americanos"], horizontal=True, key="format_odds")

# CÁLCULOS MATEMÁTICOS DE POISSON
lambda_h = d_loc['xg']
lambda_a = d_vis['xg']
prob_over25 = 1.0 - poisson.cdf(2, lambda_h + lambda_a)
prob_btts = 0.68
prob_corners = 0.76

with col_m1:
    cuota_corners_str = st.text_input("Cuota Córners > 9.5:", value="1.85", key="odd_c")
with col_m2:
    cuota_btts_str = st.text_input("Cuota BTTS (Sí):", value="1.72", key="odd_b")
with col_m3:
    cuota_goles_str = st.text_input("Cuota Over 2.5 Goles:", value="1.90", key="odd_g")

c_corners_dec = parse_odds_to_decimal(cuota_corners_str, tipo_momio)
c_btts_dec = parse_odds_to_decimal(cuota_btts_str, tipo_momio)
c_goles_dec = parse_odds_to_decimal(cuota_goles_str, tipo_momio)

# ==============================================================================
# TABLA DE OPORTUNIDADES CON CÁLCULO DE VALOR ESPERADO (EV)
# ==============================================================================
st.markdown("<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900; margin-top:15px;'>📊 MEJORES OPORTUNIDADES Y VALOR ESPERADO (EV)</h3>", unsafe_allow_html=True)

oportunidades = [
    {"id": "op_corners", "mercado": f"Córners Totales > 9.5 ({equipo_loc})", "prob": prob_corners, "cuota": c_corners_dec},
    {"id": "op_btts", "mercado": "Ambos Equipos Anotan (BTTS SÍ)", "prob": prob_btts, "cuota": c_btts_dec},
    {"id": "op_goles", "mercado": "Total de Goles Over 2.5", "prob": prob_over25, "cuota": c_goles_dec}
]

for op in oportunidades:
    ev = calcular_ev(op['prob'], op['cuota'])
    badge_label, _, _ = clasificar_opcion(op['prob'], ev)
    cuota_minima = 1.0 / op['prob'] if op['prob'] > 0 else 2.0
    
    st.markdown(f"""
    <div style="background-color:#ffffff; border:1px solid #d1e2da; border-radius:8px; padding:12px 18px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="font-weight:900; font-size:0.95rem; color:#0b4f30;">↗ {op['mercado']}</span>
            <div style="font-size:0.78rem; color:#607d71;">
                Probabilidad: <b>{op['prob']*100:.1f}%</b> | Cuota Tuya: <b>@{op['cuota']:.2f}</b> | EV: <b style="color:{'#059669' if ev > 0 else '#dc2626'};">{ev*100:+.1f}%</b> | Cuota Mínima Sugerida: <b>@{cuota_minima:.2f}</b>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:15px;">
            <span style="background-color:{'#059669' if ev > 0 else '#d97706'}; color:#ffffff; padding:4px 10px; border-radius:4px; font-weight:900; font-size:0.75rem;">{badge_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📈 Ver Análisis Estadístico para {op['mercado']}"):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"P{i+1}" for i in range(10)],
            y=d_loc['l10_corners'],
            marker_color="#10b981"
        ))
        fig.update_layout(
            title=f"Desglose Histórico L10 Partidos - {op['mercado']}",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=160,
            margin=dict(l=10, r=10, t=25, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{nombre_liga}_{op['id']}_{equipo_loc}_{equipo_vis}")
