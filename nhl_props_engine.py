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
    "Utah Hockey Club": "uta", "Utah Mammoth": "uta", "Vancouver Canucks": "van",
    "Vegas Golden Knights": "vgk", "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_CACHE_STATS_NHL = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_ids_roster_activo(abbr_clean: str) -> dict:
    """Obtiene únicamente los jugadores que pertenecen HOY al roster activo del equipo."""
    ids_activos = {}
    url_roster = f"https://api-web.nhle.com/v1/roster/{abbr_clean}/current"
    try:
        r = requests.get(url_roster, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            for grupo in ["forwards", "defensemen"]:
                for p in data.get(grupo, []):
                    pid = p.get("id")
                    nom = f"{p.get('firstName', {}).get('default', '')} {p.get('lastName', {}).get('default', '')}".strip()
                    if pid and nom:
                        ids_activos[pid] = nom
    except Exception as e:
        print(f"Error roster NHL {abbr_clean}: {e}")
    return ids_activos


def _obtener_stats_equipo_nhl(abbr: str):
    abbr_clean = abbr.lower()
    ahora = time.time()
    if abbr_clean in _CACHE_STATS_NHL and (ahora - _CACHE_STATS_NHL[abbr_clean][0] < 1800):
        return _CACHE_STATS_NHL[abbr_clean][1]

    roster_activo = _obtener_ids_roster_activo(abbr_clean)
    jugadores = {}
    url_nhl = f"https://api-web.nhle.com/v1/club-stats/{abbr_clean}/now"

    try:
        r = requests.get(url_nhl, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            for s in r.json().get("skaters", []):
                pid = s.get("playerId")
                # Filtrar estrictamente: si tenemos roster activo, exigir que el jugador siga hoy en el equipo
                if roster_activo and pid not in roster_activo:
                    continue

                games = s.get("gamesPlayed", 0)
                if games < 3:
                    continue

                nom = roster_activo.get(pid) if roster_activo else f"{s.get('firstName', {}).get('default', '')} {s.get('lastName', {}).get('default', '')}".strip()
                if not nom:
                    continue

                key = _normalizar_nombre(nom)
                ppg = round(s.get("points", 0) / games, 2)
                spg = round(s.get("shots", 0) / games, 2)

                jugadores[key] = {
                    "nombre": nom,
                    "equipo": abbr.upper(),
                    "Puntos": ppg,
                    "Tiros a Puerta": spg
                }
    except Exception as e:
        print(f"Error stats NHL {abbr_clean}: {e}")

    if jugadores:
        _CACHE_STATS_NHL[abbr_clean] = (ahora, jugadores)
    return jugadores


def _probabilidad_poisson_over(media: float, linea: float) -> float:
    k_max = int(math.floor(linea))
    prob_under = sum((math.exp(-media) * (media ** k)) / math.factorial(k) for k in range(k_max + 1))
    return max(0.01, min(0.95, 1.0 - prob_under))


def _evaluar_prop_nhl(media_real: float, tipo_prop: str, linea: float, cuota_over: float, cuota_under=None):
    prob_over = _probabilidad_poisson_over(media_real, linea)
    prob_under = 1.0 - prob_over

    # Si tenemos cuota de mercado both-ways, suavizamos 70% estadística real + 30% mercado
    if cuota_over and cuota_under and cuota_over > 1.05 and cuota_under > 1.05:
        imp_o = 1.0 / cuota_over
        imp_u = 1.0 / cuota_under
        mkt_o = imp_o / (imp_o + imp_u)
        prob_over = (prob_over * 0.70) + (mkt_o * 0.30)
        prob_under = 1.0 - prob_over

    ev_over = (prob_over * cuota_over) - 1.0

    # Evaluar lado MÁS DE (Over)
    if prob_over >= 0.53 and ev_over > 0.01:
        proy = max(int(math.ceil(linea)), int(round(media_real)))
        return {
            "lado": "MÁS DE",
            "linea": linea,
            "cuota": round(cuota_over, 2),
            "prob_real": round(prob_over * 100, 1),
            "ev": round(ev_over * 100, 1),
            "proyeccion": proy
        }

    # Evaluar lado MENOS DE (Under) si hay cuota real y valor positivo
    if cuota_under and cuota_under > 1.05:
        ev_under = (prob_under * cuota_under) - 1.0
        if prob_under >= 0.55 and ev_under > 0.02:
            proy = min(int(math.floor(linea)), int(round(media_real)))
            return {
                "lado": "MENOS DE",
                "linea": linea,
                "cuota": round(cuota_under, 2),
                "prob_real": round(prob_under * 100, 1),
                "ev": round(ev_under * 100, 1),
                "proyeccion": proy
            }

    return None


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    abbr_loc = MAPEO_EQUIPOS_NHL.get(local)
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante)
    if not abbr_loc or not abbr_vis:
        return []

    stats_totales = {**_obtener_stats_equipo_nhl(abbr_loc), **_obtener_stats_equipo_nhl(abbr_vis)}
    if not stats_totales:
        return []

    props_casino = obtener_player_props_kambi("nhl", local, visitante)
    candidatas = []

    if props_casino:
        for p in props_casino:
            datos_atleta = stats_totales.get(_normalizar_nombre(p["jugador"]))
            if not datos_atleta:
                continue

            tipo = p["tipo_prop"]
            media_real = datos_atleta.get(tipo)
            if not media_real or media_real <= 0:
                continue

            res = _evaluar_prop_nhl(
                media_real=media_real,
                tipo_prop=tipo,
                linea=p["linea"],
                cuota_over=p["cuota_over"],
                cuota_under=p.get("cuota_under")
            )
            if res:
                score = (res["prob_real"] * 0.65) + (res["ev"] * 0.35)
                candidatas.append({
                    "jugador": datos_atleta["nombre"],
                    "equipo_abbr": datos_atleta["equipo"],
                    "tipo_prop": tipo,
                    "lado": res["lado"],
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
