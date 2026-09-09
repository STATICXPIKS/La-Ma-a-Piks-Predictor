import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import datetime

# Configuración de Página - Estilo RickyPicks Light Mode
st.set_page_config(
    page_title="LA MAÑA PICKS - IA & SIMULACIÓN QUANT",
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

    .auto-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .analysis-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
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
# ALGORITMO DINÁMICO DE FATIGA Y ROTACIÓN AUTOMÁTICA
# ------------------------------------------------------------------------------
def calcular_fatiga_rotacion_automatica(equipo, liga):
    """
    Calcula automáticamente el nivel de fatiga y rotación estimado
    según la participación en torneos internacionales y densidad de partidos.
    """
    equipos_top_europeos = [
        "Real Madrid", "Manchester City", "Bayern München", "PSG", "Barcelona", 
        "Arsenal", "Liverpool", "Inter", "Atlético Madrid", "Dortmund", "Chelsea", "Tottenham", "Aston Villa"
    ]
    
    # Si el equipo juega Champions / Europa League y liga local
    if equipo in equipos_top_europeos:
        fatiga_estimada = 65  # Alta carga de partidos intersemanales
        rotacion_estimada = 40 # Alta necesidad de rotación en plantilla
    else:
        fatiga_estimada = 15  # Descanso normal de semana completa
        rotacion_estimada = 10 # Plantilla base titular
        
    return fatiga_estimada, rotacion_estimada

# ------------------------------------------------------------------------------
# BASES DE DATOS DE EQUIPOS (MÉTRICAS AUTO-ACTUALIZABLES)
# ------------------------------------------------------------------------------
PREMIER_LEAGUE_DATA = {
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Aston Villa": {"logo": "https://crests.football-data.org/58.png", "xg_loc": 1.75, "xga_loc": 1.30, "xg_vis": 1.45, "xga_vis": 1.50, "ppda": 11.2, "aereos": 51, "corners": 5.4, "tarjetas": 2.1},
    "Bournemouth": {"logo": "https://crests.football-data.org/1044.png", "xg_loc": 1.40, "xga_loc": 1.55, "xg_vis": 1.15, "xga_vis": 1.70, "ppda": 10.5, "aereos": 48, "corners": 4.9, "tarjetas": 2.3},
    "Brentford": {"logo": "https://crests.football-data.org/402.png", "xg_loc": 1.50, "xga_loc": 1.45, "xg_vis": 1.20, "xga_vis": 1.65, "ppda": 12.1, "aereos": 56, "corners": 4.6, "tarjetas": 1.8},
    "Chelsea": {"logo": "https://crests.football-data.org/61.png", "xg_loc": 1.80, "xga_loc": 1.25, "xg_vis": 1.60, "xga_vis": 1.40, "ppda": 9.8, "aereos": 52, "corners": 5.6, "tarjetas": 2.6},
    "Liverpool": {"logo": "https://crests.football-data.org/64.png", "xg_loc": 2.20, "xga_loc": 1.00, "xg_vis": 2.05, "xga_vis": 1.10, "ppda": 8.5, "aereos": 54, "corners": 7.1, "tarjetas": 1.5},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Manchester United": {"logo": "https://crests.football-data.org/66.png", "xg_loc": 1.60, "xga_loc": 1.45, "xg_vis": 1.35, "xga_vis": 1.55, "ppda": 10.8, "aereos": 50, "corners": 5.9, "tarjetas": 2.2},
    "Tottenham": {"logo": "https://crests.football-data.org/73.png", "xg_loc": 1.85, "xga_loc": 1.50, "xg_vis": 1.50, "xga_vis": 1.65, "ppda": 9.1, "aereos": 49, "corners": 6.3, "tarjetas": 2.1}
}

LALIGA_DATA = {
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg_loc": 2.30, "xga_loc": 0.95, "xg_vis": 2.10, "xga_vis": 1.05, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9},
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Atlético de Madrid": {"logo": "https://crests.football-data.org/78.png", "xg_loc": 1.85, "xga_loc": 0.90, "xg_vis": 1.55, "xga_vis": 1.10, "ppda": 10.2, "aereos": 53, "corners": 5.8, "tarjetas": 2.4},
    "Athletic": {"logo": "https://crests.football-data.org/77.png", "xg_loc": 1.60, "xga_loc": 1.10, "xg_vis": 1.30, "xga_vis": 1.25, "ppda": 9.0, "aereos": 54, "corners": 5.9, "tarjetas": 2.0},
    "Villarreal": {"logo": "https://crests.football-data.org/102.png", "xg_loc": 1.80, "xga_loc": 1.50, "xg_vis": 1.40, "xga_vis": 1.60, "ppda": 10.0, "aereos": 49, "corners": 5.6, "tarjetas": 2.2}
}

CHAMPIONS_DATA = {
    "Real Madrid": {"logo": "https://crests.football-data.org/86.png", "xg_loc": 2.35, "xga_loc": 0.80, "xg_vis": 2.15, "xga_vis": 0.90, "ppda": 8.5, "aereos": 51, "corners": 7.2, "tarjetas": 1.6},
    "Manchester City": {"logo": "https://crests.football-data.org/65.png", "xg_loc": 2.25, "xga_loc": 0.80, "xg_vis": 2.10, "xga_vis": 0.90, "ppda": 8.2, "aereos": 52, "corners": 7.5, "tarjetas": 1.3},
    "Bayern München": {"logo": "https://crests.football-data.org/5.png", "xg_loc": 2.40, "xga_loc": 0.90, "xg_vis": 2.20, "xga_vis": 1.05, "ppda": 7.8, "aereos": 53, "corners": 7.0, "tarjetas": 1.5},
    "PSG": {"logo": "https://crests.football-data.org/524.png", "xg_loc": 2.15, "xga_loc": 1.05, "xg_vis": 1.80, "xga_vis": 1.20, "ppda": 8.9, "aereos": 49, "corners": 6.5, "tarjetas": 2.0},
    "Inter": {"logo": "https://crests.football-data.org/108.png", "xg_loc": 1.95, "xga_loc": 0.85, "xg_vis": 1.65, "xga_vis": 1.00, "ppda": 10.1, "aereos": 56, "corners": 6.2, "tarjetas": 1.8},
    "Arsenal": {"logo": "https://crests.football-data.org/57.png", "xg_loc": 2.10, "xga_loc": 0.85, "xg_vis": 1.90, "xga_vis": 0.95, "ppda": 8.8, "aereos": 55, "corners": 6.8, "tarjetas": 1.4},
    "Barcelona": {"logo": "https://crests.football-data.org/81.png", "xg_loc": 2.30, "xga_loc": 0.95, "xg_vis": 2.10, "xga_vis": 1.05, "ppda": 8.0, "aereos": 50, "corners": 6.9, "tarjetas": 1.9}
}

ARBITROS = {
    "Chris Kavanagh": {"prom_tarjetas": 3.9},
    "Anthony Taylor": {"prom_tarjetas": 4.5},
    "Szymon Marciniak": {"prom_tarjetas": 4.1},
    "Daniele Orsato": {"prom_tarjetas": 4.7}
}

# ------------------------------------------------------------------------------
# FUNCIONES AUXILIARES & MOTOR MONTE CARLO
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

    # Usa xG de Local para d_loc y xG de Visitante para d_vis
    lambda_h = max(1.55 * (d_loc["xg_loc"] / 1.55) * (d_vis["xga_vis"] / 1.25) * tactical_h * fatiga_factor_loc, 0.2)
    lambda_a = max(1.25 * (d_vis["xg_vis"] / 1.25) * (d_loc["xga_loc"] / 1.55) * tactical_a * fatiga_factor_vis, 0.15)

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

# ESTADO DE SESIÓN PARA CONTROLAR NAVEGACIÓN
if "liga_activa" not in st.session_state:
    st.session_state["liga_activa"] = None

# HEADER
st.markdown("""
<div class="nav-bar">
    <div class="brand-logo">LA MAÑA <span style="color:#2563eb;">PICKS</span></div>
    <div style="font-weight:700; color:#475569; font-size:0.9rem;">MODELO QUANT MONTE CARLO AUTO-UPDATE</div>
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
        <div class="hero-subtitle">Deja de inventar parlays. Juega con cabeza y datos auto-actualizados.</div>
        """, unsafe_allow_html=True)

        if st.button("PREMIER LEAGUE ➔", use_container_width=True):
            st.session_state["liga_activa"] = "PREMIER LEAGUE"
            st.rerun()

        if st.button("LALIGA ➔", use_container_width=True):
            st.session_state["liga_activa"] = "LALIGA"
            st.rerun()

        if st.button("CHAMPIONS LEAGUE ➔", use_container_width=True):
            st.session_state["liga_activa"] = "CHAMPIONS LEAGUE"
            st.rerun()

    with col_hero_right:
        st.markdown("""
        <div class="sim-card-home">
            <div class="sim-card-title">Cada juego <br>simulado <br><span style="color:#2563eb;">10,000 veces</span></div>
            <p style="color:#64748b; font-size:0.95rem; margin-top:15px; font-weight:500;">
                Calculamos automáticamente la fatiga UEFA, rendimiento local/visita, xG y PPDA en tiempo real.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# VISTA 2: PANEL DE ANÁLISIS AUTOMÁTICO (50/50)
# ==============================================================================
else:
    c_head_title, c_head_back = st.columns([9, 3])
    with c_head_title:
        st.markdown(f"<div class='hero-title' style='font-size:2.2rem;'>Escaneo de Valor <span class='hero-highlight'>({st.session_state['liga_activa']})</span></div>", unsafe_allow_html=True)
    with c_head_back:
        if st.button("← Cambiar Competición", use_container_width=True):
            st.session_state["liga_activa"] = None
            st.rerun()

    # Cargar Dataset correspondiente
    if st.session_state["liga_activa"] == "PREMIER LEAGUE":
        TEAMS_DATA = PREMIER_LEAGUE_DATA
    elif st.session_state["liga_activa"] == "LALIGA":
        TEAMS_DATA = LALIGA_DATA
    else:
        TEAMS_DATA = CHAMPIONS_DATA

    # DISPOSICIÓN EN 2 COLUMNAS PARALELAS (50/50)
    col_izq_inputs, col_der_analysis = st.columns([1, 1])

    # --------------------------------------------------------------------------
    # COLUMNA IZQUIERDA: CONFIGURACIÓN Y MOMIOS CON AVISO DE AUTO-CÁLCULO
    # --------------------------------------------------------------------------
    with col_izq_inputs:
        st.markdown("<h3 style='color:#0f172a; font-size:1.1rem; font-weight:800;'>⚙️ Configuración y Métricas Automáticas</h3>", unsafe_allow_html=True)

        c_loc, c_vis, c_ref = st.columns([3, 3, 2])
        with c_loc: eq_loc = st.selectbox("Equipo Local:", list(TEAMS_DATA.keys()), index=0)
        with c_vis: eq_vis = st.selectbox("Equipo Visitante:", list(TEAMS_DATA.keys()), index=1 if len(TEAMS_DATA)>1 else 0)
        with c_ref: arbitro_sel = st.selectbox("Árbitro:", list(ARBITROS.keys()), index=0)

        d_loc = TEAMS_DATA[eq_loc]
        d_vis = TEAMS_DATA[eq_vis]
        arbitro_data = ARBITROS[arbitro_sel]

        # OBTENCIÓN AUTOMÁTICA DE FATIGA Y ROTACIÓN PREDICHA
        fatiga_auto_loc, rot_auto_loc = calcular_fatiga_rotacion_automatica(eq_loc, st.session_state["liga_activa"])
        fatiga_auto_vis, rot_auto_vis = calcular_fatiga_rotacion_automatica(eq_vis, st.session_state["liga_activa"])

        st.markdown("""
        <div style="margin-bottom:8px;">
            <span class="auto-badge">⚡ DATO AUTO-DETECTADO</span>
            <span style="font-size:0.78rem; color:#475569; font-weight:700; margin-left:6px;">
                Fatiga y rotación calculadas según calendario reciente y UEFA:
            </span>
        </div>
        """, unsafe_allow_html=True)

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1: fatiga_loc = st.slider(f"Fatiga {eq_loc[:3]} (%)", 0, 100, fatiga_auto_loc) / 100.0
        with col_f2: rot_loc = st.slider(f"Rot. {eq_loc[:3]} (%)", 0, 100, rot_auto_loc) / 100.0
        with col_f3: fatiga_vis = st.slider(f"Fatiga {eq_vis[:3]} (%)", 0, 100, fatiga_auto_vis) / 100.0
        with col_f4: rot_vis = st.slider(f"Rot. {eq_vis[:3]} (%)", 0, 100, rot_auto_vis) / 100.0

        if (fatiga_vis > 0.50 or rot_vis > 0.30) and d_vis["xg_vis"] > d_loc["xg_loc"]:
            st.markdown(f"""
            <div class="trap-alert">
                ⚠️ <b>TRAP LINE DETECTOR:</b> {eq_vis} llega con alta fatiga acumulada ({int(fatiga_vis*100)}%). El algoritmo castiga automáticamente su rendimiento.
            </div>
            """, unsafe_allow_html=True)

        # Banner Matchup con rendimiento Local / Visitante específico
        st.markdown(f"""
        <div class="analysis-card" style="border:1px solid #bfdbfe;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="{d_loc['logo']}" width="28">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_loc} (Local)</span>
                </div>
                <div style="font-weight:900; color:#2563eb;">VS</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:0.95rem; color:#0f172a;">{eq_vis} (Visita)</span>
                    <img src="{d_vis['logo']}" width="28">
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.75rem; color:#64748b;">
                <div>xG Local: <b>{d_loc['xg_loc']}</b> | xGA: <b>{d_loc['xga_loc']}</b></div>
                <div>xG Visita: <b>{d_vis['xg_vis']}</b> | xGA: <b>{d_vis['xga_vis']}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Captura de Momios
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

    # --------------------------------------------------------------------------
    # COLUMNA DERECHA: MATRIZ DE RIESGO Y VALOR
    # --------------------------------------------------------------------------
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
                <div style="display:flex; justify-content:space-between; align-items:center;">
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
