import os
import requests
import time

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "")
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "")

_CACHE = {}

def fetch_cached(key: str, ttl: int = 900):
    now = time.time()
    if key in _CACHE and (now - _CACHE[key]["time"]) < ttl:
        return _CACHE[key]["data"]
    return None

def set_cached(key: str, data):
    _CACHE[key] = {"time": time.time(), "data": data}

# 1. The Odds API: Cuotas de mercado en vivo
def get_live_odds(sport_key="basketball_nba"):
    cached = fetch_cached(f"odds_{sport_key}", ttl=600)
    if cached: return cached
    if not ODDS_API_KEY: return None

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal"
    }
    try:
        r = requests.get(url, params=params, timeout=6)
        if r.status_code == 200:
            data = r.json()
            set_cached(f"odds_{sport_key}", data)
            return data
    except Exception as e:
        print(f"Error The Odds API: {e}")
    return None

# 2. OpenWeatherMap: Clima real por ciudad de estadio (MLB / NFL)
def get_live_weather(ciudad: str):
    cached = fetch_cached(f"weather_{ciudad}", ttl=1800)
    if cached: return cached
    if not OPENWEATHER_KEY or not ciudad:
        return {"temp_f": 72.0, "viento_mph": 0.0, "humedad": 50.0}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": ciudad, "appid": OPENWEATHER_KEY, "units": "imperial"}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            d = r.json()
            res = {
                "temp_f": float(d["main"].get("temp", 72.0)),
                "viento_mph": float(d["wind"].get("speed", 0.0)),
                "humedad": float(d["main"].get("humidity", 50.0))
            }
            set_cached(f"weather_{ciudad}", res)
            return res
    except Exception as e:
        print(f"Error OpenWeather: {e}")
    return {"temp_f": 72.0, "viento_mph": 0.0, "humedad": 50.0}

# 3. NHL API Oficial Pública: Estadísticas en vivo
def get_nhl_stats_live(team_abbr: str):
    cached = fetch_cached(f"nhl_stats_{team_abbr}", ttl=3600)
    if cached: return cached
    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            set_cached(f"nhl_stats_{team_abbr}", data)
            return data
    except Exception as e:
        print(f"Error NHL API: {e}")
    return None

# 4. MLB StatsAPI Oficial Pública: Métricas sabermétricas
def get_mlb_stats_live(team_id: int):
    cached = fetch_cached(f"mlb_stats_{team_id}", ttl=3600)
    if cached: return cached
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats?stats=season&group=pitching,hitting"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            set_cached(f"mlb_stats_{team_id}", data)
            return data
    except Exception as e:
        print(f"Error MLB API: {e}")
    return None

# 5. NBA CDN / API Oficial Pública: Eficiencia y Ritmo en vivo
def get_nba_stats_live(team_abbr: str):
    cached = fetch_cached(f"nba_stats_{team_abbr}", ttl=3600)
    if cached: return cached
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nba.com/"
    }
    url = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            set_cached(f"nba_stats_{team_abbr}", data)
            return data
    except Exception as e:
        print(f"Error NBA API: {e}")
    return None

# 6. ESPN API Pública Gratuita: Estado de partidos, clima y lesiones NFL
def get_nfl_live_data(team_abbr: str):
    cached = fetch_cached(f"nfl_live_{team_abbr}", ttl=1800)
    if cached: return cached
    
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            set_cached(f"nfl_live_{team_abbr}", data)
            return data
    except Exception as e:
        print(f"Error NFL ESPN API: {e}")
    return None
