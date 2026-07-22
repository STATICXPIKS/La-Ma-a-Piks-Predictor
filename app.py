import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Liga MX Predictor Pro", layout="centered", page_icon="⚽")

# LOGOS OFICIALES WIKIMEDIA (PROBADOS Y ESTABLES)
LOGOS = {
    "América": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Club_America_logo.png/800px-Club_America_logo.png",
    "Atlante": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Atlante_FC_logo.png/800px-Atlante_FC_logo.png",
    "Atlas": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Atlas_FC_logo.png/800px-Atlas_FC_logo.png",
    "Chivas": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Club_Guadalajara_logo.png/800px-Club_Guadalajara_logo.png",
    "Cruz Azul": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Cruz_Azul_Logo.png/800px-Cruz_Azul_Logo.png",
    "Juárez": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/FC_Juarez_logo.png/800px-FC_Juarez_logo.png",
    "León": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Club_Leon_logo.png/800px-Club_Leon_logo.png",
    "Monterrey": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Logo_de_Club_de_F%C3%Batbol_Monterrey.png/800px-Logo_de_Club_de_F%C3%Batbol_Monterrey.png",
    "Necaxa": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Club_Necaxa_logo.png/800px-Club_Necaxa_logo.png",
    "Pachuca": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/CF_Pachuca_logo.png/800px-CF_Pachuca_logo.png",
    "Puebla": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Puebla_FC_logo.png/800px-Puebla_FC_logo.png",
    "Pumas": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Pumas_UNAM.png/800px-Pumas_UNAM.png",
    "Querétaro": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Gallos_Blancos_Quer%C3%A9taro_logo.png/800px-Gallos_Blancos_Quer%C3%A9taro_logo.png",
    "San Luis": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Atletico_san_luis.png/800px-Atletico_san_luis.png",
    "Santos": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Club_Santos_Laguna_logo.png/800px-Club_Santos_Laguna_logo.png",
    "Tigres": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/Tigres_UANL_logo.svg/800px-Tigres_UANL_logo.svg.png",
    "Tijuana": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Club_Tijuana_logo.png/800px-Club_Tijuana_logo.png",
    "Toluca": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Deportivo_Toluca_FC_logo.png/800px-Deportivo_Toluca_FC_logo.png"
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

# ESTILOS CSS DARK PROFESSIONAL
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0d1117; color: #ffffff; }
    
    /* Contenedores Profesionales */
    .card-pro {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .team-name-title {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    
    .xg-value { font-size: 20px; font-weight: 800; color: #238636; }
    .xg-value-blue { font-size: 20px; font-weight: 800; color: #2f81f7; }
    
    /* Badges BET/SKIP */
    .badge-bet { background: #238636; color: #ffffff; font-weight: 700; padding: 4px 12px; border-radius: 6px; float: right; font-size: 13px; }
    .badge-skip { background: #da3633; color: #ffffff; font-weight: 700; padding: 4px 12px; border-radius: 6px; float: right; font-size: 13px; }
    
    .market-title { font-size: 15px; font-weight: 700; color: #58a6ff; margin-top: 16px; border-bottom: 1px solid #21262d; padding-bottom: 4px; }
    .subtext { color: #8b949e; font-size: 13px; margin: 0; }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- HEADER DE LA APP ---
st.markdown("<h2 style='text-align: center; color: #ffffff; font-weight: 900; margin-bottom: 20px;'>⚽ LIGA MX ANALYTICS PRO</h2>", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)
lista_equipos = sorted(list(EQUIPOS.keys()))

local_nombre = col_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Santos") if "Santos" in lista_equipos else 0)
visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
visita_nombre = col_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("Atlas") if "Atlas" in visita_opciones else 0)

eq_local, eq_visita = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

# --- AJUSTES EN SIDEBAR ---
st.sidebar.header("🧠 Ajustes del Partido")
bajas_l = st.sidebar.slider(f"Bajas {local_nombre} (%)", 0, 30, 0) / 100.0
bajas_v = st.sidebar.slider(f"Bajas {visita_nombre} (%)", 0, 30, 0) / 100.0
fatiga_v = st.sidebar.slider(f"Fatiga {visita_nombre} (%)", 0, 20, 0) / 100.0
tendencia_arbitro = st.sidebar.slider("Rigurosidad Árbitro (Tarjetas)", 2.0, 7.0, 4.5, step=0.5)

# --- MATEMÁTICAS DEL MODELO ---
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

# 1HT
xg_local_1ht = xg_local * 0.45
xg_visita_1ht = xg_visita * 0.45
matrix_1ht = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix_1ht[x, y] = poisson.pmf(x, xg_local_1ht) * poisson.pmf(y, xg_visita_1ht)
matrix_1ht /= np.sum(matrix_1ht)

# --- TARJETAS ENCABEZADO CON ESCUDOS CORREGIDOS ---
st.markdown("---")
c_head1, c_head2 = st.columns(2)

with c_head1:
    c_img, c_txt = st.columns([1, 3])
    with c_img: st.image(LOGOS[local_nombre], use_container_width=True)
    with c_txt:
        st.markdown(f"<div class='team-name-title'>{local_nombre}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='xg-value'>{xg_local:.2f} <span style='font-size:12px; color:#8b949e;'>xG Esperado</span></div>", unsafe_allow_html=True)

with c_head2:
    c_img, c_txt = st.columns([1, 3])
    with c_img: st.image(LOGOS[visita_nombre], use_container_width=True)
    with c_txt:
        st.markdown(f"<div class='team-name-title'>{visita_nombre}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='xg-value-blue'>{xg_visita:.2f} <span style='font-size:12px; color:#8b949e;'>xG Esperado</span></div>", unsafe_allow_html=True)

# --- GRÁFICAS COMPACTAS (MÁS PEQUEÑAS) ---
st.markdown("---")
c_graf1, c_graf2 = st.columns(2)

# Gráfica 1: xG Timeline Compacto
minutos = [0, 15, 30, 45, 60, 75, 90]
xg_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_local))
xg_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_visita))

fig_xg = go.Figure()
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_local, mode='lines', name=local_nombre, line=dict(color='#238636', width=3)))
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_visita, mode='lines', name=visita_nombre, line=dict(color='#2f81f7', width=3)))

fig_xg.update_layout(
    title=dict(text="xG Progresión por Minuto", font=dict(size=13, color="#ffffff")),
    height=240,
    paper_bgcolor='#161b22',
    plot_bgcolor='#161b22',
    font=dict(color='#ffffff', size=10),
    xaxis=dict(gridcolor='#21262d', showgrid=True),
    yaxis=dict(gridcolor='#21262d', showgrid=True),
    margin=dict(l=30, r=20, t=35, b=25),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

with c_graf1: st.plotly_chart(fig_xg, use_container_width=True)

# Gráfica 2: Dona 1X2 Compacta
prob_1 = np.sum(np.tril(matrix, -1))
prob_x = np.sum(np.diag(matrix))
prob_2 = np.sum(np.triu(matrix, 1))

fig_pie = go.Figure(data=[go.Pie(
    labels=[local_nombre, 'Empate', visita_nombre],
    values=[prob_1, prob_x, prob_2],
    hole=.6,
    marker=dict(colors=['#238636', '#d29922', '#2f81f7'])
)])

fig_pie.update_layout(
    title=dict(text="Distribución 1X2", font=dict(size=13, color="#ffffff")),
    height=240,
    paper_bgcolor='#161b22',
    font=dict(color='#ffffff', size=10),
    margin=dict(l=20, r=20, t=35, b=20),
    showlegend=False
)

with c_graf2: st.plotly_chart(fig_pie, use_container_width=True)

# --- MÓDULO DE MOMIOS Y CALCULADORA DE VALOR ---
st.markdown("---")
with st.expander("⚙️ MOMIOS DE TU CASA DE APUESTAS (CALCULADORA EV)", expanded=True):
    formato_m = st.radio("Formato:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_m
    tipo_str = "Decimal" if es_dec else "Americano"
    
    c1, c2, c3 = st.columns(3)
    m_1_in = c1.number_input(f"GANA {local_nombre.upper()}", value=2.62 if es_dec else 162)
    m_x_in = c2.number_input("EMPATE", value=3.40 if es_dec else 240)
    m_2_in = c3.number_input(f"GANA {visita_nombre.upper()}", value=2.62 if es_dec else 162)
    
    c4, c5, c6 = st.columns(3)
    linea_goles = c4.selectbox("GOLES (90 Min)", ["O/U 2.5", "O/U 1.5", "O/U 3.5"])
    m_over_in = c5.number_input("OVER 2.5", value=1.83 if es_dec else -120)
    m_under_in = c6.number_input("UNDER 2.5", value=1.95 if es_dec else -105)

    c7, c8, c9 = st.columns(3)
    linea_goles_1ht = c7.selectbox("GOLES (1ra Mitad)", ["1HT O/U 0.5", "1HT O/U 1.5"])
    m_over_1ht_in = c8.number_input("1HT OVER 0.5", value=1.40 if es_dec else -250)
    m_under_1ht_in = c9.number_input("1HT UNDER 0.5", value=2.75 if es_dec else 175)
    
    c10, c11, _ = st.columns(3)
    m_btts_s_in = c10.number_input("BTTS SÍ", value=1.61 if es_dec else -164)
    m_btts_n_in = c11.number_input("BTTS NO", value=2.15 if es_dec else 115)

    m_1 = to_decimal(m_1_in, tipo_str)
    m_over25 = to_decimal(m_over_in, tipo_str)
    m_over_1ht = to_decimal(m_over_1ht_in, tipo_str)
    m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# --- DESPLIEGUE DE LOS 7 MERCADOS ---
prob_1x = prob_1 + prob_x
prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
prob_btts_si = np.sum(matrix[1:, 1:])
prob_over05_1ht = np.sum([matrix_1ht[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 0.5])
prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

lambda_corners = eq_local["corners"] + eq_visita["corners"]
prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)
prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, tendencia_arbitro)

ev_1 = (prob_1 * m_1) - 1
ev_1x = (prob_1x * 1.35) - 1
ev_over25 = (prob_over25 * m_over25) - 1
ev_over05_1ht = (prob_over05_1ht * m_over_1ht) - 1
ev_btts_si = (prob_btts_si * m_btts_s) - 1

st.markdown("### 🎯 Veredictos del Modelo")

def render_card_pro(titulo, subtitulo, ev, badge):
    badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"
    st.markdown(f"""
    <div class="card-pro">
        {badge_html}
        <div style="font-weight: 800; font-size: 15px; color: #ffffff;">{titulo}</div>
        <p class="subtext">{subtitulo} · <b>EV {ev*100:+.1f}%</b></p>
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
