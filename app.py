import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Liga MX xG Analytics", layout="wide", page_icon="⚽")

# BASE DE DATOS DE EQUIPOS
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

# ESTILOS CSS - DARK NEON MODE & GLASSMORPHISM
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    
    /* Contenedores Glassmorphism Neón */
    .neon-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    
    .neon-card-blue {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .team-title { font-size: 26px; font-weight: 900; color: #ffffff; text-shadow: 0 0 10px rgba(255,255,255,0.2); }
    .xg-badge { font-size: 24px; font-weight: 800; color: #10b981; }
    .xg-badge-blue { font-size: 24px; font-weight: 800; color: #3b82f6; }
    
    .badge-bet { background: #064e3b; color: #34d399; font-weight: bold; padding: 6px 16px; border-radius: 8px; border: 1px solid #059669; float: right; }
    .badge-skip { background: #451a1a; color: #f87171; font-weight: bold; padding: 6px 16px; border-radius: 8px; border: 1px solid #dc2626; float: right; }
    
    .form-pill { display: inline-block; width: 20px; height: 20px; border-radius: 6px; color: white; font-size: 11px; font-weight: bold; text-align: center; line-height: 20px; margin-right: 3px; }
    .bg-g { background-color: #10b981; } .bg-e { background-color: #f59e0b; } .bg-p { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# --- HEADER & SELECTOR ---
st.markdown("<h1 style='text-align: center; color: #10b981; font-weight: 900;'>⚡ LIGA MX xG ACCUMULATED ANALYTICS</h1>", unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns(2)
lista_equipos = sorted(list(EQUIPOS.keys()))

local_nombre = col_sel1.selectbox("LOCAL TEAM", lista_equipos, index=lista_equipos.index("Santos") if "Santos" in lista_equipos else 0)
visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
visita_nombre = col_sel2.selectbox("VISITING TEAM", visita_opciones, index=visita_opciones.index("Atlas") if "Atlas" in visita_opciones else 0)

eq_local, eq_visita = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]

# --- AJUSTES EN SIDEBAR ---
st.sidebar.header("⚙️ Match Variables")
bajas_l = st.sidebar.slider(f"Bajas {local_nombre} (%)", 0, 30, 0) / 100.0
bajas_v = st.sidebar.slider(f"Bajas {visita_nombre} (%)", 0, 30, 0) / 100.0
fatiga_v = st.sidebar.slider(f"Fatiga {visita_nombre} (%)", 0, 20, 0) / 100.0

# --- CÁLCULO DE xG Y MATRICES ---
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

# --- ENCABEZADO DE PARTIDO EN NEÓN ---
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
        <p style="margin-top:5px; color:#9ca3af;">Penalización Altitud: -{penal_altitud*100:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

# --- PANEL DE GRÁFICAS ESTILO CAPTURA ---
st.markdown("---")
st.subheader("📈 Visual Analytics & xG Progresión")

c_graf1, c_graf2 = st.columns([3, 2])

# GRÁFICA 1: xG ACUMULADO POR MINUTO (LÍNEAS SUAVIZADAS NEÓN)
minutos = [0, 15, 30, 45, 60, 75, 90]
xg_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_local))
xg_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(6)) * xg_visita))

fig_xg = go.Figure()
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_local, mode='lines+markers', name=local_nombre, line=dict(color='#10b981', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'))
fig_xg.add_trace(go.Scatter(x=minutos, y=xg_acc_visita, mode='lines+markers', name=visita_nombre, line=dict(color='#3b82f6', width=4, shape='spline'), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'))

fig_xg.update_layout(
    title="xG Accumulated Timeline",
    paper_bgcolor='rgba(17, 24, 39, 0.8)',
    plot_bgcolor='rgba(17, 24, 39, 0.8)',
    font=dict(color='#ffffff'),
    xaxis=dict(gridcolor='#1f2937', title="Minutos"),
    yaxis=dict(gridcolor='#1f2937', title="xG Acumulado"),
    margin=dict(l=20, r=20, t=40, b=20)
)

with c_graf1:
    st.plotly_chart(fig_xg, use_container_width=True)

# GRÁFICA 2: MARCADORES PROBABLES & DONUT POSESIÓN
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
    title="Probabilidad Implícita (1X2)",
    paper_bgcolor='rgba(17, 24, 39, 0.8)',
    font=dict(color='#ffffff'),
    margin=dict(l=10, r=10, t=40, b=10),
    showlegend=False
)

with c_graf2:
    st.plotly_chart(fig_pie, use_container_width=True)

# --- MÓDULO DE MOMIOS & RECOMENDACIONES ---
st.markdown("---")
with st.expander("⚙️ METER MOMIOS DE CASA DE APUESTAS (CALCULADORA EV)", expanded=True):
    formato_m = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_m
    tipo_str = "Decimal" if es_dec else "Americano"
    
    col_m1, col_m2, col_m3 = st.columns(3)
    m_1_in = col_m1.number_input(f"GANA {local_nombre.upper()}", value=2.10 if es_dec else 110)
    m_x_in = col_m2.number_input("EMPATE", value=3.30 if es_dec else 230)
    m_2_in = col_m3.number_input(f"GANA {visita_nombre.upper()}", value=3.50 if es_dec else 250)
    
    m_1 = to_decimal(m_1_in, tipo_str)

ev_1 = (prob_1 * m_1) - 1

st.markdown("### 🎯 Veredicto de Apuestas (+EV)")
badge = "BET" if ev_1 > 0.03 else "SKIP"
badge_html = f"<span class='badge-bet'>BET</span>" if badge == "BET" else f"<span class='badge-skip'>SKIP</span>"

st.markdown(f"""
<div class="neon-card">
    {badge_html}
    <h3 style="margin:0; color:#ffffff;">Gana {local_nombre}</h3>
    <p style="margin:5px 0 0 0; color:#9ca3af;">Probabilidad Modelo: {prob_1*100:.1f}% · EV Estimado: {ev_1*100:+.1f}%</p>
</div>
""", unsafe_allow_html=True)
