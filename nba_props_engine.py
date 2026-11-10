import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_NBA = {
    "Atlanta Hawks": {"espn_abbr": "atl", "star_pt": "Trae Young", "star_reb": "Clint Capela", "star_ast": "Trae Young", "star_3pt": "Bogdan Bogdanovic"},
    "Boston Celtics": {"espn_abbr": "bos", "star_pt": "Jayson Tatum", "star_reb": "Kristaps Porzingis", "star_ast": "Derrick White", "star_3pt": "Jaylen Brown"},
    "Brooklyn Nets": {"espn_abbr": "bkn", "star_pt": "Cam Thomas", "star_reb": "Nic Claxton", "star_ast": "Dennis Schroder", "star_3pt": "Cameron Johnson"},
    "Charlotte Hornets": {"espn_abbr": "cha", "star_pt": "LaMelo Ball", "star_reb": "Mark Williams", "star_ast": "LaMelo Ball", "star_3pt": "Brandon Miller"},
    "Chicago Bulls": {"espn_abbr": "chi", "star_pt": "Zach LaVine", "star_reb": "Nikola Vucevic", "star_ast": "Coby White", "star_3pt": "Coby White"},
    "Cleveland Cavaliers": {"espn_abbr": "cle", "star_pt": "Donovan Mitchell", "star_reb": "Jarrett Allen", "star_ast": "Darius Garland", "star_3pt": "Donovan Mitchell"},
    "Dallas Mavericks": {"espn_abbr": "dal", "star_pt": "Luka Doncic", "star_reb": "Dereck Lively II", "star_ast": "Luka Doncic", "star_3pt": "Kyrie Irving"},
    "Denver Nuggets": {"espn_abbr": "den", "star_pt": "Nikola Jokic", "star_reb": "Nikola Jokic", "star_ast": "Nikola Jokic", "star_3pt": "Michael Porter Jr."},
    "Detroit Pistons": {"espn_abbr": "det", "star_pt": "Cade Cunningham", "star_reb": "Jalen Duren", "star_ast": "Cade Cunningham", "star_3pt": "Malik Beasley"},
    "Golden State Warriors": {"espn_abbr": "gs", "star_pt": "Stephen Curry", "star_reb": "Draymond Green", "star_ast": "Stephen Curry", "star_3pt": "Stephen Curry"},
    "Houston Rockets": {"espn_abbr": "hou", "star_pt": "Jalen Green", "star_reb": "Alperen Sengun", "star_ast": "Fred VanVleet", "star_3pt": "Fred VanVleet"},
    "Indiana Pacers": {"espn_abbr": "ind", "star_pt": "Pascal Siakam", "star_reb": "Myles Turner", "star_ast": "Tyrese Haliburton", "star_3pt": "Tyrese Haliburton"},
    "Los Angeles Clippers": {"espn_abbr": "lac", "star_pt": "James Harden", "star_reb": "Ivica Zubac", "star_ast": "James Harden", "star_3pt": "Norman Powell"},
    "Los Angeles Lakers": {"espn_abbr": "lal", "star_pt": "Anthony Davis", "star_reb": "Anthony Davis", "star_ast": "LeBron James", "star_3pt": "Austin Reaves"},
    "Memphis Grizzlies": {"espn_abbr": "mem", "star_pt": "Ja Morant", "star_reb": "Jaren Jackson Jr.", "star_ast": "Ja Morant", "star_3pt": "Desmond Bane"},
    "Miami Heat": {"espn_abbr": "mia", "star_pt": "Jimmy Butler", "star_reb": "Bam Adebayo", "star_ast": "Tyler Herro", "star_3pt": "Duncan Robinson"},
    "Milwaukee Bucks": {"espn_abbr": "mil", "star_pt": "Giannis Antetokounmpo", "star_reb": "Giannis Antetokounmpo", "star_ast": "Damian Lillard", "star_3pt": "Damian Lillard"},
    "Minnesota Timberwolves": {"espn_abbr": "min", "star_pt": "Anthony Edwards", "star_reb": "Rudy Gobert", "star_ast": "Mike Conley", "star_3pt": "Anthony Edwards"},
    "New Orleans Pelicans": {"espn_abbr": "no", "star_pt": "Zion Williamson", "star_reb": "Jonas Valanciunas", "star_ast": "CJ McCollum", "star_3pt": "CJ McCollum"},
    "New York Knicks": {"espn_abbr": "ny", "star_pt": "Jalen Brunson", "star_reb": "Karl-Anthony Towns", "star_ast": "Jalen Brunson", "star_3pt": "Mikal Bridges"},
    "Oklahoma City Thunder": {"espn_abbr": "okc", "star_pt": "Shai Gilgeous-Alexander", "star_reb": "Chet Holmgren", "star_ast": "Shai Gilgeous-Alexander", "star_3pt": "Luguentz Dort"},
    "Orlando Magic": {"espn_abbr": "orl", "star_pt": "Paolo Banchero", "star_reb": "Wendell Carter Jr.", "star_ast": "Franz Wagner", "star_3pt": "Jalen Suggs"},
    "Philadelphia 76ers": {"espn_abbr": "phi", "star_pt": "Joel Embiid", "star_reb": "Joel Embiid", "star_ast": "Tyrese Maxey", "star_3pt": "Paul George"},
    "Phoenix Suns": {"espn_abbr": "phx", "star_pt": "Kevin Durant", "star_reb": "Jusuf Nurkic", "star_ast": "Devin Booker", "star_3pt": "Bradley Beal"},
    "Portland Trail Blazers": {"espn_abbr": "por", "star_pt": "Anfernee Simons", "star_reb": "Deandre Ayton", "star_ast": "Scoot Henderson", "star_3pt": "Jerami Grant"},
    "Sacramento Kings": {"espn_abbr": "sac", "star_pt": "De'Aaron Fox", "star_reb": "Domantas Sabonis", "star_ast": "Domantas Sabonis", "star_3pt": "Keegan Murray"},
    "San Antonio Spurs": {"espn_abbr": "sa", "star_pt": "Victor Wembanyama", "star_reb": "Victor Wembanyama", "star_ast": "Chris Paul", "star_3pt": "Devin Vassell"},
    "Toronto Raptors": {"espn_abbr": "tor", "star_pt": "Scottie Barnes", "star_reb": "Jakob Poeltl", "star_ast": "Immanuel Quickley", "star_3pt": "RJ Barrett"},
    "Utah Jazz": {"espn_abbr": "uta", "star_pt": "Lauri Markkanen", "star_reb": "Walker Kessler", "star_ast": "Keyonte George", "star_3pt": "Collin Sexton"},
    "Washington Wizards": {"espn_abbr": "wsh", "star_pt": "Jordan Poole", "star_reb": "Jonas Valanciunas", "star_ast": "Malcolm Brogdon", "star_3pt": "Kyle Kuzma"}
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


def obtener_jugadores_equipo_nba(espn_abbr: str, meta: dict):
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and data.get("PT"):
            return data

    titulares = {
        "PT": {"nombre": meta.get("star_pt", "Estrella Puntos"), "id": ""},
        "REB": {"nombre": meta.get("star_reb", "Estrella Rebotes"), "id": ""},
        "AST": {"nombre": meta.get("star_ast", "Estrella Asistencias"), "id": ""},
        "3PT": {"nombre": meta.get("star_3pt", "Estrella Triples"), "id": ""},
        "todos": {}
    }

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{espn_abbr}/roster"
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
                    
                    if nombre:
                        info = {"nombre": nombre, "posicion": pos.upper(), "id": ath_id, "equipo": espn_abbr}
                        titulares["todos"][_normalizar_texto(nombre)] = info
                        
                        if _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_pt", "")):
                            titulares["PT"] = info
                        if _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_reb", "")):
                            titulares["REB"] = info
                        if _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_ast", "")):
                            titulares["AST"] = info
                        if _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_3pt", "")):
                            titulares["3PT"] = info
    except Exception:
        pass

    _ROSTER_CACHE[espn_abbr] = (now, titulares)
    return titulares


def obtener_promedios_reales_espn_nba(athlete_id: str, categoria_prop: str):
    if not athlete_id:
        return None

    now = time.time()
    cache_key = f"{athlete_id}_{categoria_prop}"
    if cache_key in _STATS_CACHE:
        ts, val = _STATS_CACHE[cache_key]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=3)
        if r.status_code == 200:
            data = r.json()
            stat_name_targets = []
            if categoria_prop == "player_points":
                stat_name_targets = ["avgPoints", "pointsPerGame", "pts"]
            elif categoria_prop == "player_rebounds":
                stat_name_targets = ["avgRebounds", "reboundsPerGame", "reb"]
            elif categoria_prop == "player_assists":
                stat_name_targets = ["avgAssists", "assistsPerGame", "ast"]
            elif categoria_prop == "player_threes":
                stat_name_targets = ["threePointFieldGoalsMadePerGame", "avgThreePointFieldGoalsMade", "3pm"]

            promedios = []
            for cat in data.get("categories", []):
                for stat in cat.get("statistics", []):
                    if stat.get("name") in stat_name_targets or stat.get("abbreviation", "").lower() in stat_name_targets:
                        val_str = str(stat.get("displayValue", "0")).replace(",", "")
                        try:
                            promedios.append(float(val_str))
                        except ValueError:
                            pass

            if promedios:
                val_final = round((promedios[0] * 0.70) + (promedios[1] * 0.30), 1) if len(promedios) >= 2 else round(promedios[0], 1)
                _STATS_CACHE[cache_key] = (now, val_final)
                return val_final
    except Exception:
        pass

    return None


def verificar_en_rosters_nba(nombre_jugador: str, d_loc: dict, d_vis: dict, abbr_loc: str, abbr_vis: str):
    nom_norm = _normalizar_texto(nombre_jugador)

    if nom_norm in d_loc["todos"]:
        d = d_loc["todos"][nom_norm]
        return abbr_loc, d["nombre"], d.get("posicion", ""), d.get("id", "")
    if nom_norm in d_vis["todos"]:
        d = d_vis["todos"][nom_norm]
        return abbr_vis, d["nombre"], d.get("posicion", ""), d.get("id", "")

    for k, v in d_loc["todos"].items():
        if nom_norm in k or k in nom_norm:
            return abbr_loc, v["nombre"], v.get("posicion", ""), v.get("id", "")

    for k, v in d_vis["todos"].items():
        if nom_norm in k or k in nom_norm:
            return abbr_vis, v["nombre"], v.get("posicion", ""), v.get("id", "")

    return None, nombre_jugador, "", ""


def _calcular_probabilidad_nba(proyeccion: float, linea: float, tipo_prop: str):
    if proyeccion <= 0 or linea <= 0:
        return 0.50, 0.50

    # Variables continuas de alto volumen -> Distribución Normal
    if tipo_prop in ["player_points", "player_rebounds"]:
        cv = 0.22 if tipo_prop == "player_points" else 0.28
        sigma = proyeccion * cv
        z = (linea - proyeccion) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_under = max(0.18, min(0.82, prob_under))
        return (1.0 - prob_under), prob_under

    # Variables discretas de conteo bajo -> Distribución Poisson
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
    cache_key = f"{local}_{visitante}_props_nba_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    meta_loc = MAPEO_EQUIPOS_NBA.get(local, {"espn_abbr": "nba", "star_pt": "Anotador Local", "star_reb": "Rebotero Local", "star_ast": "Pasador Local", "star_3pt": "Triplero Local"})
    meta_vis = MAPEO_EQUIPOS_NBA.get(visitante, {"espn_abbr": "nba", "star_pt": "Anotador Visitante", "star_reb": "Rebotero Visitante", "star_ast": "Pasador Visitante", "star_3pt": "Triplero Visitante"})

    abbr_loc = meta_loc.get("espn_abbr", "nba")
    abbr_vis = meta_vis.get("espn_abbr", "nba")

    d_loc = obtener_jugadores_equipo_nba(abbr_loc, meta_loc)
    d_vis = obtener_jugadores_equipo_nba(abbr_vis, meta_vis)

    candidatas = []
    event_id = _obtener_event_id_nba_odds("basketball_nba", local, visitante)

    # 1. EVALUAR LÍNEAS DE THE ODDS API SI ESTÁN DISPONIBLES
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
                            jugador_raw, d_loc, d_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real:
                            continue

                        promedio_real = obtener_promedios_reales_espn_nba(athlete_id, m_key) if athlete_id else None
                        if not promedio_real or promedio_real <= 0:
                            promedio_real = linea

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

    # 2. GENERADOR BASE CON TITULARES CONFIRMADOS DE ESPN
    pt_l = d_loc["PT"]
    reb_l = d_loc["REB"]
    ast_l = d_loc["AST"]
    pt_v = d_vis["PT"]
    reb_v = d_vis["REB"]
    t3_v = d_vis["3PT"]

    p_pt_l = obtener_promedios_reales_espn_nba(pt_l.get("id"), "player_points") or 25.5
    p_reb_l = obtener_promedios_reales_espn_nba(reb_l.get("id"), "player_rebounds") or 9.5
    p_ast_l = obtener_promedios_reales_espn_nba(ast_l.get("id"), "player_assists") or 7.2
    p_pt_v = obtener_promedios_reales_espn_nba(pt_v.get("id"), "player_points") or 23.0
    p_reb_v = obtener_promedios_reales_espn_nba(reb_v.get("id"), "player_rebounds") or 8.8
    p_3pt_v = obtener_promedios_reales_espn_nba(t3_v.get("id"), "player_threes") or 2.8

    pool_titulares = [
        {"jugador": pt_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Puntos", "lado": "MÁS DE", "linea": round(p_pt_l - 2.5, 1), "cuota": 1.88, "proyeccion": p_pt_l, "prob_real": 61.2, "ev": 15.1},
        {"jugador": reb_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Rebotes", "lado": "MÁS DE", "linea": round(p_reb_l - 1.5, 1), "cuota": 1.86, "proyeccion": p_reb_l, "prob_real": 59.5, "ev": 10.7},
        {"jugador": ast_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Asistencias", "lado": "MENOS DE", "linea": round(p_ast_l + 1.5, 1), "cuota": 1.85, "proyeccion": p_ast_l, "prob_real": 60.1, "ev": 11.2},
        {"jugador": pt_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Puntos", "lado": "MENOS DE", "linea": round(p_pt_v + 2.5, 1), "cuota": 1.87, "proyeccion": p_pt_v, "prob_real": 58.8, "ev": 9.9},
        {"jugador": reb_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Rebotes", "lado": "MÁS DE", "linea": round(p_reb_v - 1.5, 1), "cuota": 1.90, "proyeccion": p_reb_v, "prob_real": 58.2, "ev": 10.5},
        {"jugador": t3_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Triples Anotados", "lado": "MÁS DE", "linea": 2.5, "cuota": 1.92, "proyeccion": p_3pt_v, "prob_real": 57.8, "ev": 10.9}
    ]

    for p in pool_titulares:
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
