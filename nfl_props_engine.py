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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE_NFL = {}


def _extraer_atletas_vivos_nfl(team_id, abbr):
    url_v2 = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/statistics"
    jugadores = {}

    try:
        r = requests.get(url_v2, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            cats = r.json().get("results", {}).get("stats", {}).get("categories", [])
            mapeo = {
                "passingYards": "Yardas Pase",
                "rushingYards": "Yardas Acarreo",
                "receivingYards": "Yardas Recepción",
                "receptions": "Recepciones"
            }
            for c in cats:
                name = c.get("name")
                if name in mapeo:
                    tipo = mapeo[name]
                    for leader in c.get("leaders", []):
                        nom = leader.get("athlete", {}).get("displayName")
                        val = float(str(leader.get("displayValue", 0)).replace(",", ""))
                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[nom][tipo] = val
    except Exception:
        pass

    if not jugadores:
        try:
            url_v3 = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/teams/{team_id}/athletes/statistics"
            r3 = requests.get(url_v3, headers=HEADERS, timeout=5)
            if r3.status_code == 200:
                for cat in r3.json().get("categories", []):
                    for ath in cat.get("athletes", []):
                        nom = ath.get("athlete", {}).get("displayName")
                        if not nom: continue
                        if nom not in jugadores:
                            jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                        for st in ath.get("stats", []):
                            s_name = st.get("name", "").lower()
                            s_val = float(str(st.get("value", 0)).replace(",", ""))
                            if "passingyards" in s_name and s_val > 50.0:
                                jugadores[nom]["Yardas Pase"] = s_val
                            elif "rushingyards" in s_name and s_val > 15.0:
                                jugadores[nom]["Yardas Acarreo"] = s_val
                            elif "receivingyards" in s_name and s_val > 15.0:
                                jugadores[nom]["Yardas Recepción"] = s_val
                            elif "receptions" in s_name and s_val > 1.5:
                                jugadores[nom]["Recepciones"] = s_val
        except Exception:
            pass

    return list(jugadores.values())


def _calcular_prop_seguro_nfl(media_real, tipo_prop):
    linea = math.floor(media_real) + 0.5
    sigma = max(2.5, media_real * 0.25)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under

    if prob_sel >= 0.74: cuota = 1.48
    elif prob_sel >= 0.70: cuota = 1.55
    elif prob_sel >= 0.66: cuota = 1.63
    elif prob_sel >= 0.62: cuota = 1.72
    elif prob_sel >= 0.58: cuota = 1.80
    else: cuota = 1.88

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
    key = f"{local}_{visitante}_nfl_best_props"
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

    pool = _extraer_atletas_vivos_nfl(id_loc, abbr_loc) + _extraer_atletas_vivos_nfl(id_vis, abbr_vis)
    todas_las_props = []

    for j in pool:
        for tipo in ["Yardas Pase", "Yardas Acarreo", "Yardas Recepción", "Recepciones"]:
            if tipo in j and j[tipo] > 0:
                c = _calcular_prop_seguro_nfl(j[tipo], tipo)
                if c["prob_real"] >= 58.0 and c["ev"] >= 1.0:
                    score_seguridad = (c["prob_real"] * 0.80) + (c["ev"] * 0.20)
                    todas_las_props.append({
                        "jugador": j["nombre"],
                        "equipo_abbr": j["equipo"],
                        "tipo_prop": tipo,
                        "lado": c["lado"],
                        "linea": c["linea"],
                        "cuota": c["cuota"],
                        "prob_real": c["prob_real"],
                        "ev": c["ev"],
                        "proyeccion": c["proyeccion"],
                        "_score": score_seguridad
                    })

    todas_las_props.sort(key=lambda x: x["_score"], reverse=True)
    for p in todas_las_props:
        p.pop("_score", None)

    res = todas_las_props[:top_n]
    _PROPS_CACHE_NFL[key] = (now, res)
    return res
