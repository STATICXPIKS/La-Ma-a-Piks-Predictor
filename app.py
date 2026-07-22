import streamlit as st
import numpy as np
from scipy.stats import poisson

# Configuración de página
st.set_page_config(page_title="Liga MX Predictor", layout="centered", page_icon="⚽")

# BASE DE DATOS DE EQUIPOS, LOGOS, ALTITUDES Y STATS BASE
EQUIPOS = {
    "América": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/227.png",
        "altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2, "forma": ["G", "G", "E", "G", "P"]
    },
    "Atlante": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/221.png",
        "altitud": 2240, "att": 1.35, "def": 1.20, "corners": 5.0, "forma": ["G", "E", "G", "P", "G"]
    },
    "Atlas": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/216.png",
        "altitud": 1560, "att": 1.25, "def": 1.30, "corners": 4.5, "forma": ["E", "P", "P", "G", "P"]
    },
    "Chivas": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/219.png",
        "altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5, "forma": ["G", "G", "P", "E", "G"]
    },
    "Cruz Azul": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/217.png",
        "altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0, "forma": ["G", "E", "G", "G", "P"]
    },
    "Juárez": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/17882.png",
        "altitud": 1130, "att": 1.25, "def": 1.40, "corners": 4.4, "forma": ["P", "G", "P", "E", "P"]
    },
    "León": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/225.png",
        "altitud": 1815, "att": 1.45, "def": 1.25, "corners": 5.1, "forma": ["G", "E", "P", "G", "E"]
    },
    "Monterrey": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/223.png",
        "altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1, "forma": ["G", "P", "G", "E", "G"]
    },
    "Necaxa": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/224.png",
        "altitud": 1800, "att": 1.40, "def": 1.25, "corners": 4.7, "forma": ["G", "E", "P", "P", "E"]
    },
    "Pachuca": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
        "altitud": 2400, "att": 1.70, "def": 1.20, "corners": 5.4, "forma": ["P", "G", "G", "E", "P"]
    },
    "Puebla": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/226.png",
        "altitud": 2230, "att": 1.15, "def": 1.50, "corners": 4.2, "forma": ["P", "P", "P", "E", "P"]
    },
    "Pumas": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/229.png",
        "altitud": 2240, "att": 1.50, "def": 1.15, "corners": 5.2, "forma": ["P", "G", "E", "P", "G"]
    },
    "Querétaro": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/222.png",
        "altitud": 1820, "att": 1.10, "def": 1.35, "corners": 4.0, "forma": ["P", "E", "P", "P", "G"]
    },
    "San Luis": {
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Atletico_san_luis.png/800px-Atletico_san_luis.png",
        "altitud": 1850, "att": 1.20, "def": 1.40, "corners": 4.1, "forma": ["P", "P", "G", "P", "E"]
    },
    "Santos": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/230.png",
        "altitud": 1120, "att": 1.35, "def": 1.45, "corners": 4.9, "forma": ["P", "P", "E", "P", "G"]
    },
    "Tigres": {
        "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e5/Tigres_UANL_logo.svg/1200px-Tigres_UANL_logo.svg.png",
        "altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8, "forma": ["P", "P", "P", "G", "G"]
    },
    "Tijuana": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/220.png",
        "altitud": 60, "att": 1.30, "def": 1.35, "corners": 4.8, "forma": ["E", "P", "G", "P", "P"]
    },
    "Toluca": {
        "logo": "https://a.espncdn.com/i/teamlogos/soccer/500/232.png",
        "altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9, "forma": ["G", "G", "G", "P", "E"]
    }
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

def render_forma(lista_forma):
    html = ""
    for r in lista_forma:
        cls = "bg-g" if r == "G" else ("bg-e" if r == "E" else "bg-p")
        html += f"<span class='form-pill {cls}'>{r}</span>"
    return html

# --- SELECTOR DE PARTIDO ---
st.title("⚽ Liga MX - Predictor Pro")
st.subheader("🏟️ Selecciona el Partido a Analizar")

col_sel1, col_sel2 = st.columns(2)
lista_equipos = sorted(list(EQUIPOS.keys()))

local_nombre = col_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=lista_equipos.index("Atlante") if "Atlante" in lista_equipos else 0)
visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
visita_nombre = col_sel2.selectbox("EQUIPO VISITANTE", visita_opciones, index=visita_opciones.index("América") if "América" in visita_opciones else 0)

eq_local = EQUIPOS[local_nombre]
eq_visita = EQUIPOS[visita_nombre]

# --- BARRA LATERAL ---
st.sidebar.header("🧠 Variables Avanzadas")
bajas_local = st.sidebar.slider(f"Bajas {local_nombre} (%)", 0, 30, 0) / 100.0
bajas_visita = st.sidebar.slider(f"Bajas {visita_nombre} (%)", 0, 30, 0) / 100.0
fatiga_visita = st.sidebar.slider(f"Fatiga {visita_nombre} (%)", 0, 20, 0) / 100.0
tendencia_arbitro = st.sidebar.slider("Rigurosidad Árbitro (Tarjetas)", 2.0, 7.0, 4.5, step=0.5)

# --- CÁLCULO DE ALTITUD Y xG ---
diff_altitud = max(0, eq_local["altitud"] - eq_visita["altitud"])
penalizacion_altitud = diff_altitud * 0.00015

xg_local = (eq_local["att"] * eq_visita["def"]) * (1 - bajas_local) * 1.15
xg_visita = max(0.2, (eq_visita["att"] * eq_local["def"]) * (1 - bajas_visita) * (1 - penalizacion_altitud - fatiga_visita))

max_goles = 6
matrix = np.zeros((max_goles, max_goles))
for x in range(max_goles):
    for y in range(max_goles):
        matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
matrix /= np.sum(matrix)

st.markdown("---")

# --- ENCABEZADO EQUIPOS ---
c_logo1, c_info1 = st.columns([1, 6])
with c_logo1: st.image(eq_local["logo"], width=42)
with c_info1:
    st.markdown(f"<span class='team-name'>{local_nombre}</span> {render_forma(eq_local['forma'])}", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_local:.2f} | Altitud Estadio: {eq_local['altitud']}m (CDMX)")

c_logo2, c_info2 = st.columns([1, 6])
with c_logo2: st.image(eq_visita["logo"], width=42)
with c_info2:
    st.markdown(f"<span class='team-name'>{visita_nombre}</span> {render_forma(eq_visita['forma'])}", unsafe_allow_html=True)
    st.caption(f"xG Calculado: {xg_visita:.2f} | Castigo por Altitud: -{penalizacion_altitud*100:.1f}%")

st.markdown("---")

# --- MÓDULO DE MOMIOS ---
with st.expander("⚙️ METER LOS MOMIOS DE MI CASA DE APUESTAS", expanded=True):
    formato_momios = st.radio("Formato de Momios:", ["Americano (+150 / -200)", "Decimal (2.50 / 1.50)"], horizontal=True)
    es_dec = "Decimal" in formato_momios
    tipo_str = "Decimal" if es_dec else "Americano"
    
    c1, c2, c3 = st.columns(3)
    m_1_in = c1.number_input(f"GANA {local_nombre.upper()}", value=2.80 if es_dec else 180)
    m_x_in = c2.number_input("EMPATE", value=3.20 if es_dec else 220)
    m_2_in = c3.number_input(f"GANA {visita_nombre.upper()}", value=2.30 if es_dec else 130)
    
    c4, c5, c6 = st.columns(3)
    linea_goles = c4.selectbox("LÍNEA DE GOLES", ["O/U 2.5", "O/U 1.5", "O/U 3.5"])
    m_over_in = c5.number_input("MÁS (OVER)", value=1.80 if es_dec else -125)
    m_under_in = c6.number_input("MENOS (UNDER)", value=2.00 if es_dec else 100)
    
    c7, c8, _ = st.columns(3)
    m_btts_s_in = c7.number_input("AMBOS ANOTAN: SÍ", value=1.75 if es_dec else -133)
    m_btts_n_in = c8.number_input("AMBOS ANOTAN: NO", value=2.05 if es_dec else 105)

    m_1 = to_decimal(m_1_in, tipo_str)
    m_over25 = to_decimal(m_over_in, tipo_str)
    m_btts_s = to_decimal(m_btts_s_in, tipo_str)

# --- CÁLCULO DE LOS 7 MERCADOS ---
prob_1 = np.sum(np.tril(matrix, -1))
prob_x = np.sum(np.diag(matrix))
prob_2 = np.sum(np.triu(matrix, 1))

prob_1x = prob_1 + prob_x
prob_over25 = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if x + y > 2.5])
prob_btts_si = np.sum(matrix[1:, 1:])
prob_ha_local = np.sum([matrix[x, y] for x in range(max_goles) for y in range(max_goles) if (x - y) > 1])

lambda_corners = eq_local["corners"] + eq_visita["corners"]
prob_over_corners_85 = 1.0 - poisson.cdf(8, lambda_corners)

lambda_tarjetas = tendencia_arbitro
prob_over_tarjetas_45 = 1.0 - poisson.cdf(4, lambda_tarjetas)

ev_1 = (prob_1 * m_1) - 1
ev_1x = (prob_1x * 1.35) - 1
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
render_card(f"Gana {local_nombre} (1)", f"Probabilidad Real: {prob_1*100:.1f}%", ev_1, "BET" if ev_1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>2. Doble Oportunidad</div>", unsafe_allow_html=True)
render_card(f"{local_nombre} o Empate (1X)", f"Probabilidad Real: {prob_1x*100:.1f}%", ev_1x, "BET" if ev_1x > 0.02 else "SKIP")

st.markdown("<div class='market-header'>3. Total de Goles (Over/Under)</div>", unsafe_allow_html=True)
render_card("Más de 2.5 Goles", f"Probabilidad Real: {prob_over25*100:.1f}% (xG Total: {xg_local+xg_visita:.2f})", ev_over25, "BET" if ev_over25 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>4. Ambos Equipos Anotan (BTTS)</div>", unsafe_allow_html=True)
render_card("Ambos Anotan: SÍ", f"Probabilidad Real: {prob_btts_si*100:.1f}%", ev_btts_si, "BET" if ev_btts_si > 0.03 else "SKIP")

st.markdown("<div class='market-header'>5. Hándicap Asiático</div>", unsafe_allow_html=True)
render_card(f"{local_nombre} Hándicap -1.0", f"Prob. de ganar por 2 o más goles: {prob_ha_local*100:.1f}%", (prob_ha_local*1.85)-1, "BET" if (prob_ha_local*1.85)-1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>6. Córners</div>", unsafe_allow_html=True)
render_card("Más de 8.5 Córners", f"Prob. Real: {prob_over_corners_85*100:.1f}% (Línea esperada: {lambda_corners:.1f})", (prob_over_corners_85*1.75)-1, "BET" if (prob_over_corners_85*1.75)-1 > 0.03 else "SKIP")

st.markdown("<div class='market-header'>7. Tarjetas (Árbitro)</div>", unsafe_allow_html=True)
render_card("Más de 4.5 Tarjetas", f"Prob. Real: {prob_over_tarjetas_45*100:.1f}% (Prom. Árbitro: {lambda_tarjetas:.1f})", (prob_over_tarjetas_45*1.80)-1, "BET" if (prob_over_tarjetas_45*1.80)-1 > 0.03 else "SKIP")
