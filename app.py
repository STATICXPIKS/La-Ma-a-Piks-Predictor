import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="ANÁLISIS PRO-LIGA MX", layout="wide", page_icon="🏆")

# LOGO OFICIAL LIGA MX (SVG VECTORIAL DIRECTO)
SVG_LIGA_MX_OFICIAL = """
<svg width="42" height="42" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="100" height="100" rx="20" fill="#0b0e14"/>
    <path d="M20 20 L50 10 L80 20 L80 80 L50 90 L20 80 Z" fill="#10b981" stroke="#ffffff" stroke-width="3"/>
    <path d="M35 30 L65 30 L65 45 L50 45 L50 70 L35 70 Z" fill="#ffffff"/>
    <circle cx="65" cy="60" r="8" fill="#f59e0b"/>
</svg>
"""

SVG_CORONA_MAÑA_PIKS = """
<svg width="42" height="42" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 75 L15 30 L35 50 L50 20 L65 50 L85 30 L80 75 Z" fill="url(#goldGrad)" stroke="#ffffff" stroke-width="2"/>
    <path d="M20 75 L80 75 L80 83 L20 83 Z" fill="#b45309" stroke="#fef08a" stroke-width="1.5"/>
    <circle cx="15" cy="27" r="4" fill="#ef4444"/>
    <circle cx="50" cy="17" r="5" fill="#3b82f6"/>
    <circle cx="85" cy="27" r="4" fill="#ef4444"/>
    <circle cx="35" cy="79" r="3" fill="#10b981"/>
    <circle cx="50" cy="79" r="3" fill="#ffffff"/>
    <circle cx="65" cy="79" r="3" fill="#10b981"/>
    <defs>
        <linearGradient id="goldGrad" x1="15" y1="20" x2="85" y2="83" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#fef08a"/>
            <stop offset="50%" stop-color="#f59e0b"/>
            <stop offset="100%" stop-color="#b45309"/>
        </linearGradient>
    </defs>
</svg>
"""

# BASE DE ESCUDOS VECTORIALES OFICIALES (SVG) POR CLUB
ESCUDOS_SVG = {
    "América": """<svg width="40" height="40" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#FDE100" stroke="#001A49" stroke-width="4"/><path d="M20 50 Q50 20 80 50 Q50 80 20 50" fill="none" stroke="#C8102E" stroke-width="4"/><text x="32" y="58" font-size="28" font-weight="900" fill="#001A49">CA</text></svg>""",
    "Atlante": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#002B49"/><path d="M10 10 L50 90 L90 10 Z" fill="#C8102E"/><text x="35" y="45" font-size="26" font-weight="900" fill="#ffffff">A</text></svg>""",
    "Atlas": """<svg width="40" height="40" viewBox="0 0 100 100"><rect x="10" y="10" width="40" height="80" fill="#000000"/><rect x="50" y="10" width="40" height="80" fill="#DA291C"/><text x="35" y="65" font-size="45" font-weight="900" fill="#ffffff">A</text></svg>""",
    "Chivas": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#DA291C" stroke="#002452" stroke-width="4"/><path d="M30 10 L30 70 M50 10 L50 90 M70 10 L70 70" stroke="#ffffff" stroke-width="8"/><circle cx="50" cy="35" r="15" fill="#002452"/></svg>""",
    "Cruz Azul": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#00519E"/><rect x="20" y="20" width="60" height="60" fill="#ffffff"/><path d="M35 50 L65 50 M50 35 L50 65" stroke="#DA291C" stroke-width="10"/></svg>""",
    "Juárez": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#78BE20"/><path d="M20 20 L80 20 L50 80 Z" fill="#000000"/><text x="35" y="55" font-size="30" font-weight="900" fill="#DA291C">FCJ</text></svg>""",
    "León": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#007A33" stroke="#FDE100" stroke-width="4"/><text x="30" y="55" font-size="35" font-weight="900" fill="#FDE100">L</text></svg>""",
    "Monterrey": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#002452" stroke="#ffffff" stroke-width="3"/><path d="M30 10 L30 70 M50 10 L50 90 M70 10 L70 70" stroke="#ffffff" stroke-width="6"/></svg>""",
    "Necaxa": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#DA291C" stroke="#ffffff" stroke-width="3"/><path d="M30 10 L30 70 M50 10 L50 90 M70 10 L70 70" stroke="#ffffff" stroke-width="6"/><text x="38" y="45" font-size="28" font-weight="900" fill="#002452">N</text></svg>""",
    "Pachuca": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#002B49" stroke="#ffffff" stroke-width="3"/><path d="M25 10 L25 70 M50 10 L50 90 M75 10 L75 70" stroke="#ffffff" stroke-width="6"/></svg>""",
    "Puebla": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#ffffff" stroke="#003366" stroke-width="4"/><path d="M10 10 L90 90" stroke="#003366" stroke-width="18"/><text x="35" y="60" font-size="28" font-weight="900" fill="#DA291C">P</text></svg>""",
    "Pumas": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#002B49" stroke="#C8A062" stroke-width="4"/><polygon points="50,25 70,65 30,65" fill="#C8A062"/></svg>""",
    "Querétaro": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#00519E"/><path d="M10 50 L90 50" stroke="#000000" stroke-width="15"/><text x="35" y="60" font-size="32" font-weight="900" fill="#ffffff">Q</text></svg>""",
    "San Luis": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#DA291C" stroke="#002B49" stroke-width="4"/><path d="M30 10 L30 70 M50 10 L50 90 M70 10 L70 70" stroke="#002B49" stroke-width="6"/></svg>""",
    "Santos": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#007A33" stroke="#ffffff" stroke-width="4"/><circle cx="50" cy="40" r="18" fill="#ffffff"/><text x="42" y="48" font-size="22" font-weight="900" fill="#007A33">S</text></svg>""",
    "Tigres": """<svg width="40" height="40" viewBox="0 0 100 100"><rect width="100" height="100" rx="15" fill="#FDE100"/><path d="M10 40 L90 40 L90 60 L10 60 Z" fill="#00519E"/><text x="38" y="55" font-size="30" font-weight="900" fill="#FDE100">T</text></svg>""",
    "Tijuana": """<svg width="40" height="40" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="#DA291C" stroke="#000000" stroke-width="4"/><text x="30" y="60" font-size="35" font-weight="900" fill="#000000">X</text></svg>""",
    "Toluca": """<svg width="40" height="40" viewBox="0 0 100 100"><path d="M10 10 L90 10 L50 90 Z" fill="#DA291C" stroke="#ffffff" stroke-width="3"/><circle cx="50" cy="35" r="15" fill="#ffffff"/><text x="43" y="43" font-size="20" font-weight="900" fill="#DA291C">T</text></svg>"""
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
    
    .title-banner {
        font-size: 24px;
        font-weight: 900;
        color: #ffffff !important;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        letter-spacing: -0.5px;
    }
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
    st.markdown(f'<div class="title-banner">{SVG_LIGA_MX_OFICIAL}<span style="margin-left:10px;">ANALISIS PRO-LIGA MX</span></div>', unsafe_allow_html=True)
    
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

    # ESCUDOS VECTORIALES INTEGRADOS
    c_esc1, c_esc2 = st.columns(2)
    with c_esc1:
        st.markdown(f"""
        <div class="team-badge-box">
            <div style="margin-right:12px;">{ESCUDOS_SVG.get(local_nombre, '')}</div>
            <div>
                <div style="font-weight:800; color:#fff; font-size:16px;">{local_nombre}</div>
                <div style="color:#10b981; font-weight:800; font-size:14px;">{xg_local:.2f} <span style="font-size:10px; color:#64748b;">xG Esperado</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_esc2:
        st.markdown(f"""
        <div class="team-badge-box">
            <div style="margin-right:12px;">{ESCUDOS_SVG.get(visita_nombre, '')}</div>
            <div>
                <div style="font-weight:800; color:#fff; font-size:16px;">{visita_nombre}</div>
                <div style="color:#38bdf8; font-weight:800; font-size:14px;">{xg_visita:.2f} <span style="font-size:10px; color:#64748b;">xG Esperado</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    st.markdown(f'<div class="title-banner">{SVG_CORONA_MAÑA_PIKS}<span style="margin-left:10px;">VEREDICTO MAÑA PIKS</span></div>', unsafe_allow_html=True)
    
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
