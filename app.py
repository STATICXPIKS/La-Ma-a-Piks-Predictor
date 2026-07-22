import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import poisson
import plotly.express as px

st.set_page_config(page_title="Liga MX Predictor", layout="wide", page_icon="⚽")
st.title("⚽ Liga MX - Calculadora de Probabilidades y Valor")

ESTADIOS = {
    'Toluca (Nemesio Díez)': 2680, 'Pachuca (Hidalgo)': 2400, 'Puebla (Cuauhtémoc)': 2230,
    'CDMX (Azteca / Cd. Deportes / CU)': 2240, 'Querétaro (Corregidora)': 1820,
    'Aguascalientes (Victoria)': 1800, 'San Luis (Alfonso Lastras)': 1850,
    'Guadalajara (Akron / Jalisco)': 1560, 'Torreón (TCM)': 1120, 'Cd. Juárez (Olímpico)': 1130,
    'Monterrey (BBVA / Universitario)': 500, 'Tijuana (Caliente)': 60, 'Mazatlán (El Encanto)': 10
}

def amer_a_dec(m):
    return (m/100)+1 if m > 0 else (100/abs(m))+1

def matriz_goles(xg_l, xg_v):
    mat = np.zeros((6, 6))
    for x in range(6):
        for y in range(6):
            mat[x, y] = poisson.pmf(x, xg_l) * poisson.pmf(y, xg_v)
    return mat / np.sum(mat)

st.sidebar.header("⚙️ Datos del Partido")
estadio = st.sidebar.selectbox("Estadio del Partido", list(ESTADIOS.keys()))
altitud_visita = st.sidebar.number_input("Altitud Origen Visitante (m)", value=500, step=100)
diff_alt = max(0, ESTADIOS[estadio] - altitud_visita)

col_a1, col_a2 = st.sidebar.columns(2)
ataque_l = col_a1.slider("Ataque Local", 0.5, 2.5, 1.4)
defensa_v = col_a2.slider("Defensa Visitante", 0.5, 2.5, 1.2)

col_b1, col_b2 = st.sidebar.columns(2)
ataque_v = col_b1.slider("Ataque Visitante", 0.5, 2.5, 1.1)
defensa_l = col_b2.slider("Defensa Local", 0.5, 2.5, 0.9)

xg_l = ataque_l * defensa_v * 1.2
xg_v = max(0.2, (ataque_v * defensa_l) * (1 - (diff_alt * 0.00015)))

st.subheader("📊 Goles Esperados (xG)")
c1, c2, c3 = st.columns(3)
c1.metric("Local xG", f"{xg_l:.2f}")
c2.metric("Visitante xG", f"{xg_v:.2f}")
c3.metric("Castigo por Altitud", f"-{diff_alt * 0.00015 * 100:.1f}%")

st.markdown("---")
st.subheader("💵 Carga los Momios de tu Casa de Apuestas (Formatos Americanos)")
m1_in = st.number_input("Momio Gana Local (ej. +130 o -110)", value=130)
mx_in = st.number_input("Momio Empate (ej. +220)", value=220)
m2_in = st.number_input("Momio Gana Visitante (ej. +200)", value=200)

m1, mx, m2 = amer_a_dec(m1_in), amer_a_dec(mx_in), amer_a_dec(m2_in)
mat = matriz_goles(xg_l, xg_v)

p1 = np.sum(np.tril(mat, -1))
px_p = np.sum(np.diag(mat))
p2 = np.sum(np.triu(mat, 1))

ev1 = (p1 * m1) - 1
evx = (px_p * mx) - 1
ev2 = (p2 * m2) - 1

st.markdown("---")
st.subheader("🎯 Veredicto de Apuestas con Valor (+EV)")
res1, res2, res3 = st.columns(3)

def eval_val(col, tit, prob, ev):
    col.write(f"**{tit}**")
    col.write(f"Probabilidad: {prob*100:.1f}%")
    if ev > 0.05:
        col.success(f"¡APUESTA CON VALOR!\nEV: +{ev*100:.1f}%")
    else:
        col.error(f"Sin Valor\nEV: {ev*100:.1f}%")

eval_val(res1, "Local (1)", p1, ev1)
eval_val(res2, "Empate (X)", px_p, evx)
eval_val(res3, "Visitante (2)", p2, ev2)

st.markdown("---")
st.subheader("🔥 Marcadores Exactos más Probables")
df_mat = pd.DataFrame(mat * 100, index=[f"L {i}" for i in range(6)], columns=[f"V {j}" for j in range(6)])
st.plotly_chart(px.imshow(df_mat, text_auto=".1f", color_continuous_scale="Viridis"), use_container_width=True)
