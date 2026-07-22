import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Liga MX xG Analytics", layout="wide", page_icon="⚽")

# BASE DE DATOS DE EQUIPOS CON LOGOS OFICIALES Y ALTITUDES REALES
EQUIPOS = {
    "América": {"logo": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Club_America_logo.png", "altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2, "forma": ["G", "G", "E", "G", "P"]},
    "Atlante": {"logo": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Atlante_FC_logo.png", "altitud": 2240, "att": 1.35, "def": 1.20, "corners": 5.0, "forma": ["G", "E", "G", "P", "G"]},
    "Atlas": {"logo": "https://upload.wikimedia.org/wikipedia/commons/7/77/Atlas_FC_logo.png", "altitud": 1560, "att": 1.25, "def": 1.30, "corners": 4.5, "forma": ["E", "P", "P", "G", "P"]},
    "Chivas": {"logo": "https://upload.wikimedia.org/wikipedia/commons/4/41/Club_Guadalajara_logo.png", "altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5, "forma": ["G", "G", "P", "E", "G"]},
    "Cruz Azul": {"logo": "https://upload.wikimedia.org/wikipedia/commons/d/d6/Cruz_Azul_Logo.png", "altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0, "forma": ["G", "E", "G", "G", "P"]},
    "Juárez": {"logo": "https://upload.wikimedia.org/wikipedia/commons/0/03/FC_Juarez_logo.png", "altitud": 1130, "att": 1.25, "def": 1.40, "corners": 4.4, "forma": ["P", "G", "P", "E", "P"]},
    "León": {"logo": "https://upload.wikimedia.org/wikipedia/commons/3/30/Club_Leon_logo.png", "altitud": 1815, "att": 1.45, "def": 1.25, "corners": 5.1, "forma": ["G", "E", "P", "G", "E"]},
    "Monterrey": {"logo": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Logo_de_Club_de_F%C3%Batbol_Monterrey.png", "altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1, "forma": ["G", "P", "G", "E", "G"]},
    "Necaxa": {"logo": "https://upload.wikimedia.org/wikipedia/commons/0/03/Club_Necaxa_logo.png", "altitud": 1800, "att": 1.40, "def": 1.25, "corners": 4.7, "forma": ["G", "E", "P", "P", "E"]},
    "Pachuca": {"logo": "https://upload.wikimedia.org/wikipedia/commons/b/b2/CF_Pachuca_logo.png", "altitud": 2400, "att": 1.70, "def": 1.20, "corners": 5.4, "forma": ["P", "G", "G", "E", "P"]},
    "Puebla": {"logo": "https://upload.wikimedia.org/wikipedia/commons/2/29/Puebla_FC_logo.png", "altitud": 2230, "att": 1.15, "def": 1.50, "corners": 4.2, "forma": ["P", "P", "P", "E", "P"]},
    "Pumas": {"logo": "https://upload.wikimedia.org/wikipedia/commons/8/80/Pumas_UNAM.png", "altitud": 2240, "att": 1.50, "def": 1.15, "corners": 5.2, "forma": ["P", "G", "E", "P", "G"]},
    "Querétaro": {"logo": "https://upload.wikimedia.org/wikipedia/commons/b/b4/Gallos_Blancos_Quer%C3%A9taro_logo.png", "altitud": 1820, "att": 1.10, "def": 1.35, "corners": 4.0, "forma": ["P", "E", "P", "P", "G"]},
    "San Luis": {"logo": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Atletico_san_luis.png", "altitud": 1850, "att": 1.20, "def": 1.40, "corners": 4.1, "forma": ["P", "P", "G", "P", "E"]},
    "Santos": {"logo": "https://upload.wikimedia.org/wikipedia/commons/0/07/Club_Santos_Laguna_logo.png", "altitud": 1120, "att": 1.35, "def": 1.45, "corners": 4.9, "forma": ["P", "P", "E", "P", "G"]},
    "Tigres": {"logo": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/Tigres_UANL_logo.svg/1200px-Tigres_UANL_logo.svg.png", "altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8, "forma": ["P", "P", "P", "G", "G"]},
    "Tijuana": {"logo": "https://upload.wikimedia.org/wikipedia/commons/0/0a/Club_Tijuana_logo.png", "altitud": 60, "att": 1.30, "def": 1.35, "corners": 4.8, "forma": ["E", "P", "G", "P", "P"]},
    "Toluca": {"logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Deportivo_Toluca_FC_logo.png", "altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9, "forma": ["G", "G", "G", "P", "E"]}
}

# ESTILOS CSS - DARK NEON MODE
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    
    .neon-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
    }
    
    .neon-card-blue {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
    }
    
    .team-title { font-size: 24px; font-weight: 900; color: #ffffff; }
    .xg-badge { font-size: 22px; font-weight: 800; color: #10b981; }
    .xg-badge-blue { font-size: 22px; font-weight: 800; color: #3b82f6; }
    
    .badge-bet { background: #064e3b; color: #34d399; font-weight: bold; padding: 6px 16px; border-radius: 8px; border: 1px solid #059669; float: right; }
    .badge-skip { background: #451a1a; color: #f87171; font-weight: bold; padding: 6px 16px; border-radius: 8px; border: 1px solid #dc2626; float: right; }
    
    .market-header { font-size: 16px; font-weight: bold; color: #38bdf8; margin-top: 18px; border-bottom: 1px solid #1e293b; padding-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- HEADER & SELECTOR ---
st.markdown("<h1 style='text-align: center; color: #10b981; font-weight: 900;'>⚡ LIGA MX xG ACCUMULATED ANALYTICS</h1>", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)
lista_equipos = sorted(list(EQUIPOS.keys()))

local_nombre = col_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Santos") if "Santos" in lista_equipos else 0)
visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
visita_nombre = col_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("Atlas") if "Atlas" in visita_opciones else 0)

eq_local, eq_visita = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

# --- VARIABLES EN SIDEBAR ---
st.sidebar.header("⚙️ Variables Avanzadas del Partido")
bajas_l = st.sidebar.slider(f"Bajas {local_nombre} (%)", 0, 30, 0) / 100.0
bajas_v = st.sidebar.slider(f"Bajas {visita_nombre} (%)", 0, 30, 0) / 100.0
fatiga_v = st.sidebar.slider(f"Fatiga {visita_nombre} (%)", 0, 20, 0) / 100.0
tendencia_arbitro = st.sidebar.slider("Rigurosidad Árbitro (Tarjetas)", 2.0, 7.0, 4.5, step=0.5)

# --- CÁLCULOS MATEMÁTICOS ---
diff_altitud = max(0, eq_local["altitud"] - eq_visita["altitud"])
penal_altitud = diff_altitud * 0.00015

xg_local = (eq_local["att"] * eq_visita["def"]) * (1 - bajas_l) * 1.15
xg_visita = max(0.2, (eq_visita["att"] * eq_local["def"]) * (1 - bajas_v) * (1 - penal_altitud - fatiga_v))

max_goles = 6
matrix = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
matrix /= np.sum(matrix)

# 1HT xG
xg_local_1ht = xg_local * 0.45
xg_visita_1ht = xg_visita * 0.45
matrix_1ht = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix_1ht[x, y] = poisson.pmf(x, xg_local_1ht) * poisson.pmf(y, xg_visita_1ht)
matrix_1ht /= np.sum(matrix_1ht)

# --- TARJETAS ENCABEZADO ---
c_head1, c_head2 = st.columns(2)
with c_head1:
    st.markdown(f"""
    <div class="neon-card">
        <img src="{eq_local['logo']}" width="48" style="float:left; margin-right:15px;">
        <div class="team-title">{local_nombre}</div>
        <div class="xg-badge">{xg_local:.2f} xG Esperado</div>
        <p style="margin-top:5px; color:#9ca3af;">Altitud Estadio: {eq_local['altitud']}m</p>
    </div>
    """, unsafe_allow_html=True)

with c_head2:
    st.markdown(f"""
    <div class="neon-card-blue">
        <img src="{eq_visita['logo']}" width="48" style="float:left; margin-right:15px;">
        <div class="team-title">{visita_nombre}</div>
        <div class="xg-badge-blue">{xg_visita:.2f} xG Esperado</div>
        <p style="margin-top:5px; color:#9ca3af;">Castigo Altitud: -{penal_altitud*100:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

# --- GRÁFICAS ANALÍTICAS ---
st.markdown("---")
st.subheader("📈 Visual Analytics & xG Progresión")

c_graf1, c_graf2 = st.columns([3, 2])

minutos = [0, 15, 30, 45, 60, 75, 90]
xg_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_local))
xg_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_visita))

fig_xg = go.Figure()
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_local, mode='lines+markers', name=local_nombre, line=dict(color='#10b981', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'))
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_visita, mode='lines+markers', name=visita_nombre, line=dict(color='#3b82f6', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'))

fig_xg.update_layout(
    title="Timeline xG Acumulado",
    paper_bgcolor='rgba(17, 24, 39, 0.8)',
    plot_bgcolor='rgba(17, 24, 39, 0.8)',
    font=dict(color='#ffffff'),
    xaxis=dict(gridcolor='#1f2937', title="Minutos"),
    yaxis=dict(gridcolor='#1f2937', title="xG Acumulado"),
    margin=dict(l=20, r=20, t=40, b=20)
)

with c_graf1: st.plotly_chart(fig_xg, use_container_width=True)

prob_1 = np.sum(np.tril(matrix, -1))
prob_x = np.sum(np.diag(matrix))
prob_2 = np.sum(np.triu(matrix, 1))

fig_pie = go.Figure(data=[go.Pie(
    labels=[f'Gana {local_nombre}', 'Empate', f'Gana {visita_nombre}'],
    values=[prob_1, prob_x, prob_2],
    hole=.6,
    marker=dict(colors=['#10b981', '#f59e0b', '#3b82f6'])
)])
fig_pie.update_layout(
    title="Probabilidad 1X2",
    paper_bgcolor='rgba(17, 24, 39, 0.8)',
    font=dict(color='#ffffff'),
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False
)

with c_graf2: st.plotly_chart(fig_pie, use_container_width=True)

# --- CÁLCULO Y DESPLIEGUE DE LOS 7 MERCADOS ---
st.markdown("---")
with st.expander("⚙️ METER MOMIOS DE CASA DE APUESTAS (CALCULADORA DE VALOR)", expanded=True):
    formato_m = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_m
    tipo_str = "Decimal" if es_dec else "Americano"
    
    c1, c2, c3 = st.columns(3)
    m_1_in = c1.number_input(f"GANA {local_nombre.upper()}", value=2.62 if es_dec else 162)
    m_x_in = c2.number_input("EMPATE", value=3.40 if es_dec else 240)
    m_2_in = c3.number_input(f"GANA {visita_nombre.upper()}", value=2.62 if es_dec else 162)
    
    c4, c5, c6 = st.columns(3)
    linea_goles = c4.selectbox("LÍNEA DE GOLES (90 Min)", ["O/U 2.5", "O/U 1.5", "O/U 3.5"])
    m_over_in = c5.number_input("MÁS (OVER 2.5)", value=1.83 if es_dec else -120)
    m_under_in = c6.number_input("MENOS (UNDER 2.5)", value=1.95 if es_dec else -105)

    c7, c8, c9 = st.columns(3)
    linea_goles_1ht = c7.selectbox("LÍNEA GOLES (1ra Mitad)", ["1HT O/U 0.5", "1HT O/U 1.5", "1HT O/U 2.5"])
    m_over_1ht_in = c8.number_input("1HT MÁS (OVER 0.5)", value=1.40 if es_dec else -250)
    m_under_1ht_in = c9.number_input("1HT MENOS (OVER 0.5)", value=2.75 if es_dec else 175)
    
    c10, c11, _ = st.columns(3)
    m_btts_s_in = c10.number_input("AMBOS ANOTAN: SÍ", value=1.61 if es_dec else -164)
    m_btts_n_in = c11.number_input("AMBOS ANOTAN: NO", value=2.15 if es_dec else 115)

    m_1 = to_decimal(m_1_in, tipo_str)
    m_over25 = to_decimal(m_over_in, tipo_str)
    m_over_1ht = to_decimal(m_over_1ht_in, tipo_str)
    m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# MATH 7 MERCADOS
prob_1x = prob_1 + prob_x
prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
prob_btts_si = np.sum(matrix[1:, 1:])

prob_over05_1ht = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 0.5])
prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

lambda_corners = eq_local["corners"] + eq_visita["corners"]
prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)

lambda_tarjetas = tendencia_arbitro
prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, lambda_tarjetas)

ev_1 = (prob_1 * m_1) - 1
ev_1x = (prob_1x * 1.35) - 1
ev_over25 = (prob_over25 * m_over25) - 1
ev_over05_1ht = (prob_over05_1ht * m_over_1ht) - 1
ev_btts_si = (prob_btts_si * m_btts_s) - 1

st.markdown("### 🎯 Análisis Matemático de los 7 Mercados Clave")

def render_card(titulo, subtitulo, ev, badge):
    badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
    st.markdown(f"""
    <div class="neon-card">
        {badge_html}
        <h4 style="margin: 0; color: #ffffff; font-size:16px;">{titulo}</h4>
        <p style="margin: 4px 0 0 0; color: #9ca3af; font-size: 13px;">{subtitulo} · EV {ev*100:+.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='market-header'>1. Resultado Final (1X2)</div>", unsafe_allow_html=True)
render_card(f"Gana {local_nombre} (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
render_card(f"{local_nombre} o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")

st.markdown("<div class='market-header'>3. Total de Goles (Partido Completo)</div>", unsafe_allow_html=True)
render_card("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local+xg_visita:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>4. Total de Goles 1ra Mitad (1HT)</div>", unsafe_allow_html=True)
render_card("1ra Mitad: Más de 0.5 Goles", f"Probabilidad Real: {prob_over05_1ht*100:.1f}% (xG 1HT: {xg_local_1ht+xg_visita_1ht:.2f})", ev_over05_1ht, "BET" if ev_over05_1ht > 0.03 else "SKIP")

st.markdown("<div class='market-header'>5. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
render_card("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

st.markdown("<div class='market-header'>6. Hándicap Asiático</div>", unsafe_allow_html=True)
render_card(f"{local_nombre} Hándicap -1.0", f"Prob. de ganar por 2 o más goles: {prob_ha_local*100:.1f}%", (prob_ha_local*1.85)-1, "BET" if (prob_ha_local*1.85)-1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>7. Córners & Tarjetas</div>", unsafe_allow_html=True)
render_card("Más de 8.5 Córners", f"Prob. Real: {prob_over_corners_85*100:.1f}% (Línea esperada: {lambda_corners:.1f})", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")
render_card("Más de 4.5 Tarjetas", f"Prob. Real: {prob_over_tarjetas_45*100:.1f}% (Prom. Árbitro: {tendencia_arbitro:.1f})", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
