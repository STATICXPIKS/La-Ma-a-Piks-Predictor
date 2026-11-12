import time
import requests

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

OPERADORES_KAMBI = ["ubus", "rsiusil", "rsiubus", "ubca", "unibet"]

HEADERS_WEB = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

_CACHE_EVENTOS = {}
_CACHE_OFERTAS = {}


def _simplificar(texto: str) -> str:
    return "".join(c for c in str(texto).lower() if c.isalnum())


def _apodo_equipo(nombre_completo: str) -> str:
    """Extrae la palabra distintiva del equipo (ej. 'Philadelphia 76ers' -> '76ers')."""
    partes = nombre_completo.strip().split()
    return _simplificar(partes[-1]) if partes else _simplificar(nombre_completo)


def _coincide_partido(ev_home: str, ev_away: str, local: str, visitante: str) -> bool:
    h, a = _simplificar(ev_home), _simplificar(ev_away)
    l_apodo, v_apodo = _apodo_equipo(local), _apodo_equipo(visitante)
    # Verifica tanto Local vs Visitante como Visitante @ Local
    directo = (l_apodo in h and v_apodo in a)
    invertido = (l_apodo in a and v_apodo in h)
    return directo or invertido


def _buscar_event_id_kambi(deporte: str, local: str, visitante: str):
    sport_path = KAMBI_SPORTS.get(deporte.lower())
    if not sport_path:
        return None

    ahora = time.time()
    cache_key = f"list_{deporte.lower()}"
    eventos = []

    if cache_key in _CACHE_EVENTOS and (ahora - _CACHE_EVENTOS[cache_key][0] < 600):
        eventos = _CACHE_EVENTOS[cache_key][1]
    else:
        for op in OPERADORES_KAMBI:
            url = f"https://eu-offering-api.kambicdn.com/offering/v2018/{op}/listView/{sport_path}.json?lang=en_US&market=US&client_id=2&channel_id=1&ncid={int(ahora*1000)}"
            try:
                r = requests.get(url, headers=HEADERS_WEB, timeout=5)
                if r.status_code == 200:
                    eventos = r.json().get("events", [])
                    if eventos:
                        _CACHE_EVENTOS[cache_key] = (ahora, eventos)
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
    if event_id in _CACHE_OFERTAS and (ahora - _CACHE_OFERTAS[event_id][0] < 600):
        return _CACHE_OFERTAS[event_id][1]

    for op in OPERADORES_KAMBI:
        url = f"https://eu-offering-api.kambicdn.com/offering/v2018/{op}/betoffer/event/{event_id}.json?lang=en_US&market=US&client_id=2&channel_id=1&ncid={int(ahora*1000)}"
        try:
            r = requests.get(url, headers=HEADERS_WEB, timeout=6)
            if r.status_code == 200:
                ofertas = r.json().get("betOffers", [])
                if ofertas:
                    _CACHE_OFERTAS[event_id] = (ahora, ofertas)
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
    """Fuente gratuita e ilimitada: extrae líneas y cuotas oficiales de ESPN BET / Caesars."""
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

            # Determinar cuál competidor en ESPN es el local que seleccionó el usuario
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
    """
    Extrae cuotas principales en vivo:
    1. Intenta Kambi / Rushbet (búsqueda bidireccional).
    2. Si Kambi bloquea la IP de Render, extrae directo de ESPN BET / Caesars (gratis e ilimitado).
    """
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if event_id:
        ofertas = _obtener_betoffers_evento(event_id)
        if ofertas:
            l_apodo = _apodo_equipo(local)
            v_apodo = _apodo_equipo(visitante)
            datos = {
                "bookmaker": "Kambi / Rushbet Live",
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

    # Respaldo automático gratuito e ilimitado: ESPN BET / Caesars
    res_espn = _obtener_cuotas_espn_scoreboard(deporte, local, visitante)
    if res_espn:
        return res_espn

    return {"success": False, "error": f"No hay cuotas abiertas hoy en el mercado para {local} vs {visitante}."}


def obtener_player_props_kambi(deporte: str, local: str, visitante: str):
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if not event_id:
        return []

    ofertas = _obtener_betoffers_evento(event_id)
    props_reales = []

    mapeo_mercados = {
        "points scored": "Puntos",
        "rebounds": "Rebotes",
        "assists": "Asistencias",
        "three-point": "Triples",
        "3-point": "Triples",
        "passing yards": "Yardas Pase",
        "rushing yards": "Yardas Acarreo",
        "receiving yards": "Yardas Recepción",
        "receptions": "Recepciones",
        "shots on goal": "Tiros a Puerta",
        "points": "Puntos"
    }

    for bo in ofertas:
        crit_label = str(bo.get("criterion", {}).get("label", "")).lower()
        outcomes = bo.get("outcomes", [])
        if len(outcomes) != 2:
            continue

        tipo_detectado = None
        for clave, nombre_esp in mapeo_mercados.items():
            if clave in crit_label and ("player" in crit_label or "yards" in crit_label or "receptions" in crit_label or "shots" in crit_label):
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

        if c_over and c_under and c_over > 1.05 and c_under > 1.05:
            props_reales.append({
                "jugador": jugador,
                "tipo_prop": tipo_detectado,
                "linea": linea,
                "cuota_over": c_over,
                "cuota_under": c_under
            })

    return props_reales
