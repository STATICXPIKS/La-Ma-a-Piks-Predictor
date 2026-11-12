import time
import requests

KAMBI_SPORTS = {
    "nba": "basketball/nba",
    "nfl": "american_football/nfl",
    "nhl": "ice_hockey/nhl",
    "mlb": "baseball/mlb"
}

# Operadores Kambi públicos (incluye el feed que alimenta Rushbet / BetRivers)
OPERADORES_KAMBI = ["ubus", "rsiusil", "rsiubus"]

HEADERS_KAMBI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.rushbet.co/"
}

_CACHE_EVENTOS = {}
_CACHE_OFERTAS = {}


def _simplificar(texto: str) -> str:
    return "".join(c for c in str(texto).lower() if c.isalnum())


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
                r = requests.get(url, headers=HEADERS_KAMBI, timeout=6)
                if r.status_code == 200:
                    data = r.json()
                    eventos = data.get("events", [])
                    if eventos:
                        _CACHE_EVENTOS[cache_key] = (ahora, eventos)
                        break
            except Exception:
                continue

    loc_s = _simplificar(local)
    vis_s = _simplificar(visitante)

    for item in eventos:
        ev = item.get("event", {})
        home = _simplificar(ev.get("homeName", ""))
        away = _simplificar(ev.get("awayName", ""))
        if (loc_s in home or home in loc_s) and (vis_s in away or away in vis_s):
            return ev.get("id")

    return None


def _obtener_betoffers_evento(event_id):
    ahora = time.time()
    if event_id in _CACHE_OFERTAS and (ahora - _CACHE_OFERTAS[event_id][0] < 600):
        return _CACHE_OFERTAS[event_id][1]

    for op in OPERADORES_KAMBI:
        url = f"https://eu-offering-api.kambicdn.com/offering/v2018/{op}/betoffer/event/{event_id}.json?lang=en_US&market=US&client_id=2&channel_id=1&ncid={int(ahora*1000)}"
        try:
            r = requests.get(url, headers=HEADERS_KAMBI, timeout=7)
            if r.status_code == 200:
                ofertas = r.json().get("betOffers", [])
                if ofertas:
                    _CACHE_OFERTAS[event_id] = (ahora, ofertas)
                    return ofertas
        except Exception:
            continue
    return []


def obtener_cuotas_partido_kambi(deporte: str, local: str, visitante: str):
    """Extrae Moneyline, Spread y Total en vivo desde Kambi (sin consumir créditos)."""
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if not event_id:
        return {"success": False, "error": f"No se encontró el partido {local} vs {visitante} abierto en Kambi/Rushbet."}

    ofertas = _obtener_betoffers_evento(event_id)
    if not ofertas:
        return {"success": False, "error": "Kambi no devolvió cuotas abiertas para este encuentro."}

    loc_s = _simplificar(local)
    vis_s = _simplificar(visitante)

    datos = {
        "bookmaker": "Kambi / Rushbet Live",
        "cuota_ml_local": None,
        "cuota_ml_visitante": None,
        "linea_spread_local": None,
        "cuota_spread_local": None,
        "linea_spread_visitante": None,
        "cuota_spread_visitante": None,
        "linea_total": None,
        "cuota_total_over": None,
        "cuota_total_under": None
    }

    for bo in ofertas:
        crit = bo.get("criterion", {})
        label = str(crit.get("label", "")).lower()
        bo_type = bo.get("betOfferType", {}).get("name", "").lower()
        outcomes = bo.get("outcomes", [])

        # Moneyline (Incluyendo prórroga / tiempo extra)
        if ("moneyline" in label or "including overtime" in label or "match" in bo_type) and len(outcomes) == 2 and not datos["cuota_ml_local"]:
            for o in outcomes:
                part = _simplificar(o.get("participant", "") or o.get("label", ""))
                cuota = round(o.get("odds", 0) / 1000.0, 2)
                if cuota > 1.0:
                    if loc_s in part or part in loc_s:
                        datos["cuota_ml_local"] = cuota
                    elif vis_s in part or part in vis_s:
                        datos["cuota_ml_visitante"] = cuota

        # Point Spread / Handicap
        elif ("handicap" in bo_type or "spread" in label) and "including overtime" in label and len(outcomes) == 2 and not datos["cuota_spread_local"]:
            for o in outcomes:
                part = _simplificar(o.get("participant", "") or o.get("label", ""))
                cuota = round(o.get("odds", 0) / 1000.0, 2)
                linea = o.get("line", 0) / 1000.0
                if cuota > 1.0:
                    if loc_s in part or part in loc_s:
                        datos["linea_spread_local"] = linea
                        datos["cuota_spread_local"] = cuota
                    elif vis_s in part or part in vis_s:
                        datos["linea_spread_visitante"] = linea
                        datos["cuota_spread_visitante"] = cuota

        # Total Over / Under
        elif ("total" in bo_type or "total points" in label or "total goals" in label) and "including overtime" in label and len(outcomes) == 2 and not datos["linea_total"]:
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

    if not datos["cuota_ml_local"] and not datos["linea_total"]:
        return {"success": False, "error": "Mercados principales aún bloqueados en el casino."}

    return {"success": True, "data": datos}


def obtener_player_props_kambi(deporte: str, local: str, visitante: str):
    """
    Extrae todas las líneas y momios reales de Player Props publicados en Kambi/Rushbet.
    Retorna lista de dicts: {jugador, mercado, linea, cuota_over, cuota_under}
    """
    event_id = _buscar_event_id_kambi(deporte, local, visitante)
    if not event_id:
        return []

    ofertas = _obtener_betoffers_evento(event_id)
    props_reales = []

    mapeo_mercados = {
        "points scored by the player": "Puntos",
        "rebounds by the player": "Rebotes",
        "assists by the player": "Asistencias",
        "three-point field goals made by the player": "Triples",
        "3-point field goals made by the player": "Triples",
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

        # Kambi entrega "Apellido, Nombre" -> convertir a "Nombre Apellido"
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
