import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página - Light Mode Estilo Ricky Picks
st.set_page_config(
    page_title="LA MAÑA PICKS - IA & ANÁLISIS ESTADÍSTICO",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS - INSPIRACIÓN RICKYPICKS.COM.MX (CLEAN LIGHT MODE)
st.markdown("""
<style>
    /* Fondo Claro Elegante */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    header {visibility: hidden;}

    /* Top Navigation Bar */
    .nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .brand-logo {
        font-size: 1.8rem;
        font-weight: 900;
        color: #1e40af !important;
        letter-spacing: -1px;
    }

    /* Hero Headline */
    .hero-title {
        font-size: 3.2rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        letter-spacing: -1.5px;
        margin-bottom: 10px;
    }
    .hero-highlight {
        color: #2563eb !important;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 25px;
    }

    /* Simulación Card Banner */
    .sim-card {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
    }
    .sim-title {
        font-size: 1.8rem;
        font-weight: 900;
        color: #1e3a8a;
        margin-bottom: 5px;
    }

    /* Veredict Badges */
    .verdict-badge {
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 0.82rem;
        letter-spacing: 0.5px;
        display: inline-block;
        text-align: center;
    }
    .v-bet { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .v-maybe { background-color: #dbeafe; color: #1d4ed8; border: 1px solid #93c5fd; }
    .v-skip { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

    /* Tarjetas de Mercado Clean */
    .market-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    .market-card:hover {
        border-color: #93c5fd;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.06);
    }

    /* Inputs para Momios estilo RickyPicks */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# BASE DE DATOS DE EQUIPOS DE PRUEBA
# ------------------------------------------------------------------------------
PREMIER_LEAGUE_DATA = {
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg": 2.10, "xga": 0.85, "corners": 6.8},
    "Brentford": {"logo": "https://crests.football-data.org/402.png", "xg": 1.50, "xga": 1.45, "corners": 4.6},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg": 1.80, "xga": 1.25, "corners": 5.6},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg": 2.20, "xga": 1.00, "corners": 7.1},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg": 2.25, "xga": 0.80, "corners": 7.5},
    "Tottenham": {"logo": "https://crests.football-data.org/73.png", "xg": 1.85, "xga": 1.50, "corners": 6.3}
}

LALIGA_DATA = {
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg": 2.30, "xga": 0.95, "corners": 6.9},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg": 2.35, "xga": 0.80, "corners": 7.2},
    "Atlético de Madrid": {"logo": "https://crests.football-data.org/78.png", "xg": 1.85, "xga": 0.90, "corners": 5.8},
    "Athletic": {"logo": "https://crests.football-data.org/77.png", "xg": 1.60, "xga": 1.10, "corners": 5.9}
}

# ------------------------------------------------------------------------------
# FUNCIONES MATEMÁTICAS & SIMULACIÓN MONTE CARLO (10,000 SIMULACIONES)
# ------------------------------------------------------------------------------
def simular_partido_montecarlo(lambda_local, lambda_visita, n_simulaciones=10000):
    goles_local = np.random.poisson(lambda_local, n_simulaciones)
    goles_visita = np.random.poisson(lambda_visita, n_simulaciones)
    
    prob_local = np.mean(goles_local > goles_visita)
    prob_empate = np.mean(goles_local == goles_visita)
    prob_visita = np.mean(goles_local < goles_visita)
    
    prob_over25 = np.mean((goles_local + goles_visita) > 2.5)
    prob_btts = np.mean((goles_local > 0) & (goles_visita > 0))
    
    return {
        "p_local": prob_local,
        "p_empate": prob_empate,
        "p_visita": prob_visita,
        "p_over25": prob_over25,
        "p_btts": prob_btts
    }

def parse_odds(val_str):
    try:
        val = float(val_str)
        return val if val > 1.0 else 2.00
    except:
        return 2.00

def calcular_ev(prob, cuota):
    return (prob * cuota) - 1.0

def obtener_veredicto(ev):
    if ev >= 0.05:
        return "BET", "v-bet", "Entra — El casino paga más de lo que debería."
    elif 0.00 <= ev < 0.05:
        return "MAYBE", "v-maybe", "Tú decides — Hay ventaja leve, sirve para combinadas."
    return "SKIP", "v-skip", "Déjala pasar — Sin ventaja sobre el mercado."

# ------------------------------------------------------------------------------
# BARRA DE NAVEGACIÓN Y HERO SECTION
# ------------------------------------------------------------------------------
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#2563eb;">PICKS</span></div>
    <div style="font-weight:700; color:#475569; font-size:0.9rem;">MODELO DE SIMULACIÓN ESTADÍSTICA</div>
</div>
""", unsafe_allow_html=True)

hero_col, sim_col = st.columns([6, 6])

with hero_col:
    st.markdown("""
    <div class="hero-title">El modelo cuantitativo que <span class="hero-highlight">encuentra el valor</span>.</div>
    <div class="hero-subtitle">Deja de adivinar parlays. Analiza la probabilidad cruda contra los momios de tu casino.</div>
    """, unsafe_allow_html=True)
    
    liga_sel = st.selectbox("Selecciona Liga a Analizar:", ["Premier League", "LaLiga EA Sports"])

with sim_col:
    st.markdown("""
    <div class="sim-card">
        <div class="sim-title">Cada juego simulado <br><span style="color:#2563eb;">10,000 veces</span></div>
        <p style="color:#64748b; font-size:0.88rem; margin-top:8px;">
            Ejecutamos algoritmos estocásticos de Poisson y simulación de Monte Carlo para obtener probabilidades libres de sesgo.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SELECCIÓN DE ENCUENTRO Y CONFIGURACIÓN PARALELA
# ------------------------------------------------------------------------------
TEAMS_DATA = PREMIER_LEAGUE_DATA if "Premier" in liga_sel else LALIGA_DATA

col_left_inputs, col_right_results = st.columns([6, 6])

with col_left_inputs:
    st.markdown("<h3 style='color:#0f172a; font-size:1.2rem; font-weight:800;'>⚙️ 1. Configura el Partido y tus Momios</h3>", unsafe_allow_html=True)
    
    c_loc, c_vis = st.columns(2)
    with c_loc: eq_loc = st.selectbox("Equipo Local:", list(TEAMS_DATA.keys()), index=0)
    with c_vis: eq_vis = st.selectbox("Equipo Visitante:", list(TEAMS_DATA.keys()), index=1 if len(TEAMS_DATA)>1 else 0)
    
    d_loc, d_vis = TEAMS_DATA[eq_loc], TEAMS_DATA[eq_vis]
    
    # Simulación en tiempo real
    res_sim = simular_partido_montecarlo(d_loc['xg'], d_vis['xg'])
    
    st.markdown("<p style='font-size:0.9rem; font-weight:700; color:#475569; margin-top:15px;'>Ingresa los momios de tu casino (Decimales):</p>", unsafe_allow_html=True)
    
    c_1, c_x, c_2 = st.columns(3)
    with c_1: odds_1 = st.text_input(f"1X2 {eq_loc[:3]}", value="2.10")
    with c_x: odds_x = st.text_input("1X2 Empate", value="3.40")
    with c_2: odds_2 = st.text_input(f"1X2 {eq_vis[:3]}", value="3.50")
    
    c_o25, c_btts = st.columns(2)
    with c_o25: odds_o25 = st.text_input("Total Over 2.5 Goles", value="1.90")
    with c_btts: odds_btts = st.text_input("Ambos Anotan (BTTS SÍ)", value="1.75")

# ------------------------------------------------------------------------------
# COLUMNA DERECHA: RESULTADOS ESTILO RICKYPICKS (BET / MAYBE / SKIP)
# ------------------------------------------------------------------------------
with col_right_results:
    st.markdown("<h3 style='color:#0f172a; font-size:1.2rem; font-weight:800;'>📊 2. Veredicto del Modelo vs Casino</h3>", unsafe_allow_html=True)
    
    mercados_evaluar = [
        {"nombre": f"Resultado Final: Gana {eq_loc}", "prob": res_sim['p_local'], "cuota": parse_odds(odds_1)},
        {"nombre": "Resultado Final: Empate", "prob": res_sim['p_empate'], "cuota": parse_odds(odds_x)},
        {"nombre": f"Resultado Final: Gana {eq_vis}", "prob": res_sim['p_visita'], "cuota": parse_odds(odds_2)},
        {"nombre": "Total de Goles: Over 2.5", "prob": res_sim['p_over25'], "cuota": parse_odds(odds_o25)},
        {"nombre": "Ambos Equipos Anotan: SÍ", "prob": prob_btts := res_sim['p_btts'], "cuota": parse_odds(odds_btts)}
    ]
    
    for item in mercados_evaluar:
        ev = calcular_ev(item['prob'], item['cuota'])
        tag, css_class, desc = obtener_veredicto(ev)
        cuota_justa = 1.0 / item['prob'] if item['prob'] > 0 else 2.0
        
        st.markdown(f"""
        <div class="market-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-weight:800; font-size:1rem; color:#0f172a;">{item['nombre']}</span>
                    <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">
                        Prob. IA: <b>{item['prob']*100:.1f}%</b> | Momio Justo: <b>@{cuota_justa:.2f}</b> | Tu Casa: <b>@{item['cuota']:.2f}</b>
                    </div>
                </div>
                <div>
                    <span class="verdict-badge {css_class}">{tag}</span>
                </div>
            </div>
            <div style="font-size:0.75rem; color:#475569; margin-top:8px; border-top:1px solid #f1f5f9; padding-top:6px;">
                {desc} (Ventaja EV: <b>{ev*100:+.1f}%</b>)
            </div>
        </div>
        """, unsafe_allow_html=True)
