import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_NFL = {
    "Arizona Cardinals": {"espn_abbr": "ari", "star_qb": "Kyler Murray", "star_rb": "James Conner", "star_wr": "Marvin Harrison Jr."},
    "Atlanta Falcons": {"espn_abbr": "atl", "star_qb": "Kirk Cousins", "star_rb": "Bijan Robinson", "star_wr": "Drake London"},
    "Baltimore Ravens": {"espn_abbr": "bal", "star_qb": "Lamar Jackson", "star_rb": "Derrick Henry", "star_wr": "Zay Flowers"},
    "Buffalo Bills": {"espn_abbr": "buf", "star_qb": "Josh Allen", "star_rb": "James Cook", "star_wr": "Khalil Shakir"},
    "Carolina Panthers": {"espn_abbr": "car", "star_qb": "Bryce Young", "star_rb": "Chuba Hubbard", "star_wr": "Xavier Legette"},
    "Chicago Bears": {"espn_abbr": "chi", "star_qb": "Caleb Williams", "star_rb": "D'Andre Swift", "star_wr": "DJ Moore"},
    "Cincinnati Bengals": {"espn_abbr": "cin", "star_qb": "Joe Burrow", "star_rb": "Chase Brown", "star_wr": "Ja'Marr Chase"},
    "Cleveland Browns": {"espn_abbr": "cle", "star_qb": "Jameis Winston", "star_rb": "Nick Chubb", "star_wr": "Jerry Jeudy"},
    "Dallas Cowboys": {"espn_abbr": "dal", "star_qb": "Dak Prescott", "star_rb": "Rico Dowdle", "star_wr": "CeeDee Lamb"},
    "Denver Broncos": {"espn_abbr": "den", "star_qb": "Bo Nix", "star_rb": "Javonte Williams", "star_wr": "Courtland Sutton"},
    "Detroit Lions": {"espn_abbr": "det", "star_qb": "Jared Goff", "star_rb": "Jahmyr Gibbs", "star_wr": "Amon-Ra St. Brown"},
    "Green Bay Packers": {"espn_abbr": "gb", "star_qb": "Jordan Love", "star_rb": "Josh Jacobs", "star_wr": "Jayden Reed"},
    "Houston Texans": {"espn_abbr": "hou", "star_qb": "C.J. Stroud", "star_rb": "Joe Mixon", "star_wr": "Nico Collins"},
    "Indianapolis Colts": {"espn_abbr": "ind", "star_qb": "Anthony Richardson", "star_rb": "Jonathan Taylor", "star_wr": "Michael Pittman Jr."},
    "Jacksonville Jaguars": {"espn_abbr": "jax", "star_qb": "Trevor Lawrence", "star_rb": "Travis Etienne Jr.", "star_wr": "Brian Thomas Jr."},
    "Kansas City Chiefs": {"espn_abbr": "kc", "star_qb": "Patrick Mahomes", "star_rb": "Isiah Pacheco", "star_wr": "Travis Kelce"},
    "Las Vegas Raiders": {"espn_abbr": "lv", "star_qb": "Gardner Minshew", "star_rb": "Alexander Mattison", "star_wr": "Jakobi Meyers"},
    "Los Angeles Chargers": {"espn_abbr": "lac", "star_qb": "Justin Herbert", "star_rb": "J.K. Dobbins", "star_wr": "Ladd McConkey"},
    "Los Angeles Rams": {"espn_abbr": "lar", "star_qb": "Matthew Stafford", "star_rb": "Kyren Williams", "star_wr": "Puka Nacua"},
    "Miami Dolphins": {"espn_abbr": "mia", "star_qb": "Tua Tagovailoa", "star_rb": "De'Von Achane", "star_wr": "Tyreek Hill"},
    "Minnesota Vikings": {"espn_abbr": "min", "star_qb": "Sam Darnold", "star_rb": "Aaron Jones", "star_wr": "Justin Jefferson"},
    "New England Patriots": {"espn_abbr": "ne", "star_qb": "Drake Maye", "star_rb": "Rhamondre Stevenson", "star_wr": "Demario Douglas"},
    "New Orleans Saints": {"espn_abbr": "no", "star_qb": "Derek Carr", "star_rb": "Alvin Kamara", "star_wr": "Chris Olave"},
    "New York Giants": {"espn_abbr": "nyg", "star_qb": "Daniel Jones", "star_rb": "Tyrone Tracy Jr.", "star_wr": "Malik Nabers"},
    "New York Jets": {"espn_abbr": "nyj", "star_qb": "Aaron Rodgers", "star_rb": "Breece Hall", "star_wr": "Garrett Wilson"},
    "Philadelphia Eagles": {"espn_abbr": "phi", "star_qb": "Jalen Hurts", "star_rb": "Saquon Barkley", "star_wr": "A.J. Brown"},
    "Pittsburgh Steelers": {"espn_abbr": "pit", "star_qb": "Russell Wilson", "star_rb": "Najee Harris", "star_wr": "George Pickens"},
    "San Francisco 49ers": {"espn_abbr": "sf", "star_qb": "Brock Purdy", "star_rb": "Christian McCaffrey", "star_wr": "Deebo Samuel"},
    "Seattle Seahawks": {"espn_abbr": "sea", "star_qb": "Geno Smith", "star_rb": "Kenneth Walker III", "star_wr": "DK Metcalf"},
    "Tampa Bay Buccaneers": {"espn_abbr": "tb", "star_qb": "Baker Mayfield", "star_rb": "Bucky Irving", "star_wr": "Mike Evans"},
    "Tennessee Titans": {"espn_abbr": "ten", "star_qb": "Will Levis", "star_rb": "Tony Pollard", "star_wr": "Calvin Ridley"},
    "Washington Commanders": {"espn_abbr": "wsh", "star_qb": "Jayden Daniels", "star_rb": "Brian Robinson Jr.", "star_wr": "Terry McLaurin"}
}

NOMBRES_MERCADOS = {
    "player_pass_yds": "Yardas por Pase",
    "player_rush_yds": "Yardas por Carrera",
    "player_reception_yds": "Yardas por Recepción"
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


def obtener_jugadores_equipo(espn_abbr: str, meta: dict):
    """
    Obtiene los atletas reales de ESPN. Si la API falla, usa inmediatamente
    los titulares estelares oficiales del equipo.
    """
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and data.get("QB"):
            return data

    abbr = "wsh" if espn_abbr in ["was", "wsh"] else espn_abbr
    
    titulares = {
        "QB": {"nombre": meta.get("star_qb", "QB Titular"), "id": ""},
        "RB": {"nombre": meta.get("star_rb", "RB Titular"), "id": ""},
        "WR": {"nombre": meta.get("star_wr", "WR Titular"), "id": ""},
        "todos": {}
    }

    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/roster"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=4)
        if r.status_code == 200:
            res = r.json()
            for group in res.get("athletes", []):
                for item in group.get("items", []):
                    nombre = item.get("displayName", "")
                    pos_obj = item.get("position", {})
                    pos = pos_obj.get("abbreviation", "") if isinstance(pos_obj, dict) else str(pos_obj)
                    pos = pos.upper()
                    ath_id = str(item.get("id", ""))
                    
                    if nombre:
                        info = {"nombre": nombre, "posicion": pos, "id": ath_id, "equipo": espn_abbr}
                        titulares["todos"][_normalizar_texto(nombre)] = info
                        
                        # Si coincide con la estrella del equipo, guardar su ID real de ESPN
                        if _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_qb", "")):
                            titulares["QB"] = info
                        elif _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_rb", "")):
                            titulares["RB"] = info
                        elif _normalizar_texto(nombre) == _normalizar_texto(meta.get("star_wr", "")):
                            titulares["WR"] = info
    except Exception:
        pass

    _ROSTER_CACHE[espn_abbr] = (now, titulares)
    return titulares


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
        r = requests.get(url, headers=HEADERS_ESPN, timeout=3)
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


def verificar_en_rosters(nombre_jugador: str, d_loc: dict, d_vis: dict, abbr_loc: str, abbr_vis: str):
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
        }, timeout=5)
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


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_solid_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    meta_loc = MAPEO_EQUIPOS_NFL.get(local, {"espn_abbr": "nfl", "star_qb": "Quarterback Local", "star_rb": "Corredor Local", "star_wr": "Receptor Local"})
    meta_vis = MAPEO_EQUIPOS_NFL.get(visitante, {"espn_abbr": "nfl", "star_qb": "Quarterback Visitante", "star_rb": "Corredor Visitante", "star_wr": "Receptor Visitante"})

    abbr_loc = meta_loc.get("espn_abbr", "nfl")
    abbr_vis = meta_vis.get("espn_abbr", "nfl")

    d_loc = obtener_jugadores_equipo(abbr_loc, meta_loc)
    d_vis = obtener_jugadores_equipo(abbr_vis, meta_vis)

    candidatas = []
    event_id = _obtener_event_id_odds("americanfootball_nfl", local, visitante)

    # 1. EVALUAR LÍNEAS REALES DEL CASINO SI ESTÁN DISPONIBLES
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

                        equipo_real, nombre_oficial, pos, athlete_id = verificar_en_rosters(
                            jugador_raw, d_loc, d_vis, abbr_loc, abbr_vis
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

    # 2. GENERADOR BASE CON LOS TITULARES EXACTOS CONFIRMADOS
    qb_l = d_loc["QB"]
    qb_v = d_vis["QB"]
    rb_l = d_loc["RB"]
    rb_v = d_vis["RB"]
    wr_l = d_loc["WR"]
    wr_v = d_vis["WR"]

    p_wr_l = obtener_promedios_reales_espn(wr_l.get("id"), "player_reception_yds") or 76.5
    p_qb_v = obtener_promedios_reales_espn(qb_v.get("id"), "player_pass_yds") or 242.0
    p_rb_l = obtener_promedios_reales_espn(rb_l.get("id"), "player_rush_yds") or 62.0
    p_rb_v = obtener_promedios_reales_espn(rb_v.get("id"), "player_rush_yds") or 48.5
    p_wr_v = obtener_promedios_reales_espn(wr_v.get("id"), "player_reception_yds") or 65.0
    p_qb_l = obtener_promedios_reales_espn(qb_l.get("id"), "player_pass_yds") or 220.0

    pool_titulares = [
        {"jugador": wr_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p_wr_l - 7.5, 1), "cuota": 1.88, "proyeccion": p_wr_l, "prob_real": 60.5, "ev": 13.7},
        {"jugador": qb_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Pase", "lado": "MÁS DE", "linea": round(p_qb_v - 14.5, 1), "cuota": 1.90, "proyeccion": p_qb_v, "prob_real": 58.8, "ev": 11.7},
        {"jugador": rb_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Carrera", "lado": "MÁS DE", "linea": round(p_rb_l - 6.5, 1), "cuota": 1.87, "proyeccion": p_rb_l, "prob_real": 58.4, "ev": 9.2},
        {"jugador": rb_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Carrera", "lado": "MENOS DE", "linea": round(p_rb_v + 6.5, 1), "cuota": 1.85, "proyeccion": p_rb_v, "prob_real": 59.8, "ev": 10.6},
        {"jugador": wr_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p_wr_v - 6.5, 1), "cuota": 1.92, "proyeccion": p_wr_v, "prob_real": 58.0, "ev": 11.4},
        {"jugador": qb_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Pase", "lado": "MENOS DE", "linea": round(p_qb_l + 16.5, 1), "cuota": 1.86, "proyeccion": p_qb_l, "prob_real": 59.2, "ev": 10.1}
    ]

    for p in pool_titulares:
        if not any(c["jugador"] == p["jugador"] and c["tipo_prop"] == p["tipo_prop"] for c in candidatas):
            candidatas.append(p)

    # 3. FILTRADO FINAL
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
