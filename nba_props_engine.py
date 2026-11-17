import math
import re
import time
import unicodedata
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

        fila_stats = splits[0].get("stats", [])
        for idx, col_name in enumerate(names):
            if idx >= len(fila_stats):
                break
            try:
                val = float(str(fila_stats[idx]).replace(",", ""))
            except ValueError:
                continue
            col_low = col_name.lower()
            if col_low in ["avgpoints", "pts"]:
                res["Puntos"] = round(val, 1)
            elif col_low in ["avgrebounds", "reb"]:
                res["Rebotes"] = round(val, 1)
            elif col_low in ["avgassists", "ast"]:
                res["Asistencias"] = round(val, 1)
            elif col_low in ["avgthreepointfieldgoalsmade", "3pm"]:
                res["Triples"] = round(val, 1)
    except Exception:
        pass
    return res


def _obtener_stats_reales_nba(team_id: str, abbr: str):
    ahora = time.time()
    if team_id in _CACHE_STATS_NBA and (ahora - _CACHE_STATS_NBA[team_id][0] < 3600):
        return _CACHE_STATS_NBA[team_id][1]

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

            for aid, nom in activos[:10]:
                key = _normalizar_nombre(nom)
                proms = _obtener_promedios_atleta_nba(aid)
                if proms:
                    jugadores[key] = {"nombre": nom, "equipo": abbr.upper(), **proms}
    except Exception as e:
        print(f"Error roster/stats NBA {abbr}: {e}")

    if jugadores:
        _CACHE_STATS_NBA[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nba(p_casino: dict, stats_totales: dict, abbr_defecto: str):
    jugador_raw = p_casino["jugador"]
    tipo = p_casino["tipo_prop"]
    linea = float(p_casino["linea"])
    c_over = float(p_casino["cuota_over"])
    c_under = float(p_casino.get("cuota_under") or 1.90)

    key_norm = _normalizar_nombre(jugador_raw)
    datos_atleta = stats_totales.get(key_norm)

    if not datos_atleta and len(key_norm) >= 6:
        for k, v in stats_totales.items():
            if key_norm[-5:] == k[-5:] and key_norm[0] == k[0]:
                datos_atleta = v
                break

    if not datos_atleta:
        return None

    media_real = datos_atleta.get(tipo, 0)
    if media_real <= 0:
        return None

    equipo_abbr = datos_atleta["equipo"]
    nombre_final = datos_atleta["nombre"]

    # Probabilidad estadística 100% pura derivada de los promedios reales en ESPN (sin tocar cuotas del casino)
    cv = 0.24 if tipo == "Puntos" else 0.28
    sigma = max(1.2, media_real * cv)
    z = (linea - media_real) / sigma
    prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    prob_over = 1.0 - prob_under

    # Las cuotas del casino se usan únicamente al final para calcular el +EV
    ev_over = (prob_over * c_over) - 1.0
    ev_under = (prob_under * c_under) - 1.0

    if ev_over >= ev_under and ev_over > 0.01 and prob_over >= 0.53:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    elif ev_under > 0.01 and prob_under >= 0.53:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under
    else:
        return None

    proy = int(round(media_real))
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
        "cuota": round(cuota_sel, 2),
        "prob_real": round(prob_sel * 100, 1),
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy,
        "_score": (prob_sel * 100 * 0.65) + (ev_sel * 100 * 0.35)
    }


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
            res = _evaluar_prop_nba(p, stats_totales, d_loc[0].upper())
            if res:
                candidatas.append(res)

    # Respaldo estadístico puro en vivo si el casino aún no abre líneas de jugadores
    if not candidatas and stats_totales:
        for ath in stats_totales.values():
            for tipo in ["Puntos", "Rebotes", "Asistencias"]:
                media = ath.get(tipo, 0)
                if media < 5.5:
                    continue
                linea_est = math.floor(media * 0.88) + 0.5
                cv = 0.24 if tipo == "Puntos" else 0.28
                sigma = max(1.2, media * cv)
                z = (linea_est - media) / sigma
                prob_over = 1.0 - (0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
                if prob_over >= 0.58:
                    cuota_ref = round(max(1.55, min(1.91, (1.0 / prob_over) * 1.04)), 2)
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
                        "proyeccion": int(round(media)),
                        "_score": (prob_over * 100 * 0.65) + (ev_ref * 100 * 0.35)
                    })

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
