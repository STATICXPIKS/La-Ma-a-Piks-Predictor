import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nhl_model import ejecutar_modelo_nhl_completo

app = FastAPI(title="La Maña Picks - API NHL")

# Habilitar permisos CORS sin restricciones para Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Servidor Activo", "deporte": "NHL"}

@app.get("/api/analizar-nhl")
def analizar_nhl(local: str = "Florida Panthers", visitante: str = "Edmonton Oilers"):
    return ejecutar_modelo_nhl_completo(
        loc_nombre=local,
        vis_nombre=visitante,
        cuota_ml_loc=1.85, cuota_ml_vis=1.95,
        linea_pl_loc=-1.5, cuota_pl_loc=2.85, linea_pl_vis=1.5, cuota_pl_vis=1.45,
        linea_total=6.0, cuota_over=1.90, cuota_under=1.90,
        linea_sog=62.5, cuota_sog_over=1.85, cuota_sog_under=1.85
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
