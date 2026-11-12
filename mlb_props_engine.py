import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

HEADERS_NBA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*"
}

_CACHE_LIGA_NBA = {"ts": 0, "data": {}}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_stats_nba_oficial():
    """Descarga en 1 sola petición todas las estadísticas reales por juego de la NBA."""
    ahora = time.time()
    if _CACHE_LIGA_NBA["data"] and (ahora - _CACHE_LIGA_NBA["ts"] < 3600):
        return _CACHE_LIGA_NBA["data"]

    jugadores = {}
    url = "https://stats.nba.com/stats/leaguedashplayerstats?MeasureType=Base&PerMode=PerGame&PlusMinus=N&PaceAdjust=N&Rank=N&Season=2025-26&SeasonType=Regular%20Season&LeagueID=00"
    try:
        r = requests.get(url, headers=HEADERS_NBA, timeout=6)
        if r.status_code == 200:
            res_sets = r.json().get("resultSets", [{}])[0]
            headers = res_sets.get("headers", [])
            rows = res_sets.get("rowSet", [])

            idx_nom = headers.index("PLAYER_NAME")
            idx_tm = headers.index("TEAM_ABBREVIATION")
            idx_pts = headers.index("PTS")
            idx_reb = headers.index("REB")
            idx_ast = headers.index("AST")
            idx_fg3m = headers.index("FG3M")

            for row in rows:
                nom = row[idx_nom]
                key = _normalizar_nombre(nom)
                jugadores[key] = {
                    "nombre": nom,
                    "equipo": row[idx_tm],
                    "Puntos": float(row[idx_pts]),
                    "Rebotes": float(row[idx_reb]),
                    "Asistencias": float(row[idx_ast]),
                    "Triples": float(row[idx_fg3m])
                }
    except Exception as e:
        print(f"Error stats.nba.com: {e}")

    if jugadores:
        _CACHE_LIGA_NBA["ts"] = ahora
        _CACHE_LIGA_NBA["data"] = jugadores
    return jugadores


def _evaluar_prop_nba(p_casino: dict, stats_liga: dict):
    jugador_raw = p_casino["jugador"]
    tipo = p_casino["tipo_prop"]
    linea = float(p_casino["linea"])
    c_over = float(p_casino["cuota_over"])
    c_under = float(p_casino["cuota_under"])

    key_jug = _normalizar_nombre(jugador_raw)
    datos_atleta = stats_liga.get(key_jug)

    # Probabilidad implícita real libre de comisión del casino (No-Vig)
    imp_over = 1.0 / c_over
    imp_under = 1.0 / c_under
    suma_imp = imp_over + imp_under
    prob_mercado_over = imp_over / suma_imp
    prob_mercado_under = imp_under / suma_imp

    equipo_abbr = datos_atleta["equipo"] if datos_atleta else "NBA"
    nombre_final = datos_atleta["nombre"] if datos_atleta else jugador_raw

    if datos_atleta and datos_atleta.get(tipo, 0) > 0:
        media_real = datos_atleta[tipo]
        if tipo in ["Puntos", "Rebotes"]:
            cv = 0.21 if tipo == "Puntos" else 0.25
            sigma = max(1.1, media_real * cv)
            z = (linea - media_real) / sigma
            p_stat_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
            p_stat_over = 1.0 - p_stat_under
        else:
            lamb = media_real
            k_max = int(math.floor(linea))
            p_stat_under = sum((math.exp(-lamb) * (lamb ** k)) / math.factorial(k) for k in range(k_max + 1))
            p_stat_over = 1.0 - p_stat_under

        # Fusión Bayesiana: 65% estadística real del jugador + 35% eficiencia del mercado
        prob_over = (p_stat_over * 0.65) + (prob_mercado_over * 0.35)
        prob_under = (p_stat_under * 0.65) + (prob_mercado_under * 0.35)
        proy_num = media_real
    else:
        # Si el jugador es novato o aún no está en tabla acumulada, usa la probabilidad limpia del mercado
        prob_over = prob_mercado_over
        prob_under = prob_mercado_under
        proy_num = linea + (0.6 if prob_over > prob_under else -0.6)

    ev_over = (prob_over * c_over) - 1.0
    ev_under = (prob_under * c_under) - 1.0

    # Seleccionar el lado con ventaja real (+EV) o mayor probabilidad segura
    if ev_over >= ev_under and ev_over > -0.02:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    elif ev_under > -0.02:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under
    else:
        return None

    proy = int(round(proy_num))
    if lado == "MÁS DE" and proy <= linea:
        proy = int(math.ceil(linea))
    elif lado == "MENOS DE" and proy >= linea:
        proy = int(math.floor(linea))

    return {
        "jugador": nombre_final,
        "equipo_abbr": equipo_abbr,
        "tipo_prop": tipo,
        "lado": lado,
        "linea": linea,
        "cuota": cuota_sel,
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(max(0.5, ev_sel * 100), 1),
        "proyeccion": proy,
        "_score": (prob_sel * 100 * 0.75) + (ev_sel * 100 * 0.25)
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    # 1. Extraer las props reales abiertas en Kambi/Rushbet (ej. las 53 encontradas)
    props_casino = obtener_player_props_kambi("nba", local, visitante)
    if not props_casino:
        return []

    # 2. Descargar estadísticas oficiales de la NBA
    stats_liga = _obtener_stats_nba_oficial()

    candidatas = []
    for p in props_casino:
        res = _evaluar_prop_nba(p, stats_liga)
        if res and res["prob_real"] >= 53.0:
            candidatas.append(res)

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
