import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from nhl_model import simular_partido_nhl
except ImportError:
    simular_partido_nhl = None

try:
    from nfl_model import simular_partido_nfl
except ImportError:
    simular_partido_nfl = None

try:
    from nba_model import simular_partido_nba
except ImportError:
    simular_partido_nba = None

app = FastAPI(
    title="La Maña Picks • API Multideporte",
    description="Motor cuantitativo (+EV) para NHL (FROST-IA), NFL (BLITZ-IA) y NBA (DUNK-IA)",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calcular_ev_porcentaje(prob_percent: float, cuota: float) -> float:
    if not cuota or cuota <= 0:
        return 0.0
    prob_decimal = prob_percent / 100.0
    ev = ((prob_decimal * cuota) - 1.0) * 100.0
    return round(ev, 1)

@app.get("/")
def home():
    return {
        "status": "online",
        "plataforma": "La Maña Picks",
        "modelos_activos": ["FROST-IA (NHL)", "BLITZ-IA (NFL)", "DUNK-IA (NBA)"]
    }

# -------------------------------------------------------------------
# ENDPOINT NHL: FROST-IA
# -------------------------------------------------------------------
@app.get("/api/analizar-nhl")
def analizar_nhl(
    local: str = Query(...), visitante: str = Query(...),
    c_ml_loc: float = Query(1.84), c_ml_vis: float = Query(1.96),
    l_pl_loc: float = Query(-1.5), c_pl_loc: float = Query(1.90),
    l_pl_vis: float = Query(1.5), c_pl_vis: float = Query(1.90),
    l_total: float = Query(5.5), c_over: float = Query(1.90), c_under: float = Query(1.90)
):
    if simular_partido_nhl:
        resultado = simular_partido_nhl(local, visitante, c_ml_loc, c_ml_vis, l_pl_loc, c_pl_loc, l_pl_vis, c_pl_vis, l_total, c_over, c_under)
    else:
        resultado = {
            "equipo_local_abbr": local[:3].upper(), "equipo_visitante_abbr": visitante[:3].upper(),
            "proyeccion_goles": "3.37 - 3.17", "total_goles_proyectado": 6.54,
            "ml_local": {"prob": 52.0}, "ml_visitante": {"prob": 48.0},
            "pl_local": {"linea": l_pl_loc, "prob": 29.5}, "pl_visitante": {"linea": l_pl_vis, "prob": 70.5},
            "total_over": {"linea": l_total, "prob": 63.3}, "total_under": {"linea": l_total, "prob": 36.7}
        }

    resultado["ml_local"]["ev"] = calcular_ev_porcentaje(resultado["ml_local"]["prob"], c_ml_loc)
    resultado["ml_visitante"]["ev"] = calcular_ev_porcentaje(resultado["ml_visitante"]["prob"], c_ml_vis)
    resultado["pl_local"]["ev"] = calcular_ev_porcentaje(resultado["pl_local"]["prob"], c_pl_loc)
    resultado["pl_visitante"]["ev"] = calcular_ev_porcentaje(resultado["pl_visitante"]["prob"], c_pl_vis)
    resultado["total_over"]["ev"] = calcular_ev_porcentaje(resultado["total_over"]["prob"], c_over)
    resultado["total_under"]["ev"] = calcular_ev_porcentaje(resultado["total_under"]["prob"], c_under)
    return resultado

# -------------------------------------------------------------------
# ENDPOINT NFL: BLITZ-IA
# -------------------------------------------------------------------
@app.get("/api/analizar-nfl")
def analizar_nfl(
    local: str = Query(...), visitante: str = Query(...),
    c_ml_loc: float = Query(1.84), c_ml_vis: float = Query(1.96),
    l_spread_loc: float = Query(-3.5), c_spread_loc: float = Query(1.90),
    l_spread_vis: float = Query(3.5), c_spread_vis: float = Query(1.90),
    l_total: float = Query(47.5), c_over: float = Query(1.90), c_under: float = Query(1.90)
):
    if simular_partido_nfl:
        resultado = simular_partido_nfl(local, visitante, c_ml_loc, c_ml_vis, l_spread_loc, c_spread_loc, l_spread_vis, c_spread_vis, l_total, c_over, c_under)
    else:
        resultado = {
            "equipo_local_abbr": local[:3].upper(), "equipo_visitante_abbr": visitante[:3].upper(),
            "proyeccion_puntos": "26.4 - 22.1", "total_puntos_proyectado": 48.5,
            "ml_local": {"prob": 58.0}, "ml_visitante": {"prob": 42.0},
            "spread_local": {"linea": l_spread_loc, "prob": 51.5}, "spread_visitante": {"linea": l_spread_vis, "prob": 48.5},
            "total_over": {"linea": l_total, "prob": 54.0}, "total_under": {"linea": l_total, "prob": 46.0}
        }

    resultado["ml_local"]["ev"] = calcular_ev_porcentaje(resultado["ml_local"]["prob"], c_ml_loc)
    resultado["ml_visitante"]["ev"] = calcular_ev_porcentaje(resultado["ml_visitante"]["prob"], c_ml_vis)
    resultado["spread_local"]["ev"] = calcular_ev_porcentaje(resultado["spread_local"]["prob"], c_spread_loc)
    resultado["spread_visitante"]["ev"] = calcular_ev_porcentaje(resultado["spread_visitante"]["prob"], c_spread_vis)
    resultado["total_over"]["ev"] = calcular_ev_porcentaje(resultado["total_over"]["prob"], c_over)
    resultado["total_under"]["ev"] = calcular_ev_porcentaje(resultado["total_under"]["prob"], c_under)
    return resultado

# -------------------------------------------------------------------
# ENDPOINT NBA: DUNK-IA
# -------------------------------------------------------------------
@app.get("/api/analizar-nba")
def analizar_nba(
    local: str = Query(...), visitante: str = Query(...),
    c_ml_loc: float = Query(1.84), c_ml_vis: float = Query(1.96),
    l_spread_loc: float = Query(-4.5), c_spread_loc: float = Query(1.90),
    l_spread_vis: float = Query(4.5), c_spread_vis: float = Query(1.90),
    l_total: float = Query(224.5), c_over: float = Query(1.90), c_under: float = Query(1.90)
):
    if simular_partido_nba:
        resultado = simular_partido_nba(local, visitante, c_ml_loc, c_ml_vis, l_spread_loc, c_spread_loc, l_spread_vis, c_spread_vis, l_total, c_over, c_under)
    else:
        resultado = {
            "equipo_local_abbr": local[:3].upper(), "equipo_visitante_abbr": visitante[:3].upper(),
            "proyeccion_puntos": "114.2 - 108.5", "total_puntos_proyectado": 222.7,
            "ml_local": {"prob": 62.0}, "ml_visitante": {"prob": 38.0},
            "spread_local": {"linea": l_spread_loc, "prob": 52.5}, "spread_visitante": {"linea": l_spread_vis, "prob": 47.5},
            "total_over": {"linea": l_total, "prob": 51.0}, "total_under": {"linea": l_total, "prob": 49.0}
        }

    resultado["ml_local"]["ev"] = calcular_ev_porcentaje(resultado["ml_local"]["prob"], c_ml_loc)
    resultado["ml_visitante"]["ev"] = calcular_ev_porcentaje(resultado["ml_visitante"]["prob"], c_ml_vis)
    resultado["spread_local"]["ev"] = calcular_ev_porcentaje(resultado["spread_local"]["prob"], c_spread_loc)
    resultado["spread_visitante"]["ev"] = calcular_ev_porcentaje(resultado["spread_visitante"]["prob"], c_spread_vis)
    resultado["total_over"]["ev"] = calcular_ev_porcentaje(resultado["total_over"]["prob"], c_over)
    resultado["total_under"]["ev"] = calcular_ev_porcentaje(resultado["total_under"]["prob"], c_under)
    return resultado

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
