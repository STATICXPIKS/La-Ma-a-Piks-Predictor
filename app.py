import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuración de página
st.set_page_config(page_title="Liga MX Predictor", layout="centered", page_icon="⚽")

# DICCIONARIO DE LOGOS OFICIALES Y HD DE WIKIMEDIA (NO HOTLINK BLOCKED)
LOGOS = {
    "Tigres": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/Tigres_UANL_logo.svg/1200px-Tigres_UANL_logo.svg.png",
    "San Luis": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Atletico_san_luis.png/800px-Atletico_san_luis.png"
}

# ESTILOS CSS
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .team-name { font-size: 22px; font-weight: 800; color: #111827; }
    .badge-bet { background-color: #d1fae5; color: #065f46; font-weight: bold; padding: 4px 12px; border-radius: 6px; border: 1px solid #10b981; float: right; }
    .badge-skip { background-color: #fee2e2; color: #991b1b; font-weight: bold; padding: 4px 12px; border-radius: 6px; border: 1px solid #f87171; float: right; }
    .form-pill { display: inline-block; width: 18px; height: 18px; border-radius: 4px; color: white; font-size: 10px; font-weight: bold; text-align: center; line-height: 18px; margin-right: 2px; }
    .bg-g { background-color: #10b981; } .bg-e { background-color: #f59e0b; } .bg-p { background-color: #ef4444; }
    .market-header { font-size: 16px; font-weight: bold; color: #1e3a8a; margin-top: 15px; border-bottom: 2px solid #dbeafe; padding-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal":
        return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- BARRA LATERAL: AJUSTES FINOS ---
st.sidebar.header("🧠 Variables Avanzadas del Partido")

bajas_local = st.sidebar.slider("Impacto Bajas Local (%)", 0, 30, 0) / 100.0
bajas_visita = st.sidebar.slider("Impacto Bajas Visitante (%)", 0, 30, 10) / 100.0
diff_altitud = st.sidebar.number_input("Diferencial Altitud (m)", value=1800)
fatiga_visita = st.sidebar.slider("Fatiga Visitante (%)", 0, 20, 5) / 100.0
prom_corners_local = st.sidebar.number_input("Promedio Córners Local", value=5.8)
prom_corners_visita = st.sidebar.number_input("Promedio Córners Visitante", value=4.1)
tendencia_arbitro = st.sidebar.slider("Rigurosidad Árbitro (Tarjetas)", 2.0, 7.0, 4.5, step=0.5)

# --- CÁLCULO DE GOLES ESPERADOS (xG) ---
xg_local_base = 1.95 * (1 - bajas_local)
penalizacion_altitud = diff_altitud * 0.0001
xg_visita_base = max(0.2, 1.10 * (1 - bajas_visita) * (1 - penalizacion_altitud - fatiga_visita))

# --- MATRIZ POISSON ---
max_goles = 6
matrix = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix[x, y] = poisson.pmf(x, xg_local_base) * poisson.pmf(y, xg_visita_base)
matrix /= np.sum(matrix)

# --- ENCABEZADO CON LOGOS CORREGIDOS ---
st.caption("9:00 P.M. · ESTADIO UNIVERSITARIO")

c_logo1, c_info1 = st.columns([1, 6])
with c_logo1: 
    st.image(LOGOS["Tigres"], width=42)
with c_info1:
    st.markdown("<span class='team-name'>Tigres</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-g'>G</span>", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_local_base:.2f}")

c_logo2, c_info2 = st.columns([1, 6])
with c_logo2: 
    st.image(LOGOS["San Luis"], width=42)
with c_info2:
    st.markdown("<span class='team-name'>San Luis</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-e'>E</span>", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_visita_base:.2f} (Afectado por Altitud/Bajas)")

st.markdown("---")

# --- MÓDULO DE MOMIOS (CUADRÍCULA COMPLETA DE 3 COLUMNAS) ---
with st.expander("⚙️ METER LOS MOMIOS DE MI CASA DE APUESTAS", expanded=True):
    formato_momios = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_momios
    tipo_str = "Decimal" if es_dec else "Americano"
    
    # Fila 1: 1X2
    c1, c2, c3 = st.columns(3)
    m_1_in = c1.number_input("GANA LOCAL (1)", value=1.41 if es_dec else -245)
    m_x_in = c2.number_input("EMPATE (X)", value=4.65 if es_dec else 365)
    m_2_in = c3.number_input("GANA VISITA (2)", value=7.50 if es_dec else 650)
    
    # Fila 2: Línea de Goles + Over + Under
    c4, c5, c6 = st.columns(3)
    linea_goles = c4.selectbox("LÍNEA DE GOLES", ["O/U 2.5", "O/U 1.5", "O/U 3.5"])
    m_over_in = c5.number_input("MÁS (OVER)", value=1.61 if es_dec else -163)
    m_under_in = c6.number_input("MENOS (UNDER)", value=2.25 if es_dec else 125)
    
    # Fila 3: Both Teams to Score (BTTS)
    c7, c8, c9 = st.columns(3)
    m_btts_s_in = c7.number_input("AMBOS ANOTAN: SÍ", value=1.77 if es_dec else -130)
    m_btts_n_in = c8.number_input("AMBOS ANOTAN: NO", value=1.93 if es_dec else -108)

    # Conversión
    m_1 = to_decimal(m_1_in, tipo_str)
    m_over25 = to_decimal(m_over_in, tipo_str)
    m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# --- CÁLCULOS 7 MERCADOS ---
prob_1 = np.sum(np.tril(matrix, -1))
prob_x = np.sum(np.diag(matrix))
prob_2 = np.sum(np.triu(matrix, 1))

prob_1x = prob_1 + prob_x
prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
prob_btts_si = np.sum(matrix[1:, 1:])
prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

lambda_corners = prom_corners_local + prom_corners_visita
prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)

lambda_tarjetas = tendencia_arbitro
prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, lambda_tarjetas)

ev_1 = (prob_1 * m_1) - 1
ev_1x = (prob_1x * 1.15) - 1
ev_over25 = (prob_over25 * m_over25) - 1
ev_btts_si = (prob_btts_si * m_btts_s) - 1

# --- DESPLIEGUE VISUAL ---
st.markdown("### 🎯 Análisis Matemático de los 7 Mercados")

def render_card(titulo, subtitulo, ev, badge):
    badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
    st.markdown(f"""
    <div style="background: white; padding: 14px; border-radius: 10px; border: 1px solid #e5e7eb; margin-bottom: 10px;">
        {badge_html}
        <h4 style="margin: 0; color: #111827; font-size:16px;">{titulo}</h4>
        <p style="margin: 3px 0 0 0; color: #6b7280; font-size: 13px;">{subtitulo} · EV {ev*100:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='market-header'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
render_card("Gana Local (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
render_card("Local o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")

st.markdown("<div class='market-header'>3. Total de Goles (Over/Under)</div>", unsafe_allow_html=True)
render_card("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local_base+xg_visita_base:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>4. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
render_card("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

st.markdown("<div class='market-header'>5. Hándicap Asiático</div>", unsafe_allow_html=True)
render_card("Local Hándicap -1.0", f"Prob. de ganar por 2 o más goles: {prob_ha_local*100:.1f}%", (prob_ha_local*1.85)-1, "BET" if (prob_ha_local*1.85)-1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>6. Córners</div>", unsafe_allow_html=True)
render_card("Más de 8.5 Córners", f"Prob. Real: {prob_over_corners_85*100:.1f}% (Línea esperada: {lambda_corners:.1f})", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>7. Tarjetas (Árbitro)</div>", unsafe_allow_html=True)
render_card("Más de 4.5 Tarjetas", f"Prob. Real: {prob_over_tarjetas_45*100:.1f}% (Prom. Árbitro: {lambda_tarjetas:.1f})", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
