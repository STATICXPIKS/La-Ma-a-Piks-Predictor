import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuración de página
st.set_page_config(page_title="Liga MX Predictor", layout="centered", page_icon="⚽")

# DICCIONARIO DE LOGOS CON ENLACES DIRECTOS
LOGOS = {
    "Tigres": "https://a.espncdn.com/i/teamlogos/soccer/500/218.png",
    "San Luis": "https://a.espncdn.com/i/teamlogos/soccer/500/17702.png",
    "América": "https://a.espncdn.com/i/teamlogos/soccer/500/227.png",
    "Chivas": "https://a.espncdn.com/i/teamlogos/soccer/500/219.png",
    "Cruz Azul": "https://a.espncdn.com/i/teamlogos/soccer/500/217.png",
    "Pumas": "https://a.espncdn.com/i/teamlogos/soccer/500/229.png",
    "Toluca": "https://a.espncdn.com/i/teamlogos/soccer/500/232.png",
    "Monterrey": "https://a.espncdn.com/i/teamlogos/soccer/500/223.png"
}

# ESTILOS CSS PERSONALIZADOS
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    
    .team-name {
        font-size: 22px;
        font-weight: 800;
        margin-right: 10px;
        color: #111827;
    }
    
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
</style>
""", unsafe_allow_html=True)

# FUNCIONES DE CONVERSIÓN DE MOMIOS
def to_decimal(momio, tipo):
    if tipo == "Decimal":
        return float(momio)
    else: # Americano
        return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# ENCABEZADO
st.caption("9:00 P.M. · ESTADIO UNIVERSITARIO")

# RENDER DE EQUIPOS Y ESCUDOS CON STREAMLIT
c_logo1, c_info1 = st.columns([1, 6])
with c_logo1:
    st.image(LOGOS["Tigres"], width=42)
with c_info1:
    st.markdown("<span class='team-name'>Tigres</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-g'>G</span>", unsafe_allow_html=True)
    st.caption("0-0-1 (G-E-P)")

c_logo2, c_info2 = st.columns([1, 6])
with c_logo2:
    st.image(LOGOS["San Luis"], width=42)
with c_info2:
    st.markdown("<span class='team-name'>San Luis</span> <span class='form-pill bg-p'>P</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-g'>G</span><span class='form-pill bg-p'>P</span><span class='form-pill bg-e'>E</span>", unsafe_allow_html=True)
    st.caption("0-0-1 (G-E-P)")

st.markdown("---")

# MÓDULO DE MOMIOS CON SWITCH DE FORMATO
with st.expander("⚙️ METER LOS MOMIOS DE MI CASA (OPCIONAL — ANÁLISIS MÁS PRECISO)", expanded=True):
    
    # SWITCH AMERICANO / DECIMAL
    formato_momios = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_decimal = "Decimal" in formato_momios
    
    st.caption("Ingresa los momios de tu casa. El modelo recalculará el EV y los veredictos en automático.")
    
    col_m1, col_mx, col_m2 = st.columns(3)
    val_l = 1.41 if es_decimal else -245
    val_x = 4.70 if es_decimal else 370
    val_v = 6.00 if es_decimal else 500
    
    m_local_in = col_m1.number_input("GANA TIGRES", value=val_l)
    m_empate_in = col_mx.number_input("EMPATE", value=val_x)
    m_visita_in = col_m2.number_input("GANA SAN LUIS", value=val_v)
    
    col_lg, col_over, col_under = st.columns(3)
    linea_goles = col_lg.selectbox("LÍNEA DE GOLES", ["O/U 2.5"])
    m_over_in = col_over.number_input("MÁS (OVER)", value=1.55 if es_decimal else -180)
    m_under_in = col_under.number_input("MENOS (UNDER)", value=2.20 if es_decimal else 120)
    
    col_btts_s, col_btts_n, _ = st.columns(3)
    m_btts_s_in = col_btts_s.number_input("AMBOS ANOTAN: SÍ", value=1.91 if es_decimal else -110)
    m_btts_n_in = col_btts_n.number_input("AMBOS ANOTAN: NO", value=1.91 if es_decimal else -110)

    # Conversión Unificada a Decimal
    tipo_str = "Decimal" if es_decimal else "Americano"
    m_local = to_decimal(m_local_in, tipo_str)
    m_over = to_decimal(m_over_in, tipo_str)
    m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# CÁLCULOS
xg_local, xg_visita = 2.10, 1.05
matrix = np.zeros((6, 6))
for x in range(6):
    for y in range(6):
        matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
matrix /= np.sum(matrix)

p_local = np.sum(np.tril(matrix, -1))
p_empate = np.sum(np.diag(matrix))
p_dc_1x = p_local + p_empate
p_over25 = np.sum([matrix[x, y] for x in range(6) for y in range(6) if x + y > 2.5])
p_btts_si = np.sum(matrix[1:, 1:])

# EV
ev_local = (p_local * m_local) - 1
ev_dc1x = (p_dc_1x * 1.17) - 1
ev_over25 = (p_over25 * m_over) - 1
ev_btts_si = (p_btts_si * m_btts_s) - 1

# RECOMENDACIONES
st.markdown("### Recomendaciones del Modelo")

def render_card(titulo, subtitulo, ev, badge):
    badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
    st.markdown(f"""
    <div style="background: white; padding: 16px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 12px;">
        {badge_html}
        <h4 style="margin: 0; color: #111827;">{titulo}</h4>
        <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">{subtitulo} · EV {ev*100:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

str_m_local = f"{m_local_in:.2f}" if es_decimal else f"{int(m_local_in)}"
render_card("Gana Tigres", f"1X2 UANL ({str_m_local}) · {p_local*100:.1f}%", ev_local, "SKIP" if ev_local < 0.02 else "BET")
render_card("Tigres o empate (1X)", f"DC 1X · modelo {p_dc_1x*100:.1f}%", ev_dc1x, "BET")
render_card("Más de 2.5 goles", f"O 2.5 · modelo espera {xg_local+xg_visita:.2f} · {p_over25*100:.1f}%", ev_over25, "SKIP" if ev_over25 < 0.02 else "BET")
render_card("Ambos equipos anotan: Sí", f"BTTS · modelo {p_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si >= -0.05 else "SKIP")
