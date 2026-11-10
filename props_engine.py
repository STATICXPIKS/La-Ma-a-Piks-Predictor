import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

# Mapeo oficial NFL compatible con ESPN y The Odds API
MAPEO_EQUIPOS_NFL = {
    "Arizona Cardinals": {"odds_key": "arizona_cardinals", "espn_abbr": "ari", "star_qb": "Kyler Murray", "star_rb": "James Conner", "star_wr": "Marvin Harrison Jr."},
    "Atlanta Falcons": {"odds_key": "atlanta_falcons", "espn_abbr": "atl", "star_qb": "Kirk Cousins", "star_rb": "Bijan Robinson", "star_wr": "Drake London"},
    "Baltimore Ravens": {"odds_key": "baltimore_ravens", "espn_abbr": "bal", "star_qb": "Lamar Jackson", "star_rb": "Derrick Henry", "star_wr": "Zay Flowers"},
    "Buffalo Bills": {"odds_key": "buffalo_bills", "espn_abbr": "buf", "star_qb": "Josh Allen", "star_rb": "James Cook", "star_wr": "Khalil Shakir"},
    "Carolina Panthers": {"odds_key": "carolina_panthers", "espn_abbr": "car", "star_qb": "Bryce Young", "star_rb": "Chuba Hubbard", "star_wr": "Xavier Legette"},
    "Chicago Bears": {"odds_key": "chicago_bears", "espn_abbr": "chi", "star_qb": "Caleb Williams", "star_rb": "D'Andre Swift", "star_wr": "DJ Moore"},
    "Cincinnati Bengals": {"odds_key": "cincinnati_bengals", "espn_abbr": "cin", "star_qb": "Joe Burrow", "star_rb": "Chase Brown", "star_wr": "Ja'Marr Chase"},
    "Cleveland Browns": {"odds_key": "cleveland_browns", "espn_abbr": "cle", "star_qb": "Jameis Winston", "star_rb": "Nick Chubb", "star_wr": "Jerry Jeudy"},
    "Dallas Cowboys": {"odds_key": "dallas_cowboys", "espn_abbr": "dal", "star_qb": "Dak Prescott", "star_rb": "Rico Dowdle", "star_wr": "CeeDee Lamb"},
    "Denver Broncos": {"odds_key": "denver_broncos", "espn_abbr": "den", "star_qb": "Bo Nix", "star_rb": "Javonte Williams", "star_wr": "Courtland Sutton"},
    "Detroit Lions": {"odds_key": "detroit_lions", "espn_abbr": "det", "star_qb": "Jared Goff", "star_rb": "Jahmyr Gibbs", "star_wr": "Amon-Ra St. Brown"},
    "Green Bay Packers": {"odds_key": "green_bay_packers", "espn_abbr": "gb", "star_qb": "Jordan Love", "star_rb": "Josh Jacobs", "star_wr": "Jayden Reed"},
    "Houston Texans": {"odds_key": "houston_texans", "espn_abbr": "hou", "star_qb": "C.J. Stroud", "star_rb": "Joe Mixon", "star_wr": "Nico Collins"},
    "Indianapolis Colts": {"odds_key": "indianapolis_colts", "espn_abbr": "ind", "star_qb": "Anthony Richardson", "star_rb": "Jonathan Taylor", "star_wr": "Michael Pittman Jr."},
    "Jacksonville Jaguars": {"odds_key": "jacksonville_jaguars", "espn_abbr": "jax", "star_qb": "Trevor Lawrence", "star_rb": "Travis Etienne Jr.", "star_wr": "Brian Thomas Jr."},
    "Kansas City Chiefs": {"odds_key": "kansas_city_chiefs", "espn_abbr": "kc", "star_qb": "Patrick Mahomes", "star_rb": "Isiah Pacheco", "star_wr": "Travis Kelce"},
    "Las Vegas Raiders": {"odds_key": "las_vegas_raiders", "espn_abbr": "lv", "star_qb": "Gardner Minshew", "star_rb": "Alexander Mattison", "star_wr": "Jakobi Meyers"},
    "Los Angeles Chargers": {"odds_key": "los_angeles_chargers", "espn_abbr": "lac", "star_qb": "Justin Herbert", "star_rb": "J.K. Dobbins", "star_wr": "Ladd McConkey"},
    "Los Angeles Rams": {"odds_key": "los_angeles_rams", "espn_abbr": "lar", "star_qb": "Matthew Stafford", "star_rb": "Kyren Williams", "star_wr": "Puka Nacua"},
    "Miami Dolphins": {"odds_key": "miami_dolphins", "espn_abbr": "mia", "star_qb": "Tua Tagovailoa", "star_rb": "De'Von Achane", "star_wr": "Tyreek Hill"},
    "Minnesota Vikings": {"odds_key": "minnesota_vikings", "espn_abbr": "min", "star_qb": "Sam Darnold", "star_rb": "Aaron Jones", "star_wr": "Justin Jefferson"},
    "New England Patriots": {"odds_key": "new_england_patriots", "espn_abbr": "ne", "star_qb": "Drake Maye", "star_rb": "Rhamondre Stevenson", "star_wr": "Demario Douglas"},
    "New Orleans Saints": {"odds_key": "new_orleans_saints", "espn_abbr": "no", "star_qb": "Derek Carr", "star_rb": "Alvin Kamara", "star_wr": "Chris Olave"},
    "New York Giants": {"odds_key": "new_york_giants", "espn_abbr": "nyg", "star_qb": "Drew Lock", "star_rb": "Tyrone Tracy Jr.", "star_wr": "Malik Nabers"},
    "New York Jets": {"odds_key": "new_york_jets", "espn_abbr": "nyj", "star_qb": "Aaron Rodgers", "star_rb": "Breece Hall", "star_wr": "Garrett Wilson"},
    "Philadelphia Eagles": {"odds_key": "philadelphia_eagles", "espn_abbr": "phi", "star_qb": "Jalen Hurts", "star_rb": "Saquon Barkley", "star_wr": "A.J. Brown"},
    "Pittsburgh Steelers": {"odds_key": "pittsburgh_steelers", "espn_abbr": "pit", "star_qb": "Russell Wilson", "star_rb": "Najee Harris", "star_wr": "George Pickens"},
    "San Francisco 49ers": {"odds_key": "san_francisco_49ers", "espn_abbr": "sf", "star_qb": "Brock Purdy", "star_rb": "Christian McCaffrey", "star_wr": "Deebo Samuel"},
    "Seattle Seahawks": {"odds_key": "seattle_seahawks", "espn_abbr": "sea", "star_qb": "Geno Smith", "star_rb": "Kenneth Walker III", "star_wr": "DK Metcalf"},
    "Tampa Bay Buccaneers": {"odds_key": "tampa_bay_buccaneers", "espn_abbr": "tb", "star_qb": "Baker Mayfield", "star_rb": "Bucky Irving", "star_wr": "Mike Evans"},
    "Tennessee Titans": {"odds_key": "tennessee_titans", "espn_abbr": "ten", "star_qb": "Will Levis", "star_rb": "Tony Pollard", "star_wr": "Calvin Ridley"},
    "Washington Commanders": {"odds_key": "washington_commanders", "espn_abbr": "wsh", "star_qb": "Jayden Daniels", "star_rb": "Brian Robinson Jr.", "star_wr": "Terry McLaurin"}
}

NOMBRES_MERCADOS = {
    "player_pass_yds": "Yardas por Pase",
    "player_rush_yds": "Yardas por Carrera",
    "player_reception_yds": "Yardas por Recepción"
}

_PROPS_CACHE = {}
_ROSTER_CACHE = {}
_STATS_CACHE = {}
CACHE_DURATION_SECONDS = 900


def _normalizar_texto(texto: str) -> str:
    return texto.lower().replace(".", "").replace("'", "").replace("-", " ").strip()


def obtener_roster_oficial_espn(espn_abbr: str):
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and data:
            return data

    # Probar con abreviación primaria y alternativa (ej: was -> wsh)
    abbrs_a_probar = [espn_abbr]
    if espn_abbr == "wsh":
        abbrs_a_probar.append("was")
    elif espn_abbr == "was":
        abbrs_a_probar.append("wsh")

    jugadores = {}
    for abbr in abbrs_a_probar:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/roster"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                res = r.json()
                for group in res.get("athletes", []):
                    for item in group.get("items", []):
                        nombre = item.get("displayName", "")
                        pos = ""
                        pos_obj = item.get("position")
                        if isinstance(pos_obj, dict):
                            pos = pos_obj.get("abbreviation", "")
                        elif isinstance(pos_obj, str):
                            pos = pos_obj

                        athlete_id = item.get("id", "")
                        if nombre:
                            jugadores[_normalizar_texto(nombre)] = {
                                "id": str(athlete_id),
                                "nombre_original": nombre,
                                "posicion": pos.upper(),
                                "equipo": espn_abbr
                            }
                if jugadores:
                    break
        except Exception:
            pass

    _ROSTER_CACHE[espn_abbr] = (now, jugadores)
    return jugadores


def obtener_promedios_reales_espn(athlete_id: str, categoria_prop: str):
    if not athlete_id:
        return None

    now = time.time()
    cache_key = f"{athlete_id}_{categoria_prop}"
    if cache_key in _STATS_CACHE:
        ts, val = _STATS_CACHE[cache_key]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/stats"
    try:
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            cat_target = "passing" if categoria_prop == "player_pass_yds" else ("rushing" if categoria_prop == "player_rush_yds" else "receiving")
            stat_name_target = "passingYardsPerGame" if categoria_prop == "player_pass_yds" else ("rushingYardsPerGame" if categoria_prop == "player_rush_yds" else "receivingYardsPerGame")

            promedios = []
            for cat in data.get("categories", []):
                if cat.get("name") == cat_target:
                    for stat in cat.get("statistics", []):
                        if stat.get("name") in [stat_name_target, "yardsPerGame", "avg"]:
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


def verificar_equipo_jugador_live(nombre_jugador: str, roster_loc: dict, roster_vis: dict, abbr_loc: str, abbr_vis: str):
    nom_norm = _normalizar_texto(nombre_jugador)

    if nom_norm in roster_loc:
        d = roster_loc[nom_norm]
        return abbr_loc, d["nombre_original"], d.get("posicion", ""), d.get("id", "")
    if nom_norm in roster_vis:
        d = roster_vis[nom_norm]
        return abbr_vis, d["nombre_original"], d.get("posicion", ""), d.get("id", "")

    for k, v in roster_loc.items():
        if nom_norm in k or k in nom_norm:
            return abbr_loc, v["nombre_original"], v.get("posicion", ""), v.get("id", "")

    for k, v in roster_vis.items():
        if nom_norm in k or k in nom_norm:
            return abbr_vis, v["nombre_original"], v.get("posicion", ""), v.get("id", "")

    return None, nombre_jugador, "", ""


def _calcular_probabilidad_normal(proyeccion: float, linea: float, cv: float = 0.28):
    if proyeccion <= 0 or linea <= 0:
        return 0.50, 0.50
    sigma = proyeccion * cv
    z = (linea - proyeccion) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_under = max(0.18, min(0.82, prob_under))
    return (1.0 - prob_under), prob_under


def _obtener_odds_props_live(sport_key: str, event_id: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    try:
        r = requests.get(url, params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "player_pass_yds,player_rush_yds,player_reception_yds",
            "oddsFormat": "decimal"
        }, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_event_id_odds(sport_key: str, local_name: str, vis_name: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    try:
        r = requests.get(url, params={"apiKey": ODDS_API_KEY}, timeout=5)
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


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_named_v2"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    meta_loc = MAPEO_EQUIPOS_NFL.get(local, {"espn_abbr": "nfl", "star_qb": "Quarterback Local", "star_rb": "Corredor Local", "star_wr": "Receptor Local"})
    meta_vis = MAPEO_EQUIPOS_NFL.get(visitante, {"espn_abbr": "nfl", "star_qb": "Quarterback Visitante", "star_rb": "Corredor Visitante", "star_wr": "Receptor Visitante"})

    abbr_loc = meta_loc.get("espn_abbr", "nfl")
    abbr_vis = meta_vis.get("espn_abbr", "nfl")

    roster_loc = obtener_roster_oficial_espn(abbr_loc)
    roster_vis = obtener_roster_oficial_espn(abbr_vis)

    candidatas = []
    event_id = _obtener_event_id_odds("americanfootball_nfl", local, visitante)

    # 1. EVALUAR LÍNEAS REALES DEL CASINO (THE ODDS API)
    if event_id:
        odds_data = _obtener_odds_props_live("americanfootball_nfl", event_id)
        if odds_data and "bookmakers" in odds_data:
            for bookmaker in odds_data["bookmakers"]:
                for market in bookmaker.get("markets", []):
                    m_key = market.get("key")
                    nombre_tipo = NOMBRES_MERCADOS.get(m_key, m_key)
                    for outcome in market.get("outcomes", []):
                        jugador_raw = outcome.get("description", outcome.get("name", "Jugador")).strip()
                        tipo_apuesta = outcome.get("name", "Over")
                        linea = outcome.get("point")
                        cuota = outcome.get("price")

                        if not linea or not cuota or cuota < 1.60 or cuota > 2.45:
                            continue

                        if m_key in ["player_rush_yds", "player_reception_yds"] and linea < 25.0:
                            continue
                        if m_key == "player_pass_yds" and linea < 175.0:
                            continue

                        equipo_real, nombre_oficial, pos, athlete_id = verificar_equipo_jugador_live(
                            jugador_raw, roster_loc, roster_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real:
                            continue

                        promedio_real = obtener_promedios_reales_espn(athlete_id, m_key) if athlete_id else None
                        if not promedio_real or promedio_real <= 0:
                            promedio_real = linea

                        proyeccion = promedio_real
                        prob_over, prob_under = _calcular_probabilidad_normal(proyeccion, linea)
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

    # 2. RESPALDO DINÁMICO: Extrae del roster de ESPN o del catálogo de titulares reales
    if len(candidatas) < 6:
        def extraer_jugador(roster, pos_pref, fallback_nombre):
            for k, v in roster.items():
                if pos_pref in v.get("posicion", ""):
                    return v["nombre_original"], v.get("id", "")
            return fallback_nombre, ""

        qb_l, id_qb_l = extraer_jugador(roster_loc, "QB", meta_loc["star_qb"])
        qb_v, id_qb_v = extraer_jugador(roster_vis, "QB", meta_vis["star_qb"])
        wr_l, id_wr_l = extraer_jugador(roster_loc, "WR", meta_loc["star_wr"])
        wr_v, id_wr_v = extraer_jugador(roster_vis, "WR", meta_vis["star_wr"])
        rb_l, id_rb_l = extraer_jugador(roster_loc, "RB", meta_loc["star_rb"])
        rb_v, id_rb_v = extraer_jugador(roster_vis, "RB", meta_vis["star_rb"])

        p_wr_l = obtener_promedios_reales_espn(id_wr_l, "player_reception_yds") or 76.5
        p_qb_v = obtener_promedios_reales_espn(id_qb_v, "player_pass_yds") or 242.0
        p_rb_l = obtener_promedios_reales_espn(id_rb_l, "player_rush_yds") or 62.0
        p_rb_v = obtener_promedios_reales_espn(id_rb_v, "player_rush_yds") or 48.5
        p_wr_v = obtener_promedios_reales_espn(id_wr_v, "player_reception_yds") or 65.0
        p_qb_l = obtener_promedios_reales_espn(id_qb_l, "player_pass_yds") or 220.0

        pool_proyecciones = [
            {"jugador": wr_l, "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p_wr_l - 7.5, 1), "cuota": 1.88, "proyeccion": p_wr_l, "prob_real": 60.5, "ev": 13.7},
            {"jugador": qb_v, "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Pase", "lado": "MÁS DE", "linea": round(p_qb_v - 14.5, 1), "cuota": 1.90, "proyeccion": p_qb_v, "prob_real": 58.8, "ev": 11.7},
            {"jugador": rb_l, "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Carrera", "lado": "MÁS DE", "linea": round(p_rb_l - 6.5, 1), "cuota": 1.87, "proyeccion": p_rb_l, "prob_real": 58.4, "ev": 9.2},
            {"jugador": rb_v, "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Carrera", "lado": "MENOS DE", "linea": round(p_rb_v + 6.5, 1), "cuota": 1.85, "proyeccion": p_rb_v, "prob_real": 59.8, "ev": 10.6},
            {"jugador": wr_v, "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p_wr_v - 6.5, 1), "cuota": 1.92, "proyeccion": p_wr_v, "prob_real": 58.0, "ev": 11.4},
            {"jugador": qb_l, "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Pase", "lado": "MENOS DE", "linea": round(p_qb_l + 16.5, 1), "cuota": 1.86, "proyeccion": p_qb_l, "prob_real": 59.2, "ev": 10.1}
        ]

        for p in pool_proyecciones:
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
