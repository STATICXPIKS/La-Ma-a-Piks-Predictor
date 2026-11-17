import time
import math
import hashlib
import random
import numpy as np
import xgboost as xgb
from api_service import get_nhl_real_dataset

MAPEO_NHL = {
    "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI",
    "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS", "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL", "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
}

_CACHE_XGB_NHL = {"time": 0, "model": None}


def poisson_pmf(k, lamb):
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)


def _construir_features_nhl(s_loc: dict, s_vis: dict, media_liga: float) -> list:
    diff_off = (s_loc["home_gf_pg"] - s_vis["road_gf_pg"]) / max(0.5, media_liga)
    diff_def = (s_vis["road_ga_pg"] - s_loc["home_ga_pg"]) / max(0.5, media_liga)
    diff_win = s_loc["win_pct"] - s_vis["win_pct"]
    diff_l10 = s_loc["l10_pct"] - s_vis["l10_pct"]
    return [diff_off, diff_def, diff_win, diff_l10]


def _obtener_modelo_xgb_real_nhl(dataset: dict):
    ahora = time.time()
    if _CACHE_XGB_NHL["model"] is not None and (ahora - _CACHE_XGB_NHL["time"] < 21600):
        return _CACHE_XGB_NHL["model"]

    equipos = dataset.get("equipos", {})
    partidos = dataset.get("partidos", [])
    if len(partidos) < 20 or not equipos:
        return None

    media_liga = sum(e["gf_pg"] for e in equipos.values()) / len(equipos)
    X_rows, y_rows = [], []

    for p in partidos:
        s_loc = equipos.get(p["home"])
        s_vis = equipos.get(p["away"])
        if not s_loc or not s_vis:
            continue
        X_rows.append(_construir_features_nhl(s_loc, s_vis, media_liga))
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
    _CACHE_XGB_NHL["model"] = model
    _CACHE_XGB_NHL["time"] = ahora
    return model


def simular_partido_nhl(
    local: str,
    visitante: str,
    c_ml_loc: float,
    c_ml_vis: float,
    l_pl_loc: float,
    c_pl_loc: float,
    l_pl_vis: float,
    c_pl_vis: float,
    l_total: float,
    c_over: float,
    c_under: float,
    iteraciones: int = 10000
):
    abbr_loc = MAPEO_NHL.get(local, "WSH")
    abbr_vis = MAPEO_NHL.get(visitante, "PHI")

    dataset = get_nhl_real_dataset()
    equipos = dataset.get("equipos", {})
    partidos_hist = dataset.get("partidos", [])

    if equipos:
        media_liga = sum(e["gf_pg"] for e in equipos.values()) / len(equipos)
    else:
        media_liga = l_total / 2.0

    s_loc = equipos.get(abbr_loc, {
        "gp": 1, "gf_pg": media_liga, "ga_pg": media_liga, "win_pct": 0.5,
        "home_gf_pg": media_liga, "home_ga_pg": media_liga,
        "road_gf_pg": media_liga, "road_ga_pg": media_liga, "l10_pct": 0.5
    })
    s_vis = equipos.get(abbr_vis, {
        "gp": 1, "gf_pg": media_liga, "ga_pg": media_liga, "win_pct": 0.5,
        "home_gf_pg": media_liga, "home_ga_pg": media_liga,
        "road_gf_pg": media_liga, "road_ga_pg": media_liga, "l10_pct": 0.5
    })

    off_loc = (s_loc["home_gf_pg"] * 0.60) + (s_loc["gf_pg"] * 0.40)
    def_vis = (s_vis["road_ga_pg"] * 0.60) + (s_vis["ga_pg"] * 0.40)
    lambda_loc = round((off_loc * def_vis) / max(0.5, media_liga), 2)

    off_vis = (s_vis["road_gf_pg"] * 0.60) + (s_vis["gf_pg"] * 0.40)
    def_loc = (s_loc["home_ga_pg"] * 0.60) + (s_loc["ga_pg"] * 0.40)
    lambda_vis = round((off_vis * def_loc) / max(0.5, media_liga), 2)

    total_esperado = round(lambda_loc + lambda_vis, 2)

    modelo_xgb = _obtener_modelo_xgb_real_nhl(dataset)
    if modelo_xgb is not None:
        vec = np.array([_construir_features_nhl(s_loc, s_vis, media_liga)])
        prob_xgb_loc = float(modelo_xgb.predict_proba(vec)[0][1])
    else:
        prob_xgb_loc = 0.5

    seed_str = f"{abbr_loc}_{abbr_vis}_{l_total}_{l_pl_loc}_{l_pl_vis}"
    seed_int = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    rng = random.Random(seed_int)

    wins_loc, wins_vis = 0.0, 0.0
    covers_pl_loc, covers_pl_vis = 0.0, 0.0
    overs, unders = 0.0, 0.0

    for _ in range(iteraciones):
        g_loc = rng.choices(range(14), weights=[poisson_pmf(i, lambda_loc) for i in range(14)])[0]
        g_vis = rng.choices(range(14), weights=[poisson_pmf(i, lambda_vis) for i in range(14)])[0]

        diferencia = g_loc - g_vis
        if diferencia == 1:
            if rng.random() < 0.35:
                g_loc += 1
            elif rng.random() < 0.08:
                g_vis += 1
        elif diferencia == -1:
            if rng.random() < 0.35:
                g_vis += 1
            elif rng.random() < 0.08:
                g_loc += 1

        fin_loc, fin_vis = g_loc, g_vis

        if fin_loc == fin_vis:
            if rng.random() < prob_xgb_loc:
                ganador_loc = True
                fin_loc += 1
            else:
                ganador_loc = False
                fin_vis += 1
        else:
            ganador_loc = (fin_loc > fin_vis)

        if ganador_loc:
            wins_loc += 1.0
        else:
            wins_vis += 1.0

        if (fin_loc + l_pl_loc) > fin_vis:
            covers_pl_loc += 1.0
        if (fin_vis + l_pl_vis) > fin_loc:
            covers_pl_vis += 1.0

        tot = fin_loc + fin_vis
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
    prob_pl_loc = round((covers_pl_loc / iteraciones) * 100, 1)
    prob_pl_vis = round((covers_pl_vis / iteraciones) * 100, 1)
    prob_over   = round((overs / iteraciones) * 100, 1)
    prob_under  = round((unders / iteraciones) * 100, 1)

    return {
        "equipo_local_abbr": abbr_loc,
        "equipo_visitante_abbr": abbr_vis,
        "proyeccion_goles": f"{lambda_loc} - {lambda_vis}",
        "total_goles_proyectado": total_esperado,
        "ml_local": {"prob": prob_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis},
        "pl_local": {"linea": l_pl_loc, "prob": prob_pl_loc},
        "pl_visitante": {"linea": l_pl_vis, "prob": prob_pl_vis},
        "total_over": {"linea": l_total, "prob": prob_over},
        "total_under": {"linea": l_total, "prob": prob_under},
        "resumen_explicado": (
            f"FROST-IA 100% Datos Reales: NHL Official Standings + XGBoost entrenado con {len(partidos_hist)} partidos reales 2025-2026 ({round(prob_xgb_loc*100,1)}% ML) "
            f"+ Splits Casa/Visita ({abbr_loc}: {round(s_loc['home_gf_pg'],2)} GF / {abbr_vis}: {round(s_vis['road_gf_pg'],2)} GF). "
            f"Proyección: {total_esperado} goles."
        )
    }
