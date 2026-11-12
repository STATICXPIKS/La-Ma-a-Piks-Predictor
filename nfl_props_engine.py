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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE_NFL = {}

def _obtener_estadisticas_vivas_nfl(team_id, abbr):
    jugadores = {}
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/statistics"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            stats_data = r.json().get("results", {}).get("stats", {}).get("categories", [])
            mapeo = {
                "passingYards": "Yardas Pase",
                "rushingYards": "Yardas Acarreo",
                "receivingYards": "Yardas Recepción",
                "receptions": "Recepciones"
            }
            for cat in stats_data:
                c_name = cat.get("name")
                if c_name in mapeo:
                    tipo = mapeo[c_name]
                    for lead in cat.get("leaders", []):
                        nom = lead.get("athlete", {}).get("displayName")
                        val = float(str(lead.get("displayValue", 0)).replace(",", ""))
                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[nom][tipo] = val
    except Exception as e:
        print(f"Error ESPN stats NFL {abbr}: {e}")

    # Fallback al roster en vivo de ESPN si las estadísticas no responden a tiempo
    if len(jugadores) < 2:
        try:
            url_roster = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
            r_rost = requests.get(url_roster, headers=HEADERS, timeout=4)
            if r_rost.status_code == 200:
                atletas = r_rost.json().get("athletes", [])
                for a in atletas[:8]:
                    nom = a.get("displayName")
                    pos = a.get("position", {}).get("abbreviation", "WR")
                    injuries = a.get("injuries", [])
                    if any("out" in str(inj.get("status", "")).lower() for inj in injuries):
                        continue
                    if nom and nom not in jugadores:
                        if pos == "QB":
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Yardas Pase": 235.5}
                        elif pos == "RB":
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Yardas Acarreo": 62.5}
                        else:
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Yardas Recepción": 52.5, "Recepciones": 4.5}
        except Exception:
            pass

    return list(jugadores.values())

def _calcular_prop_nfl(media_real, tipo_prop):
    linea = math.floor(media_real) + 0.5
    sigma = max(2.5, media_real * 0.28)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = max(0.51, min(0.76, prob_over if es_over else prob_under))

    if prob_sel >= 0.70: cuota = 1.55
    elif prob_sel >= 0.65: cuota = 1.65
    elif prob_sel >= 0.60: cuota = 1.75
    elif prob_sel >= 0.55: cuota = 1.84
    else: cuota = 1.90

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)
    proy = int(round(media_real))
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
    key = f"{local}_{visitante}_nfl_props_vFinal"
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

    pool = _obtener_estadisticas_vivas_nfl(id_loc, abbr_loc) + _obtener_estadisticas_vivas_nfl(id_vis, abbr_vis)
    todas = []

    for j in pool:
        for tipo in ["Yardas Pase", "Yardas Acarreo", "Yardas Recepción", "Recepciones"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_nfl(j[tipo], tipo)
                score = (c["prob_real"] * 0.75) + (c["ev"] * 0.25)
                todas.append({
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

    todas.sort(key=lambda x: x["_score"], reverse=True)
    for p in todas:
        p.pop("_score", None)

    res = todas[:top_n]
    _PROPS_CACHE_NFL[key] = (now, res)
    return res
