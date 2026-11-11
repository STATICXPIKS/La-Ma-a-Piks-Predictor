import os
import time
import math
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")

MAPEO_EQUIPOS_MLB = {
    "Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal",
    "Boston Red Sox": "bos", "Chicago Cubs": "chc", "Chicago White Sox": "chw",
    "Cincinnati Reds": "cin", "Cleveland Guardians": "cle", "Colorado Rockies": "col",
    "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc",
    "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia",
    "Milwaukee Brewers": "mil", "Minnesota Twins": "min", "New York Mets": "nym",
    "New York Yankees": "nyy", "Oakland Athletics": "oak", "Philadelphia Phillies": "phi",
    "Pittsburgh Pirates": "pit", "San Diego Padres": "sd", "San Francisco Giants": "sf",
    "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb",
    "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh"
}

NOMBRES_MERCADOS_MLB = {
    "pitcher_strikeouts": "Ponches (K's)",
    "pitcher_outs": "Outs Registrados",
    "batter_hits": "Hits",
    "batter_hits_runs_rbis": "Hits + Carreras + Impulsadas (H+R+RBI)"
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


def obtener_roster_activo_mlb(espn_abbr: str):
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and len(data) > 0:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{espn_abbr}/roster"
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


def obtener_estadisticas_reales_mlb(athlete_id: str):
    if not athlete_id:
        return {}

    now = time.time()
    if athlete_id in _STATS_CACHE:
        ts, val = _STATS_CACHE[athlete_id]
        if now - ts < 7200:
            return val

    url = f"https://site.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes/{athlete_id}/stats"
    res_stats = {}

    targets = {
        "pitcher_strikeouts": ["strikeoutsper9", "strikeouts", "avgstrikeouts", "k/9", "so"],
        "pitcher_outs": ["inningspitched", "ip", "outs"],
        "batter_hits": ["hitspergame", "avghits", "hits", "h"],
        "batter_hits_runs_rbis": ["hits", "runs", "rbi"]
    }

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=3)
        if r.status_code == 200:
            data = r.json()
            acumulados = {k: [] for k in targets}
            h_val, r_val, rbi_val = 0.0, 0.0, 0.0

            for cat in data.get("categories", []):
                for stat in cat.get("statistics", []):
                    n = stat.get("name", "").lower()
                    a = stat.get("abbreviation", "").lower()
                    val_str = str(stat.get("displayValue", "0")).replace(",", "")
                    try:
                        val_num = float(val_str)
                    except ValueError:
                        continue

                    if n in targets["pitcher_strikeouts"] or a in targets["pitcher_strikeouts"]:
                        acumulados["pitcher_strikeouts"].append(val_num)
                    if n in targets["pitcher_outs"] or a in targets["pitcher_outs"]:
                        acumulados["pitcher_outs"].append(val_num)
                    if n in targets["batter_hits"] or a in targets["batter_hits"]:
                        acumulados["batter_hits"].append(val_num)

                    if a == "h" or n == "hits": h_val = val_num
                    if a == "r" or n == "runs": r_val = val_num
                    if a == "rbi" or n == "rbi": rbi_val = val_num

            if acumulados["pitcher_strikeouts"]:
                val_k = acumulados["pitcher_strikeouts"][0]
                res_stats["pitcher_strikeouts"] = round((val_k / 9.0) * 5.6, 1) if val_k > 15 else round(val_k, 1)

            if acumulados["pitcher_outs"]:
                val_ip = acumulados["pitcher_outs"][0]
                res_stats["pitcher_outs"] = round(val_ip * 3.0, 1) if val_ip <= 9.0 else 16.5

            if acumulados["batter_hits"]:
                res_stats["batter_hits"] = round(acumulados["batter_hits"][0], 2)

            if (h_val + r_val + rbi_val) > 0:
                total_combo = h_val + r_val + rbi_val
                res_stats["batter_hits_runs_rbis"] = round(total_combo / 140.0, 2) if total_combo > 20 else round(total_combo, 2)

            _STATS_CACHE[athlete_id] = (now, res_stats)
    except Exception:
        pass

    return res_stats


def verificar_atleta_en_plantilla_mlb(nombre_raw: str, roster_loc: dict, roster_vis: dict, abbr_loc: str, abbr_vis: str):
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


def _calcular_probabilidad_mlb(media_real: float, linea_casino: float, tipo_prop: str):
    if media_real <= 0 or linea_casino <= 0:
        return 0.50, 0.50

    if tipo_prop in ["pitcher_strikeouts", "pitcher_outs"]:
        cv = 0.25 if tipo_prop == "pitcher_strikeouts" else 0.20
        sigma = media_real * cv
        z = (linea_casino - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_under = max(0.12, min(0.88, prob_under))
        return (1.0 - prob_under), prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea_casino))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_under = max(0.12, min(0.88, prob_under))
        return (1.0 - prob_under), prob_under


def _obtener_odds_props_mlb_live(sport_key: str, event_id: str):
    if not ODDS_API_KEY:
        return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    try:
        r = requests.get(url, params={
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "pitcher_strikeouts,pitcher_outs,batter_hits,batter_hits_runs_rbis",
            "oddsFormat": "decimal"
        }, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_event_id_mlb_odds(sport_key: str, local_name: str, vis_name: str):
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


def obtener_mejores_props_mlb(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_mlb_strict_rules_v1"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_MLB.get(local, "mlb")
    abbr_vis = MAPEO_EQUIPOS_MLB.get(visitante, "mlb")

    roster_loc = obtener_roster_activo_mlb(abbr_loc)
    roster_vis = obtener_roster_activo_mlb(abbr_vis)

    candidatas = []
    event_id = _obtener_event_id_mlb_odds("baseball_mlb", local, visitante)

    if event_id:
        odds_data = _obtener_odds_props_mlb_live("baseball_mlb", event_id)
        if odds_data and "bookmakers" in odds_data:
            for bookmaker in odds_data["bookmakers"]:
                for market in bookmaker.get("markets", []):
                    m_key = market.get("key")
                    nombre_tipo = NOMBRES_MERCADOS_MLB.get(m_key, m_key)
                    for outcome in market.get("outcomes", []):
                        tipo_apuesta = outcome.get("name", "").strip().lower()
                        es_over = (tipo_apuesta == "over")
                        linea = outcome.get("point")
                        cuota = outcome.get("price")
                        jugador_raw = outcome.get("description", outcome.get("name", "")).strip()

                        if not linea or not cuota or cuota < 1.40 or cuota > 2.65:
                            continue

                        # Ponches de Pitcher: OVER y UNDER
                        if m_key == "pitcher_strikeouts":
                            pass
                        # Outs de Pitcher: OVER y UNDER
                        elif m_key == "pitcher_outs":
                            pass
                        # Hits: solo OVER a partir de 0.5
                        elif m_key == "batter_hits":
                            if not es_over or linea < 0.5:
                                continue
                        # H+R+RBI: solo OVER a partir de 1.0
                        elif m_key == "batter_hits_runs_rbis":
                            if not es_over or linea < 1.0:
                                continue
                        else:
                            continue

                        equipo_real, nombre_oficial, athlete_id = verificar_atleta_en_plantilla_mlb(
                            jugador_raw, roster_loc, roster_vis, abbr_loc, abbr_vis
                        )
                        if not equipo_real or not athlete_id:
                            continue

                        stats = obtener_estadisticas_reales_mlb(athlete_id)
                        promedio_real = stats.get(m_key)

                        if not promedio_real or promedio_real <= 0:
                            continue

                        prob_over, prob_under = _calcular_probabilidad_mlb(promedio_real, linea, m_key)
                        prob_sel = prob_over if es_over else prob_under
                        ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

                        if 2.0 <= ev <= 25.0:
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

    unicos = {}
    for p in candidatas:
        k = (p["jugador"], p["tipo_prop"], p["lado"], p["linea"])
        if k not in unicos or p["ev"] > unicos[k]["ev"]:
            unicos[k] = p

    ordenadas = sorted(unicos.values(), key=lambda x: x["ev"], reverse=True)
    seleccion = ordenadas[:top_n]

    _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
