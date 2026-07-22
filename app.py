import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuración de página
st.set_page_config(page_title="Liga MX Predictor Pro", layout="centered", page_icon="⚽")

# DICCIONARIO DE LOGOS
LOGOS = {
    "Tigres": "https://a.espncdn.com/i/teamlogos/soccer/500/218.png",
    "San Luis": "https://a.espncdn.com/i/teamlogos/soccer/500/17702.png"
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

# --- BARRA LATERAL: AJUSTES FINOS DEL MODELO ---
st.sidebar.header("🧠 Variables Avanzadas del Partido")

st.sidebar.subheader("📉 Bajas / Lesiones / Rotaciones")
bajas_local = st.sidebar.slider("Impacto Bajas Local (%)", 0, 30, 0) / 100.0
bajas_visita = st.sidebar.slider("Impacto Bajas Visitante (%)", 0, 30, 10) / 100.0

st.sidebar.subheader("🏔️ Altitud y Fatiga")
diff_altitud = st.sidebar.number_input("Diferencial Altitud (m)", value=1800) # San Luis sube/baja
coef_altitud = 0.0001
fatiga_visita = st.sidebar.slider("Fatiga/Rotación Visitante (%)", 0, 20, 5) / 100.0

st.sidebar.subheader("🚩 Córners y 🟨 Tarjetas")
prom_corners_local = st.sidebar.number_input("Promedio Córners Local", value=5.8)
prom_corners_visita = st.sidebar.number_input("Promedio Córners Visitante", value=4.1)
tendencia_arbitro = st.sidebar.slider("Rigurosidad Árbitro (Tarjetas)", 2.0, 7.0, 4.5, step=0.5)

# --- CÁLCULO DE GOLES ESPERADOS (xG) DINÁMICO ---
xg_local_base = 1.95 * (1 - bajas_local)
penalizacion_altitud = diff_altitud * coef_altitud
xg_visita_base = 1.10 * (1 - bajas_visita) * (1 - penalizacion_altitud - fatiga_visita)
xg_visita_base = max(0.2, xg_visita_base)

# --- MATRIZ DE PROBABILIDAD (DIXON-COLES) ---
max_goles = 6
matrix = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix[x, y] = poisson.pmf(x, xg_local_base) * poisson.pmf(y, xg_visita_base)
matrix /= np.sum(matrix)

# --- ENCABEZADO Y VISTA ---
st.caption("9:00 P.M. · ESTADIO UNIVERSITARIO")

c_logo1, c_info1 = st.columns([1, 6])
with c_logo1: st.image(LOGOS["Tigres"], width=42)
with c_info1:
    st.markdown("<span class='team-name'>Tigres</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-g'>G</span>", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_local_base:.2f}")

c_logo2, c_info2 = st.columns([1, 6])
with c_logo2: st.image(LOGOS["San Luis"], width=42)
with c_info2:
    st.markdown("<span class='team-name'>San Luis</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-e'>E</span>", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_visita_base:.2f} (Afectado por Altitud/Bajas)")

st.markdown("---")

# --- MÓDULO DE MOMIOS ---
with st.expander("⚙️ METER LOS MOMIOS DE MI CASA DE APUESTAS", expanded=True):
    formato_momios = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_momios
    tipo_str = "Decimal" if es_dec else "Americano"
    
    c1, c2, c3 = st.columns(3)
    m_1 = to_decimal(c1.number_input("GANA LOCAL (1)", value=1.41 if es_dec else -245), tipo_str)
    m_x = to_decimal(c2.number_input("EMPATE (X)", value=4.65 if es_dec else 365), tipo_str)
    m_2 = to_decimal(c3.number_input("GANA VISITA (2)", value=7.50 if es_dec else 650), tipo_str)
    
    c4, c5, c6 = st.columns(3)
    m_over25 = to_decimal(c5.number_input("OVER 2.5 GOLES", value=1.61 if es_dec else -163), tipo_str)
    m_under25 = to_decimal(c6.number_input("UNDER 2.5 GOLES", value=2.25 if es_dec else 125), tipo_str)
    
    c7, c8, _ = st.columns(3)
    m_btts_s = to_decimal(c7.number_input("BTTS SÍ", value=1.77 if es_dec else -130), tipo_str)
    m_btts_n = to_decimal(c8.number_input("BTTS NO", value=1.93 if es_dec else -108), tipo_str)

# ==========================================
# CÁLCULO MATEMÁTICO DE LOS 7 MERCADOS
# ==========================================

# 1. RESULTADO FINAL (1X2)
prob_1 = np.sum(np.tril(matrix, -1))
prob_x = np.sum(np.diag(matrix))
prob_2 = np.sum(np.triu(matrix, 1))

# 2. DOBLE OPORTUNIDAD
prob_1x = prob_1 + prob_x
prob_x2 = prob_x + prob_2
prob_12 = prob_1 + prob_2

# 3. TOTAL DE GOLES (OVER/UNDER 2.5)
prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
prob_under25 = 1.0 - prob_over25

# 4. AMBOS EQUIPOS ANOTAN (BTTS)
prob_btts_si = np.sum(matrix[1:, 1:])
prob_btts_no = 1.0 - prob_btts_si

# 5. HÁNDICAP ASIÁTICO (-1.0 LOCAL)
prob_ha_local_cubre = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

# 6. OVER/UNDER CÓRNERS (LÍNEA 8.5)
lambda_corners = prom_corners_local + prom_corners_visita
prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)

# 7. OVER/UNDER TARJETAS (LÍNEA 4.5)
lambda_tarjetas = tendencia_arbitro
prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, lambda_tarjetas)

# EV (VALOR ESPERADO)
ev_1 = (prob_1 * m_1) - 1
ev_1x = (prob_1x * 1.15) - 1  # Estimado momio 1X
ev_over25 = (prob_over25 * m_over25) - 1
ev_btts_si = (prob_btts_si * m_btts_s) - 1

# --- DESPLIEGUE VISUAL DE LOS 7 MERCADOS ---
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

# 1. 1X2
st.markdown("<div class='market-header'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
render_card("Gana Local (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")

# 2. Doble Oportunidad
st.markdown("<div class='market-header'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
render_card("Local o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")

# 3. Goles
st.markdown("<div class='market-header'>3. Total de Goles (Over/Under)</div>", unsafe_allow_html=True)
render_card("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local_base+xg_visita_base:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

# 4. BTTS
st.markdown("<div class='market-header'>4. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
render_card("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

# 5. Hándicap Asiático
st.markdown("<div class='market-header'>5. Hándicap Asiático</div>", unsafe_allow_html=True)
render_card("Local Hándicap -1.0", f"Prob. de ganar por 2 o más goles: {prob_ha_local_cubre*100:.1f}%", (prob_ha_local_cubre*1.85)-1, "BET" if (prob_ha_local_cubre*1.85)-1 > 0.03 else "SKIP")

# 6. Córners
st.markdown("<div class='market-header'>6. Córners</div>", unsafe_allow_html=True)
render_card("Más de 8.5 Córners", f"Prob. Real: {prob_over_corners_85*100:.1f}% (Línea esperada: {lambda_corners:.1f})", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")

# 7. Tarjetas
st.markdown("<div class='market-header'>7. Tarjetas (Árbitro)</div>", unsafe_allow_html=True)
render_card("Más de 4.5 Tarjetas", f"Prob. Real: {prob_over_tarjetas_45*100:.1f}% (Prom. Árbitro: {lambda_tarjetas:.1f})", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
