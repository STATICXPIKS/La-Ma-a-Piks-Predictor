import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="LA MAÑA PICKS - DASHBOARD DE ANÁLISIS",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS ADAPTADOS AL DISEÑO ANALÍTICO CLARO DE TU IMAGEN
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

# BASES DE DATOS SEPARADAS STRICTAMENTE
PREMIER_LEAGUE_DATA = {
    "ARSENAL": {"logo": "https://crests.football-data.org/57.png", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4, "forma": ["G","G","E","G","G","P","G","G","E","G"], "l10_corners": [7, 8, 6, 9, 5, 8, 10, 6, 4, 7]},
    "ASTON VILLA": {"logo": "https://crests.football-data.org/58.png", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1, "forma": ["G","P","G","E","G","P","G","E","G","P"], "l10_corners": [5, 6, 4, 7, 5, 6, 8, 5, 4, 6]},
    "BOURNEMOUTH": {"logo": "https://crests.football-data.org/1044.png", "xg": 1.40, "xga": 1.55, "ppda": 10.5, "aereos": 48, "corners": 4.9, "tarjetas": 2.3, "forma": ["P","E","G","P","P","G","E","P","G","E"], "l10_corners": [4, 5, 6, 4, 3, 5, 6, 4, 5, 4]},
    "BRENTFORD": {"logo": "https://crests.football-data.org/402.png", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6, "tarjetas": 1.8, "forma": ["G","P","E","P","G","E","P","G","P","G"], "l10_corners": [3, 5, 8, 6, 8, 6, 10, 8, 4, 4]},
    "CHELSEA": {"logo": "https://crests.football-data.org/61.png", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6, "forma": ["G","G","P","E","G","G","P","E","G","G"], "l10_corners": [6, 7, 5, 8, 6, 9, 4, 7, 5, 6]},
    "LIVERPOOL": {"logo": "https://crests.football-data.org/64.png", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5, "forma": ["G","G","G","E","G","G","P","G","G","E"], "l10_corners": [8, 9, 7, 10, 6, 8, 11, 7, 5, 8]},
    "MANCHESTER CITY": {"logo": "https://crests.football-data.org/65.png", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3, "forma": ["G","G","E","G","G","G","P","G","E","G"], "l10_corners": [9, 8, 10, 7, 11, 8, 6, 9, 7, 10]},
    "MANCHESTER UNITED": {"logo": "https://crests.football-data.org/66.png", "xg": 1.60, "xga": 1.45, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2, "forma": ["P","G","E","P","G","E","P","G","P","E"], "l10_corners": [6, 5, 7, 6, 8, 5, 6, 7, 5, 6]}
}

LALIGA_DATA = {
    "ATHLETIC CLUB": {"logo": "https://crests.football-data.org/77.png", "xg": 1.60, "xga": 1.10, "ppda": 9.0, "aereos": 54, "corners": 5.9, "tarjetas": 2.0, "forma": ["G","E","G","G","P","G","E","G","G","P"], "l10_corners": [6, 5, 7, 6, 5, 8, 6, 7, 5, 6]},
    "ATLETICO MADRID": {"logo": "https://crests.football-data.org/78.png", "xg": 1.85, "xga": 0.90, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4, "forma": ["G","G","P","G","E","G","G","E","G","G"], "l10_corners": [6, 7, 5, 8, 6, 7, 5, 8, 6, 7]},
    "BARCELONA": {"logo": "https://crests.football-data.org/81.png", "xg": 2.30, "xga": 0.95, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9, "forma": ["G","G","G","G","P","G","G","E","G","G"], "l10_corners": [7, 8, 6, 9, 7, 8, 10, 6, 5, 8]},
    "REAL MADRID": {"logo": "https://crests.football-data.org/86.png", "xg": 2.35, "xga": 0.80, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6, "forma": ["G","G","G","E","G","G","P","G","G","G"], "l10_corners": [8, 9, 7, 10, 8, 9, 11, 7, 6, 8]}
}

ARBITROS = {
    "Chris Kavanagh": 3.9,
    "Anthony Taylor": 4.2,
    "Michael Oliver": 3.6,
    "Ricardo De Burgos": 4.1
}

def render_dots_forma(forma_list):
    html = '<div class="dot-form-container">'
    for res in forma_list[-5:]:
        cls = "dot-g" if res == "G" else ("dot-e" if res == "E" else "dot-p")
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

# ==============================================================================
# SIDEBAR: SELECCIÓN EXCLUSIVA DE COMPETICIÓN
# ==============================================================================
st.sidebar.markdown("<h3 style='color:#0b4f30; font-size:0.95rem; font-weight:900;'>FILTRAR POR COMPETICIÓN</h3>", unsafe_allow_html=True)

liga_activa = st.sidebar.radio(
    "Selecciona Liga:",
    ["⚽ Premier League", "🔴 LaLiga EA Sports"],
    index=0
)

# SELECCIÓN DINÁMICA DEL DATASET
if "Premier League" in liga_activa:
    TEAMS_DATA = PREMIER_LEAGUE_DATA
else:
    TEAMS_DATA = LALIGA_DATA

# ==============================================================================
# ENCABEZADO Y KPIS
# ==============================================================================
st.markdown("<h1 class='brand-title-top'>LA MAÑA PICKS - PANEL DE APUESTAS</h1>", unsafe_allow_html=True)

# ==============================================================================
# ENCUENTRO SELECCIONADO
# ==============================================================================
st.markdown("<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900;'>⚡ ENCUENTRO SELECCIONADO PARA ANÁLISIS DETALLADO</h3>", unsafe_allow_html=True)

col_local, col_visita, col_referee = st.columns([3, 3, 2])

with col_local:
    equipo_loc = st.selectbox("Equipo Local:", list(TEAMS_DATA.keys()), index=0)
with col_visita:
    equipo_vis = st.selectbox("Equipo Visitante:", list(TEAMS_DATA.keys()), index=1 if len(TEAMS_DATA) > 1 else 0)
with col_referee:
    arbitro_sel = st.selectbox("Árbitro Asignado:", list(ARBITROS.keys()), index=0)

d_loc = TEAMS_DATA[equipo_loc]
d_vis = TEAMS_DATA[equipo_vis]

# TARJETAS KPI SUPERIORES QUE SE ACTUALIZAN DINÁMICAMENTE CON LOS EQUIPOS ELEGIDOS
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

# TABLA DE COMPARACIÓN DINÁMICA
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
# TABLA DE MEJORES OPORTUNIDADES (SIN ERRORES DE CLAVE ÚNICA)
# ==============================================================================
st.markdown("<h3 style='color:#0b4f30; font-size:1.1rem; font-weight:900;'>📊 MEJORES OPORTUNIDADES DETECTADAS (PROBABILIDAD >= 60%)</h3>", unsafe_allow_html=True)

lambda_h = d_loc['xg']
lambda_a = d_vis['xg']
prob_over25 = 1.0 - poisson.cdf(2, lambda_h + lambda_a)
prob_btts = 0.68
prob_corners = 0.76

oportunidades = [
    {"id": "op_corners", "mercado": "Córners Totales > 9.5", "prob": prob_corners, "cuota": "1.85", "badge": "💎 APUESTA ESTRELLA"},
    {"id": "op_btts", "mercado": "Ambos Equipos Anotan (BTTS SÍ)", "prob": prob_btts, "cuota": "1.72", "badge": "HIGH CONFIDENCE"},
    {"id": "op_goles", "mercado": "Total de Goles Over 2.5", "prob": prob_over25, "cuota": "1.90", "badge": "MEDIUM PROBABILITY"}
]

for op in oportunidades:
    st.markdown(f"""
    <div style="background-color:#ffffff; border:1px solid #d1e2da; border-radius:8px; padding:12px 18px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="font-weight:900; font-size:0.95rem; color:#0b4f30;">↗ {op['mercado']}</span>
            <div style="font-size:0.78rem; color:#607d71;">Probabilidad Estimada: <b>{op['prob']*100:.1f}%</b> | Cuota Sugerida: <b>@{op['cuota']}</b></div>
        </div>
        <div style="display:flex; align-items:center; gap:15px;">
            <span style="background-color:#059669; color:#ffffff; padding:4px 10px; border-radius:4px; font-weight:900; font-size:0.75rem;">{op['badge']}</span>
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
        # SE ASIGNA UNA KEY ÚNICA A CADA PLOTLY_CHART PARA EVITAR EL StreamlitDuplicateElementId
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{op['id']}_{equipo_loc}_{equipo_vis}")
