import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import requests
import json
import os
from datetime import datetime

# Configuración de la página
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
        "linea": str(linea),
        "momio": momio,
        "ev": round(ev * 100, 1),
        "estado": "PENDING",
        "resultado_real": "En Espera"
    }
    historial.append(nueva_apuesta)
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast(f"✅ Pick guardado: {mercado}", icon="📌")

def eliminar_apuesta(id_apuesta):
    historial = cargar_base_datos()
    historial = [item for item in historial if item.get("id") != id_apuesta]
    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    st.toast("🗑️ Apuesta eliminada con éxito", icon="🗑️")
    st.rerun()

# ==========================================
# DICCIONARIOS DE EQUIPOS Y LIGAS
# ==========================================
PREMIER_DICT = {
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png", "Aston Villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png", "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png", "Manchester United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "Tottenham Hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png"
}

EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "whip": 1.18},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "whip": 1.12},
    "Boston Red Sox": {"id": 111, "wRC_plus": 105, "era_base": 4.10, "whip": 1.28},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "whip": 1.20}
}

# HEADER Y DASHBOARD PRINCIPAL
st.title("👑 LA MAÑA PICKS ANALYTICS PRO")
st.write("ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR • JUEGA CON ESTADÍSTICAS Y CON MAÑA")

historial = cargar_base_datos()
wins = sum(1 for x in historial if x.get("estado") == "WIN")
losses = sum(1 for x in historial if x.get("estado") == "LOSS")
pending = sum(1 for x in historial if x.get("estado") == "PENDING")
total = wins + losses
winrate = round((wins / total) * 100, 1) if total > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Efectividad Real", f"{winrate}%")
col2.metric("Wins ✅", wins)
col3.metric("Losses ❌", losses)
col4.metric("Pendientes ⏳", pending)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["⚽ Fútbol & Ambos Anotan (BTTS)", "⚾ MLB Sabermetría", "🏈 NFL Model", "📋 Tablero de Apuestas"])

# ⚽ SECCIÓN FÚTBOL CON AMBOS ANOTAN
with tab1:
    st.subheader("⚽ Análisis de Partido y Ambos Anotan (BTTS)")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        eq_loc = st.selectbox("Equipo Local", list(PREMIER_DICT.keys()), index=0)
        eq_vis = st.selectbox("Equipo Visitante", list(PREMIER_DICT.keys()), index=1)
        momio_loc = st.number_input(f"Momio/Cuota {eq_loc}", value=1.85)
        momio_vis = st.number_input(f"Momio/Cuota {eq_vis}", value=4.20)
        
        c_btts_si = st.number_input("Momio Ambos Anotan (BTTS): SÍ", value=1.80)
        c_btts_no = st.number_input("Momio Ambos Anotan (BTTS): NO", value=1.95)
        
    with col_f2:
        xg_loc, xg_vis = 1.75, 1.15
        p_no_loc, p_no_vis = np.exp(-xg_loc), np.exp(-xg_vis)
        prob_btts_si = int(round((1 - p_no_loc) * (1 - p_no_vis) * 100))
        prob_btts_no = 100 - prob_btts_si
        
        st.write(f"**Proyección xG:** {eq_loc} ({xg_loc}) vs ({xg_vis}) {eq_vis}")
        st.write(f"🔥 Probabilidad Ambos Anotan SÍ: **{prob_btts_si}%**")
        st.write(f"🛡️ Probabilidad Ambos Anotan NO: **{prob_btts_no}%**")
        
        if st.button("Guardar Pick BTTS SÍ 💾"):
            registrar_apuesta("Fútbol", f"{eq_loc} vs {eq_vis}", eq_loc, eq_vis, "Ambos Anotan: SÍ", 0.5, c_btts_si, 0.05)

# ⚾ SECCIÓN MLB
with tab2:
    st.subheader("⚾ Modelo Sabermétrico MLB")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        mlb_loc = st.selectbox("Equipo Local MLB", list(EQUIPOS_MLB.keys()), index=0)
        mlb_vis = st.selectbox("Equipo Visitante MLB", list(EQUIPOS_MLB.keys()), index=1)
        cuota_m = st.number_input("Momio Moneyline Local", value=1.75)
    with col_m2:
        st.info(f"Proyección: {mlb_loc} 4.6 - 3.5 {mlb_vis}")
        if st.button("Guardar Pick MLB 💾"):
            registrar_apuesta("MLB", f"{mlb_loc} vs {mlb_vis}", mlb_loc, mlb_vis, "Moneyline", 0, cuota_m, 0.06)

# 🏈 SECCIÓN NFL
with tab3:
    st.subheader("🏈 Modelo NFL (+EV)")
    st.info("Pronósticos automatizados de Spreads y Totales para NFL.")

# 📋 CONTROL DE HISTORIAL
with tab4:
    st.subheader("📋 Tablero de Control e Historial")
    if historial:
        df_hist = pd.DataFrame(historial)
        st.dataframe(df_hist, use_container_width=True)
        
        with st.expander("🛠️ Cambiar estado por ID"):
            num_id = st.number_input("ID Pick", min_value=1, step=1)
            cb1, cb2, cb3 = st.columns(3)
            if cb1.button("✅ WIN"):
                for item in historial:
                    if item.get("id") == num_id: item["estado"] = "WIN"
                guardar_base_datos(historial)
                st.rerun()
            if cb2.button("❌ LOSS"):
                for item in historial:
                    if item.get("id") == num_id: item["estado"] = "LOSS"
                guardar_base_datos(historial)
                st.rerun()
            if cb3.button("🗑️ Eliminar"):
                eliminar_apuesta(num_id)
    else:
        st.info("No hay apuestas registradas.")
