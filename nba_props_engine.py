import time
import math
import requests

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

HEADERS_ESPN = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_PROPS_CACHE = {}
_ROSTER_CACHE = {}
_STATS_CACHE = {}
CACHE_DURATION_SECONDS = 900


def obtener_roster_activo_espn(espn_abbr: str):
    now = time.time()
    if espn_abbr in _ROSTER_CACHE:
        ts, data = _ROSTER_CACHE[espn_abbr]
        if now - ts < 3600 and len(data) > 0:
            return data

    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{espn_abbr}/roster"
    jugadores = []

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=5)
        if r.status_code == 200:
            res = r.json()
            raw_athletes = res.get("athletes", [])

            def registrar_atleta(item):
                nombre = item.get("displayName", "")
                ath_id = str(item.get("id", ""))
                if nombre and ath_id:
                    jugadores.append({
                        "id": ath_id,
                        "nombre": nombre,
                        "equipo": espn_abbr
                    })

            if raw_athletes and isinstance(raw_athletes[0], dict) and "items" in raw_athletes[0]:
                for group in raw_athletes:
                    for item in group.get("items", []):
                        registrar_atleta(item)
            else:
                for item in raw_athletes:
                    registrar_atleta(item)
    except Exception as e:
        print(f"Error cargando roster ESPN {espn_abbr}: {e}")

    _ROSTER_CACHE[espn_abbr] = (now, jugadores)
    return jugadores


def obtener_estadisticas_reales_atleta(athlete_id: str):
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
        "Puntos": ["avgpoints", "pointspergame", "pts", "points"],
        "Rebotes": ["avgrebounds", "reboundspergame", "reb", "rebounds"],
        "Asistencias": ["avgassists", "assistspergame", "ast", "assists"],
        "Triples": ["threepointfieldgoalsmadepergame", "avgthreepointfieldgoalsmade", "3pm"]
    }

    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=4)
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
                    res_stats[m_key] = round(vals[0], 1)

            _STATS_CACHE[athlete_id] = (now, res_stats)
    except Exception:
        pass

    return res_stats


def _calcular_prop_cuantitativa(media_real: float, tipo_prop: str):
    linea_casino = math.floor(media_real) + 0.5
    cuota_mercado = 1.88

    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.22 if tipo_prop == "Puntos" else 0.26
        sigma = max(1.2, media_real * cv)
        z = (linea_casino - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea_casino))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under
    prob_sel = max(0.46, min(0.68, prob_sel))

    ev = round(((prob_sel * cuota_mercado) - 1.0) * 100, 1)

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea_casino,
        "cuota": cuota_mercado,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": media_real
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_v3"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_NBA.get(local, "ind")
    abbr_vis = MAPEO_EQUIPOS_NBA.get(visitante, "was")

    roster_loc = obtener_roster_activo_espn(abbr_loc)
    roster_vis = obtener_roster_activo_espn(abbr_vis)

    # Analiza los 6 jugadores de mayor volumen por plantilla para optimizar tiempos de respuesta
    atletas_totales = [(a, abbr_loc) for a in roster_loc[:6]] + [(a, abbr_vis) for a in roster_vis[:6]]
    candidatas = []

    for atleta, eq_abbr in atletas_totales:
        stats = obtener_estadisticas_reales_atleta(atleta["id"])
        if not stats:
            continue

        for tipo_prop, media in stats.items():
            if tipo_prop == "Puntos" and media < 10.0: continue
            if tipo_prop == "Rebotes" and media < 4.5: continue
            if tipo_prop == "Asistencias" and media < 3.5: continue
            if tipo_prop == "Triples" and media < 1.5: continue

            calc = _calcular_prop_cuantitativa(media, tipo_prop)

            if calc["ev"] >= 1.5:
                candidatas.append({
                    "jugador": atleta["nombre"],
                    "equipo_abbr": eq_abbr,
                    "tipo_prop": tipo_prop,
                    "lado": calc["lado"],
                    "linea": calc["linea"],
                    "cuota": calc["cuota"],
                    "prob_real": calc["prob_real"],
                    "ev": calc["ev"],
                    "proyeccion": calc["proyeccion"]
                })

    candidatas.sort(key=lambda x: x["ev"], reverse=True)
    seleccion = candidatas[:top_n]

    _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
