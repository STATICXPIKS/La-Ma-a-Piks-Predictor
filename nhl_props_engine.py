import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_NHL = {
    "Anaheim Ducks": "ana", "Boston Bruins": "bos", "Buffalo Sabres": "buf",
    "Calgary Flames": "cgy", "Carolina Hurricanes": "car", "Chicago Blackhawks": "chi",
    "Colorado Avalanche": "col", "Columbus Blue Jackets": "cbj", "Dallas Stars": "dal",
    "Detroit Red Wings": "det", "Edmonton Oilers": "edm", "Florida Panthers": "fla",
    "Los Angeles Kings": "la", "Minnesota Wild": "min", "Montreal Canadiens": "mtl",
    "Nashville Predators": "nsh", "New Jersey Devils": "nj", "New York Islanders": "nyi",
    "New York Rangers": "nyr", "Ottawa Senators": "ott", "Philadelphia Flyers": "phi",
    "Pittsburgh Penguins": "pit", "San Jose Sharks": "sj", "Seattle Kraken": "sea",
    "St. Louis Blues": "stl", "Tampa Bay Lightning": "tb", "Toronto Maple Leafs": "tor",
    "Utah Hockey Club": "utah", "Vancouver Canucks": "van", "Vegas Golden Knights": "vgk",
    "Washington Capitals": "wsh", "Winnipeg Jets": "wpg"
}

NOMBRES_MERCADOS_NHL = {
    "player_shots_on_goal": "Tiros a Puerta",
    "player_points": "Puntos (G+A)"
}

HEADERS_ESPN = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE = {}
_ROSTER_CACHE = {}
_STATS_CACHE = {}
CACHE_DURATION_SECONDS = 900


def _normalizar_texto(texto: str) -> str:
    return texto.lower().replace(".", "").replace("'", "").replace("-", " ").strip()


def obtener_roster_activo_nhl(espn_abbr: str):
    """
    Obtiene la plantilla activa de ESPN para validar la pertenencia real del jugador.
    """
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and len(data) > 0:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{espn_abbr}/roster"
    jugadores = {}

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=4)
        if r.status_code == 200:
            res = r.json()
            raw_athletes = res.get("athletes", [])

            def registrar_atleta(item):
                nombre = item.get("displayName", "")
                ath_id = str(item.get("id", ""))
                pos_obj = item.get("position", {})
                pos = pos_obj.get("abbreviation", "") if isinstance(pos_obj, dict) else str(pos_obj)
                if nombre and ath_id:
                    jugadores[_normalizar_texto(nombre)] = {
                        "id": ath_id,
                        "nombre": nombre,
                        "posicion": pos.upper(),
                        "equipo": espn_abbr
                    }

            if raw_athletes and isinstance(raw_athletes[0], dict) and "items" in raw_athletes[0]:
                for group in raw_athletes:
                    for item in group.get("items", []):
                        registrar_atleta(item)
            else:
                for item in raw_athletes:
                    registrar_atleta(item)
    except Exception:
        pass

    _ROSTER_CACHE[espn_abbr] = (now, jugadores)
    return jugadores


def obtener_estadisticas_reales_nhl(athlete_id: str):
    """
    Consulta los promedios reales por partido en la API de ESPN (tiros y puntos).
    """
    if not athlete_id:
        return {}

    now = time.time()
    if athlete_id in _STATS_CACHE:
        ts, val = _STATS_CACHE[athlete_id]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/hockey/nhl/athletes/{athlete_id}/stats"
    res_stats = {}

    targets = {
        "player_shots_on_goal": ["avgshots", "shotspergame", "sog", "shots"],
        "player_points": ["avgpoints", "pointspergame", "pts", "points"]
    }

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=3)
        if r.status_code == 200:
            data = r.json()
            acumulados = {k: [] for k in targets}

            for cat in data.get("categories", []):
                for stat in cat.get("statistics", []):
                    n = stat.get("name", "").lower()
                    a = stat.get("abbreviation", "").lower()
                    for m_key, aliases in targets.items():
                        if n in aliases or a in aliases:
                            try:
                                val_num = float(str(stat.get("displayValue", "0")).replace(",", ""))
                                acumulados[m_key].append(val_num)
                            except ValueError:
                                pass

            for m_key, vals in acumulados.items():
                if vals:
                    promedio = round((vals[0] * 0.70) + (vals[1] * 0.30), 2) if len(vals) >= 2 else round(vals[0], 2)
                    res_stats[m_key] = promedio

            _STATS_CACHE[athlete_id] = (now, res_stats)
    except Exception:
        pass

    return res_stats


def verificar_atleta_en_plantilla_nhl(nombre_raw: str, roster_loc: dict, roster_vis: dict, abbr_loc: str, abbr_vis: str):
    norm = _normalizar_texto(nombre_raw)

    if norm in roster_loc:
        d = roster_loc[norm]
        return abbr_loc, d["nombre"], d["id"]

    if norm in roster_vis:
        d = roster_vis[norm]
        return abbr_vis, d["nombre"], d["id"]

    partes = norm.split()
    if len(partes) >= 2:
        for k, d in roster_loc.items():
            if partes[0] in k and partes[-1] in k:
                return abbr_loc, d["nombre"], d["id"]
        for k, d in roster_vis.items():
            if partes[0] in k and partes[-1] in k:
                return abbr_vis, d["nombre"], d["id"]

    return None, nombre_raw, None


def _calcular_probabilidad_over_poisson(media_real: float, linea_casino: float):
    if media_real <= 0 or linea_casino <= 0:
        return 0.50
    lamb = media_real
    k_max = int(math.floor(linea_casino))
    prob_under = 0.0
    for k in range(k_max + 1):
        prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
    prob_over = max(0.15, min(0.88, 1.0 - prob_under))
    return prob_over


def _obtener_odds_props_nhl_live(sport_key: str, event_id: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    try:
        r = requests.get(url, params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "player_shots_on_goal,player_points",
            "oddsFormat": "decimal"
        }, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_event_id_nhl_odds(sport_key: str, local_name: str, vis_name: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    try:
        r = requests.get(url, params={"apiKey": ODDS_API_KEY}, timeout=3)
        if r.status_code == 200:
            loc_clean = _normalizar_texto(local_name)
            vis_clean = _normalizar_texto(vis_name)
            for ev in r.json():
                h = _normalizar_texto(ev.get("home_team", ""))
                a = _normalizar_texto(ev.get("away_team", ""))
                if (loc_clean in h or h in loc_clean) and (vis_clean in a or a in vis_clean):
                    return ev.get("id")
    except Exception:
        pass
    return None


def obtener_mejores_props_nhl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_nhl_real_data_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_NHL.get(local, "nhl")
    abbr_vis = MAPEO_EQUIPOS_NHL.get(visitante, "nhl")

    roster_loc = obtener_roster_activo_nhl(abbr_loc)
    roster_vis = obtener_roster_activo_nhl(abbr_vis)

    candidatas = []
    event_id = _obtener_event_id_nhl_odds("icehockey_nhl", local, visitante)

    # EVALUAR LÍNEAS REALES CON ESTADÍSTICAS REALES DE ESPN
    if event_id:
        odds_data = _obtener_odds_props_nhl_live("icehockey_nhl", event_id)
        if odds_data and "bookmakers" in odds_data:
            for bookmaker in odds_data["bookmakers"]:
                for market in bookmaker.get("markets", []):
                    m_key = market.get("key")
                    nombre_tipo = NOMBRES_MERCADOS_NHL.get(m_key, m_key)
                    for outcome in market.get("outcomes", []):
                        tipo_apuesta = outcome.get("name", "").strip().lower()

                        # Regla 1: Exclusivamente OVER (MÁS DE)
                        if tipo_apuesta != "over":
                            continue

                        linea = outcome.get("point")
                        cuota = outcome.get("price")
                        jugador_raw = outcome.get("description", outcome.get("name", "")).strip()

                        if not linea or not cuota:
                            continue

                        # Regla 2: Puntos (+1 o +2 puntos) con cuotas desde 1.25 hasta 3.20
                        if m_key == "player_points":
                            if linea not in [0.5, 1.5]:
                                continue
                            if cuota < 1.25 or cuota > 3.20:
                                continue

                        # Regla 3: Tiros a puerta (solo 1.5 y 2.5) con cuota mayor a 1.50
                        elif m_key == "player_shots_on_goal":
                            if linea not in [1.5, 2.5]:
                                continue
                            if cuota < 1.50 or cuota > 2.65:
                                continue
                        else:
                            continue

                        # Verificación estricta de pertenencia al equipo
                        equipo_real, nombre_oficial, athlete_id = verificar_atleta_en_plantilla_nhl(
                            jugador_raw, roster_loc, roster_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real or not athlete_id:
                            continue

                        stats = obtener_estadisticas_reales_nhl(athlete_id)
                        promedio_real = stats.get(m_key)

                        # Sin estadística real, no se emite propuesta
                        if not promedio_real or promedio_real <= 0:
                            continue

                        prob_sel = _calcular_probabilidad_over_poisson(promedio_real, linea)
                        ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

                        # Filtro de valor positivo real
                        if 1.0 <= ev <= 25.0:
                            candidatas.append({
                                "jugador": nombre_oficial,
                                "equipo_abbr": equipo_real,
                                "tipo_prop": nombre_tipo,
                                "lado": "MÁS DE",
                                "linea": linea,
                                "cuota": round(cuota, 2),
                                "prob_real": round(prob_sel * 100, 1),
                                "ev": ev,
                                "proyeccion": promedio_real
                            })

    # Filtrar picks duplicados quedándose con la opción de mayor EV
    unicos = {}
    for p in candidatas:
        k = (p["jugador"], p["tipo_prop"], p["linea"])
        if k not in unicos or p["ev"] > unicos[k]["ev"]:
            unicos[k] = p

    ordenadas = sorted(unicos.values(), key=lambda x: x["ev"], reverse=True)
    seleccion = ordenadas[:top_n]

    _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
