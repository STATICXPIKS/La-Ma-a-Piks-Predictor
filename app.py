import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nhl_model import ejecutar_modelo_nhl_completo
from nfl_model import ejecutar_modelo_nfl_completo

app = FastAPI(title="La Maña Picks - API Multi-Deporte")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Servidor Activo", "modelos": ["FROST-IA (NHL)", "BLITZ-IA (NFL)"]}

@app.get("/api/analizar-nhl")
def analizar_nhl(
    local: str = "Florida Panthers",
    visitante: str = "Edmonton Oilers",
    c_ml_loc: float = 1.84,
    c_ml_vis: float = 1.96,
    l_pl_loc: float = -1.5,
    c_pl_loc: float = 1.32,
    l_pl_vis: float = 1.5,
    c_pl_vis: float = 3.35,
    l_total: float = 5.5,
    c_over: float = 1.63,
    c_under: float = 2.23
):
    return ejecutar_modelo_nhl_completo(
        loc_nombre=local,
        vis_nombre=visitante,
        cuota_ml_loc=c_ml_loc,
        cuota_ml_vis=c_ml_vis,
        linea_pl_loc=l_pl_loc,
        cuota_pl_loc=c_pl_loc,
        linea_pl_vis=l_pl_vis,
        cuota_pl_vis=c_pl_vis,
        linea_total=l_total,
        cuota_over=c_over,
        cuota_under=c_under
    )

@app.get("/api/analizar-nfl")
def analizar_nfl(
    local: str = "Kansas City Chiefs",
    visitante: str = "San Francisco 49ers",
    c_ml_loc: float = 1.70,
    c_ml_vis: float = 2.20,
    l_spread_loc: float = -3.5,
    c_spread_loc: float = 1.90,
    l_spread_vis: float = 3.5,
    c_spread_vis: float = 1.90,
    l_total: float = 47.5,
    c_over: float = 1.90,
    c_under: float = 1.90
):
    return ejecutar_modelo_nfl_completo(
        loc_nombre=local,
        vis_nombre=visitante,
        cuota_ml_loc=c_ml_loc,
        cuota_ml_vis=c_ml_vis,
        linea_spread_loc=l_spread_loc,
        cuota_spread_loc=c_spread_loc,
        linea_spread_vis=l_spread_vis,
        cuota_spread_vis=c_spread_vis,
        linea_total=l_total,
        cuota_over=c_over,
        cuota_under=c_under
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
