import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.graph_objects as go
import json
import os
from datetime import datetime

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Premier League - Predictor Avanzado & Trap Line Detector",
    layout="wide",
    page_icon="⚽"
)

DB_FILE = "historial_apuestas_pl.json"

# ==============================================================================
# 1. GESTIÓN DE BASE DE DATOS LOCAL
# ==============================================================================
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
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error al guardar base de datos: {e}")

# ==============================================================================
# 2. MOTOR ESTADÍSTICO Y DETECTOR DE TRAMPAS
# ==============================================================================
def calcular_lambda(
    xg_local, xga_local, ppda_local, aereos_local, fatiga_local, rotacion_local,
    xg_vis, xga_vis, ppda_vis, aereos_vis, fatiga_vis, rotacion_vis,
    factor_arbitro, factor_clima
):
    """
    Calcula los parámetros Lambda (esperanza de goles) ajustando xG base por 
    factores tácticos, físicos y contextuales.
    """
    # Promedio histórico de goles por partido en la Premier League (~2.8 total)
    avg_home_goals = 1.55
    avg_away_goals = 1.25

    # Fuerza de ataque/defensa basada en xG (últimos 2.5 años)
    att_home = xg_local / avg_home_goals
    def_home = xga_local / avg_away_goals
    att_away = xg_vis / avg_away_goals
    def_away = xga_vis / avg_home_goals

    # Ajustes Tácticos (PPDA & Duelos Aéreos)
    # Menor PPDA = Mayor intensidad de presión (+rendimiento ofensivo)
    tactical_home = (15 / max(ppda_local, 5.0)) * (aereos_local / 50.0)
    tactical_away = (15 / max(ppda_vis, 5.0)) * (aereos_vis / 50.0)

    # Penalizaciones por Fatiga y Rotación de Plantilla (0.0 a 1.0)
    fatigue_penalty_home = 1.0 - (fatiga_local * 0.12 + rotacion_local * 0.10)
    fatigue_penalty_away = 1.0 - (fatiga_vis * 0.12 + rotacion_vis * 0.10)

    # Estimación de Lambdas base
    lambda_home = avg_home_goals * att_home * def_away * tactical_home * fatigue_penalty_home * factor_arbitro * factor_clima
    lambda_away = avg_away_goals * att_away * def_home * tactical_away * fatigue_penalty_away * (2.0 - factor_arbitro)

    # Mantenemos cotas mínimas realistas
    return max(lambda_home, 0.2), max(lambda_away, 0.15)

def generar_matriz_marcadores(lambda_home, lambda_away, max_goles=6):
    """
    Genera la matriz de probabilidades exactas para marcadores de 0-0 a 6-6.
    """
    matriz = np.zeros((max_goles, max_goles))
    for h in range(max_goles):
        for a in range(max_goles):
            matriz[h, a] = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
    return matriz / np.sum(matriz) # Normalización

def evaluar_riesgo_trampa(prob_modelo, cuota_casino, fatiga_rotacion_alta):
    """
    TRAP LINE DETECTOR:
    Si el casino ofrece una cuota inusualmente alta ("demasiado buena para ser verdad")
    en un equipo con alta fatiga/rotación, detecta una trampa del mercado.
    """
    prob_implícita = 1.0 / cuota_casino if cuota_casino > 1 else 0
    diferencia_ev = (prob_modelo * cuota_casino) - 1.0

    # Detección de trampa: La cuota paga mucho más de lo esperado pero el equipo llega diezmado
    es_trampa = False
    penalización = 0.0

    if fatiga_rotacion_alta and cuota_casino > 2.10 and diferencia_ev > 0.15:
        es_trampa = True
        penalización = 0.25 # Reduce el valor real percibido por riesgo oculto

    prob_ajustada = prob_modelo * (1.0 - penalización)
    ev_real = (prob_ajustada * cuota_casino) - 1.0

    return {
        "es_trampa": es_trampa,
        "prob_original": prob_modelo,
        "prob_ajustada": prob_ajustada,
        "ev_real": ev_real,
        "alerta": "⚠️ TRAP LINE DETECTADA: Cuota inflada en equipo fatigado/rotado." if es_trampa else "✅ Línea Limpia"
    }

# ==============================================================================
# 3. INTERFAZ DE USUARIO (STREAMLIT)
# ==============================================================================
st.title("⚽ Premier League Predictor & Trap Line Detector")
st.caption("Modelo Monte Carlo / Poisson ajustado con xG, PPDA, Fatiga UEFA, Árbitros y Clima.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Equipo Local")
    eq_local = st.text_input("Nombre del Equipo Local", "Arsenal")
    xg_l = st.number_input("xG Promedio (Local)", value=1.95, step=0.05)
    xga_l = st.number_input("xGA Promedio (Local)", value=0.85, step=0.05)
    ppda_l = st.number_input("PPDA (Intensidad Presión Local)", value=9.2, step=0.5)
    aereos_l = st.slider("% Duelos Aéreos Ganados (Local)", 30, 70, 54)
    fatiga_l = st.slider("Nivel de Fatiga UEFA (Local)", 0.0, 1.0, 0.2, step=0.1)
    rotacion_l = st.slider("Índice de Rotación (Local)", 0.0, 1.0, 0.1, step=0.1)
    cuota_l = st.number_input("Cuota Casino (Victoria Local)", value=1.75)

with col2:
    st.subheader("✈️ Equipo Visitante")
    eq_vis = st.text_input("Nombre del Equipo Visitante", "Chelsea")
    xg_v = st.number_input("xG Promedio (Visitante)", value=1.50, step=0.05)
    xga_v = st.number_input("xGA Promedio (Visitante)", value=1.30, step=0.05)
    ppda_v = st.number_input("PPDA (Intensidad Presión Visitante)", value=11.5, step=0.5)
    aereos_v = st.slider("% Duelos Aéreos Ganados (Visitante)", 30, 70, 48)
    fatiga_v = st.slider("Nivel de Fatiga UEFA (Visitante)", 0.0, 1.0, 0.7, step=0.1)
    rotacion_v = st.slider("Índice de Rotación (Visitante)", 0.0, 1.0, 0.6, step=0.1)
    cuota_v = st.number_input("Cuota Casino (Victoria Visitante)", value=4.20)

st.markdown("---")
st.subheader("🌦️ Factores Ambientales y Arbitraje")
col_env1, col_env2 = st.columns(2)
with col_env1:
    arbitro_bias = st.slider("Impacto Árbitro (0.9 = Favorece Visita, 1.0 = Neutral, 1.1 = Favorece Local)", 0.85, 1.15, 1.02, step=0.01)
with col_env2:
    clima_factor = st.slider("Impacto Clima (Lluvia/Viento severo reduce goles)", 0.80, 1.00, 0.95, step=0.01)

# Cálculo al hacer clic
if st.button("🚀 Calcular Probabilidades Exactas y Analizar Trampas", use_container_width=True):
    lam_h, lam_v = calcular_lambda(
        xg_l, xga_l, ppda_l, aereos_l, fatiga_l, rotacion_l,
        xg_v, xga_v, ppda_v, aereos_v, fatiga_v, rotacion_v,
        arbitro_bias, clima_factor
    )

    matriz_prob = generar_matriz_marcadores(lam_h, lam_v)

    # Probabilidades 1X2
    prob_home = float(np.sum(np.tril(matriz_prob, -1)))
    prob_draw = float(np.sum(np.diag(matriz_prob)))
    prob_away = float(np.sum(np.triu(matriz_prob, 1)))

    st.markdown("### 📊 Resultado del Análisis")
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Goles Esperados Local (λ)", f"{lam_h:.2f}")
    res_col2.metric("Goles Esperados Visitante (λ)", f"{lam_v:.2f}")
    res_col3.metric("Total Goles Esperados", f"{lam_h + lam_v:.2f}")

    # Análisis Trap Line
    fatiga_alta_v = (fatiga_v + rotacion_v) > 1.0
    trap_analysis_v = evaluar_riesgo_trampa(prob_away, cuota_v, fatiga_alta_v)

    st.markdown("### 🪤 Evaluación de Trap Line (Línea Trampa)")
    if trap_analysis_v["es_trampa"]:
        st.error(f"{trap_analysis_v['alerta']} - La cuota de {eq_vis} ({cuota_v}) parece alta pero el equipo tiene fatiga/rotación crítica. EV Ajustado: {trap_analysis_v['ev_real']:.2%}")
    else:
        st.success(f"Visita: {trap_analysis_v['alerta']} | EV Real Estimado: {trap_analysis_v['ev_real']:.2%}")

    # Tabla de Marcadores Más Probables
    st.markdown("### 🎯 Marcadores Exactos Más Probables")
    marcadores = []
    for h in range(5):
        for a in range(5):
            marcadores.append({
                "Marcador": f"{eq_local} {h} - {a} {eq_vis}",
                "Probabilidad": f"{matriz_prob[h, a]*100:.2f}%",
                "Cuota Implícita": f"{1/matriz_prob[h, a]:.2f}" if matriz_prob[h, a] > 0 else "N/A"
            })

    df_marcadores = pd.DataFrame(marcadores).sort_values(
        by="Probabilidad", 
        ascending=False, 
        key=lambda x: x.str.rstrip('%').astype(float)
    ).head(7)

    st.table(df_marcadores)

    # Mapa de Calor de Marcadores
    fig = go.Figure(data=go.Heatmap(
        z=matriz_prob[:5, :5] * 100,
        x=[f"{eq_vis} {i}" for i in range(5)],
        y=[f"{eq_local} {i}" for i in range(5)],
        colorscale='Viridis',
        hovertemplate='Marcador: %{y} - %{x}<br>Probabilidad: %{z:.2f}%<extra></extra>'
    ))
    fig.update_layout(title="Mapa de Probabilidad de Marcador Exacto (0-4 Goles)", xaxis_title=eq_vis, yaxis_title=eq_local)
    st.plotly_chart(fig, use_container_width=True)
