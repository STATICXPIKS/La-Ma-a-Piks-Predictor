import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import json

# Configuración de la página
st.set_page_config(
    page_title="Premier League - Predictor Avanzado & Trap Line Detector",
    layout="wide",
    page_icon="⚽"
)

# Estilos CSS personalizados para replicar la interfaz de la imagen
st.markdown("""
<style>
    .main-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .pl-logo {
        width: 60px;
    }
    .team-badge {
        width: 35px;
        height: 35px;
        object-fit: contain;
        vertical-align: middle;
        margin-right: 8px;
    }
    .bet-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .bet-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #1a1a1a;
        margin-bottom: 4px;
    }
    .bet-subtitle {
        font-size: 0.85rem;
        color: #6c757d;
        font-family: monospace;
    }
    .badge-bet {
        background-color: #e6f4ea;
        color: #137333;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        border: 1px solid #ceead6;
    }
    .badge-skip {
        background-color: #fce8e6;
        color: #c5221f;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        border: 1px solid #fad2cf;
    }
    .badge-maybe {
        background-color: #e8f0fe;
        color: #1a73e8;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        border: 1px solid #d2e3fc;
    }
    .badge-trap {
        background-color: #fef7e0;
        color: #b06000;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        border: 1px solid #feefc3;
    }
</style>
""", unsafe_allow_html=True)

# Diccionario de Logos y Datos Base de la Premier League
TEAMS_DATA = {
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

PL_LOGO = "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg"

# ==============================================================================
# FUNCIONES DE CONVERSIÓN DE MOMIOS / APUESTAS
# ==============================================================================
def american_to_decimal(american):
    try:
        american = float(american)
        if american > 0:
            return (american / 100.0) + 1.0
        else:
            return (100.0 / abs(american)) + 1.0
    except:
        return 2.00

def decimal_to_american(decimal_odds):
    if decimal_odds <= 1.0:
        return "+100"
    if decimal_odds >= 2.0:
        amt = int(round((decimal_odds - 1.0) * 100))
        return f"+{amt}"
    else:
        amt = int(round(100.0 / (decimal_odds - 1.0)))
        return f"-{amt}"

def calcular_ev(prob_modelo, cuota_decimal):
    # EV = (Prob * Cuota) - 1
    return (prob_modelo * cuota_decimal) - 1.0

# ==============================================================================
# MOTOR ESTADÍSTICO DE PARTIDOS
# ==============================================================================
def calcular_lambdas(h_team, a_team, fatiga_h, rot_h, fatiga_a, rot_a, arb, clima):
    dh = TEAMS_DATA[h_team]
    da = TEAMS_DATA[a_team]
    
    avg_home_goals, avg_away_goals = 1.55, 1.25
    
    att_h, def_h = dh["xg"] / avg_home_goals, dh["xga"] / avg_away_goals
    att_a, def_a = da["xg"] / avg_away_goals, da["xga"] / avg_home_goals
    
    tactical_h = (12.0 / max(dh["ppda"], 5.0)) * (dh["aereos"] / 50.0)
    tactical_a = (12.0 / max(da["ppda"], 5.0)) * (da["aereos"] / 50.0)
    
    fatigue_h = 1.0 - (fatiga_h * 0.12 + rot_h * 0.10)
    fatigue_a = 1.0 - (fatiga_a * 0.12 + rot_a * 0.10)
    
    lambda_h = avg_home_goals * att_h * def_a * tactical_h * fatigue_h * arb * clima
    lambda_a = avg_away_goals * att_a * def_h * tactical_a * fatigue_a * (2.0 - arb) * clima
    
    return max(lambda_h, 0.2), max(lambda_a, 0.15)

def generar_matriz(lambda_h, lambda_a, max_goles=7):
    mat = np.zeros((max_goles, max_goles))
    for h in range(max_goles):
        for a in range(max_goles):
            mat[h, a] = poisson.pmf(h, lambda_h) * poisson.pmf(a, lambda_a)
    return mat / np.sum(mat)

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================
col_title, col_img = st.columns([4, 1])
with col_title:
    st.title("⚽ Premier League Predictor & Trap Line Detector")
    st.caption("Calculador con Métricas Avanzadas (xG, PPDA, Fatiga UEFA, Árbitros) y Detector de Trampas de Casas de Apuestas")
with col_img:
    st.image(PL_LOGO, width=90)

st.markdown("---")

# SELECCIÓN DE EQUIPOS Y AJUSTES
col_team1, col_team2 = st.columns(2)

with col_team1:
    st.subheader("🏠 Local")
    home_team = st.selectbox("Selecciona Equipo Local", list(TEAMS_DATA.keys()), index=0)
    st.image(TEAMS_DATA[home_team]["logo"], width=50)
    
    c1, c2 = st.columns(2)
    with c1:
        fatiga_h = st.slider("Fatiga UEFA Local (%)", 0, 100, 10) / 100.0
    with c2:
        rot_h = st.slider("Rotación Local (%)", 0, 100, 10) / 100.0

with col_team2:
    st.subheader("✈️ Visitante")
    away_team = st.selectbox("Selecciona Equipo Visitante", list(TEAMS_DATA.keys()), index=9)
    st.image(TEAMS_DATA[away_team]["logo"], width=50)
    
    c3, c4 = st.columns(2)
    with c3:
        fatiga_a = st.slider("Fatiga UEFA Visitante (%)", 0, 100, 60) / 100.0
    with c4:
        rot_a = st.slider("Rotación Visitante (%)", 0, 100, 50) / 100.0

with st.expander("⚙️ Factor Árbitro y Clima (Opcional)"):
    ca, cc = st.columns(2)
    with ca:
        arbitro = st.slider("Factor Árbitro (1.0 = Neutral)", 0.85, 1.15, 1.00, step=0.01)
    with cc:
        clima = st.slider("Factor Clima (1.0 = Normal, <1.0 = Lluvia/Viento)", 0.80, 1.00, 0.95, step=0.01)

# CÁLCULOS DEL MODELO
lam_h, lam_a = calcular_lambdas(home_team, away_team, fatiga_h, rot_h, fatiga_a, rot_a, arbitro, clima)
matriz = generar_matriz(lam_h, lam_a)

# PROBABILIDADES DEL MODELO
p_home = float(np.sum(np.tril(matriz, -1)))
p_draw = float(np.sum(np.diag(matriz)))
p_away = float(np.sum(np.triu(matriz, 1)))

p_dc_1x = p_home + p_draw
p_dc_x2 = p_away + p_draw
p_dc_12 = p_home + p_away

# Más / Menos 2.5
p_under25 = float(sum(matriz[h, a] for h in range(7) for a in range(7) if h + a < 2.5))
p_over25 = 1.0 - p_under25

# Ambos Anotan (BTTS)
p_btts_yes = float(sum(matriz[h, a] for h in range(1, 7) for a in range(1, 7)))
p_btts_no = 1.0 - p_btts_yes

st.markdown("---")

# ENCABEZADO DE EQUIPOS EN RESULTADOS
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
    <img src="{TEAMS_DATA[home_team]['logo']}" class="team-badge"> 
    <span style="font-size: 1.5rem; font-weight: bold;">{home_team}</span>
    <span style="font-size: 1.2rem; color: #888;">vs</span>
    <img src="{TEAMS_DATA[away_team]['logo']}" class="team-badge"> 
    <span style="font-size: 1.5rem; font-weight: bold;">{away_team}</span>
</div>
""", unsafe_allow_html=True)

# FORMULARIO DE MOMIOS DE LA CASA DE APUESTAS
st.markdown("### ⚙️ METER LOS MOMIOS DE MI CASA (OPCIONAL — ANÁLISIS MÁS PRECISO)")
st.info("Escribe los momios **americanos** de tu casa de apuestas (ej. -150 o +240). El modelo recalculaciones del EV y los veredictos contra tus números.")

f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    m_home = st.text_input(f"GANA {home_team.upper()}", value=decimal_to_american(1/p_home if p_home>0 else 2.0))
with f_col2:
    m_draw = st.text_input("EMPATE", value=decimal_to_american(1/p_draw if p_draw>0 else 3.0))
with f_col3:
    m_away = st.text_input(f"GANA {away_team.upper()}", value=decimal_to_american(1/p_away if p_away>0 else 4.0))

f_col4, f_col5, f_col6 = st.columns(3)
with f_col4:
    linea_goles = st.selectbox("LÍNEA DE GOLES", ["0/U 2.5", "0/U 1.5", "0/U 3.5"], index=0)
with f_col5:
    m_over = st.text_input("MÁS (OVER)", value=decimal_to_american(1/p_over25 if p_over25>0 else 1.9))
with f_col6:
    m_under = st.text_input("MENOS (UNDER)", value=decimal_to_american(1/p_under25 if p_under25>0 else 1.9))

f_col7, f_col8 = st.columns(2)
with f_col7:
    m_btts_yes = st.text_input("AMBOS ANOTAN: SÍ", value=decimal_to_american(1/p_btts_yes if p_btts_yes>0 else 1.9))
with f_col8:
    m_btts_no = st.text_input("AMBOS ANOTAN: NO", value=decimal_to_american(1/p_btts_no if p_btts_no>0 else 1.9))

# CONVERSIÓN A DECIMALES Y CÁLCULO DE EV / TRAMPAS
odd_h = american_to_decimal(m_home)
odd_d = american_to_decimal(m_draw)
odd_a = american_to_decimal(m_away)
odd_over = american_to_decimal(m_over)
odd_under = american_to_decimal(m_under)
odd_btts_yes = american_to_decimal(m_btts_yes)
odd_btts_no = american_to_decimal(m_btts_no)

ev_h = calcular_ev(p_home, odd_h)
ev_d = calcular_ev(p_draw, odd_d)
ev_a = calcular_ev(p_away, odd_a)
ev_under = calcular_ev(p_under25, odd_under)
ev_over = calcular_ev(p_over25, odd_over)
ev_btts_no = calcular_ev(p_btts_no, odd_btts_no)

# DETECTOR DE TRAMPAS (TRAP LINE DETECTOR)
fatiga_critica_a = (fatiga_a + rot_a) >= 0.8
fatiga_critica_h = (fatiga_h + rot_h) >= 0.8

trap_h = fatiga_critica_h and (odd_h > 2.0) and (ev_h > 0.10)
trap_a = fatiga_critica_a and (odd_a > 2.0) and (ev_a > 0.10)

def get_verdict(ev, is_trap=False):
    if is_trap:
        return "TRAP LINE", "badge-trap"
    if ev > 0.05:
        return "BET", "badge-bet"
    elif ev > -0.03:
        return "MAYBE", "badge-maybe"
    else:
        return "SKIP", "badge-skip"

v_h, class_h = get_verdict(ev_h, trap_h)
v_dc1x, class_dc1x = get_verdict(calcular_ev(p_dc_1x, 1.25)) # Estimación
v_under, class_under = get_verdict(ev_under)
v_btts_no, class_btts_no = get_verdict(ev_btts_no)

st.markdown("---")
st.markdown("### 📊 OPCIONES DE APUESTA ANALIZADAS")

# CARTA 1: GANA LOCAL
st.markdown(f"""
<div class="bet-card">
    <div>
        <div class="bet-title">Gana {home_team}</div>
        <div class="bet-subtitle">1X2 {home_team[:3].upper()} ({decimal_to_american(1/p_home)}) · {p_home*100:.1f}% · EV {ev_h*100:+.1f}%</div>
    </div>
    <div><span class="{class_h}">{v_h}</span></div>
</div>
""", unsafe_allow_html=True)

# CARTA 2: DOBLE OPORTUNIDAD 1X
st.markdown(f"""
<div class="bet-card">
    <div>
        <div class="bet-title">{home_team} o empate (1X)</div>
        <div class="bet-subtitle">DC 1X · modelo {decimal_to_american(1/p_dc_1x)} · {p_dc_1x*100:.1f}%</div>
    </div>
    <div><span class="{class_dc1x}">{v_dc1x}</span></div>
</div>
""", unsafe_allow_html=True)

# CARTA 3: MENOS DE 2.5 GOLES
st.markdown(f"""
<div class="bet-card">
    <div>
        <div class="bet-title">Menos de 2.5 goles</div>
        <div class="bet-subtitle">U 2.5 · modelo espera {(lam_h+lam_a):.1f} goles · {p_under25*100:.1f}% · EV {ev_under*100:+.1f}%</div>
    </div>
    <div><span class="{class_under}">{v_under}</span></div>
</div>
""", unsafe_allow_html=True)

# CARTA 4: AMBOS EQUIPOS ANOTAN: NO
st.markdown(f"""
<div class="bet-card">
    <div>
        <div class="bet-title">Ambos equipos anotan: NO</div>
        <div class="bet-subtitle">BTTS · modelo {decimal_to_american(1/p_btts_no)} · {p_btts_no*100:.1f}% · EV {ev_btts_no*100:+.1f}%</div>
    </div>
    <div><span class="{class_btts_no}">{v_btts_no}</span></div>
</div>
""", unsafe_allow_html=True)

# ALERTA DE TRAMPA DE LÍNEA SI APLICA
if trap_h or trap_a:
    equipo_trap = home_team if trap_h else away_team
    st.warning(f"⚠️ **TRAP LINE DETECTADA**: La casa ofrece una cuota tentadora para **{equipo_trap}**, pero el modelo detecta un riesgo oculto debido a la alta fatiga/rotación del equipo. Te sugerimos precauciones antes de apostar a esta opción.")

# MAPA DE MATRIZ DE MARCADORES EXACTOS
with st.expander("📈 Ver Matriz de Probabilidades de Marcadores Exactos"):
    fig = go.Figure(data=go.Heatmap(
        z=matriz[:5, :5] * 100,
        x=[f"{away_team} {i}" for i in range(5)],
        y=[f"{home_team} {i}" for i in range(5)],
        colorscale='Viridis',
        hovertemplate='Marcador: %{y} - %{x}<br>Probabilidad: %{z:.2f}%<extra></extra>'
    ))
    fig.update_layout(title="Marcadores Exactos (0-4 Goles)", xaxis_title=away_team, yaxis_title=home_team)
    st.plotly_chart(fig, use_container_width=True)
