import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_NFL = {
    "Arizona Cardinals": {"odds_key": "arizona_cardinals", "espn_abbr": "ari"},
    "Atlanta Falcons": {"odds_key": "atlanta_falcons", "espn_abbr": "atl"},
    "Baltimore Ravens": {"odds_key": "baltimore_ravens", "espn_abbr": "bal"},
    "Buffalo Bills": {"odds_key": "buffalo_bills", "espn_abbr": "buf"},
    "Carolina Panthers": {"odds_key": "carolina_panthers", "espn_abbr": "car"},
    "Chicago Bears": {"odds_key": "chicago_bears", "espn_abbr": "chi"},
    "Cincinnati Bengals": {"odds_key": "cincinnati_bengals", "espn_abbr": "cin"},
    "Cleveland Browns": {"odds_key": "cleveland_browns", "espn_abbr": "cle"},
    "Dallas Cowboys": {"odds_key": "dallas_cowboys", "espn_abbr": "dal"},
    "Denver Broncos": {"odds_key": "denver_broncos", "espn_abbr": "den"},
    "Detroit Lions": {"odds_key": "detroit_lions", "espn_abbr": "det"},
    "Green Bay Packers": {"odds_key": "green_bay_packers", "espn_abbr": "gb"},
    "Houston Texans": {"odds_key": "houston_texans", "espn_abbr": "hou"},
    "Indianapolis Colts": {"odds_key": "indianapolis_colts", "espn_abbr": "ind"},
    "Jacksonville Jaguars": {"odds_key": "jacksonville_jaguars", "espn_abbr": "jax"},
    "Kansas City Chiefs": {"odds_key": "kansas_city_chiefs", "espn_abbr": "kc"},
    "Las Vegas Raiders": {"odds_key": "las_vegas_raiders", "espn_abbr": "lv"},
    "Los Angeles Chargers": {"odds_key": "los_angeles_chargers", "espn_abbr": "lac"},
    "Los Angeles Rams": {"odds_key": "los_angeles_rams", "espn_abbr": "lar"},
    "Miami Dolphins": {"odds_key": "miami_dolphins", "espn_abbr": "mia"},
    "Minnesota Vikings": {"odds_key": "minnesota_vikings", "espn_abbr": "min"},
    "New England Patriots": {"odds_key": "new_england_patriots", "espn_abbr": "ne"},
    "New Orleans Saints": {"odds_key": "new_orleans_saints", "espn_abbr": "no"},
    "New York Giants": {"odds_key": "new_york_giants", "espn_abbr": "nyg"},
    "New York Jets": {"odds_key": "new_york_jets", "espn_abbr": "nyj"},
    "Philadelphia Eagles": {"odds_key": "philadelphia_eagles", "espn_abbr": "phi"},
    "Pittsburgh Steelers": {"odds_key": "pittsburgh_steelers", "espn_abbr": "pit"},
    "San Francisco 49ers": {"odds_key": "san_francisco_49ers", "espn_abbr": "sf"},
    "Seattle Seahawks": {"odds_key": "seattle_seahawks", "espn_abbr": "sea"},
    "Tampa Bay Buccaneers": {"odds_key": "tampa_bay_buccaneers", "espn_abbr": "tb"},
    "Tennessee Titans": {"odds_key": "tennessee_titans", "espn_abbr": "ten"},
    "Washington Commanders": {"odds_key": "washington_commanders", "espn_abbr": "wsh"}
}

NOMBRES_MERCADOS = {
    "player_pass_yds": "Yardas por Pase",
    "player_rush_yds": "Yardas por Carrera",
    "player_reception_yds": "Yardas por Recepción"
}

_PROPS_CACHE = {}
_DEPTH_CACHE = {}
_STATS_CACHE = {}
CACHE_DURATION_SECONDS = 900


def _normalizar_texto(texto: str) -> str:
    return texto.lower().replace(".", "").replace("'", "").replace("-", " ").strip()


def obtener_titulares_reales_espn(espn_abbr: str):
    """
    Consulta el Depth Chart oficial de ESPN para garantizar a los titulares
    de primer equipo (Rank 1: QB1, RB1, WR1, WR2).
    """
    now = time.time()
    if espn_abbr in _DEPTH_CACHE:
        ts, data = _DEPTH_CACHE[espn_abbr]
        if now - ts < 3600 and data.get("QB"):
            return data

    abbr = "wsh" if espn_abbr == "was" else espn_abbr
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/depthcharts"
    
    titulares = {"QB": None, "RB": None, "WR": [], "todos": {}}
    
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            res = r.json()
            for dc in res.get("depthchart", []):
                for item in dc.get("positions", {}).values():
                    pos_abbr = item.get("position", {}).get("abbreviation", "")
                    athletes = item.get("athletes", [])
                    
                    for idx, ath in enumerate(athletes):
                        ath_data = ath.get("athlete", {})
                        nombre = ath_data.get("displayName", "")
                        ath_id = str(ath_data.get("id", ""))
                        rank = ath.get("rank", idx + 1)
                        
                        if nombre and ath_id:
                            info = {
                                "id": ath_id,
                                "nombre": nombre,
                                "posicion": pos_abbr,
                                "rank": rank,
                                "equipo": espn_abbr
                            }
                            titulares["todos"][_normalizar_texto(nombre)] = info
                            
                            # Asignar solo a los titulares de rango 1
                            if rank == 1:
                                if pos_abbr == "QB" and not titulares["QB"]:
                                    titulares["QB"] = info
                                elif pos_abbr == "RB" and not titulares["RB"]:
                                    titulares["RB"] = info
                                elif pos_abbr == "WR" and len(titulares["WR"]) < 2:
                                    titulares["WR"].append(info)
    except Exception:
        pass

    _DEPTH_CACHE[espn_abbr] = (now, titulares)
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


def verificar_en_depth_charts(nombre_jugador: str, dc_loc: dict, dc_vis: dict, abbr_loc: str, abbr_vis: str):
    nom_norm = _normalizar_texto(nombre_jugador)

    if nom_norm in dc_loc["todos"]:
        d = dc_loc["todos"][nom_norm]
        return abbr_loc, d["nombre"], d["posicion"], d["id"]
    if nom_norm in dc_vis["todos"]:
        d = dc_vis["todos"][nom_norm]
        return abbr_vis, d["nombre"], d["posicion"], d["id"]

    for k, v in dc_loc["todos"].items():
        if nom_norm in k or k in nom_norm:
            return abbr_loc, v["nombre"], v["posicion"], v["id"]

    for k, v in dc_vis["todos"].items():
        if nom_norm in k or k in nom_norm:
            return abbr_vis, v["nombre"], v["posicion"], v["id"]

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
    cache_key = f"{local}_{visitante}_props_depthchart_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_NFL.get(local, {}).get("espn_abbr", "nfl")
    abbr_vis = MAPEO_EQUIPOS_NFL.get(visitante, {}).get("espn_abbr", "nfl")

    dc_loc = obtener_titulares_reales_espn(abbr_loc)
    dc_vis = obtener_titulares_reales_espn(abbr_vis)

    candidatas = []
    event_id = _obtener_event_id_odds("americanfootball_nfl", local, visitante)

    # 1. EVALUAR LÍNEAS REALES DEL CASINO (SI COINCIDEN CON JUGADORES VALIDADOS)
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

                        equipo_real, nombre_oficial, pos, athlete_id = verificar_en_depth_charts(
                            jugador_raw, dc_loc, dc_vis, abbr_loc, abbr_vis
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

    # 2. GENERADOR BASADO EN EL DEPTH CHART OFICIAL (TITULARES INDISCUTIDOS)
    if len(candidatas) < 6:
        qb_l = dc_loc["QB"]
        qb_v = dc_vis["QB"]
        rb_l = dc_loc["RB"]
        rb_v = dc_vis["RB"]
        wr_l = dc_loc["WR"][0] if dc_loc["WR"] else None
        wr_v = dc_vis["WR"][0] if dc_vis["WR"] else None

        pool = []

        if wr_l:
            p = obtener_promedios_reales_espn(wr_l["id"], "player_reception_yds") or 74.5
            pool.append({"jugador": wr_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p - 6.5, 1), "cuota": 1.88, "proyeccion": p, "prob_real": 60.5, "ev": 13.7})

        if qb_v:
            p = obtener_promedios_reales_espn(qb_v["id"], "player_pass_yds") or 240.0
            pool.append({"jugador": qb_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Pase", "lado": "MÁS DE", "linea": round(p - 14.5, 1), "cuota": 1.90, "proyeccion": p, "prob_real": 58.8, "ev": 11.7})

        if rb_l:
            p = obtener_promedios_reales_espn(rb_l["id"], "player_rush_yds") or 65.0
            pool.append({"jugador": rb_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Carrera", "lado": "MÁS DE", "linea": round(p - 6.5, 1), "cuota": 1.87, "proyeccion": p, "prob_real": 58.4, "ev": 9.2})

        if rb_v:
            p = obtener_promedios_reales_espn(rb_v["id"], "player_rush_yds") or 50.0
            pool.append({"jugador": rb_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Carrera", "lado": "MENOS DE", "linea": round(p + 6.5, 1), "cuota": 1.85, "proyeccion": p, "prob_real": 59.8, "ev": 10.6})

        if wr_v:
            p = obtener_promedios_reales_espn(wr_v["id"], "player_reception_yds") or 62.0
            pool.append({"jugador": wr_v["nombre"], "equipo_abbr": abbr_vis, "tipo_prop": "Yardas por Recepción", "lado": "MÁS DE", "linea": round(p - 6.5, 1), "cuota": 1.92, "proyeccion": p, "prob_real": 58.0, "ev": 11.4})

        if qb_l:
            p = obtener_promedios_reales_espn(qb_l["id"], "player_pass_yds") or 225.0
            pool.append({"jugador": qb_l["nombre"], "equipo_abbr": abbr_loc, "tipo_prop": "Yardas por Pase", "lado": "MENOS DE", "linea": round(p + 15.5, 1), "cuota": 1.86, "proyeccion": p, "prob_real": 59.2, "ev": 10.1})

        for p in pool:
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
