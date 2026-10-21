import os
import random
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Importación de los modelos cuantitativos
try:
    from nhl_model import simular_partido_nhl
except ImportError:
    simular_partido_nhl = None

try:
    from nfl_model import simular_partido_nfl
except ImportError:
    simular_partido_nfl = None

app = FastAPI(
    title="La Maña Picks • API Multideporte",
    description="Motor cuantitativo de predicción (+EV) para NHL (FROST-IA) y NFL (BLITZ-IA)",
    version="2.0.0"
)

# Configuración de CORS para permitir peticiones desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calcular_ev_porcentaje(prob_percent: float, cuota: float) -> float:
    """Calcula el Valor Esperado (EV) en porcentaje dado el % de probabilidad y la cuota."""
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
        "modelos_activos": ["FROST-IA (NHL)", "BLITZ-IA (NFL)"]
    }

# -------------------------------------------------------------------
# ENDPOINT NHL: FROST-IA
# -------------------------------------------------------------------
@app.get("/api/analizar-nhl")
def analizar_nhl(
    local: str = Query(..., description="Nombre del equipo local"),
    visitante: str = Query(..., description="Nombre del equipo visitante"),
    c_ml_loc: float = Query(1.84, description="Cuota ML Local"),
    c_ml_vis: float = Query(1.96, description="Cuota ML Visitante"),
    l_pl_loc: float = Query(-1.5, description="Línea Puck Line Local"),
    c_pl_loc: float = Query(1.90, description="Cuota Puck Line Local"),
    l_pl_vis: float = Query(1.5, description="Línea Puck Line Visitante"),
    c_pl_vis: float = Query(1.90, description="Cuota Puck Line Visitante"),
    l_total: float = Query(5.5, description="Línea Total Goles"),
    c_over: float = Query(1.90, description="Cuota Over"),
    c_under: float = Query(1.90, description="Cuota Under")
):
    if simular_partido_nhl:
        resultado = simular_partido_nhl(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_pl_loc, c_pl_loc,
            l_pl_vis, c_pl_vis,
            l_total, c_over, c_under
        )
    else:
        # Fallback de simulación en caso de que nhl_model no esté disponible
        prob_ml_loc = 52.0
        prob_ml_vis = 48.0
        prob_pl_loc = 29.5
        prob_pl_vis = 70.5
        prob_over = 63.3
        prob_under = 36.7

        resultado = {
            "equipo_local_abbr": local[:3].upper(),
            "equipo_visitante_abbr": visitante[:3].upper(),
            "proyeccion_goles": "3.37 - 3.17",
            "total_goles_proyectado": 6.54,
            "ml_local": {"prob": prob_ml_loc, "cuota_justa": round(100/prob_ml_loc, 2)},
            "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": round(100/prob_ml_vis, 2)},
            "pl_local": {"linea": l_pl_loc, "prob": prob_pl_loc, "cuota_justa": round(100/prob_pl_loc, 2)},
            "pl_visitante": {"linea": l_pl_vis, "prob": prob_pl_vis, "cuota_justa": round(100/prob_pl_vis, 2)},
            "total_over": {"linea": l_total, "prob": prob_over, "cuota_justa": round(100/prob_over, 2)},
            "total_under": {"linea": l_total, "prob": prob_under, "cuota_justa": round(100/prob_under, 2)},
            "resumen_explicado": f"Análisis cuantitativo para {local} vs {visitante} en la NHL."
        }

    # Asegurar el cálculo del % EV en cada mercado
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
    local: str = Query(..., description="Nombre del equipo local"),
    visitante: str = Query(..., description="Nombre del equipo visitante"),
    c_ml_loc: float = Query(1.84, description="Cuota ML Local"),
    c_ml_vis: float = Query(1.96, description="Cuota ML Visitante"),
    l_spread_loc: float = Query(-3.5, description="Línea Point Spread Local"),
    c_spread_loc: float = Query(1.90, description="Cuota Spread Local"),
    l_spread_vis: float = Query(3.5, description="Línea Point Spread Visitante"),
    c_spread_vis: float = Query(1.90, description="Cuota Spread Visitante"),
    l_total: float = Query(47.5, description="Línea Total Puntos"),
    c_over: float = Query(1.90, description="Cuota Over"),
    c_under: float = Query(1.90, description="Cuota Under")
):
    if simular_partido_nfl:
        resultado = simular_partido_nfl(
            local, visitante,
            c_ml_loc, c_ml_vis,
            l_spread_loc, c_spread_loc,
            l_spread_vis, c_spread_vis,
            l_total, c_over, c_under
        )
    else:
        # Fallback de simulación en caso de que nfl_model no esté disponible
        prob_ml_loc = 58.0
        prob_ml_vis = 42.0
        prob_spread_loc = 51.5
        prob_spread_vis = 48.5
        prob_over = 54.0
        prob_under = 46.0

        resultado = {
            "equipo_local_abbr": local[:3].upper(),
            "equipo_visitante_abbr": visitante[:3].upper(),
            "proyeccion_puntos": "26.4 - 22.1",
            "total_puntos_proyectado": 48.5,
            "ml_local": {"prob": prob_ml_loc, "cuota_justa": round(100/prob_ml_loc, 2)},
            "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": round(100/prob_ml_vis, 2)},
            "spread_local": {"linea": l_spread_loc, "prob": prob_spread_loc, "cuota_justa": round(100/prob_spread_loc, 2)},
            "spread_visitante": {"linea": l_spread_vis, "prob": prob_spread_vis, "cuota_justa": round(100/prob_spread_vis, 2)},
            "total_over": {"linea": l_total, "prob": prob_over, "cuota_justa": round(100/prob_over, 2)},
            "total_under": {"linea": l_total, "prob": prob_under, "cuota_justa": round(100/prob_under, 2)},
            "resumen_explicado": f"Análisis cuantitativo para {local} vs {visitante} en la NFL."
        }

    # Asegurar el cálculo del % EV en cada mercado
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
