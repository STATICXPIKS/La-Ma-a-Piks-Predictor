import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests

# Configuración de Página - Estilo RickyPicks Light Mode con Acentos Verde Dinero
st.set_page_config(
    page_title="LA MAÑA PICKS - IA QUANT & TRACKER REAL",
    layout="wide",
    page_icon="💸"
)

# API KEY DE THE ODDS API (Ingresa tu clave gratuita)
ODDS_API_KEY = "TU_API_KEY_AQUI"

# LOGOS OFICIALES DE COMPETENCIAS
LOGOS_COMPETENCIA = {
    "PREMIER LEAGUE": "https://crests.football-data.org/PL.png",
    "LALIGA": "https://crests.football-data.org/PD.png",
    "CHAMPIONS LEAGUE": "https://crests.football-data.org/CL.png",
    "NFL": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg"
}

# MAPEO DE COMPETICIONES PARA THE ODDS API
SPORT_KEYS_ODDS_API = {
    "PREMIER LEAGUE": "soccer_epl",
    "LALIGA": "soccer_spain_la_liga",
    "CHAMPIONS LEAGUE": "soccer_uefa_champs_league",
    "NFL": "americanfootball_nfl"
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

    .trap-alert {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 800;
        margin-bottom: 15px;
    }

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
# FUNCIÓN DE CONSULTA HÍBRIDA A THE ODDS API
# ------------------------------------------------------------------------------
def obtener_momios_api(sport_key, eq_loc, eq_vis):
    if ODDS_API_KEY == "TU_API_KEY_AQUI":
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us,uk,eu&markets=h2h,totals,spreads"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            events = response.json()
            for event in events:
                home_team = event.get("home_team", "").lower()
                away_team = event.get("away_team", "").lower()
                if eq_loc.lower() in home_team and eq_vis.lower() in away_team:
                    bookmakers = event.get("bookmakers", [])
                    if bookmakers:
                        markets = bookmakers[0].get("markets", [])
                        momios = {}
                        for m in markets:
                            if m["key"] == "h2h":
                                for outcome in m["outcomes"]:
                                    if outcome["name"].lower() == home_team: momios["q1"] = outcome["price"]
                                    elif outcome["name"].lower() == away_team: momios["q2"] = outcome["price"]
                                    else: momios["qx"] = outcome["price"]
                        return momios
    except Exception as e:
        return None
    return None

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
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Bayern": {"logo": "https://crests.football-data.org/5.png", "xg_loc": 2.40, "xga_loc": 0.90, "xg_vis": 2.20, "xga_vis": 1.05, "ppda": 7.8, "aereos": 53, "corners": 7.0, "tarjetas": 1.5},
    "Fenerbahçe": {"logo": "https://crests.football-data.org/613.png", "xg_loc": 1.65, "xga_loc": 1.25, "xg_vis": 1.40, "xga_vis": 1.45, "ppda": 10.1, "aereos": 50, "corners": 5.5, "tarjetas": 2.5},
    "Roma": {"logo": "https://crests.football-data.org/100.png", "xg_loc": 1.55, "xga_loc": 1.25, "xg_vis": 1.30, "xga_vis": 1.45, "ppda": 11.1, "aereos": 51, "corners": 5.2, "tarjetas": 2.3}
}

PREMIER_LEAGUE_DATA = {
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg_loc": 1.80, "xga_loc": 1.25, "xg_vis": 1.60, "xga_vis": 1.40, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg_loc": 2.20, "xga_loc": 1.00, "xg_vis": 2.05, "xga_vis": 1.10, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3}
}

LALIGA_DATA = {
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg_loc": 2.30, "xga_loc": 0.95, "xg_vis": 2.10, "xga_vis": 1.05, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Atlético de Madrid": {"logo": "https://crests.football-data.org/78.png", "xg_loc": 1.85, "xga_loc": 0.90, "xg_vis": 1.55, "xga_vis": 1.10, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4}
}

NFL_DATA = {
    "Kansas City Chiefs": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "td_exp": 3.5, "fg_exp": 1.7},
    "San Francisco 49ers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "td_exp": 3.6, "fg_exp": 1.5},
    "Philadelphia Eagles": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "td_exp": 3.3, "fg_exp": 1.6}
}

ARBITROS_PREMIER = {"Anthony Taylor": {"prom_tarjetas": 4.5}, "Chris Kavanagh": {"prom_tarjetas": 3.9}}
ARBITROS_LALIGA = {"Jesús Gil Manzano": {"prom_tarjetas": 5.2}, "Ricardo De Burgos": {"prom_tarjetas": 4.1}}
ARBITROS_CHAMPIONS = {"Jesús Gil Manzano": {"prom_tarjetas": 5.2}, "Szymon Marciniak": {"prom_tarjetas": 4.1}}

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
    fig.add_trace(go.Bar(name='WIN', x=ligas, y=wins, marker=dict(color='#10b981', line=dict(color='#059669', width=2), cornerradius=15), opacity=0.95))
    fig.add_trace(go.Bar(name='LOOSE', x=ligas, y=looses, marker=dict(color='#ef4444', line=dict(color='#b91c1c', width=2), cornerradius=15), opacity=0.95))
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
# VISTA 2: PANEL DE ANÁLISIS HÍBRIDO (FÚTBOL Y NFL)
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
            with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(TEAMS_DATA.keys())), index=0)
            with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(TEAMS_DATA.keys())), index=1)
        else:
            c_loc, c_vis, c_ref = st.columns([3, 3, 2])
            with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(TEAMS_DATA.keys())), index=0)
            with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(TEAMS_DATA.keys())), index=1)
            with c_ref: arbitro_sel = st.selectbox("Árbitro:", list(ARBITROS_LIGA.keys()), index=0)
            arbitro_data = ARBITROS_LIGA[arbitro_sel]

        d_loc, d_vis = TEAMS_DATA[eq_loc], TEAMS_DATA[eq_vis]

        # BOTÓN HÍBRIDO PARA AUTO-COMPLETAR MOMIOS DESDE LA API
        st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Ingreso de Cuotas (Híbrido API / Manual)</h4>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns([6, 6])
        with btn_col1:
            if st.button("⚡ Cargar Momios En Vivo (API)", use_container_width=True):
                sport_key = SPORT_KEYS_ODDS_API.get(liga, "")
                momios_api = obtener_momios_api(sport_key, eq_loc, eq_vis)
                if momios_api:
                    st.session_state[f"q1_{liga}"] = str(momios_api.get("q1", "2.80"))
                    st.session_state[f"qx_{liga}"] = str(momios_api.get("qx", "3.40"))
                    st.session_state[f"q2_{liga}"] = str(momios_api.get("q2", "2.40"))
                    st.success("¡Momios de la API cargados!")
                else:
                    st.warning("No se encontraron momios en vivo para este evento. Ingresa las cuotas manualmente.")

        fmt_odds = st.radio("Formato de Cuotas:", ["Decimales", "Americanos"], horizontal=True)

        val_q1 = st.session_state.get(f"q1_{liga}", "2.80")
        val_qx = st.session_state.get(f"qx_{liga}", "3.40")
        val_q2 = st.session_state.get(f"q2_{liga}", "2.40")

        c1, c2, c3 = st.columns(3)
        with c1: q_1 = st.text_input(f"1X2 {eq_loc[:3]}", value=val_q1, key=f"q1_input_{liga}")
        with c2: q_x = st.text_input("1X2 Empate", value=val_qx, key=f"qx_input_{liga}")
        with c3: q_2 = st.text_input(f"1X2 {eq_vis[:3]}", value=val_q2, key=f"q2_input_{liga}")

        c4, c5, c6 = st.columns(3)
        with c4: q_1x = st.text_input("DC 1X", value="1.55")
        with c5: q_x2 = st.text_input("DC X2", value="1.42")
        with c6: q_12 = st.text_input("DC 12", value="1.30")

        cg1, cg2, cg3 = st.columns([1.5, 1.25, 1.25])
        with cg1: line_goles = st.slider("Línea Goles / Puntos FT", 1.5, 80.5, 2.5, step=1.0)
        with cg2: q_over_g = st.text_input(f"Over {line_goles}", value="1.90")
        with cg3: q_under_g = st.text_input(f"Under {line_goles}", value="1.90")

    with col_der_analysis:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>📊 Matriz de Riesgo y Escaneo (+EV)</h3>", unsafe_allow_html=True)

        if liga == "NFL":
            sim_results = simular_montecarlo_nfl(d_loc, d_vis, False, False, False, False, -3.5, 3.5, line_goles, 3.5, 5.5)
        else:
            sim_results = simular_montecarlo_avanzado(d_loc, d_vis, 0.2, 0.15, 0.2, 0.15, arbitro_data["prom_tarjetas"], line_goles, 9.5, 4.5)

        mercados_evaluados = [
            {"mercado": f"1. Resultado: Gana {eq_loc}", "prob": sim_results.get('p_1_ft', sim_results.get('p_ml_loc', 0.5)), "cuota": parse_odds(q_1, fmt_odds)},
            {"mercado": f"1. Resultado: Empate", "prob": sim_results.get('p_x_ft', 0.2), "cuota": parse_odds(q_x, fmt_odds)},
            {"mercado": f"1. Resultado: Gana {eq_vis}", "prob": sim_results.get('p_2_ft', sim_results.get('p_ml_vis', 0.3)), "cuota": parse_odds(q_2, fmt_odds)},
            {"mercado": f"2. Doble Chance: {eq_loc} o Empate (1X)", "prob": sim_results.get('p_1_ft', 0.5) + sim_results.get('p_x_ft', 0.2), "cuota": parse_odds(q_1x, fmt_odds)},
            {"mercado": f"2. Doble Chance: {eq_vis} o Empate (X2)", "prob": sim_results.get('p_2_ft', 0.3) + sim_results.get('p_x_ft', 0.2), "cuota": parse_odds(q_x2, fmt_odds)},
            {"mercado": f"3. Total Goles/Puntos: Over {line_goles}", "prob": sim_results.get('p_over_goles', sim_results.get('p_over_pts', 0.5)), "cuota": parse_odds(q_over_g, fmt_odds)}
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

            if st.button(f"🎯 SELECCIONAR APUESTA", key=f"sel_{liga}_{idx}"):
                guardar_apuesta_seleccionada(liga, f"{eq_loc} vs {eq_vis}", item['mercado'], item['cuota'])
                st.rerun()

            with st.expander(f"📈 Ver Tendencia de Cobertura de Línea (Últimos 15 Partidos)"):
                fig_mini = generar_grafica_mini_15_partidos(prob_val)
                st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_mini_{liga}_{idx}")

    # GESTIÓN E HISTORIAL INTERACTIVO CON ESTADO PENDIENTE REAL
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
