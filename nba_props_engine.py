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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE = {}

def _obtener_estadisticas_vivas_nba(team_id, abbr):
    jugadores = {}
    
    # Consulta a la API de estadísticas de equipo oficial de ESPN
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            stats_data = r.json().get("results", {}).get("stats", {}).get("categories", [])
            for cat in stats_data:
                c_name = cat.get("name", "")
                tipo = None
                if c_name == "avgPoints": tipo = "Puntos"
                elif c_name == "avgRebounds": tipo = "Rebotes"
                elif c_name == "avgAssists": tipo = "Asistencias"
                elif c_name == "avgThreePointFieldGoalsMade": tipo = "Triples"

                if tipo:
                    for lead in cat.get("leaders", []):
                        nom = lead.get("athlete", {}).get("displayName")
                        val = float(str(lead.get("displayValue", 0)).replace(",", ""))
                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[nom][tipo] = val
    except Exception as e:
        print(f"Error ESPN stats NBA {abbr}: {e}")

    # Fallback al roster en vivo de ESPN si el endpoint de estadísticas tarda
    if len(jugadores) < 2:
        try:
            url_roster = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
            r_rost = requests.get(url_roster, headers=HEADERS, timeout=4)
            if r_rost.status_code == 200:
                atletas = r_rost.json().get("athletes", [])
                for a in atletas[:8]:
                    nom = a.get("displayName")
                    pos = a.get("position", {}).get("abbreviation", "G")
                    injuries = a.get("injuries", [])
                    if any("out" in str(inj.get("status", "")).lower() for inj in injuries):
                        continue
                    if nom and nom not in jugadores:
                        if pos in ["C", "PF"]:
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Puntos": 16.5, "Rebotes": 8.5}
                        elif pos == "PG":
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Puntos": 18.5, "Asistencias": 6.5}
                        else:
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper(), "Puntos": 19.5, "Triples": 2.5}
        except Exception:
            pass

    return list(jugadores.values())

def _calcular_prop_nba(media_real, tipo_prop):
    linea = math.floor(media_real) + 0.5
    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.22 if tipo_prop == "Puntos" else 0.25
        sigma = max(1.2, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
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

def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    key = f"{local}_{visitante}_nba_props_vFinal"
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

    pool = _obtener_estadisticas_vivas_nba(id_loc, abbr_loc) + _obtener_estadisticas_vivas_nba(id_vis, abbr_vis)
    todas = []

    for j in pool:
        for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_nba(j[tipo], tipo)
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
    _PROPS_CACHE[key] = (now, res)
    return res
