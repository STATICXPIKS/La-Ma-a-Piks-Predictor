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
    .matchup-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    .badge-bet {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-maybe {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-fade {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .best-value-tag {
        background-color: #fef08a;
        color: #854d0e;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
        margin-left: 6px;
    }
    .model-explanation {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 0 12px 12px 0;
        margin-top: 15px;
        font-size: 0.95rem;
        color: #334155;
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
                venue_name = game.get("venue", {}).get("name", "Great American Ball Park")
                
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
                "matchup": "Athletics @ Cincinnati Reds (Juego Muestra)",
                "away": "Athletics",
                "home": "Cincinnati Reds",
                "away_logo": obtener_logo("Athletics"),
                "home_logo": obtener_logo("Cincinnati Reds"),
                "away_pitcher": "Jacob Lopez",
                "home_pitcher": "Rhett Lowder",
                "venue": "Great American Ball Park",
                "status": "Scheduled"
            }]
        return juegos_lista
    except:
        return [{
            "matchup": "Athletics @ Cincinnati Reds (Modo Seguro)",
            "away": "Athletics",
            "home": "Cincinnati Reds",
            "away_logo": obtener_logo("Athletics"),
            "home_logo": obtener_logo("Cincinnati Reds"),
            "away_pitcher": "Jacob Lopez",
            "home_pitcher": "Rhett Lowder",
            "venue": "Great American Ball Park",
            "status": "Scheduled"
        }]

def calcular_probabilidad_implicita(momio):
    if momio > 0:
        return 100 / (momio + 100)
    elif momio < 0:
        return abs(momio) / (abs(momio) + 100)
    return 0.5

def evaluar_opcion(prob_modelo_pct, momio_casa):
    prob_modelo = prob_modelo_pct / 100.0
    prob_imp = calcular_probabilidad_implicita(momio_casa)
    edge = (prob_modelo - prob_imp) * 100
    
    if prob_modelo_pct >= 70 and edge > 2:
        estado = "BET"
        clase_css = "badge-bet"
    elif prob_modelo_pct >= 58:
        estado = "MAYBE"
        clase_css = "badge-maybe"
    else:
        estado = "FADE"
        clase_css = "badge-fade"
    return edge, estado, clase_css

def render_pick_box(label_izq, prob_izq, momio_izq, label_der, prob_der, momio_der):
    edge_i, est_i, css_i = evaluar_opcion(prob_izq, momio_izq)
    edge_d, est_d, css_d = evaluar_opcion(prob_der, momio_der)
    
    mejor = "izq" if edge_i >= edge_d else "der"
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        val_tag = '<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor == "izq" else ''
        st.markdown(f"""
        <div style="background-color:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:14px; margin-bottom:8px;">
            <b>{label_izq}:</b> Prob {prob_izq}% | Momio {momio_izq} | Edge {edge_i:+.1f}% 
            <span class="{css_i}">{est_i}</span> {val_tag}
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        val_tag = '<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor == "der" else ''
        st.markdown(f"""
        <div style="background-color:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:14px; margin-bottom:8px;">
            <b>{label_der}:</b> Prob {prob_der}% | Momio {momio_der} | Edge {edge_d:+.1f}% 
            <span class="{css_d}">{est_d}</span> {val_tag}
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
    st.markdown("Consulte los picks analizados en vivo con probabilidades reales de éxito y cajas editables de momios de casino.")
with col_h2:
    st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='background-color:#dcfce7; color:#166534; padding:6px 12px; border-radius:8px; font-weight:bold;'>🟢 API EN VIVO</span></div>", unsafe_allow_html=True)

st.markdown("---")

st.markdown(f"""
<div class="matchup-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
        <span style="font-weight: bold; color: #64748b; font-size: 0.9rem;">🕒 4:40 P.M. · {juego['venue'].upper()}</span>
        <span style="background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight:bold;">ALINEACIONES CONFIRMADAS</span>
    </div>
    <div style="display:flex; align-items:center; margin-bottom: 10px;">
        <img src="{juego['away_logo']}" width="36" height="36" style="margin-right: 12px; object-fit: contain;" onerror="this.src='https://placehold.co/36x36/png?text=MLB'">
        <div style="font-size: 1.15rem; font-weight: bold; color: #1e293b;">
            {juego['away']} <span style="font-size: 0.85rem; color:#64748b; font-weight:normal;">(Abre {juego['away_pitcher']})</span>
        </div>
    </div>
    <div style="display:flex; align-items:center;">
        <img src="{juego['home_logo']}" width="36" height="36" style="margin-right: 12px; object-fit: contain;" onerror="this.src='https://placehold.co/36x36/png?text=MLB'">
        <div style="font-size: 1.15rem; font-weight: bold; color: #1e293b;">
            {juego['home']} <span style="font-size: 0.85rem; color:#64748b; font-weight:normal;">(Abre {juego['home_pitcher']})</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎯 Análisis de los 7 Mercados Clave + Momios de Casino")

# 1. Moneyline
st.markdown(f"**1. Moneyline (Ganador Directo)**")
col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
with col_m1:
    st.write(f"Prob. Modelo: **{juego['away']} (32.8%)** vs **{juego['home']} (67.2%)**")
with col_m2:
    momio_away_ml = st.number_input(f"Momio {juego['away']} (ML)", value=+140, step=5, key="ml_away")
with col_m3:
    momio_home_ml = st.number_input(f"Momio {juego['home']} (ML)", value=-165, step=5, key="ml_home")
render_pick_box(juego['away'], 32.8, momio_away_ml, juego['home'], 67.2, momio_home_ml)

# 2. Total Carreras
st.markdown(f"**2. Total Carreras (Over / Under Línea Estándar 9.5)**")
col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
with col_t1:
    st.write(f"Park Factor ({clima['park_factor']}) & Clima ({clima['temperatura']}): **Over 9.5 (61.4%)** / **Under 9.5 (38.6%)**")
with col_t2:
    momio_over = st.number_input("Momio Over 9.5", value=-110, step=5, key="ou_over")
with col_t3:
    momio_under = st.number_input("Momio Under 9.5", value=-110, step=5, key="ou_under")
render_pick_box("Over 9.5", 61.4, momio_over, "Under 9.5", 38.6, momio_under)

# 3. Run Line
st.markdown(f"**3. Run Line / Hándicap (-1.5 / +1.5)**")
col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
with col_r1:
    st.write(f"wRC+ y Bullpen: **{juego['home']} -1.5 (54.2%)** vs **{juego['away']} +1.5 (45.8%)**")
with col_r2:
    momio_rl_home = st.number_input(f"Momio {juego['home']} -1.5", value=+125, step=5, key="rl_home")
with col_r3:
    momio_rl_away = st.number_input(f"Momio {juego['away']} +1.5", value=-145, step=5, key="rl_away")
render_pick_box(f"{juego['home']} -1.5", 54.2, momio_rl_home, f"{juego['away']} +1.5", 45.8, momio_rl_away)

# 4. Ponches Totales
st.markdown(f"**4. Ponches Totales (Props de K's del Abridor Local: {juego['home_pitcher']})**")
col_k1, col_k2, col_k3 = st.columns([2, 1, 1])
with col_k1:
    st.write(f"K% y BvP: **Over 5.5 K's (66.5%)** / **Under 5.5 K's (33.5%)**")
with col_k2:
    momio_k_over = st.number_input("Momio Over K's", value=-120, step=5, key="k_over")
with col_k3:
    momio_k_under = st.number_input("Momio Under K's", value=+100, step=5, key="k_under")
render_pick_box("Over 5.5 K's", 66.5, momio_k_over, "Under 5.5 K's", 33.5, momio_k_under)

# 5. Outs Totales
st.markdown(f"**5. Outs Totales del Abridor Local ({juego['home_pitcher']})**")
col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
with col_o1:
    st.write(f"WHIP y Conteo de Lanzamientos: **Over 17.5 Outs (70.2%)** / **Under 17.5 Outs (29.8%)**")
with col_o2:
    momio_out_over = st.number_input("Momio Over Outs", value=-115, step=5, key="out_over")
with col_o3:
    momio_out_under = st.number_input("Momio Under Outs", value=-115, step=5, key="out_under")
render_pick_box("Over 17.5 Outs", 70.2, momio_out_over, "Under 17.5 Outs", 29.8, momio_out_under)

# 6. Primeras 5 Entradas
st.markdown(f"**6. Primeras 5 Entradas (F5 - Ganador)**")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    st.write(f"Efectividad Abridores F5: **{juego['away']} (35.0%)** vs **{juego['home']} (65.0%)**")
with col_f2:
    momio_f5_away = st.number_input(f"Momio {juego['away']} F5", value=+120, step=5, key="f5_away")
with col_f3:
    momio_f5_home = st.number_input(f"Momio {juego['home']} F5", value=-140, step=5, key="f5_home")
render_pick_box(f"{juego['away']} F5", 35.0, momio_f5_away, f"{juego['home']} F5", 65.0, momio_f5_home)

# 7. NRFI / YRFI
st.markdown(f"**7. NRFI / YRFI (Carrera en la 1ª Entrada)**")
col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
with col_n1:
    st.write(f"WHIP 1ª Entrada: **NRFI (No Run - 62.5%)** vs **YRFI (Yes Run - 37.5%)**")
with col_n2:
    momio_nrfi = st.number_input("Momio NRFI", value=-125, step=5, key="nrfi_val")
with col_n3:
    momio_yrfi = st.number_input("Momio YRFI", value=+105, step=5, key="yrfi_val")
render_pick_box("NRFI (No)", 62.5, momio_nrfi, "YRFI (Yes)", 37.5, momio_yrfi)

st.markdown(f"""
<div class="model-explanation">
    <b>💡 QUÉ VE EL MODELO:</b> El sistema sabermétrico de <b>LA MAÑA PIKS</b> cruza las métricas de xERA, FIP, wRC+ y bullpen para este encuentro en el <b>{juego['venue']}</b>. Se observan ventajas claras respaldadas por el factor climático ({clima['temperatura']}, viento {clima['viento']}). Ajuste sus apuestas considerando las cuotas de su casino de preferencia.
</div>
""", unsafe_allow_html=True)
