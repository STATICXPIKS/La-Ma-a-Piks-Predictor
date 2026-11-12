import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

MAPEO_EQUIPOS_NHL = {
    "Anaheim Ducks": "ana", "Boston Bruins": "bos", "Buffalo Sabres": "buf",
    "Calgary Flames": "cgy", "Carolina Hurricanes": "car", "Chicago Blackhawks": "chi",
    "Colorado Avalanche": "col", "Columbus Blue Jackets": "cbj", "Dallas Stars": "dal",
    "Detroit Red Wings": "det", "Edmonton Oilers": "edm", "Florida Panthers": "fla",
    "Los Angeles Kings": "lak", "Minnesota Wild": "min", "Montreal Canadiens": "mtl",
    "Nashville Predators": "nsh", "New Jersey Devils": "njd", "New York Islanders": "nyi",
    "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
    "Pittsburgh Penguins": "pit", "San Jose Sharks": "sjs", "Seattle Kraken": "sea",
    "St. Louis Blues": "stl", "Tampa Bay Lightning": "tbl", "Toronto Maple Leafs": "tor",
    "Utah Hockey Club": "uta", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
    "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_CACHE_STATS_NHL = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_stats_equipo_nhl(abbr: str):
    abbr_clean = abbr.lower()
    ahora = time.time()
    if abbr_clean in _CACHE_STATS_NHL and (ahora - _CACHE_STATS_NHL[abbr_clean][0] < 1800):
        return _CACHE_STATS_NHL[abbr_clean][1]

    jugadores = {}
    url_nhl = f"https://api-web.nhle.com/v1/club-stats/{abbr_clean}/now"
    try:
        r = requests.get(url_nhl, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            for s in r.json().get("skaters", []):
                games = s.get("gamesPlayed", 0)
                if games < 3:
                    continue
                nom = f"{s.get('firstName', {}).get('default', '')} {s.get('lastName', {}).get('default', '')}".strip()
                if not nom:
                    continue
                key = _normalizar_nombre(nom)
                jugadores[key] = {
                    "nombre": nom,
                    "equipo": abbr.upper(),
                    "Puntos": round(s.get("points", 0) / games, 2),
                    "Tiros a Puerta": round(s.get("shots", 0) / games, 2)
                }
    except Exception:
        pass

    if jugadores:
        _CACHE_STATS_NHL[abbr_clean] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nhl_contra_casino(media_real: float, linea_casino: float, cuota_over: float, cuota_under: float, tipo_prop: str):
    if tipo_prop == "Tiros a Puerta":
        sigma = max(0.8, media_real * 0.27)
        z = (linea_casino - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea_casino))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    ev_over = (prob_over * cuota_over) - 1.0
    ev_under = (prob_under * cuota_under) - 1.0

    if prob_over >= prob_under and ev_over > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, cuota_over, ev_over
    elif prob_under > prob_over and ev_under > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, cuota_under, ev_under
    elif ev_over >= ev_under and ev_over > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, cuota_over, ev_over
    elif ev_under > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, cuota_under, ev_under
    else:
        return None

    proy = int(round(media_real))
    if lado == "MÁS DE" and proy <= linea_casino:
        proy = int(math.ceil(linea_casino))
    elif lado == "MENOS DE" and proy >= linea_casino:
        proy = int(math.floor(linea_casino))

    return {
        "lado": lado,
        "linea": linea_casino,
        "cuota": cuota_sel,
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy
    }


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    props_casino = obtener_player_props_kambi("nhl", local, visitante)
    if not props_casino:
        return []

    abbr_loc = MAPEO_EQUIPOS_NHL.get(local)
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante)
    if not abbr_loc or not abbr_vis:
        return []

    stats_totales = {**_obtener_stats_equipo_nhl(abbr_loc), **_obtener_stats_equipo_nhl(abbr_vis)}
    candidatas = []

    for p in props_casino:
        key_jug = _normalizar_nombre(p["jugador"])
        datos_atleta = stats_totales.get(key_jug)
        if not datos_atleta:
            continue

        tipo = p["tipo_prop"]
        media_real = datos_atleta.get(tipo)
        if not media_real or media_real <= 0:
            continue

        eval_res = _evaluar_prop_nhl_contra_casino(
            media_real, p["linea"], p["cuota_over"], p["cuota_under"], tipo
        )
        if eval_res and eval_res["prob_real"] >= 54.0 and eval_res["ev"] >= 1.5:
            score = (eval_res["prob_real"] * 0.75) + (eval_res["ev"] * 0.25)
            candidatas.append({
                "jugador": datos_atleta["nombre"],
                "equipo_abbr": datos_atleta["equipo"],
                "tipo_prop": tipo,
                "lado": eval_res["lado"],
                "linea": eval_res["linea"],
                "cuota": eval_res["cuota"],
                "prob_real": eval_res["prob_real"],
                "ev": eval_res["ev"],
                "proyeccion": eval_res["proyeccion"],
                "_score": score
            })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
