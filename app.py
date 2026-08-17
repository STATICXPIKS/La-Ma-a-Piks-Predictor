import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests

# Configuración de página
st.set_page_config(
    page_title="Premier League Predictor - Cyberpunk Bet365",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS CYBERPUNK - VERDE Y ORO (MÁXIMO CONTRASTE)
st.markdown("""
<style>
    /* Fondo principal y textos globales */
    .stApp {
        background-color: #070a08 !important;
        color: #ffffff !important;
    }
    
    /* Forzar visibilidad en todos los labels y textos de Streamlit */
    label, p, span, div, .stMarkdown, .stRadio label, .stSlider label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Header Cyberpunk Bet365 */
    .cyber-header {
        background: linear-gradient(135deg, #002b1b 0%, #00120b 100%);
        border: 2px solid #00FF66;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
        padding: 15px 25px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 25px;
    }
    .cyber-title {
        color: #FFD700 !important;
        font-weight: 900;
        font-size: 1.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }
    
    /* Inputs y Formularios visiblemente resaltados */
    .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #121915 !important;
        color: #FFD700 !important;
        border: 1px solid #00FF66 !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        box-shadow: inset 0 0 5px rgba(0, 255, 102, 0.2);
    }

    /* Targetas de Apuesta Estilo Cyberpunk */
    .cyber-card {
        background-color: #0d1410;
        border: 1px solid #1a2a20;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }
    .cyber-card-title {
        font-weight: 800;
        font-size: 1.1rem;
        color: #ffffff;
    }
    .cyber-card-sub {
        font-size: 0.85rem;
        color: #a0b0a5;
        font-family: monospace;
        margin-top: 4px;
    }

    /* Estilos de Rango de Probabilidad */
    .card-high {
        border-left: 6px solid #00FF66 !important;
        box-shadow: -5px 0 12px rgba(0, 255, 102, 0.2);
    }
    .card-medium {
        border-left: 6px solid #FF9900 !important;
        box-shadow: -5px 0 12px rgba(255, 153, 0, 0.2);
    }
    .card-low {
        border-left: 6px solid #FF0055 !important;
        box-shadow: -5px 0 12px rgba(255, 0, 85, 0.2);
    }
    .card-star {
        border: 2px solid #FFD700 !important;
        background: linear-gradient(135deg, #182000 0%, #0d1410 100%) !important;
        box-shadow: 0 0 18px rgba(255, 215, 0, 0.4) !important;
    }

    /* Badges de Estado */
    .cyber-badge {
        font-weight: 900;
        padding: 8px 16px;
        border-radius: 5px;
        font-size: 0.85rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-high {
        background-color: #00FF66;
        color: #000000;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.6);
    }
    .badge-medium {
        background-color: #FF9900;
        color: #000000;
        box-shadow: 0 0 10px rgba(255, 153, 0, 0.6);
    }
    .badge-low {
        background-color: #FF0055;
        color: #ffffff;
        box-shadow: 0 0 10px rgba(255, 0, 85, 0.6);
    }
    .badge-star {
        background-color: #FFD700;
        color: #000000;
        box-shadow: 0 0 12px rgba(255, 215, 0, 0.8);
    }
</style>
""", unsafe_allow_html=True)

PL_LOGO = "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"

TEAMS_DATA_FALLBACK = {
    "Arsenal": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55},
    "Aston Villa": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51},
    "Bournemouth": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg", "xg": 1.40, "xga": 1.55, "ppda": 10.5, "aereos": 48},
    "Brentford": {"logo": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56},
    "Brighton": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_FC_crest.svg", "xg": 1.65, "xga": 1.40, "ppda": 9.5, "aereos": 47},
    "Chelsea": {"logo": "https://upload.wikimedia.org/wikipedia/en/cc/CCFC_logo.svg", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52},
    "Crystal Palace": {"logo": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo.svg", "xg": 1.35, "xga": 1.30, "ppda": 11.8, "aereos": 53},
    "Everton": {"logo": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg", "xg": 1.30, "xga": 1.40, "ppda": 12.5, "aereos": 58},
    "Fulham": {"logo": "https://upload.wikimedia.org/wikipedia/en/a/a8/Fulham_FC_%28shield%29.svg", "xg": 1.40, "xga": 1.50, "ppda": 11.0, "aereos": 50},
    "Liverpool": {"logo": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54},
    "Manchester City": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52},
    "Manchester United": {"logo": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg", "xg": 1.60, "xga": 1.45, "ppda": 10.8, "aereos": 50},
    "Newcastle": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg", "xg": 1.70, "xga": 1.20, "ppda": 9.9, "aereos": 53},
    "Nottingham Forest": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_logo.svg", "xg": 1.25, "xga": 1.50, "ppda": 13.2, "aereos": 51},
    "Tottenham": {"logo": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49},
    "West Ham": {"logo": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg", "xg": 1.35, "xga": 1.60, "ppda": 13.5, "aereos": 54},
    "Wolves": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg", "xg": 1.30, "xga": 1.55, "ppda": 12.0, "aereos": 49}
}

@st.cache_data(ttl=3600)
def cargar_datos_api():
    url = "https://api.football-data.org/v4/competitions/PL/standings"
    headers = {"X-Auth-Token": "YOUR_FREE_API_KEY"} 
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            standings = data['standings'][0]['table']
            teams = {}
            for item in standings:
                name = item['team']['name']
                played = max(item['playedGames'], 1)
                gf = item['goalsFor'] / played
                ga = item['goalsAgainst'] / played
                logo = item['team']['crest']
                base_info = TEAMS_DATA_FALLBACK.get(name, {"ppda": 10.5, "aereos": 50, "logo": logo})
                teams[name] = {
                    "logo": logo if logo else base_info["logo"],
                    "xg": round(gf * 1.05, 2),
                    "xga": round(ga * 0.95, 2),
                    "ppda": base_info["ppda"],
                    "aereos": base_info["aereos"]
                }
            return teams, True
    except Exception:
        pass
    return TEAMS_DATA_FALLBACK, False

TEAMS_DATA, api_conectada = cargar_datos_api()

# CONVERSIÓN DE MOMIOS
def parse_odds_to_decimal(val_str, format_type):
    try:
        val = float(val_str)
        if format_type == "Decimales":
            return val
        else:
            return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def format_odds_display(decimal_val, format_type):
    if format_type == "Decimales":
        return f"{decimal_val:.2f}"
    else:
        if decimal_val <= 1.0: return "+100"
        if decimal_val >= 2.0: return f"+{int(round((decimal_val - 1.0) * 100))}"
        return f"-{int(round(100.0 / (decimal_val - 1.0)))}"

def calcular_ev(prob_modelo, cuota_decimal):
    return (prob_modelo * cuota_decimal) - 1.0

# CLASIFICACIÓN DE PROBABILIDAD Y DETECCIÓN DE APUESTA ESTRELLA
def clasificar_opcion(prob, ev):
    """
    RANGOS DE PROBABILIDAD:
    - 75% a 90%: HIGH CONFIDENCE (Verde)
    - 60% a 74%: MEDIUM PROBABILITY (Naranja)
    - 10% a 59%: LOW PROBABILITY (Rojo)
    
    DISTINTIVO ESPECIAL:
    - 💎 APUESTA ESTRELLA: Rango Verde (75-90%) + EV Positivo (Error de Cuota).
    """
    prob_pct = prob * 100.0
    
    if prob_pct >= 75.0:
        if ev > 0.0:
            return "💎 APUESTA ESTRELLA", "card-star", "badge-star"
        else:
            return "HIGH CONFIDENCE", "card-high", "badge-high"
    elif 60.0 <= prob_pct < 75.0:
        return "MEDIUM PROBABILITY", "card-medium", "badge-medium"
    else:
        return "LOW PROBABILITY", "card-low", "badge-low"

def calcular_lambdas(h_team, a_team, fatiga_h, rot_h, fatiga_a, rot_a, arb, clima):
    dh, da = TEAMS_DATA[h_team], TEAMS_DATA[a_team]
    avg_h, avg_a = 1.55, 1.25
    att_h, def_h = dh["xg"] / avg_h, dh["xga"] / avg_a
    att_a, def_a = da["xg"] / avg_a, da["xga"] / avg_h
    tactical_h = (12.0 / max(dh["ppda"], 5.0)) * (dh["aereos"] / 50.0)
    tactical_a = (12.0 / max(da["ppda"], 5.0)) * (da["aereos"] / 50.0)
    fatigue_h = 1.0 - (fatiga_h * 0.12 + rot_h * 0.10)
    fatigue_a = 1.0 - (fatiga_a * 0.12 + rot_a * 0.10)
    lambda_h = avg_h * att_h * def_a * tactical_h * fatigue_h * arb * clima
    lambda_a = avg_a * att_a * def_h * tactical_a * fatigue_a * (2.0 - arb) * clima
    return max(lambda_h, 0.2), max(lambda_a, 0.15)

def generar_matriz(lambda_h, lambda_a, max_goles=7):
    mat = np.zeros((max_goles, max_goles))
    for h in range(max_goles):
        for a in range(max_goles):
            mat[h, a] = poisson.pmf(h, lambda_h) * poisson.pmf(a, lambda_a)
    return mat / np.sum(mat)

# ENCABEZADO CYBERPUNK
st.markdown(f"""
<div class="cyber-header">
    <div style="display:flex; align-items:center; gap:15px;">
        <img src="{PL_LOGO}" style="width:45px; filter: brightness(0) invert(1);">
        <h1 class="cyber-title">BET365 PREMIER LEAGUE // CYBER-PREDICTOR</h1>
    </div>
    <span style="color:#00FF66; font-weight:bold; font-family:monospace; letter-spacing:1px;">SYS.ONLINE v2.6</span>
</div>
""", unsafe_allow_html=True)

# SELECCIÓN DE EQUIPOS
col_team1, col_team2 = st.columns(2)

with col_team1:
    st.markdown("#### 🏠 EQUIPO LOCAL")
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=3)
    st.image(TEAMS_DATA[home_team]["logo"], width=45)
    c1, c2 = st.columns(2)
    with c1: fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
    with c2: rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_team2:
    st.markdown("#### ✈️ EQUIPO VISITANTE")
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=14)
    st.image(TEAMS_DATA[away_team]["logo"], width=45)
    c3, c4 = st.columns(2)
    with c3: fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    with c4: rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

with st.expander("⚙️ FACTORES AMBIENTALES Y ARBITRAJE"):
    ca, cc = st.columns(2)
    with ca: arbitro = st.slider("Factor Árbitro (1.0 = Neutral)", 0.85, 1.15, 1.00, step=0.01)
    with cc: clima = st.slider("Factor Clima (1.0 = Normal)", 0.80, 1.00, 0.95, step=0.01)

# CÁLCULOS DEL MODELO
lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a, arbitro, clima)
matriz = generar_matriz(lam_h, lam_a)

p_home = float(np.sum(np.tril(matriz, -1)))
p_draw = float(np.sum(np.diag(matriz)))
p_away = float(np.sum(np.triu(matriz, 1)))

p_dc_1x = p_home + p_draw
p_under25 = float(sum(matriz[h, a] for h in range(7) for a in range(7) if h + a < 2.5))
p_btts_no = 1.0 - float(sum(matriz[h, a] for h in range(1, 7) for a in range(1, 7)))

st.markdown("---")

# METER MOMIOS
col_head, col_opt = st.columns([3, 2])
with col_head:
    st.markdown("<h3 style='color:#FFD700; margin:0;'>⚡ MOMIOS DE TU CASA DE APUESTAS</h3>", unsafe_allow_html=True)
with col_opt:
    tipo_momio = st.radio("Formato de Momios:", ["Decimales", "Americanos"], horizontal=True)

def default_val(prob):
    dec = 1/prob if prob > 0 else 2.0
    return format_odds_display(dec, tipo_momio)

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1: m_home = st.text_input(f"GANA {home_team.upper()}", value=default_val(p_home))
with f_col2: m_draw = st.text_input("EMPATE", value=default_val(p_draw))
with f_col3: m_away = st.text_input(f"GANA {away_team.upper()}", value=default_val(p_away))

f_col4, f_col5, f_col6 = st.columns(3)
with f_col4: linea_goles = st.selectbox("LÍNEA DE GOLES", ["0/U 2.5", "0/U 1.5", "0/U 3.5"], index=0)
with f_col5: m_over = st.text_input("MÁS (OVER)", value=default_val(1.0 - p_under25))
with f_col6: m_under = st.text_input("MENOS (UNDER)", value=default_val(p_under25))

f_col7, f_col8 = st.columns(2)
with f_col7: m_btts_yes = st.text_input("AMBOS ANOTAN: SÍ", value=default_val(1.0 - p_btts_no))
with f_col8: m_btts_no = st.text_input("AMBOS ANOTAN: NO", value=default_val(p_btts_no))

# OBTENER DECIMALES Y CALCULAR EV
odd_h = parse_odds_to_decimal(m_home, tipo_momio)
odd_under = parse_odds_to_decimal(m_under, tipo_momio)
odd_btts_no = parse_odds_to_decimal(m_btts_no, tipo_momio)

ev_h = calcular_ev(p_home, odd_h)
ev_dc1x = calcular_ev(p_dc_1x, 1.25)
ev_under = calcular_ev(p_under25, odd_under)
ev_btts_no = calcular_ev(p_btts_no, odd_btts_no)

# CLASIFICACIÓN CON NUEVA LÓGICA DE RANGOS
lbl_h, card_h, badge_h = clasificar_opcion(p_home, ev_h)
lbl_dc1x, card_dc1x, badge_dc1x = clasificar_opcion(p_dc_1x, ev_dc1x)
lbl_under, card_under, badge_under = clasificar_opcion(p_under25, ev_under)
lbl_btts_no, card_btts_no, badge_btts_no = clasificar_opcion(p_btts_no, ev_btts_no)

st.markdown("---")
st.markdown("<h3 style='color:#00FF66;'>📊 ANÁLISIS MATRIX DE OPORTUNIDADES</h3>", unsafe_allow_html=True)

# TARGETAS DIBUJADAS CON ESTILO CIBERNETICO
opciones = [
    {"titulo": f"Gana {home_team}", "sub": f"1X2 {home_team[:3].upper()} ({format_odds_display(odd_h, tipo_momio)})", "prob": p_home, "ev": ev_h, "lbl": lbl_h, "card": card_h, "badge": badge_h},
    {"titulo": f"{home_team} o Empate (1X)", "sub": f"Doble Oportunidad 1X · Modelo {format_odds_display(1/p_dc_1x, tipo_momio)}", "prob": p_dc_1x, "ev": ev_dc1x, "lbl": lbl_dc1x, "card": card_dc1x, "badge": badge_dc1x},
    {"titulo": "Menos de 2.5 Goles", "sub": f"Under 2.5 · Esperados: {(lam_h+lam_a):.1f} goles", "prob": p_under25, "ev": ev_under, "lbl": lbl_under, "card": card_under, "badge": badge_under},
    {"titulo": "Ambos Equipos Anotan: NO", "sub": f"BTTS NO · Modelo {format_odds_display(1/p_btts_no, tipo_momio)}", "prob": p_btts_no, "ev": ev_btts_no, "lbl": lbl_btts_no, "card": card_btts_no, "badge": badge_btts_no}
]

for op in opciones:
    st.markdown(f"""
    <div class="cyber-card {op['card']}">
        <div>
            <div class="cyber-card-title">{op['titulo']}</div>
            <div class="cyber-card-sub">{op['sub']} | Probabilidad: <b style="color:#00FF66;">{op['prob']*100:.1f}%</b> | EV: <b style="color:#FFD700;">{op['ev']*100:+.1f}%</b></div>
        </div>
        <div><span class="cyber-badge {op['badge']}">{op['lbl']}</span></div>
    </div>
    """, unsafe_allow_html=True)
