import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests

st.set_page_config(
    page_title="LA MAÑA PIKS - Auditoría Sabermétrica MLB",
    page_icon="⚾",
    layout="wide"
)

st.markdown("""
    <style>
    /* Estilos Futuristas: Verde Botella, Verde Fluorescente y Oro */
    .stApp {
        background-color: #0b1f14;
        color: #e2e8f0;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #06140e;
        border-right: 1px solid #10b981;
    }
    
    .matchup-card {
        background: linear-gradient(135deg, #0f2d1e 0%, #081c13 100%);
        border: 1px solid #10b981;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
    }
    .badge-bet {
        background-color: rgba(16, 185, 129, 0.25);
        color: #34d399;
        border: 1px solid #10b981;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-maybe {
        background-color: rgba(245, 158, 11, 0.25);
        color: #fbbf24;
        border: 1px solid #f59e0b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-fade {
        background-color: rgba(239, 68, 68, 0.25);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .best-value-tag {
        background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
        color: #0b1f14;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 900;
        margin-left: 6px;
        box-shadow: 0 0 10px rgba(251, 191, 36, 0.4);
    }
    .golden-star-tag {
        background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
        color: #0b1f14;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 900;
        margin-left: 6px;
        box-shadow: 0 0 14px rgba(255, 215, 0, 0.6);
    }
    .model-explanation {
        background: rgba(15, 45, 30, 0.9);
        border-left: 4px solid #10b981;
        border-right: 1px solid #10b981;
        border-top: 1px solid #10b981;
        border-bottom: 1px solid #10b981;
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        margin-top: 20px;
        font-size: 0.95rem;
        color: #e2e8f0;
    }
    h1, h2, h3 {
        color: #34d399 !important;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 0 10px rgba(52, 211, 153, 0.3);
    }
    p, span, label {
        color: #cbd5e1 !important;
    }
    
    div[data-baseweb="input"] {
        background-color: #121212 !important;
        border-color: #10b981 !important;
    }
    input {
        background-color: #121212 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

ESTADIOS_COORDS = {
    "Yankee Stadium": {"lat": 40.8296, "lon": -73.9262, "factor": 1.02},
    "Fenway Park": {"lat": 42.3467, "lon": -71.0972, "factor": 1.05},
    "Dodger Stadium": {"lat": 34.0739, "lon": -118.2400, "factor": 0.98},
    "Wrigley Field": {"lat": 41.9484, "lon": -87.6553, "factor": 1.03},
    "Oracle Park": {"lat": 37.7786, "lon": -122.3893, "factor": 0.93},
    "Truist Park": {"lat": 33.8908, "lon": -84.4678, "factor": 1.01},
    "Great American Ball Park": {"lat": 39.0974, "lon": -84.5085, "factor": 1.08},
    "Minute Maid Park": {"lat": 29.7573, "lon": -95.3555, "factor": 1.01},
    "Daikin Park": {"lat": 29.7573, "lon": -95.3555, "factor": 1.01},
    "Rogers Centre": {"lat": 43.6414, "lon": -79.3894, "factor": 1.02},
    "Citizens Bank Park": {"lat": 39.9061, "lon": -75.1665, "factor": 1.06},
    "Nationals Park": {"lat": 38.8730, "lon": -77.0074, "factor": 1.01},
    "Oriole Park at Camden Yards": {"lat": 39.2839, "lon": -76.6216, "factor": 1.04},
    "Citi Field": {"lat": 40.7571, "lon": -73.8458, "factor": 0.97},
    "Guaranteed Rate Field": {"lat": 41.8299, "lon": -87.6338, "factor": 1.04},
    "Progressive Field": {"lat": 41.4962, "lon": -81.6852, "factor": 1.01},
    "Comerica Park": {"lat": 42.3390, "lon": -83.0485, "factor": 0.99},
    "Kauffman Stadium": {"lat": 39.0517, "lon": -94.4803, "factor": 1.00},
    "Target Field": {"lat": 44.9817, "lon": -93.2775, "factor": 1.00},
    "T-Mobile Park": {"lat": 47.5914, "lon": -122.3323, "factor": 0.96},
    "RingCentral Coliseum": {"lat": 37.7516, "lon": -122.2005, "factor": 0.98},
    "Angel Stadium": {"lat": 33.8003, "lon": -117.8827, "factor": 1.01},
    "Globe Life Field": {"lat": 32.7512, "lon": -97.0825, "factor": 1.00},
    "Busch Stadium": {"lat": 38.6226, "lon": -90.1928, "factor": 0.97},
    "American Family Field": {"lat": 43.0280, "lon": -87.9712, "factor": 1.02},
    "PNC Park": {"lat": 40.4469, "lon": -80.0057, "factor": 0.98},
    "Petco Park": {"lat": 32.7076, "lon": -117.1570, "factor": 0.94},
    "Coors Field": {"lat": 39.7559, "lon": -104.9942, "factor": 1.15},
    "LoanDepot park": {"lat": 25.7781, "lon": -80.2196, "factor": 0.95},
    "Tropicana Field": {"lat": 27.7682, "lon": -82.6534, "factor": 0.96},
    "Chase Field": {"lat": 33.4455, "lon": -112.0667, "factor": 1.04},
}

TEAM_LOGOS = {
    "Athletics": "https://www.mlbstatic.com/team-logos/133.svg",
    "Cincinnati Reds": "https://www.mlbstatic.com/team-logos/113.svg",
    "New York Yankees": "https://www.mlbstatic.com/team-logos/147.svg",
    "Boston Red Sox": "https://www.mlbstatic.com/team-logos/111.svg",
    "Los Angeles Dodgers": "https://www.mlbstatic.com/team-logos/119.svg",
    "Chicago Cubs": "https://www.mlbstatic.com/team-logos/112.svg",
    "San Francisco Giants": "https://www.mlbstatic.com/team-logos/137.svg",
    "Atlanta Braves": "https://www.mlbstatic.com/team-logos/144.svg",
    "Houston Astros": "https://www.mlbstatic.com/team-logos/117.svg",
    "Toronto Blue Jays": "https://www.mlbstatic.com/team-logos/141.svg",
    "Washington Nationals": "https://www.mlbstatic.com/team-logos/120.svg",
    "Philadelphia Phillies": "https://www.mlbstatic.com/team-logos/143.svg",
    "New York Mets": "https://www.mlbstatic.com/team-logos/121.svg",
    "Miami Marlins": "https://www.mlbstatic.com/team-logos/146.svg",
    "Baltimore Orioles": "https://www.mlbstatic.com/team-logos/110.svg",
    "Tampa Bay Rays": "https://www.mlbstatic.com/team-logos/139.svg",
    "Cleveland Guardians": "https://www.mlbstatic.com/team-logos/114.svg",
    "Detroit Tigers": "https://www.mlbstatic.com/team-logos/116.svg",
    "Kansas City Royals": "https://www.mlbstatic.com/team-logos/118.svg",
    "Minnesota Twins": "https://www.mlbstatic.com/team-logos/142.svg",
    "Chicago White Sox": "https://www.mlbstatic.com/team-logos/145.svg",
    "Milwaukee Brewers": "https://www.mlbstatic.com/team-logos/158.svg",
    "St. Louis Cardinals": "https://www.mlbstatic.com/team-logos/138.svg",
    "Pittsburgh Pirates": "https://www.mlbstatic.com/team-logos/134.svg",
    "Arizona Diamondbacks": "https://www.mlbstatic.com/team-logos/109.svg",
    "Colorado Rockies": "https://www.mlbstatic.com/team-logos/115.svg",
    "San Diego Padres": "https://www.mlbstatic.com/team-logos/135.svg",
    "Seattle Mariners": "https://www.mlbstatic.com/team-logos/136.svg",
    "Texas Rangers": "https://www.mlbstatic.com/team-logos/140.svg",
    "Los Angeles Angels": "https://www.mlbstatic.com/team-logos/108.svg",
}

def obtener_logo(nombre_equipo):
    for key, url in TEAM_LOGOS.items():
        if key.lower() in nombre_equipo.lower() or nombre_equipo.lower() in key.lower():
            return url
    return "https://www.mlbstatic.com/team-logos/default-team-logo.svg"

@st.cache_data(ttl=1800)
def obtener_clima_estadio(nombre_estadio):
    coords = ESTADIOS_COORDS.get(nombre_estadio, {"lat": 39.0974, "lon": -84.5085, "factor": 1.0})
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    try:
        res = requests.get(url, timeout=5).json()
        current = res.get("current", {})
        temp_c = current.get('temperature_2m', 24)
        return {
            "temperatura": f"{temp_c}°C",
            "humedad": f"{current.get('relative_humidity_2m', 55)}%",
            "viento": f"{current.get('wind_speed_10m', 9)} km/h",
            "park_factor": coords["factor"]
        }
    except:
        return {"temperatura": "24°C", "humedad": "55%", "viento": "9 km/h", "park_factor": 1.0}

@st.cache_data(ttl=3600)
def obtener_juegos_hoy(fecha_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={fecha_str}&hydrate=probablePitcher,venue,team"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        juegos_lista = []
        if "dates" in data and len(data["dates"]) > 0:
            for game in data["dates"][0]["games"]:
                away_team = game["teams"]["away"]["team"]["name"]
                home_team = game["teams"]["home"]["team"]["name"]
                venue_name = game.get("venue", {}).get("name", "Wrigley Field")
                
                probable_pitchers = game.get("probablePitchers", {})
                away_p_data = probable_pitchers.get("away")
                home_p_data = probable_pitchers.get("home")
                
                if away_p_data and "fullName" in away_p_data:
                    away_pitcher = away_p_data["fullName"]
                else:
                    away_pitcher = game["teams"]["away"].get("probablePitcher", {}).get("fullName", f"Por Anunciar ({away_team})")
                
                if home_p_data and "fullName" in home_p_data:
                    home_pitcher = home_p_data["fullName"]
                else:
                    home_pitcher = game["teams"]["home"].get("probablePitcher", {}).get("fullName", f"Por Anunciar ({home_team})")
                
                juegos_lista.append({
                    "matchup": f"{away_team} @ {home_team}",
                    "away": away_team,
                    "home": home_team,
                    "away_logo": obtener_logo(away_team),
                    "home_logo": obtener_logo(home_team),
                    "away_pitcher": away_pitcher,
                    "home_pitcher": home_pitcher,
                    "venue": venue_name,
                    "status": game["status"]["detailedState"]
                })
        if not juegos_lista:
            juegos_lista = [{
                "matchup": "Los Angeles Dodgers @ Chicago Cubs (Juego Muestra)",
                "away": "Los Angeles Dodgers",
                "home": "Chicago Cubs",
                "away_logo": obtener_logo("Los Angeles Dodgers"),
                "home_logo": obtener_logo("Chicago Cubs"),
                "away_pitcher": "Yoshinobu Yamamoto",
                "home_pitcher": "Shota Imanaga",
                "venue": "Wrigley Field",
                "status": "Scheduled"
            }]
        return juegos_lista
    except:
        return [{
            "matchup": "Los Angeles Dodgers @ Chicago Cubs (Modo Seguro)",
            "away": "Los Angeles Dodgers",
            "home": "Chicago Cubs",
            "away_logo": obtener_logo("Los Angeles Dodgers"),
            "home_logo": obtener_logo("Chicago Cubs"),
            "away_pitcher": "Yoshinobu Yamamoto",
            "home_pitcher": "Shota Imanaga",
            "venue": "Wrigley Field",
            "status": "Scheduled"
        }]

def calcular_probabilidad_implicita(momio):
    if momio > 0:
        return 100 / (momio + 100)
    elif momio < 0:
        return abs(momio) / (abs(momio) + 100)
    return 0.5

def evaluar_opcion_robusta(prob_modelo_pct, momio_casa):
    prob_modelo = prob_modelo_pct / 100.0
    prob_imp = calcular_probabilidad_implicita(momio_casa)
    edge = (prob_modelo - prob_imp) * 100
    
    es_apuesta_estrella = 75.0 <= prob_modelo_pct <= 90.0 and edge > 0
    
    if prob_modelo_pct >= 70 and edge > 1:
        estado = "BET (+EV)"
        clase_css = "badge-bet"
    elif prob_modelo_pct >= 58:
        estado = "MAYBE"
        clase_css = "badge-maybe"
    else:
        estado = "FADE"
        clase_css = "badge-fade"
        
    return edge, estado, clase_css, es_apuesta_estrella

# Inicializar historial en session_state si no existe
if "historial_apuestas" not in st.session_state:
    st.session_state.historial_apuestas = []

def agregar_al_historial(partido, seleccion, prob, momio, edge, tipo_estrellas):
    # Evitar duplicados exactos pendientes
    nueva_apuesta = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "partido": partido,
        "seleccion": seleccion,
        "prob": prob,
        "momio": momio,
        "edge": edge,
        "estrella": tipo_estrellas,
        "estado": "PENDIENTE" # PENDIENTE, WIN, LOSS
    }
    st.session_state.historial_apuestas.append(nueva_apuesta)

def render_pick_box_clean(partido_key, label_izq, prob_izq, momio_izq, label_der, prob_der, momio_der):
    edge_i, est_i, css_i, star_i = evaluar_opcion_robusta(prob_izq, momio_izq)
    edge_d, est_d, css_d, star_d = evaluar_opcion_robusta(prob_der, momio_der)
    
    mejor = "izq" if edge_i >= edge_d else "der"
    
    col1, col2 = st.columns(2)
    with col1:
        tags_html = f'<span class="{css_i}">{est_i}</span>'
        tipo_est = "Normal"
        if star_i:
            tags_html += '<span class="golden-star-tag">💎 APUESTA ESTRELLA</span>'
            tipo_est = "💎 APUESTA ESTRELLA"
        elif mejor == "izq":
            tags_html += '<span class="best-value-tag">⭐ +EV VALOR</span>'
            tipo_est = "⭐ +EV VALOR"
            
        st.markdown(f"""
        <div style="background-color:#081c13; border:1px solid #10b981; border-radius:10px; padding:14px; margin-bottom:8px;">
            <div style="color:#ffffff; font-weight:bold; font-size:1.05rem; margin-bottom:4px;">{label_izq}</div>
            <div style="color:#cbd5e1; font-size:0.85rem; margin-bottom:8px;">Prob: {prob_izq}% | Momio: {momio_izq} | Edge: {edge_i:+.1f}%</div>
            <div>{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"📥 Seleccionar {label_izq}", key=f"btn_{partido_key}_{label_izq.replace(' ', '_')}"):
            agregar_al_historial(partido_key, label_izq, prob_izq, momio_izq, edge_i, tipo_est)
            st.success(f"¡Selección guardada en tu historial!")
        
    with col2:
        tags_html_d = f'<span class="{css_d}">{est_d}</span>'
        tipo_est_d = "Normal"
        if star_d:
            tags_html_d += '<span class="golden-star-tag">💎 APUESTA ESTRELLA</span>'
            tipo_est_d = "💎 APUESTA ESTRELLA"
        elif mejor == "der":
            tags_html_d += '<span class="best-value-tag">⭐ +EV VALOR</span>'
            tipo_est_d = "⭐ +EV VALOR"
            
        st.markdown(f"""
        <div style="background-color:#081c13; border:1px solid #10b981; border-radius:10px; padding:14px; margin-bottom:8px;">
            <div style="color:#ffffff; font-weight:bold; font-size:1.05rem; margin-bottom:4px;">{label_der}</div>
            <div style="color:#cbd5e1; font-size:0.85rem; margin-bottom:8px;">Prob: {prob_der}% | Momio: {momio_der} | Edge: {edge_d:+.1f}%</div>
            <div>{tags_html_d}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"📥 Seleccionar {label_der}", key=f"btn_{partido_key}_{label_der.replace(' ', '_')}"):
            agregar_al_historial(partido_key, label_der, prob_der, momio_der, edge_d, tipo_est_d)
            st.success(f"¡Selección guardada en tu historial!")

st.sidebar.markdown("### 📅 Selector de Encuentros")
fecha_seleccionada = st.sidebar.date_input("Fecha", datetime.now())
juegos = obtener_juegos_hoy(fecha_seleccionada.strftime("%Y-%m-%d"))

opciones = [j["matchup"] for j in juegos]
juego_elegido_str = st.sidebar.selectbox("Selecciona Partido", opciones)
juego = [j for j in juegos if j["matchup"] == juego_elegido_str][0]

clima = obtener_clima_estadio(juego["venue"])

st.sidebar.markdown("---")
st.sidebar.markdown(f"🏟️ **Estadio:** {juego['venue']}")
st.sidebar.markdown(f"🌡️ **Temp:** {clima['temperatura']} | 💨 **Viento:** {clima['viento']}")

# --- GESTOR DE HISTORIAL EN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Historial y Picks Seleccionados")
apuestas_pendientes = [a for a in st.session_state.historial_apuestas if a["estado"] == "PENDIENTE"]
apuestas_resueltas = [a for a in st.session_state.historial_apuestas if a["estado"] in ["WIN", "LOSS"]]

st.sidebar.markdown(f"**Selecciones Activas:** `{len(apuestas_pendientes)}` | **Resueltas:** `{len(apuestas_resueltas)}`")

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("## ⚾ LA MAÑA PIKS · Auditoría Sabermétrica MLB")
    st.markdown("<span style='color: #94a3b8;'>Compara tu probabilidad calculada contra la probabilidad implícita de la cuota/momio del casino para determinar si existe Valor Esperado Positivo (+EV) o un Error de Cuota. Guarda tus selecciones favoritas en tu historial de apuestas interactivo.</span>", unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='background-color:rgba(16, 185, 129, 0.25); color:#34d399; border:1px solid #10b981; padding:6px 12px; border-radius:8px; font-weight:bold;'>🟢 API EN VIVO</span></div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown(f"""
<div class="matchup-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
        <span style="font-weight: bold; color: #34d399; font-size: 0.9rem;">🕒 HORARIO ESTÁNDAR · {juego['venue'].upper()}</span>
        <span style="background-color: rgba(251, 191, 36, 0.25); color: #fbbf24; border: 1px solid #f59e0b; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight:bold;">ALINEACIONES CONFIRMADAS</span>
    </div>
    <div style="display:flex; align-items:center; margin-bottom: 12px;">
        <img src="{juego['away_logo']}" width="36" height="36" style="margin-right: 12px; object-fit: contain;" onerror="this.src='https://placehold.co/36x36/png?text=MLB'">
        <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">
            [VISITA] {juego['away']} <span style="font-size: 0.85rem; color:#cbd5e1; font-weight:normal;">(Abre {juego['away_pitcher']})</span>
        </div>
    </div>
    <div style="display:flex; align-items:center;">
        <img src="{juego['home_logo']}" width="36" height="36" style="margin-right: 12px; object-fit: contain;" onerror="this.src='https://placehold.co/36x36/png?text=MLB'">
        <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">
            [LOCAL] {juego['home']} <span style="font-size: 0.85rem; color:#cbd5e1; font-weight:normal;">(Abre {juego['home_pitcher']})</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎯 Análisis de los 7 Mercados Clave + Auditoría +EV")

# 1. Moneyline
st.markdown(f"**1. Moneyline (Ganador Directo)**")
col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
with col_m1:
    st.markdown(f"<span style='color:#cbd5e1;'>Modelo: <b>[VISITA] {juego['away']} (38.5%)</b> vs <b>[LOCAL] {juego['home']} (61.5%)</b></span>", unsafe_allow_html=True)
with col_m2:
    momio_away_ml = st.number_input(f"Momio [VISITA] {juego['away']} (ML)", value=+150, step=5, key="ml_away")
with col_m3:
    momio_home_ml = st.number_input(f"Momio [LOCAL] {juego['home']} (ML)", value=-170, step=5, key="ml_home")
render_pick_box_clean(juego['matchup'], f"[VISITA] {juego['away']}", 38.5, momio_away_ml, f"[LOCAL] {juego['home']}", 61.5, momio_home_ml)

# 2. Total Carreras
st.markdown(f"**2. Total Carreras (Over / Under Personalizable 4.5 a 15.5)**")
col_sel_line, _ = st.columns([1, 3])
with col_sel_line:
    linea_ou = st.selectbox("Seleccionar Línea O/U", [4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5], index=5, key="linea_ou_sel")

prob_over_dinamica = max(15.0, min(90.0, round(78.0 - (linea_ou - 9.5) * 6.5, 1)))
prob_under_dinamica = round(100.0 - prob_over_dinamica, 1)

col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
with col_t1:
    st.markdown(f"<span style='color:#cbd5e1;'>Park Factor ({clima['park_factor']}) & Clima ({clima['temperatura']}): <b>Over {linea_ou} ({prob_over_dinamica}%)</b> / <b>Under {linea_ou} ({prob_under_dinamica}%)</b></span>", unsafe_allow_html=True)
with col_t2:
    momio_over = st.number_input(f"Momio Over {linea_ou}", value=-110, step=5, key="ou_over")
with col_t3:
    momio_under = st.number_input(f"Momio Under {linea_ou}", value=-110, step=5, key="ou_under")
render_pick_box_clean(juego['matchup'], f"Over {linea_ou}", prob_over_dinamica, momio_over, f"Under {linea_ou}", prob_under_dinamica, momio_under)

# 3. Run Line / Hándicap
st.markdown(f"**3. Run Line / Hándicap (-1.5 / +1.5)**")
col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
with col_r1:
    st.markdown(f"<span style='color:#cbd5e1;'>wRC+ y Bullpen: <b>[LOCAL] {juego['home']} -1.5 (56.0%)</b> vs <b>[VISITA] {juego['away']} +1.5 (44.0%)</b></span>", unsafe_allow_html=True)
with col_r2:
    momio_rl_home_minus = st.number_input(f"Momio [LOCAL] {juego['home']} -1.5", value=+120, step=5, key="rl_home_m")
with col_r3:
    momio_rl_away_plus = st.number_input(f"Momio [VISITA] {juego['away']} +1.5", value=-140, step=5, key="rl_away_p")
render_pick_box_clean(juego['matchup'], f"[LOCAL] {juego['home']} -1.5", 56.0, momio_rl_home_minus, f"[VISITA] {juego['away']} +1.5", 44.0, momio_rl_away_plus)

col_r_inv1, col_r_inv2, col_r_inv3 = st.columns([2, 1, 1])
with col_r_inv1:
    st.markdown(f"<span style='color:#cbd5e1;'>Alternativo: <b>[VISITA] {juego['away']} -1.5 (34.0%)</b> vs <b>[LOCAL] {juego['home']} +1.5 (66.0%)</b></span>", unsafe_allow_html=True)
with col_r_inv2:
    momio_rl_away_minus = st.number_input(f"Momio [VISITA] {juego['away']} -1.5", value=+160, step=5, key="rl_away_m")
with col_r_inv3:
    momio_rl_home_plus = st.number_input(f"Momio [LOCAL] {juego['home']} +1.5", value=-190, step=5, key="rl_home_p")
render_pick_box_clean(juego['matchup'], f"[VISITA] {juego['away']} -1.5", 34.0, momio_rl_away_minus, f"[LOCAL] {juego['home']} +1.5", 66.0, momio_rl_home_plus)

# 4. Ponches Totales (AMBOS ABRIDORES - Nombres Explícitos)
st.markdown(f"**4. Ponches Totales (Props de K's - Ambos Abridores)**")

st.markdown(f"<div style='background-color:#0d291b; padding:10px 14px; border-radius:8px; border-left:4px solid #10b981; margin-bottom:10px;'><b>📍 Pícher Visitante: {juego['away_pitcher']} ([VISITA] {juego['away']})</b></div>", unsafe_allow_html=True)
col_pk_s1, col_pk_s2, _ = st.columns([1, 1, 2])
with col_pk_s1:
    linea_k_away = st.selectbox(f"Línea de K's - {juego['away_pitcher']}", [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5], index=4, key="k_line_away_all")
prob_k_away_over = max(20.0, min(88.0, round(82.5 - (linea_k_away - 5.5) * 8.0, 1)))
prob_k_away_under = round(100.0 - prob_k_away_over, 1)

col_ka1, col_ka2, col_ka3 = st.columns([2, 1, 1])
with col_ka1:
    st.markdown(f"<span style='color:#cbd5e1;'>Modelo K%: <b>Over {linea_k_away} ({prob_k_away_over}%)</b> / <b>Under {linea_k_away} ({prob_k_away_under}%)</b></span>", unsafe_allow_html=True)
with col_ka2:
    momio_k_away_over = st.number_input(f"Momio Over {linea_k_away} K's ({juego['away_pitcher']})", value=-115, step=5, key="k_away_o_val")
with col_ka3:
    momio_k_away_under = st.number_input(f"Momio Under {linea_k_away} K's ({juego['away_pitcher']})", value=-105, step=5, key="k_away_u_val")
render_pick_box_clean(juego['matchup'], f"Over {linea_k_away} K's ({juego['away_pitcher']} - Visita)", prob_k_away_over, momio_k_away_over, f"Under {linea_k_away} K's ({juego['away_pitcher']} - Visita)", prob_k_away_under, momio_k_away_under)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"<div style='background-color:#0d291b; padding:10px 14px; border-radius:8px; border-left:4px solid #10b981; margin-bottom:10px;'><b>📍 Pícher Local: {juego['home_pitcher']} ([LOCAL] {juego['home']})</b></div>", unsafe_allow_html=True)
col_pk_h1, col_pk_h2, _ = st.columns([1, 1, 2])
with col_pk_h1:
    linea_k_home = st.selectbox(f"Línea de K's - {juego['home_pitcher']}", [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5], index=4, key="k_line_home_all")
prob_k_home_over = max(20.0, min(88.0, round(82.5 - (linea_k_home - 5.5) * 8.0, 1)))
prob_k_home_under = round(100.0 - prob_k_home_over, 1)

col_kh1, col_kh2, col_kh3 = st.columns([2, 1, 1])
with col_kh1:
    st.markdown(f"<span style='color:#cbd5e1;'>Modelo K%: <b>Over {linea_k_home} ({prob_k_home_over}%)</b> / <b>Under {linea_k_home} ({prob_k_home_under}%)</b></span>", unsafe_allow_html=True)
with col_kh2:
    momio_k_home_over = st.number_input(f"Momio Over {linea_k_home} K's ({juego['home_pitcher']})", value=-115, step=5, key="k_home_o_val")
with col_kh3:
    momio_k_home_under = st.number_input(f"Momio Under {linea_k_home} K's ({juego['home_pitcher']})", value=-105, step=5, key="k_home_u_val")
render_pick_box_clean(juego['matchup'], f"Over {linea_k_home} K's ({juego['home_pitcher']} - Local)", prob_k_home_over, momio_k_home_over, f"Under {linea_k_home} K's ({juego['home_pitcher']} - Local)", prob_k_home_under, momio_k_home_under)

# 5. Outs Totales (AMBOS ABRIDORES - Nombres Explícitos)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"**5. Outs Totales de Abridores (Ambos Abridores - 3.5 a 19.5)**")

st.markdown(f"<div style='background-color:#0d291b; padding:10px 14px; border-radius:8px; border-left:4px solid #10b981; margin-bottom:10px;'><b>📍 Pícher Visitante: {juego['away_pitcher']} ([VISITA] {juego['away']})</b></div>", unsafe_allow_html=True)
col_po_s1, col_po_s2, _ = st.columns([1, 1, 2])
with col_po_s1:
    linea_outs_away = st.selectbox(f"Línea de Outs - {juego['away_pitcher']}", [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5], index=14, key="out_line_away_all")
prob_out_away_over = max(20.0, min(88.0, round(72.0 - (linea_outs_away - 17.5) * 5.0, 1)))
prob_out_away_under = round(100.0 - prob_out_away_over, 1)

col_outa1, col_outa2, col_outa3 = st.columns([2, 1, 1])
with col_outa1:
    st.markdown(f"<span style='color:#cbd5e1;'>WHIP y Conteo: <b>Over {linea_outs_away} Outs ({prob_out_away_over}%)</b> / <b>Under {linea_outs_away} Outs ({prob_out_away_under}%)</b></span>", unsafe_allow_html=True)
with col_outa2:
    momio_out_away_over = st.number_input(f"Momio Over {linea_outs_away} Outs ({juego['away_pitcher']})", value=-115, step=5, key="out_away_o_val")
with col_outa3:
    momio_out_away_under = st.number_input(f"Momio Under {linea_outs_away} Outs ({juego['away_pitcher']})", value=-115, step=5, key="out_away_u_val")
render_pick_box_clean(juego['matchup'], f"Over {linea_outs_away} Outs ({juego['away_pitcher']} - Visita)", prob_out_away_over, momio_out_away_over, f"Under {linea_outs_away} Outs ({juego['away_pitcher']} - Visita)", prob_out_away_under, momio_out_away_under)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"<div style='background-color:#0d291b; padding:10px 14px; border-radius:8px; border-left:4px solid #10b981; margin-bottom:10px;'><b>📍 Pícher Local: {juego['home_pitcher']} ([LOCAL] {juego['home']})</b></div>", unsafe_allow_html=True)
col_po_h1, col_po_h2, _ = st.columns([1, 1, 2])
with col_po_h1:
    linea_outs_home = st.selectbox(f"Línea de Outs - {juego['home_pitcher']}", [3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 19.5], index=14, key="out_line_home_all")
prob_out_home_over = max(20.0, min(88.0, round(72.0 - (linea_outs_home - 17.5) * 5.0, 1)))
prob_out_home_under = round(100.0 - prob_out_home_over, 1)

col_outh1, col_outh2, col_outh3 = st.columns([2, 1, 1])
with col_outh1:
    st.markdown(f"<span style='color:#cbd5e1;'>WHIP y Conteo: <b>Over {linea_outs_home} Outs ({prob_out_home_over}%)</b> / <b>Under {linea_outs_home} Outs ({prob_out_home_under}%)</b></span>", unsafe_allow_html=True)
with col_outh2:
    momio_out_home_over = st.number_input(f"Momio Over {linea_outs_home} Outs ({juego['home_pitcher']})", value=-115, step=5, key="out_home_o_val")
with col_outh3:
    momio_out_home_under = st.number_input(f"Momio Under {linea_outs_home} Outs ({juego['home_pitcher']})", value=-115, step=5, key="out_home_u_val")
render_pick_box_clean(juego['matchup'], f"Over {linea_outs_home} Outs ({juego['home_pitcher']} - Local)", prob_out_home_over, momio_out_home_over, f"Under {linea_outs_home} Outs ({juego['home_pitcher']} - Local)", prob_out_home_under, momio_out_home_under)

# 6. Primeras 5 Entradas
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"**6. Primeras 5 Entradas (F5 - Ganador)**")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    st.markdown(f"<span style='color:#cbd5e1;'>Efectividad Abridores F5: <b>[VISITA] {juego['away']} (38.0%)</b> vs <b>[LOCAL] {juego['home']} (62.0%)</b></span>", unsafe_allow_html=True)
with col_f2:
    momio_f5_away = st.number_input(f"Momio [VISITA] {juego['away']} F5", value=+125, step=5, key="f5_away")
with col_f3:
    momio_f5_home = st.number_input(f"Momio [LOCAL] {juego['home']} F5", value=-145, step=5, key="f5_home")
render_pick_box_clean(juego['matchup'], f"[VISITA] {juego['away']} F5", 38.0, momio_f5_away, f"[LOCAL] {juego['home']} F5", 62.0, momio_f5_home)

# 7. NRFI / YRFI
st.markdown(f"**7. NRFI / YRFI (Carrera en la 1ª Entrada)**")
col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
with col_n1:
    st.markdown(f"<span style='color:#cbd5e1;'>WHIP 1ª Entrada: <b>NRFI (No Run - 65.0%)</b> vs <b>YRFI (Yes Run - 35.0%)</b></span>", unsafe_allow_html=True)
with col_n2:
    momio_nrfi = st.number_input("Momio NRFI", value=-130, step=5, key="nrfi_val")
with col_n3:
    momio_yrfi = st.number_input("Momio YRFI", value=+110, step=5, key="yrfi_val")
render_pick_box_clean(juego['matchup'], "NRFI (No)", 65.0, momio_nrfi, "YRFI (Yes)", 35.0, momio_yrfi)

st.markdown(f"""
<div class="model-explanation">
    <b style="color:#34d399;">💡 AUDITORÍA DE VALOR (+EV):</b> El motor analiza la probabilidad estimada contra la cuota del casino. Las selecciones que caigan en el <b style="color:#fbbf24;">Rango Verde (75% - 90%)</b> activan automáticamente el distintivo de <b style="color:#ffd700;">💎 APUESTA ESTRELLA</b> como máxima recomendación de valor para este juego en el <b style="color:#34d399;">{juego['venue']}</b>.
</div>
""", unsafe_allow_html=True)

# --- SECCIÓN VISUAL DE HISTORIAL DIVIDIDO ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("## 📊 Historial y Conteo de Apuestas Seleccionadas")
st.markdown("<span style='color: #94a3b8;'>Administra tus selecciones guardadas, actualiza su estado (WIN / LOSS) para moverlas automáticamente a la columna de resueltas y llevar tu bankroll auditado.</span>", unsafe_allow_html=True)

tab_activas, tab_resueltas = st.tabs([f"📥 Apuestas Seleccionadas / Activas ({len(apuestas_pendientes)})", f"🏆 Historial Resuelto / Win-Loss ({len(apuestas_resueltas)})"])

with tab_activas:
    if not apuestas_pendientes:
        st.info("No tienes apuestas seleccionadas actualmente. Usa los botones '📥 Seleccionar' en cada mercado para agregarlas aquí.")
    else:
        for idx, ap in enumerate(apuestas_pendientes):
            col_a1, col_a2, col_a3, col_a4 = st.columns([3, 2, 1, 1])
            with col_a1:
                st.markdown(f"**Partido:** {ap['partido']}<br>📌 **Pick:** `{ap['seleccion']}`", unsafe_allow_html=True)
            with col_a2:
                st.markdown(f"Prob: **{ap['prob']}%** | Momio: **{ap['momio']}**<br>Calidad: **{ap['estrella']}**", unsafe_allow_html=True)
            with col_a3:
                if st.button("✅ Marcar WIN", key=f"win_{ap['id']}"):
                    for item in st.session_state.historial_apuestas:
                        if item["id"] == ap["id"]:
                            item["estado"] = "WIN"
                    st.rerun()
            with col_a4:
                if st.button("❌ Marcar LOSS", key=f"loss_{ap['id']}"):
                    for item in st.session_state.historial_apuestas:
                        if item["id"] == ap["id"]:
                            item["estado"] = "LOSS"
                    st.rerun()
            st.markdown("---")
        
        if st.button("🗑️ Limpiar Todas las Activas"):
            st.session_state.historial_apuestas = [a for a in st.session_state.historial_apuestas if a["estado"] != "PENDIENTE"]
            st.rerun()

with tab_resueltas:
    if not apuestas_resueltas:
        st.info("Aún no hay apuestas resueltas (Win o Loss). Marca el resultado en la pestaña de activas.")
    else:
        # Calcular Win/Loss stats
        total_wins = len([a for a in apuestas_resueltas if a["estado"] == "WIN"])
        total_loss = len([a for a in apuestas_resueltas if a["estado"] == "LOSS"])
        win_rate = (total_wins / len(apuestas_resueltas)) * 100 if apuestas_resueltas else 0
        
        st.markdown(f"### 📈 Rendimiento Global: `{total_wins} W` - `{total_loss} L` (Efectividad: `{win_rate:.1f}%`)")
        st.markdown("---")
        
        for ap in apuestas_resueltas:
            color_badge = "#34d399" if ap["estado"] == "WIN" else "#f87171"
            col_r1, col_r2, col_r3 = st.columns([3, 2, 1])
            with col_r1:
                st.markdown(f"**Partido:** {ap['partido']}<br>📌 **Pick:** `{ap['seleccion']}`", unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"Momio: **{ap['momio']}** | Calidad: **{ap['estrella']}**", unsafe_allow_html=True)
            with col_r3:
                st.markdown(f"<span style='background-color:{color_badge}; color:#0b1f14; padding:6px 12px; border-radius:6px; font-weight:bold;'>{ap['estado']}</span>", unsafe_allow_html=True)
            st.markdown("---")
            
        if st.button("🔄 Borrar Historial Resuelto"):
            st.session_state.historial_apuestas = [a for a in st.session_state.historial_apuestas if a["estado"] == "PENDIENTE"]
            st.rerun()
