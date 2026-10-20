import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nhl_model import ejecutar_modelo_nhl_completo, SUPABASE_URL, HEADERS_SUPABASE

app = FastAPI(title="La Maña Picks - API NHL")

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
        cuota_under=c_under,
        linea_sog=62.5,
        cuota_sog_over=1.85,
        cuota_sog_under=1.85
    )

@app.post("/api/guardar-pick")
def guardar_pick_backend(payload: dict):
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/picks",
            headers=HEADERS_SUPABASE,
            json=payload,
            timeout=8
        )
        if r.status_code in [200, 201, 204]:
            return {"status": "ok"}
        else:
            print("⚠️ Error Supabase:", r.text)
            return {"status": "error", "message": r.text}
    except Exception as e:
        print("⚠️ Excepcion Backend:", str(e))
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
