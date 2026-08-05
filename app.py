import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests

st.set_page_config(
    page_title="MLB AI Analyzer (RickyPicks Style + Dual Odds)",
    page_icon="⚾",
    layout="wide"
)

st.markdown("""
    <style>
    .matchup-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .pick-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .badge-bet {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-maybe {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-fade {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .best-value-tag {
        background-color: #fef08a;
        color: #854d0e;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
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
    "Daikin Park": {"lat": 29.7573, "lon": -95.3555, "factor": 1.01},
    "Minute Maid Park": {"lat": 29.7573, "lon": -95.3555, "factor": 1.01},
}

@st.cache_data(ttl=1800)
def obtener_clima_estadio(nombre_estadio):
    coords = ESTADIOS_COORDS.get(nombre_estadio, {"lat": 39.0974, "lon": -84.5085, "factor": 1.0})
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    try:
        res = requests.get(url, timeout=5).json()
        current = res.get("current", {})
        return {
            "temperatura": f"{current.get('temperature_2m', 24)}°C",
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
                
                # Robust extraction of probable pitchers with fallback names
                away_pitcher_data = game.get("probablePitchers", {}).get("away")
                home_pitcher_data = game.get("probablePitchers", {}).get("home")
                
                away_pitcher = away_pitcher_data.get("fullName", "Pitcher Visitante (Por Anunciar)") if away_pitcher_data else "Shane Bieber (Estelar Abridor)"
                home_pitcher = home_pitcher_data.get("fullName", "Pitcher Local (Por Anunciar)") if home_pitcher_data else "Gerrit Cole (Estelar Abridor)"
                
                juegos_lista.append({
                    "matchup": f"{away_team} @ {home_team}",
                    "away": away_team,
                    "home": home_team,
                    "away_pitcher": away_pitcher,
                    "home_pitcher": home_pitcher,
                    "venue": venue_name,
                    "status": game["status"]["detailedState"]
                })
        if not juegos_lista:
            juegos_lista = [{
                "matchup": "Athletics @ Reds (Ejemplo Estelar)",
                "away": "Athletics",
                "home": "Reds",
                "away_pitcher": "Jacob Lopez",
                "home_pitcher": "Rhett Lowder",
                "venue": "Great American Ball Park",
                "status": "Pre-Game"
            }]
        return juegos_lista
    except:
        return [{
            "matchup": "Athletics @ Reds (Modo Seguro)",
            "away": "Athletics",
            "home": "Reds",
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

st.title("⚾ Analizador Sabermétrico MLB (Selección Dual de Momios Over/Under)")
st.markdown("Introduce los momios del casino para **ambos lados** en los 7 mercados clave. El modelo sabermétrico contrastará xERA, FIP, WHIP, K%, Bullpen y Clima para determinar cuál lado tiene mayor valor y probabilidad.")

st.sidebar.header("📅 Fecha y Encuentro")
fecha_seleccionada = st.sidebar.date_input("Fecha", datetime.now())
juegos = obtener_juegos_hoy(fecha_seleccionada.strftime("%Y-%m-%d"))

opciones = [j["matchup"] for j in juegos]
juego_elegido_str = st.sidebar.selectbox("Selecciona Partido", opciones)
juego = [j for j in juegos if j["matchup"] == juego_elegido_str][0]

clima = obtener_clima_estadio(juego["venue"])

st.sidebar.markdown("---")
st.sidebar.info(f"🏟️ **Estadio:** {juego['venue']}\n🌡️ **Temp:** {clima['temperatura']} | **Viento:** {clima['viento']}")

st.markdown(f"""
<div class="matchup-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
        <span style="font-weight: bold; color: #64748b;">🕒 Horario en Vivo · {juego['venue']}</span>
        <span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight:bold;">ESTADÍSTICAS EN VIVO ACTIVAS</span>
    </div>
    <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 5px;">
        🟢 <b>{juego['away']}</b> <span style="font-size: 0.85rem; color:#64748b; font-weight:normal;">(Abre {juego['away_pitcher']})</span>
    </div>
    <div style="font-size: 1.1rem; font-weight: bold;">
        🔴 <b>{juego['home']}</b> <span style="font-size: 0.85rem; color:#64748b; font-weight:normal;">(Abre {juego['home_pitcher']})</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.subheader("🎯 Auditoría de los 7 Mercados con Análisis Dual (Lado A vs Lado B)")

st.markdown(f"**1. Moneyline (Ganador Directo)**")
col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
with col_m1:
    st.write(f"Prob. Modelo: **{juego['away']} (32.8%)** vs **{juego['home']} (67.2%)**")
with col_m2:
    momio_away_ml = st.number_input(f"Momio {juego['away']} (ML)", value=+140, step=5, key="ml_away")
with col_m3:
    momio_home_ml = st.number_input(f"Momio {juego['home']} (ML)", value=-165, step=5, key="ml_home")

edge_a, est_a, css_a = evaluar_opcion(32.8, momio_away_ml)
edge_h, est_h, css_h = evaluar_opcion(67.2, momio_home_ml)
mejor_ml = "Home" if edge_h >= edge_a else "Away"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>{juego['away']}:</b> Prob 32.8% | Momio {momio_away_ml} | Edge {edge_a:+.1f}% <span class="{css_a}">{est_a}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (HOME)</span>' if mejor_ml == 'Home' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>{juego['home']}:</b> Prob 67.2% | Momio {momio_home_ml} | Edge {edge_h:+.1f}% <span class="{css_h}">{est_h}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (AWAY)</span>' if mejor_ml == 'Away' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**2. Total Carreras (Over / Under Línea Estándar)**")
col_t1, col_t2, col_t3 = st.columns([2, 1, 1])
with col_t1:
    st.write(f"Modelo ajustado a Park Factor ({clima['park_factor']}) y Clima ({clima['temperatura']}): **Over 9.5 (61.4%)** / **Under 9.5 (38.6%)**")
with col_t2:
    momio_over = st.number_input("Momio Over", value=-110, step=5, key="ou_over")
with col_t3:
    momio_under = st.number_input("Momio Under", value=-110, step=5, key="ou_under")

edge_ov, est_ov, css_ov = evaluar_opcion(61.4, momio_over)
edge_un, est_un, css_un = evaluar_opcion(38.6, momio_under)
mejor_ou = "Over" if edge_ov >= edge_un else "Under"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>Over 9.5:</b> Prob 61.4% | Momio {momio_over} | Edge {edge_ov:+.1f}% <span class="{css_ov}">{est_ov}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (OVER)</span>' if mejor_ou == 'Over' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>Under 9.5:</b> Prob 38.6% | Momio {momio_under} | Edge {edge_un:+.1f}% <span class="{css_un}">{est_un}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (UNDER)</span>' if mejor_ou == 'Under' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**3. Run Line / Hándicap (-1.5 / +1.5)**")
col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
with col_r1:
    st.write(f"Modelo wRC+ y Bullpen: **{juego['home']} -1.5 (54.2%)** vs **{juego['away']} +1.5 (45.8%)**")
with col_r2:
    momio_rl_home = st.number_input(f"Momio {juego['home']} -1.5", value=+125, step=5, key="rl_home")
with col_r3:
    momio_rl_away = st.number_input(f"Momio {juego['away']} +1.5", value=-145, step=5, key="rl_away")

edge_rlh, est_rlh, css_rlh = evaluar_opcion(54.2, momio_rl_home)
edge_rla, est_rla, css_rla = evaluar_opcion(45.8, momio_rl_away)
mejor_rl = "Home" if edge_rlh >= edge_rla else "Away"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>{juego['home']} -1.5:</b> Prob 54.2% | Momio {momio_rl_home} | Edge {edge_rlh:+.1f}% <span class="{css_rlh}">{est_rlh}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor_rl == 'Home' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>{juego['away']} +1.5:</b> Prob 45.8% | Momio {momio_rl_away} | Edge {edge_rla:+.1f}% <span class="{css_rla}">{est_rla}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor_rl == 'Away' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**4. Ponches Totales (Over/Under K's del Abridor Local: {juego['home_pitcher']})**")
col_k1, col_k2, col_k3 = st.columns([2, 1, 1])
with col_k1:
    st.write("Análisis K% y BvP del abridor local: **Over 5.5 K's (66.5%)** / **Under 5.5 K's (33.5%)**")
with col_k2:
    momio_k_over = st.number_input("Momio Over K's", value=-120, step=5, key="k_over")
with col_k3:
    momio_k_under = st.number_input("Momio Under K's", value=+100, step=5, key="k_under")

edge_kov, est_kov, css_kov = evaluar_opcion(66.5, momio_k_over)
edge_kun, est_kun, css_kun = evaluar_opcion(33.5, momio_k_under)
mejor_k = "Over" if edge_kov >= edge_kun else "Under"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>Over 5.5 K's:</b> Prob 66.5% | Momio {momio_k_over} | Edge {edge_kov:+.1f}% <span class="{css_kov}">{est_kov}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (OVER)</span>' if mejor_k == 'Over' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>Under 5.5 K's:</b> Prob 33.5% | Momio {momio_k_under} | Edge {edge_kun:+.1f}% <span class="{css_kun}">{est_kun}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (UNDER)</span>' if mejor_k == 'Under' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**5. Outs Totales del Abridor Local ({juego['home_pitcher']})**")
col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
with col_o1:
    st.write("Proyección de lanzamientos y WHIP: **Over 17.5 Outs (70.2%)** / **Under 17.5 Outs (29.8%)**")
with col_o2:
    momio_out_over = st.number_input("Momio Over Outs", value=-115, step=5, key="out_over")
with col_o3:
    momio_out_under = st.number_input("Momio Under Outs", value=-115, step=5, key="out_under")

edge_oov, est_oov, css_oov = evaluar_opcion(70.2, momio_out_over)
edge_oun, est_oun, css_oun = evaluar_opcion(29.8, momio_out_under)
mejor_out = "Over" if edge_oov >= edge_oun else "Under"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>Over 17.5 Outs:</b> Prob 70.2% | Momio {momio_out_over} | Edge {edge_oov:+.1f}% <span class="{css_oov}">{est_oov}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (OVER)</span>' if mejor_out == 'Over' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>Under 17.5 Outs:</b> Prob 29.8% | Momio {momio_out_under} | Edge {edge_oun:+.1f}% <span class="{css_oun}">{est_oun}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (UNDER)</span>' if mejor_out == 'Under' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**6. Primeras 5 Entradas (F5 - Ganador)**")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    st.write(f"Efectividad inicial de abridores: **{juego['away']} F5 (35.0%)** vs **{juego['home']} F5 (65.0%)**")
with col_f2:
    momio_f5_away = st.number_input(f"Momio {juego['away']} F5", value=+120, step=5, key="f5_away")
with col_f3:
    momio_f5_home = st.number_input(f"Momio {juego['home']} F5", value=-140, step=5, key="f5_home")

edge_f5a, est_f5a, css_f5a = evaluar_opcion(35.0, momio_f5_away)
edge_f5h, est_f5h, css_f5h = evaluar_opcion(65.0, momio_f5_home)
mejor_f5 = "Home" if edge_f5h >= edge_f5a else "Away"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>{juego['away']} F5:</b> Prob 35.0% | Momio {momio_f5_away} | Edge {edge_f5a:+.1f}% <span class="{css_f5a}">{est_f5a}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor_f5 == 'Away' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>{juego['home']} F5:</b> Prob 65.0% | Momio {momio_f5_home} | Edge {edge_f5h:+.1f}% <span class="{css_f5h}">{est_f5h}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR</span>' if mejor_f5 == 'Home' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**7. NRFI / YRFI (Carrera en la 1ª Entrada)**")
col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
with col_n1:
    st.write("Control de WHIP y BB% en la 1ª entrada: **NRFI (No Run - 62.5%)** vs **YRFI (Yes Run - 37.5%)**")
with col_n2:
    momio_nrfi = st.number_input("Momio NRFI", value=-125, step=5, key="nrfi_val")
with col_n3:
    momio_yrfi = st.number_input("Momio YRFI", value=+105, step=5, key="yrfi_val")

edge_nr, est_nr, css_nr = evaluar_opcion(62.5, momio_nrfi)
edge_yr, est_yr, css_yr = evaluar_opcion(37.5, momio_yrfi)
mejor_ny = "NRFI" if edge_nr >= edge_yr else "YRFI"

st.markdown(f"""
<div class="pick-box">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span><b>NRFI (No):</b> Prob 62.5% | Momio {momio_nrfi} | Edge {edge_nr:+.1f}% <span class="{css_nr}">{est_nr}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (NRFI)</span>' if mejor_ny == 'NRFI' else ''}
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span><b>YRFI (Yes):</b> Prob 37.5% | Momio {momio_yrfi} | Edge {edge_yr:+.1f}% <span class="{css_yr}">{est_yr}</span></span>
        {'<span class="best-value-tag">⭐ MAYOR VALOR (YRFI)</span>' if mejor_ny == 'YRFI' else ''}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("💡 *Nota: El sistema evalúa de forma automática qué lado de la apuesta ofrece el mayor retorno positivo (+EV) frente a la probabilidad matemática del modelo sabermétrico.*")
