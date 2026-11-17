import os
import time
from datetime import datetime, timedelta
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "").strip()
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "").strip()
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "").strip()

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

_CACHE = {}


def fetch_cached(key: str, ttl: int = 3600):
    now = time.time()
    if key in _CACHE and (now - _CACHE[key]["time"]) < ttl:
        return _CACHE[key]["data"]
    return None


def set_cached(key: str, data):
    _CACHE[key] = {"time": time.time(), "data": data}


def get_live_weather(ciudad: str):
    """Clima real en vivo por ciudad desde OpenWeatherMap."""
    cached = fetch_cached(f"weather_{ciudad}", ttl=1800)
    if cached:
        return cached
    if not OPENWEATHER_KEY or not ciudad:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": ciudad, "appid": OPENWEATHER_KEY, "units": "imperial"}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            d = r.json()
            res = {
                "temp_f": float(d["main"].get("temp", 70.0)),
                "viento_mph": float(d["wind"].get("speed", 0.0)),
                "humedad": float(d["main"].get("humidity", 50.0))
            }
            set_cached(f"weather_{ciudad}", res)
            return res
    except Exception as e:
        print(f"Error OpenWeather: {e}")
    return None


def _combinar_temporadas_dinamico(stats_pasada: dict, stats_actual: dict, juegos_full_temporada: int) -> dict:
    """
    Ponderación Bayesiana Dinámica:
    Combina la temporada pasada (2025-2026) con la actual (2026-2027) según cuántos juegos
    lleva cada equipo. Conforme avanzan los partidos, el peso de 2026-2027 sube automáticamente.
    """
    todos_abbr = set(stats_pasada.keys()) | set(stats_actual.keys())
    combinado = {}

    for abbr in todos_abbr:
        s_old = stats_pasada.get(abbr)
        s_new = stats_actual.get(abbr)

        if s_new and not s_old:
            combinado[abbr] = s_new
            continue
        if s_old and not s_new:
            combinado[abbr] = s_old
            continue

        gp_actual = s_new.get("gp", 0)
        w_new = min(0.88, max(0.20, gp_actual / (juegos_full_temporada * 0.55)))
        w_old = 1.0 - w_new

        entry = {"gp": gp_actual, "peso_actual": round(w_new * 100)}
        for campo in s_new:
            if campo in ["gp", "peso_actual", "jugo_ayer"]:
                continue
            val_new = s_new.get(campo, 0.0)
            val_old = s_old.get(campo, val_new)
            entry[campo] = (val_new * w_new) + (val_old * w_old)

        if "jugo_ayer" in s_new:
            entry["jugo_ayer"] = s_new["jugo_ayer"]

        combinado[abbr] = entry

    return combinado


# =====================================================================
# 1. NHL: TEMPORADA 2025-2026 + 2026-2027 REALES (SV%, PP%, PK%, TIROS, ELO DINÁMICO)
# =====================================================================
def _obtener_stats_avanzadas_nhl(season_id: int) -> dict:
    url = (
        f"https://api.nhle.com/stats/rest/en/team/summary?isAggregate=false&isGame=false"
        f"&sort=%5B%7B%22property%22:%22points%22,%22direction%22:%22DESC%22%7D%5D"
        f"&start=0&limit=50&cayenneExp=seasonId={season_id}%20and%20gameTypeId=2"
    )
    datos = {}
    name_to_abbr = {
        "Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF",
        "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI",
        "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL",
        "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM", "Florida Panthers": "FLA",
        "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montréal Canadiens": "MTL",
        "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
        "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
        "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
        "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
        "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Utah Mammoth": "UTA",
        "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH",
        "Winnipeg Jets": "WPG"
    }
    try:
        r = requests.get(url, headers=HEADERS_API, timeout=8)
        if r.status_code == 200:
            for row in r.json().get("data", []):
                t_name = row.get("teamFullName", "")
                abbr = name_to_abbr.get(t_name)
                if not abbr:
                    continue
                gp = max(1, int(row.get("gamesPlayed", 1)))
                datos[abbr] = {
                    "gp": gp,
                    "gf_pg": float(row.get("goalsForPerGame", 3.1)),
                    "ga_pg": float(row.get("goalsAgainstPerGame", 3.1)),
                    "sf_pg": float(row.get("shotsForPerGame", 30.0)),
                    "sa_pg": float(row.get("shotsAgainstPerGame", 30.0)),
                    "pp_pct": float(row.get("powerPlayPct", 0.21)) * 100.0,
                    "pk_pct": float(row.get("penaltyKillPct", 0.80)) * 100.0,
                    "win_pct": float(row.get("pointPct", 0.50))
                }
    except Exception as e:
        print(f"Error NHL Stats REST ({season_id}): {e}")
    return datos


def _obtener_sv_porteros_nhl(abbr: str, season_str: str = "now") -> float:
    url = f"https://api-web.nhle.com/v1/club-stats/{abbr.lower()}/{season_str}"
    try:
        r = requests.get(url, headers=HEADERS_API, timeout=5)
        if r.status_code == 200:
            goalies = r.json().get("goalies", [])
            total_sa = 0.0
            total_saves = 0.0
            for g in goalies:
                sa = float(g.get("shotsAgainst", 0))
                sv_pct = float(g.get("savePctg", 0))
                if sa > 0 and sv_pct > 0.75:
                    total_sa += sa
                    total_saves += (sa * sv_pct)
            if total_sa > 0:
                return round(total_saves / total_sa, 4)
    except Exception:
        pass
    return 0.903


def _parsear_standings_nhl(url: str) -> dict:
    res = {}
    try:
        r = requests.get(url, headers=HEADERS_API, timeout=8)
        if r.status_code == 200:
            for st in r.json().get("standings", []):
                abbr = st.get("teamAbbrev", {}).get("default", "").upper()
                gp = max(1, int(st.get("gamesPlayed", 1)))
                home_gp = max(1, int(st.get("homeGamesPlayed", 1)))
                road_gp = max(1, int(st.get("roadGamesPlayed", 1)))
                l10_gp = max(1, int(st.get("l10GamesPlayed", 10)))
                res[abbr] = {
                    "gp": gp,
                    "gf_pg": float(st.get("goalFor", 0)) / gp,
                    "ga_pg": float(st.get("goalAgainst", 0)) / gp,
                    "win_pct": int(st.get("wins", 0)) / gp,
                    "home_gf_pg": float(st.get("homeGoalsFor", 0)) / home_gp,
                    "home_ga_pg": float(st.get("homeGoalsAgainst", 0)) / home_gp,
                    "road_gf_pg": float(st.get("roadGoalsFor", 0)) / road_gp,
                    "road_ga_pg": float(st.get("roadGoalsAgainst", 0)) / road_gp,
                    "l10_pct": int(st.get("l10Wins", 5)) / l10_gp
                }
    except Exception as e:
        print(f"Error NHL Standings ({url}): {e}")
    return res


def get_nhl_real_dataset():
    cached = fetch_cached("nhl_real_dataset_full_v5", ttl=3600)
    if cached:
        return cached

    st_25_26 = _parsear_standings_nhl("https://api-web.nhle.com/v1/standings/2026-04-16")
    st_26_27 = _parsear_standings_nhl("https://api-web.nhle.com/v1/standings/now")

    adv_25_26 = _obtener_stats_avanzadas_nhl(20252026)
    adv_26_27 = _obtener_stats_avanzadas_nhl(20262027)

    equipos_keys = list(st_26_27.keys()) if st_26_27 else list(st_25_26.keys())
    sv_25_26 = {abbr: _obtener_sv_porteros_nhl(abbr, "20252026/2") for abbr in equipos_keys}
    sv_26_27 = {abbr: _obtener_sv_porteros_nhl(abbr, "now") for abbr in equipos_keys}

    full_25_26 = {}
    for abbr, base in st_25_26.items():
        adv = adv_25_26.get(abbr, {})
        full_25_26[abbr] = {
            **base,
            "sf_pg": adv.get("sf_pg", 30.2),
            "sa_pg": adv.get("sa_pg", 30.2),
            "pp_pct": adv.get("pp_pct", 21.0),
            "pk_pct": adv.get("pk_pct", 80.0),
            "sv_pct": sv_25_26.get(abbr, 0.903)
        }

    full_26_27 = {}
    for abbr, base in st_26_27.items():
        adv = adv_26_27.get(abbr, {})
        full_26_27[abbr] = {
            **base,
            "sf_pg": adv.get("sf_pg", 30.2),
            "sa_pg": adv.get("sa_pg", 30.2),
            "pp_pct": adv.get("pp_pct", 21.0),
            "pk_pct": adv.get("pk_pct", 80.0),
            "sv_pct": sv_26_27.get(abbr, 0.903)
        }

    equipos = _combinar_temporadas_dinamico(full_25_26, full_26_27, juegos_full_temporada=82)

    partidos_historicos = []
    fechas_a_consultar = []
    base_pasada = datetime(2026, 4, 15)
    for d in range(45, -1, -1):
        fechas_a_consultar.append((base_pasada - timedelta(days=d)).strftime("%Y%m%d"))
    hoy = datetime.utcnow()
    for d in range(35, 0, -1):
        fechas_a_consultar.append((hoy - timedelta(days=d)).strftime("%Y%m%d"))

    norm_map = {"LA": "LAK", "NJ": "NJD", "SJ": "SJS", "TB": "TBL", "UTAH": "UTA"}
    elo_dinamico = {abbr: 1500.0 for abbr in equipos.keys()}

    for fecha_str in fechas_a_consultar:
        try:
            url_sb = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={fecha_str}"
            r_sb = requests.get(url_sb, headers=HEADERS_API, timeout=4)
            if r_sb.status_code != 200:
                continue
            for ev in r_sb.json().get("events", []):
                comp = ev.get("competitions", [{}])[0]
                if not comp.get("status", {}).get("type", {}).get("completed", False):
                    continue
                comps = comp.get("competitors", [])
                if len(comps) < 2:
                    continue
                home_c = next((c for c in comps if c.get("homeAway") == "home"), None)
                away_c = next((c for c in comps if c.get("homeAway") == "away"), None)
                if not home_c or not away_c:
                    continue

                h_abbr = norm_map.get(home_c.get("team", {}).get("abbreviation", "").upper(), home_c.get("team", {}).get("abbreviation", "").upper())
                a_abbr = norm_map.get(away_c.get("team", {}).get("abbreviation", "").upper(), away_c.get("team", {}).get("abbreviation", "").upper())
                h_score = float(home_c.get("score", 0))
                a_score = float(away_c.get("score", 0))

                if h_abbr in equipos and a_abbr in equipos and h_score != a_score:
                    home_win = 1 if h_score > a_score else 0
                    elo_h = elo_dinamico[h_abbr]
                    elo_a = elo_dinamico[a_abbr]
                    exp_h = 1.0 / (1.0 + (10.0 ** ((elo_a - (elo_h + 30.0)) / 400.0)))
                    k_factor = 14.0 * (1.0 + min(1.5, abs(h_score - a_score) * 0.25))
                    elo_dinamico[h_abbr] = elo_h + k_factor * (home_win - exp_h)
                    elo_dinamico[a_abbr] = elo_a + k_factor * ((1 - home_win) - (1.0 - exp_h))

                    partidos_historicos.append({
                        "home": h_abbr,
                        "away": a_abbr,
                        "home_score": h_score,
                        "away_score": a_score,
                        "home_win": home_win
                    })
        except Exception:
            continue

    for abbr, elo_val in elo_dinamico.items():
        if abbr in equipos:
            equipos[abbr]["elo"] = round(elo_val, 1)

    dataset = {"equipos": equipos, "partidos": partidos_historicos}
    if equipos:
        set_cached("nhl_real_dataset_full_v5", dataset)
    return dataset


# =====================================================================
# 2. NBA: PACE, ORtg, DRtg, eFG%, TS%, ELO DINÁMICO Y B2B (2025-2026 + 2026-2027)
# =====================================================================
NBA_ESPN_TEAM_IDS = {
    "ATL": "1", "BOS": "2", "BKN": "17", "CHA": "30", "CHI": "4", "CLE": "5",
    "DAL": "6", "DEN": "7", "DET": "8", "GSW": "9", "HOU": "10", "IND": "11",
    "LAC": "12", "LAL": "13", "MEM": "29", "MIA": "14", "MIL": "15", "MIN": "16",
    "NOP": "3", "NYK": "18", "OKC": "25", "ORL": "19", "PHI": "20", "PHX": "21",
    "POR": "22", "SAC": "23", "SAS": "24", "TOR": "28", "UTA": "26", "WAS": "27"
}


def _obtener_eficiencia_equipo_nba(team_id: str) -> dict:
    """
    Descarga de ESPN Team Statistics los datos reales de tiro y posesiones:
    FGA, FGM, 3PM, FTA, OREB, TOV para calcular Pace, ORtg, eFG% y TS% reales.
    """
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    stats_map = {}
    try:
        r = requests.get(url, headers=HEADERS_API, timeout=5)
        if r.status_code == 200:
            cats = r.json().get("results", {}).get("stats", {}).get("categories", [])
            for cat in cats:
                for st in cat.get("stats", []):
                    name = st.get("name", "")
                    val = st.get("perGameValue") if st.get("perGameValue") is not None else st.get("value")
                    if name and val is not None:
                        try:
                            stats_map[name] = float(val)
                        except (ValueError, TypeError):
                            pass
    except Exception:
        pass

    fga = stats_map.get("avgFieldGoalsAttempted", stats_map.get("fieldGoalsAttempted", 88.5))
    fgm = stats_map.get("avgFieldGoalsMade", stats_map.get("fieldGoalsMade", 41.5))
    tpm = stats_map.get("avgThreePointFieldGoalsMade", stats_map.get("threePointFieldGoalsMade", 13.0))
    fta = stats_map.get("avgFreeThrowsAttempted", stats_map.get("freeThrowsAttempted", 22.0))
    oreb = stats_map.get("avgOffensiveRebounds", stats_map.get("offensiveRebounds", 10.5))
    tov = stats_map.get("avgTurnovers", stats_map.get("turnovers", 13.8))
    pts = stats_map.get("avgPoints", 114.5)

    # Posesiones reales por juego (Fórmula oficial NBA Dean Oliver)
    pace = max(92.0, min(108.0, fga + (0.44 * fta) - oreb + tov))
    ortg = (pts / pace) * 100.0
    efg_pct = ((fgm + 0.5 * tpm) / max(1.0, fga)) * 100.0
    ts_pct = (pts / max(1.0, 2.0 * (fga + 0.44 * fta))) * 100.0

    return {
        "pace": round(pace, 2),
        "ortg_api": round(ortg, 2),
        "efg_pct": round(efg_pct, 2),
        "ts_pct": round(ts_pct, 2)
    }


def _recolectar_partidos_nba(fechas: list) -> tuple:
    equipos_raw = {}
    partidos = []
    norm_map = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}

    for fecha_str in fechas:
        try:
            url_sb = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_str}"
            r = requests.get(url_sb, headers=HEADERS_API, timeout=4)
            if r.status_code != 200:
                continue
            for ev in r.json().get("events", []):
                comp = ev.get("competitions", [{}])[0]
                if not comp.get("status", {}).get("type", {}).get("completed", False):
                    continue
                comps = comp.get("competitors", [])
                if len(comps) < 2:
                    continue
                home_c = next((c for c in comps if c.get("homeAway") == "home"), None)
                away_c = next((c for c in comps if c.get("homeAway") == "away"), None)
                if not home_c or not away_c:
                    continue

                h_abbr = norm_map.get(home_c.get("team", {}).get("abbreviation", "").upper(), home_c.get("team", {}).get("abbreviation", "").upper())
                a_abbr = norm_map.get(away_c.get("team", {}).get("abbreviation", "").upper(), away_c.get("team", {}).get("abbreviation", "").upper())

                h_score = float(home_c.get("score", 0))
                a_score = float(away_c.get("score", 0))
                if h_score <= 0 or a_score <= 0:
                    continue

                for abbr, pts_f, pts_a, es_home, gano in [
                    (h_abbr, h_score, a_score, True, h_score > a_score),
                    (a_abbr, a_score, h_score, False, a_score > h_score)
                ]:
                    if abbr not in equipos_raw:
                        equipos_raw[abbr] = {
                            "pts_f": [], "pts_a": [], "wins": 0, "gp": 0,
                            "home_f": [], "home_a": [], "road_f": [], "road_a": []
                        }
                    equipos_raw[abbr]["pts_f"].append(pts_f)
                    equipos_raw[abbr]["pts_a"].append(pts_a)
                    equipos_raw[abbr]["gp"] += 1
                    if gano:
                        equipos_raw[abbr]["wins"] += 1
                    if es_home:
                        equipos_raw[abbr]["home_f"].append(pts_f)
                        equipos_raw[abbr]["home_a"].append(pts_a)
                    else:
                        equipos_raw[abbr]["road_f"].append(pts_f)
                        equipos_raw[abbr]["road_a"].append(pts_a)

                partidos.append({
                    "fecha": fecha_str,
                    "home": h_abbr,
                    "away": a_abbr,
                    "home_score": h_score,
                    "away_score": a_score,
                    "home_win": 1 if h_score > a_score else 0
                })
        except Exception:
            continue

    equipos = {}
    for abbr, d in equipos_raw.items():
        gp = max(1, d["gp"])
        pf_avg = sum(d["pts_f"]) / gp
        pa_avg = sum(d["pts_a"]) / gp
        var_f = sum((x - pf_avg) ** 2 for x in d["pts_f"]) / gp
        std_f = max(7.5, var_f ** 0.5)

        equipos[abbr] = {
            "gp": gp,
            "pf_pg": pf_avg,
            "pa_pg": pa_avg,
            "win_pct": d["wins"] / gp,
            "std_pts": std_f,
            "home_pf_pg": (sum(d["home_f"]) / len(d["home_f"])) if d["home_f"] else pf_avg,
            "home_pa_pg": (sum(d["home_a"]) / len(d["home_a"])) if d["home_a"] else pa_avg,
            "road_pf_pg": (sum(d["road_f"]) / len(d["road_f"])) if d["road_f"] else pf_avg,
            "road_pa_pg": (sum(d["road_a"]) / len(d["road_a"])) if d["road_a"] else pa_avg,
        }
    return equipos, partidos


def get_nba_real_dataset():
    cached = fetch_cached("nba_real_dataset_full_v6", ttl=3600)
    if cached:
        return cached

    hoy = datetime.utcnow()
    ayer_str = (hoy - timedelta(days=1)).strftime("%Y%m%d")

    # Orden cronológico para calcular Elo Dinámico real partido a partido
    base_pasada = datetime(2026, 4, 12)
    fechas_pasada = [(base_pasada - timedelta(days=d)).strftime("%Y%m%d") for d in range(60, -1, -1)]
    fechas_actual = [(hoy - timedelta(days=d)).strftime("%Y%m%d") for d in range(32, 0, -1)]

    eq_pasada, part_pasada = _recolectar_partidos_nba(fechas_pasada)
    eq_actual, part_actual = _recolectar_partidos_nba(fechas_actual)

    equipos = _combinar_temporadas_dinamico(eq_pasada, eq_actual, juegos_full_temporada=82)
    partidos_historicos = part_pasada + part_actual

    # Detectar qué equipos jugaron ayer (Back-to-Back real)
    equipos_jugaron_ayer = set()
    for p in part_actual:
        if p.get("fecha") == ayer_str:
            equipos_jugaron_ayer.add(p["home"])
            equipos_jugaron_ayer.add(p["away"])

    # Descargar Pace, ORtg, eFG% y TS% reales de ESPN para cada equipo
    eficiencia_api = {abbr: _obtener_eficiencia_equipo_nba(tid) for abbr, tid in NBA_ESPN_TEAM_IDS.items()}

    # Calcular Elo Dinámico real recorriendo los partidos de 2025-2026 y 2026-2027
    elo_dinamico = {abbr: 1500.0 for abbr in NBA_ESPN_TEAM_IDS.keys()}
    for p in partidos_historicos:
        h_abbr, a_abbr = p["home"], p["away"]
        if h_abbr in elo_dinamico and a_abbr in elo_dinamico:
            home_win = p["home_win"]
            margen = abs(p["home_score"] - p["away_score"])
            elo_h = elo_dinamico[h_abbr]
            elo_a = elo_dinamico[a_abbr]
            exp_h = 1.0 / (1.0 + (10.0 ** ((elo_a - (elo_h + 45.0)) / 400.0)))
            k_factor = 16.0 * (1.0 + min(1.5, margen / 18.0))
            elo_dinamico[h_abbr] = elo_h + k_factor * (home_win - exp_h)
            elo_dinamico[a_abbr] = elo_a + k_factor * ((1 - home_win) - (1.0 - exp_h))

    for abbr, d in equipos.items():
        ef = eficiencia_api.get(abbr, {"pace": 99.0, "ortg_api": 114.5, "efg_pct": 54.0, "ts_pct": 57.5})
        pace = ef["pace"]
        # ORtg y DRtg reales por cada 100 posesiones
        ortg_real = (d["pf_pg"] / pace) * 100.0
        drtg_real = (d["pa_pg"] / pace) * 100.0
        home_ortg = (d["home_pf_pg"] / pace) * 100.0
        home_drtg = (d["home_pa_pg"] / pace) * 100.0
        road_ortg = (d["road_pf_pg"] / pace) * 100.0
        road_drtg = (d["road_pa_pg"] / pace) * 100.0

        d["pace"] = pace
        d["ortg"] = round(ortg_real, 2)
        d["drtg"] = round(drtg_real, 2)
        d["home_ortg"] = round(home_ortg, 2)
        d["home_drtg"] = round(home_drtg, 2)
        d["road_ortg"] = round(road_ortg, 2)
        d["road_drtg"] = round(road_drtg, 2)
        d["efg_pct"] = ef["efg_pct"]
        d["ts_pct"] = ef["ts_pct"]
        d["elo"] = round(elo_dinamico.get(abbr, 1500.0), 1)
        d["jugo_ayer"] = (abbr in equipos_jugaron_ayer)

    dataset = {"equipos": equipos, "partidos": partidos_historicos}
    if equipos:
        set_cached("nba_real_dataset_full_v6", dataset)
    return dataset


# =====================================================================
# 3. NFL: TEMPORADA 2025 (18 SEMANAS) + TEMPORADA 2026 (HASTA SEMANA 18)
# =====================================================================
def _recolectar_temporada_nfl(year: int, max_weeks: int) -> tuple:
    equipos_raw = {}
    partidos = []

    for week in range(1, max_weeks + 1):
        try:
            url_wk = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype=2&week={week}"
            r = requests.get(url_wk, headers=HEADERS_API, timeout=5)
            if r.status_code != 200:
                continue
            for ev in r.json().get("events", []):
                comp = ev.get("competitions", [{}])[0]
                if not comp.get("status", {}).get("type", {}).get("completed", False):
                    continue
                comps = comp.get("competitors", [])
                if len(comps) < 2:
                    continue
                home_c = next((c for c in comps if c.get("homeAway") == "home"), None)
                away_c = next((c for c in comps if c.get("homeAway") == "away"), None)
                if not home_c or not away_c:
                    continue

                h_abbr = home_c.get("team", {}).get("abbreviation", "").upper()
                a_abbr = away_c.get("team", {}).get("abbreviation", "").upper()
                if h_abbr == "WSH": h_abbr = "WAS"
                if a_abbr == "WSH": a_abbr = "WAS"

                h_score = float(home_c.get("score", 0))
                a_score = float(away_c.get("score", 0))

                for abbr, pts_f, pts_a, es_home, gano in [
                    (h_abbr, h_score, a_score, True, h_score > a_score),
                    (a_abbr, a_score, h_score, False, a_score > h_score)
                ]:
                    if abbr not in equipos_raw:
                        equipos_raw[abbr] = {
                            "pts_f": [], "pts_a": [], "wins": 0, "gp": 0,
                            "home_f": [], "home_a": [], "road_f": [], "road_a": []
                        }
                    equipos_raw[abbr]["pts_f"].append(pts_f)
                    equipos_raw[abbr]["pts_a"].append(pts_a)
                    equipos_raw[abbr]["gp"] += 1
                    if gano:
                        equipos_raw[abbr]["wins"] += 1
                    if es_home:
                        equipos_raw[abbr]["home_f"].append(pts_f)
                        equipos_raw[abbr]["home_a"].append(pts_a)
                    else:
                        equipos_raw[abbr]["road_f"].append(pts_f)
                        equipos_raw[abbr]["road_a"].append(pts_a)

                if h_score != a_score:
                    partidos.append({
                        "home": h_abbr,
                        "away": a_abbr,
                        "home_score": h_score,
                        "away_score": a_score,
                        "home_win": 1 if h_score > a_score else 0
                    })
        except Exception:
            continue

    equipos = {}
    for abbr, d in equipos_raw.items():
        gp = max(1, d["gp"])
        pf_avg = sum(d["pts_f"]) / gp
        pa_avg = sum(d["pts_a"]) / gp
        var_f = sum((x - pf_avg) ** 2 for x in d["pts_f"]) / gp
        std_f = max(7.0, var_f ** 0.5)

        equipos[abbr] = {
            "gp": gp,
            "pf_pg": pf_avg,
            "pa_pg": pa_avg,
            "win_pct": d["wins"] / gp,
            "std_pts": std_f,
            "home_pf_pg": (sum(d["home_f"]) / len(d["home_f"])) if d["home_f"] else pf_avg,
            "home_pa_pg": (sum(d["home_a"]) / len(d["home_a"])) if d["home_a"] else pa_avg,
            "road_pf_pg": (sum(d["road_f"]) / len(d["road_f"])) if d["road_f"] else pf_avg,
            "road_pa_pg": (sum(d["road_a"]) / len(d["road_a"])) if d["road_a"] else pa_avg,
        }
    return equipos, partidos


def get_nfl_real_dataset():
    cached = fetch_cached("nfl_real_dataset_v5", ttl=3600)
    if cached:
        return cached

    eq_2025, part_2025 = _recolectar_temporada_nfl(2025, max_weeks=18)
    eq_2026, part_2026 = _recolectar_temporada_nfl(2026, max_weeks=18)

    equipos = _combinar_temporadas_dinamico(eq_2025, eq_2026, juegos_full_temporada=17)
    partidos_historicos = part_2025 + part_2026

    dataset = {"equipos": equipos, "partidos": partidos_historicos}
    if equipos:
        set_cached("nfl_real_dataset_v5", dataset)
    return dataset
