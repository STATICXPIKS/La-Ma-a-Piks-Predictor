import time
import hashlib
import random
import numpy as np
import xgboost as xgb
from api_service import get_nba_real_dataset

MAPEO_NBA = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
}

_CACHE_XGB_NBA = {"time": 0, "model": None}


def _construir_features_nba(s_loc: dict, s_vis: dict, media_liga_rtg: float) -> list:
    diff_ortg = (s_loc["home_ortg"] - s_vis["road_ortg"]) / max(10.0, media_liga_rtg)
    diff_drtg = (s_vis["road_drtg"] - s_loc["home_drtg"]) / max(10.0, media_liga_rtg)
    diff_efg = (s_loc["efg_pct"] - s_vis["efg_pct"]) / 10.0
    diff_ts = (s_loc["ts_pct"] - s_vis["ts_pct"]) / 10.0
    diff_elo = ((s_loc.get("elo", 1500.0) + 45.0) - s_vis.get("elo", 1500.0)) / 100.0
    diff_win = s_loc["win_pct"] - s_vis["win_pct"]
    return [diff_ortg, diff_drtg, diff_efg, diff_ts, diff_elo, diff_win]


def _obtener_modelo_xgb_real_nba(dataset: dict):
    ahora = time.time()
    if _CACHE_XGB_NBA["model"] is not None and (ahora - _CACHE_XGB_NBA["time"] < 21600):
        return _CACHE_XGB_NBA["model"]

    equipos = dataset.get("equipos", {})
    partidos = dataset.get("partidos", [])
    if len(partidos) < 25 or not equipos:
        return None

    media_liga_rtg = sum(e["ortg"] for e in equipos.values()) / len(equipos)
    X_rows, y_rows = [], []

    for p in partidos:
        s_loc = equipos.get(p["home"])
        s_vis = equipos.get(p["away"])
        if not s_loc or not s_vis:
            continue
        X_rows.append(_construir_features_nba(s_loc, s_vis, media_liga_rtg))
        y_rows.append(p["home_win"])

    if len(X_rows) < 25:
        return None

    model = xgb.XGBClassifier(
        n_estimators=60,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        reg_lambda=2.0,
        eval_metric="logloss",
        random_state=42
    )
    model.fit(np.array(X_rows), np.array(y_rows))
    _CACHE_XGB_NBA["model"] = model
    _CACHE_XGB_NBA["time"] = ahora
    return model


def simular_partido_nba(
    local: str,
    visitante: str,
    c_ml_loc: float,
    c_ml_vis: float,
    l_spread_loc: float,
    c_spread_loc: float,
    l_spread_vis: float,
    c_spread_vis: float,
    l_total: float,
    c_over: float,
    c_under: float,
    iteraciones: int = 25000
):
    abbr_loc = MAPEO_NBA.get(local, "BOS")
    abbr_vis = MAPEO_NBA.get(visitante, "NYK")

    dataset = get_nba_real_dataset()
    equipos = dataset.get("equipos", {})
    partidos_hist = dataset.get("partidos", [])

    if equipos:
        media_liga_rtg = sum(e["ortg"] for e in equipos.values()) / len(equipos)
        media_liga_pace = sum(e["pace"] for e in equipos.values()) / len(equipos)
    else:
        media_liga_rtg = 114.0
        media_liga_pace = 99.0

    s_loc = equipos.get(abbr_loc, {
        "gp": 10, "pf_pg": media_liga_rtg, "pa_pg": media_liga_rtg, "win_pct": 0.5,
        "std_pts": 11.5, "pace": media_liga_pace,
        "ortg": media_liga_rtg, "drtg": media_liga_rtg,
        "home_ortg": media_liga_rtg, "home_drtg": media_liga_rtg,
        "road_ortg": media_liga_rtg, "road_drtg": media_liga_rtg,
        "efg_pct": 54.0, "ts_pct": 57.5, "elo": 1500.0,
        "jugo_ayer": False, "ajuste_pts_bajas": 0.0, "bajas_texto": "Sin bajas clave"
    })
    s_vis = equipos.get(abbr_vis, {
        "gp": 10, "pf_pg": media_liga_rtg, "pa_pg": media_liga_rtg, "win_pct": 0.5,
        "std_pts": 11.5, "pace": media_liga_pace,
        "ortg": media_liga_rtg, "drtg": media_liga_rtg,
        "home_ortg": media_liga_rtg, "home_drtg": media_liga_rtg,
        "road_ortg": media_liga_rtg, "road_drtg": media_liga_rtg,
        "efg_pct": 54.0, "ts_pct": 57.5, "elo": 1500.0,
        "jugo_ayer": False, "ajuste_pts_bajas": 0.0, "bajas_texto": "Sin bajas clave"
    })

    # 1. Ritmo esperado con regresión ligera hacia la media de la liga (evita extremos irreales)
    pace_puro = s_loc["pace"] + s_vis["pace"] - media_liga_pace
    pace_estimado = round((pace_puro * 0.85) + (media_liga_pace * 0.15), 1)

    # 2. Eficiencia Ofensiva/Defensiva con peso bayesiano en splits local/visita según muestra de juegos
    w_split_loc = min(0.32, s_loc.get("gp", 10) / 75.0)
    w_split_vis = min(0.32, s_vis.get("gp", 10) / 75.0)

    ortg_loc_mix = (s_loc["home_ortg"] * w_split_loc) + (s_loc["ortg"] * (1.0 - w_split_loc))
    drtg_vis_mix = (s_vis["road_drtg"] * w_split_vis) + (s_vis["drtg"] * (1.0 - w_split_vis))
    ortg_esp_loc = ortg_loc_mix + drtg_vis_mix - media_liga_rtg

    ortg_vis_mix = (s_vis["road_ortg"] * w_split_vis) + (s_vis["ortg"] * (1.0 - w_split_vis))
    drtg_loc_mix = (s_loc["home_drtg"] * w_split_loc) + (s_loc["drtg"] * (1.0 - w_split_loc))
    ortg_esp_vis = ortg_vis_mix + drtg_loc_mix - media_liga_rtg

    # 3. Ajuste real por fatiga Back-to-Back y por jugadores titulares OUT en ESPN
    fatiga_loc = -1.6 if s_loc.get("jugo_ayer") else 0.0
    fatiga_vis = -2.2 if s_vis.get("jugo_ayer") else 0.0
    bajas_loc = float(s_loc.get("ajuste_pts_bajas", 0.0))
    bajas_vis = float(s_vis.get("ajuste_pts_bajas", 0.0))

    # Cuando una estrella está OUT, el ritmo del equipo también se frena ligeramente
    pace_ajustado = max(92.0, pace_estimado + ((bajas_loc + bajas_vis) * 0.12))

    pts_loc = max(85.0, (ortg_esp_loc * (pace_ajustado / 100.0)) + fatiga_loc + bajas_loc)
    pts_vis = max(85.0, (ortg_esp_vis * (pace_ajustado / 100.0)) + fatiga_vis + bajas_vis)

    pts_esperados_loc = round(pts_loc, 1)
    pts_esperados_vis = round(pts_vis, 1)
    total_esperado = round(pts_esperados_loc + pts_esperados_vis, 1)

    # 4. Predicción XGBoost entrenada con partidos históricos reales
    modelo_xgb = _obtener_modelo_xgb_real_nba(dataset)
    if modelo_xgb is not None:
        vec = np.array([_construir_features_nba(s_loc, s_vis, media_liga_rtg)])
        prob_xgb_loc = float(modelo_xgb.predict_proba(vec)[0][1])
    else:
        prob_xgb_loc = 0.5

    # 5. Simulación Monte Carlo (25,000 iteraciones) con correlación de ritmo y varianza NBA real (~19 pts total)
    std_loc = max(10.5, float(s_loc["std_pts"]))
    std_vis = max(10.5, float(s_vis["std_pts"]))

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_spread_loc}_{l_spread_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    wins_loc, wins_vis = 0.0, 0.0
    covers_sp_loc, covers_sp_vis = 0.0, 0.0
    overs, unders = 0.0, 0.0

    for _ in range(iteraciones):
        # Factor compartido de ritmo/arbitraje del partido (genera correlación positiva realista en totales NBA)
        factor_ritmo = rng.gauss(1.0, 0.048)
        p_loc = rng.gauss(pts_loc * factor_ritmo, std_loc)
        p_vis = rng.gauss(pts_vis * factor_ritmo, std_vis)

        if abs(p_loc - p_vis) <= 1.2:
            if rng.random() < prob_xgb_loc:
                p_loc += 8.5
                p_vis += 5.5
            else:
                p_vis += 8.5
                p_loc += 5.5

        if p_loc > p_vis:
            wins_loc += 1.0
        else:
            wins_vis += 1.0

        if (p_loc + l_spread_loc) > p_vis:
            covers_sp_loc += 1.0
        elif (p_loc + l_spread_loc) == p_vis:
            covers_sp_loc += 0.5

        if (p_vis + l_spread_vis) > p_loc:
            covers_sp_vis += 1.0
        elif (p_vis + l_spread_vis) == p_loc:
            covers_sp_vis += 0.5

        tot = p_loc + p_vis
        if tot > l_total:
            overs += 1.0
        elif tot < l_total:
            unders += 1.0
        else:
            overs += 0.5
            unders += 0.5

    sim_ml_loc = wins_loc / iteraciones
    prob_ml_loc_final = (sim_ml_loc * 0.72) + (prob_xgb_loc * 0.28)

    prob_ml_loc = round(prob_ml_loc_final * 100, 1)
    prob_ml_vis = round((1.0 - prob_ml_loc_final) * 100, 1)
    prob_sp_loc = round((covers_sp_loc / iteraciones) * 100, 1)
    prob_sp_vis = round((covers_sp_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    b2b_notas = []
    if s_loc.get("jugo_ayer"): b2b_notas.append(f"{abbr_loc} B2B")
    if s_vis.get("jugo_ayer"): b2b_notas.append(f"{abbr_vis} B2B")
    b2b_txt = f" | Fatiga: {', '.join(b2b_notas)}" if b2b_notas else ""
    bajas_txt = f" | Bajas {abbr_loc}: {s_loc.get('bajas_texto', 'Sin bajas')} / {abbr_vis}: {s_vis.get('bajas_texto', 'Sin bajas')}"

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_puntos": f"{pts_esperados_loc} - {pts_esperados_vis}",
        "total_puntos_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "spread_local": {"linea": l_spread_loc, "prob": prob_sp_loc},
        "spread_visitante": {"linea": l_spread_vis, "prob": prob_sp_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": (
            f"DUNK-IA 100% Puro (25k Monte Carlo): Pace Real ({round(pace_ajustado,1)}) + ORtg/DRtg ({round(s_loc['ortg'],1)}/{round(s_vis['ortg'],1)}) "
            f"+ eFG% ({s_loc['efg_pct']}%/{s_vis['efg_pct']}%) + Elo Dinámico ({s_loc.get('elo',1500)}/{s_vis.get('elo',1500)}) "
            f"+ XGBoost ({len(partidos_hist)} juegos reales){b2b_txt}{bajas_txt}. Proy: {total_esperado} pts."
        )
    }
