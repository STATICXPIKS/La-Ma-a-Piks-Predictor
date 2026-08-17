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
        <h1 class="cyber-title">BET365 PREMIER LEAGUE // DYNAMIC MARKETS PREDICTOR</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# SELECCIÓN DE EQUIPOS
col_t1, col_t2 = st.columns(2)
with col_t1:
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=1)
    fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 15) / 100.0
    rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_t2:
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=5)
    fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

# CÁLCULOS BASE
lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a)
matriz_ft = generar_matriz(lam_h, lam_a)

lam_h_ht, lam_a_ht = lam_h * 0.45, lam_a * 0.45
matriz_ht = generar_matriz(lam_h_ht, lam_a_ht)

# PROBABILIDADES BASE 1X2 Y DNB
p_1_ft, p_x_ft, p_2_ft = float(np.sum(np.tril(matriz_ft, -1))), float(np.sum(np.diag(matriz_ft))), float(np.sum(np.triu(matriz_ft, 1)))
p_1_ht, p_x_ht, p_2_ht = float(np.sum(np.tril(matriz_ht, -1))), float(np.sum(np.diag(matriz_ht))), float(np.sum(np.triu(matriz_ht, 1)))

st.markdown("---")

# FORMATO DE MOMIOS Y CONFIGURACIÓN
col_head, col_opt = st.columns([3, 2])
with col_head:
    st.markdown("<h3 style='color:#FFD700;'>⚡ METER MOMIOS Y AJUSTES DINÁMICOS POR MERCADO</h3>", unsafe_allow_html=True)
with col_opt:
    tipo_momio = st.radio("Formato de Momios:", ["Decimales", "Americanos"], horizontal=True)

def default_val(prob):
    return format_odds_display(1/prob if prob > 0 else 2.0, tipo_momio)

# ------------------------------------------------------------------------------
# CONTROLES Y CAMPOS INTEGRADOS POR MERCADO
# ------------------------------------------------------------------------------

# MERCADOS 1 Y 2: 1X2 Y DOBLE OPORTUNIDAD
st.markdown("#### ⚽ 1. RESULTADO FINAL (1X2) & 2. DOBLE OPORTUNIDAD")
c1, c2, c3, c4 = st.columns(4)
with c1: m_1_ft = st.text_input(f"1X2: Gana {home_team[:3]}", value=default_val(p_1_ft))
with c2: m_1x = st.text_input("Doble Chance: 1X", value=default_val(p_1_ft + p_x_ft))
with c3: m_x2 = st.text_input("Doble Chance: X2", value=default_val(p_2_ft + p_x_ft))
with c4: m_12 = st.text_input("Doble Chance: 12", value=default_val(p_1_ft + p_2_ft))

# MERCADO 3: TOTAL DE GOLES (FT) CON AJUSTE DINÁMICO
st.markdown("#### 🥅 3. TOTAL DE GOLES (FT)")
cg1, cg2, cg3 = st.columns([2, 1, 1])
with cg1:
    linea_goles_ft = st.slider("3. Línea Total de Goles (FT)", 1.5, 4.5, 2.5, step=1.0)
    p_under_goles = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h + a < linea_goles_ft))
    p_over_goles = 1.0 - p_under_goles
with cg2:
    m_over_goles = st.text_input(f"Goles Over {linea_goles_ft}", value=default_val(p_over_goles))
with cg3:
    m_under_goles = st.text_input(f"Goles Under {linea_goles_ft}", value=default_val(p_under_goles))

# MERCADO 4 Y 5: BTTS Y TOTAL DE CÓRNERS (FT) CON AJUSTE DINÁMICO
st.markdown("#### 🚩 4. AMBOS ANOTAN & 5. TOTAL DE CÓRNERS (FT)")
p_btts_yes = float(sum(matriz_ft[h, a] for h in range(1, 8) for a in range(1, 8)))
exp_corners_ft = TEAMS_DATA[home_team]["corners"] + TEAMS_DATA[away_team]["corners"]

cm1, cm2, cm3, cm4 = st.columns([1, 1, 2, 1])
with cm1: m_btts_yes = st.text_input("4. BTTS SÍ", value=default_val(p_btts_yes))
with cm2: m_btts_no = st.text_input("4. BTTS NO", value=default_val(1.0 - p_btts_yes))
with cm3:
    linea_corners_ft = st.slider("5. Línea Total de Córners (FT)", 8.5, 12.5, 9.5, step=1.0)
    p_over_corners_ft = float(1.0 - poisson.cdf(int(linea_corners_ft), exp_corners_ft))
with cm4:
    m_corners_ft = st.text_input(f"Córners Over {linea_corners_ft}", value=default_val(p_over_corners_ft))

# MERCADO 6: HÁNDICAP ASIÁTICO CON SELECTOR DINÁMICO DE LÍNEA
st.markdown("#### ⚖️ 6. HÁNDICAP ASIÁTICO")
ha_col1, ha_col2 = st.columns([2, 2])
with ha_col1:
    linea_ha = st.selectbox("6. Seleccionar Línea de Hándicap Asiático", ["+0.5", "-0.5", "0 (DNB)", "+1.0", "-1.0"], index=0)

# CÁLCULO DE PROBABILIDAD DE HÁNDICAP ELEGIDO
if linea_ha == "+0.5":
    p_ha_selected = p_1_ft + p_x_ft
elif linea_ha == "-0.5":
    p_ha_selected = p_1_ft
elif linea_ha == "0 (DNB)":
    p_ha_selected = p_1_ft / (p_1_ft + p_2_ft) if (p_1_ft + p_2_ft) > 0 else 0.5
elif linea_ha == "+1.0":
    p_ha_selected = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if (h + 1.0) > a))
else: # -1.0
    p_ha_selected = float(sum(matriz_ft[h, a] for h in range(8) for a in range(8) if h > (a + 1.0)))

with ha_col2:
    m_ha_selected = st.text_input(f"Momio AH {home_team[:3]} ({linea_ha})", value=default_val(p_ha_selected))

# MERCADOS 7 Y 8: 1RA MITAD 1X2 Y GOLES 1RA MITAD CON SELECCIÓN DE LÍNEA
st.markdown("#### ⏱️ 7. 1RA MITAD RESULTADO & 8. OVER/UNDER GOLES 1RA MITAD")
h1, h2, h3, h4 = st.columns([1, 1, 1, 1])
with h1: m_1_ht = st.text_input(f"7. 1ra Mitad Gana {home_team[:3]}", value=default_val(p_1_ht))
with h2:
    linea_goles_ht = st.selectbox("8. Línea Goles HT", ["+0.5", "+1.5"], index=0)
    p_goles_ht_sel = (1.0 - (poisson.pmf(0, lam_h_ht) * poisson.pmf(0, lam_a_ht))) if linea_goles_ht == "+0.5" else (1.0 - float(sum(matriz_ht[h, a] for h in range(8) for a in range(8) if h + a < 1.5)))
with h3: m_goles_ht = st.text_input(f"Momio Goles HT ({linea_goles_ht})", value=default_val(p_goles_ht_sel))

# MERCADOS 9, 10 Y 11: CÓRNERS HT CON SLIDER, DNB Y GANA CUALQUIER MITAD
st.markdown("#### 🚩 9. CÓRNERS HT | 10. EMPATE NO ACCIÓN | 11. GANA CUALQUIER MITAD")
m_c1, m_c2, m_c3, m_c4 = st.columns([2, 1, 1, 1])
with m_c1:
    linea_corners_ht = st.slider("9. Córners 1ra Mitad (HT)", 3.0, 6.0, 4.5, step=0.5)
    exp_corners_ht = exp_corners_ft * 0.45
    p_over_corners_ht = float(1.0 - poisson.cdf(int(linea_corners_ht), exp_corners_ht))
with m_c2: m_corners_ht = st.text_input(f"Córners HT > {linea_corners_ht}", value=default_val(p_over_corners_ht))

p_dnb_h = p_1_ft / (p_1_ft + p_2_ft) if (p_1_ft + p_2_ft) > 0 else 0.5
p_win_any_h = 1.0 - ((1.0 - p_1_ht) * (1.0 - p_1_ft))

with m_c3: m_dnb = st.text_input("10. Empate No Acción (DNB)", value=default_val(p_dnb_h))
with m_c4: m_win_any = st.text_input("11. Gana Cualq. Mitad", value=default_val(p_win_any_h))

st.markdown("<br>", unsafe_allow_html=True)

# BOTÓN DE RECÁLCULO
recalcular = st.button("⚡ RECALCULAR OPORTUNIDADES DE APUESTA", use_container_width=True)

# PROCESAR CÁLCULOS Y MOSTRAR RESULTADOS
st.markdown("---")
st.markdown("<h3 style='color:#00FF66;'>📊 ANÁLISIS MATRIX DE OPORTUNIDADES (11 MERCADOS)</h3>", unsafe_allow_html=True)

mercados_list = [
    {"tit": f"1. Resultado Final (1X2): Gana {home_team}", "sub": "Ganador 90 min", "prob": p_1_ft, "odd": m_1_ft},
    {"tit": f"2. Doble Oportunidad: {home_team} o Empate (1X)", "sub": "1X Doble Chance", "prob": p_1_ft + p_x_ft, "odd": m_1x},
    {"tit": f"3. Total de Goles (FT): Over {linea_goles_ft}", "sub": f"Goles Over {linea_goles_ft}", "prob": p_over_goles, "odd": m_over_goles},
    {"tit": "4. Ambos Equipos Anotan: SÍ", "sub": "BTTS YES", "prob": p_btts_yes, "odd": m_btts_yes},
    {"tit": f"5. Total de Córners (FT): Over {linea_corners_ft}", "sub": f"Córners FT > {linea_corners_ft}", "prob": p_over_corners_ft, "odd": m_corners_ft},
    {"tit": f"6. Hándicap Asiático: {home_team} ({linea_ha})", "sub": f"Línea elegida: {linea_ha}", "prob": p_ha_selected, "odd": m_ha_selected},
    {"tit": f"7. 1ra Mitad Resultado: Gana {home_team}", "sub": "1st Half 1X2", "prob": p_1_ht, "odd": m_1_ht},
    {"tit": f"8. Goles 1ra Mitad: Over {linea_goles_ht}", "sub": f"1st Half Goals Over {linea_goles_ht}", "prob": p_goles_ht_sel, "odd": m_goles_ht},
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
