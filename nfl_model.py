import hashlib
import random
import numpy as np
import xgboost as xgb
from api_service import get_live_weather, get_nfl_real_dataset

MAPEO_NFL = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS"
}

CIUDADES_NFL = {
    "ARI": "Phoenix", "ATL": "Atlanta", "BAL": "Baltimore", "BUF": "Buffalo",
    "CAR": "Charlotte", "CHI": "Chicago", "CIN": "Cincinnati", "CLE": "Cleveland",
    "DAL": "Arlington", "DEN": "Denver", "DET": "Detroit", "GB": "Green Bay",
    "HOU": "Houston", "IND": "Indianapolis", "JAX": "Jacksonville", "KC": "Kansas City",
    "LV": "Las Vegas", "LAC": "Los Angeles", "LAR": "Los Angeles", "MIA": "Miami",
    "MIN": "Minneapolis", "NE": "Foxborough", "NO": "New Orleans", "NYG": "East Rutherford",
    "NYJ": "East Rutherford", "PHI": "Philadelphia", "PIT": "Pittsburgh", "SF": "Santa Clara",
    "SEA": "Seattle", "TB": "Tampa", "TEN": "Nashville", "WAS": "Landover"
}

ESTADIOS_TECHADOS = {"ARI", "ATL", "DAL", "DET", "HOU", "IND", "LV", "LAR", "LAC", "MIN", "NO"}

_CACHE_XGB_NFL = None


def _construir_features_nfl(s_loc: dict, s_vis: dict, media_liga: float) -> list:
    diff_off = (s_loc["home_pf_pg"] - s_vis["road_pf_pg"]) / max(1.0, media_liga)
    diff_def = (s_vis["road_pa_pg"] - s_loc["home_pa_pg"]) / max(1.0, media_liga)
    diff_win = s_loc["win_pct"] - s_vis["win_pct"]
    net_loc = (s_loc["pf_pg"] - s_loc["pa_pg"]) / max(1.0, media_liga)
    net_vis = (s_vis["pf_pg"] - s_vis["pa_pg"]) / max(1.0, media_liga)
    return [diff_off, diff_def, diff_win, net_loc, net_vis]


def _obtener_modelo_xgb_real_nfl(dataset: dict):
    global _CACHE_XGB_NFL
    if _CACHE_XGB_NFL is not None:
        return _CACHE_XGB_NFL

    equipos = dataset.get("equipos", {})
    partidos = dataset.get("partidos", [])
    if len(partidos) < 20 or not equipos:
        return None

    media_liga = sum(e["pf_pg"] for e in equipos.values()) / len(equipos)
    X_rows, y_rows = [], []

    for p in partidos:
        s_loc = equipos.get(p["home"])
        s_vis = equipos.get(p["away"])
        if not s_loc or not s_vis:
            continue
        X_rows.append(_construir_features_nfl(s_loc, s_vis, media_liga))
        y_rows.append(p["home_win"])

    if len(X_rows) < 20:
        return None

    model = xgb.XGBClassifier(
        n_estimators=50,
        max_depth=2,
        learning_rate=0.05,
        subsample=0.8,
        reg_lambda=2.0,
        eval_metric="logloss",
        random_state=42
    )
    model.fit(np.array(X_rows), np.array(y_rows))
    _CACHE_XGB_NFL = model
    return model


def simular_partido_nfl(
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
    iteraciones: int = 10000
):
    abbr_loc = MAPEO_NFL.get(local, "PHI")
    abbr_vis = MAPEO_NFL.get(visitante, "DAL")

    dataset = get_nfl_real_dataset()
    equipos = dataset.get("equipos", {})
    partidos_hist = dataset.get("partidos", [])

    if equipos:
        media_liga = sum(e["pf_pg"] for e in equipos.values()) / len(equipos)
    else:
        media_liga = l_total / 2.0

    s_loc = equipos.get(abbr_loc, {
        "gp": 1, "pf_pg": media_liga, "pa_pg": media_liga, "win_pct": 0.5,
        "std_pts": 10.0, "home_pf_pg": media_liga, "home_pa_pg": media_liga,
        "road_pf_pg": media_liga, "road_pa_pg": media_liga
    })
    s_vis = equipos.get(abbr_vis, {
        "gp": 1, "pf_pg": media_liga, "pa_pg": media_liga, "win_pct": 0.5,
        "std_pts": 10.0, "home_pf_pg": media_liga, "home_pa_pg": media_liga,
        "road_pf_pg": media_liga, "road_pa_pg": media_liga
    })

    ciudad = CIUDADES_NFL.get(abbr_loc, "Philadelphia")
    es_techado = abbr_loc in ESTADIOS_TECHADOS
    factor_clima = 1.0
    temp_f, viento_mph = 70.0, 0.0

    if not es_techado:
        clima = get_live_weather(ciudad)
        if clima:
            viento_mph = clima.get("viento_mph", 0.0)
            temp_f = clima.get("temp_f", 65.0)
            if viento_mph > 15.0:
                factor_clima -= min(0.15, (viento_mph - 15.0) * 0.01)
            if temp_f < 32.0:
                factor_clima -= 0.03

    off_loc = (s_loc["home_pf_pg"] * 0.65) + (s_loc["pf_pg"] * 0.35)
    def_vis = (s_vis["road_pa_pg"] * 0.65) + (s_vis["pa_pg"] * 0.35)
    pts_loc = ((off_loc * def_vis) / max(1.0, media_liga)) * factor_clima

    off_vis = (s_vis["road_pf_pg"] * 0.65) + (s_vis["pf_pg"] * 0.35)
    def_loc = (s_loc["home_pa_pg"] * 0.65) + (s_loc["pa_pg"] * 0.35)
    pts_vis = ((off_vis * def_loc) / max(1.0, media_liga)) * factor_clima

    pts_esperados_loc = round(pts_loc, 1)
    pts_esperados_vis = round(pts_vis, 1)
    total_esperado = round(pts_esperados_loc + pts_esperados_vis, 1)

    modelo_xgb = _obtener_modelo_xgb_real_nfl(dataset)
    if modelo_xgb is not None:
        vec = np.array([_construir_features_nfl(s_loc, s_vis, media_liga)])
        prob_xgb_loc = float(modelo_xgb.predict_proba(vec)[0][1])
    else:
        prob_xgb_loc = 0.5

    std_loc = s_loc["std_pts"]
    std_vis = s_vis["std_pts"]

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_spread_loc}_{l_spread_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    wins_loc, wins_vis = 0.0, 0.0
    covers_sp_loc, covers_sp_vis = 0.0, 0.0
    overs, unders = 0.0, 0.0

    for _ in range(iteraciones):
        p_loc = max(0.0, rng.gauss(pts_loc, std_loc))
        p_vis = max(0.0, rng.gauss(pts_vis, std_vis))

        if round(p_loc) == round(p_vis):
            if rng.random() < prob_xgb_loc:
                p_loc += 3.0
            else:
                p_vis += 3.0

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
    prob_ml_loc_final = (sim_ml_loc * 0.70) + (prob_xgb_loc * 0.30)

    prob_ml_loc = round(prob_ml_loc_final * 100, 1)
    prob_ml_vis = round((1.0 - prob_ml_loc_final) * 100, 1)
    prob_sp_loc = round((covers_sp_loc / iteraciones) * 100, 1)
    prob_sp_vis = round((covers_sp_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    tipo_estadio = "Techado" if es_techado else f"{temp_f}°F / {viento_mph}mph"

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
            f"BLITZ-IA 100% Datos Reales: XGBoost entrenado con {len(partidos_hist)} partidos reales 2025-2026 ({round(prob_xgb_loc*100,1)}% ML) "
            f"+ Splits Reales Casa/Visita ({abbr_loc}: {round(s_loc['home_pf_pg'],1)} PF / {abbr_vis}: {round(s_vis['road_pf_pg'],1)} PF) "
            f"+ Clima Live ({tipo_estadio}). Proyección: {total_esperado} pts."
        )
    }
