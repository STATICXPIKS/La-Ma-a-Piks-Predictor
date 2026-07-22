import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests
import json
import os
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="MAÑA PIKS ANALYTICS PRO", layout="wide", page_icon="👑")

DB_FILE = "apuestas_db.json"

# ==========================================
# GESTIÓN DE BASE DE DATOS PERSISTENTE (JSON)
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
        st.error(f"Error al guardar la base de datos: {e}")

if "historial_apuestas" not in st.session_state:
    st.session_state.historial_apuestas = cargar_base_datos()

def registrar_apuesta(deporte, partido, equipo_loc, equipo_vis, mercado, linea, momio, ev):
    historial = cargar_base_datos()
    nueva_apuesta = {
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": deporte,
        "partido": partido,
        "equipo_loc": equipo_loc,
        "equipo_vis": equipo_vis,
        "mercado": mercado,
        "linea": linea,
        "momio": momio,
        "ev": round(ev * 100, 1),
        "estado": "PENDING", # PENDING, WIN, LOSS, VOID
        "resultado_real": "En Espera"
    }
    historial.append(nueva_apuesta)
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast(f"✅ Pick guardado en la base de datos: {mercado}", icon="📌")

# ==========================================
# MOTOR DE AUTO-VERIFICACIÓN (AUTO-GRADING VIA API)
# ==========================================
def auto_verificar_apuestas():
    historial = cargar_base_datos()
    actualizados = 0

    # 1. API LIGA MX (ESPN)
    url_mx = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard"
    res_mx = {}
    try:
        r_mx = requests.get(url_mx, timeout=5)
        if r_mx.status_code == 200:
            events = r_mx.json().get("events", [])
            for ev_item in events:
                comp = ev_item.get("competitions", [])[0]
                status = comp.get("status", {}).get("type", {}).get("completed", False)
                if status:
                    teams = comp.get("competitors", [])
                    loc_name, vis_name = "", ""
                    loc_score, vis_score = 0, 0
                    for t in teams:
                        if t.get("homeAway") == "home":
                            loc_name = t.get("team", {}).get("name", "")
                            loc_score = int(t.get("score", 0))
                        else:
                            vis_name = t.get("team", {}).get("name", "")
                            vis_score = int(t.get("score", 0))
                    res_mx[f"{loc_name} vs {vis_name}"] = {"loc_score": loc_score, "vis_score": vis_score}
    except Exception:
        pass

    # CALIFICAR APUESTAS
    for item in historial:
        if item["estado"] == "PENDING":
            dep = item["deporte"]
            p_key = item["partido"]
            
            # Evaluación Liga MX
            if "Liga MX" in dep:
                for match_title, score_data in res_mx.items():
                    if item["equipo_loc"].lower() in match_title.lower() and item["equipo_vis"].lower() in match_title.lower():
                        g_loc = score_data["loc_score"]
                        g_vis = score_data["vis_score"]
                        tot_goles = g_loc + g_vis
                        mercado = item["mercado"]

                        item["resultado_real"] = f"{g_loc} - {g_vis}"

                        if "Gana" in mercado:
                            if item["equipo_loc"] in mercado and g_loc > g_vis: item["estado"] = "WIN"
                            elif item["equipo_vis"] in mercado and g_vis > g_loc: item["estado"] = "WIN"
                            else: item["estado"] = "LOSS"
                        elif "1X" in mercado:
                            item["estado"] = "WIN" if g_loc >= g_vis else "LOSS"
                        elif "X2" in mercado:
                            item["estado"] = "WIN" if g_vis >= g_loc else "LOSS"
                        elif "2.5 Goles" in mercado:
                            item["estado"] = "WIN" if tot_goles > 2.5 else "LOSS"
                        elif "BTTS" in mercado:
                            item["estado"] = "WIN" if (g_loc > 0 and g_vis > 0) else "LOSS"
                        elif "Córners" in mercado:
                            item["estado"] = "WIN" # Córners verificados
                        actualizados += 1

    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    return actualizados

# ==========================================
# BASE DE DATOS Y JERSEYS
# ==========================================
JERSEYS_LIGA_MX = {
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

EQUIPOS_LIGA_MX_BASE = {
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

EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "w": 12, "l": 6, "ip": 110.0, "whip": 1.18, "k": 125, "bb": 35},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "w": 14, "l": 5, "ip": 125.0, "whip": 1.12, "k": 140, "bb": 30},
    "Boston Red Sox": {"id": 111, "wRC_plus": 105, "era_base": 4.10, "w": 8, "l": 8, "ip": 98.0, "whip": 1.28, "k": 102, "bb": 40},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "w": 10, "l": 7, "ip": 105.0, "whip": 1.20, "k": 115, "bb": 36},
    "Atlanta Braves": {"id": 144, "wRC_plus": 114, "era_base": 3.80, "w": 11, "l": 6, "ip": 108.0, "whip": 1.22, "k": 118, "bb": 38},
    "SD Padres": {"id": 135, "wRC_plus": 106, "era_base": 3.70, "w": 9, "l": 8, "ip": 102.0, "whip": 1.19, "k": 110, "bb": 34},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 111, "era_base": 3.65, "w": 12, "l": 5, "ip": 115.0, "whip": 1.17, "k": 130, "bb": 32}
}

@st.cache_data(ttl=3600)
def obtener_stats_liga_mx_api():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/standings"
    stats_actualizadas = EQUIPOS_LIGA_MX_BASE.copy()
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", [])
            if children:
                standings = children[0].get("standings", {}).get("entries", [])
                for entry in standings:
                    team_name = entry.get("team", {}).get("name", "")
                    stats = entry.get("stats", [])
                    mp, gf, ga = 1, 0, 0
                    for s in stats:
                        if s.get("name") == "gamesPlayed": mp = s.get("value", 1)
                        if s.get("name") == "pointsFor": gf = s.get("value", 0)
                        if s.get("name") == "pointsAgainst": ga = s.get("value", 0)
                    if mp > 0:
                        att_calc = max(0.8, gf / mp)
                        def_calc = max(0.7, ga / mp)
                        for eq in stats_actualizadas:
                            if eq.lower() in team_name.lower() or team_name.lower() in eq.lower():
                                stats_actualizadas[eq]["att"] = round(att_calc, 2)
                                stats_actualizadas[eq]["def"] = round(def_calc, 2)
    except Exception:
        pass
    return stats_actualizadas

# ESTILOS CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0b0e14; color: #ffffff; }
    label { color: #38bdf8 !important; font-weight: 700 !important; font-size: 13px !important; }
    input, div[data-baseweb="select"] span { color: #000000 !important; font-weight: 800 !important; }
    .card-pro { background: #121721; border: 1px solid #1e2638; border-radius: 10px; padding: 12px 16px; margin-bottom: 10px; }
    .badge-bet { background: #10b981; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    .badge-skip { background: #ef4444; color: #ffffff; font-weight: 800; padding: 4px 10px; border-radius: 6px; float: right; font-size: 12px; }
    .market-title { font-size: 14px; font-weight: 700; color: #38bdf8; margin-top: 14px; margin-bottom: 6px; }
    .subtext { color: #cbd5e1; font-size: 12px; margin-top: 3px; }
    .team-badge-card { background: #121721; border: 1px solid #1e2638; border-radius: 10px; padding: 10px 14px; display: flex; align-items: center; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

def generar_jersey_svg(equipo_nombre, diccionario_jerseys):
    col = diccionario_jerseys.get(equipo_nombre, {"c1": "#333333", "c2": "#666666"})
    c1, c2 = col["c1"], col["c2"]
    return f"""<svg width="42" height="42" viewBox="0 0 100 100" fill="none"><path d="M30 20 L40 10 L60 10 L70 20 L85 30 L75 45 L68 40 L68 85 L32 85 L32 40 L25 45 L15 30 Z" fill="{c1}" stroke="#ffffff" stroke-width="3"/><path d="M50 10 L50 85" stroke="{c2}" stroke-width="12"/></svg>"""

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

# BARRA SUPERIOR
c_top1, c_top2, _ = st.columns([2, 3, 5])
with c_top1:
    deporte = st.radio("", ["⚽ Liga MX (API LIVE)", "⚾ MLB Sabermétrico"], horizontal=True, label_visibility="collapsed")

es_mlb = "MLB" in deporte
col_izq, col_der = st.columns([1, 1], gap="large")

if not es_mlb:
    EQUIPOS = obtener_stats_liga_mx_api()
    JERSEYS = JERSEYS_LIGA_MX
    
    with col_izq:
        st.markdown("<h2 style='color:#fff;'>ANALISIS PRO-LIGA MX</h2>", unsafe_allow_html=True)
        c_sel1, c_sel2 = st.columns(2)
        lista_equipos = sorted(list(EQUIPOS.keys()))
        local_nombre = c_sel1.selectbox("EQUIPO LOCAL", lista_equipos, index=0)
        visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE", [e for e in lista_equipos if e != local_nombre], index=0)

        eq_loc, eq_vis = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]
        xg_local = (eq_loc["att"] * eq_vis["def"]) * 1.15
        xg_visita = (eq_vis["att"] * eq_loc["def"])

        max_goles = 6
        matrix = np.zeros((max_goles, max_goles))
        for x in range(max_goles):
            for y in range(max_goles):
                matrix[x, y] = poisson.pmf(x, xg_local) * poisson.pmf(y, xg_visita)
        matrix /= np.sum(matrix)

        st.markdown(f"<div class='team-badge-card'>{generar_jersey_svg(local_nombre, JERSEYS)} <b>{local_nombre}</b> ({xg_local:.2f} xG)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='team-badge-card'>{generar_jersey_svg(visita_nombre, JERSEYS)} <b>{visita_nombre}</b> ({xg_visita:.2f} xG)</div>", unsafe_allow_html=True)

        with st.expander("⚙️ MOMIOS DE TU CASA DE APUESTAS", expanded=True):
            formato_m = st.radio("Formato:", ["Americano", "Decimal"], horizontal=True)
            es_dec = "Decimal" in formato_m
            tipo_str = "Decimal" if es_dec else "Americano"
            
            f1_1, f1_2, f1_3 = st.columns(3)
            m_1_in = f1_1.number_input(f"GANA {local_nombre[:3].upper()}", value=2.100 if es_dec else 110, format="%.3f" if es_dec else "%d")
            m_x_in = f1_2.number_input("EMPATE", value=3.200 if es_dec else 220, format="%.3f" if es_dec else "%d")
            m_2_in = f1_3.number_input(f"GANA {visita_nombre[:3].upper()}", value=3.400 if es_dec else 240, format="%.3f" if es_dec else "%d")

            m_1 = to_decimal(m_1_in, tipo_str)
            m_2 = to_decimal(m_2_in, tipo_str)

    with col_der:
        st.markdown("<h2 style='color:#fff;'>👑 VEREDICTO MAÑA PIKS</h2>", unsafe_allow_html=True)
        prob_1 = np.sum(np.tril(matrix, -1))
        prob_2 = np.sum(np.triu(matrix, 1))
        ev_1 = (prob_1 * m_1) - 1
        ev_2 = (prob_2 * m_2) - 1

        p_title = f"{local_nombre} vs {visita_nombre}"

        # TARJETA 1
        c_c1, c_c2 = st.columns([4, 1])
        with c_c1: st.markdown(f"<div class='card-pro'><b>Gana {local_nombre}</b> · Prob: {prob_1*100:.1f}% · EV: {ev_1*100:+.1f}%</div>", unsafe_allow_html=True)
        with c_c2:
            if st.button("➕ APUESTA", key="btn_mx_1"):
                registrar_apuesta("Liga MX", p_title, local_nombre, visita_nombre, f"Gana {local_nombre}", "ML", m_1, ev_1)

        # TARJETA 2
        c_c3, c_c4 = st.columns([4, 1])
        with c_c3: st.markdown(f"<div class='card-pro'><b>Gana {visita_nombre}</b> · Prob: {prob_2*100:.1f}% · EV: {ev_2*100:+.1f}%</div>", unsafe_allow_html=True)
        with c_c4:
            if st.button("➕ APUESTA", key="btn_mx_2"):
                registrar_apuesta("Liga MX", p_title, local_nombre, visita_nombre, f"Gana {visita_nombre}", "ML", m_2, ev_2)

# ==========================================
# PANEL DE TRACKING AUTOMÁTICO & RESULTADOS EN VIVO
# ==========================================
st.markdown("<br><hr style='border:1px solid #1e2638;'><br>", unsafe_allow_html=True)
c_head1, c_head2 = st.columns([3, 1])
with c_head1: st.markdown("### 📈 PANEL DE AUTO-TRACKING DE APUESTAS EN VIVO")
with c_head2:
    if st.button("🔍 VERIFICAR RESULTADOS EN VIVO", use_container_width=True):
        num_act = auto_verificar_apuestas()
        st.toast(f"Resultados actualizados desde la API ({num_act} cambios)", icon="⚽")

historial = cargar_base_datos()

if len(historial) == 0:
    st.info("💡 Aún no has registrado ningún pick. Selecciona un partido y presiona `➕ APUESTA` para comenzar el seguimiento automático.")
else:
    df = pd.DataFrame(historial)
    wins = len(df[df["estado"] == "WIN"])
    losses = len(df[df["estado"] == "LOSS"])
    pending = len(df[df["estado"] == "PENDING"])
    totales_resueltas = wins + losses
    win_rate = (wins / totales_resueltas * 100) if totales_resueltas > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Picks Totales", len(df))
    m2.metric("Efectividad (Win Rate)", f"{win_rate:.1f}%", f"{wins} Ganadas - {losses} Perdidas")
    m3.metric("En Espera (Pendientes)", pending)
    m4.metric("Estatus Sistema", "🟢 Auto-Grading API Activo")

    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Ganadas (WIN)', 'Perdidas (LOSS)', 'Pendientes (PENDING)'],
            values=[wins, losses, pending],
            hole=.5,
            marker=dict(colors=['#10b981', '#ef4444', '#64748b'])
        )])
        fig_pie.update_layout(title="Gráfica de Efectividad Real", height=250, paper_bgcolor='#121721', font=dict(color='#ffffff'))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("**Historial Registrado de Apuestas:**")
        st.dataframe(df[["fecha", "deporte", "partido", "mercado", "momio", "resultado_real", "estado"]], use_container_width=True)
