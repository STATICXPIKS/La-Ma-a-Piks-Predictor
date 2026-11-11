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
CACHE_DURATION_SECONDS = 900


def _extraer_stats_jugador_espn(athlete_id: str):
    url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
    res = {}
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=4)
        if r.status_code == 200:
            data = r.json()
            # Busca categorías tanto en la raíz como dentro de 'splits'
            categories = data.get("categories", [])
            if not categories and "splits" in data:
                categories = data["splits"].get("categories", [])

            for cat in categories:
                for st in cat.get("statistics", []):
                    nom = st.get("name", "").lower()
                    val_str = str(st.get("displayValue", "0")).replace(",", "")
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue

                    if nom in ["avgpoints", "pointspergame", "pts", "points"]:
                        res["Puntos"] = round(val, 1)
                    elif nom in ["avgrebounds", "reboundspergame", "reb", "rebounds"]:
                        res["Rebotes"] = round(val, 1)
                    elif nom in ["avgassists", "assistspergame", "ast", "assists"]:
                        res["Asistencias"] = round(val, 1)
                    elif nom in ["threepointfieldgoalsmadepergame", "avgthreepointfieldgoalsmade", "3pm"]:
                        res["Triples"] = round(val, 1)
    except Exception as e:
        print(f"Error stats ESPN atleta {athlete_id}: {e}")
    return res


def _calcular_prop_cuantitativa(media_real: float, tipo_prop: str):
    linea = math.floor(media_real) + 0.5
    cuota = 1.88

    if tipo_prop in ["Puntos", "Rebotes"]:
        cv = 0.22 if tipo_prop == "Puntos" else 0.26
        sigma = max(1.2, media_real * cv)
        z = (linea - media_real) / sigma
        prob_under = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        prob_over = 1.0 - prob_under
    else:
        lamb = media_real
        k_max = int(math.floor(linea))
        prob_under = 0.0
        for k in range(k_max + 1):
            prob_under += (math.exp(-lamb) * (lamb ** k)) / math.factorial(k)
        prob_over = 1.0 - prob_under

    es_over = prob_over >= prob_under
    prob_sel = prob_over if es_over else prob_under
    prob_sel = max(0.48, min(0.68, prob_sel))

    ev = round(((prob_sel * cuota) - 1.0) * 100, 1)

    return {
        "lado": "MÁS DE" if es_over else "MENOS DE",
        "linea": linea,
        "cuota": cuota,
        "prob_real": round(prob_sel * 100, 1),
        "ev": ev,
        "proyeccion": media_real
    }


def obtener_mejores_props_nba(local: str, visitante: str, top_n: int = 6):
    cache_key = f"{local}_{visitante}_props_v4"
    now = time.time()

    if cache_key in _PROPS_CACHE:
        ts, data_cached = _PROPS_CACHE[cache_key]
        if now - ts < CACHE_DURATION_SECONDS and len(data_cached) > 0:
            return data_cached

    abbr_loc = MAPEO_EQUIPOS_NBA.get(local, "ind")
    abbr_vis = MAPEO_EQUIPOS_NBA.get(visitante, "was")

    jugadores = []
    for eq in [abbr_loc, abbr_vis]:
        url_roster = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{eq}/roster"
        try:
            r = requests.get(url_roster, headers=HEADERS_ESPN, timeout=4)
            if r.status_code == 200:
                data = r.json()
                raw_athletes = data.get("athletes", [])
                
                # Desempaqueta estructura anidada de ESPN
                items_lista = []
                if raw_athletes and isinstance(raw_athletes[0], dict) and "items" in raw_athletes[0]:
                    for g in raw_athletes:
                        items_lista.extend(g.get("items", []))
                else:
                    items_lista = raw_athletes

                # Toma los primeros 5 jugadores con ID válido
                count = 0
                for a in items_lista:
                    ath_id = str(a.get("id", ""))
                    nom = a.get("displayName", "")
                    if ath_id and nom:
                        jugadores.append({"id": ath_id, "nombre": nom, "equipo": eq.upper()})
                        count += 1
                        if count >= 5:
                            break
        except Exception as e:
            print(f"Error cargando roster {eq}: {e}")

    candidatas = []
    for j in jugadores:
        stats = _extraer_stats_jugador_espn(j["id"])
        for tipo, media in stats.items():
            # Umbrales mínimos reales para props relevantes
            if tipo == "Puntos" and media < 8.0: continue
            if tipo == "Rebotes" and media < 3.5: continue
            if tipo == "Asistencias" and media < 2.5: continue
            if tipo == "Triples" and media < 1.0: continue

            c = _calcular_prop_cuantitativa(media, tipo)
            candidatas.append({
                "jugador": j["nombre"],
                "equipo_abbr": j["equipo"],
                "tipo_prop": tipo,
                "lado": c["lado"],
                "linea": c["linea"],
                "cuota": c["cuota"],
                "prob_real": c["prob_real"],
                "ev": c["ev"],
                "proyeccion": c["proyeccion"]
            })

    candidatas.sort(key=lambda x: x["ev"], reverse=True)
    seleccion = candidatas[:top_n]

    if seleccion:
        _PROPS_CACHE[cache_key] = (now, seleccion)
    return seleccion
