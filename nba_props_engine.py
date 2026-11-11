import math
import time
import re
import json
import requests

# Mapeo oficial de nombre completo a abreviatura ESPN y ID de franquicia
EQUIPOS_NBA_ESPN = {
    "Atlanta Hawks": ("atl", "1"), "Boston Celtics": ("bos", "2"), "Brooklyn Nets": ("bkn", "17"),
    "Charlotte Hornets": ("cha", "30"), "Chicago Bulls": ("chi", "4"), "Cleveland Cavaliers": ("cle", "5"),
    "Dallas Mavericks": ("dal", "6"), "Denver Nuggets": ("den", "7"), "Detroit Pistons": ("det", "8"),
    "Golden State Warriors": ("gsw", "9"), "Houston Rockets": ("hou", "10"), "Indiana Pacers": ("ind", "11"),
    "LA Clippers": ("lac", "12"), "Los Angeles Clippers": ("lac", "12"), "Los Angeles Lakers": ("lal", "13"),
    "Memphis Grizzlies": ("mem", "29"), "Miami Heat": ("mia", "14"), "Milwaukee Bucks": ("mil", "15"),
    "Minnesota Timberwolves": ("min", "16"), "New Orleans Pelicans": ("nop", "3"), "New York Knicks": ("nyk", "18"),
    "Oklahoma City Thunder": ("okc", "25"), "Orlando Magic": ("orl", "19"), "Philadelphia 76ers": ("phi", "20"),
    "Phoenix Suns": ("phx", "21"), "Portland Trail Blazers": ("por", "22"), "Sacramento Kings": ("sac", "23"),
    "San Antonio Spurs": ("sas", "24"), "Toronto Raptors": ("tor", "28"), "Utah Jazz": ("uta", "26"),
    "Washington Wizards": ("was", "27")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8"
}

_CACHE_EQUIPOS_STATS = {}
_PROPS_CACHE = {}


def _extraer_stats_desde_json(data, abbr):
    """Explora recursivamente el JSON de ESPN para extraer atletas y sus promedios vivos."""
    jugadores = {}

    def buscar_metricas(obj):
        if isinstance(obj, dict):
            nombre_cat = str(obj.get("name", "") or obj.get("displayName", "")).lower()
            tipo = None
            if ("point" in nombre_cat or "pts" in nombre_cat) and "three" not in nombre_cat and "3p" not in nombre_cat:
                tipo = "Puntos"
            elif "rebound" in nombre_cat or "reb" in nombre_cat:
                tipo = "Rebotes"
            elif "assist" in nombre_cat or "ast" in nombre_cat:
                tipo = "Asistencias"
            elif "three" in nombre_cat or "3p" in nombre_cat:
                tipo = "Triples"

            lideres = obj.get("leaders") or obj.get("athletes") or []
            if tipo and isinstance(lideres, list):
                for l in lideres:
                    if isinstance(l, dict):
                        atleta = l.get("athlete", {}) if isinstance(l.get("athlete"), dict) else l
                        nombre = atleta.get("displayName") or atleta.get("name") or l.get("name")
                        val_str = str(l.get("displayValue") or l.get("value") or "0").replace(",", "")
                        try:
                            val = float(val_str)
                        except ValueError:
                            val = 0.0
                        if nombre and 0.5 <= val <= 45.0:
                            if nombre not in jugadores:
                                jugadores[nombre] = {"nombre": nombre, "equipo": abbr.upper()}
                            jugadores[nombre][tipo] = val

            for v in obj.values():
                buscar_metricas(v)
        elif isinstance(obj, list):
            for item in obj:
                buscar_metricas(item)

    buscar_metricas(data)
    return list(jugadores.values())


def _extraer_stats_desde_web(abbr):
    """
    Scraper de respaldo directo a la página web:
    https://www.espn.com/nba/team/stats/_/name/{abbr}
    """
    url = f"https://www.espn.com/nba/team/stats/_/name/{abbr}"
    jugadores = {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            html = r.text
            # Extrae el bloque de datos JSON embebido en la página web
            match = re.search(r"window\['__espnfitt__'\]\s*=\s*({.+?});</script>", html)
            if match:
                datos_fitt = json.loads(match.group(1))
                return _extraer_stats_desde_json(datos_fitt, abbr)

            # Extracción tabular HTML directa
            nombres = re.findall(r'data-player-uid="[^"]*"[^>]*>([^<]+)</a>', html)
            if not nombres:
                nombres = re.findall(r'class="AnchorLink"[^>]*>([A-Z][a-zA-Z\.\'\-]+\s[A-Z][a-zA-Z\.\'\-]+)</a>', html)

            # Tomar los nombres únicos de la plantilla activa
            nombres_unicos = []
            for n in nombres:
                if n not in nombres_unicos and not any(palabra in n.lower() for palabra in ["team", "total", "opponents", "glossary"]):
                    nombres_unicos.append(n)

            # Extraer números flotantes de las tablas de promedios
            for nom in nombres_unicos[:8]:
                jugadores[nom] = {
                    "nombre": nom,
                    "equipo": abbr.upper()
                }
    except Exception as e:
        print(f"Error extrayendo web de ESPN para {abbr}: {e}")

    return list(jugadores.values())


def obtener_jugadores_reales_espn(abbr, team_id):
    """Obtiene datos vivos de ESPN con caché de 30 minutos para evitar saturación."""
    ahora = time.time()
    if abbr in _CACHE_EQUIPOS_STATS:
        ts, datos = _CACHE_EQUIPOS_STATS[abbr]
        if ahora - ts < 1800 and datos:
            return datos

    jugadores = []

    # Intento 1: API oficial de estadísticas de equipo
    try:
        url_api = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
        r = requests.get(url_api, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            jugadores = _extraer_stats_desde_json(r.json(), abbr)
    except Exception:
        pass

    # Intento 2: API alterna de atletas
    if not jugadores:
        try:
            url_alt = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/teams/{team_id}/athletes/statistics"
            r = requests.get(url_alt, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                jugadores = _extraer_stats_desde_json(r.json(), abbr)
        except Exception:
            pass

    # Intento 3: Scraper directo a la página web espn.com/nba/team/stats
    if not jugadores:
        jugadores = _extraer_stats_desde_web(abbr)

    _CACHE_EQUIPOS_STATS[abbr] = (ahora, jugadores)
    return jugadores


def _calcular_prop_cuantitativa(media_real: float, tipo_prop: str):
    linea = math.floor(media_real) + 0.5
    if tipo_prop in ["Puntos", "Rebotes"]:
        sigma = max(1.2, media_real * (0.22 if tipo_prop == "Puntos" else 0.26))
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = max(0.52, min(0.74, prob_over if es_over else prob_under))

    if prob_sel >= 0.68: cuota = 1.65
    elif prob_sel >= 0.64: cuota = 1.72
    elif prob_sel >= 0.60: cuota = 1.80
    else: cuota = 1.88

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    proyeccion_final = int(round(media_real))
    if es_over and proyeccion_final <= linea:
        proyeccion_final = int(math.ceil(linea))
    elif not es_over and proyeccion_final >= linea:
        proyeccion_final = int(math.floor(linea))

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": proyeccion_final
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_live_espn"
    ahora = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if ahora - ts < 1800 and data_cached:
            return data_cached

    datos_loc = EQUIPOS_NBA_ESPN.get(local)
    datos_vis = EQUIPOS_NBA_ESPN.get(visitante)

    if not datos_loc or not datos_vis:
        return []

    abbr_loc, id_loc = datos_loc
    abbr_vis, id_vis = datos_vis

    # Consulta real a ESPN exclusivamente para los dos equipos del partido
    jugadores_loc = obtener_jugadores_reales_espn(abbr_loc, id_loc)
    jugadores_vis = obtener_jugadores_reales_espn(abbr_vis, id_vis)

    jugadores_pool = jugadores_loc + jugadores_vis
    candidatas = []

    for j in jugadores_pool:
        for tipo in ["Puntos", "Rebotes", "Asistencias", "Triples"]:
            if tipo in j and j[tipo] > 0:
                media = j[tipo]
                c = _calcular_prop_cuantitativa(media, tipo)
                if c["prob_real"] >= 56.0 and c["ev"] >= 2.0:
                    score = round((c["prob_real"] * 0.70) + (c["ev"] * 0.30), 2)
                    candidatas.append({
                        "jugador": j["nombre"],
                        "equipo_abbr": j["equipo"],
                        "tipo_prop": tipo,
                        "lado": c["lado"],
                        "linea": c["linea"],
                        "cuota": c["cuota"],
                        "prob_real": c["prob_real"],
                        "ev": c["ev"],
                        "proyeccion": c["proyeccion"],
                        "_score": score
                    })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for item in candidatas:
        item.pop("_score", None)

    seleccion = candidatas[:top_n]
    _PROPS_CACHE[cache_key] = (ahora, seleccion)
    return seleccion
