import math
import time
import unicodedata
import requests
from kambi_feed import obtener_player_props_kambi

EQUIPOS_NFL_ESPN = {
    "Arizona Cardinals": ("ari", "22"), "Atlanta Falcons": ("atl", "1"), "Baltimore Ravens": ("bal", "33"),
    "Buffalo Bills": ("buf", "2"), "Carolina Panthers": ("car", "29"), "Chicago Bears": ("chi", "3"),
    "Cincinnati Bengals": ("cin", "4"), "Cleveland Browns": ("cle", "5"), "Dallas Cowboys": ("dal", "6"),
    "Denver Broncos": ("den", "7"), "Detroit Lions": ("det", "8"), "Green Bay Packers": ("gb", "9"),
    "Houston Texans": ("hou", "34"), "Indianapolis Colts": ("ind", "11"), "Jacksonville Jaguars": ("jax", "30"),
    "Kansas City Chiefs": ("kc", "12"), "Las Vegas Raiders": ("lv", "13"), "Los Angeles Chargers": ("lac", "24"),
    "Los Angeles Rams": ("lar", "14"), "Miami Dolphins": ("mia", "15"), "Minnesota Vikings": ("min", "16"),
    "New England Patriots": ("ne", "17"), "New Orleans Saints": ("no", "18"), "New York Giants": ("nyg", "19"),
    "New York Jets": ("nyj", "20"), "Philadelphia Eagles": ("phi", "21"), "Pittsburgh Steelers": ("pit", "23"),
    "San Francisco 49ers": ("sf", "25"), "Seattle Seahawks": ("sea", "26"), "Tampa Bay Buccaneers": ("tb", "27"),
    "Tennessee Titans": ("ten", "10"), "Washington Commanders": ("was", "28")
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

_CACHE_STATS_NFL = {}


def _normalizar_nombre(nombre: str) -> str:
    n = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8")
    return "".join(c for c in n.lower() if c.isalpha())


def _obtener_stats_equipo_nfl(team_id: str, abbr: str):
    """Extrae líderes y promedios reales de la temporada activa en ESPN por equipo."""
    ahora = time.time()
    if team_id in _CACHE_STATS_NFL and (ahora - _CACHE_STATS_NFL[team_id][0] < 1800):
        return _CACHE_STATS_NFL[team_id][1]

    jugadores = {}
    url_leaders = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}?enable=leaders"

    try:
        r = requests.get(url_leaders, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            team_data = r.json().get("team", {})
            record_items = team_data.get("record", {}).get("items", [])
            juegos_jugados = 1
            if record_items:
                stats_rec = record_items[0].get("stats", [])
                wins = next((s.get("value", 0) for s in stats_rec if s.get("name") == "wins"), 0)
                losses = next((s.get("value", 0) for s in stats_rec if s.get("name") == "losses"), 0)
                ties = next((s.get("value", 0) for s in stats_rec if s.get("name") == "ties"), 0)
                juegos_jugados = max(1, int(wins + losses + ties))

            for cat in team_data.get("leaders", []):
                c_name = str(cat.get("name", "")).lower()
                tipo = None
                if "passingyards" in c_name:
                    tipo = "Yardas Pase"
                elif "rushingyards" in c_name:
                    tipo = "Yardas Acarreo"
                elif "receivingyards" in c_name:
                    tipo = "Yardas Recepción"
                elif "receptions" in c_name:
                    tipo = "Recepciones"

                if not tipo:
                    continue

                for lead in cat.get("leaders", []):
                    nom = lead.get("athlete", {}).get("displayName")
                    try:
                        total_val = float(str(lead.get("value", 0)).replace(",", ""))
                    except ValueError:
                        continue

                    if nom and total_val > 0:
                        key = _normalizar_nombre(nom)
                        if key not in jugadores:
                            jugadores[key] = {"nombre": nom, "equipo": abbr.upper()}
                        # Si el valor viene acumulado de temporada, lo divide entre juegos disputados
                        per_game = total_val / juegos_jugados if total_val > 350 or (tipo == "Recepciones" and total_val > 15) else total_val
                        jugadores[key][tipo] = round(per_game, 1)
    except Exception as e:
        print(f"Error stats NFL {abbr}: {e}")

    if jugadores:
        _CACHE_STATS_NFL[team_id] = (ahora, jugadores)
    return jugadores


def _evaluar_prop_nfl(p_casino: dict, stats_equipos: dict, abbr_defecto: str):
    jugador_raw = p_casino["jugador"]
    tipo = p_casino["tipo_prop"]
    linea = float(p_casino["linea"])
    c_over = float(p_casino["cuota_over"])
    c_under = float(p_casino["cuota_under"])

    key_jug = _normalizar_nombre(jugador_raw)
    datos_atleta = stats_equipos.get(key_jug)

    # Probabilidad limpia de mercado (No-Vig)
    imp_over = 1.0 / c_over
    imp_under = 1.0 / c_under
    suma_imp = imp_over + imp_under
    prob_mkt_over = imp_over / suma_imp
    prob_mkt_under = imp_under / suma_imp

    equipo_abbr = datos_atleta["equipo"] if datos_atleta else abbr_defecto
    nombre_final = datos_atleta["nombre"] if datos_atleta else jugador_raw

    if datos_atleta and datos_atleta.get(tipo, 0) > 0:
        media_real = datos_atleta[tipo]
        sigma = max(2.2, media_real * 0.27)
        z = (linea - media_real) / sigma
        p_stat_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        p_stat_over = 1.0 - p_stat_under

        # Fusión 65% estadística real del jugador + 35% eficiencia del mercado
        prob_over = (p_stat_over * 0.65) + (prob_mkt_over * 0.35)
        prob_under = (p_stat_under * 0.65) + (prob_mkt_under * 0.35)
        proy_num = media_real
    else:
        prob_over = prob_mkt_over
        prob_under = prob_mkt_under
        proy_num = linea + (1.0 if prob_over > prob_under else -1.0)

    ev_over = (prob_over * c_over) - 1.0
    ev_under = (prob_under * c_under) - 1.0

    if ev_over >= ev_under and ev_over > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    elif ev_under > 0:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under
    elif prob_over >= prob_under:
        lado, prob_sel, cuota_sel, ev_sel = "MÁS DE", prob_over, c_over, ev_over
    else:
        lado, prob_sel, cuota_sel, ev_sel = "MENOS DE", prob_under, c_under, ev_under

    if prob_sel < 0.525:
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
        "ev": round(ev_sel * 100, 1),
        "proyeccion": proy,
        "_score": (prob_sel * 100 * 0.75) + (ev_sel * 100 * 0.25)
    }


def obtener_mejores_props_nfl(local: str, visitante: str, top_n: int = 6):
    props_casino = obtener_player_props_kambi("nfl", local, visitante)
    if not props_casino:
        return []

    d_loc = EQUIPOS_NFL_ESPN.get(local)
    d_vis = EQUIPOS_NFL_ESPN.get(visitante)

    stats_equipos = {}
    abbr_defecto = d_loc[0].upper() if d_loc else "NFL"

    if d_loc:
        stats_equipos.update(_obtener_stats_equipo_nfl(d_loc[1], d_loc[0]))
    if d_vis:
        stats_equipos.update(_obtener_stats_equipo_nfl(d_vis[1], d_vis[0]))

    candidatas = []
    for p in props_casino:
        res = _evaluar_prop_nfl(p, stats_equipos, abbr_defecto)
        if res:
            candidatas.append(res)

    candidatas.sort(key=lambda x: x["_score"], reverse=True)
    for c in candidatas:
        c.pop("_score", None)

    return candidatas[:top_n]
