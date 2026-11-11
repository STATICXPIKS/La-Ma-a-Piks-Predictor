import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_NBA = {
    "Atlanta Hawks": "atl", "Boston Celtics": "bos", "Brooklyn Nets": "bkn",
    "Charlotte Hornets": "cha", "Chicago Bulls": "chi", "Cleveland Cavaliers": "cle",
    "Dallas Mavericks": "dal", "Denver Nuggets": "den", "Detroit Pistons": "det",
    "Golden State Warriors": "gsw", "Houston Rockets": "hou", "Indiana Pacers": "ind",
    "LA Clippers": "lac", "Los Angeles Clippers": "lac", "Los Angeles Lakers": "lal",
    "Memphis Grizzlies": "mem", "Miami Heat": "mia", "Milwaukee Bucks": "mil",
    "Minnesota Timberwolves": "min", "New Orleans Pelicans": "nop", "New York Knicks": "nyk",
    "Oklahoma City Thunder": "okc", "Orlando Magic": "orl", "Philadelphia 76ers": "phi",
    "Phoenix Suns": "phx", "Portland Trail Blazers": "por", "Sacramento Kings": "sac",
    "San Antonio Spurs": "sas", "Toronto Raptors": "tor", "Utah Jazz": "uta",
    "Washington Wizards": "was"
}

NOMBRES_MERCADOS_NBA = {
    "player_points": "Puntos",
    "player_rebounds": "Rebotes",
    "player_assists": "Asistencias",
    "player_threes": "Triples Anotados"
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


def obtener_roster_activo_espn(espn_abbr: str):
    """
    Obtiene los atletas que realmente forman parte de la plantilla oficial de ESPN hoy.
    """
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and len(data) > 0:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{espn_abbr}/roster"
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


def obtener_estadisticas_reales_atleta(athlete_id: str):
    """
    Extrae los promedios reales por partido registrados en la API de ESPN.
    """
    if not athlete_id:
        return {}

    now = time.time()
    if athlete_id in _STATS_CACHE:
        ts, val = _STATS_CACHE[athlete_id]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
    res_stats = {}

    targets = {
        "player_points": ["avgpoints", "pointspergame", "pts"],
        "player_rebounds": ["avgrebounds", "reboundspergame", "reb"],
        "player_assists": ["avgassists", "assistspergame", "ast"],
        "player_threes": ["threepointfieldgoalsmadepergame", "avgthreepointfieldgoalsmade", "3pm"]
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
                    # Ponderación: 70% temporada actual, 30% anterior si existen 2 años de registro
                    promedio = round((vals[0] * 0.70) + (vals[1] * 0.30), 1) if len(vals) >= 2 else round(vals[0], 1)
                    res_stats[m_key] = promedio

            _STATS_CACHE[athlete_id] = (now, res_stats)
    except Exception:
        pass

    return res_stats


def verificar_atleta_en_plantilla(nombre_raw: str, roster_loc: dict, roster_vis: dict, abbr_loc: str, abbr_vis: str):
    """
    Comprueba si el atleta pertenece estrictamente al equipo local o visitante analizado.
    """
    norm = _normalizar_texto(nombre_raw)

    if norm in roster_loc:
        d = roster_loc[norm]
        return abbr_loc, d["nombre"], d["id"]

    if norm in roster_vis:
        d = roster_vis[norm]
        return abbr_vis, d["nombre"], d["id"]

    # Coincidencia exacta de partes (nombre y apellido completo)
    partes = norm.split()
    if len(partes) >= 2:
        for k, d in roster_loc.items():
            if partes[0] in k and partes[-1] in k:
                return abbr_loc, d["nombre"], d["id"]
        for k, d in roster_vis.items():
            if partes[0] in k and partes[-1] in k:
                return abbr_vis, d["nombre"], d["id"]

    return None, nombre_raw, None


def _calcular_probabilidad_matematica(media_real: float, linea_casino: float, tipo_prop: str):
    """
    Calcula la probabilidad real sin factores inventados.
    """
    if media_real <= 0 or linea_casino <= 0:
        return 0.50, 0.50

    # Puntos y Rebotes: Distribución Normal empírica
    if tipo_prop in ["player_points", "player_rebounds"]:
        cv = 0.23 if tipo_prop == "player_points" else 0.28
        sigma = media_real * cv
        z = (linea_casino - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_under = max(0.12, min(0.88, prob_under))
        return (1.0 - prob_under), prob_under
    # Asistencias y Triples: Distribución de Poisson (conteo bajo)
    else:
        lamb = media_real
        k_max = int(math.floor(linea_casino))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_under = max(0.12, min(0.88, prob_under))
        return (1.0 - prob_under), prob_under


def _obtener_odds_props_nba_live(sport_key: str, event_id: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    try:
        r = requests.get(url, params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "player_points,player_rebounds,player_assists,player_threes",
            "oddsFormat": "decimal"
        }, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_event_id_nba_odds(sport_key: str, local_name: str, vis_name: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    try:
        r = requests.get(url, params={"apiKey": ODDS_API_KEY}, timeout=4)
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


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_nba_real_data_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_NBA.get(local, "nba")
    abbr_vis = MAPEO_EQUIPOS_NBA.get(visitante, "nba")

    roster_loc = obtener_roster_activo_espn(abbr_loc)
    roster_vis = obtener_roster_activo_espn(abbr_vis)

    candidatas = []
    event_id = _obtener_event_id_nba_odds("basketball_nba", local, visitante)

    # 1. EVALUAR LÍNEAS REALES DEL CASINO CONTRA ESTADÍSTICAS REALES DE ESPN
    if event_id:
        odds_data = _obtener_odds_props_nba_live("basketball_nba", event_id)
        if odds_data and "bookmakers" in odds_data:
            for bookmaker in odds_data["bookmakers"]:
                for market in bookmaker.get("markets", []):
                    m_key = market.get("key")
                    nombre_tipo = NOMBRES_MERCADOS_NBA.get(m_key, m_key)
                    for outcome in market.get("outcomes", []):
                        jugador_raw = outcome.get("description", outcome.get("name", "")).strip()
                        tipo_apuesta = outcome.get("name", "Over")
                        linea = outcome.get("point")
                        cuota = outcome.get("price")

                        if not linea or not cuota or cuota < 1.45 or cuota > 2.50:
                            continue

                        # Verificación estricta: debe estar en el roster del local o visitante
                        equipo_real, nombre_oficial, athlete_id = verificar_atleta_en_plantilla(
                            jugador_raw, roster_loc, roster_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real or not athlete_id:
                            continue

                        stats = obtener_estadisticas_reales_atleta(athlete_id)
                        promedio_real = stats.get(m_key)

                        # Si no hay estadística histórica registrada en ESPN, no se emite pick
                        if not promedio_real or promedio_real <= 0:
                            continue

                        prob_over, prob_under = _calcular_probabilidad_matematica(promedio_real, linea, m_key)
                        es_over = (tipo_apuesta.lower() == "over")
                        prob_sel = prob_over if es_over else prob_under

                        # Fórmula de Valor Esperado (+EV)
                        ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

                        # Solo se aprueban apuestas con margen matemático a favor y cuota viable
                        if 2.5 <= ev <= 22.0:
                            candidatas.append({
                                "jugador": nombre_oficial,
                                "equipo_abbr": equipo_real,
                                "tipo_prop": nombre_tipo,
                                "lado": "MÁS DE" if es_over else "MENOS DE",
                                "linea": linea,
                                "cuota": round(cuota, 2),
                                "prob_real": round(prob_sel * 100, 1),
                                "ev": ev,
                                "proyeccion": promedio_real
                            })

    # Filtrar picks duplicados quedándose con la mejor cuota/EV
    unicos = {}
    for p in candidatas:
        k = (p["jugador"], p["tipo_prop"], p["lado"])
        if k not in unicos or p["ev"] > unicos[k]["ev"]:
            unicos[k] = p

    ordenadas = sorted(unicos.values(), key=lambda x: x["ev"], reverse=True)
    seleccion = ordenadas[:top_n]

    _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
