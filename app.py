import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import os

# Configuración de página
st.set_page_config(page_title="ANALISIS PRO-LIGA MX", layout="wide", page_icon="⚽")

# ESCUDOS REALES Y OFICIALES DE CADA CLUB (ESPN CDN HIGH RES)
ESCUDOS_REALES = {
    "América": "https://a.espncdn.com/i/teamlogos/soccer/500/227.png",
    "Atlante": "https://a.espncdn.com/i/teamlogos/soccer/500/221.png",
    "Atlas": "https://a.espncdn.com/i/teamlogos/soccer/500/216.png",
    "Chivas": "https://a.espncdn.com/i/teamlogos/soccer/500/219.png",
    "Cruz Azul": "https://a.espncdn.com/i/teamlogos/soccer/500/217.png",
    "Juárez": "https://a.espncdn.com/i/teamlogos/soccer/500/17882.png",
    "León": "https://a.espncdn.com/i/teamlogos/soccer/500/225.png",
    "Monterrey": "https://a.espncdn.com/i/teamlogos/soccer/500/223.png",
    "Necaxa": "https://a.espncdn.com/i/teamlogos/soccer/500/224.png",
    "Pachuca": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
    "Puebla": "https://a.espncdn.com/i/teamlogos/soccer/500/226.png",
    "Pumas": "https://a.espncdn.com/i/teamlogos/soccer/500/229.png",
    "Querétaro": "https://a.espncdn.com/i/teamlogos/soccer/500/222.png",
    "San Luis": "https://a.espncdn.com/i/teamlogos/soccer/500/17702.png",
    "Santos": "https://a.espncdn.com/i/teamlogos/soccer/500/230.png",
    "Tigres": "https://a.espncdn.com/i/teamlogos/soccer/500/218.png",
    "Tijuana": "https://a.espncdn.com/i/teamlogos/soccer/500/220.png",
    "Toluca": "https://a.espncdn.com/i/teamlogos/soccer/500/232.png"
}

EQUIPOS = {
    "América": {"altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2},
    "Atlante": {"altitud": 2240, "att": 1.35, "def": 1.20, "corners": 5.0},
    "Atlas": {"altitud": 1560, "att": 1.25, "def": 1.30, "corners": 4.5},
    "Chivas": {"altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5},
    "Cruz Azul": {"altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0},
    "Juárez": {"altitud": 1130, "att": 1.25, "def": 1.40, "corners": 4.4},
    "León": {"altitud": 1815, "att": 1.45, "def": 1.25, "corners": 5.1},
    "Monterrey": {"altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1},
    "Necaxa": {"altitud": 1800, "att": 1.40, "def": 1.25, "corners": 4.7},
    "Pachuca": {"altitud": 2400, "att": 1.70, "def": 1.20, "corners": 5.4},
    "Puebla": {"altitud": 2230, "att": 1.15, "def": 1.50, "corners": 4.2},
    "Pumas": {"altitud": 2240, "att": 1.50, "def": 1.15, "corners": 5.2},
    "Querétaro": {"altitud": 1820, "att": 1.10, "def": 1.35, "corners": 4.0},
    "San Luis": {"altitud": 1850, "att": 1.20, "def": 1.40, "corners": 4.1},
    "Santos": {"altitud": 1120, "att": 1.35, "def": 1.45, "corners": 4.9},
    "Tigres": {"altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8},
    "Tijuana": {"altitud": 60, "att": 1.30, "def": 1.35, "corners": 4.8},
    "Toluca": {"altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9}
}

# ESTILOS CSS GENERALES
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0b0e14; color: #ffffff; }
    
    .card-pro {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    
    .badge-bet { background: #10b981; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    .badge-skip { background: #ef4444; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    
    .market-title { font-size: 14px; font-weight: 700; color: #38bdf8; margin-top: 12px; margin-bottom: 6px; }
    .subtext { color: #94a3b8; font-size: 12px; margin-top: 3px; }
    
    .team-badge-box {
        display: flex;
        align-items: center;
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- DASHBOARD A 2 COLUMNAS ---
col_izq, col_der = st.columns([1, 1], gap="large")

# ==========================================
# COLUMNA IZQUIERDA
# ==========================================
with col_izq:
    head_col1, head_col2 = st.columns([1, 6])
    with head_col1:
        if os.path.exists("liga_mx.png"):
            st.image("liga_mx.png", width=45)
        else:
            st.write("⚽")
    with head_col2:
        st.markdown("<h2 style='color:#fff; font-weight:900; margin:0;'>ANALISIS PRO-LIGA MX</h2>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c_sel1, c_sel2 = st.columns(2)
    lista_equipos = sorted(list(EQUIPOS.keys()))
    
    local_nombre = c_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Santos") if "Santos" in lista_equipos else 0)
    visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
    visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("Atlas") if "Atlas" in visita_opciones else 0)

    eq_local, eq_visita = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

    # MATEMÁTICAS DEL MODELO
    diff_altitud = max(0, eq_local["altitud"] - eq_visita["altitud"])
    penal_altitud = diff_altitud * 0.00015

    xg_local = (eq_local["att"] * eq_visita["def"]) * 1.15
    xg_visita = max(0.2, (eq_visita["att"] * eq_local["def"]) * (1 - penal_altitud))

    max_goles = 6
    matrix = np.zeros((max_goles, max_goles))
    for x in range(max_goles):
        for y in range(max_goles):
            matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
    matrix /= np.sum(matrix)

    # 1HT
    xg_local_1ht, xg_visita_1ht = xg_local * 0.45, xg_visita * 0.45
    matrix_1ht = np.zeros((max_goles, max_goles))
    for x in range(max_goles):
        for y in range(max_goles):
            matrix_1ht[x, y] = poisson.pmf(x, xg_local_1ht) * poisson.pmf(y, xg_visita_1ht)
    matrix_1ht /= np.sum(matrix_1ht)

    # TARJETAS DE EQUIPOS CON ESCUDOS REALES
    c_esc1, c_esc2 = st.columns(2)
    with c_esc1:
        c_i1, c_t1 = st.columns([1, 3])
        with c_i1: st.image(ESCUDOS_REALES[local_nombre], width=42)
        with c_t1:
            st.markdown(f"<div style='font-weight:800; color:#fff; font-size:16px;'>{local_nombre}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#10b981; font-weight:800; font-size:14px;'>{xg_local:.2f} <span style='font-size:10px; color:#64748b;'>xG Esperado</span></div>", unsafe_allow_html=True)

    with c_esc2:
        c_i2, c_t2 = st.columns([1, 3])
        with c_i2: st.image(ESCUDOS_REALES[visita_nombre], width=42)
        with c_t2:
            st.markdown(f"<div style='font-weight:800; color:#fff; font-size:16px;'>{visita_nombre}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#38bdf8; font-weight:800; font-size:14px;'>{xg_visita:.2f} <span style='font-size:10px; color:#64748b;'>xG Esperado</span></div>", unsafe_allow_html=True)

    # GRÁFICAS COMPACTAS
    cg1, cg2 = st.columns(2)
    minutos = [0, 20, 40, 60, 80]
    xg_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xg_local))
    xg_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xg_visita))

    fig_xg = go.Figure()
    fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_local, mode='lines', name=local_nombre, line=dict(color='#10b981', width=2.5)))
    fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_visita, mode='lines', name=visita_nombre, line=dict(color='#38bdf8', width=2.5)))
    fig_xg.update_layout(
        title=dict(text="xG Progresión por Minuto", font=dict(size=12, color="#ffffff")),
        height=200, paper_bgcolor='#121721', plot_bgcolor='#121721', font=dict(color='#ffffff', size=9),
        xaxis=dict(gridcolor='#1e2638'), yaxis=dict(gridcolor='#1e2638'), margin=dict(l=25, r=15, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    prob_1 = np.sum(np.tril(matrix, -1))
    prob_x = np.sum(np.diag(matrix))
    prob_2 = np.sum(np.triu(matrix, 1))

    fig_pie = go.Figure(data=[go.Pie(
        labels=[local_nombre, 'Empate', visita_nombre], values=[prob_1, prob_x, prob_2], hole=.55,
        marker=dict(colors=['#10b981', '#f59e0b', '#38bdf8'])
    )])
    fig_pie.update_layout(
        title=dict(text="Distribución 1X2", font=dict(size=12, color="#ffffff")),
        height=200, paper_bgcolor='#121721', font=dict(color='#ffffff', size=9),
        margin=dict(l=15, r=15, t=30, b=15), showlegend=False
    )

    with cg1: st.plotly_chart(fig_xg, use_container_width=True)
    with cg2: st.plotly_chart(fig_pie, use_container_width=True)

    # MOMIOS DE TU CASA
    with st.expander("⚙️ MOMIOS DE TU CASA DE APUESTAS (CALCULADORA EV)", expanded=True):
        formato_m = st.radio("Formato:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
        es_dec = "Decimal" in formato_m
        tipo_str = "Decimal" if es_dec else "Americano"
        
        f1_1, f1_2, f1_3 = st.columns(3)
        m_1_in = f1_1.number_input(f"GANA {local_nombre.upper()}", value=2.62 if es_dec else 162)
        m_x_in = f1_2.number_input("EMPATE", value=3.40 if es_dec else 240)
        m_2_in = f1_3.number_input(f"GANA {visita_nombre.upper()}", value=2.62 if es_dec else 162)
        
        f2_1, f2_2, f2_3 = st.columns(3)
        linea_goles = f2_1.selectbox("GOLES (90 Min)", ["O/U 2.5", "O/U 1.5"])
        m_over_in = f2_2.number_input("OVER 2.5", value=1.83 if es_dec else -120)
        m_under_in = f2_3.number_input("UNDER 2.5", value=1.95 if es_dec else -105)

        f3_1, f3_2, f3_3 = st.columns(3)
        linea_goles_1ht = f3_1.selectbox("GOLES (1HT)", ["1HT O/U 0.5"])
        m_over_1ht_in = f3_2.number_input("1HT OVER 0.5", value=1.40 if es_dec else -250)
        m_under_1ht_in = f3_3.number_input("1HT UNDER 0.5", value=2.75 if es_dec else 175)
        
        f4_1, f4_2, _ = st.columns(3)
        m_btts_s_in = f4_1.number_input("BTTS SÍ", value=1.61 if es_dec else -164)
        m_btts_n_in = f4_2.number_input("BTTS NO", value=2.15 if es_dec else 115)

        m_1 = to_decimal(m_1_in, tipo_str)
        m_over25 = to_decimal(m_over_in, tipo_str)
        m_over_1ht = to_decimal(m_over_1ht_in, tipo_str)
        m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# ==========================================
# COLUMNA DERECHA
# ==========================================
with col_der:
    head2_col1, head2_col2 = st.columns([1, 6])
    with head2_col1:
        if os.path.exists("logo_mana.png"):
            st.image("logo_mana.png", width=45)
        else:
            st.write("👑")
    with head2_col2:
        st.markdown("<h2 style='color:#fff; font-weight:900; margin:0;'>VEREDICTO MAÑA PIKS</h2>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # CÁLCULOS 7 MERCADOS
    prob_1x = prob_1 + prob_x
    prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
    prob_btts_si = np.sum(matrix[1:, 1:])
    prob_over05_1ht = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 0.5])
    prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

    lambda_corners = eq_local["corners"] + eq_visita["corners"]
    prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)
    prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, 4.5)

    ev_1 = (prob_1 * m_1) - 1
    ev_1x = (prob_1x * 1.35) - 1
    ev_over25 = (prob_over25 * m_over25) - 1
    ev_over05_1ht = (prob_over05_1ht * m_over_1ht) - 1
    ev_btts_si = (prob_btts_si * m_btts_s) - 1

    def render_card_pro(titulo, subtitulo, ev, badge):
        badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
        st.markdown(f"""
        <div class="card-pro">
            {badge_html}
            <div style="font-weight: 800; font-size: 15px; color: #ffffff;">{titulo}</div>
            <div class="subtext">{subtitulo} · <b>EV {ev*100:+.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div class='market-title'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
    render_card_pro(f"Gana {local_nombre} (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")

    st.markdown("<div class='market-title'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
    render_card_pro(f"{local_nombre} o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")

    st.markdown("<div class='market-title'>3. Total de Goles (Partido Completo)</div>", unsafe_allow_html=True)
    render_card_pro("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local+xg_visita:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

    st.markdown("<div class='market-title'>4. Total de Goles 1ra Mitad (1HT)</div>", unsafe_allow_html=True)
    render_card_pro("1ra Mitad: Más de 0.5 Goles", f"Probabilidad Real: {prob_over05_1ht*100:.1f}%", ev_over05_1ht, "BET" if ev_over05_1ht > 0.03 else "SKIP")

    st.markdown("<div class='market-title'>5. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
    render_card_pro("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

    st.markdown("<div class='market-title'>6. Hándicap Asiático</div>", unsafe_allow_html=True)
    render_card_pro(f"{local_nombre} Hándicap -1.0", f"Probabilidad de cubrir: {prob_ha_local*100:.1f}%", (prob_ha_local*1.85)-1, "BET" if (prob_ha_local*1.85)-1 > 0.03 else "SKIP")

    st.markdown("<div class='market-title'>7. Córners & Tarjetas</div>", unsafe_allow_html=True)
    render_card_pro("Más de 8.5 Córners", f"Probabilidad Real: {prob_over_corners_85*100:.1f}%", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")
    render_card_pro("Más de 4.5 Tarjetas", f"Probabilidad Real: {prob_over_tarjetas_45*100:.1f}%", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
