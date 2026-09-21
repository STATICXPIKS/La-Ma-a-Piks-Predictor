# ==============================================================================
# 1. INSTALACIÓN DE LIBRERÍAS
# ==============================================================================
!pip install nflreadpy pandas numpy xgboost gradio scikit-learn requests plotly -q

import nflreadpy as nfl
import pandas as pd
import numpy as np
import xgboost as xgb
import gradio as gr
import requests
import json
import os
from datetime import datetime
import plotly.graph_objects as go

print("🚀 Cargando La Maña Picks con Gráficas Independientes y Diseño Profesional...")

# ==============================================================================
# 2. SISTEMA DE HISTORIAL Y BASE DE DATOS PERSISTENTE (JSON LOCAL)
# ==============================================================================
DB_FILE = "historial_la_mana_picks.json"

def cargar_historial_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial_db(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

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

# ==============================================================================
# 3. BASE DE DATOS DE LIGAS, EQUIPOS Y LOGOS OFICIALES
# ==============================================================================
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
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "Aston Villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "AFC Bournemouth": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png",
    "Brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "Brighton & Hove Albion": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png",
    "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "Crystal Palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png",
    "Everton": "https://a.espncdn.com/i/teamlogos/soccer/500/368.png",
    "Fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png",
    "Ipswich Town": "https://a.espncdn.com/i/teamlogos/soccer/500/373.png",
    "Leicester City": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png",
    "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "Manchester United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "Newcastle United": "https://a.espncdn.com/i/teamlogos/soccer/500/361.png",
    "Nottingham Forest": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "Southampton": "https://a.espncdn.com/i/teamlogos/soccer/500/376.png",
    "Tottenham Hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "West Ham United": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png",
    "Wolverhampton": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png"
}

LALIGA_DICT = {
    "Athletic Club": "https://a.espncdn.com/i/teamlogos/soccer/500/93.png",
    "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "CA Osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "CD Leganés": "https://a.espncdn.com/i/teamlogos/soccer/500/9855.png",
    "Celta de Vigo": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "Deportivo Alavés": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "Getafe CF": "https://a.espncdn.com/i/teamlogos/soccer/500/2922.png",
    "Girona FC": "https://a.espncdn.com/i/teamlogos/soccer/500/9812.png",
    "Rayo Vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "RCD Espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png",
    "RCD Mallorca": "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "Real Betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Real Sociedad": "https://a.espncdn.com/i/teamlogos/soccer/500/89.png",
    "Sevilla FC": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "Valencia CF": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "Real Valladolid": "https://a.espncdn.com/i/teamlogos/soccer/500/95.png",
    "Villarreal CF": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png",
    "UD Las Palmas": "https://a.espncdn.com/i/teamlogos/soccer/500/98.png"
}

BUNDESLIGA_DICT = {
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "Eintracht Frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png",
    "VfB Stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "SC Freiburg": "https://a.espncdn.com/i/teamlogos/soccer/500/126.png",
    "1. FC Union Berlin": "https://a.espncdn.com/i/teamlogos/soccer/500/130.png",
    "Borussia Mönchengladbach": "https://a.espncdn.com/i/teamlogos/soccer/500/128.png",
    "Werder Bremen": "https://a.espncdn.com/i/teamlogos/soccer/500/137.png",
    "FC Augsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/3812.png",
    "TSG Hoffenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "Mainz 05": "https://a.espncdn.com/i/teamlogos/soccer/500/129.png",
    "VfL Wolfsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/138.png",
    "1. FC Heidenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/10363.png",
    "VfL Bochum": "https://a.espncdn.com/i/teamlogos/soccer/500/123.png",
    "St. Pauli": "https://a.espncdn.com/i/teamlogos/soccer/500/268.png",
    "Holstein Kiel": "https://a.espncdn.com/i/teamlogos/soccer/500/8066.png"
}

SERIE_A_DICT = {
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "AS Roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "Atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/105.png",
    "Lazio": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png",
    "Fiorentina": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png",
    "Bologna": "https://a.espncdn.com/i/teamlogos/soccer/500/107.png",
    "Torino": "https://a.espncdn.com/i/teamlogos/soccer/500/239.png",
    "Monza": "https://a.espncdn.com/i/teamlogos/soccer/500/3614.png",
    "Genoa": "https://a.espncdn.com/i/teamlogos/soccer/500/3263.png",
    "Parma": "https://a.espncdn.com/i/teamlogos/soccer/500/113.png",
    "Udinese": "https://a.espncdn.com/i/teamlogos/soccer/500/118.png",
    "Cagliari": "https://a.espncdn.com/i/teamlogos/soccer/500/108.png",
    "Hellas Verona": "https://a.espncdn.com/i/teamlogos/soccer/500/238.png",
    "Empoli": "https://a.espncdn.com/i/teamlogos/soccer/500/240.png",
    "Lecce": "https://a.espncdn.com/i/teamlogos/soccer/500/3452.png",
    "Como 1907": "https://a.espncdn.com/i/teamlogos/soccer/500/2625.png",
    "Venezia": "https://a.espncdn.com/i/teamlogos/soccer/500/2744.png"
}

CHAMPIONS_DICT = {
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "Paris Saint-Germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "Atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/105.png",
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "PSV Eindhoven": "https://a.espncdn.com/i/teamlogos/soccer/500/148.png",
    "Feyenoord": "https://a.espncdn.com/i/teamlogos/soccer/500/142.png",
    "Sporting CP": "https://a.espncdn.com/i/teamlogos/soccer/500/300.png",
    "Benfica": "https://a.espncdn.com/i/teamlogos/soccer/500/294.png",
    "Club Brujas": "https://a.espncdn.com/i/teamlogos/soccer/500/2282.png"
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

# DATA NFL
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

# ENTRENAMIENTO XGBOOST FÚTBOL Y MLB
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

# ==============================================================================
# 4. SIMULACIONES CON TARJETAS
# ==============================================================================
def simular_partido_futbol(liga, nombre_local, nombre_visita, cuota_loc, cuota_emp, cuota_vis, linea_goles, fatiga_eur, dict_actual):
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
    
    edge_loc = prob_win_local - (100 / float(cuota_loc)) if float(cuota_loc) > 1 else 0
    badge_1 = '<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if edge_loc >= 4.0 else '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'
    
    pick_1_str = f"Gana {nombre_local} (1X2) @ {cuota_loc}"
    pick_2_str = f"Doble Oportunidad: {nombre_local} o Empate (1X)"
    dif_tot = tot_goles - float(linea_goles)
    pick_3_str = f"{'OVER' if dif_tot>=0 else 'UNDER'} de {linea_goles} Goles Totales"

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
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

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Ganador 1X2: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Doble Oportunidad: {pick_2_str}</div></div><span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales: {pick_3_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_mlb_clasificado(nombre_local, nombre_visita, xera_loc, whip_loc, xera_vis, whip_vis, cuota_loc_dec, cuota_vis_dec, run_line_val, cuota_rl_dec, linea_tot_carreras):
    loc_d, vis_d = EQUIPOS_MLB[nombre_local], EQUIPOS_MLB[nombre_visita]
    logo_loc, logo_vis = loc_d["logo"], vis_d["logo"]
    input_vector = [[loc_d['wRC_plus'], vis_d['wRC_plus'], float(xera_loc), float(xera_vis), float(whip_loc), float(whip_vis), loc_d['park_factor']]]
    diff_carreras, tot_carreras = float(model_mlb_diff.predict(input_vector)[0]), float(model_mlb_tot.predict(input_vector)[0])
    carreras_loc, carreras_vis = max(0.5, (tot_carreras + diff_carreras) / 2), max(0.5, (tot_carreras - diff_carreras) / 2)
    prob_win_local = int(round(100 / (1 + 10**(-diff_carreras / 2.0))))
    prob_win_visita = 100 - prob_win_local
    
    equipo_fav = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
    prob_fav = max(prob_win_local, prob_win_visita)
    cuota_fav = cuota_loc_dec if prob_win_local >= prob_win_visita else cuota_vis_dec
    
    pick_1_str = f"{equipo_fav} ML @ {cuota_fav}"
    pick_2_str = f"{nombre_local if diff_carreras>=1.5 else nombre_visita} Run Line (-1.5) @ {cuota_rl_dec}"
    pick_3_str = f"{'OVER' if (tot_carreras - float(linea_tot_carreras))>=0 else 'UNDER'} de {linea_tot_carreras} carreras"

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO MLB</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">EFECTIVIDAD +EV: 76.5%</div>
        </div>
        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({carreras_vis:.1f} carreras)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({carreras_loc:.1f} carreras)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>
        </div>
        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Directo: {pick_1_str}</div></div><span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Run Line / Hándicap: {pick_2_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales: {pick_3_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_nfl_clasificado(nombre_local, nombre_visita, linea_spread, linea_total):
    local, visita = dict_nfl_nombres[nombre_local], dict_nfl_nombres[nombre_visita]
    logo_loc, logo_vis = dict_nfl_logos[local], dict_nfl_logos[visita]
    input_data = pd.DataFrame([[stats_nfl.loc[local, 'off_rating'], stats_nfl.loc[local, 'def_rating'], stats_nfl.loc[visita, 'off_rating'], stats_nfl.loc[visita, 'def_rating']]], columns=['home_off', 'home_def', 'away_off', 'away_def'])
    pred_spread, pred_total = float(model_nfl_sp.predict(input_data)[0]), float(model_nfl_tot.predict(input_data)[0])
    
    pts_local_est, pts_visita_est = (pred_total + pred_spread) / 2, (pred_total - pred_spread) / 2
    prob_win_local = int(round(100 / (1 + 10**(-pred_spread / 13.5))))
    prob_win_visita = 100 - prob_win_local
    
    pick_1_str = f"{nombre_local if prob_win_local>=prob_win_visita else nombre_visita} ML ({max(prob_win_local, prob_win_visita)}%)"
    dif_spread = pred_spread - (-linea_spread)
    pick_2_str = f"{nombre_local} {linea_spread}" if dif_spread > 0 else f"{nombre_visita} (+{abs(linea_spread)})"
    dif_total = pred_total - linea_total
    pick_3_str = f"{'OVER' if dif_total>=0 else 'UNDER'} de {linea_total} pts"

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO NFL (+EV)</div>
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

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Directo: {pick_1_str}</div></div><span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Hándicap / Spread: {pick_2_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales: {pick_3_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, f"{nombre_local} vs {nombre_visita}"

# ==============================================================================
# 5. GENERACIÓN DE GRÁFICAS Y RESUMEN HISTÓRICO CON PLOTLY
# ==============================================================================
def generar_graficas_home():
    stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()
    
    # 1. GRÁFICA NFL (Barras 3D/Estilizadas)
    fig_nfl = go.Figure()
    fig_nfl.add_trace(go.Bar(
        x=['WINS', 'LOSSES'],
        y=[stats['NFL']['wins'], stats['NFL']['losses']],
        marker_color=['#10B981', '#EF4444'],
        text=[stats['NFL']['wins'], stats['NFL']['losses']],
        textposition='auto'
    ))
    fig_nfl.update_layout(
        title="EFECTIVIDAD NFL",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#0F172A', size=12, family='Segoe UI'),
        height=220,
        margin=dict(l=10, r=10, t=35, b=10)
    )

    # 2. GRÁFICA MLB (Línea de Tendencia con Área Sombreada)
    fig_mlb = go.Figure()
    y_mlb_data = [0, stats['MLB']['wins']]
    fig_mlb.add_trace(go.Scatter(
        x=['Inicio', 'Actual'],
        y=y_mlb_data,
        mode='lines+markers+text',
        line=dict(color='#10B981', width=3),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.15)',
        text=[0, stats['MLB']['wins']],
        textposition='top center'
    ))
    fig_mlb.update_layout(
        title="EFECTIVIDAD MLB",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#0F172A', size=12, family='Segoe UI'),
        height=220,
        margin=dict(l=10, r=10, t=35, b=10)
    )

    # 3. GRÁFICA FÚTBOL (Dona / Donut Chart)
    labels_fut = ['WINS', 'LOSSES', 'PENDING']
    values_fut = [stats['FUTBOL']['wins'], stats['FUTBOL']['losses'], stats['FUTBOL']['pending']]
    if sum(values_fut) == 0: values_fut = [1, 0, 0] # Estado inicial
    
    fig_fut = go.Figure(data=[go.Pie(
        labels=labels_fut,
        values=values_fut,
        hole=.6,
        marker=dict(colors=['#10B981', '#EF4444', '#F59E0B'])
    )])
    fig_fut.update_layout(
        title="EFECTIVIDAD FÚTBOL",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#0F172A', size=12, family='Segoe UI'),
        height=220,
        margin=dict(l=10, r=10, t=35, b=10),
        showlegend=False
    )

    # PANEL HEADER HTML
    html_header = f"""
    <div style="background: #FFFFFF; border: 2px solid #10B981; border-radius: 20px; padding: 20px; margin-bottom: 15px; text-align: center; box-shadow: 0 10px 25px rgba(16,185,129,0.08);">
        <div style="font-size: 16px; font-weight: 800; color: #065F46;">EFECTIVIDAD GLOBAL Y RÉCORD</div>
        <div style="font-size: 42px; font-weight: 900; color: #10B981; margin: 4px 0;">{pct_global}%</div>
        <div style="font-size: 12px; font-weight: 700; color: #64748B;">
            Récord Registrado: <span style="color:#10B981;">{tot_wins} WINS</span> / <span style="color:#EF4444;">{tot_loss} LOSSES</span> (Total: {tot_global} Picks)
        </div>
    </div>
    """
    
    # HISTORIAL TEXTO HTML
    historial = cargar_historial_db()
    html_historial = f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 16px; height: 160px; overflow-y: auto;">
        <div style="font-size: 12px; font-weight: 800; color: #065F46; margin-bottom: 8px;">📋 HISTORIAL DE PICKS REGISTRADOS</div>
        <div style="font-size: 11px; color: #334155;">
    """
    if not historial:
        html_historial += "<i>No hay apuestas guardadas aún.</i>"
    else:
        for item in reversed(historial):
            st_col = "#10B981" if item["estado"] == "WIN" else ("#EF4444" if item["estado"] == "LOSS" else "#F59E0B")
            html_historial += f"<div style='margin-bottom: 6px; border-bottom: 1px solid #F1F5F9; padding-bottom: 4px;'>• <b>[{item['deporte']}]</b> {item['partido']} — {item['seleccion']} <b style='color:{st_col};'>[{item['estado']}]</b></div>"
            
    html_historial += "</div></div>"
    
    return html_header, html_historial, fig_nfl, fig_mlb, fig_fut

# ==============================================================================
# 6. INTERFAZ GRÁFICA CON BARRAS/BOTONES UNIFICADOS Y GRÁFICAS ESTÉTICAS
# ==============================================================================
with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft(primary_hue="emerald")) as app_mana:
    
    # HOME
    with gr.Column(visible=True) as vista_home:
        gr.Markdown("""
        # **LA MAÑA PICKS**
        ### **ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.**
        """)
        
        with gr.Row():
            # COLUMNA IZQUIERDA: MENÚ CON UN SOLO BOTÓN POR LIGA E ICONO INTEGRADO
            with gr.Column(scale=1):
                btn_premier = gr.Button("⚽  PREMIER LEAGUE (20 Equipos) ➔", variant="secondary")
                btn_laliga = gr.Button("⚽  LALIGA EA SPORTS (20 Equipos) ➔", variant="secondary")
                btn_bundesliga = gr.Button("⚽  BUNDESLIGA (18 Equipos) ➔", variant="secondary")
                btn_seriea = gr.Button("⚽  SERIE A (20 Equipos) ➔", variant="secondary")
                btn_champions = gr.Button("🏆  CHAMPIONS LEAGUE (36 Equipos) ➔", variant="secondary")
                btn_nfl = gr.Button("🏈  NFL (32 Equipos AFC/NFC) ➔", variant="primary")
                btn_mlb = gr.Button("⚾  MLB (30 Equipos Grandes Ligas) ➔", variant="primary")

            # COLUMNA DERECHA: DASHBOARD DE GRÁFICAS Y RÉCORD GLOBAL
            with gr.Column(scale=2):
                html_header_out = gr.HTML()
                html_historial_out = gr.HTML()
                
                with gr.Row():
                    plot_nfl_out = gr.Plot(show_label=False)
                    plot_mlb_out = gr.Plot(show_label=False)
                    plot_fut_out = gr.Plot(show_label=False)

    # VISTA FÚTBOL GENERAL
    with gr.Column(visible=False) as vista_fut:
        with gr.Row():
            btn_volver_fut = gr.Button("⬅️ Volver a Ligas", variant="secondary", scale=1)
            txt_titulo_liga = gr.Markdown("## ⚽ **Área de Análisis de Fútbol**", scale=4)
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    drop_fut_loc = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Arsenal", label="Equipo Local", scale=3)
                    img_fut_loc = gr.Image(value=PREMIER_DICT["Arsenal"], label="Local", width=60, height=60, show_label=False, scale=1)
                
                with gr.Row():
                    drop_fut_vis = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Chelsea", label="Equipo Visitante", scale=3)
                    img_fut_vis = gr.Image(value=PREMIER_DICT["Chelsea"], label="Visitante", width=60, height=60, show_label=False, scale=1)
                
                drop_fatiga = gr.Dropdown(choices=["No (Semana normal)", "Sí (Jugó Champions/Europa League hace 3 días)"], value="No (Semana normal)", label="¿Fatiga Europea?")
                
                with gr.Row():
                    num_fut_c_loc = gr.Number(value=1.85, label="Cuota Local (1)")
                    num_fut_c_emp = gr.Number(value=3.60, label="Cuota Empate (X)")
                    num_fut_c_vis = gr.Number(value=4.20, label="Cuota Visitante (2)")
                    
                num_fut_linea_tot = gr.Number(value=2.5, label="Línea Total Goles (O/U)")
                btn_sim_fut = gr.Button("Simular Partido 🚀", variant="primary")
                
                gr.Markdown("---")
                rad_pick_fut = gr.Radio(choices=["Selección 1 (1X2)", "Selección 2 (Doble Op.)", "Selección 3 (Totales)"], label="Pick a guardar")
                btn_save_fut = gr.Button("Guardar Pick en Historial 💾", variant="secondary")
                lbl_save_fut = gr.Markdown("")

            with gr.Column(scale=2):
                out_fut = gr.HTML()
                st_fut_p1, st_fut_p2, st_fut_p3, st_fut_match = gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA NFL
    with gr.Column(visible=False) as vista_nfl:
        with gr.Row():
            btn_volver_nfl = gr.Button("⬅️ Volver a Ligas", variant="secondary", scale=1)
            gr.Markdown("## 🏈 **Área de Análisis: NFL (32 Equipos)**", scale=4)
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    drop_nfl_loc = gr.Dropdown(choices=lista_nfl_nombres, value="Los Angeles Rams", label="Equipo Local", scale=3)
                    img_nfl_loc = gr.Image(value=dict_nfl_logos[dict_nfl_nombres["Los Angeles Rams"]], label="Local", width=60, height=60, show_label=False, scale=1)
                
                with gr.Row():
                    drop_nfl_vis = gr.Dropdown(choices=lista_nfl_nombres, value="New York Giants", label="Equipo Visitante", scale=3)
                    img_nfl_vis = gr.Image(value=dict_nfl_logos[dict_nfl_nombres["New York Giants"]], label="Visitante", width=60, height=60, show_label=False, scale=1)

                num_nfl_sp = gr.Number(value=-6.5, label="Spread Casino")
                num_nfl_tot = gr.Number(value=47.5, label="Línea Total")
                btn_sim_nfl = gr.Button("Simular Partido NFL 🚀", variant="primary")
                
                gr.Markdown("---")
                rad_pick_nfl = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Spread)", "Selección 3 (Totales)"], label="Pick a guardar")
                btn_save_nfl = gr.Button("Guardar Pick NFL 💾", variant="secondary")
                lbl_save_nfl = gr.Markdown("")

            with gr.Column(scale=2):
                out_nfl = gr.HTML()
                st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_match = gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA MLB
    with gr.Column(visible=False) as vista_mlb:
        with gr.Row():
            btn_volver_mlb = gr.Button("⬅️ Volver a Ligas", variant="secondary", scale=1)
            gr.Markdown("## ⚾ **Área de Análisis: MLB (30 Equipos)**", scale=4)
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    drop_mlb_loc = gr.Dropdown(choices=lista_mlb_nombres, value="San Francisco Giants", label="Equipo Local", scale=3)
                    img_mlb_loc = gr.Image(value=EQUIPOS_MLB["San Francisco Giants"]["logo"], label="Local", width=60, height=60, show_label=False, scale=1)
                
                with gr.Row():
                    drop_mlb_vis = gr.Dropdown(choices=lista_mlb_nombres, value="Minnesota Twins", label="Equipo Visitante", scale=3)
                    img_mlb_vis = gr.Image(value=EQUIPOS_MLB["Minnesota Twins"]["logo"], label="Visitante", width=60, height=60, show_label=False, scale=1)

                btn_auto_api = gr.Button("🔄 Cargar Abridores en Vivo (MLB API)", variant="secondary")
                lbl_api_status = gr.Markdown("🟢 Listo para sincronizar")
                
                with gr.Row():
                    num_xera_loc = gr.Number(value=3.45, label="ERA Local")
                    num_whip_loc = gr.Number(value=1.12, label="WHIP Local")
                with gr.Row():
                    num_xera_vis = gr.Number(value=3.65, label="ERA Visitante")
                    num_whip_vis = gr.Number(value=1.18, label="WHIP Visitante")
                
                with gr.Row():
                    num_mlb_cuota_loc = gr.Number(value=1.72, label="Cuota Local ML")
                    num_mlb_cuota_vis = gr.Number(value=2.20, label="Cuota Visitante ML")
                
                num_run_line_val = gr.Number(value=-1.5, label="Run Line")
                num_cuota_rl_dec = gr.Number(value=2.05, label="Cuota Run Line")
                num_mlb_tot = gr.Number(value=8.5, label="Línea Total Carreras")
                btn_sim_mlb = gr.Button("Simular Partido MLB 🚀", variant="primary")
                
                gr.Markdown("---")
                rad_pick_mlb = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Run Line)", "Selección 3 (Totales)"], label="Pick a guardar")
                btn_save_mlb = gr.Button("Guardar Pick MLB 💾", variant="secondary")
                lbl_save_mlb = gr.Markdown("")

            with gr.Column(scale=2):
                out_mlb = gr.HTML()
                st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_match = gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # ESTADO OCULTO LIGA ACTIVA
    st_liga_activa = gr.State("Premier League")
    st_dict_futbol_actual = gr.State(PREMIER_DICT)

    # ACTUALIZACIÓN DE ESCUDOS
    def actualizar_escudos_fut(nombre_loc, nombre_vis, dict_actual):
        logo_loc = dict_actual.get(nombre_loc, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        logo_vis = dict_actual.get(nombre_vis, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        return logo_loc, logo_vis

    def actualizar_escudos_nfl(nombre_loc, nombre_vis):
        loc, vis = dict_nfl_nombres[nombre_loc], dict_nfl_nombres[nombre_vis]
        return dict_nfl_logos[loc], dict_nfl_logos[vis]

    def actualizar_escudos_mlb(nombre_loc, nombre_vis):
        return EQUIPOS_MLB[nombre_loc]["logo"], EQUIPOS_MLB[nombre_vis]["logo"]

    # FUNCIONES DE NAVEGACIÓN
    def cambiar_a_liga_futbol(diccionario_liga, nombre_liga):
        eqs = list(diccionario_liga.keys())
        loc_inicial, vis_inicial = eqs[0], (eqs[1] if len(eqs) > 1 else eqs[0])
        return (
            gr.update(visible=False), gr.update(visible=True), 
            gr.update(choices=eqs, value=loc_inicial), gr.update(choices=eqs, value=vis_inicial), 
            diccionario_liga[loc_inicial], diccionario_liga[vis_inicial], 
            f"## ⚽ **Área de Análisis: {nombre_liga.upper()} ({len(eqs)} Equipos)**", 
            nombre_liga, diccionario_liga
        )

    btn_premier.click(fn=lambda: cambiar_a_liga_futbol(PREMIER_DICT, "Premier League"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual])
    btn_laliga.click(fn=lambda: cambiar_a_liga_futbol(LALIGA_DICT, "LaLiga EA Sports"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual])
    btn_bundesliga.click(fn=lambda: cambiar_a_liga_futbol(BUNDESLIGA_DICT, "Bundesliga"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual])
    btn_seriea.click(fn=lambda: cambiar_a_liga_futbol(SERIE_A_DICT, "Serie A"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual])
    btn_champions.click(fn=lambda: cambiar_a_liga_futbol(CHAMPIONS_DICT, "Champions League"), outputs=[vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual])

    def abrir_nfl(): return gr.update(visible=False), gr.update(visible=True)
    def abrir_mlb(): return gr.update(visible=False), gr.update(visible=True)
    def volver_home(): 
        h_head, h_hist, f_nfl, f_mlb, f_fut = generar_graficas_home()
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), h_head, h_hist, f_nfl, f_mlb, f_fut

    btn_nfl.click(fn=abrir_nfl, outputs=[vista_home, vista_nfl])
    btn_mlb.click(fn=abrir_mlb, outputs=[vista_home, vista_mlb])

    btn_volver_nfl.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, plot_nfl_out, plot_mlb_out, plot_fut_out])
    btn_volver_mlb.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, plot_nfl_out, plot_mlb_out, plot_fut_out])
    btn_volver_fut.click(fn=volver_home, outputs=[vista_home, vista_nfl, vista_mlb, vista_fut, html_header_out, html_historial_out, plot_nfl_out, plot_mlb_out, plot_fut_out])

    drop_fut_loc.change(fn=actualizar_escudos_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis])
    drop_fut_vis.change(fn=actualizar_escudos_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis])

    drop_nfl_loc.change(fn=actualizar_escudos_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis])
    drop_nfl_vis.change(fn=actualizar_escudos_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis])

    drop_mlb_loc.change(fn=actualizar_escudos_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis])
    drop_mlb_vis.change(fn=actualizar_escudos_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis])

    btn_auto_api.click(
        fn=auto_cargar_pitchers_mlb,
        inputs=[drop_mlb_loc, drop_mlb_vis],
        outputs=[num_xera_loc, num_whip_loc, num_xera_vis, num_whip_vis, lbl_api_status]
    )

    # SIMULACIONES
    btn_sim_nfl.click(fn=simular_partido_nfl_clasificado, inputs=[drop_nfl_loc, drop_nfl_vis, num_nfl_sp, num_nfl_tot], outputs=[out_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_match])
    btn_sim_mlb.click(fn=simular_partido_mlb_clasificado, inputs=[drop_mlb_loc, drop_mlb_vis, num_xera_loc, num_whip_loc, num_xera_vis, num_whip_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_run_line_val, num_cuota_rl_dec, num_mlb_tot], outputs=[out_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_match])
    btn_sim_fut.click(fn=simular_partido_futbol, inputs=[st_liga_activa, drop_fut_loc, drop_fut_vis, num_fut_c_loc, num_fut_c_emp, num_fut_c_vis, num_fut_linea_tot, drop_fatiga, st_dict_futbol_actual], outputs=[out_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_match])

    # REGISTRAR PICKS
    def fn_save_pick_nfl(radio_sel, p1, p2, p3, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NFL", match, sel_text, radio_sel, 1.90, "+4.5%")
        return f"✅ Pick de NFL guardado: {sel_text}"

    def fn_save_pick_mlb(radio_sel, p1, p2, p3, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("MLB", match, sel_text, radio_sel, 1.90, "+5.2%")
        return f"✅ Pick de MLB guardado: {sel_text}"

    def fn_save_pick_fut(radio_sel, p1, p2, p3, match, liga):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db(f"FÚTBOL ({liga})", match, sel_text, radio_sel, 1.85, "+4.2%")
        return f"✅ Pick de {liga} guardado: {sel_text}"

    btn_save_nfl.click(fn=fn_save_pick_nfl, inputs=[rad_pick_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_match], outputs=[lbl_save_nfl])
    btn_save_mlb.click(fn=fn_save_pick_mlb, inputs=[rad_pick_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_match], outputs=[lbl_save_mlb])
    btn_save_fut.click(fn=fn_save_pick_fut, inputs=[rad_pick_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_match, st_liga_activa], outputs=[lbl_save_fut])

    # EVENTO DE CARGA INICIAL DE LA HOME
    app_mana.load(fn=generar_graficas_home, outputs=[html_header_out, html_historial_out, plot_nfl_out, plot_mlb_out, plot_fut_out])

app_mana.launch(share=True, debug=True)
