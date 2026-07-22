import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="ANALISIS PRO-LIGA MX", layout="wide", page_icon="⚽")

# PALETA DE COLORES OFICIALES PARA JERSEYS (SVG)
JERSEYS_COLORES = {
    "América": {"c1": "#FDE100", "c2": "#001A49"},
    "Atlante": {"c1": "#002B49", "c2": "#C8102E"},
    "Atlas": {"c1": "#000000", "c2": "#DA291C"},
    "Chivas": {"c1": "#DA291C", "c2": "#FFFFFF"},
    "Cruz Azul": {"c1": "#00519E", "c2": "#FFFFFF"},
    "Juárez": {"c1": "#78BE20", "c2": "#000000"},
    "León": {"c1": "#007A33", "c2": "#FDE100"},
    "Monterrey": {"c1": "#002452", "c2": "#FFFFFF"},
    "Necaxa": {"c1": "#DA291C", "c2": "#FFFFFF"},
    "Pachuca": {"c1": "#002B49", "c2": "#FFFFFF"},
    "Puebla": {"c1": "#003366", "c2": "#FFFFFF"},
    "Pumas": {"c1": "#002B49", "c2": "#C8A062"},
    "Querétaro": {"c1": "#00519E", "c2": "#000000"},
    "San Luis": {"c1": "#DA291C", "c2": "#002B49"},
    "Santos": {"c1": "#007A33", "c2": "#FFFFFF"},
    "Tigres": {"c1": "#FDE100", "c2": "#00519E"},
    "Tijuana": {"c1": "#DA291C", "c2": "#000000"},
    "Toluca": {"c1": "#DA291C", "c2": "#FFFFFF"}
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

# ESTILOS CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0b0e14; color: #ffffff; }
    
    label { color: #38bdf8 !important; font-weight: 700 !important; font-size: 13px !important; }
    .stSelectbox label, .stNumberInput label, .stRadio label { color: #38bdf8 !important; }
    
    input, div[data-baseweb="select"] span, div[data-baseweb="select"] input {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stNumberInput input { color: #000000 !important; font-weight: 800 !important; }
    
    .card-pro {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    
    .badge-bet { background: #10b981; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    .badge-skip { background: #ef4444; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    
    .market-title { font-size: 14px; font-weight: 700; color: #38bdf8; margin-top: 14px; margin-bottom: 6px; }
    .subtext { color: #cbd5e1; font-size: 12px; margin-top: 3px; }
    
    .team-badge-card {
        background: #121721;
        border: 1px solid #1e2638;
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }

    .header-big-left, .header-big-right {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .header-text-left, .header-text-right {
        font-size: 34px !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        letter-spacing: -1px;
        line-height: 1;
    }
</style>
""", unsafe_allow_html=True)

def generar_jersey_svg(equipo_nombre):
    col = JERSEYS_COLORES.get(equipo_nombre, {"c1": "#333333", "c2": "#666666"})
    c1, c2 = col["c1"], col["c2"]
    
    svg = f"""
    <svg width="42" height="42" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M30 20 L40 10 L60 10 L70 20 L85 30 L75 45 L68 40 L68 85 L32 85 L32 40 L25 45 L15 30 Z" fill="{c1}" stroke="#ffffff" stroke-width="3"/>
        <path d="M50 10 L50 85" stroke="{c2}" stroke-width="12"/>
        <path d="M30 20 L40 10 L60 10 L70 20" fill="none" stroke="#ffffff" stroke-width="3"/>
    </svg>
    """
    return svg

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- DASHBOARD A 2 COLUMNAS ---
col_izq, col_der = st.columns([1, 1], gap="large")

# ==========================================
# COLUMNA IZQUIERDA
# ==========================================
with col_izq:
    st.markdown("""
    <div class="header-big-left">
        <img src="https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/22.png" style="height: 85px; margin-right: 18px; object-fit: contain;">
        <span class="header-text-left">ANALISIS PRO-LIGA MX</span>
    </div>
    """, unsafe_allow_html=True)
    
    c_sel1, c_sel2 = st.columns(2)
    lista_equipos = sorted(list(EQUIPOS.keys()))
    
    local_nombre = c_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Atlante") if "Atlante" in lista_equipos else 0)
    visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
    visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("América") if "América" in visita_opciones else 0)

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

    # 1HT MATRIZ
    xg_local_1ht, xg_visita_1ht = xg_local * 0.45, xg_visita * 0.45
    matrix_1ht = np.zeros((max_goles, max_goles))
    for x in range(max_goles):
        for y in range(max_goles):
            matrix_1ht[x, y] = poisson.pmf(x, xg_local_1ht) * poisson.pmf(y, xg_visita_1ht)
    matrix_1ht /= np.sum(matrix_1ht)

    # JERSEYS SVG CON COLORES DEL CLUB
    c_esc1, c_esc2 = st.columns(2)
    with c_esc1:
        st.markdown(f"""
        <div class="team-badge-card">
            <div style="margin-right: 12px;">{generar_jersey_svg(local_nombre)}</div>
            <div>
                <div style="font-weight: 800; color: #fff; font-size: 16px;">{local_nombre}</div>
                <div style="color: #10b981; font-weight: 800; font-size: 14px;">{xg_local:.2f} <span style="font-size: 11px; color: #38bdf8;">xG Esperado</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_esc2:
        st.markdown(f"""
        <div class="team-badge-card">
            <div style="margin-right: 12px;">{generar_jersey_svg(visita_nombre)}</div>
            <div>
                <div style="font-weight: 800; color: #fff; font-size: 16px;">{visita_nombre}</div>
                <div style="color: #38bdf8; font-weight: 800; font-size: 14px;">{xg_visita:.2f} <span style="font-size: 11px; color: #38bdf8;">xG Esperado</span></div>
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

    # MOMIOS DE TU CASA DE APUESTAS
    with st.expander("⚙️ MOMIOS DE TU CASA DE APUESTAS (CALCULADORA EV)", expanded=True):
        formato_m = st.radio("Formato:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True)
        es_dec = "Decimal" in formato_m
        tipo_str = "Decimal" if es_dec else "Americano"
        
        # Fila 1: 1X2
        f1_1, f1_2, f1_3 = st.columns(3)
        m_1_in = f1_1.number_input(f"GANA {local_nombre.upper()}", value=4.800 if es_dec else 380, format="%.3f" if es_dec else "%d")
        m_x_in = f1_2.number_input("EMPATE", value=3.750 if es_dec else 275, format="%.3f" if es_dec else "%d")
        m_2_in = f1_3.number_input(f"GANA {visita_nombre.upper()}", value=1.710 if es_dec else -141, format="%.3f" if es_dec else "%d")
        
        # Fila 2: Doble Oportunidad
        f_do1, f_do2, f_do3 = st.columns(3)
        m_1x_in = f_do1.number_input(f"1X ({local_nombre[:3].upper()}/EMP)", value=2.100 if es_dec else 110, format="%.3f" if es_dec else "%d")
        m_12_in = f_do2.number_input("12 (LOCAL/VISITA)", value=1.280 if es_dec else -357, format="%.3f" if es_dec else "%d")
        m_x2_in = f_do3.number_input(f"X2 (EMP/{visita_nombre[:3].upper()})", value=1.180 if es_dec else -555, format="%.3f" if es_dec else "%d")

        # Fila 3: Goles Partido Completo
        f2_1, f2_2, f2_3 = st.columns(3)
        linea_goles = f2_1.selectbox("GOLES (90 Min)", ["O/U 2.5", "O/U 1.5"])
        m_over_in = f2_2.number_input("OVER 2.5", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
        m_under_in = f2_3.number_input("UNDER 2.5", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

        # Fila 4: Goles 1HT (CON OPCIONES 0.5 Y 1.5)
        f3_1, f3_2, f3_3 = st.columns(3)
        linea_goles_1ht = f3_1.selectbox("GOLES (1HT)", ["1HT O/U 0.5", "1HT O/U 1.5"])
        es_1ht_05 = "0.5" in linea_goles_1ht
        
        m_over_1ht_in = f3_2.number_input(
            "1HT OVER 0.5" if es_1ht_05 else "1HT OVER 1.5", 
            value=(1.360 if es_1ht_05 else 2.650) if es_dec else (-278 if es_1ht_05 else 165), 
            format="%.3f" if es_dec else "%d"
        )
        m_under_1ht_in = f3_3.number_input(
            "1HT UNDER 0.5" if es_1ht_05 else "1HT UNDER 1.5", 
            value=(2.880 if es_1ht_05 else 1.450) if es_dec else (188 if es_1ht_05 else -222), 
            format="%.3f" if es_dec else "%d"
        )
        
        # Fila 5: BTTS
        f4_1, f4_2, _ = st.columns(3)
        m_btts_s_in = f4_1.number_input("BTTS SÍ", value=1.770 if es_dec else -130, format="%.3f" if es_dec else "%d")
        m_btts_n_in = f4_2.number_input("BTTS NO", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

        # Conversiones
        m_1 = to_decimal(m_1_in, tipo_str)
        m_2 = to_decimal(m_2_in, tipo_str)
        m_1x = to_decimal(m_1x_in, tipo_str)
        m_x2 = to_decimal(m_x2_in, tipo_str)
        m_over25 = to_decimal(m_over_in, tipo_str)
        m_over_1ht = to_decimal(m_over_1ht_in, tipo_str)
        m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# ==========================================
# COLUMNA DERECHA: VEREDICTOS
# ==========================================
with col_der:
    st.markdown("""
    <div class="header-big-right">
        <span style="font-size: 40px; margin-right: 15px; line-height:1;">👑</span>
        <span class="header-text-right">VEREDICTO MAÑA PIKS</span>
    </div>
    """, unsafe_allow_html=True)
    
    # CÁLCULOS DUALES Y MÚLTIPLES
    prob_1x = prob_1 + prob_x
    prob_x2 = prob_2 + prob_x
    prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
    prob_btts_si = np.sum(matrix[1:, 1:])
    
    # CÁLCULO DINÁMICO DE GOLES 1HT (0.5 O 1.5)
    if es_1ht_05:
        prob_1ht_target = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 0.5])
        texto_1ht_target = "1ra Mitad: Más de 0.5 Goles"
    else:
        prob_1ht_target = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 1.5])
        texto_1ht_target = "1ra Mitad: Más de 1.5 Goles"

    prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])
    prob_ha_visita = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (y - x) > 1])

    lambda_corners = eq_local["corners"] + eq_visita["corners"]
    prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)
    prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, 4.5)

    ev_1 = (prob_1 * m_1) - 1
    ev_2 = (prob_2 * m_2) - 1
    ev_1x = (prob_1x * m_1x) - 1
    ev_x2 = (prob_x2 * m_x2) - 1
    ev_over25 = (prob_over25 * m_over25) - 1
    ev_1ht = (prob_1ht_target * m_over_1ht) - 1
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

    # 1. RESULTADO FINAL
    st.markdown("<div class='market-title'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
    render_card_pro(f"Gana {local_nombre} (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")
    render_card_pro(f"Gana {visita_nombre} (2)", f"Probabilidad Real: {prob_2*100:.1f}%", ev_2, "BET" if ev_2 > 0.03 else "SKIP")

    # 2. DOBLE OPORTUNIDAD
    st.markdown("<div class='market-title'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
    render_card_pro(f"{local_nombre} o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")
    render_card_pro(f"Empate o {visita_nombre} (X2)", f"Probabilidad Real: {prob_x2*100:.1f}%", ev_x2, "BET" if ev_x2 > 0.02 else "SKIP")

    # 3. TOTAL GOLES 90 MIN
    st.markdown("<div class='market-title'>3. Total de Goles (Partido Completo)</div>", unsafe_allow_html=True)
    render_card_pro("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local+xg_visita:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

    # 4. TOTAL GOLES 1HT (DINÁMICO 0.5 / 1.5)
    st.markdown("<div class='market-title'>4. Total de Goles 1ra Mitad (1HT)</div>", unsafe_allow_html=True)
    render_card_pro(texto_1ht_target, f"Probabilidad Real: {prob_1ht_target*100:.1f}%", ev_1ht, "BET" if ev_1ht > 0.03 else "SKIP")

    # 5. BTTS
    st.markdown("<div class='market-title'>5. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
    render_card_pro("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

    # 6. HÁNDICAP ASIÁTICO
    st.markdown("<div class='market-title'>6. Hándicap Asiático</div>", unsafe_allow_html=True)
    if xg_local >= xg_visita:
        render_card_pro(f"{local_nombre} Hándicap -1.0", f"Prob. cubrir: {prob_ha_local*100:.1f}%", (prob_ha_local*1.85)-1, "BET" if (prob_ha_local*1.85)-1 > 0.03 else "SKIP")
    else:
        render_card_pro(f"{visita_nombre} Hándicap -1.0", f"Prob. cubrir: {prob_ha_visita*100:.1f}%", (prob_ha_visita*1.85)-1, "BET" if (prob_ha_visita*1.85)-1 > 0.03 else "SKIP")

    # 7. CÓRNERS & TARJETAS
    st.markdown("<div class='market-title'>7. Córners & Tarjetas</div>", unsafe_allow_html=True)
    render_card_pro("Más de 8.5 Córners", f"Probabilidad Real: {prob_over_corners_85*100:.1f}%", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")
    render_card_pro("Más de 4.5 Tarjetas", f"Probabilidad Real: {prob_over_tarjetas_45*100:.1f}%", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
