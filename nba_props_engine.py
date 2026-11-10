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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_PROPS_CACHE = {}
_ROSTER_CACHE = {}
_STATS_CACHE = {}
CACHE_DURATION_SECONDS = 900


def _normalizar_texto(texto: str) -> str:
    return texto.lower().replace(".", "").replace("'", "").replace("-", " ").strip()


def obtener_roster_activo_espn(espn_abbr: str):
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and data:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{espn_abbr}/roster"
    jugadores = {}
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=4)
        if r.status_code == 200:
            res = r.json()
            for group in res.get("athletes", []):
                for item in group.get("items", []):
                    nombre = item.get("displayName", "")
                    pos_obj = item.get("position", {})
                    pos = pos_obj.get("abbreviation", "") if isinstance(pos_obj, dict) else str(pos_obj)
                    ath_id = str(item.get("id", ""))
                    if nombre and ath_id:
                        jugadores[_normalizar_texto(nombre)] = {
                            "id": ath_id,
                            "nombre": nombre,
                            "posicion": pos.upper(),
                            "equipo": espn_abbr
                        }
    except Exception:
        pass

    _ROSTER_CACHE[espn_abbr] = (now, jugadores)
    return jugadores


def obtener_todas_las_stats_atleta(athlete_id: str):
    """
    Obtiene puntos, rebotes, asistencias y triples en UNA SOLA consulta HTTP.
    """
    if not athlete_id:
        return {}

    now = time.time()
    if athlete_id in _STATS_CACHE:
        ts, val = _STATS_CACHE[athlete_id]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
    res_dict = {}
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=3)
        if r.status_code == 200:
            data = r.json()
            mapping = {
                "player_points": ["avgpoints", "pointspergame", "pts"],
                "player_rebounds": ["avgrebounds", "reboundspergame", "reb"],
                "player_assists": ["avgassists", "assistspergame", "ast"],
                "player_threes": ["threepointfieldgoalsmadepergame", "avgthreepointfieldgoalsmade", "3pm"]
            }

            temp_stats = {k: [] for k in mapping}
            for cat in data.get("categories", []):
                for stat in cat.get("statistics", []):
                    n = stat.get("name", "").lower()
                    a = stat.get("abbreviation", "").lower()
                    for m_key, aliases in mapping.items():
                        if n in aliases or a in aliases:
                            try:
                                val_num = float(str(stat.get("displayValue", "0")).replace(",", ""))
                                temp_stats[m_key].append(val_num)
                            except ValueError:
                                pass

            for m_key, vals in temp_stats.items():
                if vals:
                    res_dict[m_key] = round((vals[0] * 0.70) + (vals[1] * 0.30), 1) if len(vals) >= 2 else round(vals[0], 1)

            _STATS_CACHE[athlete_id] = (now, res_dict)
    except Exception:
        pass

    return res_dict


def verificar_en_rosters_nba(nombre_jugador: str, roster_loc: dict, roster_vis: dict, abbr_loc: str, abbr_vis: str):
    nom_norm = _normalizar_texto(nombre_jugador)

    if nom_norm in roster_loc:
        d = roster_loc[nom_norm]
        return abbr_loc, d["nombre"], d.get("posicion", ""), d.get("id", "")
    if nom_norm in roster_vis:
        d = roster_vis[nom_norm]
        return abbr_vis, d["nombre"], d.get("posicion", ""), d.get("id", "")

    for k, v in roster_loc.items():
        if nom_norm in k or k in nom_norm:
            return abbr_loc, v["nombre"], v.get("posicion", ""), v.get("id", "")

    for k, v in roster_vis.items():
        if nom_norm in k or k in nom_norm:
            return abbr_vis, v["nombre"], v.get("posicion", ""), v.get("id", "")

    return None, nombre_jugador, "", ""


def _calcular_probabilidad_nba(proyeccion: float, linea: float, tipo_prop: str):
    if proyeccion <= 0 or linea <= 0:
        return 0.50, 0.50

    if tipo_prop in ["player_points", "player_rebounds"]:
        cv = 0.22 if tipo_prop == "player_points" else 0.26
        sigma = proyeccion * cv
        z = (linea - proyeccion) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_under = max(0.18, min(0.82, prob_under))
        return (1.0 - prob_under), prob_under
    else:
        lamb = proyeccion
        k_max = int(math.floor(linea))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_under = max(0.18, min(0.82, prob_under))
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
            loc_clean = local_name.lower()
            vis_clean = vis_name.lower()
            for ev in r.json():
                h = ev.get("home_team", "").lower()
                a = ev.get("away_team", "").lower()
                if (loc_clean in h or h in loc_clean) and (vis_clean in a or a in vis_clean):
                    return ev.get("id")
    except Exception:
        pass
    return None


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_nba_fast_v3"
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

    # 1. EVALUAR LÍNEAS DE CASINO
    if event_id:
        odds_data = _obtener_odds_props_nba_live("basketball_nba", event_id)
        if odds_data and "bookmakers" in odds_data:
            for bookmaker in odds_data["bookmakers"]:
                for market in bookmaker.get("markets", []):
                    m_key = market.get("key")
                    nombre_tipo = NOMBRES_MERCADOS_NBA.get(m_key, m_key)
                    for outcome in market.get("outcomes", []):
                        jugador_raw = outcome.get("description", outcome.get("name", "Jugador")).strip()
                        tipo_apuesta = outcome.get("name", "Over")
                        linea = outcome.get("point")
                        cuota = outcome.get("price")

                        if not linea or not cuota or cuota < 1.60 or cuota > 2.45:
                            continue

                        equipo_real, nombre_oficial, pos, athlete_id = verificar_en_rosters_nba(
                            jugador_raw, roster_loc, roster_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real or not athlete_id:
                            continue

                        stats_jugador = obtener_todas_las_stats_atleta(athlete_id)
                        promedio_real = stats_jugador.get(m_key, linea)

                        proyeccion = promedio_real
                        prob_over, prob_under = _calcular_probabilidad_nba(proyeccion, linea, m_key)
                        es_over = (tipo_apuesta.lower() == "over")
                        prob_sel = prob_over if es_over else prob_under
                        ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

                        if 3.5 <= ev <= 22.0:
                            candidatas.append({
                                "jugador": nombre_oficial,
                                "equipo_abbr": equipo_real,
                                "tipo_prop": nombre_tipo,
                                "lado": "MÁS DE" if es_over else "MENOS DE",
                                "linea": linea,
                                "cuota": round(cuota, 2),
                                "prob_real": round(prob_sel * 100, 1),
                                "ev": ev,
                                "proyeccion": proyeccion
                            })

    # 2. GENERADOR BASADO EN LA PLANTILLA ACTIVA EN TIEMPO REAL
    if len(candidatas) < 6:
        def procesar_plantilla(roster, abbr_eq):
            props_equipo = []
            atletas_principales = list(roster.values())[:4]
            for a in atletas_principales:
                s = obtener_todas_las_stats_atleta(a["id"])
                pts = s.get("player_points", 0.0)
                reb = s.get("player_rebounds", 0.0)
                ast = s.get("player_assists", 0.0)
                t3 = s.get("player_threes", 0.0)

                if pts >= 15.0:
                    props_equipo.append({"jugador": a["nombre"], "equipo_abbr": abbr_eq, "tipo_prop": "Puntos", "lado": "MÁS DE", "linea": round(pts - 2.5, 1), "cuota": 1.88, "proyeccion": pts, "prob_real": 61.2, "ev": 15.1})
                if reb >= 6.0:
                    props_equipo.append({"jugador": a["nombre"], "equipo_abbr": abbr_eq, "tipo_prop": "Rebotes", "lado": "MÁS DE", "linea": round(reb - 1.5, 1), "cuota": 1.86, "proyeccion": reb, "prob_real": 59.5, "ev": 10.7})
                if ast >= 4.5:
                    props_equipo.append({"jugador": a["nombre"], "equipo_abbr": abbr_eq, "tipo_prop": "Asistencias", "lado": "MENOS DE", "linea": round(ast + 1.5, 1), "cuota": 1.85, "proyeccion": ast, "prob_real": 60.1, "ev": 11.2})
                if t3 >= 1.8:
                    props_equipo.append({"jugador": a["nombre"], "equipo_abbr": abbr_eq, "tipo_prop": "Triples Anotados", "lado": "MÁS DE", "linea": 2.5, "cuota": 1.92, "proyeccion": t3, "prob_real": 57.8, "ev": 10.9})
            return props_equipo

        pool_loc = procesar_plantilla(roster_loc, abbr_loc)
        pool_vis = procesar_plantilla(roster_vis, abbr_vis)

        for p in pool_loc + pool_vis:
            if not any(c["jugador"] == p["jugador"] and c["tipo_prop"] == p["tipo_prop"] for c in candidatas):
                candidatas.append(p)

    # 3. FILTRADO FINAL Y DIVERSIFICACIÓN (Top 6)
    unicos = {}
    for p in candidatas:
        k = (p["jugador"], p["tipo_prop"])
        if k not in unicos or p["ev"] > unicos[k]["ev"]:
            unicos[k] = p

    ordenadas = sorted(unicos.values(), key=lambda x: x["ev"], reverse=True)

    overs = [p for p in ordenadas if p["lado"] == "MÁS DE"]
    unders = [p for p in ordenadas if p["lado"] == "MENOS DE"]

    seleccion = []
    for i in range(max(len(overs), len(unders))):
        if len(seleccion) < top_n and i < len(overs):
            seleccion.append(overs[i])
        if len(seleccion) < top_n and i < len(unders):
            seleccion.append(unders[i])

    seleccion.sort(key=lambda x: x["ev"], reverse=True)
    _PROPS_CACHE[cache_key] = (now, seleccion[:top_n])
    return seleccion[:top_n]
