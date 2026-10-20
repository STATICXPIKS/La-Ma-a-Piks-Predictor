# =========================================================
# FUNCIÓN CORREGIDA PARA GUARDAR EN SUPABASE (TABLA PICKS)
# =========================================================
def guardar_pick_db(deporte, partido, seleccion, tipo_pick, cuota, ventaja_ev):
    # Separación básica de equipos
    partes = partido.split(" vs ")
    eq_loc = partes[0] if len(partes) > 0 else "Local"
    eq_vis = partes[1] if len(partes) > 1 else "Visitante"

    nuevo_item = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "deporte": deporte.upper(),
        "modelo_nombre": "LA MAÑA MODEL",
        "equipo_local": eq_loc,
        "logo_local": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
        "equipo_visitante": eq_vis,
        "logo_visitante": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
        "pick_recomendado": seleccion,
        "cuota": float(cuota),
        "probabilidad": 60,
        "ev_porcentaje": 4.5,
        "estado": "PENDING"
    }

    try:
        url = f"{SUPABASE_URL}/rest/v1/picks"
        requests.post(url, headers=SUPABASE_HEADERS, json=nuevo_item, timeout=5)
    except Exception as e:
        print(f"Error guardando en Supabase: {e}")

# =========================================================
# RENDERIZADOR DE LOGOS REFORZADO (CORS FIX)
# =========================================================
def render_logo_html(url, height=50):
    return f"""<div style="display: flex; justify-content: center; align-items: center; height: 55px; margin-bottom: 4px; overflow: hidden;">
        <img src="{url}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='https://a.espncdn.com/i/leaguelogos/soccer/500/23.png';" style="max-height: {height}px; max-width: 100%; width: auto; object-fit: contain;" />
    </div>"""
