import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de Página - Estilo RickyPicks Light Mode
st.set_page_config(
    page_title="LA MAÑA PICKS - IA QUANT & NFL 32 TEAMS",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS REFORZADOS
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    header {visibility: hidden;}

    .nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .brand-logo {
        font-size: 2rem;
        font-weight: 900;
        color: #1e40af !important;
        letter-spacing: -1px;
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.05;
        letter-spacing: -1.8px;
        margin-bottom: 10px;
    }
    .hero-highlight { color: #2563eb !important; }
    .hero-subtitle { font-size: 1.1rem; color: #64748b; font-weight: 500; margin-bottom: 25px; }

    .sim-card-home {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 20px;
        padding: 40px 24px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.12);
    }
    .sim-card-title {
        font-size: 2.8rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 10px;
    }

    .badge-high { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-medium { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-low { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-star { background-color: #fef9c3; color: #a16207; border: 1.5px solid #fde047; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-size: 0.80rem; box-shadow: 0 0 8px rgba(234, 179, 8, 0.4); }

    .trap-alert {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-bottom: 15px;
    }

    .analysis-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 6px;
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
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    .stButton>button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 14px 20px !important;
        text-align: left !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        border-color: #2563eb !important;
        color: #2563eb !important;
        background-color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# BASE DE DATOS COMPLETA DE LA NFL (LOS 32 EQUIPOS - AFC & NFC)
# ------------------------------------------------------------------------------
NFL_DATA = {
    # --- CONFERENCIA AMERICANA (AFC) ---
    # AFC Este
    "Miami Dolphins": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "td_exp": 3.2, "fg_exp": 1.5},
    "New York Jets": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "td_exp": 2.5, "fg_exp": 2.1},
    "Buffalo Bills": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "td_exp": 3.4, "fg_exp": 1.6},
    "New England Patriots": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png", "td_exp": 2.2, "fg_exp": 1.9},
    
    # AFC Norte
    "Cincinnati Bengals": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png", "td_exp": 3.1, "fg_exp": 1.8},
    "Pittsburgh Steelers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png", "td_exp": 2.4, "fg_exp": 2.2},
    "Cleveland Browns": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png", "td_exp": 2.5, "fg_exp": 2.0},
    "Baltimore Ravens": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "td_exp": 3.5, "fg_exp": 1.7},

    # AFC Sur
    "Indianapolis Colts": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png", "td_exp": 2.8, "fg_exp": 1.8},
    "Houston Texans": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png", "td_exp": 2.9, "fg_exp": 1.9},
    "Tennessee Titans": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png", "td_exp": 2.3, "fg_exp": 2.0},
    "Jacksonville Jaguars": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png", "td_exp": 2.7, "fg_exp": 1.8},

    # AFC Oeste
    "Los Angeles Chargers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png", "td_exp": 2.8, "fg_exp": 1.9},
    "Kansas City Chiefs": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "td_exp": 3.5, "fg_exp": 1.7},
    "Las Vegas Raiders": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png", "td_exp": 2.3, "fg_exp": 2.1},
    "Denver Broncos": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png", "td_exp": 2.4, "fg_exp": 2.0},

    # --- CONFERENCIA NACIONAL (NFC) ---
    # NFC Este
    "New York Giants": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png", "td_exp": 2.1, "fg_exp": 2.0},
    "Washington Commanders": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png", "td_exp": 2.7, "fg_exp": 1.8},
    "Philadelphia Eagles": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "td_exp": 3.3, "fg_exp": 1.6},
    "Dallas Cowboys": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "td_exp": 3.2, "fg_exp": 1.9},

    # NFC Norte
    "Minnesota Vikings": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png", "td_exp": 2.9, "fg_exp": 1.8},
    "Chicago Bears": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png", "td_exp": 2.5, "fg_exp": 1.9},
    "Green Bay Packers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png", "td_exp": 3.0, "fg_exp": 1.7},
    "Detroit Lions": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "td_exp": 3.4, "fg_exp": 1.6},

    # NFC Sur
    "New Orleans Saints": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png", "td_exp": 2.6, "fg_exp": 2.0},
    "Tampa Bay Buccaneers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "td_exp": 2.8, "fg_exp": 1.8},
    "Atlanta Falcons": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png", "td_exp": 2.7, "fg_exp": 1.9},
    "Carolina Panthers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png", "td_exp": 2.0, "fg_exp": 2.1},

    # NFC Oeste
    "Los Angeles Rams": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png", "td_exp": 3.0, "fg_exp": 1.7},
    "Seattle Seahawks": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png", "td_exp": 2.7, "fg_exp": 1.9},
    "Arizona Cardinals": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png", "td_exp": 2.5, "fg_exp": 2.0},
    "San Francisco 49ers": {"logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "td_exp": 3.6, "fg_exp": 1.5}
}

# ------------------------------------------------------------------------------
# MOTOR MONTE CARLO Y FUNCIONES AUXILIARES
# ------------------------------------------------------------------------------
def simular_montecarlo_nfl(d_loc, d_vis, clima_viento, clima_frio, baja_qb_loc, baja_qb_vis, spread_loc, spread_vis, line_pts, line_fg, line_td, n_sim=10000):
    factor_clima = 1.0
    if clima_viento: factor_clima -= 0.15
    if clima_frio: factor_clima -= 0.10

    factor_qb_loc = 0.75 if baja_qb_loc else 1.0
    factor_qb_vis = 0.75 if baja_qb_vis else 1.0

    exp_td_loc = d_loc.get("td_exp", 3.0) * factor_qb_loc * factor_clima
    exp_td_vis = d_vis.get("td_exp", 2.8) * factor_qb_vis * factor_clima

    exp_fg_loc = d_loc.get("fg_exp", 1.8) * (0.7 if clima_viento else 1.0)
    exp_fg_vis = d_vis.get("fg_exp", 1.7) * (0.7 if clima_viento else 1.0)

    sim_td_loc = np.random.poisson(exp_td_loc, n_sim)
    sim_td_vis = np.random.poisson(exp_td_vis, n_sim)
    sim_fg_loc = np.random.poisson(exp_fg_loc, n_sim)
    sim_fg_vis = np.random.poisson(exp_fg_vis, n_sim)

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

def parse_odds(val_str, fmt_type):
    try:
        val = float(val_str)
        if fmt_type == "Decimales": return val if val > 1.0 else 2.00
        return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def generar_grafica_mini_15_partidos(prob_exito):
    data = np.random.choice([1, 0], size=15, p=[prob_exito, 1 - prob_exito])
    colors = ['#10b981' if x == 1 else '#ef4444' for x in data]
    labels = [f"P{i+1}" for i in range(15)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[1]*15, marker_color=colors, hoverinfo='x'))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=130, margin=dict(l=5, r=5, t=10, b=20),
        xaxis=dict(showgrid=False, tickfont=dict(size=9, color='#64748b')),
        yaxis=dict(showgrid=False, showticklabels=False, range=[0, 1.2])
    )
    return fig

# ESTADO DE SESIÓN NAVEGACIÓN
if "liga_activa" not in st.session_state:
    st.session_state["liga_activa"] = None

# HEADER BRAND
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#2563eb;">PICKS</span></div>
    <div style="font-weight:700; color:#475569; font-size:0.9rem;">MODELO QUANT & INGENIERÍA NFL (32 EQUIPOS)</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# VISTA 1: HOME LANDING PAGE
# ==============================================================================
if st.session_state["liga_activa"] is None:
    col_hero_left, col_hero_right = st.columns([6, 6])

    with col_hero_left:
        st.markdown("""
        <div class="hero-title">La IA que te <br><span class="hero-highlight">hará ganar</span></div>
        <div class="hero-subtitle">Deja de inventar parlays. Juega con cabeza y modelos estocásticos.</div>
        """, unsafe_allow_html=True)

        if st.button("🏈 NFL (32 Equipos AFC/NFC) ➔", use_container_width=True):
            st.session_state["liga_activa"] = "NFL"
            st.rerun()

    with col_hero_right:
        st.markdown("""
        <div class="sim-card-home">
            <div class="sim-card-title">Cada juego <br>simulado <br><span style="color:#2563eb;">10,000 veces</span></div>
            <p style="color:#64748b; font-size:0.95rem; margin-top:15px; font-weight:500;">
                NFL: Evaluamos los 32 equipos de AFC y NFC, Trincheras, Clima Extremo y Spreads Gancho con Teasers.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# VISTA 2: PANEL DE ANÁLISIS NFL (50/50)
# ==============================================================================
elif st.session_state["liga_activa"] == "NFL":
    c_head_title, c_head_back = st.columns([9, 3])
    with c_head_title:
        st.markdown("<div class='hero-title' style='font-size:2.2rem;'>Escaneo de Valor <span class='hero-highlight'>(NFL - 32 Equipos)</span></div>", unsafe_allow_html=True)
    with c_head_back:
        if st.button("← Cambiar Deporte", use_container_width=True):
            st.session_state["liga_activa"] = None
            st.rerun()

    col_izq_inputs, col_der_analysis = st.columns([1, 1])

    with col_izq_inputs:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>🏈 1. Ingeniería Deportiva & Trincheras</h3>", unsafe_allow_html=True)

        c_loc, c_vis = st.columns(2)
        with c_loc: eq_loc = st.selectbox("Equipo Local:", sorted(list(NFL_DATA.keys())), index=13) # Kansas City Chiefs
        with c_vis: eq_vis = st.selectbox("Equipo Visitante:", sorted(list(NFL_DATA.keys())), index=26) # San Francisco 49ers

        d_loc, d_vis = NFL_DATA[eq_loc], NFL_DATA[eq_vis]

        # BANNER CON ESCUDOS DE LOS CLUBES ELEGIDOS
        st.markdown(f"""
        <div class="analysis-card" style="border:1px solid #bfdbfe;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="{d_loc['logo']}" width="32">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_loc}</span>
                </div>
                <div style="font-weight:900; color:#2563eb;">VS</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_vis}</span>
                    <img src="{d_vis['logo']}" width="32">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PARÁMETROS CLIMÁTICOS EXTREMOS Y BAJAS
        st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569;'>Capa 3: Estadios & Clima Extremo:</p>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1: clima_viento = st.checkbox("Viento > 25km/h")
        with col_c2: clima_frio = st.checkbox("Nieve / < 0°C")
        with col_c3: baja_qb_loc = st.checkbox(f"Baja QB Local")
        with col_c4: baja_qb_vis = st.checkbox(f"Baja QB Visita")

        # CAPTURA DE SPREADS Y CUOTAS
        st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Captura de Spreads y Cuotas de tu Casa</h4>", unsafe_allow_html=True)
        fmt_odds = st.radio("Formato Cuotas:", ["Decimales", "Americanos"], horizontal=True)

        st.markdown("<b>1. Money Line (Ganador Directo)</b>", unsafe_allow_html=True)
        c_ml1, c_ml2 = st.columns(2)
        with c_ml1: q_ml_loc = st.text_input(f"ML {eq_loc[:12]}", value="1.80")
        with c_ml2: q_ml_vis = st.text_input(f"ML {eq_vis[:12]}", value="2.05")

        st.markdown("<b>2. Hándicap de Puntos Independiente (-16.5 a +16.5)</b>", unsafe_allow_html=True)
        ch1, ch2, ch3, ch4 = st.columns([1.5, 1.25, 1.5, 1.25])
        with ch1: spread_loc = st.slider(f"Spread Local", -16.5, 16.5, -3.5, step=0.5)
        with ch2: q_spread_loc = st.text_input(f"Cuota {spread_loc}", value="1.90")
        with ch3: spread_vis = st.slider(f"Spread Visita", -16.5, 16.5, +3.5, step=0.5)
        with ch4: q_spread_vis = st.text_input(f"Cuota {spread_vis}", value="1.90")

        if abs(spread_loc) in [3.5, 7.5]:
            st.markdown(f"""
            <div class="trap-alert">
                ⚠️ <b>TRAP LINE DETECTOR (-3.5 / -7.5):</b> Spread en número gancho estratégico. Sugerimos mutación a Teaser (+6.0 pts) para asegurar el cruce clave de 3 o 7.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<b>3. Totales de Puntos, Goles de Campo & Touchdowns</b>", unsafe_allow_html=True)
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

        sim_nfl = simular_montecarlo_nfl(
            d_loc, d_vis, clima_viento, clima_frio, baja_qb_loc, baja_qb_vis,
            spread_loc, spread_vis, line_pts, line_fg, line_td
        )

        mercados_nfl = [
            {"mercado": f"1. Moneyline: Gana {eq_loc}", "prob": sim_nfl['p_ml_loc'], "cuota": parse_odds(q_ml_loc, fmt_odds)},
            {"mercado": f"1. Moneyline: Gana {eq_vis}", "prob": sim_nfl['p_ml_vis'], "cuota": parse_odds(q_ml_vis, fmt_odds)},
            {"mercado": f"2. Spread: {eq_loc} ({spread_loc:+} pts)", "prob": sim_nfl['p_spread_loc'], "cuota": parse_odds(q_spread_loc, fmt_odds)},
            {"mercado": f"2. Spread: {eq_vis} ({spread_vis:+} pts)", "prob": sim_nfl['p_spread_vis'], "cuota": parse_odds(q_spread_vis, fmt_odds)},
            {"mercado": f"3. Total Puntos: Over {line_pts}", "prob": sim_nfl['p_over_pts'], "cuota": parse_odds(q_over_pts, fmt_odds)},
            {"mercado": f"3. Total Puntos: Under {line_pts}", "prob": sim_nfl['p_under_pts'], "cuota": parse_odds(q_under_pts, fmt_odds)},
            {"mercado": f"4. Goles de Campo: Over {line_fg}", "prob": sim_nfl['p_over_fg'], "cuota": parse_odds(q_over_fg, fmt_odds)},
            {"mercado": f"4. Goles de Campo: Under {line_fg}", "prob": sim_nfl['p_under_fg'], "cuota": parse_odds(q_under_fg, fmt_odds)},
            {"mercado": f"5. Touchdowns Totales: Over {line_td}", "prob": sim_nfl['p_over_td'], "cuota": parse_odds(q_over_td, fmt_odds)},
            {"mercado": f"5. Touchdowns Totales: Under {line_td}", "prob": sim_nfl['p_under_td'], "cuota": parse_odds(q_under_td, fmt_odds)}
        ]

        for idx, item in enumerate(mercados_nfl):
            prob_val = item['prob']
            cuota_casa = item['cuota']
            cuota_real = 1.0 / prob_val if prob_val > 0 else 99.0
            ev = (prob_val * cuota_casa) - 1.0

            if prob_val >= 0.75:
                badge_html = '<span class="badge-star">💎 APUESTA ESTRELLA (+EV)</span>' if ev > 0.0 else '<span class="badge-high">🟢 HIGH CONFIDENCE</span>'
            elif 0.60 <= prob_val < 0.75:
                badge_html = '<span class="badge-medium">🟠 MEDIUM PROBABILITY</span>'
            else:
                badge_html = '<span class="badge-low">🔴 LOW PROBABILITY (FADE)</span>'

            st.markdown(f"""
            <div class="analysis-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:900; font-size:0.9rem; color:#0f172a;">↗ {item['mercado']}</span>
                        <div style="font-size:0.78rem; color:#607d71; margin-top:4px;">
                            Prob. IA: <b>{prob_val*100:.1f}%</b> | Cuota Real: <b style="color:#059669;">@{cuota_real:.2f}</b> | Tu Casa: <b style="color:#2563eb;">@{cuota_casa:.2f}</b> | EV: <b>{ev*100:+.1f}%</b>
                        </div>
                    </div>
                    <div>{badge_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📈 Ver Tendencia de Cobertura de Línea (NFL 15 Partidos)"):
                fig_mini = generar_grafica_mini_15_partidos(prob_val)
                st.plotly_chart(fig_mini, use_container_width=True, key=f"chart_nfl_{idx}")
