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
st.set_page_config(page_title="MAÑA PIKS ANALYTICS PRO - SABERMETRÍA MLB", layout="wide", page_icon="👑")

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
        "estado": "PENDING", # PENDING, WIN, LOSS
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
# MOTOR DE AUTO-VERIFICACIÓN EN VIVO
# ==========================================
def auto_verificar_apuestas():
    historial = cargar_base_datos()
    actualizados = 0

    # 1. API LIGA MX (ESPN)
    url_mx = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard"
    res_mx = {}
    try:
        r_mx = requests.get(url_mx, timeout=5)
        if r_mx.status_code == 200:
            events = r_mx.json().get("events", [])
            for ev_item in events:
                comp = ev_item.get("competitions", [])[0]
                status_completed = comp.get("status", {}).get("type", {}).get("completed", False)
                period = comp.get("status", {}).get("period", 0)
                teams = comp.get("competitors", [])
                
                loc_name, vis_name = "", ""
                loc_score, vis_score = 0, 0
                loc_ht_score, vis_ht_score = 0, 0
                
                for t in teams:
                    linescores = t.get("linescores", [])
                    ht_val = int(linescores[0].get("value", 0)) if len(linescores) >= 1 else 0
                    
                    if t.get("homeAway") == "home":
                        loc_name = t.get("team", {}).get("name", "")
                        loc_score = int(t.get("score", 0))
                        loc_ht_score = ht_val
                    else:
                        vis_name = t.get("team", {}).get("name", "")
                        vis_score = int(t.get("score", 0))
                        vis_ht_score = ht_val

                res_mx[f"{loc_name} vs {vis_name}"] = {
                    "completed": status_completed, 
                    "period": period,
                    "loc_score": loc_score, 
                    "vis_score": vis_score,
                    "ht_score_tot": loc_ht_score + vis_ht_score
                }
    except Exception:
        pass

    # 2. API MLB STATS
    url_mlb = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    res_mlb = {}
    try:
        r_mlb = requests.get(url_mlb, timeout=5)
        if r_mlb.status_code == 200:
            events = r_mlb.json().get("events", [])
            for ev_item in events:
                game_id = ev_item.get("id")
                comp = ev_item.get("competitions", [])[0]
                status_completed = comp.get("status", {}).get("type", {}).get("completed", False)
                status_state = comp.get("status", {}).get("type", {}).get("state", "pre")
                period = comp.get("status", {}).get("period", 0)
                
                teams = comp.get("competitors", [])
                loc_name, vis_name = "", ""
                loc_score, vis_score = 0, 0
                loc_linescore, vis_linescore = [], []
                
                for t in teams:
                    if t.get("homeAway") == "home":
                        loc_name = t.get("team", {}).get("displayName", "")
                        loc_score = int(t.get("score", 0))
                        loc_linescore = t.get("linescores", [])
                    else:
                        vis_name = t.get("team", {}).get("displayName", "")
                        vis_score = int(t.get("score", 0))
                        vis_linescore = t.get("linescores", [])

                r1_loc = int(loc_linescore[0].get("value", 0)) if len(loc_linescore) >= 1 else 0
                r1_vis = int(vis_linescore[0].get("value", 0)) if len(vis_linescore) >= 1 else 0
                r1_tot = r1_loc + r1_vis

                f5_loc = sum([int(x.get("value", 0)) for x in loc_linescore[:5]])
                f5_vis = sum([int(x.get("value", 0)) for x in vis_linescore[:5]])
                f5_tot = f5_loc + f5_vis
                f5_completo = (period > 5) or status_completed or (len(loc_linescore) >= 5 and len(vis_linescore) >= 5 and period == 5 and status_state == "post")

                ks_dict = {}
                outs_dict = {}
                batters_h_dict = {}
                batters_r_dict = {}
                batters_hrbi_dict = {}

                if status_state in ["in", "post"]:
                    try:
                        url_box = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?event={game_id}"
                        r_box = requests.get(url_box, timeout=4)
                        if r_box.status_code == 200:
                            box_data = r_box.json()
                            players = box_data.get("boxscore", {}).get("players", [])
                            for team_p in players:
                                statistics = team_p.get("statistics", [])
                                for stat_cat in statistics:
                                    if stat_cat.get("type") == "pitching":
                                        athletes = stat_cat.get("athletes", [])
                                        for ath in athletes:
                                            p_name = ath.get("athlete", {}).get("displayName", "")
                                            stats_vals = ath.get("stats", [])
                                            if len(stats_vals) >= 6:
                                                ip_str = str(stats_vals[0])
                                                if "." in ip_str:
                                                    parts = ip_str.split(".")
                                                    outs_val = int(parts[0]) * 3 + int(parts[1])
                                                elif ip_str.isdigit():
                                                    outs_val = int(ip_str) * 3
                                                else:
                                                    outs_val = 0
                                                
                                                so_val = int(stats_vals[5]) if str(stats_vals[5]).isdigit() else 0
                                                ks_dict[p_name.lower()] = so_val
                                                outs_dict[p_name.lower()] = outs_val

                                    elif stat_cat.get("type") == "batting":
                                        athletes = stat_cat.get("athletes", [])
                                        for ath in athletes:
                                            b_name = ath.get("athlete", {}).get("displayName", "")
                                            stats_vals = ath.get("stats", [])
                                            if len(stats_vals) >= 4:
                                                r_val = int(stats_vals[1]) if str(stats_vals[1]).isdigit() else 0
                                                h_val = int(stats_vals[2]) if str(stats_vals[2]).isdigit() else 0
                                                rbi_val = int(stats_vals[3]) if str(stats_vals[3]).isdigit() else 0
                                                
                                                batters_h_dict[b_name.lower()] = h_val
                                                batters_r_dict[b_name.lower()] = r_val
                                                batters_hrbi_dict[b_name.lower()] = h_val + r_val + rbi_val
                    except Exception:
                        pass

                res_mlb[f"{loc_name} vs {vis_name}"] = {
                    "completed": status_completed,
                    "state": status_state,
                    "period": period,
                    "loc_name": loc_name, 
                    "vis_name": vis_name, 
                    "loc_score": loc_score, 
                    "vis_score": vis_score,
                    "r1_tot": r1_tot,
                    "f5_loc": f5_loc,
                    "f5_vis": f5_vis,
                    "f5_tot": f5_tot,
                    "f5_completo": f5_completo,
                    "ks_dict": ks_dict,
                    "outs_dict": outs_dict,
                    "batters_h_dict": batters_h_dict,
                    "batters_r_dict": batters_r_dict,
                    "batters_hrbi_dict": batters_hrbi_dict
                }
    except Exception:
        pass

    # EVALUAR CADA APUESTA PENDIENTE
    for item in historial:
        if item["estado"] == "PENDING":
            dep = item["deporte"]
            
            # --- LIGA MX ---
            if "Liga MX" in dep:
                for match_title, score_data in res_mx.items():
                    if item["equipo_loc"].lower() in match_title.lower() and item["equipo_vis"].lower() in match_title.lower():
                        g_loc = score_data["loc_score"]
                        g_vis = score_data["vis_score"]
                        tot_goles = g_loc + g_vis
                        ht_goles = score_data["ht_score_tot"]
                        mercado = item["mercado"]
                        linea = item.get("linea", "")

                        if "1ra Mitad" in mercado or "1HT" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 0.5
                            except: val_target = 0.5

                            if "Más" in mercado or "Over" in mercado:
                                if ht_goles > val_target:
                                    item["estado"] = "WIN"; item["resultado_real"] = f"{ht_goles} Goles (1HT)"; actualizados += 1
                                elif score_data["period"] >= 2 or score_data["completed"]:
                                    item["estado"] = "LOSS"; item["resultado_real"] = f"{ht_goles} Goles (1HT)"; actualizados += 1

                        elif "Goles" in mercado or "Over" in mercado or "Under" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 2.5
                            except: val_target = 2.5

                            if "Más" in mercado or "Over" in mercado:
                                if tot_goles > val_target:
                                    item["estado"] = "WIN"; item["resultado_real"] = f"{g_loc} - {g_vis}"; actualizados += 1
                                elif score_data["completed"]:
                                    item["estado"] = "LOSS"; item["resultado_real"] = f"{g_loc} - {g_vis}"; actualizados += 1

                        elif "Gana" in mercado:
                            if score_data["completed"]:
                                item["resultado_real"] = f"{g_loc} - {g_vis}"
                                if item["equipo_loc"] in mercado and g_loc > g_vis: item["estado"] = "WIN"
                                elif item["equipo_vis"] in mercado and g_vis > g_loc: item["estado"] = "WIN"
                                else: item["estado"] = "LOSS"
                                actualizados += 1

            # --- MLB ---
            elif "MLB" in dep:
                for match_title, score_data in res_mlb.items():
                    eq_loc_match = item["equipo_loc"].lower() in match_title.lower() or score_data["loc_name"].lower() in item["equipo_loc"].lower()
                    eq_vis_match = item["equipo_vis"].lower() in match_title.lower() or score_data["vis_name"].lower() in item["equipo_vis"].lower()
                    
                    if eq_loc_match or eq_vis_match:
                        r_loc = score_data["loc_score"]
                        r_vis = score_data["vis_score"]
                        tot_carreras = r_loc + r_vis
                        mercado = item["mercado"]
                        linea = item.get("linea", "")
                        
                        ks_dict = score_data["ks_dict"]
                        outs_dict = score_data["outs_dict"]
                        bh_dict = score_data["batters_h_dict"]
                        br_dict = score_data["batters_r_dict"]
                        bhrbi_dict = score_data["batters_hrbi_dict"]

                        if "Carreras" in mercado and not "F5" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 8.5
                            except: val_target = 8.5

                            if "Over" in mercado or "OVER" in mercado:
                                if tot_carreras > val_target:
                                    item["estado"] = "WIN"; item["resultado_real"] = f"{r_loc} - {r_vis}"; actualizados += 1
                                elif score_data["completed"]:
                                    item["estado"] = "LOSS"; item["resultado_real"] = f"{r_loc} - {r_vis}"; actualizados += 1

                            elif "Under" in mercado or "UNDER" in mercado:
                                if tot_carreras > val_target:
                                    item["estado"] = "LOSS"; item["resultado_real"] = f"{r_loc} - {r_vis}"; actualizados += 1
                                elif score_data["completed"]:
                                    item["estado"] = "WIN"; item["resultado_real"] = f"{r_loc} - {r_vis}"; actualizados += 1

                        elif "ML" in mercado or "Gana" in mercado:
                            if score_data["completed"] or score_data["period"] >= 9:
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                if item["equipo_loc"] in mercado and r_loc > r_vis: item["estado"] = "WIN"
                                elif item["equipo_vis"] in mercado and r_vis > r_loc: item["estado"] = "WIN"
                                else: item["estado"] = "LOSS"
                                actualizados += 1

                        elif "RL" in mercado or "Run Line" in mercado:
                            if score_data["completed"] or score_data["period"] >= 9:
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                if item["equipo_loc"] in mercado:
                                    diff = r_loc - r_vis
                                    if "-1.5" in mercado or "-1.5" in linea: item["estado"] = "WIN" if diff >= 2 else "LOSS"
                                    elif "+1.5" in mercado or "+1.5" in linea: item["estado"] = "WIN" if diff >= -1 else "LOSS"
                                elif item["equipo_vis"] in mercado:
                                    diff = r_vis - r_loc
                                    if "-1.5" in mercado or "-1.5" in linea: item["estado"] = "WIN" if diff >= 2 else "LOSS"
                                    elif "+1.5" in mercado or "+1.5" in linea: item["estado"] = "WIN" if diff >= -1 else "LOSS"
                                actualizados += 1

                        elif "K's" in mercado or "Ponches" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 5.5
                            except: val_target = 5.5

                            k_val = 0
                            for p_k, kv in ks_dict.items():
                                if p_k in mercado.lower(): k_val = kv; break
                            else: k_val = max(ks_dict.values()) if ks_dict else 0

                            if "Over" in mercado:
                                if k_val > val_target: item["estado"] = "WIN"; item["resultado_real"] = f"{k_val} K's"; actualizados += 1
                                elif score_data["completed"]: item["estado"] = "LOSS"; item["resultado_real"] = f"{k_val} K's"; actualizados += 1

                        elif "Outs" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 15.5
                            except: val_target = 15.5

                            outs_val = 0
                            for p_k, ov in outs_dict.items():
                                if p_k in mercado.lower(): outs_val = ov; break
                            else: outs_val = max(outs_dict.values()) if outs_dict else 0

                            if "Over" in mercado:
                                if outs_val > val_target: item["estado"] = "WIN"; item["resultado_real"] = f"{outs_val} Outs"; actualizados += 1
                                elif score_data["completed"]: item["estado"] = "LOSS"; item["resultado_real"] = f"{outs_val} Outs"; actualizados += 1

                        elif "Hit" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 0.5
                            except: val_target = 0.5

                            h_val = 0
                            for b_k, hv in bh_dict.items():
                                if b_k in mercado.lower(): h_val = hv; break

                            if h_val > val_target: item["estado"] = "WIN"; item["resultado_real"] = f"{h_val} Hits"; actualizados += 1
                            elif score_data["completed"]: item["estado"] = "LOSS"; item["resultado_real"] = f"{h_val} Hits"; actualizados += 1

                        elif "Run" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 0.5
                            except: val_target = 0.5

                            r_val = 0
                            for b_k, rv in br_dict.items():
                                if b_k in mercado.lower(): r_val = rv; break

                            if r_val > val_target: item["estado"] = "WIN"; item["resultado_real"] = f"{r_val} Runs"; actualizados += 1
                            elif score_data["completed"]: item["estado"] = "LOSS"; item["resultado_real"] = f"{r_val} Runs"; actualizados += 1

                        elif "H+R+RBI" in mercado:
                            try: val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 1.5
                            except: val_target = 1.5

                            hrbi_val = 0
                            for b_k, hrv in bhrbi_dict.items():
                                if b_k in mercado.lower(): hrbi_val = hrv; break

                            if hrbi_val > val_target: item["estado"] = "WIN"; item["resultado_real"] = f"{hrbi_val} H+R+RBI"; actualizados += 1
                            elif score_data["completed"]: item["estado"] = "LOSS"; item["resultado_real"] = f"{hrbi_val} H+R+RBI"; actualizados += 1

    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    return actualizados

# ==========================================
# BASE DE DATOS Y JERSEYS
# ==========================================
JERSEYS_LIGA_MX = {
    "América": {"c1": "#FDE100", "c2": "#001A49"}, "Atlas": {"c1": "#000000", "c2": "#DA291C"},
    "Chivas": {"c1": "#DA291C", "c2": "#FFFFFF"}, "Cruz Azul": {"c1": "#00519E", "c2": "#FFFFFF"},
    "León": {"c1": "#007A33", "c2": "#FDE100"}, "Monterrey": {"c1": "#002452", "c2": "#FFFFFF"},
    "Necaxa": {"c1": "#DA291C", "c2": "#FFFFFF"}, "Pachuca": {"c1": "#002B49", "c2": "#FFFFFF"},
    "Pumas": {"c1": "#002B49", "c2": "#C8A062"}, "Tigres": {"c1": "#FDE100", "c2": "#00519E"},
    "Tijuana": {"c1": "#DA291C", "c2": "#000000"}, "Toluca": {"c1": "#DA291C", "c2": "#FFFFFF"}
}

JERSEYS_MLB = {
    "NY Yankees": {"c1": "#001C43", "c2": "#FFFFFF"},
    "LA Dodgers": {"c1": "#005A9C", "c2": "#FFFFFF"},
    "Boston Red Sox": {"c1": "#BD3039", "c2": "#0C2340"},
    "Houston Astros": {"c1": "#002D62", "c2": "#EB6E1F"},
    "Atlanta Braves": {"c1": "#13274F", "c2": "#CE1141"},
    "SD Padres": {"c1": "#2F241D", "c2": "#FFC425"},
    "Chicago Cubs": {"c1": "#0E3386", "c2": "#CC3433"},
    "SF Giants": {"c1": "#FD5A1E", "c2": "#000000"},
    "NY Mets": {"c1": "#002D72", "c2": "#FF5910"},
    "Philadelphia Phillies": {"c1": "#E81828", "c2": "#002D72"},
    "Texas Rangers": {"c1": "#003278", "c2": "#C0111F"},
    "Toronto Blue Jays": {"c1": "#134A8E", "c2": "#1D2D5C"},
    "Seattle Mariners": {"c1": "#0C2340", "c2": "#005C5C"},
    "Baltimore Orioles": {"c1": "#DF4601", "c2": "#000000"},
    "Tampa Bay Rays": {"c1": "#092C5C", "c2": "#8FBCE6"},
    "Arizona Diamondbacks": {"c1": "#A71930", "c2": "#E3D4AD"},
    "Milwaukee Brewers": {"c1": "#12284C", "c2": "#FFC52F"},
    "St. Louis Cardinals": {"c1": "#C41E3A", "c2": "#0C2340"},
    "Cleveland Guardians": {"c1": "#0C2340", "c2": "#E31937"},
    "Minnesota Twins": {"c1": "#002B5C", "c2": "#D31145"},
    "Detroit Tigers": {"c1": "#0C2340", "c2": "#FA4616"},
    "Chicago White Sox": {"c1": "#27251F", "c2": "#FFFFFF"},
    "KC Royals": {"c1": "#004687", "c2": "#74B4E7"},
    "LA Angels": {"c1": "#003263", "c2": "#BA0021"},
    "Cincinnati Reds": {"c1": "#C6011F", "c2": "#000000"},
    "Colorado Rockies": {"c1": "#333366", "c2": "#C4CED4"},
    "Miami Marlins": {"c1": "#00A3E0", "c2": "#EF3340"},
    "Pittsburgh Pirates": {"c1": "#FDB827", "c2": "#000000"},
    "Washington Nationals": {"c1": "#AB0003", "c2": "#14225A"},
    "Oakland Athletics": {"c1": "#003831", "c2": "#EFB21E"}
}

EQUIPOS_LIGA_MX_BASE = {
    "América": {"altitud": 2240, "att": 2.10, "def": 0.85, "corners": 6.2},
    "Chivas": {"altitud": 1560, "att": 1.60, "def": 1.05, "corners": 5.5},
    "Cruz Azul": {"altitud": 2240, "att": 1.85, "def": 0.95, "corners": 6.0},
    "Monterrey": {"altitud": 500, "att": 1.90, "def": 0.90, "corners": 6.1},
    "Pachuca": {"altitud": 2400, "att": 1.70, "def": 1.20, "corners": 5.4},
    "Tigres": {"altitud": 500, "att": 1.95, "def": 0.90, "corners": 5.8},
    "Toluca": {"altitud": 2680, "att": 2.00, "def": 1.10, "corners": 5.9}
}

EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "w": 12, "l": 6, "ip": 110.0, "whip": 1.18, "k": 125},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "w": 14, "l": 5, "ip": 125.0, "whip": 1.12, "k": 140},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "w": 10, "l": 7, "ip": 105.0, "whip": 1.20, "k": 115},
    "Atlanta Braves": {"id": 144, "wRC_plus": 114, "era_base": 3.80, "w": 11, "l": 6, "ip": 108.0, "whip": 1.22, "k": 118},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 111, "era_base": 3.65, "w": 12, "l": 5, "ip": 115.0, "whip": 1.17, "k": 130},
    "Texas Rangers": {"id": 140, "wRC_plus": 104, "era_base": 4.20, "w": 7, "l": 10, "ip": 90.0, "whip": 1.30, "k": 88},
    "Seattle Mariners": {"id": 136, "wRC_plus": 95, "era_base": 3.40, "w": 11, "l": 6, "ip": 120.0, "whip": 1.10, "k": 135},
    "Miami Marlins": {"id": 146, "wRC_plus": 88, "era_base": 4.30, "w": 5, "l": 12, "ip": 85.0, "whip": 1.32, "k": 80}
}

@st.cache_data(ttl=1800)
def obtener_abridores_mlb_hoy(team_id_local, team_id_visita):
    hoy = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={hoy}&endDate={hoy}&hydrate=probablePitcher"
    p_loc, p_vis = "Por Confirmar", "Por Confirmar"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            dates = data.get("dates", [])
            if dates:
                games = dates[0].get("games", [])
                for g in games:
                    home_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
                    away_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
                    if home_id == team_id_local or away_id == team_id_local:
                        p_loc = g.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        p_vis = g.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName", "Por Confirmar")
                        break
    except Exception:
        pass
    return p_loc, p_vis

@st.cache_data(ttl=3600)
def obtener_stats_liga_mx_api():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/standings"
    stats_actualizadas = EQUIPOS_LIGA_MX_BASE.copy()
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", [])
            if children:
                standings = children[0].get("standings", {}).get("entries", [])
                for entry in standings:
                    team_name = entry.get("team", {}).get("name", "")
                    stats = entry.get("stats", [])
                    mp, gf, ga = 1, 0, 0
                    for s in stats:
                        if s.get("name") == "gamesPlayed": mp = s.get("value", 1)
                        if s.get("name") == "pointsFor": gf = s.get("value", 0)
                        if s.get("name") == "pointsAgainst": ga = s.get("value", 0)
                    if mp > 0:
                        att_calc = max(0.8, gf / mp)
                        def_calc = max(0.7, ga / mp)
                        for eq in stats_actualizadas:
                            if eq.lower() in team_name.lower() or team_name.lower() in eq.lower():
                                stats_actualizadas[eq]["att"] = round(att_calc, 2)
                                stats_actualizadas[eq]["def"] = round(def_calc, 2)
    except Exception:
        pass
    return stats_actualizadas

# ==========================================
# ESTILOS CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Orbitron:wght@700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #1d2220 !important; color: #e2e8f0; }
    
    .top-deporte-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 20px !important; font-weight: 900 !important; color: #f5d742 !important;
    }
    
    label { color: #00ff66 !important; font-weight: 800 !important; font-size: 13px !important; }
    input, div[data-baseweb="select"] * { color: #000000 !important; font-weight: 900 !important; }
    
    .header-text-left, .header-text-right {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 24px !important; font-weight: 900 !important; color: #f5d742 !important;
    }

    .card-pro {
        background: #242a26; border: 1px solid #2d3833; border-left: 4px solid #00ff66;
        border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;
    }
    .card-star {
        background: #2b2718; border: 1px solid #ffd700; border-left: 5px solid #ffd700;
        box-shadow: 0 0 14px rgba(255, 215, 0, 0.35); border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;
    }

    .badge-star {
        background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%); color: #000000;
        font-weight: 900; padding: 4px 10px; border-radius: 4px; float: right; font-size: 11px;
    }
    .badge-high { background: #00ff66; color: #000; font-weight: 900; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
    .badge-med { background: #f59e0b; color: #000; font-weight: 900; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
    .badge-low { background: #ff3366; color: #fff; font-weight: 900; padding: 4px 8px; border-radius: 4px; font-size: 11px; }

    div.stButton > button {
        background: #00ff66 !important; color: #000000 !important; font-weight: 900 !important;
        border-radius: 6px !important; border: none !important;
    }
</style>
""", unsafe_allow_html=True)

def to_decimal(momio, tipo):
    if tipo == "Decimal": return float(momio)
    return (momio / 100) + 1 if momio > 0 else (100 / abs(momio)) + 1

def to_american_str(prob):
    if prob <= 0 or prob >= 1: return "+100"
    dec = 1.0 / prob
    if dec >= 2.0:
        am = int(round((dec - 1) * 100))
        return f"+{am}"
    else:
        am = int(round(-100 / (dec - 1)))
        return f"{am}"

def render_tabla_historial_interactiva(data_list, key_prefix="hist"):
    if not data_list:
        st.info("💡 No hay apuestas en esta categoría.")
        return
        
    for row in data_list:
        id_item = row.get("id")
        estado = row.get("estado", "PENDING")
        badge_color = "#00ff66" if estado == "WIN" else ("#ff3366" if estado == "LOSS" else "#f5d742")
        badge_bg = "rgba(0,255,102,0.15)" if estado == "WIN" else ("rgba(255,51,102,0.15)" if estado == "LOSS" else "rgba(245,215,66,0.15)")
        
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 1, 2, 1.8, 0.8, 1.2, 1, 0.6])
        with c1: st.write(f"<span style='color:#94a3b8; font-size:12px;'>{row.get('fecha','')}</span>", unsafe_allow_html=True)
        with c2: st.write(f"**{row.get('deporte','')}**")
        with c3: st.write(f"<span style='color:#ffffff; font-weight:800;'>{row.get('partido','')}</span>", unsafe_allow_html=True)
        with c4: st.write(row.get('mercado',''))
        with c5: st.write(f"<span style='color:#f5d742; font-weight:900;'>{row.get('momio','')}</span>", unsafe_allow_html=True)
        with c6: st.write(row.get('resultado_real','En Espera'))
        with c7: st.write(f"<span style='color:{badge_color}; background:{badge_bg}; padding: 4px 8px; border-radius:4px; font-weight:900; font-size:11px;'>{estado}</span>", unsafe_allow_html=True)
        with c8:
            if st.button("🗑️", key=f"del_{key_prefix}_{id_item}", help="Eliminar apuesta"):
                eliminar_apuesta(id_item)
        st.markdown("<hr style='margin: 4px 0; border:0; border-top:1px solid #2d3833;'>", unsafe_allow_html=True)

# BARRA SUPERIOR
c_top_label, c_top_radio = st.columns([1, 3])
with c_top_label:
    st.markdown("<div class='top-deporte-title'>SELECCIONAR DEPORTE:</div>", unsafe_allow_html=True)
with c_top_radio:
    deporte = st.radio("", ["⚾ MLB Sabermétrico (API AUTO)", "⚽ Liga MX (API LIVE)"], horizontal=True, label_visibility="collapsed")

es_mlb = "MLB" in deporte
deporte_actual_key = "MLB" if es_mlb else "Liga MX"

st.markdown("<br>", unsafe_allow_html=True)
col_izq, col_der = st.columns([1, 1], gap="large")

# ==========================================
# SECCIÓN MLB
# ==========================================
if es_mlb:
    EQUIPOS = EQUIPOS_MLB
    JERSEYS = JERSEYS_MLB
    
    with col_izq:
        st.markdown("""
        <div style="display:flex; align-items:center; margin-bottom:15px;">
            <span style="font-size:38px; margin-right:12px;">⚾</span>
            <span class="header-text-left">SISTEMA AUDITOR ANTI-TRAMPA MLB</span>
        </div>
        """, unsafe_allow_html=True)
        
        c_sel1, c_sel2 = st.columns(2)
        lista_equipos = sorted(list(EQUIPOS.keys()))
        
        local_nombre = c_sel1.selectbox("EQUIPO LOCAL (HOME)", lista_equipos, index=lista_equipos.index("Philadelphia Phillies") if "Philadelphia Phillies" in lista_equipos else 0)
        visita_opciones = [eq for eq in lista_equipos if eq != local_nombre]
        visita_nombre = c_sel2.selectbox("EQUIPO VISITANTE (AWAY)", visita_opciones, index=visita_opciones.index("LA Dodgers") if "LA Dodgers" in visita_opciones else 0)

        eq_local_base, eq_visita_base = EQUIPOS[local_nombre], EQUIPOS[visita_nombre]
        pitcher_loc_auto, pitcher_vis_auto = obtener_abridores_mlb_hoy(eq_local_base["id"], eq_visita_base["id"])

        st.markdown(f"""
        <div style="background:#242a26; border-left:4px solid #f5d742; padding:10px 14px; border-radius:6px; margin-bottom:12px; font-size:13px; color:#ffffff;">
            <b style="color:#f5d742;">⚾ ABRIDORES HOY:</b><br>
            • {local_nombre}: <b style="color:#00ff66;">{pitcher_loc_auto}</b><br>
            • {visita_nombre}: <b style="color:#00ff66;">{pitcher_vis_auto}</b>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📊 PARÁMETROS DE ABRIDORES Y CLIMA", expanded=True):
            st.markdown(f"<p style='color:#f5d742; font-weight:800;'>MÉTRICAS {pitcher_loc_auto.upper()} ({local_nombre[:3]})</p>", unsafe_allow_html=True)
            pl1, pl2, pl3, pl4, pl5, pl6 = st.columns(6)
            w_loc = pl1.number_input("W", value=int(eq_local_base["w"]), step=1, key="w_loc")
            l_loc = pl2.number_input("L", value=int(eq_local_base["l"]), step=1, key="l_loc")
            ip_loc = pl3.number_input("IP", value=float(eq_local_base["ip"]), step=0.1, key="ip_loc")
            era_loc = pl4.number_input("xERA", value=float(eq_local_base["era_base"]), step=0.01, format="%.2f", key="era_loc")
            whip_loc = pl5.number_input("WHIP", value=float(eq_local_base["whip"]), step=0.01, format="%.2f", key="whip_loc")
            k_loc = pl6.number_input("K Total", value=int(eq_local_base["k"]), step=1, key="k_loc")

            st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:10px;'>MÉTRICAS {pitcher_vis_auto.upper()} ({visita_nombre[:3]})</p>", unsafe_allow_html=True)
            pv1, pv2, pv3, pv4, pv5, pv6 = st.columns(6)
            w_vis = pv1.number_input("W", value=int(eq_visita_base["w"]), step=1, key="w_vis")
            l_vis = pv2.number_input("L", value=int(eq_visita_base["l"]), step=1, key="l_vis")
            ip_vis = pv3.number_input("IP", value=float(eq_visita_base["ip"]), step=0.1, key="ip_vis")
            era_vis = pv4.number_input("xERA", value=float(eq_visita_base["era_base"]), step=0.01, format="%.2f", key="era_vis")
            whip_vis = pv5.number_input("WHIP", value=float(eq_visita_base["whip"]), step=0.01, format="%.2f", key="whip_vis")
            k_vis = pv6.number_input("K Total", value=int(eq_visita_base["k"]), step=1, key="k_vis")

            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:10px;'>CONDICIONES DEL ESTADIO Y CLIMA</p>", unsafe_allow_html=True)
            tipo_estadio = st.radio("Tipo de Estadio:", ["Abierto (Open Air)", "Techo Cerrado / Domo (Indoor)"], horizontal=True, key="tipo_estadio")
            es_domo = "Domo" in tipo_estadio or "Cerrado" in tipo_estadio

            cw1, cw2, cw3, cw4 = st.columns(4)
            viento_kmh = cw1.number_input("Viento (km/h)", value=0 if es_domo else 16, step=1, disabled=es_domo)
            viento_dir = cw2.selectbox("Dirección Viento", ["A favor (Out)", "En contra (In)", "Cruzado (Cross)"], disabled=es_domo)
            temp_c = cw3.number_input("Temperatura (°C)", value=21.0 if es_domo else 34.7, step=0.1, format="%.1f")
            precip_pct = cw4.number_input("Precipitación (%)", value=0, step=5, disabled=es_domo)

        if es_domo: mult_clima = 1.0
        else:
            mult_viento = 1.0
            if "favor" in viento_dir: mult_viento += (viento_kmh * 0.006)
            elif "contra" in viento_dir: mult_viento -= (viento_kmh * 0.006)
            mult_temp = 1.0 + ((temp_c - 21.0) * 0.003)
            mult_clima = mult_viento * mult_temp

        xr_local = ((eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * (whip_vis / 1.25) * 4.30) * mult_clima
        xr_visita = ((eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * (whip_loc / 1.25) * 4.10) * mult_clima

        max_c = 16
        matrix_mlb = np.zeros((max_c, max_c))
        for x in range(max_c):
            for y in range(max_c): matrix_mlb[x, y] = poisson.pmf(x, xr_local) * poisson.pmf(y, xr_visita)
        matrix_mlb /= np.sum(matrix_mlb)

        xr_loc_f5 = (eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * 2.35 * mult_clima
        xr_vis_f5 = (eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * 2.20 * mult_clima
        matrix_f5 = np.zeros((max_c, max_c))
        for x in range(max_c):
            for y in range(max_c): matrix_f5[x, y] = poisson.pmf(x, xr_loc_f5) * poisson.pmf(y, xr_vis_f5)
        matrix_f5 /= np.sum(matrix_f5)

        with st.expander("⚙️ CAPTURA DE MOMIOS DEL CASINO", expanded=True):
            formato_m = st.radio("Formato Momios:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True, key="f_mlb")
            es_dec = "Decimal" in formato_m
            tipo_str = "Decimal" if es_dec else "Americano"
            
            st.markdown("<p style='color:#f5d742; font-weight:800;'>1. MONEYLINE (ML)</p>", unsafe_allow_html=True)
            f1_1, f1_2 = st.columns(2)
            m_ml_loc_in = f1_1.number_input(f"ML {local_nombre.upper()}", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
            m_ml_vis_in = f1_2.number_input(f"ML {visita_nombre.upper()}", value=2.050 if es_dec else 105, format="%.3f" if es_dec else "%d")
            
            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>2. TOTAL DE CARRERAS (O/U)</p>", unsafe_allow_html=True)
            f2_1, f2_2, f2_3 = st.columns(3)
            linea_tot_mlb = f2_1.selectbox("Línea Total", ["8.5", "7.5", "9.5"])
            m_over_tot_in = f2_2.number_input("OVER Total", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")
            m_under_tot_in = f2_3.number_input("UNDER Total", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")

            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>3. RUN LINE (-1.5 / +1.5)</p>", unsafe_allow_html=True)
            f3_1, f3_2 = st.columns(2)
            m_rl_loc_minus_in = f3_1.number_input(f"RL {local_nombre[:3]} -1.5", value=2.450 if es_dec else 145, format="%.3f" if es_dec else "%d")
            m_rl_loc_plus_in = f3_2.number_input(f"RL {local_nombre[:3]} +1.5", value=1.500 if es_dec else -200, format="%.3f" if es_dec else "%d")

            opciones_ks = ["0.5", "1.5", "2.5", "3.5", "4.5", "5.5", "6.5", "7.5", "8.5"]
            st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:8px;'>4. PONCHES (K'S): {pitcher_loc_auto.upper()}</p>", unsafe_allow_html=True)
            fk1, fk2 = st.columns(2)
            linea_k_loc = fk1.selectbox(f"Línea K's ({pitcher_loc_auto})", opciones_ks, index=5, key="lk_loc")
            m_k_loc_over_in = fk2.number_input("Over K's", value=1.870 if es_dec else -115, format="%.3f" if es_dec else "%d", key="mk_loc_o")

            opciones_outs = ["13.5", "14.5", "15.5", "17.5", "18.5"]
            st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:8px;'>5. OUTS: {pitcher_loc_auto.upper()}</p>", unsafe_allow_html=True)
            fo1, fo2 = st.columns(2)
            linea_outs_loc = fo1.selectbox(f"Línea Outs ({pitcher_loc_auto})", opciones_outs, index=2, key="lo_loc")
            m_outs_loc_over_in = fo2.number_input("Over Outs", value=1.750 if es_dec else -133, format="%.3f" if es_dec else "%d", key="mo_loc_o")

            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>6. PRIMERAS 5 ENTRADAS (F5)</p>", unsafe_allow_html=True)
            m_f5_loc_in = st.number_input(f"F5 ML {local_nombre[:3]}", value=1.800 if es_dec else -125, format="%.3f" if es_dec else "%d")

            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>7. MERCADO 1ER INNING (NRFI / YRFI)</p>", unsafe_allow_html=True)
            m_nrfi_in = st.number_input("NRFI (No Run 1st Inn)", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")

            st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>8, 9 Y 10. PROPS DE BATEADOR</p>", unsafe_allow_html=True)
            fb1, fb2, fb3 = st.columns(3)
            nombre_bat = fb1.text_input("Bateador Star", value="Bryce Harper")
            m_hit_bat_in = fb2.number_input("1+ Hit (H > 0.5)", value=1.450 if es_dec else -222, format="%.3f" if es_dec else "%d")
            m_run_bat_in = fb3.number_input("1+ Carrera (R > 0.5)", value=1.850 if es_dec else -118, format="%.3f" if es_dec else "%d")
            m_hrbi_bat_in = st.number_input("1.5+ H+R+RBI", value=1.750 if es_dec else -133, format="%.3f" if es_dec else "%d")

            m_ml_loc = to_decimal(m_ml_loc_in, tipo_str)
            m_ml_vis = to_decimal(m_ml_vis_in, tipo_str)
            m_over_tot = to_decimal(m_over_tot_in, tipo_str)
            m_rl_loc_minus = to_decimal(m_rl_loc_minus_in, tipo_str)
            m_rl_loc_plus = to_decimal(m_rl_loc_plus_in, tipo_str)
            m_k_loc_over = to_decimal(m_k_loc_over_in, tipo_str)
            m_outs_loc_over = to_decimal(m_outs_loc_over_in, tipo_str)
            m_f5_loc = to_decimal(m_f5_loc_in, tipo_str)
            m_nrfi = to_decimal(m_nrfi_in, tipo_str)
            m_hit_bat = to_decimal(m_hit_bat_in, tipo_str)
            m_run_bat = to_decimal(m_run_bat_in, tipo_str)
            m_hrbi_bat = to_decimal(m_hrbi_bat_in, tipo_str)

    with col_der:
        st.markdown("""
        <div style="display:flex; align-items:center; margin-bottom:15px;">
            <span style="font-size:32px; margin-right:10px;">👑</span>
            <span class="header-text-right">MATRIZ DE RIESGO Y AUDITORÍA ANTI-TRAMPA</span>
        </div>
        """, unsafe_allow_html=True)

        prob_ml_loc = np.sum(np.tril(matrix_mlb, -1))
        prob_ml_vis = np.sum(np.triu(matrix_mlb, 1))

        tot_target = float(linea_tot_mlb)
        prob_tot_over = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if x + y > tot_target])

        prob_rl_loc_minus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (x - y) >= 2])
        prob_rl_loc_plus = np.sum([matrix_mlb[x, y] for x in range(max_c) for y in range(max_c) if (x - y) >= -1])

        k_target_loc = float(linea_k_loc)
        k_rate_loc = (k_loc / ip_loc) if ip_loc > 0 else 1.0
        lambda_k_loc = k_rate_loc * 5.83
        prob_k_loc_over = 1.0 - poisson.cdf(int(k_target_loc), lambda_k_loc)

        outs_target_loc = float(linea_outs_loc)
        prob_outs_loc_over = 1.0 - poisson.cdf(int(outs_target_loc), 17.5)

        prob_f5_loc = np.sum(np.tril(matrix_f5, -1))

        xr_1st_inn = (xr_local + xr_visita) * 0.13
        prob_nrfi = poisson.pmf(0, xr_1st_inn)

        prob_hit_bat = 0.78
        prob_run_bat = 0.52
        prob_hrbi_bat = 0.61

        mercados_evaluados = [
            {"name": f"1. Moneyline {local_nombre}", "prob": prob_ml_loc, "m_casa": m_ml_loc, "linea": "ML"},
            {"name": f"1. Moneyline {visita_nombre}", "prob": prob_ml_vis, "m_casa": m_ml_vis, "linea": "ML"},
            {"name": f"2. Total Carreras Over {tot_target}", "prob": prob_tot_over, "m_casa": m_over_tot, "linea": str(tot_target)},
            {"name": f"3. Run Line {local_nombre} -1.5", "prob": prob_rl_loc_minus, "m_casa": m_rl_loc_minus, "linea": "-1.5"},
            {"name": f"3. Run Line {local_nombre} +1.5", "prob": prob_rl_loc_plus, "m_casa": m_rl_loc_plus, "linea": "+1.5"},
            {"name": f"4. Ponches {pitcher_loc_auto} Over {linea_k_loc}", "prob": prob_k_loc_over, "m_casa": m_k_loc_over, "linea": linea_k_loc},
            {"name": f"5. Outs {pitcher_loc_auto} Over {linea_outs_loc}", "prob": prob_outs_loc_over, "m_casa": m_outs_loc_over, "linea": linea_outs_loc},
            {"name": f"6. F5 ML {local_nombre}", "prob": prob_f5_loc, "m_casa": m_f5_loc, "linea": "F5 ML"},
            {"name": f"7. NRFI 1st Inning", "prob": prob_nrfi, "m_casa": m_nrfi, "linea": "NRFI"},
            {"name": f"8. Hit {nombre_bat} (H > 0.5)", "prob": prob_hit_bat, "m_casa": m_hit_bat, "linea": "0.5"},
            {"name": f"9. Run {nombre_bat} (R > 0.5)", "prob": prob_run_bat, "m_casa": m_run_bat, "linea": "0.5"},
            {"name": f"10. H+R+RBI {nombre_bat} (> 1.5)", "prob": prob_hrbi_bat, "m_casa": m_hrbi_bat, "linea": "1.5"},
        ]

        partido_nombre_mlb = f"{local_nombre} vs {visita_nombre}"
        filas_tabla = []

        for item in mercados_evaluados:
            p = item["prob"]
            m_casa = item["m_casa"]
            ev = (p * m_casa) - 1.0
            momio_real_dec = 1.0 / p if p > 0 else 99.0
            prob_impl_casa = 1.0 / m_casa if m_casa > 0 else 0.0
            brecha_ev = (p - prob_impl_casa) * 100

            # 1. MATRIZ DE RIESGO DE 3 NIVELES
            if 0.75 <= p <= 0.90:
                certeza_txt = "HIGH CONFIDENCE (75%-90%)"
                badge_certeza = "<span class='badge-high'>🟢 HIGH</span>"
            elif 0.60 <= p <= 0.74:
                certeza_txt = "MEDIUM PROBABILITY (60%-74%)"
                badge_certeza = "<span class='badge-med'>🟠 MEDIUM</span>"
            else:
                certeza_txt = "LOW PROBABILITY (10%-59%)"
                badge_certeza = "<span class='badge-low'>🔴 LOW</span>"

            # 2. AUDITORÍA ANTI-TRAMPA
            if brecha_ev > 25.0:
                auditoria = "⚠️ ALERTA DE FACTOR OCULTO"
            elif ev < -0.10:
                auditoria = "🚨 RIESGO DE CORRECCIÓN"
            else:
                auditoria = "🛡️ VALOR LIMPIO"

            # 3. VALIDACIÓN DORADA
            es_estrella = (0.75 <= p <= 0.90) and (auditoria == "🛡️ VALOR LIMPIO") and (ev > 0.0)

            filas_tabla.append({
                "Mercado": item["name"],
                "Momio Casa": f"{m_casa:.3f}",
                "Momio Real Calculado": f"{momio_real_dec:.3f}",
                "Probabilidad Modelo": f"{p*100:.1f}%",
                "Filtro de Certeza": certeza_txt,
                "Validación Anti-Trampa": auditoria,
                "Estrella": es_estrella,
                "ev": ev,
                "linea": item["linea"]
            })

            card_class = "card-star" if es_estrella else "card-pro"
            badge_estrella_html = "<span class='badge-star'>💎 APUESTA ESTRELLA (+EV / ERROR DE CUOTA)</span>" if es_estrella else ""

            c_c1, c_c2 = st.columns([4, 1])
            with c_c1:
                st.markdown(f"""
                <div class="{card_class}">
                    {badge_estrella_html}
                    <div style="font-weight: 800; font-size: 14px; color: #ffffff;">{item["name"]}</div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:4px;">
                        Prob: <b>{p*100:.1f}%</b> · Real: <b>{momio_real_dec:.2f}</b> · Casa: <b>{m_casa:.2f}</b> · <b style="color:#00ff66;">EV {ev*100:+.1f}%</b><br>
                        {badge_certeza} · <b>{auditoria}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c_c2:
                if st.button("➕ APUESTA", key=f"btn_mlb_aud_{item['name']}"):
                    registrar_apuesta("MLB", partido_nombre_mlb, local_nombre, visita_nombre, item["name"], item["linea"], m_casa, ev)

        st.markdown("<p style='color:#f5d742; font-weight:900; margin-top:20px;'>📋 TABLA AUDITADA DE 10 MERCADOS</p>", unsafe_allow_html=True)
        df_resumen = pd.DataFrame(filas_tabla)[["Mercado", "Momio Casa", "Momio Real Calculado", "Probabilidad Modelo", "Filtro de Certeza", "Validación Anti-Trampa"]]
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)

# ==========================================
# SECCIÓN LIGA MX
# ==========================================
else:
    EQUIPOS = obtener_stats_liga_mx_api()
    JERSEYS = JERSEYS_LIGA_MX
    with col_izq:
        st.markdown("<div class='header-text-left'>ANALISIS PRO-LIGA MX</div>", unsafe_allow_html=True)
        st.info("💡 Cambia a 'MLB Sabermétrico' arriba para el Auditor Anti-Trampa.")

# ==========================================
# PANEL INFERIOR: TRACKER EN 3 PESTAÑAS
# ==========================================
st.markdown("<br><hr style='border:1px solid #2d3833;'><br>", unsafe_allow_html=True)
c_head1, c_head2 = st.columns([3, 1])
with c_head1: 
    st.markdown(f"<h3 style='color:#f5d742;'>📈 TRACKER DE APUESTAS: <span style='color:#00ff66;'>{deporte_actual_key.upper()}</span></h3>", unsafe_allow_html=True)
with c_head2:
    if st.button("🔍 VERIFICAR RESULTADOS EN VIVO", use_container_width=True):
        num_act = auto_verificar_apuestas()
        st.toast(f"Resultados actualizados ({num_act} cambios)", icon="⚽")

historial = cargar_base_datos()
filtro_dep = st.radio("Filtrar Tracker Por:", ["Pestaña Actual (" + deporte_actual_key + ")", "Sólo Liga MX", "Sólo MLB", "Ver Todo (Global)"], horizontal=True)

if "Pestaña Actual" in filtro_dep: historial_filtrado = [x for x in historial if x.get("deporte") == deporte_actual_key]
elif "Liga MX" in filtro_dep: historial_filtrado = [x for x in historial if x.get("deporte") == "Liga MX"]
elif "MLB" in filtro_dep: historial_filtrado = [x for x in historial if x.get("deporte") == "MLB"]
else: historial_filtrado = historial

if len(historial_filtrado) == 0:
    st.info(f"💡 No hay apuestas registradas para {filtro_dep}.")
else:
    list_pending = [x for x in historial_filtrado if x.get("estado") == "PENDING"]
    list_win = [x for x in historial_filtrado if x.get("estado") == "WIN"]
    list_loss = [x for x in historial_filtrado if x.get("estado") == "LOSS"]

    wins = len(list_win)
    losses = len(list_loss)
    pending = len(list_pending)
    totales_resueltas = wins + losses
    win_rate = (wins / totales_resueltas * 100) if totales_resueltas > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Picks Guardados", len(historial_filtrado))
    m2.metric("Efectividad (Win Rate)", f"{win_rate:.1f}%", f"{wins} W - {losses} L")
    m3.metric("En Espera (Pendientes)", pending)
    m4.metric("Estatus Deporte", f"🟢 Filtrado: {filtro_dep}")

    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Ganadas (WIN)', 'Perdidas (LOSS)', 'Pendientes (PENDING)'],
            values=[wins, losses, pending], hole=.5,
            marker=dict(colors=['#00ff66', '#ff3366', '#475569'])
        )])
        fig_pie.update_layout(title=dict(text=f"Distribución ({filtro_dep})", font=dict(color='#f5d742')), height=230, paper_bgcolor='#242a26', font=dict(color='#ffffff'))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        tab_pending, tab_win, tab_loss = st.tabs([f"⏳ PENDIENTES ({pending})", f"✅ WIN ({wins})", f"❌ LOSS ({losses})"])
        with tab_pending: render_tabla_historial_interactiva(list_pending, key_prefix="pending")
        with tab_win: render_tabla_historial_interactiva(list_win, key_prefix="win")
        with tab_loss: render_tabla_historial_interactiva(list_loss, key_prefix="loss")
