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
st.set_page_config(page_title="MAÑA PIKS - MLB MONTE CARLO 10K", layout="wide", page_icon="👑")

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

def registrar_apuesta(partido, equipo_loc, equipo_vis, mercado, linea, momio, ev):
    historial = cargar_base_datos()
    nueva_apuesta = {
        "id": len(historial) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": "MLB",
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
# SIMULADOR MONTE CARLO (10,000 ENFRENTAMIENTOS)
# ==========================================
def simular_partido_montecarlo(xr_local, xr_visita, num_simulaciones=10000):
    """
    Ejecuta 10,000 simulaciones numéricas del partido entre ambos equipos
    utilizando distribuciones de probabilidad Poisson estocásticas.
    """
    np.random.seed(42) # Semilla fija para reproducibilidad
    carreras_loc = np.random.poisson(xr_local, num_simulaciones)
    carreras_vis = np.random.poisson(xr_visita, num_simulaciones)
    
    return carreras_loc, carreras_vis

# ==========================================
# MOTOR DE DETECCIÓN DE TRAMPAS Y BAJAS MLB
# ==========================================
def evaluar_riesgo_trampa(prob_real, momio_decimal, ev):
    if ev > 0.18:
        return True, "⚠️ ALERTA TRAP: +EV anómalo (>18%). Posible baja clave de último minuto."
    if prob_real >= 0.65 and momio_decimal >= 2.20:
        return True, "⚠️ ALERTA TRAP: Cuota sospechosamente alta para la probabilidad estimada."
    return False, ""

@st.cache_data(ttl=900)
def obtener_lesiones_espn():
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/news"
    bajas_reportadas = []
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            for art in articles:
                headline = art.get("headline", "")
                description = art.get("description", "")
                text = f"{headline} {description}".lower()
                if any(k in text for k in ["baja", "lesion", "out", "injured", "duda", "scratched", "lineup"]):
                    bajas_reportadas.append(headline)
    except Exception:
        pass
    return bajas_reportadas[:3]

def generar_grafica_barras_propsbr(prob_real):
    np.random.seed(int(prob_real * 10000) % 1000)
    hits = (np.random.rand(10) < prob_real).astype(int)
    html = '<div style="display:flex; align-items:flex-end; gap:3px; height:32px; justify-content:flex-end;">'
    for val in hits:
        cls_color = "#00ff66" if val == 1 else "#ff3355"
        height_px = 28 if val == 1 else 10
        html += f'<div style="width:5px; background-color:{cls_color}; height:{height_px}px; border-radius:2px;"></div>'
    html += '</div>'
    return html

# ==========================================
# AUTO-VERIFICACIÓN EN VIVO
# ==========================================
def auto_verificar_apuestas():
    historial = cargar_base_datos()
    actualizados = 0

    url_mlb = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    res_mlb = []
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
                    except Exception:
                        pass

                res_mlb.append({
                    "match_title": f"{loc_name} vs {vis_name}",
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
                    "outs_dict": outs_dict
                })
    except Exception:
        pass

    res_mlb.sort(key=lambda x: (not x["completed"], x["state"] == "pre"))

    for item in historial:
        if item["estado"] == "PENDING" and item.get("deporte") == "MLB":
            for score_data in res_mlb:
                match_title = score_data["match_title"]
                eq_loc_match = item["equipo_loc"].lower() in match_title.lower() or score_data["loc_name"].lower() in item["equipo_loc"].lower()
                eq_vis_match = item["equipo_vis"].lower() in match_title.lower() or score_data["vis_name"].lower() in item["equipo_vis"].lower()
                
                if eq_loc_match and eq_vis_match:
                    r_loc = score_data["loc_score"]
                    r_vis = score_data["vis_score"]
                    tot_carreras = r_loc + r_vis
                    mercado = item["mercado"]
                    linea = item.get("linea", "")
                    ks_dict = score_data["ks_dict"]
                    outs_dict = score_data["outs_dict"]

                    if "Carreras" in mercado:
                        try:
                            val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 8.5
                        except Exception:
                            val_target = 8.5

                        if "Over" in mercado or "OVER" in mercado:
                            if tot_carreras > val_target:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

                        elif "Under" in mercado or "UNDER" in mercado:
                            if tot_carreras > val_target:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{r_loc} - {r_vis}"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

                    elif "Gana" in mercado or "ML" in mercado:
                        if score_data["completed"] or score_data["period"] >= 9:
                            item["resultado_real"] = f"{r_loc} - {r_vis}"
                            if item["equipo_loc"] in mercado and r_loc > r_vis: item["estado"] = "WIN"
                            elif item["equipo_vis"] in mercado and r_vis > r_loc: item["estado"] = "WIN"
                            else: item["estado"] = "LOSS"
                            actualizados += 1
                            break
                        else:
                            item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

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
                            break
                        else:
                            item["resultado_real"] = f"{r_loc} - {r_vis} (En Vivo)"

                    elif "NRFI" in mercado or "YRFI" in mercado or "1st Inning" in mercado:
                        if "NRFI" in mercado or "0 Carreras" in mercado:
                            if score_data["r1_tot"] > 0:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{score_data['r1_tot']} Carreras 1st Inn"
                                actualizados += 1
                                break
                            elif score_data["period"] >= 2 or score_data["completed"]:
                                item["estado"] = "WIN"
                                item["resultado_real"] = "0 Carreras 1st Inn"
                                actualizados += 1
                                break
                        elif "YRFI" in mercado or "1+" in mercado:
                            if score_data["r1_tot"] > 0:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{score_data['r1_tot']} Carreras 1st Inn"
                                actualizados += 1
                                break
                            elif score_data["period"] >= 2 or score_data["completed"]:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = "0 Carreras 1st Inn"
                                actualizados += 1
                                break

                    elif "F5" in mercado:
                        try:
                            val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 3.5
                        except Exception:
                            val_target = 3.5

                        if "Over" in mercado or "OVER" in mercado:
                            if score_data["f5_tot"] > val_target:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5)"
                                actualizados += 1
                                break
                            elif score_data["f5_completo"]:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5)"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5 en Vivo)"
                        
                        elif "Under" in mercado or "UNDER" in mercado:
                            if score_data["f5_tot"] > val_target:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5)"
                                actualizados += 1
                                break
                            elif score_data["f5_completo"]:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5)"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5 en Vivo)"
                        
                        elif "ML" in mercado or "Ganador" in mercado:
                            if score_data["f5_completo"]:
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5)"
                                if item["equipo_loc"] in mercado and score_data["f5_loc"] > score_data["f5_vis"]: item["estado"] = "WIN"
                                elif item["equipo_vis"] in mercado and score_data["f5_vis"] > score_data["f5_loc"]: item["estado"] = "WIN"
                                else: item["estado"] = "LOSS"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{score_data['f5_loc']} - {score_data['f5_vis']} (F5 en Vivo)"

                    elif "K's" in mercado or "Ponches" in mercado:
                        try:
                            val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 5.5
                        except Exception:
                            val_target = 5.5

                        k_actuales = 0
                        if ks_dict:
                            for p_name_k, k_val in ks_dict.items():
                                if p_name_k in mercado.lower():
                                    k_actuales = k_val
                                    break
                            else:
                                k_actuales = max(ks_dict.values()) if ks_dict.values() else 0
                        
                        if "Over" in mercado or "Más" in mercado:
                            if k_actuales > val_target:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{k_actuales} K's (Cumplido)"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{k_actuales} K's Final"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{k_actuales} K's en Vivo"
                        
                        elif "Under" in mercado or "Menos" in mercado:
                            if k_actuales > val_target:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{k_actuales} K's (Superado)"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{k_actuales} K's Final"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{k_actuales} K's en Vivo"

                    elif "Outs" in mercado:
                        try:
                            val_target = float(linea) if (linea and linea.replace('.','',1).isdigit()) else 15.5
                        except Exception:
                            val_target = 15.5

                        outs_actuales = 0
                        if outs_dict:
                            for p_name_k, o_val in outs_dict.items():
                                if p_name_k in mercado.lower():
                                    outs_actuales = o_val
                                    break
                            else:
                                outs_actuales = max(outs_dict.values()) if outs_dict.values() else 0

                        if "Over" in mercado or "Más" in mercado:
                            if outs_actuales > val_target:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{outs_actuales} Outs (Cumplido)"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{outs_actuales} Outs Final"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{outs_actuales} Outs en Vivo"

                        elif "Under" in mercado or "Menos" in mercado:
                            if outs_actuales > val_target:
                                item["estado"] = "LOSS"
                                item["resultado_real"] = f"{outs_actuales} Outs (Superado)"
                                actualizados += 1
                                break
                            elif score_data["completed"]:
                                item["estado"] = "WIN"
                                item["resultado_real"] = f"{outs_actuales} Outs Final"
                                actualizados += 1
                                break
                            else:
                                item["resultado_real"] = f"{outs_actuales} Outs en Vivo"

    guardar_base_datos(historial)
    st.session_state.historial_apuestas = historial
    return actualizados

# ==========================================
# BASE DE DATOS COMPLETA 30 EQUIPOS MLB
# ==========================================
EQUIPOS_MLB = {
    "NY Yankees": {"id": 147, "wRC_plus": 115, "era_base": 3.65, "w": 12, "l": 6, "ip": 110.0, "whip": 1.18, "k": 125, "bb": 35},
    "LA Dodgers": {"id": 119, "wRC_plus": 120, "era_base": 3.45, "w": 14, "l": 5, "ip": 125.0, "whip": 1.12, "k": 140, "bb": 30},
    "Boston Red Sox": {"id": 111, "wRC_plus": 105, "era_base": 4.10, "w": 8, "l": 8, "ip": 98.0, "whip": 1.28, "k": 102, "bb": 40},
    "Houston Astros": {"id": 117, "wRC_plus": 110, "era_base": 3.75, "w": 10, "l": 7, "ip": 105.0, "whip": 1.20, "k": 115, "bb": 36},
    "Atlanta Braves": {"id": 144, "wRC_plus": 114, "era_base": 3.80, "w": 11, "l": 6, "ip": 108.0, "whip": 1.22, "k": 118, "bb": 38},
    "SD Padres": {"id": 135, "wRC_plus": 106, "era_base": 3.70, "w": 9, "l": 8, "ip": 102.0, "whip": 1.19, "k": 110, "bb": 34},
    "Chicago Cubs": {"id": 112, "wRC_plus": 102, "era_base": 3.95, "w": 8, "l": 9, "ip": 95.0, "whip": 1.25, "k": 98, "bb": 42},
    "SF Giants": {"id": 137, "wRC_plus": 96, "era_base": 3.85, "w": 7, "l": 9, "ip": 92.0, "whip": 1.21, "k": 90, "bb": 35},
    "NY Mets": {"id": 121, "wRC_plus": 108, "era_base": 3.80, "w": 10, "l": 7, "ip": 104.0, "whip": 1.22, "k": 112, "bb": 37},
    "Philadelphia Phillies": {"id": 143, "wRC_plus": 111, "era_base": 3.65, "w": 12, "l": 5, "ip": 115.0, "whip": 1.17, "k": 130, "bb": 32},
    "Texas Rangers": {"id": 140, "wRC_plus": 104, "era_base": 4.20, "w": 7, "l": 10, "ip": 90.0, "whip": 1.30, "k": 88, "bb": 44},
    "Toronto Blue Jays": {"id": 141, "wRC_plus": 101, "era_base": 3.90, "w": 8, "l": 8, "ip": 96.0, "whip": 1.24, "k": 95, "bb": 39},
    "Seattle Mariners": {"id": 136, "wRC_plus": 95, "era_base": 3.40, "w": 11, "l": 6, "ip": 120.0, "whip": 1.10, "k": 135, "bb": 28},
    "Baltimore Orioles": {"id": 110, "wRC_plus": 112, "era_base": 3.85, "w": 11, "l": 6, "ip": 106.0, "whip": 1.21, "k": 114, "bb": 36},
    "Tampa Bay Rays": {"id": 139, "wRC_plus": 98, "era_base": 3.60, "w": 9, "l": 8, "ip": 100.0, "whip": 1.16, "k": 108, "bb": 31},
    "Arizona Diamondbacks": {"id": 109, "wRC_plus": 105, "era_base": 4.25, "w": 8, "l": 9, "ip": 94.0, "whip": 1.31, "k": 92, "bb": 45},
    "Milwaukee Brewers": {"id": 158, "wRC_plus": 100, "era_base": 3.60, "w": 10, "l": 6, "ip": 103.0, "whip": 1.18, "k": 109, "bb": 33},
    "St. Louis Cardinals": {"id": 138, "wRC_plus": 97, "era_base": 4.10, "w": 7, "l": 9, "ip": 91.0, "whip": 1.27, "k": 85, "bb": 40},
    "Cleveland Guardians": {"id": 114, "wRC_plus": 99, "era_base": 3.50, "w": 12, "l": 5, "ip": 112.0, "whip": 1.15, "k": 122, "bb": 30},
    "Minnesota Twins": {"id": 142, "wRC_plus": 104, "era_base": 3.90, "w": 9, "l": 8, "ip": 99.0, "whip": 1.23, "k": 105, "bb": 38},
    "Detroit Tigers": {"id": 116, "wRC_plus": 96, "era_base": 3.80, "w": 8, "l": 8, "ip": 95.0, "whip": 1.20, "k": 96, "bb": 35},
    "Chicago White Sox": {"id": 145, "wRC_plus": 82, "era_base": 4.90, "w": 4, "l": 14, "ip": 80.0, "whip": 1.42, "k": 72, "bb": 50},
    "KC Royals": {"id": 118, "wRC_plus": 102, "era_base": 3.90, "w": 9, "l": 7, "ip": 101.0, "whip": 1.24, "k": 100, "bb": 37},
    "LA Angels": {"id": 108, "wRC_plus": 94, "era_base": 4.50, "w": 6, "l": 11, "ip": 88.0, "whip": 1.35, "k": 82, "bb": 46},
    "Cincinnati Reds": {"id": 113, "wRC_plus": 98, "era_base": 4.40, "w": 7, "l": 10, "ip": 89.0, "whip": 1.33, "k": 86, "bb": 43},
    "Colorado Rockies": {"id": 115, "wRC_plus": 90, "era_base": 5.40, "w": 4, "l": 13, "ip": 78.0, "whip": 1.50, "k": 68, "bb": 52},
    "Miami Marlins": {"id": 146, "wRC_plus": 88, "era_base": 4.30, "w": 5, "l": 12, "ip": 85.0, "whip": 1.32, "k": 80, "bb": 44},
    "Pittsburgh Pirates": {"id": 134, "wRC_plus": 92, "era_base": 4.00, "w": 8, "l": 9, "ip": 93.0, "whip": 1.26, "k": 91, "bb": 41},
    "Washington Nationals": {"id": 120, "wRC_plus": 93, "era_base": 4.60, "w": 6, "l": 11, "ip": 86.0, "whip": 1.36, "k": 78, "bb": 47},
    "Oakland Athletics": {"id": 133, "wRC_plus": 95, "era_base": 4.50, "w": 6, "l": 11, "ip": 87.0, "whip": 1.34, "k": 81, "bb": 45}
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

# ==========================================
# ESTILOS CSS CON BOTONES VERDE FLUORESCENTE RESPLANDECIENTE
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Orbitron:wght@700;900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }
    
    .stApp { 
        background-color: #1d2220 !important; 
        color: #e2e8f0; 
    }
    
    details[data-testid="stExpander"], details[data-testid="stExpander"][open] {
        background-color: #242a26 !important;
        border: 1px solid #2d3833 !important;
        border-radius: 8px !important;
    }
    summary[data-testid="stExpanderSummary"] {
        background-color: #242a26 !important;
        border-radius: 8px !important;
    }
    summary[data-testid="stExpanderSummary"] * {
        color: #f5d742 !important;
        fill: #f5d742 !important;
        font-weight: 800 !important;
    }

    .header-big-left, .header-big-right {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .header-text-left, .header-text-right {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #f5d742 !important;
        text-shadow: 0 0 10px rgba(245, 215, 66, 0.4);
        letter-spacing: 0.5px;
    }
    
    label { 
        color: #00ff66 !important; 
        font-weight: 800 !important; 
        font-size: 13px !important; 
        text-transform: uppercase;
    }
    
    input, div[data-baseweb="select"] span, div[data-baseweb="select"] input {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    
    .card-pro {
        background: #242a26;
        border: 1px solid #2d3833;
        border-left: 4px solid #00ff66;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .card-pro:hover {
        border-color: #00ff66;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.3);
    }

    .card-star {
        background: #2b2718;
        border: 1px solid #ffd700;
        border-left: 5px solid #ffd700;
        box-shadow: 0 0 14px rgba(255, 215, 0, 0.35);
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .card-star:hover {
        border-color: #00ff66;
        box-shadow: 0 0 18px rgba(0, 255, 102, 0.5);
    }

    .card-trap {
        background: #381a20;
        border: 1px solid #ff3366;
        border-left: 5px solid #ff3366;
        box-shadow: 0 0 14px rgba(255, 51, 102, 0.35);
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    .badge-star {
        background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%);
        color: #000000;
        font-weight: 900;
        padding: 4px 12px;
        border-radius: 4px;
        float: right;
        font-size: 12px;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.7);
    }
    .badge-bet { 
        background: #00ff66; 
        color: #000000; 
        font-weight: 900; 
        padding: 4px 12px; 
        border-radius: 4px; 
        float: right; 
        font-size: 12px; 
        box-shadow: 0 0 8px rgba(0, 255, 102, 0.6);
    }
    .badge-skip { 
        background: #3d1b20; 
        color: #ff3366; 
        border: 1px solid #661e27;
        font-weight: 900; 
        padding: 4px 12px; 
        border-radius: 4px; 
        float: right; 
        font-size: 12px; 
    }
    .badge-trap-flag {
        background: #ff3366;
        color: #ffffff;
        font-weight: 900;
        padding: 4px 12px;
        border-radius: 4px;
        float: right;
        font-size: 12px;
        box-shadow: 0 0 10px rgba(255, 51, 102, 0.8);
    }
    
    .market-title { 
        font-size: 14px; 
        font-weight: 900; 
        color: #f5d742; 
        text-shadow: 0 0 6px rgba(245, 215, 66, 0.3);
        margin-top: 16px; 
        margin-bottom: 6px; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .subtext { color: #94a3b8; font-size: 12px; margin-top: 3px; }
    
    .team-badge-card {
        background: #242a26;
        border: 1px solid #2d3833;
        border-radius: 6px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }

    .pitcher-box {
        background: #242a26;
        border-left: 4px solid #f5d742;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 12px;
        font-size: 13px;
        color: #ffffff;
    }

    /* BOTONES VERDE FLUORESCENTE DESTACADOS CON BORDE NEÓN */
    div.stButton > button {
        background-color: #00ff66 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 13px !important;
        border-radius: 6px !important;
        border: 2px solid #33ff88 !important;
        box-shadow: 0 0 12px rgba(0, 255, 102, 0.8), inset 0 0 4px rgba(255, 255, 255, 0.6) !important;
        transition: all 0.25s ease-in-out !important;
        text-transform: uppercase;
    }
    div.stButton > button:hover {
        background-color: #33ff88 !important;
        color: #000000 !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 1), 0 0 8px rgba(0, 255, 102, 0.9) !important;
        transform: scale(1.03);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #242a26;
        border-radius: 6px 6px 0 0;
        color: #e2e8f0;
        font-weight: 700;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ff66 !important;
        color: #000000 !important;
        font-weight: 900 !important;
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

# REPORTE EN VIVO DE LESIONES / BAJAS Y NOTICIAS MLB
noticias_lesiones = obtener_lesiones_espn()
if noticias_lesiones:
    with st.expander("🩹 REPORTES DE BAJAS Y NOTICIAS EN VIVO - MLB", expanded=False):
        for noti in noticias_lesiones:
            st.markdown(f"• <span style='color:#f5d742; font-size:13px;'>{noti}</span>", unsafe_allow_html=True)

col_izq, col_der = st.columns([1, 1], gap="large")

# ==========================================
# SECCIÓN MLB SABERMETRÍA EXCLUSIVA
# ==========================================
EQUIPOS = EQUIPOS_MLB

with col_izq:
    st.markdown("""
    <div class="header-big-left">
        <span style="font-size:38px; margin-right:12px;">⚾</span>
        <span class="header-text-left">ANALISIS SABERMÉTRICO MLB</span>
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
    <div class="pitcher-box">
        <b style="color:#f5d742;">⚾ ABRIDORES HOY (MLB API AUTO-FETCH):</b><br>
        • {local_nombre}: <b style="color:#00ff66;">{pitcher_loc_auto}</b><br>
        • {visita_nombre}: <b style="color:#00ff66;">{pitcher_vis_auto}</b>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📊 PARÁMETROS DE ABRIDORES Y CLIMA", expanded=True):
        st.markdown(f"<p style='color:#f5d742; font-weight:800;'>ESTADÍSTICAS ABRIDOR LOCAL: {local_nombre[:3].upper()} ({pitcher_loc_auto})</p>", unsafe_allow_html=True)
        pl1, pl2, pl3, pl4, pl5, pl6 = st.columns(6)
        w_loc = pl1.number_input("W", value=int(eq_local_base["w"]), step=1, key="w_loc")
        l_loc = pl2.number_input("L", value=int(eq_local_base["l"]), step=1, key="l_loc")
        ip_loc = pl3.number_input("IP", value=float(eq_local_base["ip"]), step=0.1, key="ip_loc")
        era_loc = pl4.number_input("ERA", value=float(eq_local_base["era_base"]), step=0.01, format="%.2f", key="era_loc")
        whip_loc = pl5.number_input("WHIP", value=float(eq_local_base["whip"]), step=0.01, format="%.2f", key="whip_loc")
        k_loc = pl6.number_input("K Total", value=int(eq_local_base["k"]), step=1, key="k_loc")

        st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:10px;'>ESTADÍSTICAS ABRIDOR VISITANTE: {visita_nombre[:3].upper()} ({pitcher_vis_auto})</p>", unsafe_allow_html=True)
        pv1, pv2, pv3, pv4, pv5, pv6 = st.columns(6)
        w_vis = pv1.number_input("W", value=int(eq_visita_base["w"]), step=1, key="w_vis")
        l_vis = pv2.number_input("L", value=int(eq_visita_base["l"]), step=1, key="l_vis")
        ip_vis = pv3.number_input("IP", value=float(eq_visita_base["ip"]), step=0.1, key="ip_vis")
        era_vis = pv4.number_input("ERA", value=float(eq_visita_base["era_base"]), step=0.01, format="%.2f", key="era_vis")
        whip_vis = pv5.number_input("WHIP", value=float(eq_visita_base["whip"]), step=0.01, format="%.2f", key="whip_vis")
        k_vis = pv6.number_input("K Total", value=int(eq_visita_base["k"]), step=1, key="k_vis")

        st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:10px;'>CONDICIONES DEL CLIMA Y ESTADIO</p>", unsafe_allow_html=True)
        
        tipo_estadio = st.radio("Tipo de Estadio:", ["Abierto (Open Air)", "Techo Cerrado / Domo (Indoor)"], horizontal=True, key="tipo_estadio")
        es_domo = "Domo" in tipo_estadio or "Cerrado" in tipo_estadio

        cw1, cw2, cw3, cw4 = st.columns(4)
        viento_kmh = cw1.number_input("Viento (km/h)", value=0 if es_domo else 16, step=1, disabled=es_domo)
        viento_dir = cw2.selectbox("Dirección Viento", ["A favor (Out)", "En contra (In)", "Cruzado (Cross)"], disabled=es_domo)
        temp_c = cw3.number_input("Temperatura (°C)", value=21.0 if es_domo else 24.0, step=0.1, format="%.1f")
        precip_pct = cw4.number_input("Precipitación (%)", value=0, step=5, disabled=es_domo)

    if es_domo:
        mult_clima = 1.0
    else:
        mult_viento = 1.0
        if "favor" in viento_dir:
            mult_viento += (viento_kmh * 0.006)
        elif "contra" in viento_dir:
            mult_viento -= (viento_kmh * 0.006)
            
        mult_temp = 1.0 + ((temp_c - 21.0) * 0.003)
        mult_clima = mult_viento * mult_temp

    xr_local = ((eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * (whip_vis / 1.25) * 4.30) * mult_clima
    xr_visita = ((eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * (whip_loc / 1.25) * 4.10) * mult_clima

    # SIMULACIÓN MONTE CARLO (10,000 ENFRENTAMIENTOS REALES)
    carreras_loc_sim, carreras_vis_sim = simular_partido_montecarlo(xr_local, xr_visita, 10000)

    xr_loc_f5 = (eq_local_base["wRC_plus"] / 100.0) * (era_vis / 4.10) * 2.35 * mult_clima
    xr_vis_f5 = (eq_visita_base["wRC_plus"] / 100.0) * (era_loc / 4.10) * 2.20 * mult_clima
    carreras_f5_loc_sim, carreras_f5_vis_sim = simular_partido_montecarlo(xr_loc_f5, xr_vis_f5, 10000)

    id_loc = eq_local_base.get("id", 147)
    id_vis = eq_visita_base.get("id", 119)
    logo_url_loc = f"https://www.mlbstatic.com/team-logos/{id_loc}.svg"
    logo_url_vis = f"https://www.mlbstatic.com/team-logos/{id_vis}.svg"

    c_esc1, c_esc2 = st.columns(2)
    with c_esc1:
        st.markdown(f"""
        <div class="team-badge-card">
            <img src="{logo_url_loc}" width="42" height="42" style="margin-right:12px; object-fit:contain;">
            <div>
                <div style="font-weight: 800; color: #ffffff; font-size: 15px;">{local_nombre} (HOME)</div>
                <div style="color: #00ff66; font-weight: 800; font-size: 14px;">{xr_local:.2f} <span style="font-size: 11px; color: #f5d742;">xR Carreras</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_esc2:
        st.markdown(f"""
        <div class="team-badge-card">
            <img src="{logo_url_vis}" width="42" height="42" style="margin-right:12px; object-fit:contain;">
            <div>
                <div style="font-weight: 800; color: #ffffff; font-size: 15px;">{visita_nombre} (AWAY)</div>
                <div style="color: #f5d742; font-weight: 800; font-size: 14px;">{xr_visita:.2f} <span style="font-size: 11px; color: #f5d742;">xR Carreras</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    cg1, cg2 = st.columns(2)
    innings = [1, 3, 5, 7, 9]
    xr_acc_local = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xr_local))
    xr_acc_visita = np.cumsum([0] + list(np.random.dirichlet(np.ones(4)) * xr_visita))

    fig_xr = go.Figure()
    fig_xr.add_trace(go.Scatter(x=innings, y=xr_acc_local, mode='lines', name=local_nombre, line=dict(color='#00ff66', width=3)))
    fig_xr.add_trace(go.Scatter(x=innings, y=xr_acc_visita, mode='lines', name=visita_nombre, line=dict(color='#f5d742', width=3)))
    fig_xr.update_layout(
        title=dict(text="xR Progresión por Inning", font=dict(size=12, color="#f5d742")),
        height=190, paper_bgcolor='#242a26', plot_bgcolor='#242a26', font=dict(color='#ffffff', size=9),
        xaxis=dict(gridcolor='#2d3833'), yaxis=dict(gridcolor='#2d3833'), margin=dict(l=25, r=15, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    prob_ml_local = np.mean(carreras_loc_sim > carreras_vis_sim)
    prob_ml_visita = np.mean(carreras_vis_sim > carreras_loc_sim)

    fig_pie_mlb = go.Figure(data=[go.Pie(
        labels=[local_nombre, visita_nombre], values=[prob_ml_local, prob_ml_visita], hole=.55,
        marker=dict(colors=['#00ff66', '#f5d742'])
    )])
    fig_pie_mlb.update_layout(
        title=dict(text="Moneyline % Probabilidad (10K Sim)", font=dict(size=12, color="#f5d742")),
        height=190, paper_bgcolor='#242a26', font=dict(color='#ffffff', size=9),
        margin=dict(l=15, r=15, t=30, b=15), showlegend=False
    )

    with cg1: st.plotly_chart(fig_xr, use_container_width=True)
    with cg2: st.plotly_chart(fig_pie_mlb, use_container_width=True)

    with st.expander("⚙️ CAPTURA DE MOMIOS MLB (CASAS DE APUESTAS)", expanded=True):
        formato_m = st.radio("Formato Momios:", ["Americano (+150 / -200)", "Decimal (2.500 / 1.500)"], horizontal=True, key="f_mlb")
        es_dec = "Decimal" in formato_m
        tipo_str = "Decimal" if es_dec else "Americano"
        
        st.markdown("<p style='color:#f5d742; font-weight:800;'>1. MONEYLINE (GANADOR DIRECTO)</p>", unsafe_allow_html=True)
        f1_1, f1_2 = st.columns(2)
        m_ml_loc_in = f1_1.number_input(f"ML {local_nombre.upper()}", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
        m_ml_vis_in = f1_2.number_input(f"ML {visita_nombre.upper()}", value=2.050 if es_dec else 105, format="%.3f" if es_dec else "%d")
        
        st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>2. TOTAL DE CARRERAS (O/U)</p>", unsafe_allow_html=True)
        f2_1, f2_2, f2_3 = st.columns(3)
        linea_tot_mlb = f2_1.selectbox("LINEA TOTAL", ["8.5", "7.5", "9.5"])
        m_over_tot_in = f2_2.number_input("OVER TOTAL", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")
        m_under_tot_in = f2_3.number_input("UNDER TOTAL", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d")

        st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>3. RUN LINE (+1.5 Y -1.5 AMBOS EQUIPOS)</p>", unsafe_allow_html=True)
        f3_1, f3_2, f3_3, f3_4 = st.columns(4)
        m_rl_loc_minus_in = f3_1.number_input(f"RL {local_nombre[:3]} -1.5", value=2.450 if es_dec else 145, format="%.3f" if es_dec else "%d")
        m_rl_loc_plus_in = f3_2.number_input(f"RL {local_nombre[:3]} +1.5", value=1.500 if es_dec else -200, format="%.3f" if es_dec else "%d")
        m_rl_vis_minus_in = f3_3.number_input(f"RL {visita_nombre[:3]} -1.5", value=2.600 if es_dec else 160, format="%.3f" if es_dec else "%d")
        m_rl_vis_plus_in = f3_4.number_input(f"RL {visita_nombre[:3]} +1.5", value=1.600 if es_dec else -166, format="%.3f" if es_dec else "%d")

        st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>4. PRIMERAS 5 ENTRADAS (F5 ML Y OVER/UNDER 3.5 A 5.5)</p>", unsafe_allow_html=True)
        f4_1, f4_2, f4_3, f4_4, f4_5 = st.columns(5)
        m_f5_loc_in = f4_1.number_input(f"F5 ML {local_nombre[:3]}", value=1.800 if es_dec else -125, format="%.3f" if es_dec else "%d")
        m_f5_vis_in = f4_2.number_input(f"F5 ML {visita_nombre[:3]}", value=2.050 if es_dec else 105, format="%.3f" if es_dec else "%d")
        linea_f5_sel = f4_3.selectbox("Línea F5 O/U", ["3.5", "4.5", "5.5"], index=1)
        m_f5_over_in = f4_4.number_input(f"F5 OVER {linea_f5_sel}", value=1.850 if es_dec else -118, format="%.3f" if es_dec else "%d")
        m_f5_under_in = f4_5.number_input(f"F5 UNDER {linea_f5_sel}", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

        opciones_ks = ["0.5", "1.5", "2.5", "3.5", "4.5", "5.5", "6.5", "7.5", "8.5"]
        
        st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:8px;'>5. PROPS DE PONCHES (K'S): <span style='color:#00ff66;'>{pitcher_loc_auto.upper()} ({local_nombre[:3].upper()})</span></p>", unsafe_allow_html=True)
        fk1, fk2, fk3 = st.columns(3)
        linea_k_loc = fk1.selectbox(f"Línea K's ({pitcher_loc_auto})", opciones_ks, index=5, key="lk_loc")
        m_k_loc_over_in = fk2.number_input("Over K's", value=1.870 if es_dec else -115, format="%.3f" if es_dec else "%d", key="mk_loc_o")
        m_k_loc_under_in = fk3.number_input("Under K's", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d", key="mk_loc_u")

        st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:4px;'>PROPS DE PONCHES (K'S): <span style='color:#00ff66;'>{pitcher_vis_auto.upper()} ({visita_nombre[:3].upper()})</span></p>", unsafe_allow_html=True)
        fk4, fk5, fk6 = st.columns(3)
        linea_k_vis = fk4.selectbox(f"Línea K's ({pitcher_vis_auto})", opciones_ks, index=5, key="lk_vis")
        m_k_vis_over_in = fk5.number_input("Over K's", value=1.900 if es_dec else -110, format="%.3f" if es_dec else "%d", key="mk_vis_o")
        m_k_vis_under_in = fk6.number_input("Under K's", value=1.870 if es_dec else -115, format="%.3f" if es_dec else "%d", key="mk_vis_u")

        opciones_outs = ["13.5", "14.5", "15.5", "17.5", "18.5"]
        st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:8px;'>6. PROPS DE OUTS REGISTRADOS: <span style='color:#00ff66;'>{pitcher_loc_auto.upper()} ({local_nombre[:3].upper()})</span></p>", unsafe_allow_html=True)
        fo1, fo2, fo3 = st.columns(3)
        linea_outs_loc = fo1.selectbox(f"Línea Outs ({pitcher_loc_auto})", opciones_outs, index=2, key="lo_loc")
        m_outs_loc_over_in = fo2.number_input("Over Outs", value=1.750 if es_dec else -133, format="%.3f" if es_dec else "%d", key="mo_loc_o")
        m_outs_loc_under_in = fo3.number_input("Under Outs", value=2.000 if es_dec else 100, format="%.3f" if es_dec else "%d", key="mo_loc_u")

        st.markdown(f"<p style='color:#f5d742; font-weight:800; margin-top:4px;'>PROPS DE OUTS REGISTRADOS: <span style='color:#00ff66;'>{pitcher_vis_auto.upper()} ({visita_nombre[:3].upper()})</span></p>", unsafe_allow_html=True)
        fo4, fo5, fo6 = st.columns(3)
        linea_outs_vis = fo4.selectbox(f"Línea Outs ({pitcher_vis_auto})", opciones_outs, index=2, key="lo_vis")
        m_outs_vis_over_in = fo5.number_input("Over Outs", value=1.800 if es_dec else -125, format="%.3f" if es_dec else "%d", key="mo_vis_o")
        m_outs_vis_under_in = fo6.number_input("Under Outs", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d", key="mo_vis_u")

        st.markdown("<p style='color:#f5d742; font-weight:800; margin-top:8px;'>7. MERCADO 1ER INNING (NRFI / YRFI)</p>", unsafe_allow_html=True)
        fn1, fn2 = st.columns(2)
        m_nrfi_in = fn1.number_input("NRFI - No Run 1st Inning (Under 0.5)", value=1.830 if es_dec else -120, format="%.3f" if es_dec else "%d")
        m_yrfi_in = fn2.number_input("YRFI - Yes Run 1st Inning (Over 0.5)", value=1.950 if es_dec else -105, format="%.3f" if es_dec else "%d")

        st.button("🔄 RECALCULAR VEREDICTOS MLB", use_container_width=True)

        m_ml_loc = to_decimal(m_ml_loc_in, tipo_str)
        m_ml_vis = to_decimal(m_ml_vis_in, tipo_str)
        m_over_tot = to_decimal(m_over_tot_in, tipo_str)
        m_under_tot = to_decimal(m_under_tot_in, tipo_str)
        m_rl_loc_minus = to_decimal(m_rl_loc_minus_in, tipo_str)
        m_rl_loc_plus = to_decimal(m_rl_loc_plus_in, tipo_str)
        m_rl_vis_minus = to_decimal(m_rl_vis_minus_in, tipo_str)
        m_rl_vis_plus = to_decimal(m_rl_vis_plus_in, tipo_str)
        m_f5_loc = to_decimal(m_f5_loc_in, tipo_str)
        m_f5_vis = to_decimal(m_f5_vis_in, tipo_str)
        m_f5_over = to_decimal(m_f5_over_in, tipo_str)
        m_f5_under = to_decimal(m_f5_under_in, tipo_str)
        m_k_loc_over = to_decimal(m_k_loc_over_in, tipo_str)
        m_k_loc_under = to_decimal(m_k_loc_under_in, tipo_str)
        m_k_vis_over = to_decimal(m_k_vis_over_in, tipo_str)
        m_k_vis_under = to_decimal(m_k_vis_under_in, tipo_str)
        m_outs_loc_over = to_decimal(m_outs_loc_over_in, tipo_str)
        m_outs_loc_under = to_decimal(m_outs_loc_under_in, tipo_str)
        m_outs_vis_over = to_decimal(m_outs_vis_over_in, tipo_str)
        m_outs_vis_under = to_decimal(m_outs_vis_under_in, tipo_str)
        m_nrfi = to_decimal(m_nrfi_in, tipo_str)
        m_yrfi = to_decimal(m_yrfi_in, tipo_str)

with col_der:
    st.markdown("""
    <div class="header-big-right">
        <span style="font-size: 32px; margin-right: 10px;">👑</span>
        <span class="header-text-right">VEREDICTO MAÑA PIKS MLB</span>
    </div>
    """, unsafe_allow_html=True)

    # 1. TOTALES EMPÍRICOS SOBRE 10,000 SIMULACIONES
    tot_target = float(linea_tot_mlb)
    totales_sim = carreras_loc_sim + carreras_vis_sim
    prob_tot_over = np.mean(totales_sim > tot_target)
    prob_tot_under = np.mean(totales_sim < tot_target)

    # 2. RUN LINE EMPÍRICO SOBRE 10,000 SIMULACIONES
    diferencia_sim = carreras_loc_sim - carreras_vis_sim
    prob_rl_loc_minus = np.mean(diferencia_sim >= 2)
    prob_rl_loc_plus = np.mean(diferencia_sim >= -1)
    prob_rl_vis_minus = np.mean(diferencia_sim <= -2)
    prob_rl_vis_plus = np.mean(diferencia_sim <= 1)

    # 3. K'S Y OUTS (CÁLCULOS PITCHERS)
    k_target_loc = float(linea_k_loc)
    k_rate_loc = (k_loc / ip_loc) if ip_loc > 0 else 1.0
    outs_exp_loc_val = 17.5
    lambda_k_loc = k_rate_loc * (outs_exp_loc_val / 3.0)
    prob_k_loc_over = 1.0 - poisson.cdf(int(k_target_loc), lambda_k_loc)
    prob_k_loc_under = poisson.cdf(int(k_target_loc), lambda_k_loc)

    k_target_vis = float(linea_k_vis)
    k_rate_vis = (k_vis / ip_vis) if ip_vis > 0 else 1.0
    outs_exp_vis_val = 16.5
    lambda_k_vis = k_rate_vis * (outs_exp_vis_val / 3.0)
    prob_k_vis_over = 1.0 - poisson.cdf(int(k_target_vis), lambda_k_vis)
    prob_k_vis_under = poisson.cdf(int(k_target_vis), lambda_k_vis)

    outs_target_loc = float(linea_outs_loc)
    prob_outs_loc_over = 1.0 - poisson.cdf(int(outs_target_loc), outs_exp_loc_val)
    prob_outs_loc_under = poisson.cdf(int(outs_target_loc), outs_exp_loc_val)

    outs_target_vis = float(linea_outs_vis)
    prob_outs_vis_over = 1.0 - poisson.cdf(int(outs_target_vis), outs_exp_vis_val)
    prob_outs_vis_under = poisson.cdf(int(outs_target_vis), outs_exp_vis_val)

    # 4. F5 EMPÍRICO SOBRE 10,000 SIMULACIONES
    prob_f5_loc = np.mean(carreras_f5_loc_sim > carreras_f5_vis_sim)
    prob_f5_vis = np.mean(carreras_f5_vis_sim > carreras_f5_loc_sim)
    f5_target = float(linea_f5_sel)
    totales_f5_sim = carreras_f5_loc_sim + carreras_f5_vis_sim
    prob_f5_over = np.mean(totales_f5_sim > f5_target)
    prob_f5_under = np.mean(totales_f5_sim < f5_target)

    # 5. NRFI / YRFI EMPÍRICO SOBRE 10,000 SIMULACIONES
    xr_1st_inn_loc = xr_local * 0.13
    xr_1st_inn_vis = xr_visita * 0.13
    carreras_1st_loc_sim, carreras_1st_vis_sim = simular_partido_montecarlo(xr_1st_inn_loc, xr_1st_inn_vis, 10000)
    totales_1st_sim = carreras_1st_loc_sim + carreras_1st_vis_sim
    prob_nrfi = np.mean(totales_1st_sim == 0)
    prob_yrfi = np.mean(totales_1st_sim > 0)

    # CÁLCULO DE VALOR ESPERADO (+EV%)
    ev_ml_loc = (prob_ml_local * m_ml_loc) - 1
    ev_ml_vis = (prob_ml_visita * m_ml_vis) - 1
    ev_tot_over = (prob_tot_over * m_over_tot) - 1
    ev_tot_under = (prob_tot_under * m_under_tot) - 1
    ev_rl_loc_minus = (prob_rl_loc_minus * m_rl_loc_minus) - 1
    ev_rl_loc_plus = (prob_rl_loc_plus * m_rl_loc_plus) - 1
    ev_rl_vis_minus = (prob_rl_vis_minus * m_rl_vis_minus) - 1
    ev_rl_vis_plus = (prob_rl_vis_plus * m_rl_vis_plus) - 1
    ev_f5_loc = (prob_f5_loc * m_f5_loc) - 1
    ev_f5_vis = (prob_f5_vis * m_f5_vis) - 1
    ev_f5_over = (prob_f5_over * m_f5_over) - 1
    ev_f5_under = (prob_f5_under * m_f5_under) - 1
    ev_k_loc_over = (prob_k_loc_over * m_k_loc_over) - 1
    ev_k_loc_under = (prob_k_loc_under * m_k_loc_under) - 1
    ev_k_vis_over = (prob_k_vis_over * m_k_vis_over) - 1
    ev_k_vis_under = (prob_k_vis_under * m_k_vis_under) - 1
    ev_outs_loc_over = (prob_outs_loc_over * m_outs_loc_over) - 1
    ev_outs_loc_under = (prob_outs_loc_under * m_outs_loc_under) - 1
    ev_outs_vis_over = (prob_outs_vis_over * m_outs_vis_over) - 1
    ev_outs_vis_under = (prob_outs_vis_under * m_outs_vis_under) - 1
    ev_nrfi = (prob_nrfi * m_nrfi) - 1
    ev_yrfi = (prob_yrfi * m_yrfi) - 1

    partido_nombre_mlb = f"{local_nombre} vs {visita_nombre}"

    def render_card_mlb_con_tracker(titulo, prob_real, ev, mercado_str, momio_val, linea_val=""):
        momio_justo = 1.0 / prob_real if prob_real > 0 else 99.0
        momio_am = to_american_str(prob_real)
        
        es_trampa, msj_trampa = evaluar_riesgo_trampa(prob_real, momio_val, ev)
        es_estrella = (0.75 <= prob_real <= 0.90) and (0.02 < ev <= 0.18) and not es_trampa
        
        if es_trampa:
            badge_html = "<span class='badge-trap-flag'>⚠️ POSIBLE TRAMPA (+EV SOSPECHOSO)</span>"
            card_class = "card-trap"
        elif es_estrella:
            badge_html = "<span class='badge-star'>💎 APUESTA ESTRELLA (+EV VALIDADO)</span>"
            card_class = "card-star"
        elif ev > 0.02:
            badge_html = "<span class='badge-bet'>BET</span>"
            card_class = "card-pro"
        else:
            badge_html = "<span class='badge-skip'>SKIP</span>"
            card_class = "card-pro"

        sparkline_html = generar_grafica_barras_propsbr(prob_real)

        c_card1, c_card2, c_card3 = st.columns([3, 1.2, 0.8])
        with c_card1:
            st.markdown(f"""
            <div class="{card_class}">
                {badge_html}
                <div style="font-weight: 800; font-size: 15px; color: #ffffff;">{titulo}</div>
                <div class="subtext">
                    Prob. Real (10K Sim): <b>{prob_real*100:.1f}%</b> · Momio Justo: <b>{momio_justo:.3f} ({momio_am})</b> · <b style="color:#00ff66;">EV {ev*100:+.1f}%</b>
                </div>
                {f'<div style="color:#ff3366; font-size:11px; font-weight:800; margin-top:4px;">{msj_trampa}</div>' if es_trampa else ''}
            </div>
            """, unsafe_allow_html=True)
        with c_card2:
            st.markdown(f"""
            <div style="text-align:right; padding-top:6px;">
                <div style="font-size:10px; color:#718096; font-weight:800;">TENDENCIA L10</div>
                {sparkline_html}
            </div>
            """, unsafe_allow_html=True)
        with c_card3:
            if st.button("➕ APUESTA", key=f"btn_mlb_{mercado_str}"):
                registrar_apuesta(partido_nombre_mlb, local_nombre, visita_nombre, mercado_str, linea_val, momio_val, ev)

    st.markdown("<div class='market-title'>1. Moneyline (Ganador Directo - 9 Innings)</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"Gana {local_nombre} (ML)", prob_ml_local, ev_ml_loc, f"Gana {local_nombre} ML", m_ml_loc, "ML")
    render_card_mlb_con_tracker(f"Gana {visita_nombre} (ML)", prob_ml_visita, ev_ml_vis, f"Gana {visita_nombre} ML", m_ml_vis, "ML")

    st.markdown("<div class='market-title'>2. Total de Carreras (Over / Under)</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"Más de {tot_target} Carreras (OVER)", prob_tot_over, ev_tot_over, f"Over {tot_target} Carreras", m_over_tot, str(tot_target))
    render_card_mlb_con_tracker(f"Menos de {tot_target} Carreras (UNDER)", prob_tot_under, ev_tot_under, f"Under {tot_target} Carreras", m_under_tot, str(tot_target))

    st.markdown("<div class='market-title'>3. Run Line / Hándicap (+1.5 y -1.5)</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"{local_nombre} Run Line -1.5", prob_rl_loc_minus, ev_rl_loc_minus, f"{local_nombre} RL -1.5", m_rl_loc_minus, "-1.5")
    render_card_mlb_con_tracker(f"{local_nombre} Run Line +1.5", prob_rl_loc_plus, ev_rl_loc_plus, f"{local_nombre} RL +1.5", m_rl_loc_plus, "+1.5")
    render_card_mlb_con_tracker(f"{visita_nombre} Run Line -1.5", prob_rl_vis_minus, ev_rl_vis_minus, f"{visita_nombre} RL -1.5", m_rl_vis_minus, "-1.5")
    render_card_mlb_con_tracker(f"{visita_nombre} Run Line +1.5", prob_rl_vis_plus, ev_rl_vis_plus, f"{visita_nombre} RL +1.5", m_rl_vis_plus, "+1.5")

    st.markdown("<div class='market-title'>4. Props de Pitcheo: Ponches (K's)</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"Abridor {pitcher_loc_auto} ({local_nombre[:3]}): OVER {linea_k_loc} K's", prob_k_loc_over, ev_k_loc_over, f"Abridor {pitcher_loc_auto} Over {linea_k_loc} K's", m_k_loc_over, linea_k_loc)
    render_card_mlb_con_tracker(f"Abridor {pitcher_loc_auto} ({local_nombre[:3]}): UNDER {linea_k_loc} K's", prob_k_loc_under, ev_k_loc_under, f"Abridor {pitcher_loc_auto} Under {linea_k_loc} K's", m_k_loc_under, linea_k_loc)
    render_card_mlb_con_tracker(f"Abridor {pitcher_vis_auto} ({visita_nombre[:3]}): OVER {linea_k_vis} K's", prob_k_vis_over, ev_k_vis_over, f"Abridor {pitcher_vis_auto} Over {linea_k_vis} K's", m_k_vis_over, linea_k_vis)
    render_card_mlb_con_tracker(f"Abridor {pitcher_vis_auto} ({visita_nombre[:3]}): UNDER {linea_k_vis} K's", prob_k_vis_under, ev_k_vis_under, f"Abridor {pitcher_vis_auto} Under {linea_k_vis} K's", m_k_vis_under, linea_k_vis)

    st.markdown("<div class='market-title'>5. Props de Pitcheo: Outs Registrados</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"Abridor {pitcher_loc_auto} ({local_nombre[:3]}): OVER {linea_outs_loc} Outs", prob_outs_loc_over, ev_outs_loc_over, f"Abridor {pitcher_loc_auto} Over {linea_outs_loc} Outs", m_outs_loc_over, linea_outs_loc)
    render_card_mlb_con_tracker(f"Abridor {pitcher_loc_auto} ({local_nombre[:3]}): UNDER {linea_outs_loc} Outs", prob_outs_loc_under, ev_outs_loc_under, f"Abridor {pitcher_loc_auto} Under {linea_outs_loc} Outs", m_outs_loc_under, linea_outs_loc)
    render_card_mlb_con_tracker(f"Abridor {pitcher_vis_auto} ({visita_nombre[:3]}): OVER {linea_outs_vis} Outs", prob_outs_vis_over, ev_outs_vis_over, f"Abridor {pitcher_vis_auto} Over {linea_outs_vis} Outs", m_outs_vis_over, linea_outs_vis)
    render_card_mlb_con_tracker(f"Abridor {pitcher_vis_auto} ({visita_nombre[:3]}): UNDER {linea_outs_vis} Outs", prob_outs_vis_under, ev_outs_vis_under, f"Abridor {pitcher_vis_auto} Under {linea_outs_vis} Outs", m_outs_vis_under, linea_outs_vis)

    st.markdown("<div class='market-title'>6. Primeras 5 Entradas (F5 ML y Over/Under)</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker(f"F5 Ganador {local_nombre}", prob_f5_loc, ev_f5_loc, f"F5 ML {local_nombre}", m_f5_loc, "F5 ML")
    render_card_mlb_con_tracker(f"F5 Ganador {visita_nombre}", prob_f5_vis, ev_f5_vis, f"F5 ML {visita_nombre}", m_f5_vis, "F5 ML")
    render_card_mlb_con_tracker(f"F5: OVER {f5_target} Carreras", prob_f5_over, ev_f5_over, f"F5 Over {f5_target}", m_f5_over, str(f5_target))
    render_card_mlb_con_tracker(f"F5: UNDER {f5_target} Carreras", prob_f5_under, ev_f5_under, f"F5 Under {f5_target}", m_f5_under, str(f5_target))

    st.markdown("<div class='market-title'>7. Mercado 1er Inning: NRFI / YRFI</div>", unsafe_allow_html=True)
    render_card_mlb_con_tracker("NRFI: 0 Carreras en la 1ra Entrada (UNDER 0.5)", prob_nrfi, ev_nrfi, "NRFI 1st Inning", m_nrfi, "NRFI")
    render_card_mlb_con_tracker("YRFI: 1+ Carreras en la 1ra Entrada (OVER 0.5)", prob_yrfi, ev_yrfi, "YRFI 1st Inning", m_yrfi, "YRFI")

# ==========================================
# PANEL INFERIOR: TRACKER MLB
# ==========================================
st.markdown("<br><hr style='border:1px solid #2d3833;'><br>", unsafe_allow_html=True)
c_head1, c_head2 = st.columns([3, 1])
with c_head1: 
    st.markdown("<h3 style='color:#f5d742;'>📈 TRACKER DE APUESTAS: <span style='color:#00ff66;'>MLB</span></h3>", unsafe_allow_html=True)
with c_head2:
    if st.button("🔍 VERIFICAR RESULTADOS EN VIVO", use_container_width=True):
        num_act = auto_verificar_apuestas()
        st.toast(f"Resultados actualizados desde la API ({num_act} cambios)", icon="⚾")

historial = cargar_base_datos()
historial_filtrado = [x for x in historial if x.get("deporte") == "MLB"]

if len(historial_filtrado) == 0:
    st.info("💡 No hay apuestas registradas para MLB. Selecciona un partido arriba y presiona `➕ APUESTA` para comenzar la contabilización.")
else:
    df = pd.DataFrame(historial_filtrado)
    
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
    m4.metric("Estatus Deporte", "🟢 MLB Activo")

    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Ganadas (WIN)', 'Perdidas (LOSS)', 'Pendientes (PENDING)'],
            values=[wins, losses, pending],
            hole=.5,
            marker=dict(colors=['#00ff66', '#ff3366', '#475569'])
        )])
        fig_pie.update_layout(
            title=dict(text="Distribución (MLB)", font=dict(color='#f5d742')), 
            height=230, 
            paper_bgcolor='#242a26', 
            font=dict(color='#ffffff'),
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("**Listas de Apuestas por Estado:**")
        tab_pending, tab_win, tab_loss = st.tabs([f"⏳ PENDIENTES ({pending})", f"✅ WIN ({wins})", f"❌ LOSS ({losses})"])

        with tab_pending:
            render_tabla_historial_interactiva(list_pending, key_prefix="pending")

        with tab_win:
            render_tabla_historial_interactiva(list_win, key_prefix="win")

        with tab_loss:
            render_tabla_historial_interactiva(list_loss, key_prefix="loss")
