import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuración de página limpia
st.set_page_config(page_title="Liga MX Predictor", layout="centered", page_icon="⚽")

# Estilos CSS para replicar el diseño exacto de la imagen
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    
    /* Tarjeta Principal */
    .match-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Insignias BET y SKIP */
    .badge-bet {
        background-color: #d1fae5;
        color: #065f46;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 8px;
        border: 1px solid #10b981;
        float: right;
    }
    .badge-skip {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: bold;
        padding: 6px 16px;
        border-radius: 8px;
        border: 1px solid #f87171;
        float: right;
    }
    
    /* Indicadores de Forma G-E-P */
    .form-pill {
        display: inline-block;
        width: 18px;
        height: 18px;
        border-radius: 4px;
        color: white;
        font-size: 10px;
        font-weight: bold;
        text-align: center;
        line-height: 18px;
        margin-right: 2px;
    }
    .bg-g { background-color: #10b981; }
    .bg-e { background-color: #f59e0b; }
    .bg-p { background-color: #ef4444; }
    
    /* Botón azul principal */
    div.stButton > button:first-child {
        background-color: #1d4ed8;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        height: 48px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Helper para convertir momio americano a decimal
def amer_to_dec(m):
    return (m / 100) + 1 if m > 0 else (100 / abs(m)) + 1

# --- ENCABEZADO DE PARTIDO ---
st.caption("9:00 P.M. · ESTADIO UNIVERSITARIO")

col_logo, col_info = st.columns([1, 4])
with col_info:
    st.markdown("### **Tigres** <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-g'>G</span>", unsafe_allow_html=True)
    st.caption("0-0-1 (G-E-P)")
    
    st.markdown("### **San Luis** <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-e'>E</span>", unsafe_allow_html=True)
    st.caption("0-0-1 (G-E-P)")

st.markdown("---")

# --- MÓDULO DE MOMIOS DESPLEGABLE / ENTRADAS ---
with st.expander("⚙️ METER LOS MOMIOS DE MI CASA (OPCIONAL — ANÁLISIS MÁS PRECISO)", expanded=True):
    st.caption("Escribe los momios **americanos** de tu casa de apuestas (ej. -150 o +240). El modelo recalcula el valor y los veredictos contra tus números.")
    
    col_m1, col_mx, col_m2 = st.columns(3)
    m_local = col_m1.number_input("GANA TIGRES", value=-245)
    m_empate = col_mx.number_input("EMPATE", value=370)
    m_visita = col_m2.number_input("GANA SAN LUIS", value=500)
    
    col_lg, col_over, col_under = st.columns(3)
    linea_goles = col_lg.selectbox("LÍNEA DE GOLES", ["O/U 2.5"])
    m_over = col_over.number_input("MÁS (OVER)", value=-180)
    m_under = col_under.number_input("MENOS (UNDER)", value=120)
    
    col_btts_s, col_btts_n, col_dummy = st.columns(3)
    m_btts_si = col_btts_s.number_input("AMBOS ANOTAN: SÍ", value=-110)
    m_btts_no = col_btts_n.number_input("AMBOS ANOTAN: NO", value=-110)

    btn_recalc = st.button("Recalcular con mis momios")

# --- CÁLCULOS MATEMÁTICOS DEL MODELO ---
# xG estimado ajustado por altitud y fortaleza base
xg_local, xg_visita = 2.10, 1.05  

matrix = np.zeros((6, 6))
for x in range(6):
    for y in range(6):
        matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
matrix = matrix / np.sum(matrix)

# Probabilidades
p_local = np.sum(np.tril(matrix, -1))
p_empate = np.sum(np.diag(matrix))
p_dc_1x = p_local + p_empate
p_over25 = np.sum([matrix[x, y] for x in range(6) for y in range(6) if x + y > 2.5])
p_btts_si = np.sum(matrix[1:, 1:])

# EV (Expected Value)
ev_local = (p_local * amer_to_dec(m_local)) - 1
ev_dc1x = (p_dc_1x * amer_to_dec(-590)) - 1
ev_over25 = (p_over25 * amer_to_dec(m_over)) - 1
ev_btts_si = (p_btts_si * amer_to_dec(m_btts_si)) - 1

# --- BLOQUES DE VEREDICTO DE APUESTAS (DISEÑO CLEAN) ---
st.markdown("### Recomendaciones del Modelo")

def render_option(titulo, subtitulo, ev, badge_type):
    badge_html = f"<span class='badge-bet'>BET</span>" if badge_type == "BET" else f"<span class='badge-skip'>SKIP</span>"
    st.markdown(f"""
    <div style="background: white; padding: 16px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 12px;">
        {badge_html}
        <h4 style="margin: 0; color: #111827;">{titulo}</h4>
        <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">{subtitulo} · EV {ev*100:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

# Renderizado de Tarjetas estilo Pick Comercial
render_option("Gana Tigres", f"1X2 UANL ({m_local}) · {p_local*100:.1f}%", ev_local, "SKIP" if ev_local < 0.02 else "BET")
render_option("Tigres o empate (1X)", f"DC 1X · modelo -590 · {p_dc_1x*100:.1f}%", ev_dc1x, "BET")
render_option("Más de 2.5 goles", f"O 2.5 · modelo espera {xg_local+xg_visita:.2f} · {p_over25*100:.1f}%", ev_over25, "SKIP" if ev_over25 < 0.02 else "BET")
render_option("Ambos equipos anotan: Sí", f"BTTS · modelo -126 · {p_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si >= -0.05 else "SKIP")
