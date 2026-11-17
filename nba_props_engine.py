import math
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from kambi_feed import obtener_player_props_kambi

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
    "Accept": "application/json"
}

_CACHE_STATS_NBA = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', str(nombre)).encode('ascii', 'ignore').decode("utf-8").lower()
    n = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', n)
    return "".join(c for c in n if c.isalpha())


def _seleccionar_split_temporada(splits: list) -> list:
    """
    Elige el split de Temporada Regular actual en lugar de tomar splits[0] a ciegas.
    """
    if not splits:
        return []
    for sp in splits:
        disp = str(sp.get("displayName", "")).lower()
        if "regular" in disp and "career" not in disp:
            return sp.get("stats", [])
    return splits[0].get("stats", [])


def _obtener_promedios_atleta_nba(athlete_id: str) -> dict:
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/overview"
    res = {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code != 200:
            return res
        stats_block = r.json().get("statistics", {})
        names = stats_block.get("names", [])
        splits = stats_block.get("splits", [])
        if not names or not splits:
            return res

        fila_stats = _seleccionar_split_temporada(splits)
        for idx, col_name in enumerate(names):
            if idx >= len(fila_stats):
                break
            try:
                val = float(str(fila_stats[idx]).replace(",", ""))
            except ValueError:
                continue
            col_low = col_name.lower()
            if col_low in ["gamesplayed", "gp"]:
                res["GP"] = val
            elif col_low in ["avgminutes", "min", "mpg"]:
                res["MPG"] = val
            elif col_low in ["avgpoints", "pts"]:
                res["Puntos"] = round(val, 1)
            elif col_low in ["avgrebounds", "reb"]:
                res["Rebotes"] = round(val, 1)
            elif col_low in ["avgassists", "ast"]:
                res["Asistencias"] = round(val, 1)
            elif col_low in ["avgthreepointfieldgoalsmade", "3pm"]:
                res["Triples"] = round(val, 1)

        pts = res.get("Puntos", 0.0)
        reb = res.get("Rebotes", 0.0)
        ast = res.get("Asistencias", 0.0)
        if pts > 0 or reb > 0 or ast > 0:
            res["P+R+A"] = round(pts + reb + ast, 1)

    except Exception:
        pass
    return res


def _obtener_stats_reales_nba(team_id: str, abbr: str):
    ahora = time.time()
    cache_key = f"v2_{team_id}"
    if cache_key in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[cache_key][0] < 3600):
        return _CACHE_STATS_NBA[cache_key][1]

    jugadores = {}
    url_roster = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
    try:
        r_ros = requests.get(url_roster, headers=HEADERS, timeout=6)
        if r_ros.status_code == 200:
            athletes = r_ros.json().get("athletes", [])
            activos = []
            for ath in athletes:
                if not isinstance(ath, dict):
                    continue
                injuries = ath.get("injuries", [])
                esta_fuera = any("out" in str(inj.get("status", "")).lower() for inj in injuries)
                if esta_fuera:
                    continue
                nom = ath.get("displayName") or ath.get("fullName")
                aid = str(ath.get("id", ""))
                if nom and aid:
                    activos.append((aid, nom))

            # Consulta paralela de toda la plantilla activa para incluir titulares y estrellas sin importar orden alfabético
            with ThreadPoolExecutor(max_workers=8) as executor:
                futuros = {
                    executor.submit(_obtener_promedios_atleta_nba, aid): (aid, nom)
                    for aid, nom in activos[:16]
                }
                for fut in as_completed(futuros):
                    _, nom = futuros[fut]
                    try:
                        proms = fut.result()
                    except Exception:
                        proms = {}

                    if not proms:
                        continue

                    gp = proms.get("GP", 10)
                    mpg = proms.get("MPG", 20.0)
                    # Filtra jugadores marginales o muestras mínimas que distorsionan promedios
                    if gp < 4 or mpg < 15.0:
                        continue

                    key = _normalizar_nombre(nom)
                    jugadores[key] = {"nombre": nom, "equipo": abbr.upper(), **proms}

    except Exception as e:
        print(f"Error roster/stats NBA {abbr}: {e}")

    if jugadores:
        _CACHE_STATS_NBA[cache_key] = (ahora, jugadores)
    return jugadores


def _buscar_atleta_exacto(jugador_raw: str, stats_totales: dict):
    """
    Cruza el nombre del casino exclusivamente contra jugadores reales de los dos equipos
    del partido, evitando cruces erróneos entre jugadores de otros equipos.
    """
    key_norm = _normalizar_nombre(jugador_raw)
    if key_norm in stats_totales:
        return stats_totales[key_norm]

    partes = [
        _normalizar_nombre(p) for p in re.split(r'\s+', str(jugador_raw).strip())
        if _normalizar_nombre(p)
    ]
    if len(partes) >= 2:
        nombre_apellido = partes[0] + partes[-1]
        if nombre_apellido in stats_totales:
            return stats_totales[nombre_apellido]

    return None


def _parametros_dispersion_nba(tipo: str, media_real: float) -> float:
    if tipo == "Puntos":
        return max(2.8, media_real * 0.34)
    if tipo == "Rebotes":
        return max(1.6, media_real * 0.38)
    if tipo == "Asistencias":
        return max(1.4, media_real * 0.42)
    if tipo == "P+R+A":
        return max(3.8, media_real * 0.28)
    return max(1.5, media_real * 0.35)


def _evaluar_prop_nba(p_casino: dict, stats_totales: dict):
    jugador_raw = p_casino["jugador"]
    tipo = p_casino["tipo_prop"]
    if tipo not in ["Puntos", "Rebotes", "Asistencias", "P+R+A"]:
        return None

    linea = float(p_casino["linea"])
    c_over = float(p_casino["cuota_over"])
    c_under = float(p_casino.get("cuota_under") or 1.90)

    datos_atleta = _buscar_atleta_exacto(jugador_raw, stats_totales)
    if not datos_atleta:
        return None

    media_real = float(datos_atleta.get(tipo, 0.0))
    min_requerido = 10.0 if tipo == "P+R+A" else 3.0
    if media_real < min_requerido:
        return None

    # Si la línea del casino difiere más del 55% del promedio histórico (ej. cambio brusco de titularidad por lesión), se descarta
    tolerancia_cambio_rol = max(6.5, media_real * 0.55)
    if abs(media_real - linea) > tolerancia_cambio_rol:
        return None

    equipo_abbr = datos_atleta["equipo"]
    nombre_final = datos_atleta["nombre"]

    # Probabilidad estadística 100% pura derivada de promedios reales en ESPN (sin tocar cuotas del casino)
    sigma = _parametros_dispersion_nba(tipo, media_real)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    # Las cuotas del casino se usan exclusivamente al final para calcular +EV
    ev_over = (prob_over * c_over) - 1.0
    ev_under = (prob_under * c_under) - 1.0

    if ev_over >= ev_under and 0.02 <= ev_over <= 0.35 and prob_over >= 0.54:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    elif 0.02 <= ev_under <= 0.35 and prob_under >= 0.54:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under
    else:
        return None

    proy_redondeada = round(media_real, 1)
    if lado == "MÁS DE" and proy_redondeada <= linea:
        proy_redondeada = round(linea + 0.5, 1)
    elif lado == "MENOS DE" and proy_redondeada >= linea:
        proy_redondeada = round(max(0.5, linea - 0.5), 1)

    return {
        "jugador": nombre_final,
        "equipo_abbr": equipo_abbr,
        "tipo_prop": tipo,
        "lado": lado,
        "linea": linea,
        "cuota": round(cuota_sel, 2),
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy_redondeada,
        "_score": (prob_sel * 100 * 0.65) + (ev_sel * 100 * 0.35)
    }


def _seleccionar_top_diversificado(candidatas: list, top_n: int) -> list:
    """
    Garantiza que no se repita ningún jugador ni mercado duplicado y promueve
    variedad entre Puntos, Rebotes, Asistencias y P+R+A.
    """
    if not candidatas:
        return []

    candidatas.sort(key=lambda x: x["_score"], reverse=True)

    # 1. Deduplicación estricta por (jugador, tipo_prop)
    unicas_por_mercado = []
    vistos_par = set()
    for c in candidatas:
        clave_par = (_normalizar_nombre(c["jugador"]), c["tipo_prop"])
        if clave_par in vistos_par:
            continue
        vistos_par.add(clave_par)
        unicas_por_mercado.append(c)

    # 2. Primera pasada: máximo 1 tarjeta por jugador, priorizando cubrir distintos tipos de prop
    seleccionadas = []
    jugadores_usados = set()
    mercados_cubiertos = set()

    for tipo_objetivo in ["P+R+A", "Puntos", "Asistencias", "Rebotes"]:
        for c in unicas_por_mercado:
            jug_key = _normalizar_nombre(c["jugador"])
            if jug_key in jugadores_usados:
                continue
            if c["tipo_prop"] == tipo_objetivo and tipo_objetivo not in mercados_cubiertos:
                seleccionadas.append(c)
                jugadores_usados.add(jug_key)
                mercados_cubiertos.add(tipo_objetivo)
                break

    # 3. Completar hasta top_n con los mejores restantes de jugadores distintos
    for c in unicas_por_mercado:
        if len(seleccionadas) >= top_n:
            break
        jug_key = _normalizar_nombre(c["jugador"])
        if jug_key in jugadores_usados:
            continue
        seleccionadas.append(c)
        jugadores_usados.add(jug_key)

    seleccionadas.sort(key=lambda x: x["_score"], reverse=True)
    for item in seleccionadas:
        item.pop("_score", None)

    return seleccionadas[:top_n]


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    d_loc = EQUIPOS_NBA_ESPN.get(local)
    d_vis = EQUIPOS_NBA_ESPN.get(visitante)
    if not d_loc or not d_vis:
        return []

    stats_totales = {
        **_obtener_stats_reales_nba(d_loc[1], d_loc[0]),
        **_obtener_stats_reales_nba(d_vis[1], d_vis[0])
    }
    props_casino = obtener_player_props_kambi("nba", local, visitante)

    candidatas = []
    if props_casino:
        for p in props_casino:
            res = _evaluar_prop_nba(p, stats_totales)
            if res:
                candidatas.append(res)

    # Respaldo estadístico puro en vivo si el casino aún no abre líneas de jugadores
    if not candidatas and stats_totales:
        for ath in stats_totales.values():
            for tipo, min_val in [("P+R+A", 16.0), ("Puntos", 11.0), ("Rebotes", 5.5), ("Asistencias", 4.5)]:
                media = float(ath.get(tipo, 0.0))
                if media < min_val:
                    continue
                linea_est = math.floor(media * 0.90) + 0.5
                sigma = _parametros_dispersion_nba(tipo, media)
                z = (linea_est - media) / sigma
                prob_over = 1.0 - (0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
                if prob_over >= 0.57:
                    cuota_ref = round(max(1.58, min(1.91, (1.0 / prob_over) * 1.04)), 2)
                    ev_ref = (prob_over * cuota_ref) - 1.0
                    candidatas.append({
                        "jugador": ath["nombre"],
                        "equipo_abbr": ath["equipo"],
                        "tipo_prop": tipo,
                        "lado": "MÁS DE",
                        "linea": linea_est,
                        "cuota": cuota_ref,
                        "prob_real": round(prob_over * 100, 1),
                        "ev": round(ev_ref * 100, 1),
                        "proyeccion": round(media, 1),
                        "_score": (prob_over * 100 * 0.65) + (ev_ref * 100 * 0.35)
                    })

    return _seleccionar_top_diversificado(candidatas, top_n)
