import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests
import json

# Configuración de la página
st.set_page_config(
    page_title="Premier League Predictor - Bet365 Edition",
    layout="wide",
    page_icon="⚽"
)

# Estilos CSS personalizados inspirados en Bet365
st.markdown("""
<style>
    /* Estilo Global Bet365 */
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    /* Header Verde Bet365 */
    .bet365-header {
        background-color: #006341;
        padding: 15px 25px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .bet365-title {
        color: #FFDF1B;
        font-weight: 800;
        font-size: 1.8rem;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .pl-logo-header {
        width: 45px;
        filter: brightness(0) invert(1);
    }

    /* Tarjetas de Apuesta Bet365 */
    .bet365-card {
        background-color: #282828;
        border-left: 5px solid #006341;
        border-radius: 6px;
        padding: 14px 20px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    .bet365-card-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #ffffff;
    }
    .bet365-card-sub {
        font-size: 0.82rem;
        color: #b0b0b0;
        font-family: monospace;
        margin-top: 2px;
    }

    /* Badges de Veredicto Bet365 */
    .b365-badge {
        font-weight: bold;
        padding: 6px 14px;
        border-radius: 4px;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-bet {
        background-color: #FFDF1B;
        color: #000000;
    }
    .badge-skip {
        background-color: #3a3a3a;
        color: #888888;
        border: 1px solid #555555;
    }
    .badge-maybe {
        background-color: #006341;
        color: #ffffff;
    }
    .badge-trap {
        background-color: #e74c3c;
        color: #ffffff;
    }

    /* Selectores e Inputs */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #333333 !important;
        color: white !important;
        border-color: #444444 !important;
    }
    .stTextInput input {
        color: #FFDF1B !important;
        font-weight: bold;
        background-color: #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

PL_LOGO = "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"

# Base de Datos de Equipos de Premier League
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

# Funciones de Momios
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

# ENCABEZADO ESTILO BET365
st.markdown(f"""
<div class="bet365-header">
    <div style="display:flex; align-items:center; gap:15px;">
        <img src="{PL_LOGO}" class="pl-logo-header">
        <h1 class="bet365-title">Bet365 Premier League Predictor</h1>
    </div>
    <span style="color:#FFDF1B; font-weight:bold; font-size:0.9rem;">TRAP LINE DETECTOR V2.0</span>
</div>
""", unsafe_allow_html=True)

# SELECCIÓN DE EQUIPOS
col_team1, col_team2 = st.columns(2)

with col_team1:
    st.subheader("🏠 Local")
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=0)
    st.image(TEAMS_DATA[home_team]["logo"], width=45)
    c1, c2 = st.columns(2)
    with c1: fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
    with c2: rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_team2:
    st.subheader("✈️ Visitante")
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=9)
    st.image(TEAMS_DATA[away_team]["logo"], width=45)
    c3, c4 = st.columns(2)
    with c3: fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    with c4: rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

with st.expander("⚙️ Factores Ambientales (Árbitro & Clima)"):
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
p_over25 = 1.0 - p_under25
p_btts_yes = float(sum(matriz[h, a] for h in range(1, 7) for a in range(1, 7)))
p_btts_no = 1.0 - p_btts_yes

st.markdown("---")

# METER MOMIOS DE LA CASA DE APUESTAS
col_head, col_opt = st.columns([3, 2])
with col_head:
    st.markdown("<h3 style='color:#FFDF1B; margin:0;'>🟩 MOMIOS DE TU CASA DE APUESTAS</h3>", unsafe_allow_html=True)
with col_opt:
    tipo_momio = st.radio("Formato de Momios:", ["Americanos", "Decimales"], horizontal=True)

def default_val(prob):
    dec = 1/prob if prob > 0 else 2.0
    return format_odds_display(dec, tipo_momio)

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1: m_home = st.text_input(f"GANA {home_team.upper()}", value=default_val(p_home))
with f_col2: m_draw = st.text_input("EMPATE", value=default_val(p_draw))
with f_col3: m_away = st.text_input(f"GANA {away_team.upper()}", value=default_val(p_away))

f_col4, f_col5, f_col6 = st.columns(3)
with f_col4: linea_goles = st.selectbox("LÍNEA DE GOLES", ["0/U 2.5", "0/U 1.5", "0/U 3.5"], index=0)
with f_col5: m_over = st.text_input("MÁS (OVER)", value=default_val(p_over25))
with f_col6: m_under = st.text_input("MENOS (UNDER)", value=default_val(p_under25))

f_col7, f_col8 = st.columns(2)
with f_col7: m_btts_yes = st.text_input("AMBOS ANOTAN: SÍ", value=default_val(p_btts_yes))
with f_col8: m_btts_no = st.text_input("AMBOS ANOTAN: NO", value=default_val(p_btts_no))

# EVALUACIÓN DE APUESTAS Y VEREDICTOS
odd_h = parse_odds_to_decimal(m_home, tipo_momio)
odd_under = parse_odds_to_decimal(m_under, tipo_momio)
odd_btts_no = parse_odds_to_decimal(m_btts_no, tipo_momio)

ev_h = calcular_ev(p_home, odd_h)
ev_under = calcular_ev(p_under25, odd_under)
ev_btts_no = calcular_ev(p_btts_no, odd_btts_no)

trap_h = ((fatiga_h + rot_h) >= 0.8) and (odd_h > 2.0) and (ev_h > 0.10)

def get_verdict(ev, is_trap=False):
    if is_trap: return "TRAP LINE", "badge-trap"
    if ev > 0.05: return "BET", "badge-bet"
    elif ev > -0.03: return "MAYBE", "badge-maybe"
    else: return "SKIP", "badge-skip"

v_h, class_h = get_verdict(ev_h, trap_h)
v_dc1x, class_dc1x = get_verdict(calcular_ev(p_dc_1x, 1.25))
v_under, class_under = get_verdict(ev_under)
v_btts_no, class_btts_no = get_verdict(ev_btts_no)

st.markdown("---")
st.markdown("<h3 style='color:#FFDF1B;'>📊 OPCIONES DE APUESTA DETECTADAS</h3>", unsafe_allow_html=True)

st.markdown(f"""
<div class="bet365-card">
    <div>
        <div class="bet365-card-title">Gana {home_team}</div>
        <div class="bet365-card-sub">1X2 {home_team[:3].upper()} ({format_odds_display(odd_h, tipo_momio)}) · Probabilidad {p_home*100:.1f}% · EV {ev_h*100:+.1f}%</div>
    </div>
    <div><span class="b365-badge {class_h}">{v_h}</span></div>
</div>

<div class="bet365-card">
    <div>
        <div class="bet365-card-title">{home_team} o Empate (1X)</div>
        <div class="bet365-card-sub">Doble Oportunidad 1X · Modelo {format_odds_display(1/p_dc_1x, tipo_momio)} · Probabilidad {p_dc_1x*100:.1f}%</div>
    </div>
    <div><span class="b365-badge {class_dc1x}">{v_dc1x}</span></div>
</div>

<div class="bet365-card">
    <div>
        <div class="bet365-card-title">Menos de 2.5 Goles</div>
        <div class="bet365-card-sub">Under 2.5 · Goles esperados {(lam_h+lam_a):.1f} · Probabilidad {p_under25*100:.1f}% · EV {ev_under*100:+.1f}%</div>
    </div>
    <div><span class="b365-badge {class_under}">{v_under}</span></div>
</div>

<div class="bet365-card">
    <div>
        <div class="bet365-card-title">Ambos Equipos Anotan: NO</div>
        <div class="bet365-card-sub">BTTS NO · Modelo {format_odds_display(1/p_btts_no, tipo_momio)} · Probabilidad {p_btts_no*100:.1f}% · EV {ev_btts_no*100:+.1f}%</div>
    </div>
    <div><span class="b365-badge {class_btts_no}">{v_btts_no}</span></div>
</div>
""", unsafe_allow_html=True)
