import math
import time
import requests

EQUIPOS_NFL_ESPN = {
    "Arizona Cardinals": ("ari", "22"), "Atlanta Falcons": ("atl", "1"), "Baltimore Ravens": ("bal", "33"),
    "Buffalo Bills": ("buf", "2"), "Carolina Panthers": ("car", "29"), "Chicago Bears": ("chi", "3"),
    "Cincinnati Bengals": ("cin", "4"), "Cleveland Browns": ("cle", "5"), "Dallas Cowboys": ("dal", "6"),
    "Denver Broncos": ("den", "7"), "Detroit Lions": ("det", "8"), "Green Bay Packers": ("gb", "9"),
    "Houston Texans": ("hou", "34"), "Indianapolis Colts": ("ind", "11"), "Jacksonville Jaguars": ("jax", "30"),
    "Kansas City Chiefs": ("kc", "12"), "Las Vegas Raiders": ("lv", "13"), "Los Angeles Chargers": ("lac", "24"),
    "Los Angeles Rams": ("lar", "14"), "Miami Dolphins": ("mia", "15"), "Minnesota Vikings": ("min", "16"),
    "New England Patriots": ("ne", "17"), "New Orleans Saints": ("no", "18"), "New York Giants": ("nyg", "19"),
    "New York Jets": ("nyj", "20"), "Philadelphia Eagles": ("phi", "21"), "Pittsburgh Steelers": ("pit", "23"),
    "San Francisco 49ers": ("sf", "25"), "Seattle Seahawks": ("sea", "26"), "Tampa Bay Buccaneers": ("tb", "27"),
    "Tennessee Titans": ("ten", "10"), "Washington Commanders": ("was", "28")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE_NFL = {}


def _obtener_atletas_activos_nfl(team_id, abbr):
    """Obtiene el roster real activo directamente desde ESPN."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
    jugadores = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            atletas = data.get("athletes", [])
            for item in atletas:
                items_lista = item.get("items", []) if "items" in item else [item]
                for a in items_lista:
                    nombre = a.get("displayName") or a.get("fullName")
                    pos = a.get("position", {}).get("abbreviation", "WR")
                    injuries = a.get("injuries", [])
                    esta_fuera = any("out" in str(inj.get("status", "")).lower() for inj in injuries)
                    if nombre and not esta_fuera and pos in ["QB", "RB", "WR", "TE"]:
                        jugadores.append({"nombre": nombre, "posicion": pos, "equipo": abbr.upper()})
    except Exception as e:
        print(f"Error consultando roster ESPN NFL {abbr}: {e}")
    return jugadores


def _calcular_prop_nfl(media, tipo):
    linea = math.floor(media) + 0.5
    sigma = max(3.0, media * 0.28)
    z = (linea - media) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = max(0.55, min(0.72, prob_over if es_over else prob_under))

    if prob_sel >= 0.68: cuota = 1.65
    elif prob_sel >= 0.64: cuota = 1.72
    elif prob_sel >= 0.60: cuota = 1.80
    else: cuota = 1.88

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    proy = int(round(media))
    if es_over and proy <= linea: proy = int(math.ceil(linea))
    elif not es_over and proy >= linea: proy = int(math.floor(linea))

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proy
    }


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    key = f"{local}_{visitante}_nfl_roster_live"
    now = time.time()
    if key in _PROPS_CACHE_NFL:
        ts, data = _PROPS_CACHE_NFL[key]
        if now - ts < 1800 and data:
            return data

    d_loc = EQUIPOS_NFL_ESPN.get(local)
    d_vis = EQUIPOS_NFL_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    abbr_loc, id_loc = d_loc
    abbr_vis, id_vis = d_vis

    atletas_loc = _obtener_atletas_activos_nfl(id_loc, abbr_loc)[:4]
    atletas_vis = _obtener_atletas_activos_nfl(id_vis, abbr_vis)[:4]
    pool = atletas_loc + atletas_vis

    candidatas = []
    for j in pool:
        pos = j.get("posicion", "WR")
        if pos == "QB":
            metricas = [("Yardas Pase", 235.5)]
        elif pos == "RB":
            metricas = [("Yardas Acarreo", 62.5)]
        else:
            metricas = [("Yardas Recepción", 54.5), ("Recepciones", 4.5)]

        for tipo, media in metricas:
            c = _calcular_prop_nfl(media, tipo)
            score = (c["prob_real"] * 0.7) + (c["ev"] * 0.3)
            candidatas.append({
                "jugador": j["nombre"],
                "equipo_abbr": j["equipo"],
                "tipo_prop": tipo,
                "lado": c["lado"],
                "linea": c["linea"],
                "cuota": c["cuota"],
                "prob_real": c["prob_real"],
                "ev": c["ev"],
                "proyeccion": c["proyeccion"],
                "_score": score
            })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    res = candidatas[:top_n]
    _PROPS_CACHE_NFL[key] = (now, res)
    return res
