import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import requests
import json
import os
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y TEMA NEÓN
# ==========================================
st.set_page_config(
    page_title="MAÑA PIKS - MLB SABERMÉTRICO PRO",
    layout="wide",
    page_icon="👑",
    initial_sidebar_state="collapsed"
)

DB_FILE = "apuestas_db.json"

# Estilos CSS Personalizados estilo PropsBR (Cyber Neón Dark)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Orbitron:wght@700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #080a0c !important;
        color: #e2e8f0;
    }

    .stApp {
        background-color: #080a0c !important;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .header-big {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        color: #f5d742 !important;
        text-shadow: 0 0 10px rgba(245, 215, 66, 0.4);
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Cards de Mercados */
    .card-pro {
        background-color: #0e1217;
        border: 1px solid #1a2228;
        border-left: 4px solid #00ff66;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    .card-star {
        background: #1a1608;
        border: 1px solid #ffd700;
        border-left: 5px solid #ffd700;
        box-shadow: 0 0 14px rgba(255, 215, 0, 0.3);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    .card-trap {
        background: #240d13;
        border: 1px solid #ff3366;
        border-left: 5px solid #ff3366;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* Badges */
    .badge-star {
        background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%);
        color: #000000;
        font-weight: 900;
        padding: 3px 10px;
        border-radius: 4px;
        float: right;
        font-size: 11px;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.6);
    }

    .badge-clean {
        background: #00ff66;
        color: #000000;
        font-weight: 900;
        padding: 3px 10px;
        border-radius: 4px;
        float: right;
        font-size: 11px;
    }

    .badge-trap {
        background: #ff3366;
        color: #ffffff;
        font-weight: 900;
        padding: 3px 10px;
        border-radius: 4px;
        float: right;
        font-size: 11px;
    }

    .badge-medium {
        background: #ffaa00;
        color: #000000;
        font-weight: 900;
        padding: 3px 10px;
        border-radius: 4px;
        float: right;
        font-size: 11px;
    }

    .badge-fade {
        background: #3d1b20;
        color: #ff3366;
        border: 1px solid #661e27;
        font-weight: 900;
        padding: 3px 10px;
        border-radius: 4px;
        float: right;
        font-size: 11px;
    }

    .subtext { color: #8c9ba5; font-size: 12px; margin-top: 4px; }
    .pitcher-info { background-color: #0e1217; border-left: 4px solid #f5d742; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; }

    /* Botones Neón */
    div.stButton > button {
        background: #00ff66 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        border-radius: 6px !important;
        border: none !important;
        box-shadow: 0 0 8px rgba(0, 255, 102, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DATOS Y AUTO-VERIFICACIÓN
# ==========================================
def cargar_base_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_base_datos(datos):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

if "historial_apuestas" not in st.session_state:
    st.session_state.historial_apuestas = cargar_base_datos()

def registrar_apuesta(partido, equipo_loc, equipo_vis, mercado, linea, momio, ev):
    historial = cargar_base_datos()
    nueva = {
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": "MLB",
        "partido": partido,
        "equipo_loc": equipo_loc,
        "equipo_vis": equipo_vis,
        "mercado": mercado,
        "linea": str(linea),
        "momio": momio,
        "ev": round(ev * 100, 1),
        "estado": "PENDING",
        "resultado_real": "En Espera"
    }
    historial.append(nueva)
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast(f"✅ Pick guardado: {mercado}", icon="📌")

def eliminar_apuesta(id_item):
    historial = cargar_base_datos()
    historial = [x for x in historial if x.get("id") != id_item]
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast("🗑️ Apuesta eliminada", icon="🗑️")
    st.rerun()

# ==========================================
# BASE SABERMÉTRICA MLB
# ==========================================
EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 118, "ops": .760, "iso": .195, "xera_base": 3.55, "fip": 3.60, "whip": 1.15, "k_pct": 24.5, "bb_pct": 8.0, "park_factor": 1.02, "w": 14, "l": 6, "ip": 115.0, "k": 130},
    "LA Dodgers": {"id": 119, "wRC_plus": 122, "ops": .780, "iso": .205, "xera_base": 3.40, "fip": 3.45, "whip": 1.10, "k_pct": 26.0, "bb_pct": 7.5, "park_factor": 0.98, "w": 15, "l": 5, "ip": 120.0, "k": 145},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 112, "ops": .745, "iso": .180, "xera_base": 3.60, "fip": 3.65, "whip": 1.16, "k_pct": 24.0, "bb_pct": 8.2, "park_factor": 1.04, "w": 13, "l": 6, "ip": 110.0, "k": 128},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "ops": .735, "iso": .175, "xera_base": 3.70, "fip": 3.75, "whip": 1.19, "k_pct": 23.5, "bb_pct": 7.8, "park_factor": 0.99, "w": 11, "l": 8, "ip": 108.0, "k": 118},
    "Atlanta Braves": {"id": 144, "wRC_plus": 115, "ops": .755, "iso": .190, "xera_base": 3.75, "fip": 3.80, "whip": 1.20, "k_pct": 24.2, "bb_pct": 8.1, "park_factor": 1.01, "w": 12, "l": 7, "ip": 105.0, "k": 120},
    "Baltimore Orioles": {"id": 110, "wRC_plus": 111, "ops": .740, "iso": .185, "xera_base": 3.80, "fip": 3.85, "whip": 1.21, "k_pct": 23.0, "bb_pct": 8.3, "park_factor": 0.97, "w": 11, "l": 7, "ip": 102.0, "k": 112},
    "Cincinnati Reds": {"id": 113, "wRC_plus": 98, "ops": .705, "iso": .160, "xera_base": 4.30, "fip": 4.35, "whip": 1.32, "k_pct": 21.5, "bb_pct": 9.0, "park_factor": 1.08, "w": 8, "l": 11, "ip": 92.0, "k": 95},
    "Cleveland Guardians": {"id": 114, "wRC_plus": 100, "ops": .710, "iso": .150, "xera_base": 3.45, "fip": 3.50, "whip": 1.14, "k_pct": 25.0, "bb_pct": 7.2, "park_factor": 0.96, "w": 12, "l": 6, "ip": 112.0, "k": 125}
}

@st.cache_data(ttl=1800)
def obtener_abridores_mlb_hoy(team_id_local, team_id_visita):
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={hoy}&endDate={hoy}&hydrate=probablePitcher"
    p_loc, p_vis = "Por Confirmar", "Por Confirmar"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            dates = data.get("dates", [])
            if dates:
                games = dates[0].get("games", [])
                for g in games:
                    home_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
                    away_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
                    if home_id == team_id_local or away_id == team_id_local:
                        p_loc = g.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        p_vis = g.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        break
    except Exception:
        pass
    return p_loc, p_vis

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

def to_american_str(prob):
    if prob <= 0 or prob >= 1: return "+100"
    dec = 1.0 / prob
    return f"+{int(round((dec - 1) * 100))}" if dec >= 2.0 else f"{int(round(-100 / (dec - 1)))}"

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.markdown('<div class="header-big"><span>⚾</span> MAÑA PIKS - MOTOR SABERMÉTRICO MLB</div>', unsafe_allow_html=True)

c_sel1, c_sel2 = st.columns(2)
lista_eq = sorted(list(EQUIPOS_MLB.keys()))
loc_nombre = c_sel1.selectbox("EQUIPO LOCAL (HOME)", lista_eq, index=lista_eq.index("Philadelphia Phillies") if "Philadelphia Phillies" in lista_eq else 0)
vis_opciones = [x for x in lista_eq if x != loc_nombre]
vis_nombre = c_sel2.selectbox("EQUIPO VISITANTE (AWAY)", vis_opciones, index=vis_opciones.index("LA Dodgers") if "LA Dodgers" in vis_opciones else 0)

eq_loc, eq_vis = EQUIPOS_MLB[loc_nombre], EQUIPOS_MLB[vis_nombre]
p_loc_auto, p_vis_auto = obtener_abridores_mlb_hoy(eq_loc["id"], eq_vis["id"])

st.markdown(f"""
<div class="pitcher-info">
    <b>⚾ ABRIDORES PROGRAMADOS:</b><br>
    • {loc_nombre}: <b style="color:#00ff66;">{p_loc_auto}</b> | xERA Base: {eq_loc['xera_base']} | WHIP: {eq_loc['whip']}<br>
    • {vis_nombre}: <b style="color:#00ff66;">{p_vis_auto}</b> | xERA Base: {eq_vis['xera_base']} | WHIP: {eq_vis['whip']}
</div>
""", unsafe_allow_html=True)

# Parámetros y Ajustes
with st.expander("📊 PARÁMETROS SABERMÉTRICOS Y CLIMA (ESTADIO/BULLPEN/PARK FACTOR)", expanded=False):
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        st.markdown("**Local - Ajustes**")
        wrc_loc = st.number_input("wRC+ Local", value=int(eq_loc["wRC_plus"]))
        xera_vis = st.number_input("xERA Pitcher Visitante", value=float(eq_vis["xera_base"]), format="%.2f")
        whip_vis = st.number_input("WHIP Pitcher Visitante", value=float(eq_vis["whip"]), format="%.2f")

    with col_p2:
        st.markdown("**Visitante - Ajustes**")
        wrc_vis = st.number_input("wRC+ Visitante", value=int(eq_vis["wRC_plus"]))
        xera_loc = st.number_input("xERA Pitcher Local", value=float(eq_loc["xera_base"]), format="%.2f")
        whip_loc = st.number_input("WHIP Pitcher Local", value=float(eq_loc["whip"]), format="%.2f")

    with col_p3:
        st.markdown("**Clima / Factor Estadio**")
        tipo_estadio = st.radio("Estadio", ["Abierto", "Domo / Techo Cerrado"], horizontal=True)
        viento_kmh = st.number_input("Viento (km/h)", value=0 if "Domo" in tipo_estadio else 14)
        viento_dir = st.selectbox("Dirección Viento", ["A favor (Out)", "En contra (In)", "Cruzado"])
        park_f = st.number_input("Park Factor", value=float(eq_loc["park_factor"]), format="%.2f")

# Cálculo de Proyección xR (Expected Runs)
mult_clima = 1.0
if "Abierto" in tipo_estadio:
    if "favor" in viento_dir: mult_clima += (viento_kmh * 0.005)
    elif "contra" in viento_dir: mult_clima -= (viento_kmh * 0.005)

xr_local = ((wrc_loc / 100.0) * (xera_vis / 4.10) * (whip_vis / 1.25) * 4.30) * park_f * mult_clima
xr_visita = ((wrc_vis / 100.0) * (xera_loc / 4.10) * (whip_loc / 1.25) * 4.10) * park_f * mult_clima

# Matriz de Distribución de Poisson
max_c = 16
matrix_mlb = np.zeros((max_c, max_c))
for x in range(max_c):
    for y in range(max_c):
        matrix_mlb[x, y] = poisson.pmf(x, xr_local) * poisson.pmf(y, xr_visita)
matrix_mlb /= np.sum(matrix_mlb)

# Matriz F5
xr_loc_f5 = xr_local * 0.55
xr_vis_f5 = xr_visita * 0.55
matrix_f5 = np.zeros((max_c, max_c))
for x in range(max_c):
    for y in range(max_c):
        matrix_f5[x, y] = poisson.pmf(x, xr_loc_f5) * poisson.pmf(y, xr_vis_f5)
matrix_f5 /= np.sum(matrix_f5)

# CAPTURA DE MOMIOS
with st.expander("⚙️ CAPTURA DE MOMIOS DEL CASINO", expanded=True):
    formato_m = st.radio("Formato Momios:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True)
    es_dec = "Decimal" in formato_m
    t_str = "Decimal" if es_dec else "Americano"

    c_m1, c_m2, c_m3 = st.columns(3)
    m_ml_loc_in = c_m1.number_input(f"ML {loc_nombre[:3]}", value=1.830 if es_dec else -120)
    m_ml_vis_in = c_m2.number_input(f"ML {vis_nombre[:3]}", value=2.050 if es_dec else 105)
    linea_tot = c_m3.selectbox("Línea Total Carreras", ["7.5", "8.5", "9.5"], index=1)

    c_m4, c_m5, c_m6 = st.columns(3)
    m_over_in = c_m4.number_input("Over Total", value=1.900 if es_dec else -110)
    m_under_in = c_m5.number_input("Under Total", value=1.900 if es_dec else -110)
    linea_k_loc = c_m6.selectbox(f"Línea K's ({p_loc_auto[:12]})", ["4.5", "5.5", "6.5"], index=1)

    c_m7, c_m8, c_m9 = st.columns(3)
    m_k_loc_over_in = c_m7.number_input("Over K's Local", value=1.850 if es_dec else -118)
    linea_outs_loc = c_m8.selectbox(f"Línea Outs ({p_loc_auto[:12]})", ["14.5", "15.5", "17.5"], index=1)
    m_outs_loc_over_in = c_m9.number_input("Over Outs Local", value=1.800 if es_dec else -125)

    c_m10, c_m11, c_m12 = st.columns(3)
    m_f5_loc_in = c_m10.number_input(f"F5 ML {loc_nombre[:3]}", value=1.800 if es_dec else -125)
    m_nrfi_in = c_m11.number_input("NRFI (0 Carreras 1st Inn)", value=1.830 if es_dec else -120)
    m_yrfi_in = c_m12.number_input("YRFI (1+ Carreras 1st Inn)", value=1.950 if es_dec else -105)

    m_ml_loc = to_decimal(m_ml_loc_in, t_str)
    m_ml_vis = to_decimal(m_ml_vis_in, t_str)
    m_over = to_decimal(m_over_in, t_str)
    m_under = to_decimal(m_under_in, t_str)
    m_k_loc_over = to_decimal(m_k_loc_over_in, t_str)
    m_outs_loc_over = to_decimal(m_outs_loc_over_in, t_str)
    m_f5_loc = to_decimal(m_f5_loc_in, t_str)
    m_nrfi = to_decimal(m_nrfi_in, t_str)
    m_yrfi = to_decimal(m_yrfi_in, t_str)

# ==========================================
# CÁLCULOS DE PROBABILIDAD Y MATRIZ DE RIESGO
# ==========================================
prob_ml_loc = np.sum(np.tril(matrix_mlb, -1))
prob_ml_vis = np.sum(np.triu(matrix_mlb, 1))

tot_t = float(linea_tot)
prob_tot_over = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if x + y > tot_t])
prob_tot_under = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if x + y < tot_t])

# K's
k_rate_loc = (eq_loc["k"] / eq_loc["ip"]) if eq_loc["ip"] > 0 else 1.0
lambda_k_loc = k_rate_loc * (17.5 / 3.0)
prob_k_over = 1.0 - poisson.cdf(int(float(linea_k_loc)), lambda_k_loc)

# Outs
outs_exp = 16.5
prob_outs_over = 1.0 - poisson.cdf(int(float(linea_outs_loc)), outs_exp)

# F5
prob_f5_loc = np.sum(np.tril(matrix_f5, -1))

# NRFI / YRFI
xr_1st = (xr_local + xr_visita) * 0.13
prob_nrfi = poisson.pmf(0, xr_1st)
prob_yrfi = 1.0 - prob_nrfi

# EV Cálculos
ev_ml_loc = (prob_ml_loc * m_ml_loc) - 1
ev_ml_vis = (prob_ml_vis * m_ml_vis) - 1
ev_tot_over = (prob_tot_over * m_over) - 1
ev_tot_under = (prob_tot_under * m_under) - 1
ev_k_over = (prob_k_over * m_k_loc_over) - 1
ev_outs_over = (prob_outs_over * m_outs_loc_over) - 1
ev_f5_loc = (prob_f5_loc * m_f5_loc) - 1
ev_nrfi = (prob_nrfi * m_nrfi) - 1
ev_yrfi = (prob_yrfi * m_yrfi) - 1

# EVALUADOR ANTI-TRAMPA Y CLASIFICACIÓN
def auditar_mercado(prob, momio_dec, ev):
    # Detección de trampa: EV sospechoso mayor a 18% o cuota inflada por posible lesión
    es_trap = (ev > 0.18) or (prob >= 0.65 and momio_dec >= 2.20)
    
    if 0.75 <= prob <= 0.90:
        rango = "HIGH CONFIDENCE"
        color_badge = "badge-clean"
        if es_trap:
            etiqueta = "⚠️ POSIBLE TRAMPA (+EV SOSPECHOSO)"
            color_badge = "badge-trap"
        elif ev > 0.02:
            etiqueta = "💎 APUESTA ESTRELLA (+EV / VALOR LIMPIO)"
            color_badge = "badge-star"
        else:
            etiqueta = "🛡️ VALOR LIMPIO"
    elif 0.60 <= prob <= 0.74:
        rango = "MEDIUM PROBABILITY"
        color_badge = "badge-medium"
        etiqueta = "⚠️ MEDIANA CERTEZA / VOLÁTIL" if not es_trap else "⚠️ ALERTA TRAP"
    else:
        rango = "LOW PROBABILITY"
        color_badge = "badge-fade"
        etiqueta = "🚨 FADE ALERT (ALTO RIESGO)"

    return rango, etiqueta, color_badge, es_trap

# ==========================================
# SECCIÓN 1: VISTAS / TARJETAS DE MERCADOS
# ==========================================
st.markdown("<h3 style='color:#f5d742;'>👑 VEREDICTO DE LOS 7 MERCADOS CLAVE</h3>", unsafe_allow_html=True)

mercados_data = [
    ("1. Moneyline Directo", f"Gana {loc_nombre} (ML)", prob_ml_loc, ev_ml_loc, m_ml_loc, "ML"),
    ("1. Moneyline Directo", f"Gana {vis_nombre} (ML)", prob_ml_vis, ev_ml_vis, m_ml_vis, "ML"),
    ("2. Total de Carreras", f"Más de {linea_tot} Carreras (OVER)", prob_tot_over, ev_tot_over, m_over, str(linea_tot)),
    ("2. Total de Carreras", f"Menos de {linea_tot} Carreras (UNDER)", prob_tot_under, ev_tot_under, m_under, str(linea_tot)),
    ("3. Run Line (-1.5 / +1.5)", f"{loc_nombre} RL -1.5", prob_ml_loc * 0.75, (prob_ml_loc * 0.75 * 2.40) - 1, 2.40, "-1.5"),
    ("4. Props K's Pitcher", f"{p_loc_auto}: OVER {linea_k_loc} K's", prob_k_over, ev_k_over, m_k_loc_over, str(linea_k_loc)),
    ("5. Props Outs Pitcher", f"{p_loc_auto}: OVER {linea_outs_loc} Outs", prob_outs_over, ev_outs_over, m_outs_loc_over, str(linea_outs_loc)),
    ("6. Primeras 5 Entradas (F5)", f"F5 ML {loc_nombre}", prob_f5_loc, ev_f5_loc, m_f5_loc, "F5 ML"),
    ("7. Mercado 1er Inning", "NRFI: 0 Carreras en la 1ª Entrada", prob_nrfi, ev_nrfi, m_nrfi, "NRFI"),
    ("7. Mercado 1er Inning", "YRFI: 1+ Carreras en la 1ª Entrada", prob_yrfi, ev_yrfi, m_yrfi, "YRFI")
]

partido_str = f"{loc_nombre} vs {vis_nombre}"

for cat, tit, p_val, ev_val, m_val, lin_val in mercados_data:
    rango, etiq, badge_cls, is_trap = auditar_mercado(p_val, m_val, ev_val)
    card_cls = "card-star" if "APUESTA ESTRELLA" in etiq else ("card-trap" if is_trap else "card-pro")
    m_am = to_american_str(p_val)
    m_justo = 1.0 / p_val if p_val > 0 else 99.0

    st.markdown(f"""
    <div class="{card_cls}">
        <span class="{badge_cls}">{etiq}</span>
        <div style="font-weight: 800; font-size: 15px; color: #ffffff;">[{cat}] {tit}</div>
        <div class="subtext">
            Prob. Real: <b>{p_val*100:.1f}%</b> · Momio Justo: <b>{m_justo:.2f} ({m_am})</b> · Rango: <b>{rango}</b> · <b style="color:#00ff66;">EV {ev_val*100:+.1f}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("➕ REGISTRAR PICK", key=f"btn_{tit}"):
        registrar_apuesta(partido_str, loc_nombre, vis_nombre, tit, lin_val, m_val, ev_val)

# ==========================================
# SECCIÓN 2: PASO 2 - MATRIZ DE RIESGO
# ==========================================
st.markdown("<br><hr style='border:1px solid #1a2228;'><br>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#f5d742;'>📊 PASO 2: MATRIZ DE RIESGO DE 3 NIVELES Y AUDITORÍA ANTI-TRAMPA</h3>", unsafe_allow_html=True)

matriz_filas = []
for cat, tit, p_val, ev_val, m_val, lin_val in mercados_data:
    rango, etiq, _, is_trap = auditar_mercado(p_val, m_val, ev_val)
    matriz_filas.append({
        "Mercado": tit,
        "Prob. Calculada": f"{p_val*100:.1f}%",
        "Momio Casino": f"{m_val:.2f}",
        "EV (%)": f"{ev_val*100:+.1f}%",
        "Rango de Riesgo": rango,
        "Dictamen / Sello": etiq
    })

df_matriz = pd.DataFrame(matriz_filas)

# Estilizado visual de la tabla
def color_rango(val):
    if val == "HIGH CONFIDENCE":
        return 'background-color: rgba(0, 255, 102, 0.15); color: #00ff66; font-weight: bold;'
    elif val == "MEDIUM PROBABILITY":
        return 'background-color: rgba(255, 170, 0, 0.15); color: #ffaa00; font-weight: bold;'
    else:
        return 'background-color: rgba(255, 51, 102, 0.15); color: #ff3366; font-weight: bold;'

st.dataframe(df_matriz.style.map(color_rango, subset=["Rango de Riesgo"]), use_container_width=True)

# ==========================================
# SECCIÓN 3: TRACKER DE APUESTAS PENDIENTES / RESUELTAS
# ==========================================
st.markdown("<br><hr style='border:1px solid #1a2228;'><br>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#f5d742;'>📈 TRACKER PERSISTENTE DE APUESTAS</h3>", unsafe_allow_html=True)

historial = cargar_base_datos()
if len(historial) == 0:
    st.info("💡 No hay apuestas en el historial. Haz clic en `➕ REGISTRAR PICK` en cualquiera de los mercados superiores.")
else:
    list_p = [x for x in historial if x.get("estado") == "PENDING"]
    list_w = [x for x in historial if x.get("estado") == "WIN"]
    list_l = [x for x in historial if x.get("estado") == "LOSS"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Picks Guardados", len(historial))
    m2.metric("Ganadas / Perdidas", f"{len(list_w)} W - {len(list_l)} L")
    m3.metric("Pendientes", len(list_p))

    st.markdown("**Lista de Registro:**")
    for row in historial:
        c1, c2, c3, c4, c5 = st.columns([1.5, 3, 1.5, 1.5, 0.8])
        c1.write(f"<span style='color:#718096; font-size:12px;'>{row.get('fecha')}</span>", unsafe_allow_html=True)
        c2.write(f"**{row.get('mercado')}** ({row.get('partido')})")
        c3.write(f"Momio: **{row.get('momio')}**")
        c4.write(f"Estado: **{row.get('estado')}**")
        with c5:
            if st.button("🗑️", key=f"del_track_{row.get('id')}"):
                eliminar_apuesta(row.get('id'))
