import os
import time
import requests

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "").strip()

DEPORTE_TO_SPORT_KEY = {
    "nba": "basketball_nba",
    "nhl": "icehockey_nhl",
    "nfl": "americanfootball_nfl",
    "mlb": "baseball_mlb"
}

# Solo los 2 mercados principales por deporte para consumir el mínimo de créditos
PROP_MARKETS_BY_SPORT = {
    "nhl": "player_shots_on_goal,player_points",
    "nba": "player_points,player_rebounds",
    "nfl": "player_pass_yds,player_rush_yds",
    "mlb": "batter_hits,pitcher_strikeouts"
}

MAPEO_MERCADO_ODDS_API = {
    "player_shots_on_goal": "Tiros a Puerta",
    "player_points": "Puntos",
    "player_assists": "Asistencias",
    "player_rebounds": "Rebotes",
    "player_threes": "Triples",
    "player_pass_yds": "Yardas Pase",
    "player_rush_yds": "Yardas Acarreo",
    "player_reception_yds": "Yardas Recepción",
    "player_receptions": "Recepciones",
    "batter_hits": "Hits",
    "batter_total_bases": "Bases Totales",
    "pitcher_strikeouts": "Ponches"
}

KAMBI_SPORTS = {
    "nba": "basketball/nba",
    "nfl": "american_football/nfl",
    "nhl": "ice_hockey/nhl",
    "mlb": "baseball/mlb"
}

ESPN_SCOREBOARD_URLS = {
    "nba": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
    "nfl": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "nhl": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
    "mlb": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
}

OPERADORES_KAMBI = ["ubca", "unibet", "ubus", "rsiusil", "rsiubus"]

HEADERS_WEB = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

_CACHE_EVENTOS_ODDS_API = {}
_CACHE_PROPS_ODDS_API = {}
_CACHE_EVENTOS_KAMBI = {}
_CACHE_OFERTAS_KAMBI = {}
_ODDS_API_AGOTADA_HASTA = 0


def _simplificar(texto: str) -> str:
    return "".join(c for c in str(texto).lower() if c.isalnum())


def _apodo_equipo(nombre_completo: str) -> str:
    partes = nombre_completo.strip().split()
    return _simplificar(partes[-1]) if partes else _simplificar(nombre_completo)


def _coincide_partido(ev_home: str, ev_away: str, local: str, visitante: str) -> bool:
    h, a = _simplificar(ev_home), _simplificar(ev_away)
    l_apodo, v_apodo = _apodo_equipo(local), _apodo_equipo(visitante)
    return (l_apodo in h and v_apodo in a) or (l_apodo in a and v_apodo in h)


def _obtener_props_the_odds_api(deporte: str, local: str, visitante: str):
    """Consulta The Odds API en modo ahorro extremo de créditos (caché largo + 1 región)."""
    global _ODDS_API_AGOTADA_HASTA

    ahora = time.time()
    # Si ya dio 401/429 (sin créditos), no vuelve a intentar durante 1 hora
    if ahora < _ODDS_API_AGOTADA_HASTA:
        return []

    dep = deporte.lower()
    sport_key = DEPORTE_TO_SPORT_KEY.get(dep)
    markets = PROP_MARKETS_BY_SPORT.get(dep)
    api_key = os.getenv("ODDS_API_KEY", ODDS_API_KEY).strip()

    if not sport_key or not markets or not api_key:
        return []

    # Caché de 45 minutos (2700s) para no repetir gasto de créditos en el mismo partido
    cache_key = f"{dep}_{_simplificar(local)}_{_simplificar(visitante)}"
    if cache_key in _CACHE_PROPS_ODDS_API and (ahora - _CACHE_PROPS_ODDS_API[cache_key][0] < 2700):
        return _CACHE_PROPS_ODDS_API[cache_key][1]

    try:
        # 1. Lista de eventos del día (este endpoint NO consume créditos en The Odds API, pero igual lo cacheamos 30 min)
        ev_cache_key = f"events_{dep}"
        if ev_cache_key in _CACHE_EVENTOS_ODDS_API and (ahora - _CACHE_EVENTOS_ODDS_API[ev_cache_key][0] < 1800):
            eventos = _CACHE_EVENTOS_ODDS_API[ev_cache_key][1]
        else:
            url_events = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
            r_ev = requests.get(url_events, params={"apiKey": api_key}, timeout=6)
            if r_ev.status_code in [401, 429]:
                _ODDS_API_AGOTADA_HASTA = ahora + 3600
                return []
            if r_ev.status_code != 200:
                return []
            eventos = r_ev.json()
            _CACHE_EVENTOS_ODDS_API[ev_cache_key] = (ahora, eventos)

        event_id = None
        for ev in eventos:
            if _coincide_partido(ev.get("home_team", ""), ev.get("away_team", ""), local, visitante):
                event_id = ev.get("id")
                break

        if not event_id:
            return []

        # 2. Consultar solo region="us" para gastar solo 2 créditos por partido (1 por mercado)
        url_props = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": markets,
            "oddsFormat": "decimal"
        }
        r_props = requests.get(url_props, params=params, timeout=8)
        if r_props.status_code in [401, 429]:
            _ODDS_API_AGOTADA_HASTA = ahora + 3600
            return []
        if r_props.status_code != 200:
            return []

        bookmakers = r_props.json().get("bookmakers", [])
        if not bookmakers:
            return []

        prioridad = ["fanduel", "draftkings", "betmgm", "caesars", "espnbet"]
        bookmakers.sort(key=lambda b: prioridad.index(b.get("key")) if b.get("key") in prioridad else 99)

        agrupado = {}
        for bm in bookmakers[:3]:
            for market in bm.get("markets", []):
                m_key = market.get("key")
                tipo_esp = MAPEO_MERCADO_ODDS_API.get(m_key)
                if not tipo_esp:
                    continue

                for out in market.get("outcomes", []):
                    jugador = out.get("description", "").strip()
                    lado = out.get("name", "").lower()
                    linea = out.get("point")
                    precio = out.get("price")

                    if not jugador or linea is None or not precio or precio <= 1.05:
                        continue

                    clave = (_simplificar(jugador), tipo_esp, float(linea))
                    if clave not in agrupado:
                        agrupado[clave] = {
                            "jugador": jugador,
                            "tipo_prop": tipo_esp,
                            "linea": float(linea),
                            "cuota_over": None,
                            "cuota_under": None
                        }

                    if lado == "over" and agrupado[clave]["cuota_over"] is None:
                        agrupado[clave]["cuota_over"] = round(float(precio), 2)
                    elif lado == "under" and agrupado[clave]["cuota_under"] is None:
                        agrupado[clave]["cuota_under"] = round(float(precio), 2)

        props_finales = [v for v in agrupado.values() if v["cuota_over"] is not None]
        if props_finales:
            _CACHE_PROPS_ODDS_API[cache_key] = (ahora, props_finales)
        return props_finales

    except Exception as e:
        print(f"Error Odds API Player Props ({deporte}): {e}")
        return []


def _buscar_event_id_kambi(deporte: str, local: str, visitante: str):
    sport_path = KAMBI_SPORTS.get(deporte.lower())
    if not sport_path:
        return None

    ahora = time.time()
    cache_key = f"list_{deporte.lower()}"
    eventos = []

    if cache_key in _CACHE_EVENTOS_KAMBI and (ahora - _CACHE_EVENTOS_KAMBI[cache_key][0] < 900):
        eventos = _CACHE_EVENTOS_KAMBI[cache_key][1]
    else:
        for op in OPERADORES_KAMBI:
            market_code = "CA" if op == "ubca" else ("GB" if op == "unibet" else "US")
            url = f"https://eu-offering-api.kambicdn.com/offering/v2018/{op}/listView/{sport_path}.json?lang=en_US&market={market_code}&client_id=2&channel_id=1&ncid={int(ahora*1000)}"
            try:
                r = requests.get(url, headers=HEADERS_WEB, timeout=5)
                if r.status_code == 200:
                    eventos = r.json().get("events", [])
                    if eventos:
                        _CACHE_EVENTOS_KAMBI[cache_key] = (ahora, eventos)
                        break
            except Exception:
                continue

    for item in eventos:
        ev = item.get("event", {})
        if _coincide_partido(ev.get("homeName", ""), ev.get("awayName", ""), local, visitante):
            return ev.get("id")

    return None


def _obtener_betoffers_evento(event_id):
    ahora = time.time()
    if event_id in _CACHE_OFERTAS_KAMBI and (ahora - _CACHE_OFERTAS_KAMBI[event_id][0] < 900):
        return _CACHE_OFERTAS_KAMBI[event_id][1]

    for op in OPERADORES_KAMBI:
        market_code = "CA" if op == "ubca" else ("GB" if op == "unibet" else "US")
        url = f"https://eu-offering-api.kambicdn.com/offering/v2018/{op}/betoffer/event/{event_id}.json?lang=en_US&market={market_code}&client_id=2&channel_id=1&ncid={int(ahora*1000)}"
        try:
            r = requests.get(url, headers=HEADERS_WEB, timeout=6)
            if r.status_code == 200:
                ofertas = r.json().get("betOffers", [])
                if ofertas:
                    _CACHE_OFERTAS_KAMBI[event_id] = (ahora, ofertas)
                    return ofertas
        except Exception:
            continue
    return []


def _americana_a_decimal(americana) -> float:
    try:
        val = float(americana)
        if val > 0:
            return round((val / 100.0) + 1.0, 2)
        elif val < 0:
            return round((100.0 / abs(val)) + 1.0, 2)
    except Exception:
        pass
    return 1.90


def _obtener_cuotas_espn_scoreboard(deporte: str, local: str, visitante: str):
    url = ESPN_SCOREBOARD_URLS.get(deporte.lower())
    if not url:
        return None

    try:
        r = requests.get(url, headers=HEADERS_WEB, timeout=6)
        if r.status_code != 200:
            return None

        eventos = r.json().get("events", [])
        l_apodo = _apodo_equipo(local)
        v_apodo = _apodo_equipo(visitante)

        for ev in eventos:
            comp = ev.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            nombres = [_simplificar(c.get("team", {}).get("displayName", "")) for c in competitors]
            if not (any(l_apodo in n for n in nombres) and any(v_apodo in n for n in nombres)):
                continue

            odds_list = comp.get("odds", [])
            if not odds_list:
                continue

            odds = odds_list[0]
            provider = odds.get("provider", {}).get("name", "ESPN BET / Caesars")
            over_under = odds.get("overUnder")
            spread = odds.get("spread")

            home_odds = odds.get("homeTeamOdds", {})
            away_odds = odds.get("awayTeamOdds", {})

            espn_home_name = ""
            for c in competitors:
                if c.get("homeAway") == "home":
                    espn_home_name = _simplificar(c.get("team", {}).get("displayName", ""))

            local_es_home = (l_apodo in espn_home_name)

            ml_loc_raw = home_odds.get("moneyLine") if local_es_home else away_odds.get("moneyLine")
            ml_vis_raw = away_odds.get("moneyLine") if local_es_home else home_odds.get("moneyLine")

            sp_loc_raw = home_odds.get("spreadOdds", -110) if local_es_home else away_odds.get("spreadOdds", -110)
            sp_vis_raw = away_odds.get("spreadOdds", -110) if local_es_home else home_odds.get("spreadOdds", -110)

            linea_sp_loc = float(spread) if (spread is not None and local_es_home) else (-float(spread) if spread is not None else -2.5)
            linea_sp_vis = -linea_sp_loc

            over_odds_raw = odds.get("overOdds", -110)
            under_odds_raw = odds.get("underOdds", -110)

            return {
                "success": True,
                "data": {
                    "bookmaker": f"{provider} (Live)",
                    "cuota_ml_local": _americana_a_decimal(ml_loc_raw) if ml_loc_raw else 1.90,
                    "cuota_ml_visitante": _americana_a_decimal(ml_vis_raw) if ml_vis_raw else 1.90,
                    "linea_spread_local": linea_sp_loc,
                    "cuota_spread_local": _americana_a_decimal(sp_loc_raw),
                    "linea_spread_visitante": linea_sp_vis,
                    "cuota_spread_visitante": _americana_a_decimal(sp_vis_raw),
                    "linea_total": float(over_under) if over_under else 220.5,
                    "cuota_total_over": _americana_a_decimal(over_odds_raw),
                    "cuota_total_under": _americana_a_decimal(under_odds_raw)
                }
            }
    except Exception as e:
        print(f"Error ESPN Scoreboard Odds: {e}")

    return None


def obtener_cuotas_partido_kambi(deporte: str, local: str, visitante: str):
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if event_id:
        ofertas = _obtener_betoffers_evento(event_id)
        if ofertas:
            l_apodo = _apodo_equipo(local)
            v_apodo = _apodo_equipo(visitante)
            datos = {
                "bookmaker": "Kambi / Unibet Live",
                "cuota_ml_local": None, "cuota_ml_visitante": None,
                "linea_spread_local": None, "cuota_spread_local": None,
                "linea_spread_visitante": None, "cuota_spread_visitante": None,
                "linea_total": None, "cuota_total_over": None, "cuota_total_under": None
            }

            for bo in ofertas:
                crit = bo.get("criterion", {})
                label = str(crit.get("label", "")).lower()
                bo_type = bo.get("betOfferType", {}).get("name", "").lower()
                outcomes = bo.get("outcomes", [])

                if ("moneyline" in label or "including overtime" in label or "match" in bo_type) and len(outcomes) == 2 and not datos["cuota_ml_local"]:
                    for o in outcomes:
                        part = _simplificar(o.get("participant", "") or o.get("label", ""))
                        cuota = round(o.get("odds", 0) / 1000.0, 2)
                        if cuota > 1.0:
                            if l_apodo in part: datos["cuota_ml_local"] = cuota
                            elif v_apodo in part: datos["cuota_ml_visitante"] = cuota

                elif ("handicap" in bo_type or "spread" in label) and len(outcomes) == 2 and not datos["cuota_spread_local"]:
                    for o in outcomes:
                        part = _simplificar(o.get("participant", "") or o.get("label", ""))
                        cuota = round(o.get("odds", 0) / 1000.0, 2)
                        linea = o.get("line", 0) / 1000.0
                        if cuota > 1.0:
                            if l_apodo in part:
                                datos["linea_spread_local"] = linea
                                datos["cuota_spread_local"] = cuota
                            elif v_apodo in part:
                                datos["linea_spread_visitante"] = linea
                                datos["cuota_spread_visitante"] = cuota

                elif ("total" in bo_type or "total points" in label or "total goals" in label) and len(outcomes) == 2 and not datos["linea_total"]:
                    for o in outcomes:
                        lado = str(o.get("type", "")).lower()
                        cuota = round(o.get("odds", 0) / 1000.0, 2)
                        linea = o.get("line", 0) / 1000.0
                        if cuota > 1.0 and linea > 0:
                            datos["linea_total"] = linea
                            if "over" in lado or "over" in str(o.get("label", "")).lower():
                                datos["cuota_total_over"] = cuota
                            elif "under" in lado or "under" in str(o.get("label", "")).lower():
                                datos["cuota_total_under"] = cuota

            if datos["cuota_ml_local"] or datos["linea_total"]:
                return {"success": True, "data": datos}

    res_espn = _obtener_cuotas_espn_scoreboard(deporte, local, visitante)
    if res_espn:
        return res_espn

    return {"success": False, "error": f"No hay cuotas abiertas hoy en el mercado para {local} vs {visitante}."}


def obtener_player_props_kambi(deporte: str, local: str, visitante: str):
    # 1. Intenta The Odds API (se salta automáticamente si ya se agotaron los 500 créditos)
    props_odds_api = _obtener_props_the_odds_api(deporte, local, visitante)
    if props_odds_api:
        return props_odds_api

    # 2. Respaldo gratuito e ilimitado: Kambi multi-operador (ubca / unibet / ubus)
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if not event_id:
        return []

    ofertas = _obtener_betoffers_evento(event_id)
    props_reales = []

    mapeo_mercados = {
        "shots on goal": "Tiros a Puerta",
        "points scored": "Puntos",
        "total points": "Puntos",
        "rebounds": "Rebotes",
        "assists": "Asistencias",
        "three-point": "Triples",
        "3-point": "Triples",
        "passing yards": "Yardas Pase",
        "rushing yards": "Yardas Acarreo",
        "receiving yards": "Yardas Recepción",
        "receptions": "Recepciones",
        "points": "Puntos"
    }

    for bo in ofertas:
        crit_label = str(bo.get("criterion", {}).get("label", "")).lower()
        outcomes = bo.get("outcomes", [])
        if len(outcomes) != 2:
            continue

        # Excluir totales de equipo
        if "team" in crit_label or "home" in crit_label or "away" in crit_label:
            continue

        tipo_detectado = None
        for clave, nombre_esp in mapeo_mercados.items():
            if clave in crit_label:
                tipo_detectado = nombre_esp
                break

        if not tipo_detectado:
            continue

        jugador_raw = outcomes[0].get("participant", "")
        if not jugador_raw:
            continue

        if "," in jugador_raw:
            partes = [p.strip() for p in jugador_raw.split(",", 1)]
            jugador = f"{partes[1]} {partes[0]}"
        else:
            jugador = jugador_raw.strip()

        linea = outcomes[0].get("line", 0) / 1000.0
        if linea <= 0:
            continue

        c_over = None
        c_under = None
        for o in outcomes:
            o_type = str(o.get("type", "")).lower()
            o_label = str(o.get("label", "")).lower()
            odds = round(o.get("odds", 0) / 1000.0, 2)
            if "over" in o_type or "over" in o_label:
                c_over = odds
            elif "under" in o_type or "under" in o_label:
                c_under = odds

        if c_over and c_over > 1.05:
            props_reales.append({
                "jugador": jugador,
                "tipo_prop": tipo_detectado,
                "linea": linea,
                "cuota_over": c_over,
                "cuota_under": c_under or 1.90
            })

    return props_reales
