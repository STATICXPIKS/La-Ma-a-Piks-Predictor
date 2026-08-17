import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson

# Configuración de página
st.set_page_config(
    page_title="Premier League Predictor - Cyberpunk Bet365",
    layout="wide",
    page_icon="⚽"
)

# ESTILOS CSS CYBERPUNK - BET365 (VERDE Y ORO)
st.markdown("""
<style>
    .stApp {
        background-color: #070a08 !important;
        color: #ffffff !important;
    }
    
    label, p, span, div, .stMarkdown, .stRadio label, .stSlider label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .cyber-header {
        background: linear-gradient(135deg, #002b1b 0%, #00120b 100%);
        border: 2px solid #00FF66;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.4);
        padding: 15px 25px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .cyber-title {
        color: #FFD700 !important;
        font-weight: 900;
        font-size: 1.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }
    
    .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #121915 !important;
        color: #FFD700 !important;
        border: 1px solid #00FF66 !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }

    .cyber-card {
        background-color: #0d1410;
        border: 1px solid #1a2a20;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .cyber-card-title {
        font-weight: 800;
        font-size: 1.05rem;
        color: #ffffff;
    }
    .cyber-card-sub {
        font-size: 0.85rem;
        color: #a0b0a5;
        font-family: monospace;
        margin-top: 2px;
    }

    .card-high { border-left: 6px solid #00FF66 !important; box-shadow: -5px 0 10px rgba(0, 255, 102, 0.2); }
    .card-medium { border-left: 6px solid #FF9900 !important; box-shadow: -5px 0 10px rgba(255, 153, 0, 0.2); }
    .card-low { border-left: 6px solid #FF0055 !important; box-shadow: -5px 0 10px rgba(255, 0, 85, 0.2); }
    .card-star { border: 2px solid #FFD700 !important; background: linear-gradient(135deg, #182000 0%, #0d1410 100%) !important; box-shadow: 0 0 15px rgba(255, 215, 0, 0.4) !important; }

    .cyber-badge {
        font-weight: 900;
        padding: 6px 14px;
        border-radius: 5px;
        font-size: 0.8rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-high { background-color: #00FF66; color: #000000; }
    .badge-medium { background-color: #FF9900; color: #000000; }
    .badge-low { background-color: #FF0055; color: #ffffff; }
    .badge-star { background-color: #FFD700; color: #000000; }

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

TEAMS_DATA = {
    "Arsenal": {"logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg", "xg": 2.10, "xga": 0.85, "ppda": 8.8, "aereos": 55, "corners": 6.8},
    "Brentford": {"logo": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg", "xg": 1.50, "xga": 1.45, "ppda": 12.1, "aereos": 56, "corners": 4.6},
    "Chelsea": {"logo": "https://upload.wikimedia.org/wikipedia/en/cc/CCFC_logo.svg", "xg": 1.80, "xga": 1.25, "ppda": 9.8, "aereos": 52, "corners": 5.6},
    "Liverpool": {"logo": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg", "xg": 2.20, "xga": 1.00, "ppda": 8.5, "aereos": 54, "corners": 7.1},
    "Manchester City": {"logo": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg", "xg": 2.25, "xga": 0.80, "ppda": 8.2, "aereos": 52, "corners": 7.5},
    "Tottenham": {"logo": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg", "xg": 1.85, "xga": 1.50, "ppda": 9.1, "aereos": 49, "corners": 6.3}
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

# ENCABEZADO
st.markdown(f"""
<div class="cyber-header">
    <div style="display:flex; align-items:center; gap:15px;">
        <img src="{PL_LOGO}" style="width:45px; filter: brightness(0) invert(1);">
        <h1 class="cyber-title">BET365 PREMIER LEAGUE // ALL-MARKETS PREDICTOR</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# SELECCIÓN DE EQUIPOS Y CONFIGURACIÓN DE LÍNEAS
col_t1, col_t2 = st.columns(2)
with col_t1:
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=1)
    fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
    rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_t2:
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=5)
    fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

st.markdown("### ⚙️ AJUSTE DINÁMICO DE LÍNEAS DE MERCADO")
c_line1, c_line2, c_line3 = st.columns(3)
with c_line1:
    linea_goles = st.slider("3. Línea Total de Goles (FT)", 1.5, 4.5, 2.5, step=1.0)
with c_line2:
    linea_corners_ft = st.slider("5. Línea Total de Córners (FT)", 8.5, 12.5, 9.5, step=1.0)
with c_line3:
    linea_corners_ht = st.slider("9. Córners 1ra Mitad (HT)", 3.0, 6.0, 4.5, step=0.5)

# CÁLCULOS ESTADÍSTICOS
lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a)
matriz_ft = generar_matriz(lam_h, lam_a)

lam_h_ht, lam_a_ht = lam_h * 0.45, lam_a * 0.45
matriz_ht = generar_matriz(lam_h_ht, lam_a_ht)

# 1. RESULTADO FINAL (1X2)
p_1_ft, p_x_ft, p_2_ft = float(np.sum(np.tril(matriz_ft, -1))), float(np.sum(np.diag(matriz_ft))), float(np.sum(np.triu(matriz_ft, 1)))

# 2. DOBLE OPORTUNIDAD
p_1x = p_1_ft + p_x_ft
p_x2 = p_2_ft + p_x_ft
p_12 = p_1_ft + p_2_ft

# 3. TOTAL GOLES (OVER / UNDER)
p_under_goles = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h + a < linea_goles))
p_over_goles = 1.0 - p_under_goles

# 4. AMBOS EQUIPOS ANOTAN (BTTS)
p_btts_yes = float(sum(matriz_ft[h, a] for h in range(1, 8) for a in range(1, 8)))
p_btts_no = 1.0 - p_btts_yes

# 5. TOTAL DE CÓRNERS (FT)
exp_corners_ft = TEAMS_DATA[home_team]["corners"] + TEAMS_DATA[away_team]["corners"]
p_over_corners_ft = float(1.0 - poisson.cdf(int(linea_corners_ft), exp_corners_ft))

# 6. HÁNDICAP ASIÁTICO (+0.5, -0.5, 0, +1.0, -1.0)
p_ah_h_plus05 = p_1_ft + p_x_ft
p_ah_h_minus05 = p_1_ft
p_ah_h_0 = p_1_ft / (p_1_ft + p_2_ft) if (p_1_ft + p_2_ft) > 0 else 0.5 # Empate No Acción
p_ah_h_plus10 = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if (h + 1.0) > a))
p_ah_h_minus10 = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h > (a + 1.0)))

# 7. 1RA MITAD RESULTADO (1X2)
p_1_ht, p_x_ht, p_2_ht = float(np.sum(np.tril(matriz_ht, -1))), float(np.sum(np.diag(matriz_ht))), float(np.sum(np.triu(matriz_ht, 1)))

# 8. OVER / UNDER GOLES 1RA MITAD (+0.5/-0.5, +1.5/-1.5)
p_over05_ht = 1.0 - (poisson.pmf(0, lam_h_ht) * poisson.pmf(0, lam_a_ht))
p_under05_ht = 1.0 - p_over05_ht
p_under15_ht = float(sum(matriz_ht[h, a] for h in range(8) for a in range(8) if h + a < 1.5))
p_over15_ht = 1.0 - p_under15_ht

# 9. TIROS DE ESQUINA 1RA MITAD
exp_corners_ht = exp_corners_ft * 0.45
p_over_corners_ht = float(1.0 - poisson.cdf(int(linea_corners_ht), exp_corners_ht))

# 10. EMPATE NO ACCIÓN (DRAW NO BET / AH 0)
p_dnb_h = p_ah_h_0

# 11. GANA CUALQUIER MITAD
p_win_any_h = 1.0 - ((1.0 - p_1_ht) * (1.0 - p_1_ft))

st.markdown("---")

# INGRESO DE MOMIOS DE LOS 11 MERCADOS
col_head, col_opt = st.columns([3, 2])
with col_head:
    st.markdown("<h3 style='color:#FFD700;'>⚡ METER MOMIOS PARA CADA MERCADO</h3>", unsafe_allow_html=True)
with col_opt:
    tipo_momio = st.radio("Formato de Momios:", ["Decimales", "Americanos"], horizontal=True)

def default_val(prob):
    return format_odds_display(1/prob if prob > 0 else 2.0, tipo_momio)

m1, m2, m3 = st.columns(3)
with m1: m_1_ft = st.text_input(f"1. Gana {home_team[:3]} (1X2)", value=default_val(p_1_ft))
with m2: m_1x = st.text_input(f"2. Doble Oportunidad ({home_team[:3]} o Empate 1X)", value=default_val(p_1x))
with m3: m_over_goles = st.text_input(f"3. Goles Over {linea_goles}", value=default_val(p_over_goles))

m4, m5, m6 = st.columns(3)
with m4: m_btts_yes = st.text_input("4. Ambos Anotan (BTTS SÍ)", value=default_val(p_btts_yes))
with m5: m_corners_ft = st.text_input(f"5. Córners Over {linea_corners_ft}", value=default_val(p_over_corners_ft))
with m6: m_ah_h_p05 = st.text_input(f"6. Hándicap Asiático {home_team[:3]} (+0.5)", value=default_val(p_ah_h_plus05))

m7, m8, m9 = st.columns(3)
with m7: m_ah_h_m05 = st.text_input(f"6. Hándicap Asiático {home_team[:3]} (-0.5)", value=default_val(p_ah_h_minus05))
with m8: m_ah_h_0 = st.text_input(f"6. Hándicap Asiático {home_team[:3]} (0)", value=default_val(p_ah_h_0))
with m9: m_ah_h_p10 = st.text_input(f"6. Hándicap Asiático {home_team[:3]} (+1.0)", value=default_val(p_ah_h_plus10))

m10, m11, m12 = st.columns(3)
with m10: m_1_ht = st.text_input(f"7. 1ra Mitad Gana {home_team[:3]}", value=default_val(p_1_ht))
with m11: m_ht_o05 = st.text_input("8. Goles 1ra Mitad Over 0.5", value=default_val(p_over05_ht))
with m12: m_ht_o15 = st.text_input("8. Goles 1ra Mitad Over 1.5", value=default_val(p_over15_ht))

m13, m14, m15 = st.columns(3)
with m13: m_corners_ht = st.text_input(f"9. Córners 1ra Mitad Over {linea_corners_ht}", value=default_val(p_over_corners_ht))
with m14: m_dnb = st.text_input(f"10. Empate No Acción {home_team[:3]}", value=default_val(p_dnb_h))
with m15: m_win_any = st.text_input(f"11. Gana Cualquier Mitad {home_team[:3]}", value=default_val(p_win_any_h))

st.markdown("<br>", unsafe_allow_html=True)

# BOTÓN DE RECÁLCULO
recalcular = st.button("⚡ RECALCULAR OPORTUNIDADES DE APUESTA", use_container_width=True)

# PROCESAR CÁLCULOS Y MOSTRAR RESULTADOS
st.markdown("---")
st.markdown("<h3 style='color:#00FF66;'>📊 ANÁLISIS MATRIX DE OPORTUNIDADES (11 MERCADOS)</h3>", unsafe_allow_html=True)

mercados_list = [
    {"tit": f"1. Resultado Final (1X2): Gana {home_team}", "sub": "Ganador 90 min", "prob": p_1_ft, "odd": m_1_ft},
    {"tit": f"2. Doble Oportunidad: {home_team} o Empate (1X)", "sub": "1X Doble Chance", "prob": p_1x, "odd": m_1x},
    {"tit": f"3. Total de Goles: Over {linea_goles}", "sub": f"Goles Over {linea_goles}", "prob": p_over_goles, "odd": m_over_goles},
    {"tit": "4. Ambos Equipos Anotan: SÍ", "sub": "BTTS YES", "prob": p_btts_yes, "odd": m_btts_yes},
    {"tit": f"5. Total de Córners: Over {linea_corners_ft}", "sub": f"Córners FT > {linea_corners_ft}", "prob": p_over_corners_ft, "odd": m_corners_ft},
    {"tit": f"6. Hándicap Asiático: {home_team} (+0.5)", "sub": "AH +0.5", "prob": p_ah_h_plus05, "odd": m_ah_h_p05},
    {"tit": f"6. Hándicap Asiático: {home_team} (-0.5)", "sub": "AH -0.5", "prob": p_ah_h_minus05, "odd": m_ah_h_m05},
    {"tit": f"6. Hándicap Asiático: {home_team} (0)", "sub": "AH 0 (Draw No Bet)", "prob": p_ah_h_0, "odd": m_ah_h_0},
    {"tit": f"6. Hándicap Asiático: {home_team} (+1.0)", "sub": "AH +1.0", "prob": p_ah_h_plus10, "odd": m_ah_h_p10},
    {"tit": f"7. 1ra Mitad Resultado: Gana {home_team}", "sub": "1st Half 1X2", "prob": p_1_ht, "odd": m_1_ht},
    {"tit": "8. Over/Under Goles 1ra Mitad: Over 0.5", "sub": "1st Half Goals > 0.5", "prob": p_over05_ht, "odd": m_ht_o05},
    {"tit": "8. Over/Under Goles 1ra Mitad: Over 1.5", "sub": "1st Half Goals > 1.5", "prob": p_over15_ht, "odd": m_ht_o15},
    {"tit": f"9. Córners 1ra Mitad: Over {linea_corners_ht}", "sub": f"1st Half Corners > {linea_corners_ht}", "prob": p_over_corners_ht, "odd": m_corners_ht},
    {"tit": f"10. Empate No Acción: {home_team}", "sub": "Draw No Bet (DNB)", "prob": p_dnb_h, "odd": m_dnb},
    {"tit": f"11. Gana Cualquier Mitad: {home_team}", "sub": "Win Either Half", "prob": p_win_any_h, "odd": m_win_any}
]

for item in mercados_list:
    dec_odd = parse_odds_to_decimal(item['odd'], tipo_momio)
    ev = calcular_ev(item['prob'], dec_odd)
    lbl, card, badge = clasificar_opcion(item['prob'], ev)
    
    st.markdown(f"""
    <div class="cyber-card {card}">
        <div>
            <div class="cyber-card-title">{item['tit']}</div>
            <div class="cyber-card-sub">{item['sub']} | Probabilidad: <b style="color:#00FF66;">{item['prob']*100:.1f}%</b> | EV: <b style="color:#FFD700;">{ev*100:+.1f}%</b></div>
        </div>
        <div><span class="cyber-badge {badge}">{lbl}</span></div>
    </div>
    """, unsafe_allow_html=True)
