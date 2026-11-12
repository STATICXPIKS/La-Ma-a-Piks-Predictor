import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

EQUIPOS_MLB_ID = {
    "Arizona Diamondbacks": ("ari", 109), "Atlanta Braves": ("atl", 144), "Baltimore Orioles": ("bal", 110),
    "Boston Red Sox": ("bos", 111), "Chicago Cubs": ("chc", 112), "Chicago White Sox": ("cws", 145),
    "Cincinnati Reds": ("cin", 113), "Cleveland Guardians": ("cle", 114), "Colorado Rockies": ("col", 115),
    "Detroit Tigers": ("det", 116), "Houston Astros": ("hou", 117), "Kansas City Royals": ("kc", 118),
    "Los Angeles Angels": ("laa", 108), "Los Angeles Dodgers": ("lad", 119), "Miami Marlins": ("mia", 146),
    "Milwaukee Brewers": ("mil", 158), "Minnesota Twins": ("min", 142), "New York Mets": ("nym", 121),
    "New York Yankees": ("nyy", 147), "Oakland Athletics": ("oak", 133), "Philadelphia Phillies": ("phi", 143),
    "Pittsburgh Pirates": ("pit", 134), "San Diego Padres": ("sd", 135), "San Francisco Giants": ("sf", 137),
    "Seattle Mariners": ("sea", 136), "St. Louis Cardinals": ("stl", 138), "Tampa Bay Rays": ("tb", 139),
    "Texas Rangers": ("tex", 140), "Toronto Blue Jays": ("tor", 141), "Washington Nationals": ("wsh", 120)
}

_CACHE_STATS_MLB = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_stats_equipo_mlb(team_id: int, abbr: str):
    ahora = time.time()
    if team_id in _CACHE_STATS_MLB and (ahora - _CACHE_STATS_MLB[team_id][0] < 1800):
        return _CACHE_STATS_MLB[team_id][1]

    jugadores = {}
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=active"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            for item in r.json().get("roster", []):
                person = item.get("person", {})
                nom = person.get("fullName")
                pid = person.get("id")
                if not nom or not pid:
                    continue
                key = _normalizar_nombre(nom)
                jugadores[key] = {"nombre": nom, "equipo": abbr.upper(), "id": pid}
    except Exception:
        pass

    if jugadores:
        _CACHE_STATS_MLB[team_id] = (ahora, jugadores)
    return jugadores


def obtener_mejores_props_mlb(local: str, visitante: str, top_n: int = 6):
    props_casino = obtener_player_props_kambi("mlb", local, visitante)
    if not props_casino:
        return []

    d_loc = EQUIPOS_MLB_ID.get(local)
    d_vis = EQUIPOS_MLB_ID.get(visitante)
    if not d_loc or not d_vis:
        return []

    stats_totales = {**_obtener_stats_equipo_mlb(d_loc[1], d_loc[0]), **_obtener_stats_equipo_mlb(d_vis[1], d_vis[0])}
    candidatas = []

    for p in props_casino:
        key_jug = _normalizar_nombre(p["jugador"])
        datos_atleta = stats_totales.get(key_jug)
        if not datos_atleta:
            continue

        linea = p["linea"]
        lamb = max(0.5, linea * 1.05)
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

        ev_over = (prob_over * p["cuota_over"]) - 1.0
        ev_under = (prob_under * p["cuota_under"]) - 1.0

        if prob_over >= prob_under and ev_over > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, p["cuota_over"], ev_over
        elif ev_under > 0:
            lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, p["cuota_under"], ev_under
        else:
            continue

        if prob_sel * 100 >= 54.0 and ev_sel * 100 >= 1.5:
            score = (prob_sel * 100 * 0.75) + (ev_sel * 100 * 0.25)
            candidatas.append({
                "jugador": datos_atleta["nombre"],
                "equipo_abbr": datos_atleta["equipo"],
                "tipo_prop": p["tipo_prop"],
                "lado": lado,
                "linea": linea,
                "cuota": cuota_sel,
                "prob_real": round(prob_sel * 100, 1),
                "ev": round(ev_sel * 100, 1),
                "proyeccion": int(math.ceil(linea)) if lado == "MÁS DE" else int(math.floor(linea)),
                "_score": score
            })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
