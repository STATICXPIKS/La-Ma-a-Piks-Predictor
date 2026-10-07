import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

DB_FILE = "historial_la_mana_picks.json"

NFL_TEAM_IDS = {
    "Arizona Cardinals": 22, "Atlanta Falcons": 1, "Baltimore Ravens": 33,
    "Buffalo Bills": 2, "Carolina Panthers": 29, "Chicago Bears": 3,
    "Cincinnati Bengals": 4, "Cleveland Browns": 5, "Dallas Cowboys": 6,
    "Denver Broncos": 7, "Detroit Lions": 8, "Green Bay Packers": 9,
    "Houston Texans": 34, "Indianapolis Colts": 11, "Jacksonville Jaguars": 30,
    "Kansas City Chiefs": 12, "Las Vegas Raiders": 13, "Los Angeles Chargers": 24,
    "Los Angeles Rams": 14, "Miami Dolphins": 15, "Minnesota Vikings": 16,
    "New England Patriots": 17, "New Orleans Saints": 18, "New York Giants": 19,
    "New York Jets": 20, "Philadelphia Eagles": 21, "Pittsburgh Steelers": 23,
    "San Francisco 49ers": 25, "Seattle Seahawks": 26, "Tampa Bay Buccaneers": 27,
    "Tennessee Titans": 10, "Washington Commanders": 28
}

NBA_TEAM_IDS = {
    "Atlanta Hawks": 1, "Boston Celtics": 2, "Brooklyn Nets": 17,
    "Charlotte Hornets": 30, "Chicago Bulls": 4, "Cleveland Cavaliers": 5,
    "Dallas Mavericks": 6, "Denver Nuggets": 7, "Detroit Pistons": 8,
    "Golden State Warriors": 9, "Houston Rockets": 10, "Indiana Pacers": 11,
    "LA Clippers": 12, "Los Angeles Lakers": 13, "Memphis Grizzlies": 29,
    "Miami Heat": 14, "Milwaukee Bucks": 15, "Minnesota Timberwolves": 16,
    "New Orleans Pelicans": 3, "New York Knicks": 18, "Oklahoma City Thunder": 25,
    "Orlando Magic": 19, "Philadelphia 76ers": 20, "Phoenix Suns": 21,
    "Portland Trail Blazers": 22, "Sacramento Kings": 23, "San Antonio Spurs": 24,
    "Toronto Raptors": 28, "Utah Jazz": 26, "Washington Wizards": 27
}

ESPN_SOCCER_LEAGUES = {
    "Premier League": "eng.1", "LaLiga EA Sports": "esp.1",
    "Bundesliga": "ger.1", "Serie A": "ita.1",
    "Champions League": "uefa.champions", "UEFA Nations League": "uefa.nations"
}

NATIONS_TROPHY_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 120'><path d='M30 110 L70 110 L65 85 C65 85 75 50 82 20 L18 20 C25 50 35 85 35 85 Z' fill='%23C0C0C0' stroke='%23333' stroke-width='2'/><path d='M25 25 C40 35 60 15 75 25 L70 40 C55 30 45 45 30 35 Z' fill='%234A5568'/><path d='M28 42 C43 52 57 32 72 42 L68 57 C53 47 43 62 32 52 Z' fill='%2310B981'/><path d='M32 59 C47 69 55 49 68 59 L65 74 C50 64 42 79 34 69 Z' fill='%23EF4444'/><circle cx='50' cy='98' r='6' fill='%23D97706'/></svg>"

LOGOS_LIGAS = {
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "LaLiga EA Sports": "https://a.espncdn.com/i/leaguelogos/soccer/500/15.png",
    "UEFA Nations League": NATIONS_TROPHY_SVG,
    "Champions League": "https://a.espncdn.com/i/leaguelogos/soccer/500/2.png",
    "Bundesliga": "https://a.espncdn.com/i/leaguelogos/soccer/500/10.png",
    "Serie A": "https://a.espncdn.com/i/leaguelogos/soccer/500/12.png",
    "NFL": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg",
    "MLB": "https://upload.wikimedia.org/wikipedia/commons/a/a6/Major_League_Baseball_logo.svg",
    "NBA": "https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg"
}

PREMIER_DICT = {
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png", 
    "Aston Villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "AFC Bournemouth": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png", 
    "Brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "Brighton & Hove Albion": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png", 
    "Chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "Crystal Palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png", 
    "Everton": "https://a.espncdn.com/i/teamlogos/soccer/500/368.png",
    "Fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png", 
    "Ipswich Town": "https://a.espncdn.com/i/teamlogos/soccer/500/373.png",
    "Leicester City": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png", 
    "Liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png", 
    "Manchester United": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "Newcastle United": "https://a.espncdn.com/i/teamlogos/soccer/500/361.png", 
    "Nottingham Forest": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "Southampton": "https://a.espncdn.com/i/teamlogos/soccer/500/376.png", 
    "Tottenham Hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "West Ham United": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png", 
    "Wolverhampton": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png"
}

LALIGA_DICT = {
    "Athletic Club": "https://a.espncdn.com/i/teamlogos/soccer/500/93.png", 
    "Atlético de Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "CA Osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png", 
    "CD Leganés": "https://a.espncdn.com/i/teamlogos/soccer/500/9855.png",
    "Celta de Vigo": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png", 
    "Deportivo Alavés": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png", 
    "Getafe CF": "https://a.espncdn.com/i/teamlogos/soccer/500/2922.png",
    "Girona FC": "https://a.espncdn.com/i/teamlogos/soccer/500/9812.png", 
    "Rayo Vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "RCD Espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png", 
    "RCD Mallorca": "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "Real Betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png", 
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Real Sociedad": "https://a.espncdn.com/i/teamlogos/soccer/500/89.png", 
    "Sevilla FC": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "Valencia CF": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png", 
    "Real Valladolid": "https://a.espncdn.com/i/teamlogos/soccer/500/95.png",
    "Villarreal CF": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png", 
    "UD Las Palmas": "https://a.espncdn.com/i/teamlogos/soccer/500/98.png"
}

NATIONS_LEAGUE_DICT = {
    "España": "https://a.espncdn.com/i/teamlogos/countries/500/esp.png",
    "Francia": "https://a.espncdn.com/i/teamlogos/countries/500/fra.png",
    "Alemania": "https://a.espncdn.com/i/teamlogos/countries/500/ger.png",
    "Inglaterra": "https://a.espncdn.com/i/teamlogos/countries/500/eng.png",
    "Portugal": "https://a.espncdn.com/i/teamlogos/countries/500/por.png",
    "Italia": "https://a.espncdn.com/i/teamlogos/countries/500/ita.png",
    "Países Bajos": "https://a.espncdn.com/i/teamlogos/countries/500/ned.png",
    "Bélgica": "https://a.espncdn.com/i/teamlogos/countries/500/bel.png",
    "Croacia": "https://a.espncdn.com/i/teamlogos/countries/500/cro.png",
    "Dinamarca": "https://a.espncdn.com/i/teamlogos/countries/500/den.png",
    "Suiza": "https://a.espncdn.com/i/teamlogos/countries/500/sui.png",
    "Austria": "https://a.espncdn.com/i/teamlogos/countries/500/aut.png",
    "Hungría": "https://a.espncdn.com/i/teamlogos/countries/500/hun.png",
    "Polonia": "https://a.espncdn.com/i/teamlogos/countries/500/pol.png",
    "Escocia": "https://a.espncdn.com/i/teamlogos/countries/500/sco.png",
    "Serbia": "https://a.espncdn.com/i/teamlogos/countries/500/srb.png"
}

BUNDESLIGA_DICT = {
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "Bayer Leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "Borussia Dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png", 
    "RB Leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "Eintracht Frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png", 
    "VfB Stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png"
}

SERIE_A_DICT = {
    "Inter de Milán": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "Juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "AC Milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "Napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "AS Roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "Atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/105.png"
}

CHAMPIONS_DICT = {
    "Paris Saint-Germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "Bayern Múnich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "FC Barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "Manchester City": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "Real Madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "Arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png"
}

NBA_DICT = {
    "Atlanta Hawks": {"abbr": "atl", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png", "pace": 101.2, "hca": 2.2},
    "Boston Celtics": {"abbr": "bos", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png", "pace": 98.8, "hca": 2.8},
    "Brooklyn Nets": {"abbr": "bkn", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png", "pace": 97.5, "hca": 2.1},
    "Denver Nuggets": {"abbr": "den", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/den.png", "pace": 97.1, "hca": 4.0},
    "Golden State Warriors": {"abbr": "gsw", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png", "pace": 100.1, "hca": 2.9},
    "Los Angeles Lakers": {"abbr": "lal", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png", "pace": 100.8, "hca": 2.7},
    "Miami Heat": {"abbr": "mia", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png", "pace": 96.5, "hca": 2.6},
    "Milwaukee Bucks": {"abbr": "mil", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/mil.png", "pace": 100.4, "hca": 2.8}
}

lista_nba_nombres = sorted(list(NBA_DICT.keys()))

EQUIPOS_MLB = {
    "Arizona Diamondbacks": {"abbr": "ari", "id": 109, "wRC_plus": 105, "park_factor": 1.02},
    "Atlanta Braves": {"abbr": "atl", "id": 144, "wRC_plus": 115, "park_factor": 1.01},
    "Houston Astros": {"abbr": "hou", "id": 117, "wRC_plus": 113, "park_factor": 0.99},
    "Los Angeles Dodgers": {"abbr": "lad", "id": 119, "wRC_plus": 120, "park_factor": 1.01},
    "New York Yankees": {"abbr": "nyy", "id": 147, "wRC_plus": 118, "park_factor": 1.02},
    "Tampa Bay Rays": {"abbr": "tb", "id": 139, "wRC_plus": 100, "park_factor": 0.95}
}

for eq, d in EQUIPOS_MLB.items():
    d["logo"] = f"https://a.espncdn.com/i/teamlogos/mlb/500/{d['abbr']}.png"

lista_mlb_nombres = sorted(list(EQUIPOS_MLB.keys()))

DICT_NFL_COMPLETO = {
    "Baltimore Ravens": {"abbr": "BAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "off": 27.1, "def": 18.5},
    "Buffalo Bills": {"abbr": "BUF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "off": 26.5, "def": 19.2},
    "Dallas Cowboys": {"abbr": "DAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "off": 26.2, "def": 22.1},
    "Detroit Lions": {"abbr": "DET", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "off": 28.5, "def": 20.2},
    "Kansas City Chiefs": {"abbr": "KC", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "off": 25.8, "def": 17.5},
    "New York Jets": {"abbr": "NYJ", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "off": 18.0, "def": 19.8},
    "San Francisco 49ers": {"abbr": "SF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "off": 27.8, "def": 19.1}
}

lista_nfl_nombres = sorted(list(DICT_NFL_COMPLETO.keys()))
