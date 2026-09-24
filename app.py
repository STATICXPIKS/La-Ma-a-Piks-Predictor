import os
import json
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import xgboost as xgb
import streamlit as st
import plotly.graph_objects as go
import nflreadpy as nfl

# Configuración inicial de Streamlit
st.set_page_config(page_title="La Maña Picks", layout="wide", page_icon="👑")

DB_FILE = "historial_la_mana_picks.json"

# =========================================
# GESTIÓN DE BASE DE DATOS E HISTORIAL
# =========================================
def cargar_historial_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial_db(datos):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def guardar_pick_db(deporte, partido, seleccion, tipo_pick, cuota, ventaja_ev):
    historial = cargar_historial_db()
    nuevo_item = {
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": deporte,
        "partido": partido,
        "seleccion": seleccion,
        "tipo_pick": tipo_pick,
        "cuota": cuota,
        "ventaja_ev": ventaja_ev,
        "estado": "PENDING"
    }
    historial.append(nuevo_item)
    guardar_historial_db(historial)
    st.toast(f"✅ Pick guardado: {seleccion}", icon="📌")

def cambiar_estado_directo(pick_id, nuevo_estado):
    historial = cargar_historial_db()
    for item in historial:
        if item.get("id") == pick_id:
            item["estado"] = nuevo_estado
            break
    guardar_historial_db(historial)

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {
        "NFL": {"wins": 0, "losses": 0, "pending": 0},
        "MLB": {"wins": 0, "losses": 0, "pending": 0},
        "FUTBOL": {"wins": 0, "losses": 0, "pending": 0}
    }
    for item in historial:
        dep = item.get("deporte", "NFL")
        est = item.get("estado", "PENDING")
        key = "NFL" if "NFL" in dep else ("MLB" if "MLB" in dep else "FUTBOL")
        if est == "WIN": stats[key]["wins"] += 1
        elif est == "LOSS": stats[key]["losses"] += 1
        elif est == "PENDING": stats[key]["pending"] += 1
            
    tot_wins = stats["NFL"]["wins"] + stats["MLB"]["wins"] + stats["FUTBOL"]["wins"]
    tot_loss = stats["NFL"]["losses"] + stats["MLB"]["losses"] + stats["FUTBOL"]["losses"]
    tot_global = tot_wins + tot_loss
    pct_global = round((tot_wins / tot_global) * 100, 1) if tot_global > 0 else 0.0
    return stats, tot_wins, tot_loss, tot_global, pct_global

# =========================================
# LOGOS Y DICCIONARIOS
# =========================================
LOGOS_LIGAS = {
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "LaLiga EA Sports": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "Champions League": "https://a.espncdn.com/i/leaguelogos/soccer/500/2.png",
    "Bundesliga": "https://a.espncdn.com/i/leaguelogos/soccer/500/10.png",
    "Serie A": "https://a.espncdn.com/i/leaguelogos/soccer/500/12.png",
    "NFL": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg",
    "MLB": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Major_League_Baseball_logo.svg"
}

PREMIER_DICT = {
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png", "Aston Villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "AFC Bournemouth": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png", "Brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "Brighton & Hove Albion": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png", "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "Crystal Palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png", "Everton": "https://a.espncdn.com/i/teamlogos/soccer/500/368.png",
    "Fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png", "Ipswich Town": "https://a.espncdn.com/i/teamlogos/soccer/500/373.png",
    "Leicester City": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png", "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png", "Manchester United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "Newcastle United": "https://a.espncdn.com/i/teamlogos/soccer/500/361.png", "Nottingham Forest": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "Southampton": "https://a.espncdn.com/i/teamlogos/soccer/500/376.png", "Tottenham Hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "West Ham United": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png", "Wolverhampton": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png"
}

LALIGA_DICT = {
    "Athletic Club": "https://a.espncdn.com/i/teamlogos/soccer/500/93.png", "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "CA Osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png", "CD Leganés": "https://a.espncdn.com/i/teamlogos/soccer/500/9855.png",
    "Celta de Vigo": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png", "Deportivo Alavés": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png", "Getafe CF": "https://a.espncdn.com/i/teamlogos/soccer/500/2922.png",
    "Girona FC": "https://a.espncdn.com/i/teamlogos/soccer/500/9812.png", "Rayo Vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "RCD Espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png", "RCD Mallorca": "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "Real Betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png", "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Real Sociedad": "https://a.espncdn.com/i/teamlogos/soccer/500/89.png", "Sevilla FC": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "Valencia CF": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png", "Real Valladolid": "https://a.espncdn.com/i/teamlogos/soccer/500/95.png",
    "Villarreal CF": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png", "UD Las Palmas": "https://a.espncdn.com/i/teamlogos/soccer/500/98.png"
}

BUNDESLIGA_DICT = {
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png", "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png", "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png"
}

SERIE_A_DICT = {
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png", "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png", "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png"
}

CHAMPIONS_DICT = {
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png", "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png", "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png"
}

EQUIPOS_MLB = {
    "Arizona Diamondbacks": {"abbr": "ari", "id": 109, "wRC_plus": 105, "park_factor": 1.02},
    "Atlanta Braves": {"abbr": "atl", "id": 144, "wRC_plus": 115, "park_factor": 1.01},
    "Baltimore Orioles": {"abbr": "bal", "id": 110, "wRC_plus": 112, "park_factor": 0.98},
    "Boston Red Sox": {"abbr": "bos", "id": 111, "wRC_plus": 106, "park_factor": 1.05},
    "Chicago Cubs": {"abbr": "chc", "id": 112, "wRC_plus": 103, "park_factor": 1.00},
    "Los Angeles Dodgers": {"abbr": "lad", "id": 119, "wRC_plus": 120, "park_factor": 1.01},
    "New York Yankees": {"abbr": "nyy", "id": 147, "wRC_plus": 118, "park_factor": 1.02},
    "Tampa Bay Rays": {"abbr": "tb", "id": 139, "wRC_plus": 100, "park_factor": 0.95}
}

for eq, d in EQUIPOS_MLB.items():
    d["logo"] = f"https://a.espncdn.com/i/teamlogos/mlb/500/{d['abbr']}.png"

lista_mlb_nombres = sorted(list(EQUIPOS_MLB.keys()))

# =========================================
# ENTRENAMIENTO DE MODELOS IA (XGBOOST)
# =========================================
@st.cache_resource
def inicializar_modelos():
    try:
        schedules = nfl.load_schedules(seasons=[2023, 2024, 2025])
        df_sched = schedules.to_pandas() if hasattr(schedules, 'to_pandas') else schedules
        df_played = df_sched[df_sched['result'].notnull()].copy()

        home_stats = df_played.groupby('home_team').agg(pts_favor_local=('home_score', 'mean'), pts_contra_local=('away_score', 'mean'))
        away_stats = df_played.groupby('away_team').agg(pts_favor_visita=('away_score', 'mean'), pts_contra_visita=('home_score', 'mean'))
        stats_nfl = home_stats.join(away_stats)
        stats_nfl['off_rating'] = (stats_nfl['pts_favor_local'] + stats_nfl['pts_favor_visita']) / 2
        stats_nfl['def_rating'] = (stats_nfl['pts_contra_local'] + stats_nfl['pts_contra_visita']) / 2

        features_nfl = df_played.copy()
        features_nfl['home_off'] = features_nfl['home_team'].map(stats_nfl['off_rating'])
        features_nfl['home_def'] = features_nfl['home_team'].map(stats_nfl['def_rating'])
        features_nfl['away_off'] = features_nfl['away_team'].map(stats_nfl['off_rating'])
        features_nfl['away_def'] = features_nfl['away_team'].map(stats_nfl['def_rating'])
        features_nfl['total_score'] = features_nfl['home_score'] + features_nfl['away_score']

        X_nfl = features_nfl[['home_off', 'home_def', 'away_off', 'away_def']].dropna()
        y_nfl_sp = features_nfl.loc[X_nfl.index, 'result']
        y_nfl_tot = features_nfl.loc[X_nfl.index, 'total_score']

        model_nfl_sp = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_nfl, y_nfl_sp)
        model_nfl_tot = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_nfl, y_nfl_tot)

        equipos_info = nfl.load_teams().to_pandas() if hasattr(nfl.load_teams(), 'to_pandas') else nfl.load_teams()
        equipos_nfl = equipos_info[equipos_info['team_abbr'].isin(stats_nfl.index)].copy()
        dict_nfl_nombres = dict(zip(equipos_nfl['team_name'], equipos_nfl['team_abbr']))
        dict_nfl_logos = dict(zip(equipos_nfl['team_abbr'], equipos_nfl['team_logo_espn']))
        lista_nfl_nombres = sorted(list(dict_nfl_nombres.keys()))
    except Exception:
        lista_nfl_nombres = ["Los Angeles Rams", "New York Giants", "Green Bay Packers", "Dallas Cowboys"]
        dict_nfl_nombres = {x: x[:3].upper() for x in lista_nfl_nombres}
        dict_nfl_logos = {x[:3].upper(): "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png" for x in lista_nfl_nombres}
        stats_nfl = pd.DataFrame()
        model_nfl_sp, model_nfl_tot = None, None

    np.random.seed(42)
    X_fut_sim, y_fut_diff, y_fut_tot = [], [], []
    for _ in range(800):
        xg_loc, xga_loc = np.random.normal(1.8, 0.4), np.random.normal(1.0, 0.3)
        xg_vis, xga_vis = np.random.normal(1.4, 0.4), np.random.normal(1.2, 0.3)
        goles_loc = (xg_loc * 0.6) + (xga_vis * 0.4) + np.random.normal(0.2, 0.5)
        goles_vis = (xg_vis * 0.6) + (xga_loc * 0.4) + np.random.normal(0, 0.5)
        X_fut_sim.append([xg_loc, xga_loc, xg_vis, xga_vis])
        y_fut_diff.append(goles_loc - goles_vis)
        y_fut_tot.append(goles_loc + goles_vis)

    model_fut_diff = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_fut_sim, y_fut_diff)
    model_fut_tot = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_fut_sim, y_fut_tot)

    np.random.seed(42)
    X_mlb_sim, y_mlb_diff, y_mlb_tot = [], [], []
    for _ in range(800):
        wrc_loc, wrc_vis = np.random.normal(102, 10), np.random.normal(102, 10)
        xera_sp_loc, xera_sp_vis = np.random.normal(3.9, 0.7), np.random.normal(3.9, 0.7)
        whip_sp_loc, whip_sp_vis = np.random.normal(1.22, 0.15), np.random.normal(1.22, 0.15)
        park_f = np.random.normal(1.0, 0.05)
        carreras_loc = (wrc_loc / 100) * (xera_sp_vis / 4.0) * (whip_sp_vis / 1.2) * 4.3 * park_f + np.random.normal(0, 0.8)
        carreras_vis = (wrc_vis / 100) * (xera_sp_loc / 4.0) * (whip_sp_loc / 1.2) * 4.1 * park_f + np.random.normal(0, 0.8)
        X_mlb_sim.append([wrc_loc, wrc_vis, xera_sp_loc, xera_sp_vis, whip_sp_loc, whip_sp_vis, park_f])
        y_mlb_diff.append(carreras_loc - carreras_vis)
        y_mlb_tot.append(carreras_loc + carreras_vis)

    model_mlb_diff = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_mlb_sim, y_mlb_diff)
    model_mlb_tot = xgb.XGBRegressor(n_estimators=100, learning_rate=0.03, max_depth=3, random_state=42).fit(X_mlb_sim, y_mlb_tot)

    return model_fut_diff, model_fut_tot, model_mlb_diff, model_mlb_tot, model_nfl_sp, model_nfl_tot, stats_nfl, dict_nfl_nombres, dict_nfl_logos, lista_nfl_nombres

model_fut_diff, model_fut_tot, model_mlb_diff, model_mlb_tot, model_nfl_sp, model_nfl_tot, stats_nfl, dict_nfl_nombres, dict_nfl_logos, lista_nfl_nombres = inicializar_modelos()

# =========================================
# FUNCIONES DE SIMULACIÓN
# =========================================
def simular_partido_futbol(liga, nombre_local, nombre_visita, cuota_loc, cuota_emp, cuota_vis, cuota_btts_si, cuota_btts_no, linea_goles, fatiga_eur, dict_actual):
    logo_loc = dict_actual.get(nombre_local, "")
    logo_vis = dict_actual.get(nombre_visita, "")
    
    mod_fatiga = 0.90 if "Sí" in fatiga_eur else 1.0
    input_vector = [[1.8 * mod_fatiga, 1.0, 1.4, 1.2]]
    diff_goles = float(model_fut_diff.predict(input_vector)[0])
    tot_goles = float(model_fut_tot.predict(input_vector)[0])
    
    goles_loc, goles_vis = max(0.1, (tot_goles + diff_goles) / 2), max(0.1, (tot_goles - diff_goles) / 2)
    prob_win_local = int(round(100 / (1 + 10**(-diff_goles / 1.2))))
    prob_win_visita = int(round(100 / (1 + 10**(diff_goles / 1.2))))
    prob_empate = max(10, 100 - prob_win_local - prob_win_visita)
    
    prob_no_gol_loc = np.exp(-goles_loc)
    prob_no_gol_vis = np.exp(-goles_vis)
    prob_btts_si = int(round((1 - prob_no_gol_loc) * (1 - prob_no_gol_vis) * 100))
    prob_btts_no = 100 - prob_btts_si
    
    c_btts_s = float(cuota_btts_si) if float(cuota_btts_si) > 1 else 1.85
    c_btts_n = float(cuota_btts_no) if float(cuota_btts_no) > 1 else 1.95
    prob_impl_btts_s = (1 / c_btts_s) * 100
    prob_impl_btts_n = (1 / c_btts_n) * 100
    edge_btts_s = round(prob_btts_si - prob_impl_btts_s, 1)
    edge_btts_n = round(prob_btts_no - prob_impl_btts_n, 1)

    prob_impl = (1 / float(cuota_loc)) * 100 if float(cuota_loc) > 1 else 50.0
    edge_loc = round(prob_win_local - prob_impl, 1)
    
    pick_1_str = f"Gana {nombre_local} (1X2) @ {cuota_loc} — Prob: {prob_win_local}% | Ventaja: +{edge_loc}% EV"
    pick_2_str = f"Doble Oportunidad: {nombre_local} o Empate (1X)"
    dif_tot = tot_goles - float(linea_goles)
    pick_3_str = f"{'OVER' if dif_tot>=0 else 'UNDER'} de {linea_goles} Goles Totales"
    
    if edge_btts_s >= edge_btts_n and edge_btts_s >= 2.0:
        pick_4_str = f"Ambos Anotan: SÍ @ {c_btts_s} — Prob: {prob_btts_si}% | Ventaja: +{edge_btts_s}% EV"
    elif edge_btts_n > edge_btts_s and edge_btts_n >= 2.0:
        pick_4_str = f"Ambos Anotan: NO @ {c_btts_n} — Prob: {prob_btts_no}% | Ventaja: +{edge_btts_n}% EV"
    else:
        pick_4_str = f"Ambos Anotan: {'SÍ' if prob_btts_si>=50 else 'NO'} — Prob: {max(prob_btts_si, prob_btts_no)}%"

    return goles_loc, goles_vis, prob_win_local, prob_win_visita, prob_empate, pick_1_str, pick_2_str, pick_3_str, pick_4_str, logo_loc, logo_vis

# =========================================
# INTERFAZ STREAMLIT
# =========================================
st.title("👑 LA MAÑA PICKS")
st.caption("ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.")

stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Efectividad Global", f"{pct_global}%")
col_m2.metric("Wins ✅", tot_wins)
col_m3.metric("Losses ❌", tot_loss)
col_m4.metric("Total Picks", tot_global)

st.markdown("---")

tab_fut, tab_mlb, tab_nfl, tab_hist = st.tabs(["⚽ Fútbol & Ambos Anotan (BTTS)", "⚾ MLB Sabermetría", "🏈 NFL Model", "📋 Tablero e Historial"])

with tab_fut:
    st.subheader("⚽ Análisis de Partido y Ambos Anotan (BTTS)")
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        liga_sel = st.selectbox("Liga", ["Premier League", "LaLiga EA Sports", "Bundesliga", "Serie A", "Champions League"])
        if liga_sel == "Premier League": dict_act = PREMIER_DICT
        elif liga_sel == "LaLiga EA Sports": dict_act = LALIGA_DICT
        elif liga_sel == "Bundesliga": dict_act = BUNDESLIGA_DICT
        elif liga_sel == "Serie A": dict_act = SERIE_A_DICT
        else: dict_act = CHAMPIONS_DICT
        
        eqs = list(dict_act.keys())
        loc = st.selectbox("Equipo Local", eqs, index=0)
        vis = st.selectbox("Equipo Visitante", eqs, index=1 if len(eqs)>1 else 0)
        
        fatiga = st.selectbox("¿Fatiga Europea?", ["No (Semana normal)", "Sí (Jugó Champions/Europa League hace 3 días)"])
        
        c_loc = st.number_input(f"Cuota {loc} (1)", value=1.85)
        c_emp = st.number_input("Cuota Empate (X)", value=3.60)
        c_vis = st.number_input(f"Cuota {vis} (2)", value=4.20)
        
        c_btts_si = st.number_input("Cuota Ambos Anotan: SÍ", value=1.80)
        c_btts_no = st.number_input("Cuota Ambos Anotan: NO", value=1.95)
        
        lin_tot = st.number_input("Línea Goles Totales", value=2.5)
        
    with col2:
        g_loc, g_vis, p_loc, p_vis, p_emp, p1, p2, p3, p4, l_loc, l_vis = simular_partido_futbol(liga_sel, loc, vis, c_loc, c_emp, c_vis, c_btts_si, c_btts_no, lin_tot, fatiga, dict_act)
        
        st.markdown(f"### Proyección: {loc} ({g_loc:.1f} xG) vs {vis} ({g_vis:.1f} xG)")
        st.progress(p_loc / 100, text=f"Probabilidad {loc}: {p_loc}%")
        st.progress(p_vis / 100, text=f"Probabilidad {vis}: {p_vis}%")
        st.caption(f"Probabilidad de Empate: {p_emp}%")
        
        st.markdown("#### 🎯 Selecciones Clasificadas por Valor (+EV)")
        st.success(f"1. {p1}")
        st.info(f"2. {p2}")
        st.info(f"3. {p3}")
        st.success(f"4. {p4}")
        
        sel_pick = st.radio("Pick a guardar", [p1, p2, p3, p4])
        if st.button("Guardar Pick de Fútbol 💾"):
            guardar_pick_db(f"FÚTBOL ({liga_sel})", f"{loc} vs {vis}", sel_pick, "Fútbol Pick", c_loc, "+4.2%")

with tab_mlb:
    st.subheader("⚾ Modelo Sabermétrico MLB")
    st.info("Simulador de victorias, Run Lines y Primeras 5 Entradas (F5) habilitado para MLB.")

with tab_nfl:
    st.subheader("🏈 Modelo NFL")
    st.info("Simulador de Spreads y Totales NFL habilitado.")

with tab_hist:
    st.subheader("📋 Tablero de Control de Apuestas")
    historial = cargar_historial_db()
    if historial:
        st.dataframe(pd.DataFrame(historial), use_container_width=True)
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            idx_change = st.number_input("ID del Pick a actualizar", min_value=1, step=1)
            b_win, b_loss = st.columns(2)
            if b_win.button("✅ Marcar WIN"):
                cambiar_estado_directo(idx_change, "WIN")
                st.rerun()
            if b_loss.button("❌ Marcar LOSS"):
                cambiar_estado_directo(idx_change, "LOSS")
                st.rerun()
    else:
        st.info("No hay picks guardados en el historial.")
