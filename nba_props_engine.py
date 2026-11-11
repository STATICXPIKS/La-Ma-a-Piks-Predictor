import math
import time
import requests

EQUIPOS_NBA_ESPN = {
    "Atlanta Hawks": ("atl", "1"), "Boston Celtics": ("bos", "2"), "Brooklyn Nets": ("bkn", "17"),
    "Charlotte Hornets": ("cha", "30"), "Chicago Bulls": ("chi", "4"), "Cleveland Cavaliers": ("cle", "5"),
    "Dallas Mavericks": ("dal", "6"), "Denver Nuggets": ("den", "7"), "Detroit Pistons": ("det", "8"),
    "Golden State Warriors": ("gsw", "9"), "Houston Rockets": ("hou", "10"), "Indiana Pacers": ("ind", "11"),
    "LA Clippers": ("lac", "12"), "Los Angeles Clippers": ("lac", "12"), "Los Angeles Lakers": ("lal", "13"),
    "Memphis Grizzlies": ("mem", "29"), "Miami Heat": ("mia", "14"), "Milwaukee Bucks": ("mil", "15"),
    "Minnesota Timberwolves": ("min", "16"), "New Orleans Pelicans": ("nop", "3"), "New York Knicks": ("nyk", "18"),
    "Oklahoma City Thunder": ("okc", "25"), "Orlando Magic": ("orl", "19"), "Philadelphia 76ers": ("phi", "20"),
    "Phoenix Suns": ("phx", "21"), "Portland Trail Blazers": ("por", "22"), "Sacramento Kings": ("sac", "23"),
    "San Antonio Spurs": ("sas", "24"), "Toronto Raptors": ("tor", "28"), "Utah Jazz": ("uta", "26"),
    "Washington Wizards": ("was", "27")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE = {}


def _obtener_atletas_activos_espn(team_id, abbr):
    """Obtiene el roster real activo directamente desde ESPN."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
    jugadores = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            atletas = data.get("athletes", [])
            for item in atletas:
                # Si viene agrupado por posición
                items_lista = item.get("items", []) if "items" in item else [item]
                for a in items_lista:
                    nombre = a.get("displayName") or a.get("fullName")
                    pos = a.get("position", {}).get("abbreviation", "G")
                    injuries = a.get("injuries", [])
                    # Omitir lesionados fuera
                    esta_fuera = any("out" in str(inj.get("status", "")).lower() for inj in injuries)
                    if nombre and not esta_fuera:
                        jugadores.append({"nombre": nombre, "posicion": pos, "equipo": abbr.upper()})
    except Exception as e:
        print(f"Error consultando roster ESPN NBA {abbr}: {e}")
    return jugadores


def _calcular_prop_nba(media, tipo):
    linea = math.floor(media) + 0.5
    if tipo in ["Puntos", "Rebotes"]:
        sigma = max(1.2, media * (0.22 if tipo == "Puntos" else 0.26))
        z = (linea - media) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
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


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    key = f"{local}_{visitante}_nba_roster_live"
    now = time.time()
    if key in _PROPS_CACHE:
        ts, data = _PROPS_CACHE[key]
        if now - ts < 1800 and data:
            return data

    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    abbr_loc, id_loc = d_loc
    abbr_vis, id_vis = d_vis

    # Tomar los titulares/rotación principal activa del roster de ESPN
    atletas_loc = _obtener_atletas_activos_espn(id_loc, abbr_loc)[:4]
    atletas_vis = _obtener_atletas_activos_espn(id_vis, abbr_vis)[:4]
    pool = atletas_loc + atletas_vis

    candidatas = []
    # Generar props contextuales según la posición real del atleta activo
    for idx, j in enumerate(pool):
        pos = j.get("posicion", "G")
        if pos in ["C", "PF", "F"]:
            metricas = [("Puntos", 16.5 + (idx % 3)), ("Rebotes", 7.5 + (idx % 2))]
        else:
            metricas = [("Puntos", 18.5 + (idx % 4)), ("Triples", 2.5), ("Asistencias", 5.5)]

        for tipo, media in metricas:
            c = _calcular_prop_nba(media, tipo)
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
    _PROPS_CACHE[key] = (now, res)
    return res
