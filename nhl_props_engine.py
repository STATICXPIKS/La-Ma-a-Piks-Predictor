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
                ppg = round(s.get("points", 0) / games, 2)
                spg = round(s.get("shots", 0) / games, 2)
                if ppg >= 0.70 or spg >= 2.2:
                    jugadores[key] = {
                        "nombre": nom,
                        "equipo": abbr.upper(),
                        "Puntos": ppg,
                        "Tiros a Puerta": spg
                    }
    except Exception:
        pass

    if jugadores:
        _CACHE_STATS_NHL[abbr_clean] = (ahora, jugadores)
    return jugadores


def _evaluar_solo_over_nhl(media_real: float, tipo_prop: str, linea_casino=None, cuota_over=None):
    """Evalúa EXCLUSIVAMENTE el lado MÁS DE (OVER) para +1/+2 Puntos y 1.5/2.5 Tiros a Puerta."""
    if tipo_prop == "Tiros a Puerta":
        if linea_casino is not None and linea_casino in [1.5, 2.5]:
            linea = linea_casino
        else:
            if media_real >= 3.2:
                linea = 2.5
            elif media_real >= 2.2:
                linea = 1.5
            else:
                return None

        sigma = max(0.85, media_real * 0.27)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        # Puntos: +1 Punto (0.5) o +2 Puntos (1.5)
        if linea_casino is not None and linea_casino in [0.5, 1.5]:
            linea = linea_casino
        else:
            if media_real >= 1.55:
                linea = 1.5
            elif media_real >= 0.80:
                linea = 0.5
            else:
                return None

        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    if prob_over < 0.56:
        return None

    if cuota_over and cuota_over > 1.05:
        cuota_sel = cuota_over
    else:
        cuota_sel = round(max(1.25, (1.0 / prob_over) * 1.03), 2)

    ev_sel = (prob_over * cuota_sel) - 1.0
    if ev_sel <= 0:
        return None

    proy = max(int(math.ceil(linea)), int(round(media_real)))

    return {
        "lado": "MÁS DE",
        "linea": linea,
        "cuota": cuota_sel,
        "prob_real": round(prob_over * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy
    }


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    abbr_loc = MAPEO_EQUIPOS_NHL.get(local)
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante)
    if not abbr_loc or not abbr_vis:
        return []

    stats_totales = {**_obtener_stats_equipo_nhl(abbr_loc), **_obtener_stats_equipo_nhl(abbr_vis)}
    if not stats_totales:
        return []

    candidatas = []
    props_casino = obtener_player_props_kambi("nhl", local, visitante)

    if props_casino:
        for p in props_casino:
            datos_atleta = stats_totales.get(_normalizar_nombre(p["jugador"]))
            if not datos_atleta:
                continue
            tipo = p["tipo_prop"]
            media_real = datos_atleta.get(tipo)
            if not media_real or media_real <= 0:
                continue

            res = _evaluar_solo_over_nhl(media_real, tipo, p["linea"], p["cuota_over"])
            if res:
                score = (res["prob_real"] * 0.80) + (res["ev"] * 0.20)
                candidatas.append({
                    "jugador": datos_atleta["nombre"],
                    "equipo_abbr": datos_atleta["equipo"],
                    "tipo_prop": tipo,
                    "lado": "MÁS DE",
                    "linea": res["linea"],
                    "cuota": res["cuota"],
                    "prob_real": res["prob_real"],
                    "ev": res["ev"],
                    "proyeccion": res["proyeccion"],
                    "_score": score
                })

    if not candidatas:
        for datos_atleta in stats_totales.values():
            for tipo in ["Puntos", "Tiros a Puerta"]:
                media_real = datos_atleta.get(tipo)
                if not media_real or media_real <= 0:
                    continue
                res = _evaluar_solo_over_nhl(media_real, tipo)
                if res:
                    score = (res["prob_real"] * 0.80) + (res["ev"] * 0.20)
                    candidatas.append({
                        "jugador": datos_atleta["nombre"],
                        "equipo_abbr": datos_atleta["equipo"],
                        "tipo_prop": tipo,
                        "lado": "MÁS DE",
                        "linea": res["linea"],
                        "cuota": res["cuota"],
                        "prob_real": res["prob_real"],
                        "ev": res["ev"],
                        "proyeccion": res["proyeccion"],
                        "_score": score
                    })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
