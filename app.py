import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de Página - Estilo Light Mode con Acentos Verde Dinero
st.set_page_config(
    page_title="LA MAÑA PICKS - IA QUANT MULTI-SPORT",
    layout="wide",
    page_icon="💸"
)

# LOGOS OFICIALES DE COMPETENCIAS
LOGOS_COMPETENCIA = {
    "PREMIER LEAGUE": "https://crests.football-data.org/PL.png",
    "LALIGA": "https://crests.football-data.org/PD.png",
    "CHAMPIONS LEAGUE": "https://crests.football-data.org/CL.png",
    "NFL": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg"
}

# ESTILOS CSS REFORZADOS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap');

    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif !important;
    }

    header {visibility: hidden;}

    .nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .brand-logo {
        font-family: 'Syne', sans-serif !important;
        font-size: 2.4rem;
        font-weight: 900;
        color: #059669 !important;
        letter-spacing: -1.5px;
        text-transform: uppercase;
    }

    .hero-title {
        font-family: 'Syne', sans-serif !important;
        font-size: 3.2rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.05;
        letter-spacing: -1.8px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }
    .hero-highlight { color: #059669 !important; }
    .hero-subtitle { 
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.15rem; 
        color: #047857; 
        font-weight: 800; 
        letter-spacing: 0.5px;
        margin-bottom: 25px; 
        text-transform: uppercase;
    }

    .sim-card-home {
        background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        border: 2px solid #a7f3d0;
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.15);
    }
    .sim-card-title {
        font-family: 'Syne', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 900;
        color: #064e3b;
        line-height: 1.1;
        margin-bottom: 5px;
    }

    .badge-high { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-medium { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-low { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-star { background-color: #fef9c3; color: #854d0e; border: 1.5px solid #fde047; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-size: 0.80rem; box-shadow: 0 0 8px rgba(234, 179, 8, 0.4); }

    .analysis-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }

    .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        margin-bottom: 12px !important;
    }

    .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #a7f3d0 !important;
        border-radius: 8px !important;
        color: #064e3b !important;
        font-weight: 800 !important;
    }

    .stButton>button {
        font-family: 'Syne', sans-serif !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        padding: 12px 18px !important;
        text-align: left !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        border-color: #059669 !important;
        color: #059669 !important;
        background-color: #ecfdf5 !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SESSION STATE & TRACKER
# ------------------------------------------------------------------------------
OPCIONES_ESTADO = ["⏳ PENDIENTE", "WIN", "LOOSE"]

if "apuestas_registradas" not in st.session_state:
    st.session_state["apuestas_registradas"] = []

if "liga_activa" not in st.session_state:
    st.session_state["liga_activa"] = None

def guardar_apuesta_seleccionada(liga, partido, mercado, cuota):
    nuevo_id = max([a["id"] for a in st.session_state["apuestas_registradas"]], default=0) + 1
    st.session_state["apuestas_registradas"].append({
        "id": nuevo_id,
        "liga": liga,
        "partido": partido,
        "mercado": mercado,
        "cuota": cuota,
        "resultado": "⏳ PENDIENTE"
    })

def eliminar_apuesta(apuesta_id):
    st.session_state["apuestas_registradas"] = [a for a in st.session_state["apuestas_registradas"] if a["id"] != apuesta_id]

# ------------------------------------------------------------------------------
# DATOS COMPLETOS DE EQUIPOS Y ARBITROS
# ------------------------------------------------------------------------------
def calcular_fatiga_rotacion_automatica(equipo):
    equipos_top = [
        "Real Madrid", "Manchester City", "Bayern", "PSG", "Barcelona", 
        "Arsenal", "Liverpool", "Inter", "Atlético Madrid", "Dortmund", "Chelsea", "Tottenham", "Aston Villa", "Napoli"
    ]
    return (65, 40) if equipo in equipos_top else (20, 15)

CHAMPIONS_DATA = {
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Aston Villa": {"logo": "https://crests.football-data.org/58.png", "xg_loc": 1.75, "xga_loc": 1.30, "xg_vis": 1.45, "xga_vis": 1.50, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1},
    "Real Betis": {"logo": "https://crests.football-data.org/90.png", "xg_loc": 1.50, "xga_loc": 1.30, "xg_vis": 1.35, "xga_vis": 1.45, "ppda": 11.0, "aereos": 49, "corners": 5.2, "tarjetas": 2.4},
    "Dortmund": {"logo": "https://crests.football-data.org/4.png", "xg_loc": 1.90, "xga_loc": 1.20, "xg_vis": 1.65, "xga_vis": 1.35, "ppda": 9.2, "aereos": 52, "corners": 6.1, "tarjetas": 1.8},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "AEK": {"logo": "https://crests.football-data.org/1075.png", "xg_loc": 1.30, "xga_loc": 1.40, "xg_vis": 1.10, "xga_vis": 1.60, "ppda": 11.5, "aereos": 48, "corners": 4.5, "tarjetas": 2.2},
    "Fenerbahçe": {"logo": "https://crests.football-data.org/613.png", "xg_loc": 1.65, "xga_loc": 1.25, "xg_vis": 1.40, "xga_vis": 1.45, "ppda": 10.1, "aereos": 50, "corners": 5.5, "tarjetas": 2.5},
    "Napoli": {"logo": "https://crests.football-data.org/113.png", "xg_loc": 1.80, "xga_loc": 1.10, "xg_vis": 1.55, "xga_vis": 1.30, "ppda": 9.4, "aereos": 49, "corners": 5.8, "tarjetas": 1.9},
    "Slovan Bratislava": {"logo": "https://crests.football-data.org/1816.png", "xg_loc": 1.10, "xga_loc": 1.85, "xg_vis": 0.90, "xga_vis": 2.10, "ppda": 14.0, "aereos": 46, "corners": 3.8, "tarjetas": 2.6},
    "Shakhtar": {"logo": "https://crests.football-data.org/588.png", "xg_loc": 1.40, "xga_loc": 1.50, "xg_vis": 1.20, "xga_vis": 1.70, "ppda": 11.8, "aereos": 47, "corners": 4.6, "tarjetas": 2.1},
    "Sporting Lisboa": {"logo": "https://crests.football-data.org/498.png", "xg_loc": 1.95, "xga_loc": 0.90, "xg_vis": 1.70, "xga_vis": 1.10, "ppda": 8.9, "aereos": 53, "corners": 6.4, "tarjetas": 1.7},
    "Como": {"logo": "https://crests.football-data.org/1072.png", "xg_loc": 1.25, "xga_loc": 1.55, "xg_vis": 1.05, "xga_vis": 1.75, "ppda": 12.2, "aereos": 48, "corners": 4.2, "tarjetas": 2.3},
    "Feyenoord": {"logo": "https://crests.football-data.org/675.png", "xg_loc": 1.70, "xga_loc": 1.20, "xg_vis": 1.45, "xga_vis": 1.40, "ppda": 9.6, "aereos": 51, "corners": 5.9, "tarjetas": 1.8},
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Stuttgart": {"logo": "https://crests.football-data.org/10.png", "xg_loc": 1.60, "xga_loc": 1.35, "xg_vis": 1.35, "xga_vis": 1.50, "ppda": 10.4, "aereos": 50, "corners": 5.1, "tarjetas": 2.0},
    "PSV": {"logo": "https://crests.football-data.org/674.png", "xg_loc": 1.85, "xga_loc": 1.15, "xg_vis": 1.55, "xga_vis": 1.35, "ppda": 9.0, "aereos": 49, "corners": 6.2, "tarjetas": 1.6},
    "Bayern": {"logo": "https://crests.football-data.org/5.png", "xg_loc": 2.40, "xga_loc": 0.90, "xg_vis": 2.20, "xga_vis": 1.05, "ppda": 7.8, "aereos": 53, "corners": 7.0, "tarjetas": 1.5},
    "Lens": {"logo": "https://crests.football-data.org/523.png", "xg_loc": 1.35, "xga_loc": 1.30, "xg_vis": 1.15, "xga_vis": 1.50, "ppda": 10.8, "aereos": 52, "corners": 4.8, "tarjetas": 2.2},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg_loc": 2.20, "xga_loc": 1.00, "xg_vis": 2.05, "xga_vis": 1.10, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5},
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg_loc": 2.30, "xga_loc": 0.95, "xg_vis": 2.10, "xga_vis": 1.05, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9},
    "PSG": {"logo": "https://crests.football-data.org/524.png", "xg_loc": 2.15, "xga_loc": 1.05, "xg_vis": 1.80, "xga_vis": 1.20, "ppda": 8.9, "aereos": 49, "corners": 6.5, "tarjetas": 2.0},
    "Bodø/Glimt": {"logo": "https://crests.football-data.org/1149.png", "xg_loc": 1.30, "xga_loc": 1.60, "xg_vis": 1.10, "xga_vis": 1.80, "ppda": 11.0, "aereos": 47, "corners": 4.5, "tarjetas": 1.9},
    "Sabah Futbol": {"logo": "https://crests.football-data.org/8157.png", "xg_loc": 1.05, "xga_loc": 1.90, "xg_vis": 0.85, "xga_vis": 2.20, "ppda": 13.5, "aereos": 45, "corners": 3.6, "tarjetas": 2.7},
    "Viking": {"logo": "https://crests.football-data.org/1148.png", "xg_loc": 1.20, "xga_loc": 1.65, "xg_vis": 1.00, "xga_vis": 1.85, "ppda": 12.0, "aereos": 49, "corners": 4.1, "tarjetas": 2.1},
    "Galatasaray": {"logo": "https://crests.football-data.org/610.png", "xg_loc": 1.60, "xga_loc": 1.35, "xg_vis": 1.35, "xga_vis": 1.55, "ppda": 10.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.4},
    "RB Leipzig": {"logo": "https://crests.football-data.org/721.png", "xg_loc": 1.85, "xga_loc": 1.15, "xg_vis": 1.60, "xga_vis": 1.35, "ppda": 9.1, "aereos": 50, "corners": 6.0, "tarjetas": 1.8},
    "Atlético Madrid": {"logo": "https://crests.football-data.org/78.png", "xg_loc": 1.85, "xga_loc": 0.90, "xg_vis": 1.55, "xga_vis": 1.10, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4},
    "Slavia Praga": {"logo": "https://crests.football-data.org/583.png", "xg_loc": 1.35, "xga_loc": 1.30, "xg_vis": 1.15, "xga_vis": 1.50, "ppda": 10.6, "aereos": 52, "corners": 4.7, "tarjetas": 2.0},
    "Roma": {"logo": "https://crests.football-data.org/100.png", "xg_loc": 1.55, "xga_loc": 1.25, "xg_vis": 1.30, "xga_vis": 1.45, "ppda": 11.1, "aereos": 51, "corners": 5.2, "tarjetas": 2.3},
    "Manchester United": {"logo": "https://crests.football-data.org/66.png", "xg_loc": 1.60, "xga_loc": 1.45, "xg_vis": 1.35, "xga_vis": 1.55, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2},
    "Villarreal": {"logo": "https://crests.football-data.org/102.png", "xg_loc": 1.80, "xga_loc": 1.50, "xg_vis": 1.40, "xga_vis": 1.60, "ppda": 10.0, "aereos": 49, "corners": 5.6, "tarjetas": 2.2},
    "Club Brujas": {"logo": "https://crests.football-data.org/551.png", "xg_loc": 1.45, "xga_loc": 1.40, "xg_vis": 1.25, "xga_vis": 1.60, "ppda": 11.3, "aereos": 48, "corners": 4.9, "tarjetas": 2.1},
    "LOSC": {"logo": "https://crests.football-data.org/521.png", "xg_loc": 1.50, "xga_loc": 1.25, "xg_vis": 1.30, "xga_vis": 1.45, "ppda": 10.0, "aereos": 50, "corners": 5.2, "tarjetas": 1.9},
    "Inter": {"logo": "https://crests.football-data.org/108.png", "xg_loc": 1.95, "xga_loc": 0.85, "xg_vis": 1.65, "xga_vis": 1.00, "ppda": 10.1, "aereos": 56, "corners": 6.2, "tarjetas": 1.8},
    "LASK": {"logo": "https://crests.football-data.org/151.png", "xg_loc": 1.20, "xga_loc": 1.50, "xg_vis": 1.00, "xga_vis": 1.75, "ppda": 12.5, "aereos": 47, "corners": 4.0, "tarjetas": 2.5},
    "Porto": {"logo": "https://crests.football-data.org/503.png", "xg_loc": 1.75, "xga_loc": 1.10, "xg_vis": 1.45, "xga_vis": 1.30, "ppda": 9.3, "aereos": 52, "corners": 6.0, "tarjetas": 2.2}
}

PREMIER_LEAGUE_DATA = {
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Aston Villa": {"logo": "https://crests.football-data.org/58.png", "xg_loc": 1.75, "xga_loc": 1.30, "xg_vis": 1.45, "xga_vis": 1.50, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1},
    "Bournemouth": {"logo": "https://crests.football-data.org/1044.png", "xg_loc": 1.40, "xga_loc": 1.55, "xg_vis": 1.15, "xga_vis": 1.70, "ppda": 10.5, "aereos": 48, "corners": 4.9, "tarjetas": 2.3},
    "Brentford": {"logo": "https://crests.football-data.org/402.png", "xg_loc": 1.50, "xga_loc": 1.45, "xg_vis": 1.20, "xga_vis": 1.65, "ppda": 12.1, "aereos": 56, "corners": 4.6, "tarjetas": 1.8},
    "Brighton": {"logo": "https://crests.football-data.org/397.png", "xg_loc": 1.65, "xga_loc": 1.40, "xg_vis": 1.35, "xga_vis": 1.55, "ppda": 9.5, "aereos": 47, "corners": 5.8, "tarjetas": 2.0},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg_loc": 1.80, "xga_loc": 1.25, "xg_vis": 1.60, "xga_vis": 1.40, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6},
    "Coventry City": {"logo": "https://crests.football-data.org/1070.png", "xg_loc": 1.30, "xga_loc": 1.50, "xg_vis": 1.10, "xga_vis": 1.70, "ppda": 11.5, "aereos": 50, "corners": 4.8, "tarjetas": 1.9},
    "Crystal Palace": {"logo": "https://crests.football-data.org/354.png", "xg_loc": 1.35, "xga_loc": 1.30, "xg_vis": 1.15, "xga_vis": 1.50, "ppda": 11.8, "aereos": 53, "corners": 4.8, "tarjetas": 2.2},
    "Everton": {"logo": "https://crests.football-data.org/62.png", "xg_loc": 1.30, "xga_loc": 1.40, "xg_vis": 1.10, "xga_vis": 1.60, "ppda": 12.5, "aereos": 58, "corners": 4.7, "tarjetas": 2.1},
    "Fulham": {"logo": "https://crests.football-data.org/63.png", "xg_loc": 1.40, "xga_loc": 1.50, "xg_vis": 1.20, "xga_vis": 1.65, "ppda": 11.0, "aereos": 50, "corners": 5.1, "tarjetas": 2.0},
    "Hull City": {"logo": "https://crests.football-data.org/322.png", "xg_loc": 1.22, "xga_loc": 1.58, "xg_vis": 1.00, "xga_vis": 1.75, "ppda": 12.0, "aereos": 47, "corners": 4.3, "tarjetas": 1.7},
    "Ipswich Town": {"logo": "https://crests.football-data.org/349.png", "xg_loc": 1.20, "xga_loc": 1.60, "xg_vis": 0.95, "xga_vis": 1.85, "ppda": 13.0, "aereos": 48, "corners": 4.2, "tarjetas": 2.4},
    "Leeds": {"logo": "https://crests.football-data.org/341.png", "xg_loc": 1.45, "xga_loc": 1.40, "xg_vis": 1.25, "xga_vis": 1.60, "ppda": 9.2, "aereos": 51, "corners": 5.5, "tarjetas": 2.1},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg_loc": 2.20, "xga_loc": 1.00, "xg_vis": 2.05, "xga_vis": 1.10, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Manchester United": {"logo": "https://crests.football-data.org/66.png", "xg_loc": 1.60, "xga_loc": 1.45, "xg_vis": 1.35, "xga_vis": 1.55, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2},
    "Newcastle": {"logo": "https://crests.football-data.org/67.png", "xg_loc": 1.70, "xga_loc": 1.20, "xg_vis": 1.40, "xga_vis": 1.45, "ppda": 9.9, "aereos": 53, "corners": 6.1, "tarjetas": 1.9},
    "Nottingham Forest": {"logo": "https://crests.football-data.org/351.png", "xg_loc": 1.25, "xga_loc": 1.50, "xg_vis": 1.05, "xga_vis": 1.70, "ppda": 13.2, "aereos": 51, "corners": 4.1, "tarjetas": 2.3},
    "Sunderland": {"logo": "https://crests.football-data.org/71.png", "xg_loc": 1.28, "xga_loc": 1.52, "xg_vis": 1.05, "xga_vis": 1.75, "ppda": 12.2, "aereos": 50, "corners": 4.4, "tarjetas": 2.0},
    "Tottenham": {"logo": "https://crests.football-data.org/73.png", "xg_loc": 1.85, "xga_loc": 1.50, "xg_vis": 1.50, "xga_vis": 1.65, "ppda": 9.1, "aereos": 49, "corners": 6.3, "tarjetas": 2.1}
}

LALIGA_DATA = {
    "Deportivo Alavés": {"logo": "https://crests.football-data.org/263.png", "xg_loc": 1.25, "xga_loc": 1.45, "xg_vis": 1.00, "xga_vis": 1.65, "ppda": 12.0, "aereos": 56, "corners": 4.4, "tarjetas": 2.5},
    "Espanyol": {"logo": "https://crests.football-data.org/80.png", "xg_loc": 1.15, "xga_loc": 1.60, "xg_vis": 0.90, "xga_vis": 1.80, "ppda": 13.0, "aereos": 48, "corners": 4.1, "tarjetas": 2.6},
    "Sevilla": {"logo": "https://crests.football-data.org/559.png", "xg_loc": 1.45, "xga_loc": 1.40, "xg_vis": 1.25, "xga_vis": 1.55, "ppda": 10.5, "aereos": 51, "corners": 5.3, "tarjetas": 2.7},
    "Deportivo La Coruña": {"logo": "https://crests.football-data.org/560.png", "xg_loc": 1.20, "xga_loc": 1.45, "xg_vis": 1.00, "xga_vis": 1.65, "ppda": 11.8, "aereos": 49, "corners": 4.2, "tarjetas": 2.2},
    "Elche CF": {"logo": "https://crests.football-data.org/285.png", "xg_loc": 1.18, "xga_loc": 1.50, "xg_vis": 0.95, "xga_vis": 1.70, "ppda": 12.4, "aereos": 47, "corners": 4.0, "tarjetas": 2.3},
    "Racing Santander": {"logo": "https://crests.football-data.org/457.png", "xg_loc": 1.22, "xga_loc": 1.40, "xg_vis": 1.05, "xga_vis": 1.60, "ppda": 11.2, "aereos": 50, "corners": 4.5, "tarjetas": 2.1},
    "Villarreal": {"logo": "https://crests.football-data.org/102.png", "xg_loc": 1.80, "xga_loc": 1.50, "xg_vis": 1.40, "xga_vis": 1.60, "ppda": 10.0, "aereos": 49, "corners": 5.6, "tarjetas": 2.2},
    "Athletic": {"logo": "https://crests.football-data.org/77.png", "xg_loc": 1.60, "xga_loc": 1.10, "xg_vis": 1.30, "xga_vis": 1.25, "ppda": 9.0, "aereos": 54, "corners": 5.9, "tarjetas": 2.0},
    "Atlético de Madrid": {"logo": "https://crests.football-data.org/78.png", "xg_loc": 1.85, "xga_loc": 0.90, "xg_vis": 1.55, "xga_vis": 1.10, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4},
    "Osasuna": {"logo": "https://crests.football-data.org/79.png", "xg_loc": 1.35, "xga_loc": 1.35, "xg_vis": 1.10, "xga_vis": 1.50, "ppda": 11.5, "aereos": 53, "corners": 4.7, "tarjetas": 2.3},
    "Celta de Vigo": {"logo": "https://crests.football-data.org/558.png", "xg_loc": 1.40, "xga_loc": 1.45, "xg_vis": 1.15, "xga_vis": 1.60, "ppda": 10.8, "aereos": 47, "corners": 4.8, "tarjetas": 2.1},
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg_loc": 2.30, "xga_loc": 0.95, "xg_vis": 2.10, "xga_vis": 1.05, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9},
    "Málaga": {"logo": "https://crests.football-data.org/84.png", "xg_loc": 1.25, "xga_loc": 1.42, "xg_vis": 1.00, "xga_vis": 1.65, "ppda": 11.6, "aereos": 48, "corners": 4.3, "tarjetas": 2.2},
    "Betis": {"logo": "https://crests.football-data.org/90.png", "xg_loc": 1.50, "xga_loc": 1.30, "xg_vis": 1.25, "xga_vis": 1.45, "ppda": 11.0, "aereos": 49, "corners": 5.2, "tarjetas": 2.4},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Real Sociedad": {"logo": "https://crests.football-data.org/92.png", "xg_loc": 1.65, "xga_loc": 1.15, "xg_vis": 1.35, "xga_vis": 1.30, "ppda": 9.1, "aereos": 52, "corners": 5.7, "tarjetas": 2.0},
    "Valencia CF": {"logo": "https://crests.football-data.org/95.png", "xg_loc": 1.25, "xga_loc": 1.45, "xg_vis": 1.05, "xga_vis": 1.60, "ppda": 11.8, "aereos": 50, "corners": 4.6, "tarjetas": 2.5},
    "Rayo Vallecano": {"logo": "https://crests.football-data.org/87.png", "xg_loc": 1.30, "xga_loc": 1.40, "xg_vis": 1.10, "xga_vis": 1.55, "ppda": 9.4, "aereos": 48, "corners": 5.0, "tarjetas": 2.6},
    "Getafe": {"logo": "https://crests.football-data.org/82.png", "xg_loc": 1.10, "xga_loc": 1.20, "xg_vis": 0.85, "xga_vis": 1.45, "ppda": 12.8, "aereos": 58, "corners": 4.0, "tarjetas": 3.1},
    "Levante": {"logo": "https://crests.football-data.org/88.png", "xg_loc": 1.22, "xga_loc": 1.55, "xg_vis": 0.95, "xga_vis": 1.70, "ppda": 12.1, "aereos": 49, "corners": 4.2, "tarjetas": 2.4}
}

NFL_DATA = {
    "Miami Dolphins": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "td_exp": 3.2, "fg_exp": 1.5},
    "New York Jets": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "td_exp": 2.5, "fg_exp": 2.1},
    "Buffalo Bills": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "td_exp": 3.4, "fg_exp": 1.6},
    "New England Patriots": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png", "td_exp": 2.2, "fg_exp": 1.9},
    "Cincinnati Bengals": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png", "td_exp": 3.1, "fg_exp": 1.8},
    "Pittsburgh Steelers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png", "td_exp": 2.4, "fg_exp": 2.2},
    "Cleveland Browns": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png", "td_exp": 2.5, "fg_exp": 2.0},
    "Baltimore Ravens": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "td_exp": 3.5, "fg_exp": 1.7},
    "Indianapolis Colts": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png", "td_exp": 2.8, "fg_exp": 1.8},
    "Houston Texans": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png", "td_exp": 2.9, "fg_exp": 1.9},
    "Tennessee Titans": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png", "td_exp": 2.3, "fg_exp": 2.0},
    "Jacksonville Jaguars": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png", "td_exp": 2.7, "fg_exp": 1.8},
    "Los Angeles Chargers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png", "td_exp": 2.8, "fg_exp": 1.9},
    "Kansas City Chiefs": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "td_exp": 3.5, "fg_exp": 1.7},
    "Las Vegas Raiders": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png", "td_exp": 2.3, "fg_exp": 2.1},
    "Denver Broncos": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png", "td_exp": 2.4, "fg_exp": 2.0},
    "New York Giants": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png", "td_exp": 2.1, "fg_exp": 2.0},
    "Washington Commanders": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png", "td_exp": 2.7, "fg_exp": 1.8},
    "Philadelphia Eagles": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "td_exp": 3.3, "fg_exp": 1.6},
    "Dallas Cowboys": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "td_exp": 3.2, "fg_exp": 1.9},
    "Minnesota Vikings": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png", "td_exp": 2.9, "fg_exp": 1.8},
    "Chicago Bears": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png", "td_exp": 2.5, "fg_exp": 1.9},
    "Green Bay Packers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png", "td_exp": 3.0, "fg_exp": 1.7},
    "Detroit Lions": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "td_exp": 3.4, "fg_exp": 1.6},
    "New Orleans Saints": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png", "td_exp": 2.6, "fg_exp": 2.0},
    "Tampa Bay Buccaneers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "td_exp": 2.8, "fg_exp": 1.8},
    "Atlanta Falcons": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png", "td_exp": 2.7, "fg_exp": 1.9},
    "Carolina Panthers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png", "td_exp": 2.0, "fg_exp": 2.1},
    "Los Angeles Rams": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png", "td_exp": 3.0, "fg_exp": 1.7},
    "Seattle Seahawks": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png", "td_exp": 2.7, "fg_exp": 1.9},
    "Arizona Cardinals": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png", "td_exp": 2.5, "fg_exp": 2.0},
    "San Francisco 49ers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "td_exp": 3.6, "fg_exp": 1.5}
}

ARBITROS_PREMIER = {
    "Anthony Taylor": {"prom_tarjetas": 4.5},
    "Michael Oliver": {"prom_tarjetas": 3.6},
    "Paul Tierney": {"prom_tarjetas": 4.8},
    "Chris Kavanagh": {"prom_tarjetas": 3.9}
}

ARBITROS_LALIGA = {
    "Jesús Gil Manzano": {"prom_tarjetas": 5.2},
    "José María Sánchez Martínez": {"prom_tarjetas": 4.9},
    "Alejandro Hernández Hernández": {"prom_tarjetas": 5.8},
    "Ricardo De Burgos Bengoetxea": {"prom_tarjetas": 4.1}
}

ARBITROS_CHAMPIONS = {
    "Jesús Gil Manzano": {"prom_tarjetas": 5.2},
    "Szymon Marciniak": {"prom_tarjetas": 4.1},
    "Daniele Orsato": {"prom_tarjetas": 4.7},
    "Clément Turpin": {"prom_tarjetas": 3.8},
    "Slavko Vinčić": {"prom_tarjetas": 3.9}
}

# ------------------------------------------------------------------------------
# MOTORES DE SIMULACIÓN Y GENERACIÓN GRÁFICA
# ------------------------------------------------------------------------------
def parse_odds(val_str, fmt_type):
    try:
        val = float(val_str)
        if fmt_type == "Decimales": return val if val > 1.0 else 2.00
        return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def simular_montecarlo_avanzado(d_loc, d_vis, fatiga_loc, rot_loc, fatiga_vis, rot_vis, arbitro_card, line_goles, line_corners, line_cards, n_sim=10000):
    fatiga_factor_loc = 1.0 - (fatiga_loc * 0.12 + rot_loc * 0.10)
    fatiga_factor_vis = 1.0 - (fatiga_vis * 0.12 + rot_vis * 0.10)

    tactical_h = (12.0 / max(d_loc["ppda"], 5.0)) * (d_loc["aereos"] / 50.0)
    tactical_a = (12.0 / max(d_vis["ppda"], 5.0)) * (d_vis["aereos"] / 50.0)

    lambda_h = max(1.55 * (d_loc["xg_loc"] / 1.55) * (d_vis["xga_vis"] / 1.25) * tactical_h * fatiga_factor_loc, 0.2)
    lambda_a = max(1.25 * (d_vis["xg_vis"] / 1.25) * (d_loc["xga_loc"] / 1.55) * tactical_a * fatiga_factor_vis, 0.15)

    goles_h = np.random.poisson(lambda_h, n_sim)
    goles_a = np.random.poisson(lambda_a, n_sim)

    exp_c = (d_loc["corners"] + d_vis["corners"]) * 0.95
    corners_totales = np.random.poisson(exp_c, n_sim)
    tarjetas_totales = np.random.poisson((d_loc["tarjetas"] + d_vis["tarjetas"]) * (arbitro_card / 4.0), n_sim)

    return {
        "p_1_ft": np.mean(goles_h > goles_a),
        "p_x_ft": np.mean(goles_h == goles_a),
        "p_2_ft": np.mean(goles_h < goles_a),
        "p_over_goles": np.mean((goles_h + goles_a) > line_goles),
        "p_under_goles": np.mean((goles_h + goles_a) < line_goles),
        "p_btts_si": np.mean((goles_h > 0) & (goles_a > 0)),
        "p_btts_no": np.mean((goles_h == 0) | (goles_a == 0)),
        "p_over_corners": np.mean(corners_totales > line_corners),
        "p_under_corners": np.mean(corners_totales < line_corners),
        "p_over_cards": np.mean(tarjetas_totales > line_cards),
        "p_under_cards": np.mean(tarjetas_totales < line_cards)
    }

def simular_montecarlo_nfl(d_loc, d_vis, clima_viento, clima_frio, baja_qb_loc, baja_qb_vis, spread_loc, spread_vis, line_pts, line_fg, line_td, n_sim=10000):
    factor_clima = 1.0 - (0.15 if clima_viento else 0.0) - (0.10 if clima_frio else 0.0)
    exp_td_loc = d_loc.get("td_exp", 3.0) * (0.75 if baja_qb_loc else 1.0) * factor_clima
    exp_td_vis = d_vis.get("td_exp", 2.8) * (0.75 if baja_qb_vis else 1.0) * factor_clima

    sim_td_loc = np.random.poisson(exp_td_loc, n_sim)
    sim_td_vis = np.random.poisson(exp_td_vis, n_sim)
    sim_fg_loc = np.random.poisson(d_loc.get("fg_exp", 1.8), n_sim)
    sim_fg_vis = np.random.poisson(d_vis.get("fg_exp", 1.7), n_sim)

    pts_loc = (sim_td_loc * 7) + (sim_fg_loc * 3)
    pts_vis = (sim_td_vis * 7) + (sim_fg_vis * 3)

    return {
        "p_ml_loc": np.mean(pts_loc > pts_vis),
        "p_ml_vis": np.mean(pts_vis > pts_loc),
        "p_spread_loc": np.mean((pts_loc + spread_loc) > pts_vis),
        "p_spread_vis": np.mean((pts_vis + spread_vis) > pts_loc),
        "p_over_pts": np.mean((pts_loc + pts_vis) > line_pts),
        "p_under_pts": np.mean((pts_loc + pts_vis) < line_pts),
        "p_over_fg": np.mean((sim_fg_loc + sim_fg_vis) > line_fg),
        "p_under_fg": np.mean((sim_fg_loc + sim_fg_vis) < line_fg),
        "p_over_td": np.mean((sim_td_loc + sim_td_vis) > line_td),
        "p_under_td": np.mean((sim_td_loc + sim_td_vis) < line_td)
    }

def generar_grafica_mini_15_partidos(prob_exito):
    data = np.random.choice([1, 0], size=15, p=[prob_exito, 1 - prob_exito])
    colors = ['#10b981' if x == 1 else '#ef4444' for x in data]
    labels = [f"L{i+1}" for i in range(5)] + [f"V{i+1}" for i in range(5)] + [f"H{i+1}" for i in range(5)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[1]*15, marker_color=colors, hoverinfo='x'))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=130, margin=dict(l=5, r=5, t=10, b=20),
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color='#64748b')),
        yaxis=dict(showgrid=False, showticklabels=False, range=[0, 1.2])
    )
    return fig

def generar_grafica_efectividad_capsulas_3d(list_apuestas):
    ligas = ["PREMIER LEAGUE", "LALIGA", "CHAMPIONS LEAGUE", "NFL"]
    wins = [sum(1 for a in list_apuestas if a["liga"] == l and a["resultado"] == "WIN") for l in ligas]
    looses = [sum(1 for a in list_apuestas if a["liga"] == l and a["resultado"] == "LOOSE") for l in ligas]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='WIN (Ganados)',
        x=ligas, y=wins,
        marker=dict(color='#10b981', line=dict(color='#059669', width=2), cornerradius=15),
        opacity=0.95
    ))

    fig.add_trace(go.Bar(
        name='LOOSE (Perdidos)',
        x=ligas, y=looses,
        marker=dict(color='#ef4444', line=dict(color='#b91c1c', width=2), cornerradius=15),
        opacity=0.95
    ))

    fig.update_layout(
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=260, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color='#0f172a', family='Syne')),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color='#0f172a', family='Syne')),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=10, color='#64748b'))
    )
    return fig

# HEADER
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#059669;">PICKS</span></div>
    <div style="font-weight:800; color:#475569; font-size:0.9rem;">MODELO QUANT MULTI-SPORT</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# VISTA 1: HOME LANDING PAGE
# ==============================================================================
if st.session_state["liga_activa"] is None:
    col_hero_left, col_hero_right = st.columns([6, 6])

    with col_hero_left:
        st.markdown("""
        <div class="hero-title">ANALIZANDO CON LA MAÑA <br><span class="hero-highlight">QUE NOS HACE GANAR</span></div>
        <div class="hero-subtitle">JUEGA CON ESTADÍSTICAS Y CON MAÑA.</div>
        """, unsafe_allow_html=True)

        col_b1, col_b1_img = st.columns([10, 2])
        with col_b1:
            if st.button("PREMIER LEAGUE (20 Equipos) ➔", use_container_width=True):
                st.session_state["liga_activa"] = "PREMIER LEAGUE"
                st.rerun()
        with col_b1_img: st.image(LOGOS_COMPETENCIA["PREMIER LEAGUE"], width=40)

        col_b2, col_b2_img = st.columns([10, 2])
        with col_b2:
            if st.button("LALIGA EA SPORTS (20 Equipos) ➔", use_container_width=True):
                st.session_state["liga_activa"] = "LALIGA"
                st.rerun()
        with col_b2_img: st.image(LOGOS_COMPETENCIA["LALIGA"], width=40)

        col_b3, col_b3_img = st.columns([10, 2])
        with col_b3:
            if st.button("CHAMPIONS LEAGUE (36 Equipos) ➔", use_container_width=True):
                st.session_state["liga_activa"] = "CHAMPIONS LEAGUE"
                st.rerun()
        with col_b3_img: st.image(LOGOS_COMPETENCIA["CHAMPIONS LEAGUE"], width=40)

        col_b4, col_b4_img = st.columns([10, 2])
        with col_b4:
            if st.button("NFL (32 Equipos AFC/NFC) ➔", use_container_width=True):
                st.session_state["liga_activa"] = "NFL"
                st.rerun()
        with col_b4_img: st.image(LOGOS_COMPETENCIA["NFL"], width=40)

    with col_hero_right:
        apuestas_hist = st.session_state["apuestas_registradas"]
        total_w = sum(1 for a in apuestas_hist if a["resultado"] == "WIN")
        total_l = sum(1 for a in apuestas_hist if a["resultado"] == "LOOSE")
        tot_picks = total_w + total_l
        efectividad_val = (total_w / tot_picks * 100.0) if tot_picks > 0 else 0.0

        st.markdown(f"""
        <div class="sim-card-home">
            <div class="sim-card-title">Efectividad Global: <span style="color:#059669;">{efectividad_val:.1f}%</span></div>
            <p style="color:#475569; font-size:0.88rem; font-weight:700; margin-bottom:10px;">
                Récord Registrado: <b>{total_w} WINS</b> / <b>{total_l} LOOSES</b> (Total: {tot_picks} Picks)
            </p>
        </div>
        """, unsafe_allow_html=True)

        fig_capsulas_3d = generar_grafica_efectividad_capsulas_3d(apuestas_hist)
        st.plotly_chart(fig_capsulas_3d, use_container_width=True, key="chart_3d_home")

# ==============================================================================
# VISTA 2: PANEL DE ANÁLISIS (FÚTBOL Y NFL)
# ==============================================================================
else:
    liga = st.session_state["liga_activa"]

    c_head_title, c_head_back = st.columns([9, 3])
    with c_head_title:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="{LOGOS_COMPETENCIA[liga]}" width="45">
            <div class='hero-title' style='font-size:2.0rem;'>Escaneo de Valor <span class='hero-highlight'>({liga})</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c_head_back:
        if st.button("← Inicio", use_container_width=True):
            st.session_state["liga_activa"] = None
            st.rerun()

    if liga == "PREMIER LEAGUE": TEAMS_DATA, ARBITROS_LIGA = PREMIER_LEAGUE_DATA, ARBITROS_PREMIER
    elif liga == "LALIGA": TEAMS_DATA, ARBITROS_LIGA = LALIGA_DATA, ARBITROS_LALIGA
    elif liga == "CHAMPIONS LEAGUE": TEAMS_DATA, ARBITROS_LIGA = CHAMPIONS_DATA, ARBITROS_CHAMPIONS
    else: TEAMS_DATA, ARBITROS_LIGA = NFL_DATA, {}

    col_izq_inputs, col_der_analysis = st.columns([1, 1])

    with col_izq_inputs:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>⚙️ Configuración y Métricas Automáticas</h3>", unsafe_allow_html=True)

        if liga == "NFL":
            c_loc, c_vis = st.columns(2)
            with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(TEAMS_DATA.keys())), index=13)
            with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(TEAMS_DATA.keys())), index=26)
        else:
            c_loc, c_vis, c_ref = st.columns([3, 3, 2])
            with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(TEAMS_DATA.keys())), index=0)
            with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(TEAMS_DATA.keys())), index=1 if len(TEAMS_DATA)>1 else 0)
            with c_ref: arbitro_sel = st.selectbox("Árbitro:", list(ARBITROS_LIGA.keys()), index=0)
            arbitro_data = ARBITROS_LIGA[arbitro_sel]

        d_loc, d_vis = TEAMS_DATA[eq_loc], TEAMS_DATA[eq_vis]

        st.markdown(f"""
        <div class="analysis-card" style="border:1px solid #a7f3d0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="{d_loc['logo']}" width="28">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_loc}</span>
                </div>
                <div style="font-weight:900; color:#059669;">VS</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_vis}</span>
                    <img src="{d_vis['logo']}" width="28">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # CÁLCULO ESTIMADO DE MOMIOS BASE ESTILO CALIENTE PARA AUTO-COMPLETAR
        if liga == "NFL":
            sim_init = simular_montecarlo_nfl(d_loc, d_vis, False, False, False, False, -3.5, 3.5, 47.5, 3.5, 5.5)
            q1_calc = str(round(1.0 / (sim_init['p_ml_loc'] * 1.06), 2))
            q2_calc = str(round(1.0 / (sim_init['p_ml_vis'] * 1.06), 2))
            qx_calc = "15.0"
        else:
            fatiga_auto_loc, rot_auto_loc = calcular_fatiga_rotacion_automatica(eq_loc)
            fatiga_auto_vis, rot_auto_vis = calcular_fatiga_rotacion_automatica(eq_vis)
            sim_init = simular_montecarlo_avanzado(d_loc, d_vis, fatiga_auto_loc/100, rot_auto_loc/100, fatiga_auto_vis/100, rot_auto_vis/100, arbitro_data["prom_tarjetas"], 2.5, 9.5, 4.5)
            q1_calc = str(round(1.0 / (sim_init['p_1_ft'] * 1.06), 2))
            qx_calc = str(round(1.0 / (sim_init['p_x_ft'] * 1.06), 2))
            q2_calc = str(round(1.0 / (sim_init['p_2_ft'] * 1.06), 2))

        # BOTÓN AUTO-COMPLETAR AUTO-ESTIMADO
        st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Ingreso de Cuotas Estimadas / Manuales</h4>", unsafe_allow_html=True)
        if st.button("⚡ Cargar Momios Estimados de Mercado (Caliente/Bet365)", use_container_width=True):
            st.session_state[f"q1_input_{liga}"] = q1_calc
            st.session_state[f"qx_input_{liga}"] = qx_calc
            st.session_state[f"q2_input_{liga}"] = q2_calc
            st.success("¡Momios estimados de mercado cargados!")
            st.rerun()

        fmt_odds = st.radio("Formato de Cuotas:", ["Decimales", "Americanos"], horizontal=True)

        # FORMULARIO CONTEXTUAL AJUSTABLE
        with st.expander("⚙️ Ajustar Momios Manualmente (Todas las Opciones)", expanded=True):
            if liga == "NFL":
                c_ml1, c_ml2 = st.columns(2)
                with c_ml1: q_1 = st.text_input(f"ML {eq_loc[:12]}", value=st.session_state.get(f"q1_input_{liga}", q1_calc), key=f"q1_input_{liga}")
                with c_ml2: q_2 = st.text_input(f"ML {eq_vis[:12]}", value=st.session_state.get(f"q2_input_{liga}", q2_calc), key=f"q2_input_{liga}")
                q_x = "15.0"

                ch1, ch2, ch3, ch4 = st.columns([1.5, 1.25, 1.5, 1.25])
                with ch1: spread_loc = st.slider(f"Spread Local", -16.5, 16.5, -3.5, step=0.5)
                with ch2: q_spread_loc = st.text_input(f"Cuota {spread_loc}", value="1.90")
                with ch3: spread_vis = st.slider(f"Spread Visita", -16.5, 16.5, +3.5, step=0.5)
                with ch4: q_spread_vis = st.text_input(f"Cuota {spread_vis}", value="1.90")

                ct1, ct2, ct3 = st.columns([1.5, 1.25, 1.25])
                with ct1: line_pts = st.slider("Línea Puntos Totales", 20.5, 80.5, 47.5, step=1.0)
                with ct2: q_over_pts = st.text_input(f"Over {line_pts}", value="1.90")
                with ct3: q_under_pts = st.text_input(f"Under {line_pts}", value="1.90")
            else:
                c1, c2, c3 = st.columns(3)
                with c1: q_1 = st.text_input(f"1X2 {eq_loc[:3]}", value=st.session_state.get(f"q1_input_{liga}", q1_calc), key=f"q1_input_{liga}")
                with c2: q_x = st.text_input("1X2 Empate", value=st.session_state.get(f"qx_input_{liga}", qx_calc), key=f"qx_input_{liga}")
                with c3: q_2 = st.text_input(f"1X2 {eq_vis[:3]}", value=st.session_state.get(f"q2_input_{liga}", q2_calc), key=f"q2_input_{liga}")

                c4, c5, c6 = st.columns(3)
                with c4: q_1x = st.text_input("DC 1X", value="1.55")
                with c5: q_x2 = st.text_input("DC X2", value="1.42")
                with c6: q_12 = st.text_input("DC 12", value="1.30")

                cg1, cg2, cg3 = st.columns([1.5, 1.25, 1.25])
                with cg1: line_goles = st.slider("Línea Goles FT", 1.5, 4.5, 2.5, step=1.0)
                with cg2: q_over_g = st.text_input(f"Over {line_goles}", value="1.90")
                with cg3: q_under_g = st.text_input(f"Under {line_goles}", value="1.90")

                cb1, cb2, cha1, cha2, cha3 = st.columns([1, 1, 1.2, 1, 1])
                with cb1: q_btts_si = st.text_input("BTTS SÍ", value="1.75")
                with cb2: q_btts_no = st.text_input("BTTS NO", value="2.05")
                with cha1: line_ha = st.selectbox("Hándicap AH", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=0)
                with cha2: q_ha_loc = st.text_input(f"AH {eq_loc[:3]}", value="1.55")
                with cha3: q_ha_vis = st.text_input(f"AH {eq_vis[:3]}", value="2.35")

                cc1, cc2, cc3 = st.columns([1.5, 1.25, 1.25])
                with cc1: line_corners = st.slider("Línea Córners", 8.5, 12.5, 9.5, step=1.0)
                with cc2: q_over_c = st.text_input(f"Córners > {line_corners}", value="1.85")
                with cc3: q_under_c = st.text_input(f"Córners < {line_corners}", value="1.85")

                ct1, ct2, ct3 = st.columns([1.5, 1.25, 1.25])
                with ct1: line_cards = st.slider("Línea Tarjetas", 3.5, 5.5, 4.5, step=1.0)
                with ct2: q_over_t = st.text_input(f"Tarjetas > {line_cards}", value="1.95")
                with ct3: q_under_t = st.text_input(f"Tarjetas < {line_cards}", value="1.80")

    with col_der_analysis:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>📊 Matriz de Riesgo y Escaneo (+EV)</h3>", unsafe_allow_html=True)

        if liga == "NFL":
            sim_results = simular_montecarlo_nfl(d_loc, d_vis, False, False, False, False, spread_loc, spread_vis, line_pts, 3.5, 5.5)
            mercados_evaluados = [
                {"mercado": f"1. Moneyline: Gana {eq_loc}", "prob": sim_results['p_ml_loc'], "cuota": parse_odds(q_1, fmt_odds)},
                {"mercado": f"1. Moneyline: Gana {eq_vis}", "prob": sim_results['p_ml_vis'], "cuota": parse_odds(q_2, fmt_odds)},
                {"mercado": f"2. Spread: {eq_loc} ({spread_loc:+} pts)", "prob": sim_results['p_spread_loc'], "cuota": parse_odds(q_spread_loc, fmt_odds)},
                {"mercado": f"2. Spread: {eq_vis} ({spread_vis:+} pts)", "prob": sim_results['p_spread_vis'], "cuota": parse_odds(q_spread_vis, fmt_odds)},
                {"mercado": f"3. Total Puntos: Over {line_pts}", "prob": sim_results['p_over_pts'], "cuota": parse_odds(q_over_pts, fmt_odds)},
                {"mercado": f"3. Total Puntos: Under {line_pts}", "prob": sim_results['p_under_pts'], "cuota": parse_odds(q_under_pts, fmt_odds)}
            ]
        else:
            fatiga_auto_loc, rot_auto_loc = calcular_fatiga_rotacion_automatica(eq_loc)
            fatiga_auto_vis, rot_auto_vis = calcular_fatiga_rotacion_automatica(eq_vis)
            sim_results = simular_montecarlo_avanzado(d_loc, d_vis, fatiga_auto_loc/100, rot_auto_loc/100, fatiga_auto_vis/100, rot_auto_vis/100, arbitro_data["prom_tarjetas"], line_goles, line_corners, line_cards)
            mercados_evaluados = [
                {"mercado": f"1. Resultado: Gana {eq_loc}", "prob": sim_results['p_1_ft'], "cuota": parse_odds(q_1, fmt_odds)},
                {"mercado": f"1. Resultado: Empate", "prob": sim_results['p_x_ft'], "cuota": parse_odds(q_x, fmt_odds)},
                {"mercado": f"1. Resultado: Gana {eq_vis}", "prob": sim_results['p_2_ft'], "cuota": parse_odds(q_2, fmt_odds)},
                {"mercado": f"2. Doble Chance: {eq_loc} o Empate (1X)", "prob": sim_results['p_1_ft'] + sim_results['p_x_ft'], "cuota": parse_odds(q_1x, fmt_odds)},
                {"mercado": f"2. Doble Chance: {eq_vis} o Empate (X2)", "prob": sim_results['p_2_ft'] + sim_results['p_x_ft'], "cuota": parse_odds(q_x2, fmt_odds)},
                {"mercado": f"3. Total Goles: Over {line_goles}", "prob": sim_results['p_over_goles'], "cuota": parse_odds(q_over_g, fmt_odds)},
                {"mercado": f"3. Total Goles: Under {line_goles}", "prob": sim_results['p_under_goles'], "cuota": parse_odds(q_under_g, fmt_odds)},
                {"mercado": "4. Ambos Equipos Anotan: SÍ", "prob": sim_results['p_btts_si'], "cuota": parse_odds(q_btts_si, fmt_odds)},
                {"mercado": "4. Ambos Equipos Anotan: NO", "prob": sim_results['p_btts_no'], "cuota": parse_odds(q_btts_no, fmt_odds)},
                {"mercado": f"5. Hándicap Asiático: {eq_loc} ({line_ha})", "prob": sim_results['p_1_ft'] + (sim_results['p_x_ft'] if "+0.5" in line_ha else 0), "cuota": parse_odds(q_ha_loc, fmt_odds)},
                {"mercado": f"5. Hándicap Asiático: {eq_vis} ({line_ha})", "prob": sim_results['p_2_ft'] + (sim_results['p_x_ft'] if "+0.5" in line_ha else 0), "cuota": parse_odds(q_ha_vis, fmt_odds)},
                {"mercado": f"6. Total Córners: Over {line_corners}", "prob": sim_results['p_over_corners'], "cuota": parse_odds(q_over_c, fmt_odds)},
                {"mercado": f"7. Total Tarjetas: Over {line_cards}", "prob": sim_results['p_over_cards'], "cuota": parse_odds(q_over_t, fmt_odds)}
            ]

        for idx, item in enumerate(mercados_evaluados):
            prob_val = item['prob']
            cuota_casa = item['cuota']
            cuota_real = 1.0 / prob_val if prob_val > 0 else 99.0
            ev = (prob_val * cuota_casa) - 1.0

            badge_html = '<span class="badge-star">💎 APUESTA ESTRELLA (+EV)</span>' if (prob_val >= 0.75 and ev > 0) else '<span class="badge-medium">🟠 MEDIUM PROBABILITY</span>'

            st.markdown(f"""
            <div class="analysis-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:900; font-size:0.9rem; color:#0f172a;">↗ {item['mercado']}</span>
                        <div style="font-size:0.78rem; color:#607d71; margin-top:4px;">
                            Prob. IA: <b>{prob_val*100:.1f}%</b> | Cuota Real: <b style="color:#059669;">@{cuota_real:.2f}</b> | Tu Casa: <b style="color:#059669;">@{cuota_casa:.2f}</b>
                        </div>
                    </div>
                    <div>{badge_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"🎯 SELECCIONAR APUESTA", key=f"sel_fut_{idx}"):
                guardar_apuesta_seleccionada(liga, f"{eq_loc} vs {eq_vis}", item['mercado'], item['cuota'])
                st.rerun()

            with st.expander(f"📈 Ver Tendencia de Cobertura de Línea (Últimos 15 Partidos)"):
                fig_mini = generar_grafica_mini_15_partidos(prob_val)
                st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_mini_{liga}_{idx}")

    # GESTIÓN E HISTORIAL INTERACTIVO DE PICKS REALES
    st.markdown("<br><h3 style='color:#0f172a; font-size:1.1rem; font-weight:900;'>📜 Histórico e Inspección de Apuestas</h3>", unsafe_allow_html=True)
    
    liga_apuestas = [a for a in st.session_state["apuestas_registradas"] if a["liga"] == liga]
    if not liga_apuestas:
        st.info("No hay apuestas seleccionadas aún para esta competición.")
    else:
        for a in liga_apuestas:
            col_info, col_estado, col_del = st.columns([7, 3, 2])
            with col_info:
                st.markdown(f"<b>{a['partido']}</b> - {a['mercado']} (@{a['cuota']})", unsafe_allow_html=True)
            with col_estado:
                estado_actual = a.get("resultado", "⏳ PENDIENTE")
                idx_sel = OPCIONES_ESTADO.index(estado_actual) if estado_actual in OPCIONES_ESTADO else 0
                nuevo_res = st.selectbox("Estado Real", OPCIONES_ESTADO, index=idx_sel, key=f"res_{a['id']}")
                a["resultado"] = nuevo_res
            with col_del:
                if st.button("🗑️ Eliminar", key=f"del_{a['id']}"):
                    eliminar_apuesta(a["id"])
                    st.rerun()
