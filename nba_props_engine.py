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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_PROPS_CACHE = {}


def _extraer_stats_equipo_nba(team_id, abbr):
    jugadores = {}
    
    # 1. Feed primario de líderes oficiales de equipo
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}?enable=leaders"
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            cats = r.json().get("team", {}).get("leaders", [])
            for c in cats:
                cat_name = c.get("name", "").lower()
                tipo = None
                if "point" in cat_name or "pts" in cat_name: tipo = "Puntos"
                elif "rebound" in cat_name or "reb" in cat_name: tipo = "Rebotes"
                elif "assist" in cat_name or "ast" in cat_name: tipo = "Asistencias"
                
                if tipo:
                    for l in c.get("leaders", []):
                        nom = l.get("athlete", {}).get("displayName")
                        val = float(str(l.get("value", 0)).replace(",", ""))
                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[nom][tipo] = val
    except Exception:
        pass

    # 2. Feed secundario si el primero no devolvió suficientes atletas
    if len(jugadores) < 2:
        try:
            url_alt = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/teams/{team_id}/athletes/statistics"
            r2 = requests.get(url_alt, headers=HEADERS, timeout=4)
            if r2.status_code == 200:
                for cat in r2.json().get("categories", []):
                    for ath in cat.get("athletes", []):
                        nom = ath.get("athlete", {}).get("displayName")
                        if not nom: continue
                        if nom not in jugadores:
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                        for st in ath.get("stats", []):
                            s_name = st.get("name", "").lower()
                            s_val = float(str(st.get("value", 0)).replace(",", ""))
                            if "avgpoints" in s_name and s_val > 5.0: jugadores[nom]["Puntos"] = s_val
                            elif "avgrebounds" in s_name and s_val > 2.0: jugadores[nom]["Rebotes"] = s_val
                            elif "avgassists" in s_name and s_val > 1.5: jugadores[nom]["Asistencias"] = s_val
                            elif "avgthreepointfieldgoalsmade" in s_name and s_val > 0.8: jugadores[nom]["Triples"] = s_val
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
    prob_sel = max(0.51, min(0.75, prob_over if es_over else prob_under))

    if prob_sel >= 0.68: cuota = 1.65
    elif prob_sel >= 0.64: cuota = 1.72
    elif prob_sel >= 0.60: cuota = 1.80
    elif prob_sel >= 0.55: cuota = 1.86
    else: cuota = 1.91

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
    key = f"{local}_{visitante}_nba_props"
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

    pool = _extraer_stats_equipo_nba(id_loc, abbr_loc) + _extraer_stats_equipo_nba(id_vis, abbr_vis)
    todas = []

    for j in pool:
        for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_nba(j[tipo], tipo)
                score = (c["prob_real"] * 0.70) + (c["ev"] * 0.30)
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
