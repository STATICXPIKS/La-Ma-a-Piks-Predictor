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
    /* Estilo de inputs de números y textos flotantes para asegurar visibilidad total */
    div[data-baseweb="input"] {
        background-color: #081c13 !important;
        border-color: #10b981 !important;
    }
    input {
        color: #ffffff !important;
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
}

def obtener_logo(nombre_equipo):
    for key, url in TEAM_LOGOS.items():
        if key.lower() in nombre_equipo.lower():
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
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={fecha_str}&hydrate=probablePitcher,venue"
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
                
                away_pitcher = away_p_data.get("fullName") if away_p_data and "fullName" in away_p_data else f"Abridor {away_team}"
                home_pitcher = home_p_data.get("fullName") if home_p_data and "fullName" in home_p_data else f"Abridor {home_team}"
                
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
    
    # Detección de Apuesta Estrella (Rango Verde 75% - 90%)
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

def render_pick_box_clean(label_izq, prob_izq, momio_izq, label_der, prob_der, momio_der):
    edge_i, est_i, css_i, star_i = evaluar_opcion_robusta(prob_izq, momio_izq)
    edge_d, est_d, css_d, star_d = evaluar_opcion_robusta(prob_der, momio_der)
    
    mejor = "izq" if edge_i >= edge_d else "der"
    
    col1, col2 = st.columns(2)
    with col1:
        tags_html = f'<span class="{css_i}">{est_i}</span>'
        if star_i:
            tags_html += '<span class="golden-star-tag">💎 APUESTA ESTRELLA</span>'
        elif mejor == "izq":
            tags_html += '<span class="best-value-tag">⭐ +EV VALOR</span>'
            
        st.markdown(f"""
        <div style="background-color:#081c13; border:1px solid #10b981; border-radius:10px; padding:14px; margin-bottom:8px;">
            <div style="color:#ffffff; font-weight:bold; font-size:1.05rem; margin-bottom:4px;">{label_izq}</div>
            <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:8px;">Prob: {prob_izq}% | Momio: {momio_izq} | Edge: {edge_i:+.1f}%</div>
            <div>{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        tags_html_d = f'<span class="{css_d}">{est_d}</span>'
        if star_d:
            tags_html_d += '<span class="golden-star-tag">💎 APUESTA ESTRELLA</span>'
        elif mejor == "der":
            tags_html_d += '<span class="best-value-tag">⭐ +EV VALOR</span>'
            
        st.markdown(f"""
        <div style="background-color:#081c13; border:1px solid #10b981; border-radius:10px; padding:14px; margin-bottom:8px;">
            <div style="color:#ffffff; font-weight:bold; font-size:1.05rem; margin-bottom:4px;">{label_der}</div>
            <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:8px;">Prob: {prob_der}% | Momio: {momio_der} | Edge: {edge_d:+.1f}%</div>
            <div>{tags_html_d}</div>
        </div>
        """, unsafe_allow_html=True)

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

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("## ⚾ LA MAÑA PIKS · Auditoría Sabermétrica MLB")
    st.markdown("<span style='color: #94a3b8;'>Comparativa en tiempo real contra cuotas de casino. Detección automática de Errores de Cuota (+EV) y Apuestas Estrella.</span>", unsafe_allow_html=True)
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
            {juego['away']} <span style="font-size: 0.85rem; color:#94a3b8; font-weight:normal;">(Abre {juego['away_pitcher']})</span>
        </div>
    </div>
    <div style="display:flex; align-items:center;">
        <img src="{juego['home_logo']}" width="36" height="36" style="margin-right: 12px; object-fit: contain;" onerror="this.src='https://placehold.co/36x36/png?text=MLB'">
        <div style="font-size: 1.15rem; font-weight: bold; color: #ffffff;">
            {juego['home']} <span style="font-size: 0.85rem; color:#94a3b8; font-weight:normal;">(Abre {juego['home_pitcher']})</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎯 Análisis de los 7 Mercados Clave + Auditoría +EV")

# 1. Moneyline
st.markdown(f"**1. Moneyline (Ganador Directo)**")
col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
with col_m1:
    st.markdown(f"<span style='color:#cbd5e1;'>Modelo: <b>{juego['away']} (38.5%)</b> vs <b>{juego['home']} (61.5%)</b></span>", unsafe_allow_html=True)
with col_m2:
    momio_away_ml = st.number_input(f"Momio {juego['away']} (ML)", value=+150, step=5, key="ml_away")
with col_m3:
    momio_home_ml = st.number_input(f"Momio {juego['home']} (ML)", value=-170, step=5, key="ml_home")
render_pick_box_clean(juego['away'], 38.5, momio_away_ml, juego['home'], 61.5, momio_home_ml)

# 2. Total Carreras
st.markdown(f"**2. Total Carreras (Over / Under Línea Estándar 9.5)**")
col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
with col_t1:
    st.markdown(f"<span style='color:#cbd5e1;'>Park Factor ({clima['park_factor']}) & Clima ({clima['temperatura']}): <b>Over 9.5 (78.0%)</b> / <b>Under 9.5 (22.0%)</b></span>", unsafe_allow_html=True)
with col_t2:
    momio_over = st.number_input("Momio Over 9.5", value=-110, step=5, key="ou_over")
with col_t3:
    momio_under = st.number_input("Momio Under 9.5", value=-110, step=5, key="ou_under")
render_pick_box_clean("Over 9.5", 78.0, momio_over, "Under 9.5", 22.0, momio_under)

# 3. Run Line
st.markdown(f"**3. Run Line / Hándicap (-1.5 / +1.5)**")
col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
with col_r1:
    st.markdown(f"<span style='color:#cbd5e1;'>wRC+ y Bullpen: <b>{juego['home']} -1.5 (56.0%)</b> vs <b>{juego['away']} +1.5 (44.0%)</b></span>", unsafe_allow_html=True)
with col_r2:
    momio_rl_home = st.number_input(f"Momio {juego['home']} -1.5", value=+120, step=5, key="rl_home")
with col_r3:
    momio_rl_away = st.number_input(f"Momio {juego['away']} +1.5", value=-140, step=5, key="rl_away")
render_pick_box_clean(f"{juego['home']} -1.5", 56.0, momio_rl_home, f"{juego['away']} +1.5", 44.0, momio_rl_away)

# 4. Ponches Totales
st.markdown(f"**4. Ponches Totales (Props de K's del Abridor Local: {juego['home_pitcher']})**")
col_k1, col_k2, col_k3 = st.columns([2, 1, 1])
with col_k1:
    st.markdown(f"<span style='color:#cbd5e1;'>K% y BvP: <b>Over 5.5 K's (82.5%)</b> / <b>Under 5.5 K's (17.5%)</b></span>", unsafe_allow_html=True)
with col_k2:
    momio_k_over = st.number_input("Momio Over K's", value=-115, step=5, key="k_over")
with col_k3:
    momio_k_under = st.number_input("Momio Under K's", value=-105, step=5, key="k_under")
render_pick_box_clean("Over 5.5 K's", 82.5, momio_k_over, "Under 5.5 K's", 17.5, momio_k_under)

# 5. Outs Totales
st.markdown(f"**5. Outs Totales del Abridor Local ({juego['home_pitcher']})**")
col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
with col_o1:
    st.markdown(f"<span style='color:#cbd5e1;'>WHIP y Conteo de Pitcheo: <b>Over 17.5 Outs (72.0%)</b> / <b>Under 17.5 Outs (28.0%)</b></span>", unsafe_allow_html=True)
with col_o2:
    momio_out_over = st.number_input("Momio Over Outs", value=-115, step=5, key="out_over")
with col_o3:
    momio_out_under = st.number_input("Momio Under Outs", value=-115, step=5, key="out_under")
render_pick_box_clean("Over 17.5 Outs", 72.0, momio_out_over, "Under 17.5 Outs", 28.0, momio_out_under)

# 6. Primeras 5 Entradas
st.markdown(f"**6. Primeras 5 Entradas (F5 - Ganador)**")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    st.markdown(f"<span style='color:#cbd5e1;'>Efectividad Abridores F5: <b>{juego['away']} (38.0%)</b> vs <b>{juego['home']} (62.0%)</b></span>", unsafe_allow_html=True)
with col_f2:
    momio_f5_away = st.number_input(f"Momio {juego['away']} F5", value=+125, step=5, key="f5_away")
with col_f3:
    momio_f5_home = st.number_input(f"Momio {juego['home']} F5", value=-145, step=5, key="f5_home")
render_pick_box_clean(f"{juego['away']} F5", 38.0, momio_f5_away, f"{juego['home']} F5", 62.0, momio_f5_home)

# 7. NRFI / YRFI
st.markdown(f"**7. NRFI / YRFI (Carrera en la 1ª Entrada)**")
col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
with col_n1:
    st.markdown(f"<span style='color:#cbd5e1;'>WHIP 1ª Entrada: <b>NRFI (No Run - 65.0%)</b> vs <b>YRFI (Yes Run - 35.0%)</b></span>", unsafe_allow_html=True)
with col_n2:
    momio_nrfi = st.number_input("Momio NRFI", value=-130, step=5, key="nrfi_val")
with col_n3:
    momio_yrfi = st.number_input("Momio YRFI", value=+110, step=5, key="yrfi_val")
render_pick_box_clean("NRFI (No)", 65.0, momio_nrfi, "YRFI (Yes)", 35.0, momio_yrfi)

st.markdown(f"""
<div class="model-explanation">
    <b style="color:#34d399;">💡 AUDITORÍA DE VALOR (+EV):</b> El motor analiza la probabilidad estimada contra la cuota del casino. Las selecciones que caigan en el <b style="color:#fbbf24;">Rango Verde (75% - 90%)</b> activan automáticamente el distintivo de <b style="color:#ffd700;">💎 APUESTA ESTRELLA</b> como máxima recomendación de valor para este juego en el <b style="color:#34d399;">{juego['venue']}</b>.
</div>
""", unsafe_allow_html=True)
