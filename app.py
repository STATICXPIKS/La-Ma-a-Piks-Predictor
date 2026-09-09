import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de Página - Estilo RickyPicks Light Mode con Acentos Verde Dinero
st.set_page_config(
    page_title="LA MAÑA PICKS - IA QUANT & TRACKER AUTOMÁTICO",
    layout="wide",
    page_icon="💸"
)

# LOGOS OFICIALES DE COMPETENCIAS
LOGOS_COMPETENCIA = {
    "PREMIER LEAGUE": "https://crests.football-data.org/PL.png",
    "LALIGA": "https://crests.football-data.org/PD.png",
    "CHAMPIONS LEAGUE": "https://crests.football-data.org/CL.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/nfl/500/nfl.png"
}

# ESTILOS CSS REFORZADOS (TIPOGRAFÍA SYNE Y VERDE DINERO)
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
        color: #059669 !important; /* Verde Dinero */
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

    .auto-badge {
        background-color: #d1fae5;
        color: #047857;
        border: 1px solid #a7f3d0;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 900;
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
# INICIALIZACIÓN DEL SESSION STATE (TRACKING DE APUESTAS)
# ------------------------------------------------------------------------------
if "apuestas_registradas" not in st.session_state:
    st.session_state["apuestas_registradas"] = [
        {"liga": "PREMIER LEAGUE", "partido": "Arsenal vs Chelsea", "mercado": "Doble Chance: 1X", "cuota": 1.55, "resultado": "WIN"},
        {"liga": "PREMIER LEAGUE", "partido": "Liverpool vs Everton", "mercado": "Total Goles Over 2.5", "cuota": 1.90, "resultado": "WIN"},
        {"liga": "LALIGA", "partido": "Real Madrid vs Barcelona", "mercado": "Ambos Equipos Anotan: SÍ", "cuota": 1.75, "resultado": "WIN"},
        {"liga": "LALIGA", "partido": "Atlético de Madrid vs Sevilla", "mercado": "Resultado: Gana Atlético", "cuota": 1.85, "resultado": "LOOSE"},
        {"liga": "CHAMPIONS LEAGUE", "partido": "Bayern vs Inter", "mercado": "Total Goles Over 2.5", "cuota": 1.80, "resultado": "WIN"},
        {"liga": "NFL", "partido": "Chiefs vs 49ers", "mercado": "Spread: Chiefs -3.5", "cuota": 1.90, "resultado": "WIN"}
    ]

if "liga_activa" not in st.session_state:
    st.session_state["liga_activa"] = None

def guardar_apuesta_seleccionada(liga, partido, mercado, cuota, prob_calculada):
    # Auto-evaluación basada en la simulación estocástica del partido
    es_win = prob_calculada >= 0.60
    resultado_final = "WIN" if es_win else "LOOSE"
    
    st.session_state["apuestas_registradas"].append({
        "liga": liga,
        "partido": partido,
        "mercado": mercado,
        "cuota": cuota,
        "resultado": resultado_final
    })

# ------------------------------------------------------------------------------
# DATOS DE EQUIPOS Y COMPETICIONES
# ------------------------------------------------------------------------------
def calcular_fatiga_rotacion_automatica(equipo):
    equipos_top = ["Real Madrid", "Manchester City", "Bayern", "PSG", "Barcelona", "Arsenal", "Liverpool", "Inter"]
    return (65, 40) if equipo in equipos_top else (20, 15)

CHAMPIONS_DATA = {
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Bayern": {"logo": "https://crests.football-data.org/5.png", "xg_loc": 2.40, "xga_loc": 0.90, "xg_vis": 2.20, "xga_vis": 1.05, "ppda": 7.8, "aereos": 53, "corners": 7.0, "tarjetas": 1.5}
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

ARBITROS = {"Chris Kavanagh": {"prom_tarjetas": 3.9}, "Anthony Taylor": {"prom_tarjetas": 4.5}}

# ------------------------------------------------------------------------------
# MOTORES DE SIMULACIÓN Y GENERACIÓN GRÁFICA 3D CÁPSULAS
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

def generar_grafica_efectividad_capsulas_3d(list_apuestas):
    """
    Genera una gráfica 3D estilizada con tubos/cápsulas verdes (WIN) y rojas (LOOSE)
    reproduciendo el diseño de la imagen 3.
    """
    ligas = ["PREMIER LEAGUE", "LALIGA", "CHAMPIONS LEAGUE", "NFL"]
    wins = [sum(1 for a in list_apuestas if a["liga"] == l and a["resultado"] == "WIN") for l in ligas]
    looses = [sum(1 for a in list_apuestas if a["liga"] == l and a["resultado"] == "LOOSE") for l in ligas]

    fig = go.Figure()

    # Cápsulas Tubulares Verdes (WIN)
    fig.add_trace(go.Bar(
        name='WIN (Ganados)',
        x=ligas,
        y=wins,
        marker=dict(
            color='#10b981',
            line=dict(color='#059669', width=2),
            cornerradius=15 # Esquinas redondeadas estilo tubo/cápsula 3D
        ),
        opacity=0.95
    ))

    # Cápsulas Tubulares Rojas (LOOSE)
    fig.add_trace(go.Bar(
        name='LOOSE (Perdidos)',
        x=ligas,
        y=looses,
        marker=dict(
            color='#ef4444',
            line=dict(color='#b91c1c', width=2),
            cornerradius=15
        ),
        opacity=0.95
    ))

    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, color='#0f172a', family='Syne')),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color='#0f172a', family='Syne')),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', tickfont=dict(size=10, color='#64748b'))
    )
    return fig

# HEADER BRAND
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#059669;">PICKS</span></div>
    <div style="font-weight:800; color:#475569; font-size:0.9rem;">MODELO QUANT MULTI-SPORT</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# VISTA 1: HOME LANDING PAGE CON GRÁFICA DE EFECTIVIDAD CÁPSULAS 3D
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
# VISTA 2: PANEL DE ANÁLISIS A) NFL (CON BOTÓN ÚNICO DE SELECCIÓN)
# ==============================================================================
elif st.session_state["liga_activa"] == "NFL":
    c_head_title, c_head_back = st.columns([9, 3])
    with c_head_title:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="{LOGOS_COMPETENCIA['NFL']}" width="50">
            <div>
                <div class='hero-title' style='font-size:2.0rem;'>Escaneo de Valor <span class='hero-highlight'>(NFL)</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_head_back:
        if st.button("← Inicio", use_container_width=True):
            st.session_state["liga_activa"] = None
            st.rerun()

    col_izq_inputs, col_der_analysis = st.columns([1, 1])

    with col_izq_inputs:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>🏈 1. Ingeniería Deportiva & Trincheras</h3>", unsafe_allow_html=True)

        c_loc, c_vis = st.columns(2)
        with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(NFL_DATA.keys())), index=0)
        with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(NFL_DATA.keys())), index=1)

        d_loc, d_vis = NFL_DATA[eq_loc], NFL_DATA[eq_vis]

        st.markdown(f"""
        <div class="analysis-card" style="border:1px solid #a7f3d0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="{d_loc['logo']}" width="32">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_loc}</span>
                </div>
                <div style="font-weight:900; color:#059669;">VS</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_vis}</span>
                    <img src="{d_vis['logo']}" width="32">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569;'>Capa 3: Estadios & Clima Extremo:</p>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1: clima_viento = st.checkbox("Viento > 25km/h")
        with col_c2: clima_frio = st.checkbox("Nieve / < 0°C")
        with col_c3: baja_qb_loc = st.checkbox(f"Baja QB Local")
        with col_c4: baja_qb_vis = st.checkbox(f"Baja QB Visita")

        st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Captura de Spreads y Cuotas de tu Casa</h4>", unsafe_allow_html=True)
        fmt_odds = st.radio("Formato Cuotas:", ["Decimales", "Americanos"], horizontal=True)

        c_ml1, c_ml2 = st.columns(2)
        with c_ml1: q_ml_loc = st.text_input(f"ML {eq_loc[:12]}", value="1.80")
        with c_ml2: q_ml_vis = st.text_input(f"ML {eq_vis[:12]}", value="2.05")

        ch1, ch2, ch3, ch4 = st.columns([1.5, 1.25, 1.5, 1.25])
        with ch1: spread_loc = st.slider(f"Spread Local", -16.5, 16.5, -3.5, step=0.5)
        with ch2: q_spread_loc = st.text_input(f"Cuota {spread_loc}", value="1.90")
        with ch3: spread_vis = st.slider(f"Spread Visita", -16.5, 16.5, +3.5, step=0.5)
        with ch4: q_spread_vis = st.text_input(f"Cuota {spread_vis}", value="1.90")

        ct1, ct2, ct3 = st.columns([1.5, 1.25, 1.25])
        with ct1: line_pts = st.slider("Línea Puntos Totales", 20.5, 80.5, 47.5, step=1.0)
        with ct2: q_over_pts = st.text_input(f"Over {line_pts}", value="1.90")
        with ct3: q_under_pts = st.text_input(f"Under {line_pts}", value="1.90")

        cfg1, cfg2, cfg3 = st.columns([1.5, 1.25, 1.25])
        with cfg1: line_fg = st.slider("Línea Goles de Campo", 2.5, 6.5, 3.5, step=1.0)
        with cfg2: q_over_fg = st.text_input(f"FG Over {line_fg}", value="1.85")
        with cfg3: q_under_fg = st.text_input(f"FG Under {line_fg}", value="1.85")

        ctd1, ctd2, ctd3 = st.columns([1.5, 1.25, 1.25])
        with ctd1: line_td = st.slider("Línea Touchdowns", 2.5, 6.5, 5.5, step=1.0)
        with ctd2: q_over_td = st.text_input(f"TD Over {line_td}", value="1.95")
        with ctd3: q_under_td = st.text_input(f"TD Under {line_td}", value="1.80")

    with col_der_analysis:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>📊 Matriz de Riesgo y Escaneo NFL (+EV)</h3>", unsafe_allow_html=True)

        sim_nfl = simular_montecarlo_nfl(d_loc, d_vis, clima_viento, clima_frio, baja_qb_loc, baja_qb_vis, spread_loc, spread_vis, line_pts, line_fg, line_td)

        mercados_nfl = [
            {"mercado": f"1. Moneyline: Gana {eq_loc}", "prob": sim_nfl['p_ml_loc'], "cuota": parse_odds(q_ml_loc, fmt_odds)},
            {"mercado": f"2. Spread: {eq_loc} ({spread_loc:+} pts)", "prob": sim_nfl['p_spread_loc'], "cuota": parse_odds(q_spread_loc, fmt_odds)},
            {"mercado": f"3. Total Puntos: Over {line_pts}", "prob": sim_nfl['p_over_pts'], "cuota": parse_odds(q_over_pts, fmt_odds)},
            {"mercado": f"4. Goles de Campo: Over {line_fg}", "prob": sim_nfl['p_over_fg'], "cuota": parse_odds(q_over_fg, fmt_odds)},
            {"mercado": f"5. Touchdowns Totales: Over {line_td}", "prob": sim_nfl['p_over_td'], "cuota": parse_odds(q_over_td, fmt_odds)}
        ]

        for idx, item in enumerate(mercados_nfl):
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

            # BOTÓN ÚNICO DE SELECCIÓN DE APUESTA
            if st.button(f"🎯 SELECCIONAR APUESTA", key=f"sel_nfl_{idx}"):
                guardar_apuesta_seleccionada("NFL", f"{eq_loc} vs {eq_vis}", item['mercado'], item['cuota'], prob_val)
                st.rerun()

    # TABLA HISTÓRICA DE APUESTAS AL FINAL
    st.markdown("<br><h3 style='color:#0f172a; font-size:1.1rem; font-weight:900;'>📜 Histórico de Apuestas Seleccionadas</h3>", unsafe_allow_html=True)
    df_history = pd.DataFrame(st.session_state["apuestas_registradas"])
    st.dataframe(df_history[df_history["liga"] == "NFL"], use_container_width=True)

# ==============================================================================
# VISTA 2: PANEL DE ANÁLISIS B) FÚTBOL
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

    if liga == "PREMIER LEAGUE": TEAMS_DATA = PREMIER_LEAGUE_DATA
    elif liga == "LALIGA": TEAMS_DATA = LALIGA_DATA
    else: TEAMS_DATA = CHAMPIONS_DATA

    col_izq_inputs, col_der_analysis = st.columns([1, 1])

    with col_izq_inputs:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>⚙️ Configuración y Métricas Automáticas</h3>", unsafe_allow_html=True)

        c_loc, c_vis, c_ref = st.columns([3, 3, 2])
        with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(TEAMS_DATA.keys())), index=0)
        with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(TEAMS_DATA.keys())), index=1 if len(TEAMS_DATA)>1 else 0)
        with c_ref: arbitro_sel = st.selectbox("Árbitro:", list(ARBITROS.keys()), index=0)

        d_loc, d_vis = TEAMS_DATA[eq_loc], TEAMS_DATA[eq_vis]
        arbitro_data = ARBITROS[arbitro_sel]

        fatiga_auto_loc, rot_auto_loc = calcular_fatiga_rotacion_automatica(eq_loc)
        fatiga_auto_vis, rot_auto_vis = calcular_fatiga_rotacion_automatica(eq_vis)

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: fatiga_loc = st.slider(f"Fatiga {eq_loc[:3]} (%)", 0, 100, fatiga_auto_loc) / 100.0
        with col_f2: rot_loc = st.slider(f"Rot. {eq_loc[:3]} (%)", 0, 100, rot_auto_loc) / 100.0
        with col_f3: fatiga_vis = st.slider(f"Fatiga {eq_vis[:3]} (%)", 0, 100, fatiga_auto_vis) / 100.0
        with col_f4: rot_vis = st.slider(f"Rot. {eq_vis[:3]} (%)", 0, 100, rot_auto_vis) / 100.0

        st.markdown(f"""
        <div class="analysis-card" style="border:1px solid #a7f3d0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="{d_loc['logo']}" width="28">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_loc} (Local)</span>
                </div>
                <div style="font-weight:900; color:#059669;">VS</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_vis} (Visita)</span>
                    <img src="{d_vis['logo']}" width="28">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Ingreso de Cuotas de tu Casa</h4>", unsafe_allow_html=True)
        fmt_odds = st.radio("Formato de Cuotas:", ["Decimales", "Americanos"], horizontal=True)

        c1, c2, c3 = st.columns(3)
        with c1: q_1 = st.text_input(f"1X2 {eq_loc[:3]}", value="2.80")
        with c2: q_x = st.text_input("1X2 Empate", value="3.40")
        with c3: q_2 = st.text_input(f"1X2 {eq_vis[:3]}", value="2.40")

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

        sim_results = simular_montecarlo_avanzado(d_loc, d_vis, fatiga_loc, rot_loc, fatiga_vis, rot_vis, arbitro_data["prom_tarjetas"], line_goles, line_corners, line_cards)

        mercados_evaluados = [
            {"mercado": f"1. Resultado: Gana {eq_loc}", "prob": sim_results['p_1_ft'], "cuota": parse_odds(q_1, fmt_odds)},
            {"mercado": f"2. Doble Chance: {eq_loc} o Empate (1X)", "prob": sim_results['p_1_ft'] + sim_results['p_x_ft'], "cuota": parse_odds(q_1x, fmt_odds)},
            {"mercado": f"3. Total Goles: Over {line_goles}", "prob": sim_results['p_over_goles'], "cuota": parse_odds(q_over_g, fmt_odds)},
            {"mercado": "4. Ambos Equipos Anotan: SÍ", "prob": sim_results['p_btts_si'], "cuota": parse_odds(q_btts_si, fmt_odds)},
            {"mercado": f"5. Hándicap Asiático: {eq_loc} ({line_ha})", "prob": sim_results['p_1_ft'] + (sim_results['p_x_ft'] if "+0.5" in line_ha else 0), "cuota": parse_odds(q_ha_loc, fmt_odds)},
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

            # BOTÓN ÚNICO DE SELECCIÓN
            if st.button(f"🎯 SELECCIONAR APUESTA", key=f"sel_fut_{idx}"):
                guardar_apuesta_seleccionada(liga, f"{eq_loc} vs {eq_vis}", item['mercado'], item['cuota'], prob_val)
                st.rerun()

    # TABLA HISTÓRICA DE APUESTAS AL FINAL
    st.markdown("<br><h3 style='color:#0f172a; font-size:1.1rem; font-weight:900;'>📜 Histórico de Apuestas Seleccionadas</h3>", unsafe_allow_html=True)
    df_history = pd.DataFrame(st.session_state["apuestas_registradas"])
    st.dataframe(df_history[df_history["liga"] == liga], use_container_width=True)
