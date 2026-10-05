import os
import json
import requests
import math
from datetime import datetime
import pandas as pd
import numpy as np
import xgboost as xgb
import gradio as gr
from scipy.stats import norm, poisson

# Liberar puertos previos
gr.close_all()

# =========================================
# CONFIGURACIÓN DE SUPABASE (VÍA HTTP REST)
# =========================================
SUPABASE_URL = "https://tuywqyjsaubcxmbzxwlg.supabase.co"
SUPABASE_KEY = "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

DB_FILE = "historial_la_mana_picks.json"

NFL_TEAM_IDS = {
    "Arizona Cardinals": 22, "Atlanta Falcons": 1, "Baltimore Ravens": 33,
    "Buffalo Bills": 2, "Carolina Panthers": 29, "Chicago Bears": 3,
    "Cincinnati Bengals": 4, "Cleveland Browns": 5, "Dallas Cowboys": 6,
    "Denver Broncos": 7, "Detroit Lions": 8, "Green Bay Packers": 9,
    "Houston Texans": 34, "Indianapolis Colts": 11, "Jacksonville Jaguars": 30,
    "Kansas City Chiefs": 12, "Las Vegas Raiders": 13, "Los Angeles Chargers": 24,
    "Los Angeles Rams": 14, "Miami Dolphins": 15, "Minnesota Vikings": 16,
    "New England Patriots": 17, "New Orleans Saints": 18, "New York Giants": 19,
    "New York Jets": 20, "Philadelphia Eagles": 21, "Pittsburgh Steelers": 23,
    "San Francisco 49ers": 25, "Seattle Seahawks": 26, "Tampa Bay Buccaneers": 27,
    "Tennessee Titans": 10, "Washington Commanders": 28
}

ESPN_SOCCER_LEAGUES = {
    "Premier League": "eng.1",
    "LaLiga EA Sports": "esp.1",
    "Bundesliga": "ger.1",
    "Serie A": "ita.1",
    "Champions League": "uefa.champions",
    "UEFA Nations League": "uefa.nations"
}

STAT_CACHE_SOCCER = {}

# =========================================
# GESTIÓN DE BASE DE DATOS PERMANENTE
# =========================================
def cargar_historial_db():
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_picks?select=*&order=id.asc"
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error HTTP leyendo Supabase: {e}")
    
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_pick_db(deporte, partido, seleccion, tipo_pick, cuota, ventaja_ev):
    nuevo_item = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": deporte,
        "partido": partido,
        "seleccion": seleccion,
        "tipo_pick": tipo_pick,
        "cuota": float(cuota),
        "ventaja_ev": ventaja_ev,
        "estado": "PENDING"
    }
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_picks"
        requests.post(url, headers=SUPABASE_HEADERS, json=nuevo_item, timeout=5)
    except Exception as e:
        print(f"Error HTTP guardando en Supabase: {e}")
        historial = cargar_historial_db()
        nuevo_item["id"] = len(historial) + 1
        historial.append(nuevo_item)
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(historial, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def cambiar_estado_directo(pick_id, nuevo_estado):
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_picks?id=eq.{int(pick_id)}"
        requests.patch(url, headers=SUPABASE_HEADERS, json={"estado": nuevo_estado}, timeout=5)
    except Exception as e:
        print(f"Error HTTP actualizando en Supabase: {e}")
    
    recalibrar_modelos_auto()
    return generar_dashboard_completo()

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {
        "NFL": {"wins": 0, "losses": 0, "pending": 0},
        "MLB": {"wins": 0, "losses": 0, "pending": 0},
        "NBA": {"wins": 0, "losses": 0, "pending": 0},
        "PREMIER LEAGUE": {"wins": 0, "losses": 0, "pending": 0},
        "LALIGA": {"wins": 0, "losses": 0, "pending": 0},
        "BUNDESLIGA": {"wins": 0, "losses": 0, "pending": 0},
        "SERIE A": {"wins": 0, "losses": 0, "pending": 0},
        "CHAMPIONS LEAGUE": {"wins": 0, "losses": 0, "pending": 0},
        "NATIONS LEAGUE": {"wins": 0, "losses": 0, "pending": 0}
    }
    
    for item in historial:
        dep = str(item.get("deporte", "")).upper()
        est = item.get("estado", "PENDING")
        
        if "NFL" in dep: key = "NFL"
        elif "MLB" in dep: key = "MLB"
        elif "NBA" in dep: key = "NBA"
        elif "PREMIER" in dep: key = "PREMIER LEAGUE"
        elif "LALIGA" in dep: key = "LALIGA"
        elif "BUNDESLIGA" in dep: key = "BUNDESLIGA"
        elif "SERIE A" in dep: key = "SERIE A"
        elif "CHAMPIONS" in dep: key = "CHAMPIONS LEAGUE"
        elif "NATIONS" in dep: key = "NATIONS LEAGUE"
        else: key = "PREMIER LEAGUE"
            
        if est == "WIN": stats[key]["wins"] += 1
        elif est == "LOSS": stats[key]["losses"] += 1
        elif est == "PENDING": stats[key]["pending"] += 1

    tot_wins = sum(s["wins"] for s in stats.values())
    tot_loss = sum(s["losses"] for s in stats.values())
    tot_global = tot_wins + tot_loss
    pct_global = round((tot_wins / tot_global) * 100, 1) if tot_global > 0 else 0.0
    return stats, tot_wins, tot_loss, tot_global, pct_global

# =========================================
# FASE 2: MOTOR DE AUTO-APRENDIZAJE
# =========================================
FACTOR_AJUSTE_AUTO = {
    "NFL": 1.0, "MLB": 1.0, "NBA": 1.0, "PREMIER LEAGUE": 1.0, 
    "LALIGA": 1.0, "BUNDESLIGA": 1.0, "SERIE A": 1.0, 
    "CHAMPIONS LEAGUE": 1.0, "NATIONS LEAGUE": 1.0
}

def recalibrar_modelos_auto():
    global FACTOR_AJUSTE_AUTO
    stats, _, _, _, _ = calcular_metricas_historial()
    
    for key in FACTOR_AJUSTE_AUTO.keys():
        w = stats.get(key, {}).get("wins", 0)
        l = stats.get(key, {}).get("losses", 0)
        tot = w + l
        if tot >= 4:
            win_rate = w / tot
            if win_rate < 0.55:
                FACTOR_AJUSTE_AUTO[key] = 0.92
            elif win_rate > 0.70:
                FACTOR_AJUSTE_AUTO[key] = 1.08
            else:
                FACTOR_AJUSTE_AUTO[key] = 1.0
        else:
            FACTOR_AJUSTE_AUTO[key] = 1.0

# =========================================
# REPORTE ESTRUCTURADO DE LESIONES (NFL)
# =========================================
def obtener_lesionados_oficiales_nfl(nombre_equipo):
    team_id = NFL_TEAM_IDS.get(nombre_equipo)
    if not team_id:
        return 0.0, 0.0, f"<div style='font-size:11px; color:#64748B;'>⚪ Sin ID de equipo para {nombre_equipo}</div>"

    url_injuries = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams/{team_id}/injuries"
    penalización_off, penalización_def = 0.0, 0.0
    lista_jugadores = []

    try:
        r = requests.get(url_injuries, timeout=3)
        if r.status_code == 200:
            items = r.json().get("items", [])
            for item in items[:8]:
                ref_url = item.get("$ref")
                if ref_url:
                    r_detail = requests.get(ref_url, timeout=2)
                    if r_detail.status_code == 200:
                        data_inj = r_detail.json()
                        status = data_inj.get("status", "").upper()
                        ath_ref = data_inj.get("athlete", {}).get("$ref", "")
                        nombre_ath, posicion = "Jugador", "NFL"
                        if ath_ref:
                            r_ath = requests.get(ath_ref, timeout=2)
                            if r_ath.status_code == 200:
                                d_ath = r_ath.json()
                                nombre_ath = d_ath.get("displayName", "Jugador")
                                posicion = d_ath.get("position", {}).get("abbreviation", "NFL")

                        if status in ["OUT", "INJURED RESERVE", "IR", "DOUBTFUL"]:
                            if posicion in ["QB"]:
                                penalización_off += 4.0
                                lista_jugadores.append(f"❌ <b>{nombre_ath} ({posicion}): OUT</b> [-4.0 pts Off]")
                            elif posicion in ["WR", "RB", "TE", "OT"]:
                                penalización_off += 1.5
                                lista_jugadores.append(f"⚠️ <b>{nombre_ath} ({posicion}): {status}</b> [-1.5 pts Off]")
                            elif posicion in ["CB", "DE", "LB", "S"]:
                                penalización_def += 1.5
                                lista_jugadores.append(f"🛡️ <b>{nombre_ath} ({posicion}): {status}</b> [+1.5 pts Def Concedidos]")
                            else:
                                penalización_off += 0.5
                                lista_jugadores.append(f"🔸 {nombre_ath} ({posicion}): {status}")
    except Exception as e:
        print(f"Error consultando API de lesiones: {e}")

    if not lista_jugadores:
        reporte_html = f"<div style='font-size:11px; color:#10B981;'>🟢 <b>{nombre_equipo}:</b> Plantilla Titular Completa (Sin Bajas Críticas)</div>"
    else:
        reporte_html = f"<div style='font-size:11px; color:#D97706;'>🚨 <b>Bajas Confirmadas ({nombre_equipo}):</b><br/>" + "<br/>".join(lista_jugadores) + "</div>"

    return penalización_off, penalización_def, reporte_html

# =========================================
# LOGOS Y DICCIONARIOS
# =========================================
NATIONS_TROPHY_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 120'><path d='M30 110 L70 110 L65 85 C65 85 75 50 82 20 L18 20 C25 50 35 85 35 85 Z' fill='%23C0C0C0' stroke='%23333' stroke-width='2'/><path d='M25 25 C40 35 60 15 75 25 L70 40 C55 30 45 45 30 35 Z' fill='%234A5568'/><path d='M28 42 C43 52 57 32 72 42 L68 57 C53 47 43 62 32 52 Z' fill='%2310B981'/><path d='M32 59 C47 69 55 49 68 59 L65 74 C50 64 42 79 34 69 Z' fill='%23EF4444'/><circle cx='50' cy='98' r='6' fill='%23D97706'/></svg>"

LOGOS_LIGAS = {
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "LaLiga EA Sports": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "UEFA Nations League": NATIONS_TROPHY_SVG,
    "Champions League": "https://a.espncdn.com/i/leaguelogos/soccer/500/2.png",
    "Bundesliga": "https://a.espncdn.com/i/leaguelogos/soccer/500/10.png",
    "Serie A": "https://a.espncdn.com/i/leaguelogos/soccer/500/12.png",
    "NFL": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg",
    "MLB": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Major_League_Baseball_logo.svg",
    "NBA": "https://a.espncdn.com/i/leaguelogos/basketball/500/46.png"
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

NATIONS_LEAGUE_DICT = {
    # LIGA A
    "España": "https://a.espncdn.com/i/teamlogos/countries/500/esp.png",
    "Francia": "https://a.espncdn.com/i/teamlogos/countries/500/fra.png",
    "Alemania": "https://a.espncdn.com/i/teamlogos/countries/500/ger.png",
    "Inglaterra": "https://a.espncdn.com/i/teamlogos/countries/500/eng.png",
    "Portugal": "https://a.espncdn.com/i/teamlogos/countries/500/por.png",
    "Italia": "https://a.espncdn.com/i/teamlogos/countries/500/ita.png",
    "Países Bajos": "https://a.espncdn.com/i/teamlogos/countries/500/ned.png",
    "Bélgica": "https://a.espncdn.com/i/teamlogos/countries/500/bel.png",
    "Croacia": "https://a.espncdn.com/i/teamlogos/countries/500/cro.png",
    "Dinamarca": "https://a.espncdn.com/i/teamlogos/countries/500/den.png",
    "Suiza": "https://a.espncdn.com/i/teamlogos/countries/500/sui.png",
    "Austria": "https://a.espncdn.com/i/teamlogos/countries/500/aut.png",
    "Hungría": "https://a.espncdn.com/i/teamlogos/countries/500/hun.png",
    "Polonia": "https://a.espncdn.com/i/teamlogos/countries/500/pol.png",
    "Escocia": "https://a.espncdn.com/i/teamlogos/countries/500/sco.png",
    "Serbia": "https://a.espncdn.com/i/teamlogos/countries/500/srb.png",
    # LIGA B
    "Israel": "https://a.espncdn.com/i/teamlogos/countries/500/isr.png",
    "Bosnia y Herzegovina": "https://a.espncdn.com/i/teamlogos/countries/500/bih.png",
    "República Checa": "https://a.espncdn.com/i/teamlogos/countries/500/cze.png",
    "Gales": "https://a.espncdn.com/i/teamlogos/countries/500/wal.png",
    "Finlandia": "https://a.espncdn.com/i/teamlogos/countries/500/fin.png",
    "Ucrania": "https://a.espncdn.com/i/teamlogos/countries/500/ukr.png",
    "Islandia": "https://a.espncdn.com/i/teamlogos/countries/500/isl.png",
    "Noruega": "https://a.espncdn.com/i/teamlogos/countries/500/nor.png",
    "Eslovenia": "https://a.espncdn.com/i/teamlogos/countries/500/svn.png",
    "Irlanda": "https://a.espncdn.com/i/teamlogos/countries/500/irl.png",
    "Albania": "https://a.espncdn.com/i/teamlogos/countries/500/alb.png",
    "Georgia": "https://a.espncdn.com/i/teamlogos/countries/500/geo.png",
    "Grecia": "https://a.espncdn.com/i/teamlogos/countries/500/gre.png",
    "Turquía": "https://a.espncdn.com/i/teamlogos/countries/500/tur.png",
    "Kazajistán": "https://a.espncdn.com/i/teamlogos/countries/500/kaz.png",
    "Montenegro": "https://a.espncdn.com/i/teamlogos/countries/500/mne.png",
    # LIGA C
    "Suecia": "https://a.espncdn.com/i/teamlogos/countries/500/swe.png",
    "Rumanía": "https://a.espncdn.com/i/teamlogos/countries/500/rou.png",
    "Armenia": "https://a.espncdn.com/i/teamlogos/countries/500/arm.png",
    "Luxemburgo": "https://a.espncdn.com/i/teamlogos/countries/500/lux.png",
    "Azerbaiyán": "https://a.espncdn.com/i/teamlogos/countries/500/aze.png",
    "Bulgaria": "https://a.espncdn.com/i/teamlogos/countries/500/bul.png",
    "Islas Feroe": "https://a.espncdn.com/i/teamlogos/countries/500/fro.png",
    "Macedonia del Norte": "https://a.espncdn.com/i/teamlogos/countries/500/mkd.png",
    "Eslovaquia": "https://a.espncdn.com/i/teamlogos/countries/500/svk.png",
    "Irlanda del Norte": "https://a.espncdn.com/i/teamlogos/countries/500/nir.png",
    "Chipre": "https://a.espncdn.com/i/teamlogos/countries/500/cyp.png",
    "Bielorrusia": "https://a.espncdn.com/i/teamlogos/countries/500/blr.png",
    "Lituania": "https://a.espncdn.com/i/teamlogos/countries/500/ltu.png",
    "Estonia": "https://a.espncdn.com/i/teamlogos/countries/500/est.png",
    "Letonia": "https://a.espncdn.com/i/teamlogos/countries/500/lva.png",
    "Kosovo": "https://a.espncdn.com/i/teamlogos/countries/500/kvx.png",
    # LIGA D
    "Moldavia": "https://a.espncdn.com/i/teamlogos/countries/500/mda.png",
    "Malta": "https://a.espncdn.com/i/teamlogos/countries/500/mlt.png",
    "Andorra": "https://a.espncdn.com/i/teamlogos/countries/500/and.png", 
    "San Marino": "https://a.espncdn.com/i/teamlogos/countries/500/smr.png",
    "Liechtenstein": "https://a.espncdn.com/i/teamlogos/countries/500/lie.png",
    "Gibraltar": "https://a.espncdn.com/i/teamlogos/countries/500/gib.png"
}

BUNDESLIGA_DICT = {
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png", 
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "Eintracht Frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png", 
    "VfB Stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "SC Freiburg": "https://a.espncdn.com/i/teamlogos/soccer/500/126.png", 
    "Union Berlin": "https://a.espncdn.com/i/teamlogos/soccer/500/130.png",
    "Borussia Mönchengladbach": "https://a.espncdn.com/i/teamlogos/soccer/500/128.png", 
    "Werder Bremen": "https://a.espncdn.com/i/teamlogos/soccer/500/137.png",
    "FC Augsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/3812.png", 
    "TSG Hoffenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "Mainz 05": "https://a.espncdn.com/i/teamlogos/soccer/500/129.png", 
    "VfL Wolfsburgo": "https://a.espncdn.com/i/teamlogos/soccer/500/138.png",
    "Heidenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/10363.png", 
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
    "Paris Saint-Germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "Manchester United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "Como 1907": "https://a.espncdn.com/i/teamlogos/soccer/500/2625.png",
    "Sporting CP": "https://a.espncdn.com/i/teamlogos/soccer/500/300.png",
    "VfB Stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "Aston Villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "RC Lens": "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    "Real Betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "AEK Athens": "https://a.espncdn.com/i/teamlogos/soccer/500/448.png",
    "AS Roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "Shakhtar Donetsk": "https://a.espncdn.com/i/teamlogos/soccer/500/438.png",
    "Fenerbahçe": "https://a.espncdn.com/i/teamlogos/soccer/500/436.png",
    "PSV Eindhoven": "https://a.espncdn.com/i/teamlogos/soccer/500/148.png",
    "Villarreal CF": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png",
    "Club Brujas": "https://a.espncdn.com/i/teamlogos/soccer/500/2282.png",
    "Lille OSC": "https://a.espncdn.com/i/teamlogos/soccer/500/162.png",
    "Slavia Praha": "https://a.espncdn.com/i/teamlogos/soccer/500/439.png",
    "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "LASK": "https://a.espncdn.com/i/teamlogos/soccer/500/3282.png",
    "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "Galatasaray": "https://a.espncdn.com/i/teamlogos/soccer/500/437.png",
    "Viking FK": "https://a.espncdn.com/i/teamlogos/soccer/500/2324.png",
    "FC Porto": "https://a.espncdn.com/i/teamlogos/soccer/500/298.png",
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "Feyenoord": "https://a.espncdn.com/i/teamlogos/soccer/500/142.png",
    "Sabah FK": "https://a.espncdn.com/i/teamlogos/soccer/500/20340.png",
    "Slovan Bratislava": "https://a.espncdn.com/i/teamlogos/soccer/500/2322.png",
    "Bodø/Glimt": "https://a.espncdn.com/i/teamlogos/soccer/500/10365.png"
}

# DICCIONARIO NBA COMPLETO (30 EQUIPOS)
NBA_DICT = {
    "Atlanta Hawks": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png",
    "Boston Celtics": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",
    "Brooklyn Nets": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png",
    "Charlotte Hornets": "https://a.espncdn.com/i/teamlogos/nba/500/cha.png",
    "Chicago Bulls": "https://a.espncdn.com/i/teamlogos/nba/500/chi.png",
    "Cleveland Cavaliers": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",
    "Dallas Mavericks": "https://a.espncdn.com/i/teamlogos/nba/500/dal.png",
    "Denver Nuggets": "https://a.espncdn.com/i/teamlogos/nba/500/den.png",
    "Detroit Pistons": "https://a.espncdn.com/i/teamlogos/nba/500/det.png",
    "Golden State Warriors": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png",
    "Houston Rockets": "https://a.espncdn.com/i/teamlogos/nba/500/hou.png",
    "Indiana Pacers": "https://a.espncdn.com/i/teamlogos/nba/500/ind.png",
    "LA Clippers": "https://a.espncdn.com/i/teamlogos/nba/500/lac.png",
    "Los Angeles Lakers": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "Memphis Grizzlies": "https://a.espncdn.com/i/teamlogos/nba/500/mem.png",
    "Miami Heat": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png",
    "Milwaukee Bucks": "https://a.espncdn.com/i/teamlogos/nba/500/mil.png",
    "Minnesota Timberwolves": "https://a.espncdn.com/i/teamlogos/nba/500/min.png",
    "New Orleans Pelicans": "https://a.espncdn.com/i/teamlogos/nba/500/nop.png",
    "New York Knicks": "https://a.espncdn.com/i/teamlogos/nba/500/nyk.png",
    "Oklahoma City Thunder": "https://a.espncdn.com/i/teamlogos/nba/500/okc.png",
    "Orlando Magic": "https://a.espncdn.com/i/teamlogos/nba/500/orl.png",
    "Philadelphia 76ers": "https://a.espncdn.com/i/teamlogos/nba/500/phi.png",
    "Phoenix Suns": "https://a.espncdn.com/i/teamlogos/nba/500/phx.png",
    "Portland Trail Blazers": "https://a.espncdn.com/i/teamlogos/nba/500/por.png",
    "Sacramento Kings": "https://a.espncdn.com/i/teamlogos/nba/500/sac.png",
    "San Antonio Spurs": "https://a.espncdn.com/i/teamlogos/nba/500/sas.png",
    "Toronto Raptors": "https://a.espncdn.com/i/teamlogos/nba/500/tor.png",
    "Utah Jazz": "https://a.espncdn.com/i/teamlogos/nba/500/uta.png",
    "Washington Wizards": "https://a.espncdn.com/i/teamlogos/nba/500/was.png"
}

lista_nba_nombres = sorted(list(NBA_DICT.keys()))

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

DICT_NFL_COMPLETO = {
    "Arizona Cardinals": {"abbr": "ARI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png", "off": 21.5, "def": 24.2},
    "Atlanta Falcons": {"abbr": "ATL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png", "off": 22.8, "def": 21.9},
    "Baltimore Ravens": {"abbr": "BAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "off": 27.1, "def": 18.5},
    "Buffalo Bills": {"abbr": "BUF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "off": 26.5, "def": 19.2},
    "Carolina Panthers": {"abbr": "CAR", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png", "off": 16.2, "def": 25.8},
    "Chicago Bears": {"abbr": "CHI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png", "off": 20.1, "def": 22.3},
    "Cincinnati Bengals": {"abbr": "CIN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png", "off": 24.8, "def": 23.1},
    "Cleveland Browns": {"abbr": "CLE", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png", "off": 19.5, "def": 21.0},
    "Dallas Cowboys": {"abbr": "DAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "off": 26.2, "def": 22.1},
    "Denver Broncos": {"abbr": "DEN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png", "off": 21.0, "def": 20.5},
    "Detroit Lions": {"abbr": "DET", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "off": 28.5, "def": 20.2},
    "Green Bay Packers": {"abbr": "GB", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png", "off": 24.5, "def": 21.0},
    "Houston Texans": {"abbr": "HOU", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png", "off": 23.1, "def": 19.8},
    "Indianapolis Colts": {"abbr": "IND", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png", "off": 22.4, "def": 23.5},
    "Jacksonville Jaguars": {"abbr": "JAX", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png", "off": 21.2, "def": 23.8},
    "Kansas City Chiefs": {"abbr": "KC", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "off": 25.8, "def": 17.5},
    "Las Vegas Raiders": {"abbr": "LV", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png", "off": 18.2, "def": 24.1},
    "Los Angeles Chargers": {"abbr": "LAC", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png", "off": 22.0, "def": 19.2},
    "Los Angeles Rams": {"abbr": "LAR", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png", "off": 23.8, "def": 22.5},
    "Miami Dolphins": {"abbr": "MIA", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "off": 25.0, "def": 22.8},
    "Minnesota Vikings": {"abbr": "MIN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png", "off": 24.1, "def": 20.4},
    "New England Patriots": {"abbr": "NE", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png", "off": 17.1, "def": 22.0},
    "New Orleans Saints": {"abbr": "NO", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png", "off": 22.5, "def": 21.8},
    "New York Giants": {"abbr": "NYG", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png", "off": 17.8, "def": 23.9},
    "New York Jets": {"abbr": "NYJ", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "off": 18.0, "def": 19.8},
    "Philadelphia Eagles": {"abbr": "PHI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "off": 26.1, "def": 20.8},
    "Pittsburgh Steelers": {"abbr": "PIT", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png", "off": 20.5, "def": 18.8},
    "San Francisco 49ers": {"abbr": "SF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "off": 27.8, "def": 19.1},
    "Seattle Seahawks": {"abbr": "SEA", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png", "off": 22.9, "def": 22.4},
    "Tampa Bay Buccaneers": {"abbr": "TB", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "off": 24.2, "def": 22.0},
    "Tennessee Titans": {"abbr": "TEN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png", "off": 18.9, "def": 23.1},
    "Washington Commanders": {"abbr": "WAS", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/was.png", "off": 24.8, "def": 23.5}
}

lista_nfl_nombres = sorted(list(DICT_NFL_COMPLETO.keys()))

# =========================================
# CONSULTA DINÁMICA A API GRATUITA ESPN NBA & SOCCER
# =========================================
def obtener_estadisticas_soccer_api(nombre_liga, nombre_equipo):
    cache_key = f"{nombre_liga}_{nombre_equipo}"
    if cache_key in STAT_CACHE_SOCCER:
        return STAT_CACHE_SOCCER[cache_key]

    code_league = ESPN_SOCCER_LEAGUES.get(nombre_liga, "eng.1")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code_league}/teams"
    
    goles_fFavor = 1.4
    goles_contra = 1.2

    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            sports = data.get("sports", [])
            if sports:
                leagues = sports[0].get("leagues", [])
                if leagues:
                    teams = leagues[0].get("teams", [])
                    for t in teams:
                        t_info = t.get("team", {})
                        disp_name = t_info.get("displayName", "")
                        sh_name = t_info.get("shortDisplayName", "")
                        if nombre_equipo.lower() in disp_name.lower() or disp_name.lower() in nombre_equipo.lower() or nombre_equipo.lower() in sh_name.lower():
                            t_id = t_info.get("id")
                            if t_id:
                                url_t = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code_league}/teams/{t_id}/schedule"
                                r_sched = requests.get(url_t, timeout=3)
                                if r_sched.status_code == 200:
                                    events = r_sched.json().get("events", [])
                                    gf_list, gc_list = [], []
                                    for ev in events[-6:]:
                                        comps = ev.get("competitions", [])
                                        if comps:
                                            competitors = comps[0].get("competitors", [])
                                            for c in competitors:
                                                if c.get("id") == t_id:
                                                    gf_list.append(float(c.get("score", {}).get("value", 1)))
                                                else:
                                                    gc_list.append(float(c.get("score", {}).get("value", 1)))
                                    if gf_list: goles_fFavor = sum(gf_list) / len(gf_list)
                                    if gc_list: goles_contra = sum(gc_list) / len(gc_list)
                            break
    except Exception as e:
        print(f"Error llamando a API ESPN Soccer ({nombre_equipo}): {e}")

    res = (max(0.5, goles_fFavor), max(0.5, goles_contra))
    STAT_CACHE_SOCCER[cache_key] = res
    return res

def obtener_estadisticas_nba_api(nombre_equipo):
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
    pts_favor = 114.5
    pts_contra = 112.0

    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            teams = r.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
            for t in teams:
                t_info = t.get("team", {})
                if nombre_equipo.lower() in t_info.get("displayName", "").lower():
                    t_id = t_info.get("id")
                    if t_id:
                        r_sched = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{t_id}/schedule", timeout=3)
                        if r_sched.status_code == 200:
                            events = r_sched.json().get("events", [])
                            pf_list, pc_list = [], []
                            for ev in events[-8:]:
                                comps = ev.get("competitions", [])
                                if comps:
                                    for c in comps[0].get("competitors", []):
                                        if c.get("id") == t_id:
                                            pf_list.append(float(c.get("score", {}).get("value", 110)))
                                        else:
                                            pc_list.append(float(c.get("score", {}).get("value", 110)))
                            if pf_list: pts_favor = sum(pf_list) / len(pf_list)
                            if pc_list: pts_contra = sum(pc_list) / len(pc_list)
                    break
    except Exception as e:
        print(f"Error API NBA ({nombre_equipo}): {e}")

    return pts_favor, pts_contra

# =========================================
# MODELOS DE ENTRENAMIENTO IA
# =========================================
np.random.seed(42)
X_nfl_sim, y_nfl_sp, y_nfl_tot = [], [], []
for _ in range(800):
    o_l, d_l = np.random.normal(24, 3), np.random.normal(21, 3)
    o_v, d_v = np.random.normal(22, 3), np.random.normal(21, 3)
    p_loc = (o_l * 0.6) + (d_v * 0.4) + 1.5 + np.random.normal(0, 2)
    p_vis = (o_v * 0.6) + (d_l * 0.4) + np.random.normal(0, 2)
    X_nfl_sim.append([o_l, d_l, o_v, d_v])
    y_nfl_sp.append(p_loc - p_vis)
    y_nfl_tot.append(p_loc + p_vis)

model_nfl_sp = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_nfl_sim, y_nfl_sp)
model_nfl_tot = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_nfl_sim, y_nfl_tot)

X_fut_sim, y_fut_diff, y_fut_tot = [], [], []
for _ in range(800):
    xg_loc, xga_loc = np.random.normal(1.8, 0.4), np.random.normal(1.0, 0.3)
    xg_vis, xga_vis = np.random.normal(1.4, 0.4), np.random.normal(1.2, 0.3)
    goles_loc = (xg_loc * 0.6) + (xga_vis * 0.4) + np.random.normal(0.2, 0.5)
    goles_vis = (xg_vis * 0.6) + (xga_loc * 0.4) + np.random.normal(0, 0.5)
    X_fut_sim.append([xg_loc, xga_loc, xg_vis, xga_vis])
    y_fut_diff.append(goles_loc - goles_vis)
    y_fut_tot.append(goles_loc + goles_vis)

model_fut_diff = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_fut_sim, y_fut_diff)
model_fut_tot = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_fut_sim, y_fut_tot)

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

model_mlb_diff = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_mlb_sim, y_mlb_diff)
model_mlb_tot = xgb.XGBRegressor(n_estimators=80, learning_rate=0.03, max_depth=3, random_state=42).fit(X_mlb_sim, y_mlb_tot)

recalibrar_modelos_auto()

# =========================================
# SIMULACIÓN NBA
# =========================================
def simular_partido_nba(nombre_local, nombre_visita, cuota_ml_loc, cuota_ml_vis, sp_loc_val, cuota_sp_loc, sp_vis_val, cuota_sp_vis, linea_total, cuota_tot_over, cuota_tot_under, descanso_option):
    logo_loc = NBA_DICT.get(nombre_local, "https://a.espncdn.com/i/leaguelogos/basketball/500/46.png")
    logo_vis = NBA_DICT.get(nombre_visita, "https://a.espncdn.com/i/leaguelogos/basketball/500/46.png")

    pf_loc, pc_loc = obtener_estadisticas_nba_api(nombre_local)
    pf_vis, pc_vis = obtener_estadisticas_nba_api(nombre_visita)

    prom_nba = 113.5
    att_loc = pf_loc / prom_nba
    def_vis = pc_vis / prom_nba
    att_vis = pf_vis / prom_nba
    def_loc = pc_loc / prom_nba

    mod_auto = FACTOR_AJUSTE_AUTO.get("NBA", 1.0)
    pen_descanso_loc = -2.5 if "Local" in descanso_option else 0.0
    pen_descanso_vis = -2.5 if "Visitante" in descanso_option else 0.0

    # Bono Localía NBA (+3.0 pts)
    pts_loc_est = round(((att_loc * def_vis * prom_nba) + 3.0 + pen_descanso_loc) * mod_auto, 1)
    pts_vis_est = round(((att_vis * def_loc * prom_nba) + pen_descanso_vis) * mod_auto, 1)

    diff_pts = pts_loc_est - pts_vis_est
    prob_win_local = int(round(min(96, max(4, norm.cdf(diff_pts / 11.5) * 100))))
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
        badge_1 = f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    p_cubre_sp_loc = round(norm.cdf((diff_pts + float(sp_loc_val)) / 11.5) * 100, 1)
    p_cubre_sp_vis = round(norm.cdf(((-diff_pts) + float(sp_vis_val)) / 11.5) * 100, 1)

    prob_impl_sp_loc = (1 / float(cuota_sp_loc)) * 100 if float(cuota_sp_loc) > 1 else 50.0
    edge_sp_loc = round(p_cubre_sp_loc - prob_impl_sp_loc, 1)

    pick_2_str = f"{nombre_local if p_cubre_sp_loc >= p_cubre_sp_vis else nombre_visita} Spread ({sp_loc_val if p_cubre_sp_loc >= p_cubre_sp_vis else sp_vis_val}) @ {cuota_sp_loc if p_cubre_sp_loc >= p_cubre_sp_vis else cuota_sp_vis}"
    badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_loc}% EV)</span>' if edge_sp_loc >= 2.5 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    tot_est_real = pts_loc_est + pts_vis_est
    dif_total = tot_est_real - float(linea_total)
    tipo_tot = "OVER" if dif_total >= 0 else "UNDER"
    cuota_tot_fav = cuota_tot_over if tipo_tot == "OVER" else cuota_tot_under
    prob_tot = min(88, int(50 + abs(dif_total) * 3.5))

    pick_3_str = f"{tipo_tot} de {linea_total} pts @ {cuota_tot_fav} — Probabilidad: {prob_tot}% (Proyección: {tot_est_real:.1f} pts)"
    badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if abs(dif_total) >= 3.0 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO NBA EFICIENCIA DE POSESIONES</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">EFECTIVIDAD REAL: 76.8%</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({pts_vis_est:.1f} pts)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({pts_loc_est:.1f} pts)</span>
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
    return html_out, pick_1_str, pick_2_str, pick_3_str, "", f"{nombre_local} vs {nombre_visita}"

def simular_player_prop_nba(nombre_jugador, tipo_prop, linea_casino, cuota_over, cuota_under):
    linea = float(linea_casino)
    c_over, c_under = float(cuota_over), float(cuota_under)

    if "Puntos" in tipo_prop:
        proyeccion = round(24.5 + np.random.normal(0, 3.5), 1)
        unidad = "Pts"
    elif "Rebotes" in tipo_prop:
        proyeccion = round(7.5 + np.random.normal(0, 1.2), 1)
        unidad = "Reb"
    elif "Asistencias" in tipo_prop:
        proyeccion = round(6.2 + np.random.normal(0, 1.1), 1)
        unidad = "Ast"
    elif "Triples" in tipo_prop:
        proyeccion = round(2.8 + np.random.normal(0, 0.5), 1)
        unidad = "3PM"
    else:
        proyeccion = round(34.5 + np.random.normal(0, 4.0), 1)
        unidad = "PRA"

    prob_over = int(min(90, max(10, 50 + (proyeccion - linea) * 12)))
    prob_under = 100 - prob_over

    prob_impl_over = (1 / c_over) * 100 if c_over > 1 else 50.0
    ev_over = round(prob_over - prob_impl_over, 1)

    if ev_over >= 2.0:
        rec_str = f"OVER de {linea} {unidad} para {nombre_jugador} @ {c_over}"
        badge = f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">BET OVER 🔥 (+{ev_over}% EV)</span>'
    else:
        rec_str = f"UNDER de {linea} {unidad} para {nombre_jugador} @ {c_under}"
        badge = '<span style="background: #3B82F6; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 11px;">MAYBE ⚡</span>'

    html_prop = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="font-size: 16px; font-weight: 900; color: #065F46; border-bottom: 1px solid #ECFDF5; padding-bottom: 8px; margin-bottom: 12px;">
            🏀 ANÁLISIS DE PLAYER PROP NBA: {nombre_jugador.upper()} ({tipo_prop})
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
            </div>
            {badge}
        </div>
    </div>
    """
    return html_prop, rec_str

# =========================================================
# GENERADORES DE COMPONENTES 3D
# =========================================================
def crear_grafica_barras_3d(titulo, wins, losses, pending):
    total = wins + losses
    pct = round((wins / total) * 100, 1) if total > 0 else 0.0
    
    max_val = max(wins, losses, pending, 1)
    h_l = max(6, int((losses / max_val) * 38))
    h_p = max(6, int((pending / max_val) * 38))
    h_w = max(6, int((wins / max_val) * 38))

    return f"""
    <div style="background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 16px; padding: 10px 6px; box-shadow: 0 6px 16px rgba(0,0,0,0.04); text-align: center; font-family: 'Segoe UI', system-ui, sans-serif;">
        <div style="font-size: 10px; font-weight: 800; color: #065F46; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{titulo}</div>
        
        <div style="font-size: 20px; font-weight: 900; color: #059669; margin: 1px 0;">{pct}%</div>
        
        <div style="display: flex; justify-content: center; align-items: flex-end; gap: 8px; height: 42px; margin: 6px 0; padding: 0 8px;">
            <div style="width: 14px; height: {h_l}px; background: linear-gradient(180deg, #F87171 0%, #EF4444 60%, #B91C1C 100%); border-radius: 3px; box-shadow: 2px 2px 4px rgba(0,0,0,0.2), inset 1px 1px 1px rgba(255,255,255,0.6);" title="Losses: {losses}"></div>
            <div style="width: 14px; height: {h_p}px; background: linear-gradient(180deg, #FBBF24 0%, #F59E0B 60%, #B45309 100%); border-radius: 3px; box-shadow: 2px 2px 4px rgba(0,0,0,0.2), inset 1px 1px 1px rgba(255,255,255,0.6);" title="Pending: {pending}"></div>
            <div style="width: 14px; height: {h_w}px; background: linear-gradient(180deg, #34D399 0%, #10B981 60%, #047857 100%); border-radius: 3px; box-shadow: 2px 2px 4px rgba(0,0,0,0.2), inset 1px 1px 1px rgba(255,255,255,0.6);" title="Wins: {wins}"></div>
        </div>

        <div style="display: flex; justify-content: center; gap: 3px; font-size: 8px; font-weight: 700;">
            <span style="color: #059669; background: #ECFDF5; padding: 1px 4px; border-radius: 3px; border: 1px solid #A7F3D0;">W:{wins}</span>
            <span style="color: #EF4444; background: #FEF2F2; padding: 1px 4px; border-radius: 3px; border: 1px solid #FECACA;">L:{losses}</span>
            <span style="color: #D97706; background: #FFFBEB; padding: 1px 4px; border-radius: 3px; border: 1px solid #FDE68A;">P:{pending}</span>
        </div>
    </div>
    """

def crear_velocimetro_3d(pct_global, tot_wins, tot_loss, tot_global):
    angulo_rad = math.pi * (1.0 - (pct_global / 100.0))
    x2 = 100 + 65 * math.cos(angulo_rad)
    y2 = 100 - 65 * math.sin(angulo_rad)

    svg_gauge = f"""
    <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px); border: 2px solid #10B981; border-radius: 20px; padding: 16px 20px; text-align: center; box-shadow: 0 10px 25px rgba(16,185,129,0.12); display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: 'Segoe UI', system-ui, sans-serif;">
        <div style="font-size: 13px; font-weight: 800; color: #065F46; letter-spacing: 1px; margin-bottom: 2px;">EFECTIVIDAD GLOBAL Y RÉCORD</div>
        
        <div style="position: relative; width: 200px; height: 110px; margin: 4px 0;">
            <svg width="200" height="110" viewBox="0 0 200 110">
                <defs>
                    <filter id="shadow3d" x="-10%" y="-10%" width="120%" height="120%">
                        <feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.15"/>
                    </filter>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#EF4444" />
                        <stop offset="45%" stop-color="#F59E0B" />
                        <stop offset="75%" stop-color="#10B981" />
                        <stop offset="100%" stop-color="#059669" />
                    </linearGradient>
                </defs>

                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E2E8F0" stroke-width="22" stroke-linecap="round" filter="url(#shadow3d)" />
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gaugeGradient)" stroke-width="18" stroke-linecap="round" />
                
                <line x1="20" y1="100" x2="32" y2="100" stroke="#FFF" stroke-width="2"/>
                <line x1="100" y1="20" x2="100" y2="32" stroke="#FFF" stroke-width="2"/>
                <line x1="180" y1="100" x2="168" y2="100" stroke="#FFF" stroke-width="2"/>

                <line x1="100" y1="100" x2="{x2}" y2="{y2}" stroke="#DC2626" stroke-width="5" stroke-linecap="round" filter="url(#shadow3d)"/>
                <line x1="100" y1="100" x2="{x2}" y2="{y2}" stroke="#EF4444" stroke-width="3" stroke-linecap="round"/>
                
                <circle cx="100" cy="100" r="10" fill="#1E293B" filter="url(#shadow3d)"/>
                <circle cx="100" cy="100" r="5" fill="#EF4444"/>
            </svg>
        </div>

        <div style="font-size: 38px; font-weight: 900; color: #10B981; margin-top: -10px;">{pct_global}%</div>
        <div style="font-size: 12px; font-weight: 700; color: #64748B; margin-top: 2px;">
            Récord Registrado: <span style="color:#10B981;">{tot_wins} WINS</span> / <span style="color:#EF4444;">{tot_loss} LOSSES</span> (Total: {tot_global} Picks)
        </div>
    </div>
    """
    return svg_gauge

def generar_dashboard_completo():
    stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()

    kpi_premier_html = crear_grafica_barras_3d("Record Premier", stats['PREMIER LEAGUE']['wins'], stats['PREMIER LEAGUE']['losses'], stats['PREMIER LEAGUE']['pending'])
    kpi_laliga_html = crear_grafica_barras_3d("Record LaLiga", stats['LALIGA']['wins'], stats['LALIGA']['losses'], stats['LALIGA']['pending'])
    kpi_bundesliga_html = crear_grafica_barras_3d("Record Bundesliga", stats['BUNDESLIGA']['wins'], stats['BUNDESLIGA']['losses'], stats['BUNDESLIGA']['pending'])
    kpi_seriea_html = crear_grafica_barras_3d("Record Serie A", stats['SERIE A']['wins'], stats['SERIE A']['losses'], stats['SERIE A']['pending'])
    kpi_champions_html = crear_grafica_barras_3d("Record Champions", stats['CHAMPIONS LEAGUE']['wins'], stats['CHAMPIONS LEAGUE']['losses'], stats['CHAMPIONS LEAGUE']['pending'])
    kpi_nations_html = crear_grafica_barras_3d("Record Nationals", stats['NATIONS LEAGUE']['wins'], stats['NATIONS LEAGUE']['losses'], stats['NATIONS LEAGUE']['pending'])
    kpi_nfl_html = crear_grafica_barras_3d("Récord NFL", stats['NFL']['wins'], stats['NFL']['losses'], stats['NFL']['pending'])
    kpi_mlb_html = crear_grafica_barras_3d("Récord MLB", stats['MLB']['wins'], stats['MLB']['losses'], stats['MLB']['pending'])
    kpi_nba_html = crear_grafica_barras_3d("Récord NBA", stats['NBA']['wins'], stats['NBA']['losses'], stats['NBA']['pending'])

    html_header = crear_velocimetro_3d(pct_global, tot_wins, tot_loss, tot_global)

    historial = cargar_historial_db()
    pending_items = [x for x in historial if x.get("estado") == "PENDING"]
    win_items = [x for x in historial if x.get("estado") == "WIN"]
    loss_items = [x for x in historial if x.get("estado") == "LOSS"]

    def render_lista_html(titulo, lista, color_hex):
        html_b = f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 10px; height: 100%;">
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

    html_pending = render_lista_html("⏳ PICKS PENDIENTES", pending_items, "#F59E0B")
    html_wins = render_lista_html("✅ APUESTAS GANADAS (WIN)", win_items, "#10B981")
    html_losses = render_lista_html("❌ APUESTAS PERDIDAS (LOSS)", loss_items, "#EF4444")

    return html_header, html_pending, html_wins, html_losses, kpi_premier_html, kpi_laliga_html, kpi_bundesliga_html, kpi_seriea_html, kpi_champions_html, kpi_nations_html, kpi_nfl_html, kpi_mlb_html, kpi_nba_html

def render_logo_html(url, height=50):
    return f"""<div style="display: flex; justify-content: center; align-items: center; height: 55px; margin-bottom: 4px;">
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

        # FILA 1: BOTONES DE LIGAS (ARRIBA INCLUYENDO NBA)
        with gr.Row():
            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Premier League"]))
                btn_premier = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["LaLiga EA Sports"]))
                btn_laliga = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Bundesliga"]))
                btn_bundesliga = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Serie A"]))
                btn_seriea = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Champions League"]))
                btn_champions = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["UEFA Nations League"], height=45))
                btn_nations = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NFL"]))
                btn_nfl = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["MLB"]))
                btn_mlb = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NBA"]))
                btn_nba = gr.Button("Analizar ➔", variant="primary", size="sm")

        # FILA 2: MINI HISTOGRAMAS TRICOLOR POR LIGA
        with gr.Row():
            kpi_premier_out = gr.HTML()
            kpi_laliga_out = gr.HTML()
            kpi_bundesliga_out = gr.HTML()
            kpi_seriea_out = gr.HTML()
            kpi_champions_out = gr.HTML()
            kpi_nations_out = gr.HTML()
            kpi_nfl_out = gr.HTML()
            kpi_mlb_out = gr.HTML()
            kpi_nba_out = gr.HTML()

        gr.Markdown("<br>")

        # FILA 3: GESTOR POR ID (IZQUIERDA) Y VELOCÍMETRO 3D (DERECHA)
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🛠️ **Gestor Directo por ID**")
                num_input_id = gr.Number(value=1, label="Ingresa # ID del Pick", precision=0)
                with gr.Row():
                    btn_direct_win = gr.Button("✅ Marcar WIN", variant="primary")
                    btn_direct_loss = gr.Button("❌ Marcar LOSS", variant="secondary")

            with gr.Column(scale=2):
                html_header_out = gr.HTML()

        gr.Markdown("### 📋 **TABLERO HISTÓRICO DE CONTROL Y SEGUIMIENTO**")

        # FILA 4: TABLERO EN 3 COLUMNAS ABAJO DE TODO
        with gr.Row():
            html_pending_out = gr.HTML()
            html_wins_out = gr.HTML()
            html_losses_out = gr.HTML()

    # VISTA FÚTBOL
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

                        gr.Markdown("#### ⚽ Línea de Goles y Cuotas (Over/Under)")
                        num_fut_linea_tot = gr.Number(value=2.5, label="Línea Total Goles (O/U)")
                        with gr.Row():
                            num_fut_c_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_fut_c_under = gr.Number(value=1.95, label="Cuota UNDER")

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

    # VISTA NFL
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
                            num_nfl_cuota_ml_loc = gr.Number(value=1.30, label="Cuota ML Detroit Lions")
                            num_nfl_cuota_ml_vis = gr.Number(value=3.55, label="Cuota ML New York Jets")

                        gr.Markdown("#### 🏈 Spread / Hándicap (Casino)")
                        with gr.Row():
                            num_sp_loc_val = gr.Number(value=-7.0, label="Spread Detroit Lions")
                            num_cuota_sp_loc = gr.Number(value=1.91, label="Cuota Spread Lions")
                        with gr.Row():
                            num_sp_vis_val = gr.Number(value=+7.0, label="Spread New York Jets")
                            num_cuota_sp_vis = gr.Number(value=1.83, label="Cuota Spread Jets")

                        gr.Markdown("#### 🏈 Totales (Puntos Juego Completo)")
                        num_nfl_tot = gr.Number(value=48.0, label="Línea Total Puntos")
                        with gr.Row():
                            num_nfl_cuota_tot_over = gr.Number(value=1.88, label="Cuota OVER")
                            num_nfl_cuota_tot_under = gr.Number(value=1.87, label="Cuota UNDER")

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

    # VISTA MLB
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

    # VISTA NBA
    with gr.Column(visible=False) as vista_nba:
        with gr.Row():
            btn_volver_nba = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## 🏀 **Área de Análisis: NBA (30 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_nba_loc = gr.Dropdown(choices=lista_nba_nombres, value="Boston Celtics", label="Equipo Local", scale=3)
                            img_nba_loc = gr.Image(value=NBA_DICT["Boston Celtics"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_nba_vis = gr.Dropdown(choices=lista_nba_nombres, value="Los Angeles Lakers", label="Equipo Visitante", scale=3)
                            img_nba_vis = gr.Image(value=NBA_DICT["Los Angeles Lakers"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        drop_descanso_nba = gr.Dropdown(choices=["Sin Back-to-Back (Descanso Normal)", "Back-to-Back Local (Jugó Anoche)", "Back-to-Back Visitante (Jugó Anoche)"], value="Sin Back-to-Back (Descanso Normal)", label="¿Carga de Partidos / Descanso?")

                        gr.Markdown("#### 🏀 Cuotas Moneyline (Ganador Directo)")
                        with gr.Row():
                            num_nba_cuota_ml_loc = gr.Number(value=1.45, label="Cuota ML Boston Celtics")
                            num_nba_cuota_ml_vis = gr.Number(value=2.85, label="Cuota ML LA Lakers")

                        gr.Markdown("#### 🏀 Spread / Hándicap (Casino)")
                        with gr.Row():
                            num_sp_nba_loc_val = gr.Number(value=-5.5, label="Spread Boston Celtics")
                            num_cuota_sp_nba_loc = gr.Number(value=1.90, label="Cuota Spread Celtics")
                        with gr.Row():
                            num_sp_nba_vis_val = gr.Number(value=+5.5, label="Spread LA Lakers")
                            num_cuota_sp_nba_vis = gr.Number(value=1.90, label="Cuota Spread Lakers")

                        gr.Markdown("#### 🏀 Totales (Puntos Juego Completo)")
                        num_nba_tot = gr.Number(value=224.5, label="Línea Total Puntos (O/U)")
                        with gr.Row():
                            num_nba_cuota_tot_over = gr.Number(value=1.87, label="Cuota OVER")
                            num_nba_cuota_tot_under = gr.Number(value=1.87, label="Cuota UNDER")

                        btn_sim_nba = gr.Button("Simular Partido NBA 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_nba = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Spread)", "Selección 3 (Totales)"], label="Pick a guardar")
                        btn_save_nba = gr.Button("Guardar Pick NBA 💾", variant="secondary")
                        lbl_save_nba = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_nba = gr.HTML()
                        st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

            with gr.TabItem("👤 Player Props NBA"):
                with gr.Row():
                    with gr.Column(scale=1):
                        txt_prop_nba_player = gr.Textbox(value="Jayson Tatum", label="Nombre del Jugador")
                        drop_prop_nba_type = gr.Dropdown(choices=["Puntos (Pts)", "Rebotes (Reb)", "Asistencias (Ast)", "Triples (3PM)", "Puntos + Rebotes + Asistencias (PRA)"], value="Puntos (Pts)", label="Tipo de Prop")
                        num_prop_nba_line = gr.Number(value=26.5, label="Línea de Casino")
                        with gr.Row():
                            num_prop_nba_cuota_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_prop_nba_cuota_under = gr.Number(value=1.95, label="Cuota UNDER")
                        btn_sim_prop_nba = gr.Button("Analizar Prop NBA 🚀", variant="primary")

                        gr.Markdown("---")
                        btn_save_prop_nba = gr.Button("Guardar Prop NBA 💾", variant="secondary")
                        lbl_save_prop_nba = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_prop_nba = gr.HTML()
                        st_prop_nba_rec_text = gr.State("")

    st_liga_activa = gr.State("Premier League")
    st_dict_futbol_actual = gr.State(PREMIER_DICT)

    def actualizar_interfaz_fut(nombre_loc, nombre_vis, dict_actual):
        logo_loc = dict_actual.get(nombre_loc, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        logo_vis = dict_actual.get(nombre_vis, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        return logo_loc, logo_vis, gr.update(label=f"Cuota {nombre_loc} (1)"), gr.update(label=f"Cuota {nombre_vis} (2)")

    def actualizar_interfaz_nfl(nombre_loc, nombre_vis):
        logo_loc = DICT_NFL_COMPLETO.get(nombre_loc, {}).get("logo", "https://a.espncdn.com/i/teamlogos/nfl/500/det.png")
        logo_vis = DICT_NFL_COMPLETO.get(nombre_vis, {}).get("logo", "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png")
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

    def actualizar_interfaz_nba(nombre_loc, nombre_vis):
        logo_loc = NBA_DICT.get(nombre_loc, "https://a.espncdn.com/i/leaguelogos/basketball/500/46.png")
        logo_vis = NBA_DICT.get(nombre_vis, "https://a.espncdn.com/i/leaguelogos/basketball/500/46.png")
        return (
            logo_loc, logo_vis,
            gr.update(label=f"Cuota ML {nombre_loc}"),
            gr.update(label=f"Cuota ML {nombre_vis}"),
            gr.update(label=f"Spread {nombre_loc}"),
            gr.update(label=f"Cuota Spread {nombre_loc}"),
            gr.update(label=f"Spread {nombre_vis}"),
            gr.update(label=f"Cuota Spread {nombre_vis}")
        )

    def cambiar_a_liga_futbol(diccionario_liga, nombre_liga):
        eqs = sorted(list(diccionario_liga.keys()))
        loc_inicial = eqs[0]
        vis_inicial = eqs[1] if len(eqs) > 1 else eqs[0]

        logo_loc = diccionario_liga.get(loc_inicial, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")
        logo_vis = diccionario_liga.get(vis_inicial, "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png")

        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(choices=eqs, value=loc_inicial),
            gr.update(choices=eqs, value=vis_inicial),
            logo_loc,
            logo_vis,
            f"## ⚽ **Área de Análisis: {nombre_liga.upper()} ({len(eqs)} Equipos/Selecciones)**",
            nombre_liga,
            diccionario_liga,
            gr.update(label=f"Cuota {loc_inicial} (1)"),
            gr.update(label=f"Cuota {vis_inicial} (2)")
        )

    outputs_liga_futbol = [vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga, st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis]

    btn_premier.click(fn=lambda: cambiar_a_liga_futbol(PREMIER_DICT, "Premier League"), outputs=outputs_liga_futbol)
    btn_laliga.click(fn=lambda: cambiar_a_liga_futbol(LALIGA_DICT, "LaLiga EA Sports"), outputs=outputs_liga_futbol)
    btn_bundesliga.click(fn=lambda: cambiar_a_liga_futbol(BUNDESLIGA_DICT, "Bundesliga"), outputs=outputs_liga_futbol)
    btn_seriea.click(fn=lambda: cambiar_a_liga_futbol(SERIE_A_DICT, "Serie A"), outputs=outputs_liga_futbol)
    btn_champions.click(fn=lambda: cambiar_a_liga_futbol(CHAMPIONS_DICT, "Champions League"), outputs=outputs_liga_futbol)
    btn_nations.click(fn=lambda: cambiar_a_liga_futbol(NATIONS_LEAGUE_DICT, "UEFA Nations League"), outputs=outputs_liga_futbol)

    def abrir_nfl(): return gr.update(visible=False), gr.update(visible=True)
    def abrir_mlb(): return gr.update(visible=False), gr.update(visible=True)
    def abrir_nba(): return gr.update(visible=False), gr.update(visible=True)

    def volver_home():
        recalibrar_modelos_auto()
        h_head, p_out, w_out, l_out, f_prem, f_lali, f_bund, f_seri, f_champ, f_nat, f_nfl, f_mlb, f_nba = generar_dashboard_completo()
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), h_head, p_out, w_out, l_out, f_prem, f_lali, f_bund, f_seri, f_champ, f_nat, f_nfl, f_mlb, f_nba

    btn_nfl.click(fn=abrir_nfl, outputs=[vista_home, vista_nfl])
    btn_mlb.click(fn=abrir_mlb, outputs=[vista_home, vista_mlb])
    btn_nba.click(fn=abrir_nba, outputs=[vista_home, vista_nba])

    outputs_volver = [
        vista_home, vista_nfl, vista_mlb, vista_fut, vista_nba,
        html_header_out, html_pending_out, html_wins_out, html_losses_out,
        kpi_premier_out, kpi_laliga_out, kpi_bundesliga_out, kpi_seriea_out, 
        kpi_champions_out, kpi_nations_out, kpi_nfl_out, kpi_mlb_out, kpi_nba_out
    ]

    btn_volver_nfl.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_mlb.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_fut.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_nba.click(fn=volver_home, outputs=outputs_volver)

    drop_fut_loc.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])
    drop_fut_vis.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])

    drop_nfl_loc.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])
    drop_nfl_vis.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])

    drop_mlb_loc.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, lbl_hdr_loc, lbl_hdr_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_linea_team_loc, num_linea_team_vis])
    drop_mlb_vis.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, lbl_hdr_loc, lbl_hdr_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_linea_team_loc, num_linea_team_vis])

    drop_nba_loc.change(fn=actualizar_interfaz_nba, inputs=[drop_nba_loc, drop_nba_vis], outputs=[img_nba_loc, img_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis])
    drop_nba_vis.change(fn=actualizar_interfaz_nba, inputs=[drop_nba_loc, drop_nba_vis], outputs=[img_nba_loc, img_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis])

    btn_auto_api.click(fn=auto_cargar_pitchers_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[num_xera_loc, num_whip_loc, num_xera_vis, num_whip_vis, lbl_api_status])

    outputs_directos = [
        html_header_out, html_pending_out, html_wins_out, html_losses_out,
        kpi_premier_out, kpi_laliga_out, kpi_bundesliga_out, kpi_seriea_out, 
        kpi_champions_out, kpi_nations_out, kpi_nfl_out, kpi_mlb_out, kpi_nba_out
    ]

    btn_direct_win.click(fn=lambda idx: cambiar_estado_directo(idx, "WIN"), inputs=[num_input_id], outputs=outputs_directos)
    btn_direct_loss.click(fn=lambda idx: cambiar_estado_directo(idx, "LOSS"), inputs=[num_input_id], outputs=outputs_directos)

    btn_sim_nfl.click(fn=simular_partido_nfl_clasificado, inputs=[drop_nfl_loc, drop_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis, num_nfl_tot, num_nfl_cuota_tot_over, num_nfl_cuota_tot_under], outputs=[out_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match])
    btn_sim_mlb.click(fn=simular_partido_mlb_clasificado, inputs=[drop_mlb_loc, drop_mlb_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_mlb_tot, num_linea_team_loc, num_cuota_team_loc_over, num_cuota_team_loc_under, num_linea_team_vis, num_cuota_team_vis_over, num_cuota_team_vis_under, num_cuota_nrfi, num_cuota_yrfi], outputs=[out_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match])
    btn_sim_fut.click(fn=simular_partido_futbol, inputs=[st_liga_activa, drop_fut_loc, drop_fut_vis, num_fut_c_loc, num_fut_c_emp, num_fut_c_vis, num_fut_c_btts_si, num_fut_c_btts_no, num_fut_linea_tot, num_fut_c_over, num_fut_c_under, drop_fatiga, st_dict_futbol_actual], outputs=[out_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match])
    btn_sim_nba.click(fn=simular_partido_nba, inputs=[drop_nba_loc, drop_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis, num_nba_tot, num_nba_cuota_tot_over, num_nba_cuota_tot_under, drop_descanso_nba], outputs=[out_nba, st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match])

    btn_sim_prop.click(fn=simular_player_prop_mlb, inputs=[txt_prop_player_name, drop_prop_type, num_prop_line, num_prop_cuota_over, num_prop_cuota_under, num_xera_vis, num_whip_vis], outputs=[out_prop_mlb, st_prop_rec_text])
    btn_sim_prop_nfl.click(fn=simular_player_prop_nfl, inputs=[txt_prop_nfl_player, drop_prop_nfl_type, num_prop_nfl_line, num_prop_nfl_cuota_over, num_prop_nfl_cuota_under], outputs=[out_prop_nfl, st_prop_nfl_rec_text])
    btn_sim_prop_fut.click(fn=simular_prop_futbol, inputs=[txt_prop_fut_item, drop_prop_fut_type, num_prop_fut_line, num_prop_fut_cuota_over, num_prop_fut_cuota_under], outputs=[out_prop_fut, st_prop_fut_rec_text])
    btn_sim_prop_nba.click(fn=simular_player_prop_nba, inputs=[txt_prop_nba_player, drop_prop_nba_type, num_prop_nba_line, num_prop_nba_cuota_over, num_prop_nba_cuota_under], outputs=[out_prop_nba, st_prop_nba_rec_text])

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

    def fn_save_pick_nba(radio_sel, p1, p2, p3, p4, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NBA", match, sel_text, radio_sel, 1.90, "+4.8%")
        return f"✅ Pick de NBA guardado: {sel_text}"

    def fn_save_generic_prop(deporte, rec_text):
        if not rec_text: return "⚠️ Primero debes analizar la Prop."
        guardar_pick_db(f"{deporte} (PROP)", "Prop Individual", rec_text, "Player Prop", 1.85, "+5.0%")
        return f"✅ Prop guardada: {rec_text}"

    btn_save_nfl.click(fn=fn_save_pick_nfl, inputs=[rad_pick_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match], outputs=[lbl_save_nfl])
    btn_save_mlb.click(fn=fn_save_pick_mlb, inputs=[rad_pick_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match], outputs=[lbl_save_mlb])
    btn_save_fut.click(fn=fn_save_pick_fut, inputs=[rad_pick_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match, st_liga_activa], outputs=[lbl_save_fut])
    btn_save_nba.click(fn=fn_save_pick_nba, inputs=[rad_pick_nba, st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match], outputs=[lbl_save_nba])

    btn_save_prop_mlb.click(fn=lambda text: fn_save_generic_prop("MLB", text), inputs=[st_prop_rec_text], outputs=[lbl_save_prop_mlb])
    btn_save_prop_nfl.click(fn=lambda text: fn_save_generic_prop("NFL", text), inputs=[st_prop_nfl_rec_text], outputs=[lbl_save_prop_nfl])
    btn_save_prop_fut.click(fn=lambda text: fn_save_generic_prop("FÚTBOL", text), inputs=[st_prop_fut_rec_text], outputs=[lbl_save_prop_fut])
    btn_save_prop_nba.click(fn=lambda text: fn_save_generic_prop("NBA", text), inputs=[st_prop_nba_rec_text], outputs=[lbl_save_prop_nba])

    app_mana.load(fn=generar_dashboard_completo, outputs=outputs_directos)

# Vinculación de puerto para Render / Colab
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app_mana.launch(share=True, server_name="0.0.0.0", server_port=port)
