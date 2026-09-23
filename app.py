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
# INTERFAZ Y DASHBOARD PRINCIPAL
# ==========================================
st.title("👑 LA MAÑA PICKS ANALYTICS PRO")
st.write("Plataforma de pronósticos y gestión de valor +EV")

historial = cargar_base_datos()

# Métricas rápidas
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
st.subheader("📋 Tablero de Control de Apuestas")

if historial:
    df_hist = pd.DataFrame(historial)
    st.dataframe(df_hist, use_container_width=True)
else:
    st.info("No hay apuestas registradas en el historial.")

# Gestión de IDs
with st.expander("⚙️ Gestor de Estado de Apuestas por ID"):
    num_id = st.number_input("ID de la Apuesta", min_value=1, step=1)
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    if c_btn1.button("✅ Marcar WIN"):
        for item in historial:
            if item.get("id") == num_id:
                item["estado"] = "WIN"
        guardar_base_datos(historial)
        st.rerun()
    if c_btn2.button("❌ Marcar LOSS"):
        for item in historial:
            if item.get("id") == num_id:
                item["estado"] = "LOSS"
        guardar_base_datos(historial)
        st.rerun()
    if c_btn3.button("🗑️ Eliminar Pick"):
        eliminar_apuesta(num_id)
