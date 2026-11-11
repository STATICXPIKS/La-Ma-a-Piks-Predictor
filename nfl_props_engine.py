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


def _consultar_estadisticas_reales_nfl(team_id, abbr):
    """Descarga los líderes reales de Yardas Pase, Acarreo y Recepción desde ESPN."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/statistics"
    jugadores = {}

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            cats = data.get("results", {}).get("stats", {}).get("categories", [])
            mapeo = {
                "passingYards": "Yardas Pase",
                "rushingYards": "Yardas Acarreo",
                "receivingYards": "Yardas Recepción",
                "receptions": "Recepciones"
            }
            for c in cats:
                c_name = c.get("name")
                if c_name in mapeo:
                    tipo = mapeo[c_name]
                    for leader in c.get("leaders", []):
                        nom = leader.get("athlete", {}).get("displayName")
                        val = float(str(leader.get("displayValue", 0)).replace(",", ""))
                        if nom and val > 0:
                            if nom not in jugadores:
                                jugadores[nom] = {"nombre": nom, "equipo": abbr.upper()}
                            jugadores[nom][tipo] = val
    except Exception as e:
        print(f"Error en consulta ESPN NFL {abbr}: {e}")

    if not jugadores:
        try:
            url_v3 = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/teams/{team_id}/athletes/statistics"
            r3 = requests.get(url_v3, headers=HEADERS, timeout=5)
            if r3.status_code == 200:
                d3 = r3.json()
                for cat in d3.get("categories", []):
                    for ath in cat.get("athletes", []):
                        nom = ath.get("athlete", {}).get("displayName")
                        if not nom:
                            continue
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


def _evaluar_mercado_prop_nfl(media_real: float, tipo_prop: str):
    linea = math.floor(media_real) + 0.5
    sigma = max(2.5, media_real * 0.28)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under

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


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NFL_ESPN.get(local)
    d_vis = EQUIPOS_NFL_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    abbr_loc, id_loc = d_loc
    abbr_vis, id_vis = d_vis

    jugadores_loc = _consultar_estadisticas_reales_nfl(id_loc, abbr_loc)
    jugadores_vis = _consultar_estadisticas_reales_nfl(id_vis, abbr_vis)

    def procesar_equipo(jugadores):
        lista = []
        for j in jugadores:
            for tipo in ["Yardas Pase", "Yardas Acarreo", "Yardas Recepción", "Recepciones"]:
                if tipo in j and j[tipo] > 0:
                    c = _evaluar_mercado_prop_nfl(j[tipo], tipo)
                    if c["prob_real"] >= 55.0 and c["ev"] >= 1.0:
                        score = (c["prob_real"] * 0.7) + (c["ev"] * 0.3)
                        lista.append({
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
        lista.sort(key=lambda x: x["_score"], reverse=True)
        return lista

    props_loc = procesar_equipo(jugadores_loc)
    props_vis = procesar_equipo(jugadores_vis)

    cupo = top_n // 2
    resultado = props_loc[:cupo] + props_vis[:cupo]

    if len(resultado) < top_n:
        faltan = top_n - len(resultado)
        extras = props_loc[cupo:] + props_vis[cupo:]
        extras.sort(key=lambda x: x["_score"], reverse=True)
        resultado += extras[:faltan]

    for p in resultado:
        p.pop("_score", None)

    return resultado
