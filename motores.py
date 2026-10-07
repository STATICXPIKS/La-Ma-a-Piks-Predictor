import os
import json
import requests
import math
from datetime import datetime
import numpy as np
import xgboost as xgb
from scipy.stats import norm, poisson
from datos import *

STAT_CACHE_SOCCER = {}

FACTOR_AJUSTE_AUTO = {
    "NFL": 1.0, "MLB": 1.0, "NBA": 1.0, "PREMIER LEAGUE": 1.0, 
    "LALIGA": 1.0, "BUNDESLIGA": 1.0, "SERIE A": 1.0, 
    "CHAMPIONS LEAGUE": 1.0, "NATIONS LEAGUE": 1.0
}

def cargar_historial_db():
    try:
        url = f"{SUPABASE_URL}/rest/v1/historial_picks?select=*&order=id.asc"
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200: return res.json()
    except Exception: pass
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return []
    return []

def guardar_pick_db(deporte, partido, seleccion, tipo_pick, cuota, ventaja_ev):
    nuevo = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "deporte": deporte, "partido": partido, "seleccion": seleccion,
        "tipo_pick": tipo_pick, "cuota": float(cuota), "ventaja_ev": ventaja_ev, "estado": "PENDING"
    }
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/historial_picks", headers=SUPABASE_HEADERS, json=nuevo, timeout=5)
    except Exception:
        h = cargar_historial_db()
        nuevo["id"] = len(h) + 1
        h.append(nuevo)
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(h, f, ensure_ascii=False, indent=2)
        except Exception: pass

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {k: {"wins": 0, "losses": 0, "pending": 0} for k in FACTOR_AJUSTE_AUTO.keys()}
    for item in historial:
        dep = str(item.get("deporte", "")).upper()
        est = item.get("estado", "PENDING")
        key = "PREMIER LEAGUE"
        for k in stats.keys():
            if k in dep: key = k; break
        if est == "WIN": stats[key]["wins"] += 1
        elif est == "LOSS": stats[key]["losses"] += 1
        else: stats[key]["pending"] += 1
    tw = sum(s["wins"] for s in stats.values())
    tl = sum(s["losses"] for s in stats.values())
    tg = tw + tl
    return stats, tw, tl, tg, round((tw/tg)*100, 1) if tg > 0 else 0.0

def recalibrar_modelos_auto():
    global FACTOR_AJUSTE_AUTO
    stats, _, _, _, _ = calcular_metricas_historial()
    for key in FACTOR_AJUSTE_AUTO.keys():
        w, l = stats[key]["wins"], stats[key]["losses"]
        tot = w + l
        if tot >= 4:
            wr = w / tot
            FACTOR_AJUSTE_AUTO[key] = 0.92 if wr < 0.55 else (1.08 if wr > 0.70 else 1.0)

# Entrenar XGBoost basico
np.random.seed(42)
X_nfl, y_nfl_sp, y_nfl_tot = [], [], []
for _ in range(500):
    ol, dl, ov, dv = np.random.normal(24,3), np.random.normal(21,3), np.random.normal(22,3), np.random.normal(21,3)
    X_nfl.append([ol, dl, ov, dv])
    y_nfl_sp.append((ol*0.6)+(dv*0.4)+1.5 - ((ov*0.6)+(dl*0.4)))
    y_nfl_tot.append((ol*0.6)+(dv*0.4)+1.5 + ((ov*0.6)+(dl*0.4)))
model_nfl_sp = xgb.XGBRegressor(n_estimators=50, max_depth=3).fit(X_nfl, y_nfl_sp)
model_nfl_tot = xgb.XGBRegressor(n_estimators=50, max_depth=3).fit(X_nfl, y_nfl_tot)

X_mlb, y_mlb_diff, y_mlb_tot = [], [], []
for _ in range(500):
    wl, wv, xl, xv, whl, whv, pf = np.random.normal(102,10), np.random.normal(102,10), np.random.normal(3.9,0.7), np.random.normal(3.9,0.7), np.random.normal(1.2,0.1), np.random.normal(1.2,0.1), np.random.normal(1.0,0.05)
    cl = (wl/100)*(xv/4.0)*(whv/1.2)*4.3*pf
    cv = (wv/100)*(xl/4.0)*(whl/1.2)*4.1*pf
    X_mlb.append([wl, wv, xl, xv, whl, whv, pf])
    y_mlb_diff.append(cl - cv)
    y_mlb_tot.append(cl + cv)
model_mlb_diff = xgb.XGBRegressor(n_estimators=50, max_depth=3).fit(X_mlb, y_mlb_diff)
model_mlb_tot = xgb.XGBRegressor(n_estimators=50, max_depth=3).fit(X_mlb, y_mlb_tot)

# MOTOR FÚTBOL (9 GRUPOS)
def simular_futbol_9grupos(liga, n_loc, n_vis, xg_lc, xga_lc, xg_vf, xga_vf, p5_l, p5_v, st_l, bc_v, bj_l, bj_v, des_l, des_v, dt_l, c_l, c_e, c_v, c_btts_s, c_btts_n, c_o15, c_o25, c_o35, c_u25, c_ht, d_act):
    logo_loc, logo_vis = d_act.get(n_loc, ""), d_act.get(n_vis, "")
    b_loc = (float(xg_lc)*0.65) + (float(xga_vf)*0.35)
    b_vis = (float(xg_vf)*0.65) + (float(xga_lc)*0.35)
    m_f_loc = 1.0 + ((float(p5_l) - 7.5) / 50.0)
    m_f_vis = 1.0 + ((float(p5_v) - 7.5) / 50.0)
    conv_loc = 1.0 + ((float(st_l) - 4.5) * 0.03)
    vuln_vis = 1.0 + ((float(bc_v) - 1.8) * 0.04)
    mb_loc, mb_vis = max(0.65, 1.0 - (int(bj_l)*0.07)), max(0.65, 1.0 - (int(bj_v)*0.07))
    m_dt = 1.05 if "Sí" in dt_l else 1.0
    mf_loc = 0.90 if float(des_l) < 3.5 else 1.0
    mf_vis = 0.90 if float(des_v) < 3.5 else 1.0
    mod_auto = FACTOR_AJUSTE_AUTO.get(liga.upper(), 1.0)

    l_loc = max(0.2, round(b_loc * m_f_loc * conv_loc * vuln_vis * mb_loc * m_dt * mf_loc * mod_auto, 2))
    l_vis = max(0.2, round(b_vis * m_f_vis * mb_vis * mf_vis * mod_auto, 2))

    max_g = 7
    pl, pv = [poisson.pmf(i, l_loc) for i in range(max_g)], [poisson.pmf(j, l_vis) for j in range(max_g)]
    p_win_l, p_emp, p_win_v, p_o25, p_btts = 0.0, 0.0, 0.0, 0.0, 0.0
    for i in range(max_g):
        for j in range(max_g):
            pr = pl[i] * pv[j]
            if i > j: p_win_l += pr
            elif i == j: p_emp += pr
            else: p_win_v += pr
            if (i+j) > 2.5: p_o25 += pr
            if i > 0 and j > 0: p_btts += pr

    pct_l, pct_v = int(round(p_win_l*100)), int(round(p_win_v*100))
    pct_emp = max(5, 100 - pct_l - pct_v)
    pct_o25, pct_btts = int(round(p_o25*100)), int(round(p_btts*100))
    prob_ht = round((1.0 - poisson.pmf(0, (l_loc+l_vis)*0.43))*100, 1)

    ev_l = round(pct_l - ((1/float(c_l))*100 if float(c_l)>1 else 50), 1)
    ev_v = round(pct_v - ((1/float(c_v))*100 if float(c_v)>1 else 50), 1)

    p1 = f"Gana {n_loc if ev_l>=ev_v else n_vis} @ {c_l if ev_l>=ev_v else c_v} ({max(pct_l, pct_v)}%)"
    p2 = f"Doble Op: {n_loc if pct_l>=pct_v else n_vis} o Empate"
    p3 = f"OVER 2.5 Goles @ {c_o25} ({pct_o25}%)" if pct_o25>=52 else f"UNDER 2.5 @ {c_u25}"
    p4 = f"BTTS SÍ @ {c_btts_s} ({pct_btts}%)"
    p5 = f"Gol HT (Over 0.5 HT) @ {c_ht} ({prob_ht}%)"

    html = f"""
    <div style="padding:16px; background:#FFF; border-radius:12px; border:1px solid #E2E8F0; font-family:sans-serif;">
        <h3 style="color:#065F46;">⚽ LA MAÑA PICKS • FÚTBOL MULTIVARIABLE (9 GRUPOS)</h3>
        <p><b>{n_loc} ({l_loc:.2f} xG)</b>: {pct_l}% | <b>{n_vis} ({l_vis:.2f} xG)</b>: {pct_vis}% | Empate: {pct_emp}%</p>
        <hr/>
        <p><b>1. 1X2:</b> {p1}</p>
        <p><b>2. Doble Op:</b> {p2}</p>
        <p><b>3. Totales:</b> {p3}</p>
        <p><b>4. BTTS:</b> {p4}</p>
        <p><b>5. Gol HT:</b> {p5}</p>
    </div>
    """
    return html, p1, p2, p3, p4, p5, f"{n_loc} vs {n_vis}"
