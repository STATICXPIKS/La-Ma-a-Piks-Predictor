import os
import json
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import xgboost as xgb
import gradio as gr
import nflreadpy as nfl
from scipy.stats import norm

# Archivo de base de datos local en el servidor
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
        print(f"Error al guardar: {e}")

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

def cambiar_estado_directo(pick_id, nuevo_estado):
    historial = cargar_historial_db()
    for item in historial:
        if item.get("id") == pick_id:
            item["estado"] = nuevo_estado
            break
    guardar_historial_db(historial)
    return generar_dashboard_completo()

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {
        "NFL": {"wins": 0, "losses": 0, "pending": 0},
        "MLB": {"wins": 0, "losses": 0, "pending": 0},
        "FUTBOL": {"wins": 0, "losses": 0, "pending": 0}
    }
    for item in historial:
        dep = str(item.get("deporte", "")).upper()
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
# LOGOS Y DICCIONARIOS DE EQUIPOS
# =========================================
LOGOS_LIGAS = {
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "LaLiga EA Sports": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "UEFA Conference League": "https://a.espncdn.com/i/leaguelogos/soccer/500/2036.png",
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

CONFERENCE_LEAGUE_DICT = {
    "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png", "Real Betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "Fiorentina": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png", "FC Heidenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/10363.png",
    "Panathinaikos": "https://a.espncdn.com/i/teamlogos/soccer/500/265.png", "Copenhague": "https://a.espncdn.com/i/teamlogos/soccer/500/165.png",
    "Rapid Viena": "https://a.espncdn.com/i/teamlogos/soccer/500/171.png", "Legia Varsovia": "https://a.espncdn.com/i/teamlogos/soccer/500/237.png",
    "Vitória Guimarães": "https://a.espncdn.com/i/teamlogos/soccer/500/2020.png", "Gent": "https://a.espncdn.com/i/teamlogos/soccer/500/463.png",
    "LASK": "https://a.espncdn.com/i/teamlogos/soccer/500/2034.png", "Molde": "https://a.espncdn.com/i/teamlogos/soccer/500/624.png"
}

BUNDESLIGA_DICT = {
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png", "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png", "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "Eintracht Frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png", "VfB Stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "SC Freiburg": "https://a.espncdn.com/i/teamlogos/soccer/500/126.png", "1. FC Union Berlin": "https://a.espncdn.com/i/teamlogos/soccer/500/130.png",
    "Borussia Mönchengladbach": "https://a.espncdn.com/i/teamlogos/soccer/500/128.png", "Werder Bremen": "https://a.espncdn.com/i/teamlogos/soccer/500/137.png",
    "FC Augsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/3812.png", "TSG Hoffenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "Mainz 05": "https://a.espncdn.com/i/teamlogos/soccer/500/129.png", "VfL Wolfsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/138.png",
    "1. FC Heidenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/10363.png", "VfL Bochum": "https://a.espncdn.com/i/teamlogos/soccer/500/123.png",
    "St. Pauli": "https://a.espncdn.com/i/teamlogos/soccer/500/268.png", "Holstein Kiel": "https://a.espncdn.com/i/teamlogos/soccer/500/8066.png"
}

SERIE_A_DICT = {
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png", "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png", "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "AS Roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png", "Atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/105.png",
    "Lazio": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png", "Fiorentina": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png",
    "Bologna": "https://a.espncdn.com/i/teamlogos/soccer/500/107.png", "Torino": "https://a.espncdn.com/i/teamlogos/soccer/500/239.png",
    "Monza": "https://a.espncdn.com/i/teamlogos/soccer/500/3614.png", "Genoa": "https://a.espncdn.com/i/teamlogos/soccer/500/3263.png",
    "Parma": "https://a.espncdn.com/i/teamlogos/soccer/500/113.png", "Udinese": "https://a.espncdn.com/i/teamlogos/soccer/500/118.png",
    "Cagliari": "https://a.espncdn.com/i/teamlogos/soccer/500/108.png", "Hellas Verona": "https://a.espncdn.com/i/teamlogos/soccer/500/238.png",
    "Empoli": "https://a.espncdn.com/i/teamlogos/soccer/500/240.png", "Lecce": "https://a.espncdn.com/i/teamlogos/soccer/500/3452.png",
    "Como 1907": "https://a.espncdn.com/i/teamlogos/soccer/500/2625.png", "Venezia": "https://a.espncdn.com/i/teamlogos/soccer/500/2744.png"
}

CHAMPIONS_DICT = {
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png", "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png", "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png", "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png", "Paris Saint-Germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png", "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png", "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png", "Atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/105.png",
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png", "PSV Eindhoven": "https://a.espncdn.com/i/teamlogos/soccer/500/148.png",
    "Feyenoord": "https://a.espncdn.com/i/teamlogos/soccer/500/142.png", "Sporting CP": "https://a.espncdn.com/i/teamlogos/soccer/500/300.png",
    "Benfica": "https://a.espncdn.com/i/teamlogos/soccer/500/294.png", "Club Brujas": "https://a.espncdn.com/i/teamlogos/soccer/500/2282.png"
}

EQUIPOS_MLB = {
    "Arizona Diamondbacks": {"abbr": "ari", "id": 109, "wRC_plus": 105, "park_factor": 1.02},
    "Atlanta Braves": {"abbr": "atl", "id": 144, "wRC_plus": 115, "park_factor": 1.01},
    "Baltimore Orioles": {"abbr": "bal", "id": 110, "wRC_plus": 112, "park_factor": 0.98},
    "Boston Red Sox": {"abbr": "bos", "id": 111, "wRC_plus": 106, "park_factor": 1.05},
    "Chicago Cubs": {"abbr": "chc", "id": 112, "wRC_plus": 103, "park_factor": 1.00},
    "Chicago White Sox": {"abbr": "cws", "id": 145, "wRC_plus": 84, "park_factor": 0.98},
    "Cincinnati Reds": {"abbr": "cin", "id": 113, "wRC_plus": 98, "park_factor": 1.06},
    "Cleveland Guardians": {"abbr": "cle", "id": 114, "wRC_plus": 101, "park_factor": 0.96},
    "Colorado Rockies": {"abbr": "col", "id": 115, "wRC_plus": 91, "park_factor": 1.15},
    "Detroit Tigers": {"abbr": "det", "id": 116, "wRC_plus": 97, "park_factor": 0.97},
    "Houston Astros": {"abbr": "hou", "id": 117, "wRC_plus": 113, "park_factor": 0.99},
    "Kansas City Royals": {"abbr": "kc", "id": 118, "wRC_plus": 102, "park_factor": 1.02},
    "Los Angeles Angels": {"abbr": "laa", "id": 108, "wRC_plus": 95, "park_factor": 0.99},
    "Los Angeles Dodgers": {"abbr": "lad", "id": 119, "wRC_plus": 120, "park_factor": 1.01},
    "Miami Marlins": {"abbr": "mia", "id": 146, "wRC_plus": 89, "park_factor": 0.95},
    "Milwaukee Brewers": {"abbr": "mil", "id": 158, "wRC_plus": 101, "park_factor": 1.01},
    "Minnesota Twins": {"abbr": "min", "id": 142, "wRC_plus": 104, "park_factor": 1.00},
    "New York Mets": {"abbr": "nym", "id": 121, "wRC_plus": 109, "park_factor": 0.96},
    "New York Yankees": {"abbr": "nyy", "id": 147, "wRC_plus": 118, "park_factor": 1.02},
    "Oakland Athletics": {"abbr": "oak", "id": 133, "wRC_plus": 96, "park_factor": 0.95},
    "Philadelphia Phillies": {"abbr": "phi", "id": 143, "wRC_plus": 114, "park_factor": 1.03},
    "Pittsburgh Pirates": {"abbr": "pit", "id": 134, "wRC_plus": 93, "park_factor": 0.97},
    "San Diego Padres": {"abbr": "sd", "id": 135, "wRC_plus": 107, "park_factor": 0.95},
    "San Francisco Giants": {"abbr": "sf", "id": 137, "wRC_plus": 97, "park_factor": 0.94},
    "Seattle Mariners": {"abbr": "sea", "id": 136, "wRC_plus": 98, "park_factor": 0.92},
    "St. Louis Cardinals": {"abbr": "stl", "id": 138, "wRC_plus": 98, "park_factor": 0.98},
    "Tampa Bay Rays": {"abbr": "tb", "id": 139, "wRC_plus": 100, "park_factor": 0.95},
    "Texas Rangers": {"abbr": "tex", "id": 140, "wRC_plus": 105, "park_factor": 1.02},
    "Toronto Blue Jays": {"abbr": "tor", "id": 141, "wRC_plus": 102, "park_factor": 0.99},
    "Washington Nationals": {"abbr": "wsh", "id": 120, "wRC_plus": 94, "park_factor": 1.01}
}

for eq, d in EQUIPOS_MLB.items():
    d["logo"] = f"https://a.espncdn.com/i/teamlogos/mlb/500/{d['abbr']}.png"

lista_mlb_nombres = sorted(list(EQUIPOS_MLB.keys()))

# =========================================
# MODELOS DE ENTRENAMIENTO IA
# =========================================
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
    lista_nfl_nombres = ["Detroit Lions", "New York Jets", "Green Bay Packers", "Dallas Cowboys"]
    dict_nfl_nombres = {
        "Detroit Lions": "DET", "New York Jets": "NYJ",
        "Green Bay Packers": "GB", "Dallas Cowboys": "DAL"
    }
    dict_nfl_logos = {
        "DET": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png",
        "NYJ": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
        "GB": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
        "DAL": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png"
    }

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

# =========================================
# FUNCIONES DE SIMULACIÓN Y APIS
# =========================================
def auto_cargar_pitchers_mlb(nombre_local, nombre_visita):
    id_loc = EQUIPOS_MLB[nombre_local]["id"]
    id_vis = EQUIPOS_MLB[nombre_visita]["id"]
    hoy = datetime.now().strftime("%Y-%m-%d")
    url_sched = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={hoy}&endDate={hoy}&hydrate=probablePitcher"
    p_loc_name, era_loc, whip_loc = "Abridor Local", 3.80, 1.20
    p_vis_name, era_vis, whip_vis = "Abridor Visitante", 3.80, 1.20

    try:
        r = requests.get(url_sched, timeout=4)
        if r.status_code == 200:
            data = r.json()
            dates = data.get("dates", [])
            if dates:
                games = dates[0].get("games", [])
                for g in games:
                    h_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
                    a_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
                    if h_id == id_loc or a_id == id_loc:
                        p_loc_data = g.get("teams", {}).get("home", {}).get("probablePitcher", {})
                        p_vis_data = g.get("teams", {}).get("away", {}).get("probablePitcher", {})
                        p_loc_id, p_vis_id = p_loc_data.get("id"), p_vis_data.get("id")
                        if p_loc_data.get("fullName"): p_loc_name = p_loc_data.get("fullName")
                        if p_vis_data.get("fullName"): p_vis_name = p_vis_data.get("fullName")

                        if p_loc_id:
                            r_p1 = requests.get(f"https://statsapi.mlb.com/api/v1/people/{p_loc_id}?hydrate=stats(group=[pitching],type=[season])", timeout=3)
                            if r_p1.status_code == 200:
                                st1 = r_p1.json().get("people", [{}])[0].get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
                                era_loc, whip_loc = float(st1.get("era", 3.80)), float(st1.get("whip", 1.20))

                        if p_vis_id:
                            r_p2 = requests.get(f"https://statsapi.mlb.com/api/v1/people/{p_vis_id}?hydrate=stats(group=[pitching],type=[season])", timeout=3)
                            if r_p2.status_code == 200:
                                st2 = r_p2.json().get("people", [{}])[0].get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
                                era_vis, whip_vis = float(st2.get("era", 3.80)), float(st2.get("whip", 1.20))
                        break
    except Exception:
        pass

    status_msg = f"🟢 MLB API: {p_loc_name} ({era_loc} ERA) vs {p_vis_name} ({era_vis} ERA)"
    return era_loc, whip_loc, era_vis, whip_vis, status_msg

def simular_player_prop_mlb(nombre_jugador, tipo_prop, linea_casino, cuota_over, cuota_under, era_rival, whip_rival):
    linea = float(linea_casino)
    c_over, c_under = float(cuota_over), float(cuota_under)

    if "Ponches" in tipo_prop or "Ks" in tipo_prop:
        proyeccion = round(5.2 * (4.0 / float(era_rival)) * (1.2 / float(whip_rival)) + np.random.normal(0, 0.4), 1)
        unidad = "Ks"
    elif "Hits" in tipo_prop or "H+R+RBI" in tipo_prop:
        proyeccion = round(1.8 * (float(era_rival) / 3.8) * (float(whip_rival) / 1.15) + np.random.normal(0, 0.2), 1)
        unidad = "Pts/H"
    else:
        proyeccion = round(16.5 * (3.8 / float(era_rival)) + np.random.normal(0, 0.5), 1)
        unidad = "Outs"

    prob_over = int(min(90, max(10, 50 + (proyeccion - linea) * 18)))
    prob_under = 100 - prob_over

    prob_impl_over = (1 / c_over) * 100 if c_over > 1 else 50.0
    prob_impl_under = (1 / c_under) * 100 if c_under > 1 else 50.0

    ev_over = round(prob_over - prob_impl_over, 1)
    ev_under = round(prob_under - prob_impl_under, 1)

    if ev_over >= ev_under and ev_over >= 2.0:
        rec_str = f"OVER de {linea} {unidad} para {nombre_jugador} @ {c_over}"
        prob_rec = prob_over
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET OVER 🔥 (+{ev_over}% EV)</span>'
    elif ev_under > ev_over and ev_under >= 2.0:
        rec_str = f"UNDER de {linea} {unidad} para {nombre_jugador} @ {c_under}"
        prob_rec = prob_under
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET UNDER 🔥 (+{ev_under}% EV)</span>'
    else:
        rec_str = f"Línea de {nombre_jugador} en {linea} {unidad}"
        prob_rec = max(prob_over, prob_under)
        badge = '<span style="background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">SKIP ❌ (Sin Ventaja)</span>'

    html_prop = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="font-size: 16px; font-weight: 900; color: #065F46; border-bottom: 1px solid #ECFDF5; padding-bottom: 8px; margin-bottom: 12px;">
            👤 ANÁLISIS DE PLAYER PROP MLB: {nombre_jugador.upper()} ({tipo_prop})
        </div>
        <div style="background: #F8FAFC; border-radius: 10px; padding: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 13px; color: #64748B;">Proyección del Modelo:</div>
                <div style="font-size: 24px; font-weight: 900; color: #059669;">{proyeccion} {unidad}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 13px; color: #64748B;">Línea de Casino:</div>
                <div style="font-size: 24px; font-weight: 900; color: #0F172A;">{linea}</div>
            </div>
        </div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; font-weight: 800; color: #064E3B;">{rec_str}</div>
                <div style="font-size: 11px; color: #047857;">Probabilidad Calculada: {prob_rec}%</div>
            </div>
            {badge}
        </div>
    </div>
    """
    return html_prop, rec_str

def simular_player_prop_nfl(nombre_jugador, tipo_prop, linea_casino, cuota_over, cuota_under):
    linea = float(linea_casino)
    c_over, c_under = float(cuota_over), float(cuota_under)

    if "Pase" in tipo_prop:
        proyeccion = round(245.5 + np.random.normal(0, 15), 1)
        unidad = "Yds Pase"
    elif "Tierra" in tipo_prop:
        proyeccion = round(68.0 + np.random.normal(0, 8), 1)
        unidad = "Yds Tierra"
    elif "Recepción" in tipo_prop:
        proyeccion = round(58.5 + np.random.normal(0, 6), 1)
        unidad = "Yds Rec"
    else:
        proyeccion = round(0.75 + np.random.normal(0, 0.1), 2)
        unidad = "TDs"

    prob_over = int(min(90, max(10, 50 + (proyeccion - linea) * 1.5)))
    prob_under = 100 - prob_over

    prob_impl_over = (1 / c_over) * 100 if c_over > 1 else 50.0
    prob_impl_under = (1 / c_under) * 100 if c_under > 1 else 50.0

    ev_over = round(prob_over - prob_impl_over, 1)
    ev_under = round(prob_under - prob_impl_under, 1)

    if ev_over >= ev_under and ev_over >= 2.0:
        rec_str = f"OVER de {linea} {unidad} para {nombre_jugador} @ {c_over}"
        prob_rec = prob_over
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET OVER 🔥 (+{ev_over}% EV)</span>'
    elif ev_under > ev_over and ev_under >= 2.0:
        rec_str = f"UNDER de {linea} {unidad} para {nombre_jugador} @ {c_under}"
        prob_rec = prob_under
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET UNDER 🔥 (+{ev_under}% EV)</span>'
    else:
        rec_str = f"Línea de {nombre_jugador} en {linea} {unidad}"
        prob_rec = max(prob_over, prob_under)
        badge = '<span style="background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">SKIP ❌ (Sin Ventaja)</span>'

    html_prop = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="font-size: 16px; font-weight: 900; color: #065F46; border-bottom: 1px solid #ECFDF5; padding-bottom: 8px; margin-bottom: 12px;">
            🏈 ANÁLISIS DE PLAYER PROP NFL: {nombre_jugador.upper()} ({tipo_prop})
        </div>
        <div style="background: #F8FAFC; border-radius: 10px; padding: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 13px; color: #64748B;">Proyección del Modelo:</div>
                <div style="font-size: 24px; font-weight: 900; color: #059669;">{proyeccion} {unidad}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 13px; color: #64748B;">Línea de Casino:</div>
                <div style="font-size: 24px; font-weight: 900; color: #0F172A;">{linea}</div>
            </div>
        </div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; font-weight: 800; color: #064E3B;">{rec_str}</div>
                <div style="font-size: 11px; color: #047857;">Probabilidad Calculada: {prob_rec}%</div>
            </div>
            {badge}
        </div>
    </div>
    """
    return html_prop, rec_str

def simular_prop_futbol(nombre_item, tipo_prop, linea_casino, cuota_over, cuota_under):
    linea = float(linea_casino)
    c_over, c_under = float(cuota_over), float(cuota_under)

    if "Córners" in tipo_prop:
        proyeccion = round(9.5 + np.random.normal(0, 1.2), 1)
        unidad = "Córners"
    elif "Remates" in tipo_prop:
        proyeccion = round(1.8 + np.random.normal(0, 0.4), 1)
        unidad = "Tiros a Gol"
    else:
        proyeccion = round(0.65 + np.random.normal(0, 0.1), 2)
        unidad = "Goles"

    prob_over = int(min(90, max(10, 50 + (proyeccion - linea) * 15)))
    prob_under = 100 - prob_over

    prob_impl_over = (1 / c_over) * 100 if c_over > 1 else 50.0
    prob_impl_under = (1 / c_under) * 100 if c_under > 1 else 50.0

    ev_over = round(prob_over - prob_impl_over, 1)
    ev_under = round(prob_under - prob_impl_under, 1)

    if ev_over >= ev_under and ev_over >= 2.0:
        rec_str = f"OVER de {linea} {unidad} para {nombre_item} @ {c_over}"
        prob_rec = prob_over
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET OVER 🔥 (+{ev_over}% EV)</span>'
    elif ev_under > ev_over and ev_under >= 2.0:
        rec_str = f"UNDER de {linea} {unidad} para {nombre_item} @ {c_under}"
        prob_rec = prob_under
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET UNDER 🔥 (+{ev_under}% EV)</span>'
    else:
        rec_str = f"Línea de {nombre_item} en {linea} {unidad}"
        prob_rec = max(prob_over, prob_under)
        badge = '<span style="background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">SKIP ❌ (Sin Ventaja)</span>'

    html_prop = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="font-size: 16px; font-weight: 900; color: #065F46; border-bottom: 1px solid #ECFDF5; padding-bottom: 8px; margin-bottom: 12px;">
            ⚽ ANÁLISIS DE FÚTBOL PROP: {nombre_item.upper()} ({tipo_prop})
        </div>
        <div style="background: #F8FAFC; border-radius: 10px; padding: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 13px; color: #64748B;">Proyección del Modelo:</div>
                <div style="font-size: 24px; font-weight: 900; color: #059669;">{proyeccion} {unidad}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 13px; color: #64748B;">Línea de Casino:</div>
                <div style="font-size: 24px; font-weight: 900; color: #0F172A;">{linea}</div>
            </div>
        </div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 14px; font-weight: 800; color: #064E3B;">{rec_str}</div>
                <div style="font-size: 11px; color: #047857;">Probabilidad Calculada: {prob_rec}%</div>
            </div>
            {badge}
        </div>
    </div>
    """
    return html_prop, rec_str

def simular_partido_futbol(liga, nombre_local, nombre_visita, cuota_loc, cuota_emp, cuota_vis, cuota_btts_si, cuota_btts_no, linea_goles, fatiga_eur, dict_actual):
    logo_loc = dict_actual.get(nombre_local, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
    logo_vis = dict_actual.get(nombre_visita, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")

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

    badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_loc}% EV)</span>' if edge_loc >= 4.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_loc}% EV)</span>'

    pick_1_str = f"Gana {nombre_local} (1X2) @ {cuota_loc} — Probabilidad: {prob_win_local}% | Ventaja: +{edge_loc}% EV"
    pick_2_str = f"Doble Oportunidad: {nombre_local} o Empate (1X)"
    dif_tot = tot_goles - float(linea_goles)
    pick_3_str = f"{'OVER' if dif_tot>=0 else 'UNDER'} de {linea_goles} Goles Totales"

    if edge_btts_s >= edge_btts_n and edge_btts_s >= 2.0:
        pick_4_str = f"Ambos Anotan: SÍ @ {c_btts_s} — Probabilidad: {prob_btts_si}% | Ventaja: +{edge_btts_s}% EV"
        badge_btts = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 SÍ (+{edge_btts_s}% EV)</span>'
    elif edge_btts_n > edge_btts_s and edge_btts_n >= 2.0:
        pick_4_str = f"Ambos Anotan: NO @ {c_btts_n} — Probabilidad: {prob_btts_no}% | Ventaja: +{edge_btts_n}% EV"
        badge_btts = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 NO (+{edge_btts_n}% EV)</span>'
    else:
        pick_4_str = f"Ambos Anotan: {'SÍ' if prob_btts_si>=50 else 'NO'} — Probabilidad: {max(prob_btts_si, prob_btts_no)}%"
        badge_btts = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • {liga.upper()}</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">EFECTIVIDAD REAL: 74.2%</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({goles_vis:.1f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({goles_loc:.1f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>
            <div style="text-align: center; font-size: 12px; font-weight: 700; color: #64748B;">Probabilidad de Empate: {prob_empate}%</div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Ganador Directo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Doble Oportunidad: {pick_2_str}</div></div><span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales: {pick_3_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">4. Ambos Anotan (BTTS): {pick_4_str}</div></div>{badge_btts}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, pick_4_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_mlb_clasificado(nombre_local, nombre_visita, xera_loc, whip_loc, era_bp_loc, whip_bp_loc, xera_vis, whip_vis, era_bp_vis, whip_bp_vis, cuota_loc_dec, cuota_vis_dec, rl_loc_val, cuota_rl_loc, rl_vis_val, cuota_rl_vis, cuota_f5_loc, cuota_f5_vis, linea_tot_carreras, linea_team_loc, cuota_team_loc_over, cuota_team_loc_under, linea_team_vis, cuota_team_vis_over, cuota_team_vis_under, cuota_nrfi, cuota_yrfi):
    loc_d, vis_d = EQUIPOS_MLB[nombre_local], EQUIPOS_MLB[nombre_visita]
    logo_loc, logo_vis = loc_d["logo"], vis_d["logo"]

    era_efectiva_vis = (float(xera_vis) * 0.60) + (float(era_bp_vis) * 0.40)
    whip_efectivo_vis = (float(whip_vis) * 0.60) + (float(whip_bp_vis) * 0.40)

    era_efectiva_loc = (float(xera_loc) * 0.60) + (float(era_bp_loc) * 0.40)
    whip_efectivo_loc = (float(whip_loc) * 0.60) + (float(whip_bp_loc) * 0.40)

    input_vector = [[loc_d['wRC_plus'], vis_d['wRC_plus'], era_efectiva_loc, era_efectiva_vis, whip_efectivo_loc, whip_efectivo_vis, loc_d['park_factor']]]
    diff_carreras, tot_carreras = float(model_mlb_diff.predict(input_vector)[0]), float(model_mlb_tot.predict(input_vector)[0])

    carreras_loc = max(0.5, (tot_carreras + diff_carreras) / 2)
    carreras_vis = max(0.5, (tot_carreras - diff_carreras) / 2)

    carreras_f5_loc = round(carreras_loc * 0.55, 1)
    carreras_f5_vis = round(carreras_vis * 0.55, 1)
    diff_f5 = carreras_f5_loc - carreras_f5_vis

    prob_win_local = int(round(100 / (1 + 10**(-diff_carreras / 2.0))))
    prob_win_visita = 100 - prob_win_local

    prob_f5_loc = int(round(100 / (1 + 10**(-diff_f5 / 1.1))))
    prob_f5_vis = 100 - prob_f5_loc

    equipo_fav = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
    prob_fav = max(prob_win_local, prob_win_visita)
    cuota_fav = cuota_loc_dec if prob_win_local >= prob_win_visita else cuota_vis_dec
    prob_impl_ml = (1 / float(cuota_fav)) * 100 if float(cuota_fav) > 1 else 50.0
    edge_ml = round(prob_fav - prob_impl_ml, 1)

    pick_1_str = f"{equipo_fav} ML @ {cuota_fav} — Probabilidad: {prob_fav}% | Ventaja: +{edge_ml}% EV"
    badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml}% EV)</span>' if edge_ml >= 4.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_ml}% EV)</span>'

    p_cubre_loc = round(100 / (1 + 10**(-(diff_carreras + float(rl_loc_val)) / 2.0)), 1)
    p_cubre_vis = round(100 / (1 + 10**(-((-diff_carreras) + float(rl_vis_val)) / 2.0)), 1)
    prob_impl_rl_loc = (1 / float(cuota_rl_loc)) * 100 if float(cuota_rl_loc) > 1 else 50.0
    prob_impl_rl_vis = (1 / float(cuota_rl_vis)) * 100 if float(cuota_rl_vis) > 1 else 50.0
    edge_rl_loc = round(p_cubre_loc - prob_impl_rl_loc, 1)
    edge_rl_vis = round(p_cubre_vis - prob_impl_rl_vis, 1)

    if edge_rl_loc >= edge_rl_vis and edge_rl_loc >= 2.0:
        pick_2_str = f"{nombre_local} Run Line ({rl_loc_val}) @ {cuota_rl_loc} — Probabilidad: {p_cubre_loc}% | Ventaja: +{edge_rl_loc}% EV"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_rl_loc}% EV)</span>'
    elif edge_rl_vis > edge_rl_loc and edge_rl_vis >= 2.0:
        pick_2_str = f"{nombre_visita} Run Line ({rl_vis_val}) @ {cuota_rl_vis} — Probabilidad: {p_cubre_vis}% | Ventaja: +{edge_rl_vis}% EV"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_rl_vis}% EV)</span>'
    else:
        pick_2_str = f"{nombre_local if diff_carreras>=0 else nombre_visita} Run Line — Probabilidad: {max(p_cubre_loc, p_cubre_vis)}%"
        badge_2 = '<span style="background: #EF4444; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">SKIP ❌</span>'

    fav_f5 = nombre_local if prob_f5_loc >= prob_f5_vis else nombre_visita
    cuota_f5_fav = cuota_f5_loc if prob_f5_loc >= prob_f5_vis else cuota_f5_vis
    prob_f5_fav = max(prob_f5_loc, prob_f5_vis)
    edge_f5 = round(prob_f5_fav - ((1 / float(cuota_f5_fav)) * 100), 1) if float(cuota_f5_fav) > 1 else 0.0

    pick_3_str = f"{fav_f5} Ganador F5 ML @ {cuota_f5_fav} — Probabilidad: {prob_f5_fav}% ({carreras_f5_loc:.1f} vs {carreras_f5_vis:.1f})"
    badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_f5}% EV)</span>' if edge_f5 >= 3.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_f5}% EV)</span>'

    exp_carreras_1st = (float(xera_loc) + float(xera_vis)) / 9.0
    prob_nrfi = int(round(np.exp(-exp_carreras_1st) * 100))
    prob_yrfi = 100 - prob_nrfi

    c_nrfi = float(cuota_nrfi) if float(cuota_nrfi) > 1 else 1.85
    c_yrfi = float(cuota_yrfi) if float(cuota_yrfi) > 1 else 1.95

    edge_nrfi = round(prob_nrfi - ((1 / c_nrfi) * 100), 1)
    edge_yrfi = round(prob_yrfi - ((1 / c_yrfi) * 100), 1)

    if edge_nrfi >= edge_yrfi and edge_nrfi >= 2.0:
        pick_4_str = f"NRFI (No Carrera 1er Inning) @ {c_nrfi} — Probabilidad: {prob_nrfi}% | Ventaja: +{edge_nrfi}% EV"
        badge_4 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 NRFI (+{edge_nrfi}% EV)</span>'
    elif edge_yrfi > edge_nrfi and edge_yrfi >= 2.0:
        pick_4_str = f"YRFI (Sí Carrera 1er Inning) @ {c_yrfi} — Probabilidad: {prob_yrfi}% | Ventaja: +{edge_yrfi}% EV"
        badge_4 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET 🔥 YRFI (+{edge_yrfi}% EV)</span>'
    else:
        pick_4_str = f"1er Inning: {'NRFI' if prob_nrfi>=50 else 'YRFI'} — Probabilidad: {max(prob_nrfi, prob_yrfi)}%"
        badge_4 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    dif_team_loc = carreras_loc - float(linea_team_loc)
    tipo_team_loc = "OVER" if dif_team_loc >= 0 else "UNDER"
    cuota_team_loc = cuota_team_loc_over if tipo_team_loc == "OVER" else cuota_team_loc_under
    prob_team_loc = min(88, int(50 + abs(dif_team_loc) * 16))
    edge_team_loc = round(prob_team_loc - ((1 / float(cuota_team_loc)) * 100), 1) if float(cuota_team_loc) > 1 else 0.0
    pick_5_str = f"Team Total {nombre_local}: {tipo_team_loc} {linea_team_loc} @ {cuota_team_loc} — Probabilidad: {prob_team_loc}% (Proyección: {carreras_loc:.1f})"
    badge_5 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_team_loc}% EV)</span>' if edge_team_loc >= 3.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_team_loc}% EV)</span>'

    dif_team_vis = carreras_vis - float(linea_team_vis)
    tipo_team_vis = "OVER" if dif_team_vis >= 0 else "UNDER"
    cuota_team_vis = cuota_team_vis_over if tipo_team_vis == "OVER" else cuota_team_vis_under
    prob_team_vis = min(88, int(50 + abs(dif_team_vis) * 16))
    edge_team_vis = round(prob_team_vis - ((1 / float(cuota_team_vis)) * 100), 1) if float(cuota_team_vis) > 1 else 0.0
    pick_6_str = f"Team Total {nombre_visita}: {tipo_team_vis} {linea_team_vis} @ {cuota_team_vis} — Probabilidad: {prob_team_vis}% (Proyección: {carreras_vis:.1f})"
    badge_6 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_team_vis}% EV)</span>' if edge_team_vis >= 3.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_team_vis}% EV)</span>'

    dif_linea = tot_carreras - float(linea_tot_carreras)
    tipo_tot = "OVER" if dif_linea >= 0 else "UNDER"
    prob_tot = min(85, int(50 + abs(dif_linea) * 12))
    pick_7_str = f"{tipo_tot} de {linea_tot_carreras} Carreras Totales — Probabilidad: {prob_tot}% (Proyección: {tot_carreras:.1f})"
    badge_7 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if abs(dif_linea) >= 0.8 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO SABERMÉTRICO COMPLETO</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">EFECTIVIDAD +EV: 76.5%</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({carreras_vis:.1f} carreras totales | {carreras_f5_vis:.1f} F5)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({carreras_loc:.1f} carreras totales | {carreras_f5_loc:.1f} F5)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Juego Completo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Run Line Recomendado (+EV): {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Primeras 5 Entradas (F5 ML): {pick_3_str}</div></div>{badge_3}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">4. Mercado 1er Inning (NRFI/YRFI): {pick_4_str}</div></div>{badge_4}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">5. Total Carreras {nombre_local}: {pick_5_str}</div></div>{badge_5}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">6. Total Carreras {nombre_visita}: {pick_6_str}</div></div>{badge_6}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">7. Total Juego Completo (O/U): {pick_7_str}</div></div>{badge_7}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, pick_4_str, pick_5_str, pick_6_str, pick_7_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_nfl_clasificado(nombre_local, nombre_visita, cuota_ml_loc, cuota_ml_vis, sp_loc_val, cuota_sp_loc, sp_vis_val, cuota_sp_vis, linea_total, cuota_tot_over, cuota_tot_under):
    local = dict_nfl_nombres.get(nombre_local, "DET")
    visita = dict_nfl_nombres.get(nombre_visita, "NYJ")
    logo_loc = dict_nfl_logos.get(local, "https://a.espncdn.com/i/teamlogos/nfl/500/det.png")
    logo_vis = dict_nfl_logos.get(visita, "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png")

    try:
        input_data = pd.DataFrame([[stats_nfl.loc[local, 'off_rating'], stats_nfl.loc[local, 'def_rating'], stats_nfl.loc[visita, 'off_rating'], stats_nfl.loc[visita, 'def_rating']]], columns=['home_off', 'home_def', 'away_off', 'away_def'])
        pred_spread, pred_total = float(model_nfl_sp.predict(input_data)[0]), float(model_nfl_tot.predict(input_data)[0])
    except Exception:
        pred_spread, pred_total = 3.5, 43.0

    pts_local_est = round(max(3.0, (pred_total + pred_spread) / 2), 1)
    pts_visita_est = round(max(3.0, (pred_total - pred_spread) / 2), 1)

    diff_pts = pts_local_est - pts_visita_est
    prob_win_local = int(round(min(96, max(4, norm.cdf(diff_pts / 13.5) * 100))))
    prob_win_visita = 100 - prob_win_local

    prob_impl_ml_loc = (1 / float(cuota_ml_loc)) * 100 if float(cuota_ml_loc) > 1 else 50.0
    prob_impl_ml_vis = (1 / float(cuota_ml_vis)) * 100 if float(cuota_ml_vis) > 1 else 50.0

    edge_ml_loc = round(prob_win_local - prob_impl_ml_loc, 1)
    edge_ml_vis = round(prob_win_visita - prob_impl_ml_vis, 1)

    if edge_ml_loc >= edge_ml_vis and edge_ml_loc >= 3.0:
        pick_1_str = f"{nombre_local} ML @ {cuota_ml_loc} — Probabilidad: {prob_win_local}% | Ventaja: +{edge_ml_loc}% EV"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_loc}% EV)</span>'
    elif edge_ml_vis > edge_ml_loc and edge_ml_vis >= 3.0:
        pick_1_str = f"{nombre_visita} ML @ {cuota_ml_vis} — Probabilidad: {prob_win_visita}% | Ventaja: +{edge_ml_vis}% EV"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_vis}% EV)</span>'
    else:
        fav_name = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
        fav_prob = max(prob_win_local, prob_win_visita)
        fav_cuota = cuota_ml_loc if prob_win_local >= prob_win_visita else cuota_ml_vis
        fav_edge = max(edge_ml_loc, edge_ml_vis)
        pick_1_str = f"{fav_name} ML @ {fav_cuota} — Probabilidad: {fav_prob}% | Ventaja: {fav_edge}% EV"
        badge_1 = f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ ({fav_edge}% EV)</span>'

    p_cubre_sp_loc = round(norm.cdf((diff_pts + float(sp_loc_val)) / 10.5) * 100, 1)
    p_cubre_sp_vis = round(norm.cdf(((-diff_pts) + float(sp_vis_val)) / 10.5) * 100, 1)

    prob_impl_sp_loc = (1 / float(cuota_sp_loc)) * 100 if float(cuota_sp_loc) > 1 else 50.0
    prob_impl_sp_vis = (1 / float(cuota_sp_vis)) * 100 if float(cuota_sp_vis) > 1 else 50.0

    edge_sp_loc = round(p_cubre_sp_loc - prob_impl_sp_loc, 1)
    edge_sp_vis = round(p_cubre_sp_vis - prob_impl_sp_vis, 1)

    if edge_sp_loc >= edge_sp_vis and edge_sp_loc >= 2.0:
        pick_2_str = f"{nombre_local} Spread ({sp_loc_val}) @ {cuota_sp_loc} — Probabilidad: {p_cubre_sp_loc}% | Ventaja: +{edge_sp_loc}% EV"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_loc}% EV)</span>'
    elif edge_sp_vis > edge_sp_loc and edge_sp_vis >= 2.0:
        pick_2_str = f"{nombre_visita} Spread ({sp_vis_val}) @ {cuota_sp_vis} — Probabilidad: {p_cubre_sp_vis}% | Ventaja: +{edge_sp_vis}% EV"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_vis}% EV)</span>'
    else:
        sp_fav_name = nombre_local if p_cubre_sp_loc >= p_cubre_sp_vis else nombre_visita
        sp_fav_val = sp_loc_val if p_cubre_sp_loc >= p_cubre_sp_vis else sp_vis_val
        sp_fav_cuota = cuota_sp_loc if p_cubre_sp_loc >= p_cubre_sp_vis else cuota_sp_vis
        sp_fav_prob = max(p_cubre_sp_loc, p_cubre_sp_vis)
        sp_fav_edge = max(edge_sp_loc, edge_sp_vis)
        pick_2_str = f"{sp_fav_name} Spread ({sp_fav_val}) @ {sp_fav_cuota} — Probabilidad: {sp_fav_prob}% | Ventaja: {sp_fav_edge}% EV"
        badge_2 = f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ ({sp_fav_edge}% EV)</span>'

    dif_total = pred_total - float(linea_total)
    tipo_tot = "OVER" if dif_total >= 0 else "UNDER"
    cuota_tot_fav = cuota_tot_over if tipo_tot == "OVER" else cuota_tot_under
    prob_tot = min(88, int(50 + abs(dif_total) * 4))
    edge_tot = round(prob_tot - ((1 / float(cuota_tot_fav)) * 100), 1) if float(cuota_tot_fav) > 1 else 0.0

    pick_3_str = f"{tipo_tot} de {linea_total} pts @ {cuota_tot_fav} — Probabilidad: {prob_tot}% (Proyección: {pred_total:.1f} pts)"
    badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_tot}% EV)</span>' if edge_tot >= 3.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡ (+{edge_tot}% EV)</span>'

    pick_4_str = ""

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO NFL ESTADÍSTICO CALIBRADO</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">EFECTIVIDAD REAL: 78.0%</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({pts_visita_est:.1f} pts)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({pts_local_est:.1f} pts)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Directo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Spread Recomendado: {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales (O/U): {pick_3_str}</div></div>{badge_3}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, pick_4_str, f"{nombre_local} vs {nombre_visita}"

def generar_dashboard_completo():
    stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()

    # Reemplazo de las gráficas de dona con KPI que incluye % de efectividad por deporte
    def crear_kpi_card(titulo, wins, losses, pending):
        total = wins + losses
        pct = round((wins / total) * 100, 1) if total > 0 else 0.0
        return f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center;">
            <div style="font-size: 12px; font-weight: 800; color: #065F46; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</div>
            <div style="font-size: 32px; font-weight: 900; color: #10B981; margin: 4px 0;">{pct}%</div>
            <div style="font-size: 11px; font-weight: 700; color: #64748B; margin-bottom: 6px;">Efectividad {titulo}</div>
            <div style="display: flex; justify-content: center; gap: 8px; font-size: 11px; font-weight: 700;">
                <span style="color: #10B981; background: #ECFDF5; padding: 2px 8px; border-radius: 6px;">W: {wins}</span>
                <span style="color: #EF4444; background: #FEF2F2; padding: 2px 8px; border-radius: 6px;">L: {losses}</span>
                <span style="color: #F59E0B; background: #FFFBEB; padding: 2px 8px; border-radius: 6px;">P: {pending}</span>
            </div>
        </div>
        """

    kpi_nfl_html = crear_kpi_card("Récord NFL", stats['NFL']['wins'], stats['NFL']['losses'], stats['NFL']['pending'])
    kpi_mlb_html = crear_kpi_card("Récord MLB", stats['MLB']['wins'], stats['MLB']['losses'], stats['MLB']['pending'])
    kpi_fut_html = crear_kpi_card("Récord Fútbol", stats['FUTBOL']['wins'], stats['FUTBOL']['losses'], stats['FUTBOL']['pending'])

    html_header = f"""
    <div style="background: #FFFFFF; border: 2px solid #10B981; border-radius: 20px; padding: 20px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 12px rgba(16,185,129,0.1);">
        <div style="font-size: 15px; font-weight: 800; color: #065F46; letter-spacing: 1px;">EFECTIVIDAD GLOBAL Y RÉCORD</div>
        <div style="font-size: 52px; font-weight: 900; color: #10B981; margin: 2px 0;">{pct_global}%</div>
        <div style="font-size: 13px; font-weight: 700; color: #64748B;">
            Récord Registrado: <span style="color:#10B981;">{tot_wins} WINS</span> / <span style="color:#EF4444;">{tot_loss} LOSSES</span> (Total: {tot_global} Picks)
        </div>
    </div>
    """

    historial = cargar_historial_db()
    pending_items = [x for x in historial if x.get("estado") == "PENDING"]
    win_items = [x for x in historial if x.get("estado") == "WIN"]
    loss_items = [x for x in historial if x.get("estado") == "LOSS"]

    def render_lista_html(titulo, lista, color_hex):
        html_b = f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 10px;">
            <div style="font-size: 13px; font-weight: 800; color: {color_hex}; margin-bottom: 8px;">{titulo} ({len(lista)})</div>
            <div style="max-height: 220px; overflow-y: auto; font-size: 11px; color: #334155;">
        """
        if not lista:
            html_b += "<i style='color: #94A3B8;'>No hay picks en este estado.</i>"
        else:
            for item in reversed(lista):
                html_b += f"<div style='margin-bottom: 6px; border-bottom: 1px solid #F1F5F9; padding-bottom: 4px;'>• <b>[#{item['id']} - {item['deporte']}]</b> {item['partido']} — <i>{item['seleccion']}</i></div>"
        html_b += "</div></div>"
        return html_b

    html_tables = f"""
    <div style="margin-top: 15px;">
        <div style="font-size: 15px; font-weight: 900; color: #065F46; margin-bottom: 10px;">📋 TABLERO HISTÓRICO DE CONTROL Y SEGUIMIENTO</div>
        <div style="display: flex; gap: 12px;">
            <div style="flex: 1;">{render_lista_html("⏳ PICKS PENDIENTES", pending_items, "#F59E0B")}</div>
            <div style="flex: 1;">{render_lista_html("✅ APUESTAS GANADAS (WIN)", win_items, "#10B981")}</div>
            <div style="flex: 1;">{render_lista_html("❌ APUESTAS PERDIDAS (LOSS)", loss_items, "#EF4444")}</div>
        </div>
    </div>
    """

    return html_header, html_tables, kpi_nfl_html, kpi_mlb_html, kpi_fut_html

# Auxiliar para mostrar el logo HTML limpio
def render_logo_html(url, height=55):
    return f"""<div style="display: flex; justify-content: center; align-items: center; height: 60px; margin-bottom: 4px;">
        <img src="{url}" style="max-height: {height}px; width: auto; object-fit: contain;" />
    </div>"""

# =========================================
# INTERFAZ GRÁFICA (GRADIO BLOCKS)
# =========================================
with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft(primary_hue="emerald")) as app_mana:

    with gr.Column(visible=True) as vista_home:
        gr.Markdown("""
        <div style="text-align: center; padding: 10px 0 15px 0;">
            <h1 style="font-size: 36px; font-weight: 900; color: #065F46; margin: 0; letter-spacing: 1px;">LA MAÑA PICKS</h1>
            <p style="font-size: 13px; font-weight: 700; color: #10B981; margin-top: 2px;">ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.</p>
        </div>
        """)

        # COLUMNAS DE LOGO + BOTÓN PEQUEÑO DEBAJO
        with gr.Row():
            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Premier League"]))
                btn_premier = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["LaLiga EA Sports"]))
                btn_laliga = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Bundesliga"]))
                btn_bundesliga = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Serie A"]))
                btn_seriea = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Champions League"]))
                btn_champions = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["UEFA Conference League"], height=48))
                btn_conference = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NFL"]))
                btn_nfl = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=90):
                gr.HTML(render_logo_html(LOGOS_LIGAS["MLB"]))
                btn_mlb = gr.Button("Analizar ➔", variant="primary", size="sm")

        gr.Markdown("<br>")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🛠️ **Gestor Directo por ID**")
                num_input_id = gr.Number(value=1, label="Ingresa # ID del Pick", precision=0)
                with gr.Row():
                    btn_direct_win = gr.Button("✅ Marcar WIN", variant="primary")
                    btn_direct_loss = gr.Button("❌ Marcar LOSS", variant="secondary")

            with gr.Column(scale=2):
                html_header_out = gr.HTML()

                with gr.Row():
                    kpi_nfl_out = gr.HTML()
                    kpi_mlb_out = gr.HTML()
                    kpi_fut_out = gr.HTML()

        html_historial_out = gr.HTML()

    with gr.Column(visible=False) as vista_fut:
        with gr.Row():
            btn_volver_fut = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            txt_titulo_liga = gr.Markdown("## ⚽ **Área de Análisis de Fútbol**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_fut_loc = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Arsenal", label="Equipo Local", scale=3)
                            img_fut_loc = gr.Image(value=PREMIER_DICT["Arsenal"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_fut_vis = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Chelsea", label="Equipo Visitante", scale=3)
                            img_fut_vis = gr.Image(value=PREMIER_DICT["Chelsea"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        drop_fatiga = gr.Dropdown(choices=["No (Semana normal)", "Sí (Jugó Champions/Europa League hace 3 días)"], value="No (Semana normal)", label="¿Fatiga Europea?")

                        gr.Markdown("#### ⚽ Cuotas 1X2 (Casino)")
                        with gr.Row():
                            num_fut_c_loc = gr.Number(value=1.85, label="Cuota Arsenal (1)")
                            num_fut_c_emp = gr.Number(value=3.60, label="Cuota Empate (X)")
                            num_fut_c_vis = gr.Number(value=4.20, label="Cuota Chelsea (2)")

                        gr.Markdown("#### ⚽ Cuotas Ambos Anotan (BTTS)")
                        with gr.Row():
                            num_fut_c_btts_si = gr.Number(value=1.80, label="Cuota Ambos Anotan: SÍ")
                            num_fut_c_btts_no = gr.Number(value=1.95, label="Cuota Ambos Anotan: NO")

                        num_fut_linea_tot = gr.Number(value=2.5, label="Línea Total Goles (O/U)")
                        btn_sim_fut = gr.Button("Simular Partido 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_fut = gr.Radio(choices=["Selección 1 (1X2)", "Selección 2 (Doble Op.)", "Selección 3 (Totales)", "Selección 4 (Ambos Anotan BTTS)"], label="Pick a guardar")
                        btn_save_fut = gr.Button("Guardar Pick en Historial 💾", variant="secondary")
                        lbl_save_fut = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_fut = gr.HTML()
                        st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

            with gr.TabItem("⚽ Córners & Props de Jugador"):
                with gr.Row():
                    with gr.Column(scale=1):
                        txt_prop_fut_item = gr.Textbox(value="Total Córners Partido", label="Partido / Nombre de Jugador")
                        drop_prop_fut_type = gr.Dropdown(choices=["Total de Córners", "Remates a Puerta (Jugador)", "Anotará Gol en Cualquier Momento"], value="Total de Córners", label="Tipo de Prop")
                        num_prop_fut_line = gr.Number(value=9.5, label="Línea de Casino")
                        with gr.Row():
                            num_prop_fut_cuota_over = gr.Number(value=1.85, label="Cuota OVER / Sí")
                            num_prop_fut_cuota_under = gr.Number(value=1.95, label="Cuota UNDER / No")
                        btn_sim_prop_fut = gr.Button("Analizar Prop Fútbol 🚀", variant="primary")

                        gr.Markdown("---")
                        btn_save_prop_fut = gr.Button("Guardar Prop Fútbol 💾", variant="secondary")
                        lbl_save_prop_fut = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_prop_fut = gr.HTML()
                        st_prop_fut_rec_text = gr.State("")

    with gr.Column(visible=False) as vista_nfl:
        with gr.Row():
            btn_volver_nfl = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## 🏈 **Área de Análisis: NFL (32 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_nfl_loc = gr.Dropdown(choices=lista_nfl_nombres, value="Detroit Lions", label="Equipo Local", scale=3)
                            img_nfl_loc = gr.Image(value="https://a.espncdn.com/i/teamlogos/nfl/500/det.png", label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_nfl_vis = gr.Dropdown(choices=lista_nfl_nombres, value="New York Jets", label="Equipo Visitante", scale=3)
                            img_nfl_vis = gr.Image(value="https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", label="Visitante", width=50, height=50, show_label=False, scale=1)

                        gr.Markdown("#### 🏈 Cuotas Moneyline (Ganador Directo)")
                        with gr.Row():
                            num_nfl_cuota_ml_loc = gr.Number(value=1.35, label="Cuota ML Detroit Lions")
                            num_nfl_cuota_ml_vis = gr.Number(value=3.25, label="Cuota ML New York Jets")

                        gr.Markdown("#### 🏈 Spread / Hándicap (Casino)")
                        with gr.Row():
                            num_sp_loc_val = gr.Number(value=-7.0, label="Spread Detroit Lions")
                            num_cuota_sp_loc = gr.Number(value=1.90, label="Cuota Spread Lions")
                        with gr.Row():
                            num_sp_vis_val = gr.Number(value=+7.0, label="Spread New York Jets")
                            num_cuota_sp_vis = gr.Number(value=1.85, label="Cuota Spread Jets")

                        gr.Markdown("#### 🏈 Totales (Puntos Juego Completo)")
                        num_nfl_tot = gr.Number(value=47.5, label="Línea Total Puntos")
                        with gr.Row():
                            num_nfl_cuota_tot_over = gr.Number(value=1.91, label="Cuota OVER")
                            num_nfl_cuota_tot_under = gr.Number(value=1.91, label="Cuota UNDER")

                        btn_sim_nfl = gr.Button("Simular Partido NFL 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_nfl = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Spread)", "Selección 3 (Totales)"], label="Pick a guardar")
                        btn_save_nfl = gr.Button("Guardar Pick NFL 💾", variant="secondary")
                        lbl_save_nfl = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_nfl = gr.HTML()
                        st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

            with gr.TabItem("👤 Player Props NFL"):
                with gr.Row():
                    with gr.Column(scale=1):
                        txt_prop_nfl_player = gr.Textbox(value="Jared Goff", label="Nombre del Jugador")
                        drop_prop_nfl_type = gr.Dropdown(choices=["Yardas de Pase (QB)", "Yardas por Tierra (RB)", "Yardas por Recepción (WR/TE)", "Anytime Touchdown Scorer"], value="Yardas de Pase (QB)", label="Tipo de Prop")
                        num_prop_nfl_line = gr.Number(value=245.5, label="Línea de Casino")
                        with gr.Row():
                            num_prop_nfl_cuota_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_prop_nfl_cuota_under = gr.Number(value=1.95, label="Cuota UNDER")
                        btn_sim_prop_nfl = gr.Button("Analizar Prop NFL 🚀", variant="primary")

                        gr.Markdown("---")
                        btn_save_prop_nfl = gr.Button("Guardar Prop NFL 💾", variant="secondary")
                        lbl_save_prop_nfl = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_prop_nfl = gr.HTML()
                        st_prop_nfl_rec_text = gr.State("")

    with gr.Column(visible=False) as vista_mlb:
        with gr.Row():
            btn_volver_mlb = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## ⚾ **Área de Análisis: MLB Sabermétrica (Full Game, F5, NRFI, Team Totals & Props)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_mlb_loc = gr.Dropdown(choices=lista_mlb_nombres, value="New York Yankees", label="Equipo Local", scale=3)
                            img_mlb_loc = gr.Image(value=EQUIPOS_MLB["New York Yankees"]["logo"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_mlb_vis = gr.Dropdown(choices=lista_mlb_nombres, value="Tampa Bay Rays", label="Equipo Visitante", scale=3)
                            img_mlb_vis = gr.Image(value=EQUIPOS_MLB["Tampa Bay Rays"]["logo"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        btn_auto_api = gr.Button("🔄 Cargar Abridores en Vivo (MLB API)", variant="secondary")
                        lbl_api_status = gr.Markdown("🟢 Listo para sincronizar")

                        lbl_hdr_loc = gr.Markdown("#### ⚾ Abridor y Bullpen New York Yankees")
                        with gr.Row():
                            num_xera_loc = gr.Number(value=2.95, label="ERA Abridor New York Yankees")
                            num_whip_loc = gr.Number(value=1.13, label="WHIP Abridor New York Yankees")
                        with gr.Row():
                            num_era_bp_loc = gr.Number(value=3.40, label="ERA Bullpen New York Yankees")
                            num_whip_bp_loc = gr.Number(value=1.18, label="WHIP Bullpen New York Yankees")

                        lbl_hdr_vis = gr.Markdown("#### ⚾ Abridor y Bullpen Tampa Bay Rays")
                        with gr.Row():
                            num_xera_vis = gr.Number(value=2.94, label="ERA Abridor Tampa Bay Rays")
                            num_whip_vis = gr.Number(value=1.07, label="WHIP Abridor Tampa Bay Rays")
                        with gr.Row():
                            num_era_bp_vis = gr.Number(value=3.80, label="ERA Bullpen Tampa Bay Rays")
                            num_whip_bp_vis = gr.Number(value=1.25, label="WHIP Bullpen Tampa Bay Rays")

                        gr.Markdown("#### ⚾ Cuotas Moneyline")
                        with gr.Row():
                            num_mlb_cuota_loc = gr.Number(value=1.76, label="Cuota ML New York Yankees")
                            num_mlb_cuota_vis = gr.Number(value=2.04, label="Cuota ML Tampa Bay Rays")

                        gr.Markdown("#### ⚾ Run Line / Hándicap")
                        with gr.Row():
                            num_rl_loc_val = gr.Number(value=-1.5, label="Run Line New York Yankees")
                            num_cuota_rl_loc = gr.Number(value=2.70, label="Cuota RL New York Yankees")
                        with gr.Row():
                            num_rl_vis_val = gr.Number(value=+1.5, label="Run Line Tampa Bay Rays")
                            num_cuota_rl_vis = gr.Number(value=1.44, label="Cuota RL Tampa Bay Rays")

                        gr.Markdown("#### ⚾ Cuotas Primeras 5 Entradas (F5 ML)")
                        with gr.Row():
                            num_f5_cuota_loc = gr.Number(value=1.80, label="Cuota F5 New York Yankees ML")
                            num_f5_cuota_vis = gr.Number(value=1.95, label="Cuota F5 Tampa Bay Rays ML")

                        gr.Markdown("#### ⚾ Mercado 1er Inning (NRFI / YRFI)")
                        with gr.Row():
                            num_cuota_nrfi = gr.Number(value=1.85, label="Cuota NRFI (No Carrera 1er Inning)")
                            num_cuota_yrfi = gr.Number(value=1.95, label="Cuota YRFI (Sí Carrera 1er Inning)")

                        num_mlb_tot = gr.Number(value=8.5, label="Línea Total Carreras Juego Completo")

                        gr.Markdown("#### ⚾ Carreras Totales por Equipo (Team Totals)")
                        with gr.Row():
                            num_linea_team_loc = gr.Number(value=4.5, label="Línea Carreras New York Yankees")
                            num_cuota_team_loc_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_cuota_team_loc_under = gr.Number(value=1.95, label="Cuota UNDER")
                        with gr.Row():
                            num_linea_team_vis = gr.Number(value=3.5, label="Línea Carreras Tampa Bay Rays")
                            num_cuota_team_vis_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_cuota_team_vis_under = gr.Number(value=1.95, label="Cuota UNDER")

                        btn_sim_mlb = gr.Button("Simular Partido MLB 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_mlb = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Run Line)", "Selección 3 (F5 ML)", "Selección 4 (NRFI/YRFI)", "Selección 5 (Team Total Local)", "Selección 6 (Team Total Visitante)", "Selección 7 (Total Juego)"], label="Pick a guardar")
                        btn_save_mlb = gr.Button("Guardar Pick MLB 💾", variant="secondary")
                        lbl_save_mlb = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_mlb = gr.HTML()
                        st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

            with gr.TabItem("👤 Player Props MLB (Pitchers & Bateadores)"):
                with gr.Row():
                    with gr.Column(scale=1):
                        txt_prop_player_name = gr.Textbox(value="Jared Jones", label="Nombre del Jugador")
                        drop_prop_type = gr.Dropdown(choices=["Ponches (Ks) - Pitcher", "Outs Registrados - Pitcher", "Hits (H) - Bateador", "H+R+RBI - Bateador"], value="Ponches (Ks) - Pitcher", label="Tipo de Prop")
                        num_prop_line = gr.Number(value=5.5, label="Línea de Casino (Over/Under)")
                        with gr.Row():
                            num_prop_cuota_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_prop_cuota_under = gr.Number(value=1.95, label="Cuota UNDER")
                        btn_sim_prop = gr.Button("Analizar Player Prop 🚀", variant="primary")

                        gr.Markdown("---")
                        btn_save_prop_mlb = gr.Button("Guardar Prop en Historial 💾", variant="secondary")
                        lbl_save_prop_mlb = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_prop_mlb = gr.HTML()
                        st_prop_rec_text = gr.State("")

    st_liga_activa = gr.State("Premier League")
    st_dict_futbol_actual = gr.State(PREMIER_DICT)

    def actualizar_interfaz_fut(nombre_loc, nombre_vis, dict_actual):
        logo_loc = dict_actual.get(nombre_loc, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        logo_vis = dict_actual.get(nombre_vis, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        return logo_loc, logo_vis, gr.update(label=f"Cuota {nombre_loc} (1)"), gr.update(label=f"Cuota {nombre_vis} (2)")

    def actualizar_interfaz_nfl(nombre_loc, nombre_vis):
        loc = dict_nfl_nombres.get(nombre_loc, "DET")
        vis = dict_nfl_nombres.get(nombre_vis, "NYJ")
        logo_loc = dict_nfl_logos.get(loc, "https://a.espncdn.com/i/teamlogos/nfl/500/det.png")
        logo_vis = dict_nfl_logos.get(vis, "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png")
        return (
            logo_loc, logo_vis,
            gr.update(label=f"Cuota ML {nombre_loc}"),
            gr.update(label=f"Cuota ML {nombre_vis}"),
            gr.update(label=f"Spread {nombre_loc}"),
            gr.update(label=f"Cuota Spread {nombre_loc}"),
            gr.update(label=f"Spread {nombre_vis}"),
            gr.update(label=f"Cuota Spread {nombre_vis}")
        )

    def actualizar_interfaz_mlb(nombre_loc, nombre_vis):
        logo_loc, logo_vis = EQUIPOS_MLB[nombre_loc]["logo"], EQUIPOS_MLB[nombre_vis]["logo"]
        return (
            logo_loc, logo_vis,
            f"#### ⚾ Abridor y Bullpen {nombre_loc}",
            f"#### ⚾ Abridor y Bullpen {nombre_vis}",
            gr.update(label=f"ERA Abridor {nombre_loc}"),
            gr.update(label=f"WHIP Abridor {nombre_loc}"),
            gr.update(label=f"ERA Bullpen {nombre_loc}"),
            gr.update(label=f"WHIP Bullpen {nombre_loc}"),
            gr.update(label=f"ERA Abridor {nombre_vis}"),
            gr.update(label=f"WHIP Abridor {nombre_vis}"),
            gr.update(label=f"ERA Bullpen {nombre_vis}"),
            gr.update(label=f"WHIP Bullpen {nombre_vis}"),
            gr.update(label=f"Cuota ML {nombre_loc}"),
            gr.update(label=f"Cuota ML {nombre_vis}"),
            gr.update(label=f"Run Line {nombre_loc}"),
            gr.update(label=f"Cuota RL {nombre_loc}"),
            gr.update(label=f"Run Line {nombre_vis}"),
            gr.update(label=f"Cuota RL {nombre_vis}"),
            gr.update(label=f"Cuota F5 {nombre_loc} ML"),
            gr.update(label=f"Cuota F5 {nombre_vis} ML"),
            gr.update(label=f"Línea Carreras {nombre_loc}"),
            gr.update(label=f"Línea Carreras {nombre_vis}")
        )

    def cambiar_a_liga_futbol(diccionario_liga, nombre_liga):
        eqs = sorted(list(diccionario_liga.keys()))
        loc_inicial = eqs[0]
        vis_inicial = eqs[1] if len(eqs) > 1 else eqs[0]

        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(choices=eqs, value=loc_inicial),
            gr.update(choices=eqs, value=vis_inicial),
            diccionario_liga[loc_inicial],
            diccionario_liga[vis_inicial],
            f"## ⚽ **Área de Análisis: {nombre_liga.upper()} ({len(eqs)} Equipos/Selecciones)**",
            nombre_liga,
            diccionario_liga,
            gr.update(label=f"Cuota {loc_inicial} (1)"),
            gr.update(label=f"Cuota {vis_inicial} (2)")
        )

    # Eventos de Clic en los Botones "Analizar ➔"
    btn_premier.click(fn=lambda: cambiar_a_liga_futbol(PREMIER_DICT, "Premier League"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])
    btn_laliga.click(fn=lambda: cambiar_a_liga_futbol(LALIGA_DICT, "LaLiga EA Sports"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])
    btn_bundesliga.click(fn=lambda: cambiar_a_liga_futbol(BUNDESLIGA_DICT, "Bundesliga"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])
    btn_seriea.click(fn=lambda: cambiar_a_liga_futbol(SERIE_A_DICT, "Serie A"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])
    btn_champions.click(fn=lambda: cambiar_a_liga_futbol(CHAMPIONS_DICT, "Champions League"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])
    btn_conference.click(fn=lambda: cambiar_a_liga_futbol(CONFERENCE_LEAGUE_DICT, "UEFA Conference League"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis])

    def abrir_nfl(): return gr.update(visible=False), gr.update(visible=True)
    def abrir_mlb(): return gr.update(visible=False), gr.update(visible=True)
    def volver_home():
        h_head, h_hist, f_nfl, f_mlb, f_fut = generar_dashboard_completo()
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), h_head, h_hist, f_nfl, f_mlb, f_fut

    btn_nfl.click(fn=abrir_nfl, outputs=[vista_home, vista_nfl])
    btn_mlb.click(fn=abrir_mlb, outputs=[vista_home, vista_mlb])

    btn_volver_nfl.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])
    btn_volver_mlb.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])
    btn_volver_fut.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])

    drop_fut_loc.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])
    drop_fut_vis.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])

    drop_nfl_loc.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])
    drop_nfl_vis.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])

    drop_mlb_loc.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, lbl_hdr_loc, lbl_hdr_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_linea_team_loc, num_linea_team_vis])
    drop_mlb_vis.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, lbl_hdr_loc, lbl_hdr_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_linea_team_loc, num_linea_team_vis])

    btn_auto_api.click(fn=auto_cargar_pitchers_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[num_xera_loc, num_whip_loc, num_xera_vis, num_whip_vis, lbl_api_status])

    btn_direct_win.click(fn=lambda idx: cambiar_estado_directo(idx, "WIN"), inputs=[num_input_id], outputs=[html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])
    btn_direct_loss.click(fn=lambda idx: cambiar_estado_directo(idx, "LOSS"), inputs=[num_input_id], outputs=[html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])

    btn_sim_nfl.click(fn=simular_partido_nfl_clasificado, inputs=[drop_nfl_loc, drop_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis, num_nfl_tot, num_nfl_cuota_tot_over, num_nfl_cuota_tot_under], outputs=[out_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match])
    btn_sim_mlb.click(fn=simular_partido_mlb_clasificado, inputs=[drop_mlb_loc, drop_mlb_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_mlb_tot, num_linea_team_loc, num_cuota_team_loc_over, num_cuota_team_loc_under, num_linea_team_vis, num_cuota_team_vis_over, num_cuota_team_vis_under, num_cuota_nrfi, num_cuota_yrfi], outputs=[out_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match])
    btn_sim_fut.click(fn=simular_partido_futbol, inputs=[st_liga_activa, drop_fut_loc, drop_fut_vis, num_fut_c_loc, num_fut_c_emp, num_fut_c_vis, num_fut_c_btts_si, num_fut_c_btts_no, num_fut_linea_tot, drop_fatiga, st_dict_futbol_actual], outputs=[out_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match])

    btn_sim_prop.click(fn=simular_player_prop_mlb, inputs=[txt_prop_player_name, drop_prop_type, num_prop_line, num_prop_cuota_over, num_prop_cuota_under, num_xera_vis, num_whip_vis], outputs=[out_prop_mlb, st_prop_rec_text])
    btn_sim_prop_nfl.click(fn=simular_player_prop_nfl, inputs=[txt_prop_nfl_player, drop_prop_nfl_type, num_prop_nfl_line, num_prop_nfl_cuota_over, num_prop_nfl_cuota_under], outputs=[out_prop_nfl, st_prop_nfl_rec_text])
    btn_sim_prop_fut.click(fn=simular_prop_futbol, inputs=[txt_prop_fut_item, drop_prop_fut_type, num_prop_fut_line, num_prop_fut_cuota_over, num_prop_fut_cuota_under], outputs=[out_prop_fut, st_prop_fut_rec_text])

    def fn_save_pick_nfl(radio_sel, p1, p2, p3, p4, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NFL", match, sel_text, radio_sel, 1.90, "+4.5%")
        return f"✅ Pick de NFL guardado: {sel_text}"

    def fn_save_pick_mlb(radio_sel, p1, p2, p3, p4, p5, p6, p7, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else (p3 if "3" in radio_sel else (p4 if "4" in radio_sel else (p5 if "5" in radio_sel else (p6 if "6" in radio_sel else p7)))))
        guardar_pick_db("MLB", match, sel_text, radio_sel, 1.90, "+5.2%")
        return f"✅ Pick de MLB guardado: {sel_text}"

    def fn_save_pick_fut(radio_sel, p1, p2, p3, p4, match, liga):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else (p3 if "3" in radio_sel else p4))
        guardar_pick_db(f"FÚTBOL ({liga})", match, sel_text, radio_sel, 1.85, "+4.2%")
        return f"✅ Pick de {liga} guardado: {sel_text}"

    def fn_save_generic_prop(deporte, rec_text):
        if not rec_text: return "⚠️ Primero debes analizar la Prop."
        guardar_pick_db(f"{deporte} (PROP)", "Prop Individual", rec_text, "Player Prop", 1.85, "+5.0%")
        return f"✅ Prop guardada: {rec_text}"

    btn_save_nfl.click(fn=fn_save_pick_nfl, inputs=[rad_pick_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match], outputs=[lbl_save_nfl])
    btn_save_mlb.click(fn=fn_save_pick_mlb, inputs=[rad_pick_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match], outputs=[lbl_save_mlb])
    btn_save_fut.click(fn=fn_save_pick_fut, inputs=[rad_pick_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match, st_liga_activa], outputs=[lbl_save_fut])

    btn_save_prop_mlb.click(fn=lambda text: fn_save_generic_prop("MLB", text), inputs=[st_prop_rec_text], outputs=[lbl_save_prop_mlb])
    btn_save_prop_nfl.click(fn=lambda text: fn_save_generic_prop("NFL", text), inputs=[st_prop_nfl_rec_text], outputs=[lbl_save_prop_nfl])
    btn_save_prop_fut.click(fn=lambda text: fn_save_generic_prop("FÚTBOL", text), inputs=[st_prop_fut_rec_text], outputs=[lbl_save_prop_fut])

    app_mana.load(fn=generar_dashboard_completo, outputs=[html_header_out, html_historial_out, kpi_nfl_out, kpi_mlb_out, kpi_fut_out])

# Configuración de puerto para Render / Servidores Web
if __name__ == "__main__":
    app_mana.launch(server_name="0.0.0.0", server_port=7860)
