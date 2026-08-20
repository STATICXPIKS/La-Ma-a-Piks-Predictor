import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="LA MAÑA PICKS - PANEL DE APUESTAS",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚽"
)

# ESTILOS CSS CLAROS ANALÍTICOS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f4f2 !important;
        color: #1a2b22 !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    header {visibility: hidden;}

    .brand-title-top {
        font-size: 2.5rem;
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
    .kpi-header { font-size: 0.78rem; font-weight: 800; color: #537065; text-transform: uppercase; }
    .kpi-metric-main { font-size: 1.1rem; font-weight: 900; color: #0b4f30; text-align: center; margin-top: 8px; }

    .match-row-card {
        background-color: #ffffff;
        border: 1px solid #e1ebe6;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }

    .dot-form-container { display: flex; gap: 4px; align-items: center; }
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
    .stButton>button:hover { background-color: #047857 !important; }
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

ARBITROS = {"Chris Kavanagh": 3.9, "Anthony Taylor": 4.2, "Michael Oliver": 3.6, "Ricardo De Burgos": 4.1}

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

def generar_matriz(lambda_h, lambda_a, max_goles=8):
    mat = np.zeros((max_goles, max_goles))
    for h in range(max_goles):
        for a in range(max_goles):
            mat[h, a] = poisson.pmf(h, lambda_h) * poisson.pmf(a, lambda_a)
    return mat / np.sum(mat)

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

st.markdown("<h1 class='brand-title-top'>LA MAÑA PICKS - PANEL DE APUESTAS</h1>", unsafe_allow_html=True)

# ==============================================================================
# DISPOSICIÓN PRINCIPAL EN DOS COLUMNAS PARALELAS (50/50)
# ==============================================================================
col_panel_izq, col_panel_der = st.columns([1, 1])

# ------------------------------------------------------------------------------
# COLUMNA IZQUIERDA: CONFIGURACIÓN + CAPTURA COMPLETA DE MOMIOS
# ------------------------------------------------------------------------------
with col_panel_izq:
    st.markdown(f"<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900;'>⚙️ CONFIGURACIÓN Y MOMIOS ({nombre_liga})</h3>", unsafe_allow_html=True)

    col_loc, col_vis = st.columns(2)
    with col_loc: equipo_loc = st.selectbox("Equipo Local:", list(TEAMS_DATA.keys()), index=0, key="select_local")
    with col_vis: equipo_vis = st.selectbox("Equipo Visitante:", list(TEAMS_DATA.keys()), index=1 if len(TEAMS_DATA) > 1 else 0, key="select_visita")
    arbitro_sel = st.selectbox("Árbitro Asignado:", list(ARBITROS.keys()), index=0, key="select_arbitro")

    d_loc, d_vis = TEAMS_DATA[equipo_loc], TEAMS_DATA[equipo_vis]

    st.markdown(f"""
    <div class="match-row-card">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #edf4f0; padding-bottom:8px; margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <img src="{d_loc['logo']}" width="28">
                <span style="font-weight:900; font-size:0.95rem; color:#0b4f30;">{equipo_loc}</span>
            </div>
            <div style="font-weight:900; font-size:0.9rem; color:#059669;">VS</div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:900; font-size:0.95rem; color:#0b4f30;">{equipo_vis}</span>
                <img src="{d_vis['logo']}" width="28">
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; text-align:center; font-size:0.8rem;">
            <div><b>Forma:</b> {render_dots_forma(d_loc['forma'])}</div>
            <div><b>xG:</b> {d_loc['xg']} / {d_vis['xg']}</div>
            <div><b>Córners:</b> {d_loc['corners']}</div>
            <div><b>Árbitro:</b> 🟨 {ARBITROS[arbitro_sel]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color:#0b4f30; font-size:0.95rem; font-weight:900;'>🎲 CAPTURA DE MOMIOS REALES</h4>", unsafe_allow_html=True)
    tipo_momio = st.radio("Formato Cuotas:", ["Decimales", "Americanos"], horizontal=True, key="odds_fmt")

    # Mercados 1 y 2
    m1_1, m1_x, m1_2 = st.columns(3)
    with m1_1: c_1x2_1 = st.text_input(f"1X2 {equipo_loc[:3]}", value="2.10")
    with m1_x: c_1x2_x = st.text_input("1X2 Empate", value="3.40")
    with m1_2: c_1x2_2 = st.text_input(f"1X2 {equipo_vis[:3]}", value="3.50")

    m2_1x, m2_x2, m2_12 = st.columns(3)
    with m2_1x: c_dc_1x = st.text_input("DC 1X", value="1.30")
    with m2_x2: c_dc_x2 = st.text_input("DC X2", value="1.70")
    with m2_12: c_dc_12 = st.text_input("DC 12", value="1.32")

    # Mercado 3: Total Goles
    mg1, mg2, mg3 = st.columns([1.5, 1.25, 1.25])
    with mg1: line_goles = st.slider("Línea Goles FT", 1.5, 4.5, 2.5, step=1.0, key="sl_g")
    with mg2: c_over_g = st.text_input(f"Over {line_goles}", value="1.90")
    with mg3: c_under_g = st.text_input(f"Under {line_goles}", value="1.90")

    # Mercado 4 y 5: BTTS & Córners
    mb1, mb2, mc1, mc2, mc3 = st.columns([1, 1, 1.2, 1, 1])
    with mb1: c_btts_si = st.text_input("BTTS SÍ", value="1.75")
    with mb2: c_btts_no = st.text_input("BTTS NO", value="2.05")
    with mc1: line_corners = st.slider("Línea Córners", 8.5, 12.5, 9.5, step=1.0, key="sl_c")
    with mc2: c_over_c = st.text_input(f"Córners > {line_corners}", value="1.85")
    with mc3: c_under_c = st.text_input(f"Córners < {line_corners}", value="1.85")

    # Mercado 6: Hándicap Asiático
    ha1, ha2, ha3 = st.columns([1.5, 1.25, 1.25])
    with ha1: line_ha = st.selectbox("Hándicap AH", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=0)
    with ha2: c_ha_loc = st.text_input(f"AH {equipo_loc[:3]}", value="1.80")
    with ha3: c_ha_vis = st.text_input(f"AH {equipo_vis[:3]}", value="2.00")

    # Mercado 7 y 8: 1ra Mitad
    mh1, mh2, mh3 = st.columns(3)
    with mh1: c_ht_1 = st.text_input(f"HT {equipo_loc[:3]}", value="2.70")
    with mh2: c_ht_x = st.text_input("HT Empate", value="2.10")
    with mh3: c_ht_2 = st.text_input(f"HT {equipo_vis[:3]}", value="4.00")

    mh4, mh5, mh6 = st.columns([1.5, 1.25, 1.25])
    with mh4: line_ht_g = st.selectbox("Línea Goles HT", ["0.5", "1.5"], index=0)
    with mh5: c_ht_over_g = st.text_input(f"HT Over {line_ht_g}", value="1.40")
    with mh6: c_ht_under_g = st.text_input(f"HT Under {line_ht_g}", value="2.70")

    # Mercado 9 y 10: DNB & Gana Cualquier Mitad
    md1, md2, mw1, mw2 = st.columns(4)
    with md1: c_dnb_loc = st.text_input(f"DNB {equipo_loc[:3]}", value="1.50")
    with md2: c_dnb_vis = st.text_input(f"DNB {equipo_vis[:3]}", value="2.50")
    with mw1: c_winhalf_loc = st.text_input(f"Gana Mitad {equipo_loc[:3]}", value="1.60")
    with mw2: c_winhalf_vis = st.text_input(f"Gana Mitad {equipo_vis[:3]}", value="2.20")

# ------------------------------------------------------------------------------
# COLUMNA DERECHA: ANÁLISIS MATRIX Y EVALUACIÓN DE OPORTUNIDADES (EV)
# ------------------------------------------------------------------------------
with col_panel_der:
    st.markdown("<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900;'>📊 ANÁLISIS MATRIX Y EV DETECTADOS</h3>", unsafe_allow_html=True)

    # CÁLCULOS MATEMÁTICOS DE POISSON
    lam_h, lam_a = d_loc['xg'], d_vis['xg']
    matriz_ft = generar_matriz(lam_h, lam_a)
    p_1_ft = float(np.sum(np.tril(matriz_ft, -1)))
    p_x_ft = float(np.sum(np.diag(matriz_ft)))
    p_2_ft = float(np.sum(np.triu(matriz_ft, 1)))

    lam_h_ht, lam_a_ht = lam_h * 0.45, lam_a * 0.45
    matriz_ht = generar_matriz(lam_h_ht, lam_a_ht)
    p_1_ht = float(np.sum(np.tril(matriz_ht, -1)))

    p_under_goles = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h + a < line_goles))
    p_over_goles = 1.0 - p_under_goles
    p_btts_si = float(sum(matriz_ft[h, a] for h in range(1, 8) for a in range(1, 8)))
    p_btts_no = 1.0 - p_btts_si

    exp_corners_ft = d_loc["corners"] + d_vis["corners"]
    p_under_corners = float(poisson.cdf(int(line_corners), exp_corners_ft))
    p_over_corners = 1.0 - p_under_corners

    p_ht_over05 = 1.0 - (poisson.pmf(0, lam_h_ht) * poisson.pmf(0, lam_a_ht))
    p_ht_under05 = 1.0 - p_ht_over05
    p_ht_under15 = float(sum(matriz_ht[h, a] for h in range(8) for a in range(8) if h + a < 1.5))
    p_ht_over15 = 1.0 - p_ht_under15
    p_ht_over_g = p_ht_over05 if line_ht_g == "0.5" else p_ht_over15
    p_ht_under_g = 1.0 - p_ht_over_g

    p_dnb_loc = p_1_ft / (p_1_ft + p_2_ft) if (p_1_ft + p_2_ft) > 0 else 0.5
    p_winhalf_loc = 1.0 - ((1.0 - p_1_ht) * (1.0 - p_1_ft))

    mercados_list = [
        {"mercado": f"1. Resultado (1X2): Gana {equipo_loc}", "prob": p_1_ft, "cuota": parse_odds_to_decimal(c_1x2_1, tipo_momio)},
        {"mercado": f"1. Resultado (1X2): Empate", "prob": p_x_ft, "cuota": parse_odds_to_decimal(c_1x2_x, tipo_momio)},
        {"mercado": f"1. Resultado (1X2): Gana {equipo_vis}", "prob": p_2_ft, "cuota": parse_odds_to_decimal(c_1x2_2, tipo_momio)},
        {"mercado": "2. Doble Oportunidad: 1X", "prob": p_1_ft + p_x_ft, "cuota": parse_odds_to_decimal(c_dc_1x, tipo_momio)},
        {"mercado": "2. Doble Oportunidad: X2", "prob": p_2_ft + p_x_ft, "cuota": parse_odds_to_decimal(c_dc_x2, tipo_momio)},
        {"mercado": f"3. Total Goles: Over {line_goles}", "prob": p_over_goles, "cuota": parse_odds_to_decimal(c_over_g, tipo_momio)},
        {"mercado": f"3. Total Goles: Under {line_goles}", "prob": p_under_goles, "cuota": parse_odds_to_decimal(c_under_g, tipo_momio)},
        {"mercado": "4. Ambos Equipos Anotan: SÍ", "prob": p_btts_si, "cuota": parse_odds_to_decimal(c_btts_si, tipo_momio)},
        {"mercado": f"5. Total Córners: Over {line_corners}", "prob": p_over_corners, "cuota": parse_odds_to_decimal(c_over_c, tipo_momio)},
        {"mercado": f"6. AH Local ({line_ha}): {equipo_loc}", "prob": p_1_ft + (p_x_ft if "+0.5" in line_ha else 0), "cuota": parse_odds_to_decimal(c_ha_loc, tipo_momio)},
        {"mercado": f"7. 1ra Mitad Gana {equipo_loc}", "prob": p_1_ht, "cuota": parse_odds_to_decimal(c_ht_1, tipo_momio)},
        {"mercado": f"8. Goles 1ra Mitad: Over {line_ht_g}", "prob": p_ht_over_g, "cuota": parse_odds_to_decimal(c_ht_over_g, tipo_momio)},
        {"mercado": f"9. DNB Local: {equipo_loc}", "prob": p_dnb_loc, "cuota": parse_odds_to_decimal(c_dnb_loc, tipo_momio)},
        {"mercado": f"10. Gana Cualquier Mitad: {equipo_loc}", "prob": p_winhalf_loc, "cuota": parse_odds_to_decimal(c_winhalf_loc, tipo_momio)}
    ]

    # FILTRADO EXCLUSIVO PROBABILIDAD >= 60%
    mercados_filtrados = [m for m in mercados_list if m['prob'] >= 0.60]

    for idx, op in enumerate(mercados_filtrados):
        ev = calcular_ev(op['prob'], op['cuota'])
        badge_label, _, _ = clasificar_opcion(op['prob'], ev)
        cuota_minima = 1.0 / op['prob'] if op['prob'] > 0 else 2.0
        
        st.markdown(f"""
        <div style="background-color:#ffffff; border:1px solid #d1e2da; border-radius:8px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-weight:900; font-size:0.9rem; color:#0b4f30;">↗ {op['mercado']}</span>
                <div style="font-size:0.75rem; color:#607d71;">
                    Prob: <b>{op['prob']*100:.1f}%</b> | Tu Cuota: <b>@{op['cuota']:.2f}</b> | EV: <b style="color:{'#059669' if ev > 0 else '#dc2626'};">{ev*100:+.1f}%</b> | Cuota Mín: <b>@{cuota_minima:.2f}</b>
                </div>
            </div>
            <div>
                <span style="background-color:{'#059669' if ev > 0 else '#d97706'}; color:#ffffff; padding:4px 8px; border-radius:4px; font-weight:900; font-size:0.7rem;">{badge_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📈 Ver Gráfica L10 - {op['mercado']}"):
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[f"P{i+1}" for i in range(10)], y=d_loc['l10_corners'], marker_color="#10b981"))
            fig.update_layout(title=f"Desglose L10 - {op['mercado']}", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=150, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}_{equipo_loc}_{equipo_vis}")
