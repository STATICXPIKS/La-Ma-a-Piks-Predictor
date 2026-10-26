import os
import requests
import time

# Lectura directa de tus variables de entorno en Render
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")

# Cache en memoria para no quemar tus límites de peticiones (10 min)
_CACHE = {}

def get_live_odds(sport_key="icehockey_nhl"):
    """
    The Odds API: Obtiene cuotas en vivo de Moneyline, Spreads y Totales
    sport_key: 'icehockey_nhl', 'americanfootball_nfl', 'basketball_nba', 'baseball_mlb'
    """
    now = time.time()
    cache_key = f"odds_{sport_key}"
    if cache_key in _CACHE and (now - _CACHE[cache_key]['time']) < 600:
        return _CACHE[cache_key]['data']

    if not ODDS_API_KEY:
        return None

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            _CACHE[cache_key] = {'time': now, 'data': data}
            return data
    except Exception as e:
        print(f"Error consultando The Odds API: {e}")
    return None

def get_live_weather(ciudad: str):
    """
    OpenWeatherMap: Retorna temperatura en Fahrenheit y viento en MPH
    """
    if not OPENWEATHER_KEY or not ciudad:
        return {"temp_f": 72.0, "viento_mph": 0.0}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": ciudad,
        "appid": OPENWEATHER_KEY,
        "units": "imperial"
    }
    try:
        r = requests.get(url, params=params, timeout=4)
        if r.status_code == 200:
            d = r.json()
            return {
                "temp_f": d["main"].get("temp", 72.0),
                "viento_mph": d["wind"].get("speed", 0.0)
            }
    except Exception as e:
        print(f"Error consultando OpenWeather: {e}")
    return {"temp_f": 72.0, "viento_mph": 0.0}

def get_nhl_team_live_stats(team_name: str):
    """
    API-Sports (Hockey): Consulta estadísticas reales actualizadas de la temporada
    """
    if not API_SPORTS_KEY:
        return None

    url = "https://v1.hockey.api-sports.io/teams"
    headers = {"x-apisports-key": API_SPORTS_KEY}
    try:
        r = requests.get(url, headers=headers, params={"search": team_name}, timeout=4)
        if r.status_code == 200:
            resp = r.json().get("response", [])
            if resp:
                team_id = resp[0]["id"]
                stat_url = "https://v1.hockey.api-sports.io/teams/statistics"
                s_resp = requests.get(stat_url, headers=headers, params={"team": team_id, "season": 2026}, timeout=4)
                if s_resp.status_code == 200:
                    data = s_resp.json().get("response", {})
                    goals = data.get("goals", {})
                    for_avg = float(goals.get("for", {}).get("average", {}).get("total", 3.0) or 3.0)
                    against_avg = float(goals.get("against", {}).get("average", {}).get("total", 3.0) or 3.0)
                    return (for_avg, against_avg)
    except Exception as e:
        print(f"Error consultando API-Sports: {e}")
    return None
