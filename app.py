import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson

# Configuración de página
st.set_page_config(
    page_title="LA MAÑA PICKS - PREMIER LEAGUE PREDICTIONS",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS PROFESIONALES CYBERPUNK (COMPACTOS Y ALINEADOS)
st.markdown("""
<style>
    .stApp {
        background-color: #050806 !important;
        color: #ffffff !important;
    }
    
    label, p, span, div, .stMarkdown, .stRadio label, .stSlider label {
        color: #e0f2fe !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    
    /* Header compacto */
    .cyber-header {
        background: linear-gradient(135deg, #001f12 0%, #000905 100%);
        border: 1px solid #00FF66;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.25);
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 15px;
    }
    
    .cyber-title {
        color: #FFD700 !important;
        font-weight: 800;
        font-size: 1.15rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0;
    }
    
    .pl-logo-header {
        width: 38px !important;
        height: auto !important;
        filter: brightness(0) invert(1);
    }

    /* Inputs y Selects compactos */
    .stTextInput input {
        background-color: #0b130e !important;
        color: #FFD700 !important;
        border: 1px solid #00FF66 !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        font-size: 0.85rem !important;
        padding: 4px 8px !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #0b130e !important;
        color: #00FF66 !important;
        border: 1px solid #00FF66 !important;
        border-radius: 4px !important;
        min-height: 32px !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="popover"] * {
        background-color: #0b130e !important;
        color: #00FF66 !important;
    }

    /* Historial de Forma (G/E/P) */
    .form-container {
        display: flex;
        gap: 3px;
        align-items: center;
        margin: 4px 0 8px 0;
    }
    .form-box {
        width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.65rem;
        border-radius: 2px;
        color: #000000;
    }
    .form-g { background-color: #00FF66; color: #000; }
    .form-e { background-color: #FFD700; color: #000; }
    .form-p { background-color: #FF0055; color: #FFF; }

    /* Tarjetas de Análisis Compactas y Perfectamente Alineadas */
    .cyber-card {
        background-color: #090f0b;
        border: 1px solid #142218;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    .cyber-card-title {
        font-weight: 700;
        font-size: 0.82rem;
        color: #ffffff;
    }
    .cyber-card-sub {
        font-size: 0.72rem;
        color: #8fa396;
        font-family: monospace;
        margin-top: 1px;
    }

    .card-high { border-left: 4px solid #00FF66 !important; }
    .card-medium { border-left: 4px solid #FF9900 !important; }
    .card-low { border-left: 4px solid #FF0055 !important; }
    .card-star { border: 1.5px solid #FFD700 !important; background: linear-gradient(135deg, #141c00 0%, #090f0b 100%) !important; }

    .cyber-badge {
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 3px;
        font-size: 0.68rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .badge-high { background-color: #00FF66; color: #000000; }
    .badge-medium { background-color: #FF9900; color: #000000; }
    .badge-low { background-color: #FF0055; color: #ffffff; }
    .badge-star { background-color: #FFD700; color: #000000; box-shadow: 0 0 8px rgba(255,215,0,0.4); }

    .stButton>button {
        background: linear-gradient(135deg, #00FF66 0%, #008833 100%) !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.3) !important;
        width: 100% !important;
        text-transform: uppercase !important;
    }
</style>
""", unsafe_allow_html=True)

PL_LOGO = "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"

TEAMS_DATA = {
    "Arsenal": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8, "forma": ["G","G","E","G","G","P","G","G","E","G"]},
    "Aston Villa": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg", "xg": 1.75, "xga": 1.30, "ppda": 11.2, "aereos": 51, "corners": 5.4, "forma": ["G","P","G","E","G","P","G","E","G","P"]},
    "Bournemouth": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg", "xg": 1.40, "xga": 1.55, "ppda": 10.5, "aereos": 48, "corners": 4.9, "forma": ["P","E","G","P","P","G","E","P","G","E"]},
    "Brentford": {"logo": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6, "forma": ["G","P","E","P","G","E","P","G","P","G"]},
    "Brighton": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_FC_crest.svg", "xg": 1.65, "xga": 1.40, "ppda": 9.5, "aereos": 47, "corners": 5.8, "forma": ["E","G","P","G","E","P","G","G","P","E"]},
    "Chelsea": {"logo": "https://upload.wikimedia.org/wikipedia/en/cc/CCFC_logo.svg", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6, "forma": ["G","G","P","E","G","G","P","E","G","G"]},
    "Crystal Palace": {"logo": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo.svg", "xg": 1.35, "xga": 1.30, "ppda": 11.8, "aereos": 53, "corners": 4.8, "forma": ["E","P","G","E","P","P","G","E","P","G"]},
    "Everton": {"logo": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg", "xg": 1.30, "xga": 1.40, "ppda": 12.5, "aereos": 58, "corners": 4.7, "forma": ["P","E","E","G","P","E","P","G","E","P"]},
    "Fulham": {"logo": "https://upload.wikimedia.org/wikipedia/en/a/a8/Fulham_FC_%28shield%29.svg", "xg": 1.40, "xga": 1.50, "ppda": 11.0, "aereos": 50, "corners": 5.1, "forma": ["G","P","E","G","P","G","E","P","P","G"]},
    "Ipswich Town": {"logo": "https://upload.wikimedia.org/wikipedia/en/4/43/Ipswich_Town.svg", "xg": 1.20, "xga": 1.60, "ppda": 13.0, "aereos": 48, "corners": 4.2, "forma": ["P","P","E","P","E","G","P","P","E","P"]},
    "Leicester City": {"logo": "https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg", "xg": 1.25, "xga": 1.55, "ppda": 12.8, "aereos": 49, "corners": 4.3, "forma": ["P","E","G","P","P","E","P","G","P","P"]},
    "Liverpool": {"logo": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1, "forma": ["G","G","G","E","G","G","P","G","G","E"]},
    "Manchester City": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5, "forma": ["G","G","E","G","G","G","P","G","E","G"]},
    "Manchester United": {"logo": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg", "xg": 1.60, "xga": 1.45, "ppda": 10.8, "aereos": 50, "corners": 5.9, "forma": ["P","G","E","P","G","E","P","G","P","E"]},
    "Newcastle United": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg", "xg": 1.70, "xga": 1.20, "ppda": 9.9, "aereos": 53, "corners": 6.1, "forma": ["G","P","G","E","G","P","G","G","E","P"]},
    "Nottingham Forest": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_logo.svg", "xg": 1.25, "xga": 1.50, "ppda": 13.2, "aereos": 51, "corners": 4.1, "forma": ["E","G","P","G","E","P","G","P","E","P"]},
    "Southampton": {"logo": "https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg", "xg": 1.15, "xga": 1.65, "ppda": 11.5, "aereos": 46, "corners": 4.5, "forma": ["P","P","P","E","P","G","P","P","E","P"]},
    "Tottenham Hotspur": {"logo": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49, "corners": 6.3, "forma": ["G","P","G","G","E","P","G","P","G","E"]},
    "West Ham United": {"logo": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg", "xg": 1.35, "xga": 1.60, "ppda": 13.5, "aereos": 54, "corners": 4.5, "forma": ["P","E","G","P","P","E","G","P","P","E"]},
    "Wolverhampton": {"logo": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg", "xg": 1.30, "xga": 1.55, "ppda": 12.0, "aereos": 49, "corners": 4.4, "forma": ["P","E","P","G","P","P","E","G","P","P"]}
}

def parse_odds_to_decimal(val_str, format_type):
    try:
        val = float(val_str)
        if format_type == "Decimales": return val
        return (val / 100.0) + 1.0 if val > 0 else (100.0 / abs(val)) + 1.0
    except:
        return 2.00

def format_odds_display(decimal_val, format_type):
    if format_type == "Decimales": return f"{decimal_val:.2f}"
    if decimal_val <= 1.0: return "+100"
    if decimal_val >= 2.0: return f"+{int(round((decimal_val - 1.0) * 100))}"
    return f"-{int(round(100.0 / (decimal_val - 1.0)))}"

def calcular_ev(prob, cuota_decimal):
    return (prob * cuota_decimal) - 1.0

def clasificar_opcion(prob, ev):
    prob_pct = prob * 100.0
    if prob_pct >= 75.0:
        return ("💎 APUESTA ESTRELLA", "card-star", "badge-star") if ev > 0.0 else ("HIGH CONFIDENCE", "card-high", "badge-high")
    elif 60.0 <= prob_pct < 75.0:
        return "MEDIUM PROBABILITY", "card-medium", "badge-medium"
    return "LOW PROBABILITY", "card-low", "badge-low"

def generar_badges_forma(lista_forma):
    html = '<div class="form-container">'
    for res in lista_forma:
        cls = "form-g" if res == "G" else ("form-e" if res == "E" else "form-p")
        html += f'<div class="form-box {cls}">{res}</div>'
    html += '</div>'
    return html

def calcular_lambdas(h_team, a_team, fatiga_h, rot_h, fatiga_a, rot_a):
    dh, da = TEAMS_DATA[h_team], TEAMS_DATA[a_team]
    avg_h, avg_a = 1.55, 1.25
    att_h, def_h = dh["xg"] / avg_h, dh["xga"] / avg_a
    att_a, def_a = da["xg"] / avg_a, da["xga"] / avg_h
    tactical_h = (12.0 / max(dh["ppda"], 5.0)) * (dh["aereos"] / 50.0)
    tactical_a = (12.0 / max(da["ppda"], 5.0)) * (da["aereos"] / 50.0)
    fatigue_h = 1.0 - (fatiga_h * 0.12 + rot_h * 0.10)
    fatigue_a = 1.0 - (fatiga_a * 0.12 + rot_a * 0.10)
    lambda_h = avg_h * att_h * def_a * tactical_h * fatigue_h
    lambda_a = avg_a * att_a * def_h * tactical_a * fatigue_a
    return max(lambda_h, 0.2), max(lambda_a, 0.15)

def generar_matriz(lambda_h, lambda_a, max_goles=8):
    mat = np.zeros((max_goles, max_goles))
    for h in range(max_goles):
        for a in range(max_goles):
            mat[h, a] = poisson.pmf(h, lambda_h) * poisson.pmf(a, lambda_a)
    return mat / np.sum(mat)

def calcular_prob_ha(linea_str, is_local, p_1, p_x, p_2, matriz):
    if linea_str == "+0.5": return (p_1 + p_x) if is_local else (p_2 + p_x)
    elif linea_str == "-0.5": return p_1 if is_local else p_2
    elif linea_str == "0 (DNB)": return (p_1 / (p_1 + p_2)) if is_local else (p_2 / (p_1 + p_2))
    elif linea_str == "+1.0":
        return float(sum(matriz[h, a] for h in range(8) for a in range(8) if (h + 1.0) > a)) if is_local else float(sum(matriz[h, a] for h in range(8) for a in range(8) if (a + 1.0) > h))
    elif linea_str == "-1.0":
        return float(sum(matriz[h, a] for h in range(8) for a in range(8) if h > (a + 1.0))) if is_local else float(sum(matriz[h, a] for h in range(8) for a in range(8) if a > (h + 1.0)))
    return 0.5

# ENCABEZADO
st.markdown(f"""
<div class="cyber-header">
    <img src="{PL_LOGO}" class="pl-logo-header">
    <h1 class="cyber-title">LA MAÑA PICKS - PREMIER LEAGUE PREDICTIONS</h1>
</div>
""", unsafe_allow_html=True)

# ESTRUCTURA DE 2 COLUMNAS: IZQUIERDA (ANÁLISIS) / DERECHA (DATOS Y MOMIOS)
col_left_panel, col_right_panel = st.columns([5, 7])

# ==============================================================================
# COLUMNA DERECHA: DATOS DEL ENCUENTRO, HISTORIAL Y MOMIOS
# ==============================================================================
with col_right_panel:
    st.markdown("<h3 style='color:#FFD700; font-size:1.1rem; margin-bottom:10px;'>⚡ DATOS Y CONFIGURACIÓN DEL ENCUENTRO</h3>", unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        home_team = st.selectbox("Equipo Local", list(TEAMS_DATA.keys()), index=3)
        st.image(TEAMS_DATA[home_team]["logo"], width=32)
        st.caption("Últimos 10 partidos:")
        st.markdown(generar_badges_forma(TEAMS_DATA[home_team]["forma"]), unsafe_allow_html=True)
        fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
        rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

    with col_t2:
        away_team = st.selectbox("Equipo Visitante", list(TEAMS_DATA.keys()), index=17)
        st.image(TEAMS_DATA[away_team]["logo"], width=32)
        st.caption("Últimos 10 partidos:")
        st.markdown(generar_badges_forma(TEAMS_DATA[away_team]["forma"]), unsafe_allow_html=True)
        fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
        rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

    # CÁLCULOS
    lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a)
    matriz_ft = generar_matriz(lam_h, lam_a)

    lam_h_ht, lam_a_ht = lam_h * 0.45, lam_a * 0.45
    matriz_ht = generar_matriz(lam_h_ht, lam_a_ht)

    p_1_ft, p_x_ft, p_2_ft = float(np.sum(np.tril(matriz_ft, -1))), float(np.sum(np.diag(matriz_ft))), float(np.sum(np.triu(matriz_ft, 1)))
    p_1_ht, p_x_ht, p_2_ht = float(np.sum(np.tril(matriz_ht, -1))), float(np.sum(np.diag(matriz_ht))), float(np.sum(np.triu(matriz_ht, 1)))

    st.markdown("---")
    
    col_head, col_opt = st.columns([2, 2])
    with col_head:
        st.markdown("<h4 style='color:#00FF66; font-size:0.95rem; margin:0;'>⚡ INGRESO DE MOMIOS</h4>", unsafe_allow_html=True)
    with col_opt:
        tipo_momio = st.radio("Formato Momios:", ["Decimales", "Americanos"], horizontal=True)

    def default_val(prob): return format_odds_display(1/prob if prob > 0 else 2.0, tipo_momio)

    # 1 Y 2. 1X2 Y DOBLE OPORTUNIDAD
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-bottom:2px;'>1. RESULTADO FINAL (1X2) & 2. DOBLE OPORTUNIDAD</p>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: m_1_ft = st.text_input(f"1X2 {home_team[:3]}", value=default_val(p_1_ft))
    with c2: m_x_ft = st.text_input("Empate X", value=default_val(p_x_ft))
    with c3: m_2_ft = st.text_input(f"1X2 {away_team[:3]}", value=default_val(p_2_ft))
    with c4: m_1x = st.text_input("DC 1X", value=default_val(p_1_ft + p_x_ft))
    with c5: m_x2 = st.text_input("DC X2", value=default_val(p_2_ft + p_x_ft))

    # 3. TOTAL DE GOLES (FT)
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-top:8px; margin-bottom:2px;'>3. TOTAL DE GOLES (FT)</p>", unsafe_allow_html=True)
    cg1, cg2, cg3 = st.columns([2, 1, 1])
    with cg1:
        linea_goles_ft = st.slider("Línea Goles FT", 1.5, 4.5, 2.5, step=1.0)
        p_under_goles = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h + a < linea_goles_ft))
        p_over_goles = 1.0 - p_under_goles
    with cg2: m_over_goles = st.text_input(f"Over {linea_goles_ft}", value=default_val(p_over_goles))
    with cg3: m_under_goles = st.text_input(f"Under {linea_goles_ft}", value=default_val(p_under_goles))

    # 4 Y 5. BTTS Y CÓRNERS FT
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-top:8px; margin-bottom:2px;'>4. AMBOS ANOTAN & 5. TOTAL CÓRNERS (FT)</p>", unsafe_allow_html=True)
    p_btts_yes = float(sum(matriz_ft[h, a] for h in range(1, 8) for a in range(1, 8)))
    exp_corners_ft = TEAMS_DATA[home_team]["corners"] + TEAMS_DATA[away_team]["corners"]

    cm1, cm2, cm3, cm4, cm5 = st.columns([1, 1, 2, 1, 1])
    with cm1: m_btts_yes = st.text_input("BTTS SÍ", value=default_val(p_btts_yes))
    with cm2: m_btts_no = st.text_input("BTTS NO", value=default_val(1.0 - p_btts_yes))
    with cm3:
        linea_corners_ft = st.slider("Línea Córners FT", 8.5, 12.5, 9.5, step=1.0)
        p_under_corners_ft = float(poisson.cdf(int(linea_corners_ft), exp_corners_ft))
        p_over_corners_ft = 1.0 - p_under_corners_ft
    with cm4: m_corners_ft_over = st.text_input(f"Córners >{linea_corners_ft}", value=default_val(p_over_corners_ft))
    with cm5: m_corners_ft_under = st.text_input(f"Córners <{linea_corners_ft}", value=default_val(p_under_corners_ft))

    # 6. HÁNDICAP ASIÁTICO
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-top:8px; margin-bottom:2px;'>6. HÁNDICAP ASIÁTICO</p>", unsafe_allow_html=True)
    ha_c1, ha_c2, ha_c3, ha_c4 = st.columns(4)

    with ha_c1:
        linea_ha_h = st.selectbox(f"AH {home_team[:3]}", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=0, key="ha_h_select")
        p_ha_h = calcular_prob_ha(linea_ha_h, True, p_1_ft, p_x_ft, p_2_ft, matriz_ft)
    with ha_c2: m_ha_h = st.text_input("Momio AH Local", value=default_val(p_ha_h))

    with ha_c3:
        linea_ha_a = st.selectbox(f"AH {away_team[:3]}", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=1, key="ha_a_select")
        p_ha_a = calcular_prob_ha(linea_ha_a, False, p_1_ft, p_x_ft, p_2_ft, matriz_ft)
    with ha_c4: m_ha_a = st.text_input("Momio AH Visita", value=default_val(p_ha_a))

    # 7 Y 8. 1RA MITAD Y GOLES HT
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-top:8px; margin-bottom:2px;'>7. 1RA MITAD 1X2 & 8. GOLES 1RA MITAD</p>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1: m_1_ht = st.text_input(f"HT {home_team[:3]}", value=default_val(p_1_ht))
    with h2: m_x_ht = st.text_input("HT Empate", value=default_val(p_x_ht))
    with h3: m_2_ht = st.text_input(f"HT {away_team[:3]}", value=default_val(p_2_ht))

    p_over05_ht = 1.0 - (poisson.pmf(0, lam_h_ht) * poisson.pmf(0, lam_a_ht))
    p_under05_ht = 1.0 - p_over05_ht
    p_under15_ht = float(sum(matriz_ht[h, a] for h in range(8) for a in range(8) if h + a < 1.5))
    p_over15_ht = 1.0 - p_under15_ht

    hg1, hg2, hg3, hg4 = st.columns(4)
    with hg1: m_ht_o05 = st.text_input("HT Over 0.5", value=default_val(p_over05_ht))
    with hg2: m_ht_u05 = st.text_input("HT Under 0.5", value=default_val(p_under05_ht))
    with hg3: m_ht_o15 = st.text_input("HT Over 1.5", value=default_val(p_over15_ht))
    with hg4: m_ht_u15 = st.text_input("HT Under 1.5", value=default_val(p_under15_ht))

    # 9, 10 Y 11. CÓRNERS HT, DNB Y GANA MITAD
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#FFD700; margin-top:8px; margin-bottom:2px;'>9. CÓRNERS HT | 10. DNB | 11. GANA CUALQ. MITAD</p>", unsafe_allow_html=True)
    c_ht1, c_ht2, c_ht3, c_ht4, c_ht5, c_ht6, c_ht7 = st.columns([1.5, 1, 1, 1, 1, 1, 1])

    with c_ht1:
        linea_corners_ht = st.slider("Córners HT", 3.0, 6.0, 4.5, step=0.5)
        exp_corners_ht = exp_corners_ft * 0.45
        p_under_corners_ht = float(poisson.cdf(int(linea_corners_ht), exp_corners_ht))
        p_over_corners_ht = 1.0 - p_under_corners_ht

    with c_ht2: m_corners_ht_over = st.text_input(f"HT >{linea_corners_ht}", value=default_val(p_over_corners_ht))
    with c_ht3: m_corners_ht_under = st.text_input(f"HT <{linea_corners_ht}", value=default_val(p_under_corners_ht))

    p_dnb_h = p_1_ft / (p_1_ft + p_2_ft) if (p_1_ft + p_2_ft) > 0 else 0.5
    p_dnb_a = 1.0 - p_dnb_h

    with c_ht4: m_dnb_h = st.text_input(f"DNB {home_team[:3]}", value=default_val(p_dnb_h))
    with c_ht5: m_dnb_a = st.text_input(f"DNB {away_team[:3]}", value=default_val(p_dnb_a))

    p_win_any_h = 1.0 - ((1.0 - p_1_ht) * (1.0 - p_1_ft))
    p_win_any_a = 1.0 - ((1.0 - p_2_ht) * (1.0 - p_2_ft))

    with c_ht6: m_win_any_h = st.text_input("Gana L", value=default_val(p_win_any_h))
    with c_ht7: m_win_any_a = st.text_input("Gana V", value=default_val(p_win_any_a))

    st.markdown("<br>", unsafe_allow_html=True)
    recalcular = st.button("⚡ RECALCULAR OPORTUNIDADES DE APUESTA", use_container_width=True)

# ==============================================================================
# COLUMNA IZQUIERDA: ANÁLISIS MATRIX DE OPORTUNIDADES (ALINEADO Y COMPACTO)
# ==============================================================================
with col_left_panel:
    st.markdown("<h3 style='color:#00FF66; font-size:1.1rem; margin-bottom:10px;'>📊 ANÁLISIS MATRIX DE OPORTUNIDADES</h3>", unsafe_allow_html=True)

    mercados_list = [
        {"tit": f"1. Resultado Final (1X2): Gana Local ({home_team})", "sub": "1X2 Local", "prob": p_1_ft, "odd": m_1_ft},
        {"tit": f"1. Resultado Final (1X2): Gana Visitante ({away_team})", "sub": "1X2 Visitante", "prob": p_2_ft, "odd": m_2_ft},
        {"tit": f"2. Doble Oportunidad: {home_team} o Empate (1X)", "sub": "1X Doble Chance", "prob": p_1_ft + p_x_ft, "odd": m_1x},
        {"tit": f"2. Doble Oportunidad: {away_team} o Empate (X2)", "sub": "X2 Doble Chance", "prob": p_2_ft + p_x_ft, "odd": m_x2},
        {"tit": f"3. Total de Goles (FT): Over {linea_goles_ft}", "sub": f"Goles Over {linea_goles_ft}", "prob": p_over_goles, "odd": m_over_goles},
        {"tit": f"3. Total de Goles (FT): Under {linea_goles_ft}", "sub": f"Goles Under {linea_goles_ft}", "prob": p_under_goles, "odd": m_under_goles},
        {"tit": "4. Ambos Equipos Anotan: SÍ", "sub": "BTTS YES", "prob": p_btts_yes, "odd": m_btts_yes},
        {"tit": "4. Ambos Equipos Anotan: NO", "sub": "BTTS NO", "prob": 1.0 - p_btts_yes, "odd": m_btts_no},
        {"tit": f"5. Total de Córners (FT): Over {linea_corners_ft}", "sub": f"Córners Over {linea_corners_ft}", "prob": p_over_corners_ft, "odd": m_corners_ft_over},
        {"tit": f"5. Total de Córners (FT): Under {linea_corners_ft}", "sub": f"Córners Under {linea_corners_ft}", "prob": p_under_corners_ft, "odd": m_corners_ft_under},
        {"tit": f"6. Hándicap Asiático Local: {home_team} ({linea_ha_h})", "sub": f"AH Local {linea_ha_h}", "prob": p_ha_h, "odd": m_ha_h},
        {"tit": f"6. Hándicap Asiático Visitante: {away_team} ({linea_ha_a})", "sub": f"AH Visita {linea_ha_a}", "prob": p_ha_a, "odd": m_ha_a},
        {"tit": f"7. 1ra Mitad Resultado: Gana Local ({home_team})", "sub": "1st Half Local", "prob": p_1_ht, "odd": m_1_ht},
        {"tit": f"7. 1ra Mitad Resultado: Gana Visitante ({away_team})", "sub": "1st Half Visitante", "prob": p_2_ht, "odd": m_2_ht},
        {"tit": "8. Goles 1ra Mitad: Over 0.5", "sub": "HT Over 0.5", "prob": p_over05_ht, "odd": m_ht_o05},
        {"tit": "8. Goles 1ra Mitad: Under 0.5", "sub": "HT Under 0.5", "prob": p_under05_ht, "odd": m_ht_u05},
        {"tit": "8. Goles 1ra Mitad: Over 1.5", "sub": "HT Over 1.5", "prob": p_over15_ht, "odd": m_ht_o15},
        {"tit": "8. Goles 1ra Mitad: Under 1.5", "sub": "HT Under 1.5", "prob": p_under15_ht, "odd": m_ht_u15},
        {"tit": f"9. Córners 1ra Mitad: Over {linea_corners_ht}", "sub": f"HT Córners Over {linea_corners_ht}", "prob": p_over_corners_ht, "odd": m_corners_ht_over},
        {"tit": f"9. Córners 1ra Mitad: Under {linea_corners_ht}", "sub": f"HT Córners Under {linea_corners_ht}", "prob": p_under_corners_ht, "odd": m_corners_ht_under},
        {"tit": f"10. Empate No Acción: {home_team}", "sub": "DNB Local", "prob": p_dnb_h, "odd": m_dnb_h},
        {"tit": f"10. Empate No Acción: {away_team}", "sub": "DNB Visitante", "prob": p_dnb_a, "odd": m_dnb_a},
        {"tit": f"11. Gana Cualquier Mitad: {home_team}", "sub": "Win Either Half Local", "prob": p_win_any_h, "odd": m_win_any_h},
        {"tit": f"11. Gana Cualquier Mitad: {away_team}", "sub": "Win Either Half Visitante", "prob": p_win_any_a, "odd": m_win_any_a}
    ]

    for item in mercados_list:
        dec_odd = parse_odds_to_decimal(item['odd'], tipo_momio)
        ev = calcular_ev(item['prob'], dec_odd)
        lbl, card, badge = clasificar_opcion(item['prob'], ev)
        
        st.markdown(f"""
        <div class="cyber-card {card}">
            <div>
                <div class="cyber-card-title">{item['tit']}</div>
                <div class="cyber-card-sub">{item['sub']} | Prob: <b style="color:#00FF66;">{item['prob']*100:.1f}%</b> | EV: <b style="color:#FFD700;">{ev*100:+.1f}%</b></div>
            </div>
            <div><span class="cyber-badge {badge}">{lbl}</span></div>
        </div>
        """, unsafe_allow_html=True)
