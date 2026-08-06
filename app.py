import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import requests
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y TEMA NEÓN
# ==========================================
st.set_page_config(
    page_title="PROPS MLB ANALYTICS - PROPS BR STYLE",
    layout="wide",
    page_icon="⚾",
    initial_sidebar_state="collapsed"
)

# Estilos CSS Personalizados para replicar PROPS BR
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #080a0c !important;
        color: #e2e8f0;
    }

    .stApp {
        background-color: #080a0c !important;
    }

    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Barra Superior Deportes */
    .nav-sports {
        display: flex;
        gap: 12px;
        border-bottom: 1px solid #1a2026;
        padding-bottom: 10px;
        margin-bottom: 15px;
        overflow-x: auto;
    }
    .sport-chip {
        color: #718096;
        font-weight: 700;
        font-size: 14px;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
    }
    .sport-chip.active {
        color: #00ff66;
        border-bottom: 3px solid #00ff66;
    }

    /* Chips de Filtros Rápidos */
    .filter-badge {
        background-color: #12171c;
        border: 1px solid #232d35;
        color: #a0aec0;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .filter-badge.active-green {
        background-color: #00ff66 !important;
        color: #000000 !important;
        border: none !important;
    }
    .filter-badge.gold {
        border: 1px solid #e2b13c;
        color: #e2b13c;
    }

    /* Tarjetas de Props (Estilo PROPS BR) */
    .prop-card {
        background-color: #0e1217;
        border: 1px solid #1a2228;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: transform 0.2s, border-color 0.2s;
    }
    .prop-card:hover {
        border-color: #00ff66;
        transform: translateY(-2px);
    }

    /* Sección Jugador / Prop */
    .player-title {
        font-size: 16px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 2px;
    }
    .player-team {
        font-size: 12px;
        color: #718096;
        font-weight: 600;
    }

    /* Cuotas y Mercado Chips */
    .line-chip {
        background-color: #172019;
        border: 1px solid #223825;
        color: #00ff66;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .odd-chip {
        background-color: #2b2311;
        border: 1px solid #4a3812;
        color: #ffc800;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 900;
    }

    /* Columnas de Métricas */
    .metric-val {
        font-size: 14px;
        font-weight: 800;
        text-align: center;
    }
    .metric-val.green { color: #00ff66; }
    .metric-val.gold { color: #ffc800; }
    .metric-val.red { color: #ff3355; }
    .metric-label {
        font-size: 10px;
        color: #4a5568;
        font-weight: 800;
        text-transform: uppercase;
        text-align: center;
    }

    /* Gráfico de Barras Sparkline (Historial L10) */
    .sparkbar-container {
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 38px;
    }
    .sparkbar {
        width: 6px;
        border-radius: 2px;
    }
    .sparkbar.hit { background-color: #00ff66; }
    .sparkbar.miss { background-color: #ff3355; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNCIONES AUXILIARES Y API MLB
# ==========================================
@st.cache_data(ttl=1800)
def cargar_props_mlb_demo():
    """
    Simula / Genera el Feed de Player Props Sabermétricos
    con historial de últimos 10 juegos (L10)
    """
    props = [
        {
            "jugador": "Juan Soto", "equipo": "NYM, LE",
            "mercado": "Rebatidas (Hits)", "linea": 0.5, "odd": 1.38,
            "vant": "+0.9", "match": "A+", "conf": 85,
            "l10": [1, 1, 0, 1, 1, 1, 1, 0, 1, 1]
        },
        {
            "jugador": "Elly De La Cruz", "equipo": "CIN, SH",
            "mercado": "Rebatidas (Hits)", "linea": 0.5, "odd": 1.35,
            "vant": "+0.8", "match": "A+", "conf": 85,
            "l10": [1, 1, 1, 0, 1, 1, 1, 1, 0, 1]
        },
        {
            "jugador": "Shohei Ohtani", "equipo": "LAD, DH",
            "mercado": "Bases Totales", "linea": 1.5, "odd": 1.85,
            "vant": "+1.2", "match": "A+", "conf": 82,
            "l10": [1, 1, 0, 1, 1, 1, 1, 1, 0, 1]
        },
        {
            "jugador": "Bo Bichette", "equipo": "TOR, SS",
            "mercado": "Rebatidas (Hits)", "linea": 0.5, "odd": 1.26,
            "vant": "+0.3", "match": "A", "conf": 80,
            "l10": [0, 1, 1, 1, 1, 0, 1, 1, 1, 1]
        },
        {
            "jugador": "Paul Skenes", "equipo": "PIT, SP",
            "mercado": "Ponches (Strikeouts)", "linea": 6.5, "odd": 1.77,
            "vant": "+1.4", "match": "A+", "conf": 84,
            "l10": [1, 1, 1, 1, 0, 1, 1, 1, 1, 1]
        },
        {
            "jugador": "Aaron Judge", "equipo": "NYY, RF",
            "mercado": "Home Runs", "linea": 0.5, "odd": 3.10,
            "vant": "+0.4", "match": "B+", "conf": 72,
            "l10": [1, 0, 1, 0, 0, 1, 1, 0, 1, 0]
        },
        {
            "jugador": "Hunter Goodman", "equipo": "COL, C",
            "mercado": "Rebatidas (Hits)", "linea": 0.5, "odd": 1.42,
            "vant": "+0.9", "match": "A+", "conf": 75,
            "l10": [0, 0, 1, 1, 1, 0, 1, 1, 0, 1]
        }
    ]
    return props

def render_sparkbar_html(l10_list):
    """
    Genera el HTML de las barritas verde/rojo para el historial L10
    """
    html = '<div class="sparkbar-container">'
    for val in l10_list:
        cls = "hit" if val == 1 else "miss"
        # Generar alturas variadas para simular stats más altas/bajas
        h = 32 if val == 1 else 14
        html += f'<div class="sparkbar {cls}" style="height: {h}px;"></div>'
    html += '</div>'
    return html

# ==========================================
# INTERFAZ PRINCIPAL (UI NATIVA PROPS BR)
# ==========================================

# 1. Barra Superior de Navegación
st.markdown("""
<div class="nav-sports">
    <span class="sport-chip">NBA</span>
    <span class="sport-chip">NCAAB</span>
    <span class="sport-chip">NHL</span>
    <span class="sport-chip">Futebol</span>
    <span class="sport-chip">Tennis</span>
    <span class="sport-chip active">⚾ MLB PROPS</span>
</div>
""", unsafe_allow_html=True)

# 2. Chips de Filtros Rápidos (LIVE, TODOS, MEJOR DEL DÍA)
f_col1, f_col2, f_col3, f_col4 = st.columns([1, 1, 1, 2])

with f_col1:
    st.markdown('<span class="filter-badge active-green">● LIVE / HOY</span>', unsafe_allow_html=True)
with f_col2:
    st.markdown('<span class="filter-badge gold">⭐ MEJOR DEL DÍA</span>', unsafe_allow_html=True)
with f_col3:
    st.markdown('<span class="filter-badge gold">🔥 10 MEJORES</span>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 3. Barra de Búsqueda y Parámetros
c_search, c_mercado, c_sort = st.columns([2, 1, 1])

with c_search:
    query = st.text_input("", placeholder="🔍 Buscar Jugadores o Equipos MLB...", label_visibility="collapsed")
with c_mercado:
    filtro_mercado = st.selectbox("Mercado", ["Todos", "Hits", "Home Runs", "Strikeouts", "Bases Totales"], label_visibility="collapsed")
with c_sort:
    orden = st.selectbox("Ordenar Por", ["Mayor Confianza %", "Mayor Ventaja (+VANT)", "Momio Elevado"], label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Cargar y Filtrar Feed de Props
all_props = cargar_props_mlb_demo()

# Renderizado de Tarjetas de Props (Feed Principal)
for prop in all_props:
    # Filtrado básico por búsqueda
    if query and query.lower() not in prop["jugador"].lower() and query.lower() not in prop["equipo"].lower():
        continue

    # Tarjeta Renderizada
    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.2, 0.8, 0.8, 0.8, 1.8])

    with c1:
        st.markdown(f"""
        <div>
            <div class="player-title">{prop['jugador']}</div>
            <div class="player-team">{prop['equipo']}</div>
            <div style="margin-top: 6px;">
                <span class="line-chip">↑ O {prop['linea']} {prop['mercado']}</span>
                <span class="odd-chip">{prop['odd']:.2f} ↗</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.write("") # Espaciador

    with c3:
        st.markdown(f"""
        <div class="metric-label">VANT</div>
        <div class="metric-val green">{prop['vant']}</div>
        """, unsafe_allow_html=True)

    with c4:
        match_color = "green" if "A" in prop['match'] else "gold"
        st.markdown(f"""
        <div class="metric-label">MATCH</div>
        <div class="metric-val {match_color}">{prop['match']}</div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown(f"""
        <div class="metric-label">CONF</div>
        <div class="metric-val green">{prop['conf']}%</div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
        <div style="text-align: right;">
            <div class="metric-label" style="text-align: right; margin-bottom: 4px;">HISTORIAL (L10)</div>
            {render_sparkbar_html(prop['l10'])}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 8px 0; border:0; border-top:1px solid #141a20;'>", unsafe_allow_html=True)

# 5. Barra Flotante Inferior de Modos de Análisis (H2H, DvP, L5, L10)
st.markdown("<br><br>", unsafe_allow_html=True)
b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns(5)

with b_col1:
    st.button("📊 H2H Directo", use_container_width=True)
with b_col2:
    st.button("🛡️ DvP (Pitcher vs Bateador)", use_container_width=True)
with b_col3:
    st.button("🔥 ÚLTIMOS 5 (L5)", use_container_width=True)
with b_col4:
    st.button("🟢 ÚLTIMOS 10 (L10)", type="primary", use_container_width=True)
with b_col5:
    st.button("📋 Tracker de Apuestas", use_container_width=True)
