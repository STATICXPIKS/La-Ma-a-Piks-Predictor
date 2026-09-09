import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson

# Configuración de página - Modo Claro Estilo RickyPicks
st.set_page_config(
    page_title="LA MAÑA PICKS - PREMIER LEAGUE IA",
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
        padding: 12px 0 20px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .brand-logo {
        font-size: 2rem;
        font-weight: 900;
        color: #1e40af !important;
        letter-spacing: -1px;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        letter-spacing: -1.2px;
        margin-bottom: 8px;
    }
    .hero-highlight { color: #2563eb !important; }

    .match-banner {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }

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

    /* Tarjetas de Análisis Lado Derecho */
    .analysis-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }

    .badge-high { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-medium { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-low { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-star { background-color: #fef9c3; color: #a16207; border: 1.5px solid #fde047; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-size: 0.80rem; box-shadow: 0 0 8px rgba(234, 179, 8, 0.4); }

    .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# BASE DE DATOS PREMIER LEAGUE
PREMIER_LEAGUE_DATA = {
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Aston Villa": {"logo": "https://crests.football-data.org/58.png", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1},
    "Bournemouth": {"logo": "https://crests.football-data.org/1044.png", "xg": 1.40, "xga": 1.55, "ppda": 10.5, "aereos": 48, "corners": 4.9, "tarjetas": 2.3},
    "Brentford": {"logo": "https://crests.football-data.org/402.png", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6, "tarjetas": 1.8},
    "Brighton": {"logo": "https://crests.football-data.org/397.png", "xg": 1.65, "xga": 1.40, "ppda": 9.5, "aereos": 47, "corners": 5.8, "tarjetas": 2.0},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6},
    "Coventry City": {"logo": "https://crests.football-data.org/1070.png", "xg": 1.30, "xga": 1.50, "ppda": 11.5, "aereos": 50, "corners": 4.8, "tarjetas": 1.9},
    "Crystal Palace": {"logo": "https://crests.football-data.org/354.png", "xg": 1.35, "xga": 1.30, "ppda": 11.8, "aereos": 53, "corners": 4.8, "tarjetas": 2.2},
    "Everton": {"logo": "https://crests.football-data.org/62.png", "xg": 1.30, "xga": 1.40, "ppda": 12.5, "aereos": 58, "corners": 4.7, "tarjetas": 2.1},
    "Fulham": {"logo": "https://crests.football-data.org/63.png", "xg": 1.40, "xga": 1.50, "ppda": 11.0, "aereos": 50, "corners": 5.1, "tarjetas": 2.0},
    "Hull City": {"logo": "https://crests.football-data.org/322.png", "xg": 1.22, "xga": 1.58, "ppda": 12.0, "aereos": 47, "corners": 4.3, "tarjetas": 1.7},
    "Ipswich Town": {"logo": "https://crests.football-data.org/349.png", "xg": 1.20, "xga": 1.60, "ppda": 13.0, "aereos": 48, "corners": 4.2, "tarjetas": 2.4},
    "Leeds": {"logo": "https://crests.football-data.org/341.png", "xg": 1.45, "xga": 1.40, "ppda": 9.2, "aereos": 51, "corners": 5.5, "tarjetas": 2.1},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Manchester United": {"logo": "https://crests.football-data.org/66.png", "xg": 1.60, "xga": 1.45, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2},
    "Newcastle": {"logo": "https://crests.football-data.org/67.png", "xg": 1.70, "xga": 1.20, "ppda": 9.9, "aereos": 53, "corners": 6.1, "tarjetas": 1.9},
    "Nottingham Forest": {"logo": "https://crests.football-data.org/351.png", "xg": 1.25, "xga": 1.50, "ppda": 13.2, "aereos": 51, "corners": 4.1, "tarjetas": 2.3},
    "Sunderland": {"logo": "https://crests.football-data.org/71.png", "xg": 1.28, "xga": 1.52, "ppda": 12.2, "aereos": 50, "corners": 4.4, "tarjetas": 2.0},
    "Tottenham": {"logo": "https://crests.football-data.org/73.png", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49, "corners": 6.3, "tarjetas": 2.1}
}

ARBITROS = {
    "Chris Kavanagh": {"prom_tarjetas": 3.9},
    "Anthony Taylor": {"prom_tarjetas": 4.5},
    "Michael Oliver": {"prom_tarjetas": 3.6},
    "Paul Tierney": {"prom_tarjetas": 4.8}
}

def parse_odds(val_str, fmt_type):
    try:
        val = float(val_str)
        if fmt_type == "Decimales":
            return val if val > 1.0 else 2.00
        return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def simular_montecarlo_avanzado(d_loc, d_vis, fatiga_loc, rot_loc, fatiga_vis, rot_vis, arbitro_card, line_goles, line_corners, line_cards, n_sim=10000):
    fatiga_factor_loc = 1.0 - (fatiga_loc * 0.12 + rot_loc * 0.10)
    fatiga_factor_vis = 1.0 - (fatiga_vis * 0.12 + rot_vis * 0.10)

    tactical_h = (12.0 / max(d_loc["ppda"], 5.0)) * (d_loc["aereos"] / 50.0)
    tactical_a = (12.0 / max(d_vis["ppda"], 5.0)) * (d_vis["aereos"] / 50.0)

    lambda_h = max(1.55 * (d_loc["xg"] / 1.55) * (d_vis["xga"] / 1.25) * tactical_h * fatiga_factor_loc, 0.2)
    lambda_a = max(1.25 * (d_vis["xg"] / 1.25) * (d_loc["xga"] / 1.55) * tactical_a * fatiga_factor_vis, 0.15)

    goles_h = np.random.poisson(lambda_h, n_sim)
    goles_a = np.random.poisson(lambda_a, n_sim)

    exp_c = (d_loc["corners"] + d_vis["corners"]) * 0.95
    corners_totales = np.random.poisson(exp_c, n_sim)

    exp_tarjetas = (d_loc["tarjetas"] + d_vis["tarjetas"]) * (arbitro_card / 4.0)
    tarjetas_totales = np.random.poisson(exp_tarjetas, n_sim)

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

# ------------------------------------------------------------------------------
# ENCABEZADO Y HEADER BAR
# ------------------------------------------------------------------------------
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#2563eb;">PICKS</span></div>
    <div style="font-weight:700; color:#475569; font-size:0.9rem;">PREMIER LEAGUE QUANT MODEL</div>
</div>
<div class="hero-title">Escaneo de Valor <span class="hero-highlight">(+EV)</span> & Detector de Trampas</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# DISPOSICIÓN PRINCIPAL EN DOS COLUMNAS PARALELAS (50/50)
# ------------------------------------------------------------------------------
col_izq_inputs, col_der_analysis = st.columns([1, 1])

# ==============================================================================
# COLUMNA IZQUIERDA: CONFIGURACIÓN + MOMIOS
# ==============================================================================
with col_izq_inputs:
    st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>⚙️ Configuración y Captura de Momios</h3>", unsafe_allow_html=True)

    c_loc, c_vis, c_ref = st.columns([3, 3, 2])
    with c_loc: eq_loc = st.selectbox("Equipo Local:", list(PREMIER_LEAGUE_DATA.keys()), index=0) # Arsenal
    with c_vis: eq_vis = st.selectbox("Equipo Visitante:", list(PREMIER_LEAGUE_DATA.keys()), index=8) # Everton
    with c_ref: arbitro_sel = st.selectbox("Árbitro:", list(ARBITROS.keys()), index=0)

    d_loc = PREMIER_LEAGUE_DATA[eq_loc]
    d_vis = PREMIER_LEAGUE_DATA[eq_vis]
    arbitro_data = ARBITROS[arbitro_sel]

    # Ajustes Físicos
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:2px;'>Fatiga UEFA y Rotaciones:</p>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1: fatiga_loc = st.slider(f"Fatiga {eq_loc[:3]} (%)", 0, 100, 15) / 100.0
    with col_f2: rot_loc = st.slider(f"Rot. {eq_loc[:3]} (%)", 0, 100, 10) / 100.0
    with col_f3: fatiga_vis = st.slider(f"Fatiga {eq_vis[:3]} (%)", 0, 100, 65) / 100.0
    with col_f4: rot_vis = st.slider(f"Rot. {eq_vis[:3]} (%)", 0, 100, 40) / 100.0

    if (fatiga_vis > 0.50 or rot_vis > 0.30) and d_vis["xg"] > d_loc["xg"]:
        st.markdown(f"""
        <div class="trap-alert">
            ⚠️ <b>TRAP LINE DETECTOR:</b> Cuota inusualmente alta en {eq_vis}. Viene fatigado ({int(fatiga_vis*100)}%). Se aplicó castigo probabilístico.
        </div>
        """, unsafe_allow_html=True)

    # Banner Matchup
    st.markdown(f"""
    <div class="match-banner">
        <div style="display:flex; justify-shadow:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:8px;">
                <img src="{d_loc['logo']}" width="28">
                <span style="font-weight:900; font-size:0.95rem;">{eq_loc}</span>
            </div>
            <div style="font-weight:900; color:#2563eb;">VS</div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:900; font-size:0.95rem;">{eq_vis}</span>
                <img src="{d_vis['logo']}" width="28">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Captura de Momios
    st.markdown("<h4 style='color:#0f172a; font-size:0.95rem; font-weight:800;'>🎲 Ingreso de Cuotas de tu Casa</h4>", unsafe_allow_html=True)
    fmt_odds = st.radio("Formato de Cuotas:", ["Decimales", "Americanos"], horizontal=True)

    # Mercados 1 & 2
    c1, c2, c3 = st.columns(3)
    with c1: q_1 = st.text_input(f"1X2 {eq_loc[:3]}", value="2.80")
    with c2: q_x = st.text_input("1X2 Empate", value="3.40")
    with c3: q_2 = st.text_input(f"1X2 {eq_vis[:3]}", value="2.40")

    c4, c5, c6 = st.columns(3)
    with c4: q_1x = st.text_input("DC 1X", value="1.55")
    with c5: q_x2 = st.text_input("DC X2", value="1.42")
    with c6: q_12 = st.text_input("DC 12", value="1.30")

    # Mercado 3: Goles
    cg1, cg2, cg3 = st.columns([1.5, 1.25, 1.25])
    with cg1: line_goles = st.slider("Línea Goles FT", 1.5, 4.5, 2.5, step=1.0)
    with cg2: q_over_g = st.text_input(f"Over {line_goles}", value="1.90")
    with cg3: q_under_g = st.text_input(f"Under {line_goles}", value="1.90")

    # Mercado 4 & 5: BTTS & AH
    cb1, cb2, cha1, cha2, cha3 = st.columns([1, 1, 1.2, 1, 1])
    with cb1: q_btts_si = st.text_input("BTTS SÍ", value="1.75")
    with cb2: q_btts_no = st.text_input("BTTS NO", value="2.05")
    with cha1: line_ha = st.selectbox("Hándicap AH", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=0)
    with cha2: q_ha_loc = st.text_input(f"AH {eq_loc[:3]}", value="1.55")
    with cha3: q_ha_vis = st.text_input(f"AH {eq_vis[:3]}", value="2.35")

    # Mercado 6 & 7: Córners & Tarjetas
    cc1, cc2, cc3 = st.columns([1.5, 1.25, 1.25])
    with cc1: line_corners = st.slider("Línea Córners", 8.5, 12.5, 9.5, step=1.0)
    with cc2: q_over_c = st.text_input(f"Córners > {line_corners}", value="1.85")
    with cc3: q_under_c = st.text_input(f"Córners < {line_corners}", value="1.85")

    ct1, ct2, ct3 = st.columns([1.5, 1.25, 1.25])
    with ct1: line_cards = st.slider("Línea Tarjetas", 3.5, 5.5, 4.5, step=1.0)
    with ct2: q_over_t = st.text_input(f"Tarjetas > {line_cards}", value="1.95")
    with ct3: q_under_t = st.text_input(f"Tarjetas < {line_cards}", value="1.80")

# ==============================================================================
# COLUMNA DERECHA: ANÁLISIS Y MATRIZ DE RIESGO
# ==============================================================================
with col_der_analysis:
    st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>📊 Matriz de Riesgo y Escaneo (+EV)</h3>", unsafe_allow_html=True)

    sim_results = simular_montecarlo_avanzado(
        d_loc, d_vis, fatiga_loc, rot_loc, fatiga_vis, rot_vis,
        arbitro_data["prom_tarjetas"], line_goles, line_corners, line_cards
    )

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
        {"mercado": f"6. Total Córners: Over {line_corners}", "prob": sim_results['p_over_corners'], "cuota": parse_odds(q_over_c, fmt_odds)},
        {"mercado": f"6. Total Córners: Under {line_corners}", "prob": sim_results['p_under_corners'], "cuota": parse_odds(q_under_c, fmt_odds)},
        {"mercado": f"7. Total Tarjetas: Over {line_cards}", "prob": sim_results['p_over_cards'], "cuota": parse_odds(q_over_t, fmt_odds)},
        {"mercado": f"7. Total Tarjetas: Under {line_cards}", "prob": sim_results['p_under_cards'], "cuota": parse_odds(q_under_t, fmt_odds)}
    ]

    for item in mercados_evaluados:
        prob_val = item['prob']
        cuota_casa = item['cuota']
        cuota_real = 1.0 / prob_val if prob_val > 0 else 99.0
        ev = (prob_val * cuota_casa) - 1.0

        if prob_val >= 0.75:
            if ev > 0.0:
                badge_html = '<span class="badge-star">💎 APUESTA ESTRELLA (+EV)</span>'
            else:
                badge_html = '<span class="badge-high">🟢 HIGH CONFIDENCE</span>'
        elif 0.60 <= prob_val < 0.75:
            badge_html = '<span class="badge-medium">🟠 MEDIUM PROBABILITY</span>'
        else:
            badge_html = '<span class="badge-low">🔴 LOW PROBABILITY (FADE)</span>'

        st.markdown(f"""
        <div class="analysis-card">
            <div style="display:flex; justify-shadow:space-between; align-items:center;">
                <div>
                    <span style="font-weight:900; font-size:0.9rem; color:#0f172a;">↗ {item['mercado']}</span>
                    <div style="font-size:0.78rem; color:#607d71; margin-top:4px;">
                        Prob. IA: <b>{prob_val*100:.1f}%</b> | Cuota Real: <b style="color:#059669;">@{cuota_real:.2f}</b> | Tu Casa: <b style="color:#2563eb;">@{cuota_casa:.2f}</b> | EV: <b>{ev*100:+.1f}%</b>
                    </div>
                </div>
                <div>
                    {badge_html}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
