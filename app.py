import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
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
    
    /* Inputs y Formularios */
    .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #121915 !important;
        color: #FFD700 !important;
        border: 1px solid #00FF66 !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        box-shadow: inset 0 0 5px rgba(0, 255, 102, 0.2);
    }

    /* Targetas de Apuesta */
    .cyber-card {
        background-color: #0d1410;
        border: 1px solid #1a2a20;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    .card-high { border-left: 6px solid #00FF66 !important; box-shadow: -5px 0 12px rgba(0, 255, 102, 0.2); }
    .card-medium { border-left: 6px solid #FF9900 !important; box-shadow: -5px 0 12px rgba(255, 153, 0, 0.2); }
    .card-low { border-left: 6px solid #FF0055 !important; box-shadow: -5px 0 12px rgba(255, 0, 85, 0.2); }
    .card-star { border: 2px solid #FFD700 !important; background: linear-gradient(135deg, #182000 0%, #0d1410 100%) !important; box-shadow: 0 0 18px rgba(255, 215, 0, 0.4) !important; }

    /* Badges */
    .cyber-badge {
        font-weight: 900;
        padding: 8px 16px;
        border-radius: 5px;
        font-size: 0.85rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-high { background-color: #00FF66; color: #000000; }
    .badge-medium { background-color: #FF9900; color: #000000; }
    .badge-low { background-color: #FF0055; color: #ffffff; }
    .badge-star { background-color: #FFD700; color: #000000; }

    /* Botón Cyberpunk */
    .stButton>button {
        background: linear-gradient(135deg, #00FF66 0%, #009933 100%) !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.5) !important;
        width: 100% !important;
        text-transform: uppercase !important;
    }
</style>
""", unsafe_allow_html=True)

PL_LOGO = "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"

TEAMS_DATA_FALLBACK = {
    "Arsenal": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8},
    "Aston Villa": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51, "corners": 5.4},
    "Brentford": {"logo": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6},
    "Chelsea": {"logo": "https://upload.wikimedia.org/wikipedia/en/cc/CCFC_logo.svg", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6},
    "Liverpool": {"logo": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1},
    "Manchester City": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5},
    "Tottenham": {"logo": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49, "corners": 6.3}
}

TEAMS_DATA = TEAMS_DATA_FALLBACK

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

def clasificar_opcion(prob, ev):
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
    <span style="color:#00FF66; font-weight:bold; font-family:monospace;">PRO ENGINE v3.0</span>
</div>
""", unsafe_allow_html=True)

# SELECCIÓN DE EQUIPOS
col_team1, col_team2 = st.columns(2)
with col_team1:
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=2)
    st.image(TEAMS_DATA[home_team]["logo"], width=45)
    c1, c2 = st.columns(2)
    with c1: fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
    with c2: rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_team2:
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=6)
    st.image(TEAMS_DATA[away_team]["logo"], width=45)
    c3, c4 = st.columns(2)
    with c3: fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    with c4: rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

# MODELADO MATEMÁTICO COMPLETO
lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a, 1.0, 0.95)
matriz_full = generar_matriz(lam_h, lam_a)

# 1. Tiempos Completos (FT)
p_home_ft = float(np.sum(np.tril(matriz_full, -1)))
p_draw_ft = float(np.sum(np.diag(matriz_full)))
p_away_ft = float(np.sum(np.triu(matriz_full, 1)))

# 2. 1ra Mitad (HT) - Lambdas ajustadas a 45 min
lam_h_ht, lam_a_ht = lam_h * 0.45, lam_a * 0.45
matriz_ht = generar_matriz(lam_h_ht, lam_a_ht)
p_home_ht = float(np.sum(np.tril(matriz_ht, -1)))
p_draw_ht = float(np.sum(np.diag(matriz_ht)))
p_away_ht = float(np.sum(np.triu(matriz_ht, 1)))

p_over05_ht = 1.0 - (poisson.pmf(0, lam_h_ht) * poisson.pmf(0, lam_a_ht))
p_under05_ht = 1.0 - p_over05_ht
p_under15_ht = float(sum(matriz_ht[h, a] for h in range(7) for a in range(7) if h + a < 1.5))
p_over15_ht = 1.0 - p_under15_ht

# 3. Hándicaps Asiáticos (FT)
p_ah_h_0 = p_home_ft / (p_home_ft + p_away_ft) if (p_home_ft + p_away_ft) > 0 else 0.5 # Draw No Bet / 0
p_ah_a_0 = p_away_ft / (p_home_ft + p_away_ft) if (p_home_ft + p_away_ft) > 0 else 0.5
p_ah_h_plus05 = p_home_ft + p_draw_ft
p_ah_h_minus05 = p_home_ft
p_ah_h_plus10 = float(sum(matriz_full[h, a] for h in range(7) for a in range(7) if (h + 1.0) > a))
p_ah_h_minus10 = float(sum(matriz_full[h, a] for h in range(7) for a in range(7) if h > (a + 1.0)))

# 4. Gana Cualquier Mitad
p_win_any_h = 1.0 - ((1.0 - p_home_ht) * (1.0 - p_home_ft))

# 5. Córners 1ra Mitad
linea_corners_ht = st.sidebar.slider("Línea Córners 1ra Mitad", 3.0, 6.0, 4.5, step=0.5)
exp_corners_ht = (TEAMS_DATA[home_team].get("corners", 5.0) + TEAMS_DATA[away_team].get("corners", 5.0)) * 0.45
p_over_corners_ht = float(1.0 - poisson.cdf(int(linea_corners_ht), exp_corners_ht))

st.markdown("---")

# METER MOMIOS
col_head, col_opt = st.columns([3, 2])
with col_head:
    st.markdown("<h3 style='color:#FFD700; margin:0;'>⚡ INGRESO DE MOMIOS (TODOS LOS MERCADOS)</h3>", unsafe_allow_html=True)
with col_opt:
    tipo_momio = st.radio("Formato de Momios:", ["Decimales", "Americanos"], horizontal=True)

def default_val(prob):
    dec = 1/prob if prob > 0 else 2.0
    return format_odds_display(dec, tipo_momio)

# BLOQUES DE INGRESO DE MOMIOS SEPARADOS POR CATEGORÍA
st.markdown("#### ⚽ 1X2 & 1RA MITAD")
f1, f2, f3, f4, f5 = st.columns(5)
with f1: m_home = st.text_input(f"Gana {home_team[:3]} (FT)", value=default_val(p_home_ft))
with f2: m_away = st.text_input(f"Gana {away_team[:3]} (FT)", value=default_val(p_away_ft))
with f3: m_ht_h = st.text_input(f"1ra Mitad {home_team[:3]}", value=default_val(p_home_ht))
with f4: m_ht_d = st.text_input("1ra Mitad Empate", value=default_val(p_draw_ht))
with f5: m_dnb_h = st.text_input("Empate No Acción Local", value=default_val(p_ah_h_0))

st.markdown("#### 🎯 HÁNDICAPS ASIÁTICOS")
h1, h2, h3, h4 = st.columns(4)
with h1: m_ah_h_p05 = st.text_input(f"{home_team[:3]} AH +0.5", value=default_val(p_ah_h_plus05))
with h2: m_ah_h_m05 = st.text_input(f"{home_team[:3]} AH -0.5", value=default_val(p_ah_h_minus05))
with h3: m_ah_h_p10 = st.text_input(f"{home_team[:3]} AH +1.0", value=default_val(p_ah_h_plus10))
with h4: m_ah_h_m10 = st.text_input(f"{home_team[:3]} AH -1.0", value=default_val(p_ah_h_minus10))

st.markdown("#### 🚩 GOLES 1RA MITAD & CÓRNERS")
g1, g2, g3 = st.columns(3)
with g1: m_ht_o05 = st.text_input("Goles 1ra Mitad Over 0.5", value=default_val(p_over05_ht))
with g2: m_ht_u15 = st.text_input("Goles 1ra Mitad Under 1.5", value=default_val(p_under15_ht))
with g3: m_corn_ht = st.text_input(f"Córners 1ra Mitad > {linea_corners_ht}", value=default_val(p_over_corners_ht))

st.markdown("<br>", unsafe_allow_html=True)
recalcular = st.button("⚡ RECALCULAR OPORTUNIDADES DE APUESTA", use_container_width=True)

# PROCESAR Y MOSTRAR RESULTADOS
st.markdown("---")
st.markdown("<h3 style='color:#00FF66;'>📊 ANÁLISIS MATRIX DE OPORTUNIDADES</h3>", unsafe_allow_html=True)

opciones = [
    {"titulo": f"1ra Mitad: Gana {home_team}", "sub": f"Resultado 1ra Mitad", "prob": p_home_ht, "ev": calcular_ev(p_home_ht, parse_odds_to_decimal(m_ht_h, tipo_momio))},
    {"titulo": f"Empate No Acción: {home_team}", "sub": "Draw No Bet (DNB / AH 0)", "prob": p_ah_h_0, "ev": calcular_ev(p_ah_h_0, parse_odds_to_decimal(m_dnb_h, tipo_momio))},
    {"titulo": f"Hándicap Asiático {home_team} (+0.5)", "sub": "AH +0.5", "prob": p_ah_h_plus05, "ev": calcular_ev(p_ah_h_plus05, parse_odds_to_decimal(m_ah_h_p05, tipo_momio))},
    {"titulo": f"Hándicap Asiático {home_team} (-0.5)", "sub": "AH -0.5", "prob": p_ah_h_minus05, "ev": calcular_ev(p_ah_h_minus05, parse_odds_to_decimal(m_ah_h_m05, tipo_momio))},
    {"titulo": f"Hándicap Asiático {home_team} (+1.0)", "sub": "AH +1.0", "prob": p_ah_h_plus10, "ev": calcular_ev(p_ah_h_plus10, parse_odds_to_decimal(m_ah_h_p10, tipo_momio))},
    {"titulo": f"Gana Cualquier Mitad: {home_team}", "sub": "Win Either Half", "prob": p_win_any_h, "ev": 0.05},
    {"titulo": "1ra Mitad: Over 0.5 Goles", "sub": "Goles 1st Half > 0.5", "prob": p_over05_ht, "ev": calcular_ev(p_over05_ht, parse_odds_to_decimal(m_ht_o05, tipo_momio))},
    {"titulo": f"1ra Mitad Córners: Over {linea_corners_ht}", "sub": f"Córners HT > {linea_corners_ht}", "prob": p_over_corners_ht, "ev": calcular_ev(p_over_corners_ht, parse_odds_to_decimal(m_corn_ht, tipo_momio))}
]

for op in opciones:
    lbl, card, badge = clasificar_opcion(op['prob'], op['ev'])
    st.markdown(f"""
    <div class="cyber-card {card}">
        <div>
            <div class="cyber-card-title">{op['titulo']}</div>
            <div class="cyber-card-sub">{op['sub']} | Probabilidad: <b style="color:#00FF66;">{op['prob']*100:.1f}%</b> | EV: <b style="color:#FFD700;">{op['ev']*100:+.1f}%</b></div>
        </div>
        <div><span class="cyber-badge {badge}">{lbl}</span></div>
    </div>
    """, unsafe_allow_html=True)
