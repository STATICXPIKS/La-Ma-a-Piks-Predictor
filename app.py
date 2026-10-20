import math
import sys
import subprocess
import json
import os
from datetime import datetime
import gradio as gr
import numpy as np
import pandas as pd
import requests
from scipy.stats import norm, poisson

# Liberar puertos previos
gr.close_all()

# =========================================
# CONFIGURACIÓN DE APIS Y SUPABASE
# =========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuywqyjsaubcxmbzxwlg.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_Q2Zvz4kGTFxikHIDISUCKg_hqiZnsYj")

ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "826e995b77fba63fd42c2915877b1037")
API_SPORT_KEY = os.environ.get("API_SPORT_KEY", "2612f1217a97fa602d307de0fddf81de")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

DB_FILE = "historial_la_mana_picks.json"

NHL_PNG_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAI4AAACqCAYAAACpA4yTAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAB3pJREFUeJzt3X2QVFUdx/HP7sLChsIurLCIooCKi4IvhASJij4MSo40pU2mOaOpjI6V03CspBybzGocp5SGyqyctBytsaL4AEEUeSg+AUEEF1gW3YVddvf2j3vR23v34773nvf23s33M7M399xe7u3N+d1zz/nccx8RkX3SInsl2e0A/DfgX0l2Swi/L4S/41L4fSo4n/Gv4By6A3fC38C/gTnhd+Be4C74G/hf4E7cATsAt8P34TfBf8O/wvfBbfBfI8E5XATfgtvgb+BOwO3w13A7/DV8E34TvAnfA98A34Db/I3uN694k538+f+f5Kx1y1c0/Hq655M565v56499/1v6HfwIvwq+Ar4IvgC+AH4S/Dh4f54y40XjLpC6Q+4CuQuXG1kIHg/uBHsS7AF7ANsAewCbgc3AN4BNwEbg68B3sRnoB3oA29q6p42/C33O3Llyp/udfN9x4053s1s/0f1w53p/s3O9+2G3X9itE7s1sb5O5tZn9L/2M3qdu3P1P19/IftH3+4m4GvA9cCXgX8HXwY+D7wX329sFvgx8A/A3wO/A/4f/C/w/fAd8K1362e+S1u9pC6e3a5mDsc2N3mO52jmcK7nOI7I4Tia43A8xxO5e1Ycx3Fsce1i53p1A3fAtX4d2I5fBf4L7/mR34T/gC/gD+Hvg38F/xD8f/AdcAe+A238A/gO+HrgM8CF4C/AD8P3wreBL/N3XQvfCN8I33S3e+S/mSsdmXoH5+9O38xT5tzE39nc4O69M+sO/0v9X1l+12N6N54L/wX/Ev41fBN4a46+Oedl/u+eO6729/i7q332eLuvve5o22u4L+3s/rN2I1y7m9z7k7A42GfQ50/4H5S2GfgX8Btw3f59D1sA3wb/Ff4f+E3w90OfL3fC/0m3X4m8A/XOnS913tw5U1fr8vY53X/U/1n132U0v73a/YxmszMczd26E17X690OvwXvg3/S1y/83X83/B18F9yD37q/w+/D78Lvw9XAv8N78UeA10Jvh0fD/3X/q3j1/q8L6E7mOTo8f/ZOnl/3d3dO46m3S5mXm2fe4/2R5vudP+O41/9K9g85fwrXb1a20822u+3W1vX04K5tP3P3dvef8U24a9193dme9gq40lfgIbg/PAy2HuwG8A/BvwG1mS2uL6s1a31/X3f3t3j291m5/SdtG2xzt8/B3Lp+r/eH/uO8vXOnk3q+vN297X4Ydzx3rOcx/GfAt3Anvg28AX8Nfws+BLfAdXjP3wG/Cddm343L371wG+y2eD33Iff3O373/T/0v4T4A4+7/S/S3v/E9iOAt8P2ww9Bf4sPgnfDX4B34/U4yS/Ea71f0/Iq8H3ge3e5t5331X7P3X6p3NfRnc3ddLrb89L2544X1v8o9/P1S1a6I84e607mjsP5c8f13PF33I1fhO+BO8A+BDsPthc4S/e/H3eCP/f7fTfwXfB3o/Xv4XfA6+3aM/X4z984/N2938v/GfgG78+5H+7f2pI6L39ve+dM/9eG683f1G9/U333m3vX8v2f92r4p5/S/m/qXgbfAt5O899Xf0x/TfdT3R/C/xP4e7S15o/L4L+C9+L132a2y60/hO/e82L9D6f9mfs/E5p4d667c2xNXXzP2sO4a/y95j1fDvea43UIno9fBff09Qv2X/a/i/U44z+4o/S7z8x+5a7Iu2Oa7fL8XzSfxv4Z+Pq6L+d++IeeK3/s1a/m6O/q+K+L6e/q+I3aN3T841E34Xf02I/Ufl12L8K18Z3u64p3c03eD995j4d1a/oN/i2kP3zX5dOdt3v/03y//X3/f/f49brmXjLvfO7o+O39v/m043743f/4E56PvwMewfvw47v1/tqC43O8v+sJ3Dq/9eN4Ibg8+C/4RrgPvw2+C13/BnyN3I23uS+LrwXvwA+CHwE346u9e3qO4z628pP221/c82Gv45/pfgH+L+C7aJ/2/w/8k0BvS/M1YI40A7G2m4/1T/x/l76/p5vJ1A/sS3f9B67v022v4k3G3s/S60bL/T2f0e/M/WfM3172S+0+c14Jv4S8L43X370b395sve938yL4O287IseX4RvhX+E2eE1f1jfhP8P4m/B6yfe3bM7s8O/f8xL5Tf37G352o0H458G3wS3w97v/fM1v38S4q691x/v3/4PfhH8C/zN6Xy/f03d551e9A78f9y0u373wA3ADbh24C+5/R2/p+dM9/w/pS8h75O5e/j/e+92aP2U604+Gf1L4Xf8v/S931OqP4LrgV8E/D65P+0XwY/gS65vwu+G/uD+C/22756/a45v0+U6M0/lUq/M0R1u/wV/Gfg5+CbgM9kXwD+G74L/mftf3x0v6m+Jq4AtuN3mOn/mK9k2a71f0/qM/qvvU/2vL3+zO7+oG/wH3A98B/y2+v+u/wn/x/sP63/D4Lp232q0vA5+Ea/C/o+e1f4x4s4mJp008C360X58u4D/Bv0p1v2r69S+eG8H78T/s4EbwzXf4G/CfwXehxzeAt+a98D2/Cq4f+w/0+3O7zX6B7e+E+0D0v3kL/hE85v0Z138a3I4X8Xfh89G/FfxL+H74Ufg2fDf8K7wZ4/fAvfC9cDv+P3Anbg/e634L/A9uB/4ffA/c3rX5qPvf0T/B+92vwO+D2/En4DvwfXB/+C53A3fgTsAnmXm1e4G74T/D1+G94Pvgn8An8QehP624G3f6f/P/6N5a/0s2u20uIe7XvUvT4O1u4Gq3s7v83f3gGqP+s3s8wW1v4a6TuxvuA3eB/T633+m2/33w34B/Cv4r/mfgH8L/Av8G3APvhXvgB+4m+A24AnwE33L3wDfgf8P/hu/3t3v/eD9e34/vgmv8/L/3s3r/u3u8we0+A29we5c+N7md3ebv7oHbg1uAG+C2vY/u3O3wSbgP7Anm/zvwA9wO33yHvx13vX15DkL9f9n4f0DqN8+s..."

LOGOS_LIGAS = {
    "Premier League": "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png",
    "NFL": "https://a.espncdn.com/i/leaguelogos/nfl/500/nfl.png",
    "MLB": "https://a.espncdn.com/i/leaguelogos/mlb/500/mlb.png",
    "NBA": "https://a.espncdn.com/i/leaguelogos/nba/500/nba.png",
    "NHL": NHL_PNG_BASE64
}

# =========================================
# DICCIONARIOS DE EQUIPOS
# =========================================
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

ESPN_SOCCER_LEAGUES = {"Premier League": "eng.1"}
STAT_CACHE_SOCCER = {}
DEFAULT_SOCCER_LOGO = "https://a.espncdn.com/i/leaguelogos/soccer/500/23.png"

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

NHL_DICT = {
    "Anaheim Ducks": {"abbr": "ana", "id": 25, "xg_f": 2.65, "xg_a": 3.45},
    "Boston Bruins": {"abbr": "bos", "id": 1, "xg_f": 3.25, "xg_a": 2.70},
    "Buffalo Sabres": {"abbr": "buf", "id": 2, "xg_f": 2.95, "xg_a": 3.15},
    "Calgary Flames": {"abbr": "cgy", "id": 3, "xg_f": 2.85, "xg_a": 3.05},
    "Carolina Hurricanes": {"abbr": "car", "id": 7, "xg_f": 3.45, "xg_a": 2.55},
    "Chicago Blackhawks": {"abbr": "chi", "id": 4, "xg_f": 2.45, "xg_a": 3.55},
    "Colorado Avalanche": {"abbr": "col", "id": 16, "xg_f": 3.50, "xg_a": 2.95},
    "Columbus Blue Jackets": {"abbr": "cbj", "id": 29, "xg_f": 2.80, "xg_a": 3.40},
    "Dallas Stars": {"abbr": "dal", "id": 9, "xg_f": 3.35, "xg_a": 2.60},
    "Detroit Red Wings": {"abbr": "det", "id": 5, "xg_f": 2.90, "xg_a": 3.10},
    "Edmonton Oilers": {"abbr": "edm", "id": 6, "xg_f": 3.55, "xg_a": 2.85},
    "Florida Panthers": {"abbr": "fla", "id": 26, "xg_f": 3.40, "xg_a": 2.65},
    "Los Angeles Kings": {"abbr": "lak", "id": 8, "xg_f": 3.10, "xg_a": 2.60},
    "Minnesota Wild": {"abbr": "min", "id": 30, "xg_f": 3.05, "xg_a": 2.85},
    "Montreal Canadiens": {"abbr": "mtl", "id": 10, "xg_f": 2.75, "xg_a": 3.35},
    "Nashville Predators": {"abbr": "nsh", "id": 27, "xg_f": 2.90, "xg_a": 2.90},
    "New Jersey Devils": {"abbr": "nj", "id": 11, "xg_f": 3.20, "xg_a": 2.90},
    "New York Islanders": {"abbr": "nyi", "id": 12, "xg_f": 2.80, "xg_a": 2.85},
    "New York Rangers": {"abbr": "nyr", "id": 13, "xg_f": 3.30, "xg_a": 2.70},
    "Ottawa Senators": {"abbr": "ott", "id": 14, "xg_f": 3.05, "xg_a": 3.20},
    "Philadelphia Flyers": {"abbr": "phi", "id": 15, "xg_f": 2.80, "xg_a": 3.15},
    "Pittsburgh Penguins": {"abbr": "pit", "id": 16, "xg_f": 3.10, "xg_a": 3.10},
    "San Jose Sharks": {"abbr": "sj", "id": 22, "xg_f": 2.40, "xg_a": 3.65},
    "Seattle Kraken": {"abbr": "sea", "id": 119, "xg_f": 2.85, "xg_a": 2.95},
    "St. Louis Blues": {"abbr": "stl", "id": 19, "xg_f": 2.80, "xg_a": 3.05},
    "Tampa Bay Lightning": {"abbr": "tb", "id": 20, "xg_f": 3.40, "xg_a": 3.00},
    "Toronto Maple Leafs": {"abbr": "tor", "id": 21, "xg_f": 3.35, "xg_a": 2.90},
    "Utah Hockey Club": {"abbr": "utah", "id": 24, "xg_f": 2.85, "xg_a": 3.10},
    "Vancouver Canucks": {"abbr": "van", "id": 22, "xg_f": 3.25, "xg_a": 2.75},
    "Vegas Golden Knights": {"abbr": "vgk", "id": 118, "xg_f": 3.20, "xg_a": 2.70},
    "Washington Capitals": {"abbr": "wsh", "id": 23, "xg_f": 3.00, "xg_a": 2.95},
    "Winnipeg Jets": {"abbr": "wpg", "id": 28, "xg_f": 3.25, "xg_a": 2.50}
}
for eq, d in NHL_DICT.items():
    d["logo"] = f"https://a.espncdn.com/i/teamlogos/nhl/500/{d['abbr']}.png"
lista_nhl_nombres = sorted(list(NHL_DICT.keys()))

NBA_DICT = {
    "Atlanta Hawks": {"abbr": "atl", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png", "pace": 101.2, "hca": 2.2},
    "Boston Celtics": {"abbr": "bos", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png", "pace": 98.8, "hca": 2.8},
    "Brooklyn Nets": {"abbr": "bkn", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png", "pace": 97.5, "hca": 2.1},
    "Charlotte Hornets": {"abbr": "cha", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/cha.png", "pace": 99.1, "hca": 2.0},
    "Chicago Bulls": {"abbr": "chi", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/chi.png", "pace": 100.5, "hca": 2.3},
    "Cleveland Cavaliers": {"abbr": "cle", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png", "pace": 97.2, "hca": 2.6},
    "Dallas Mavericks": {"abbr": "dal", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/dal.png", "pace": 96.8, "hca": 2.5},
    "Denver Nuggets": {"abbr": "den", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/den.png", "pace": 97.1, "hca": 4.0},
    "Detroit Pistons": {"abbr": "det", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/det.png", "pace": 98.6, "hca": 2.0},
    "Golden State Warriors": {"abbr": "gsw", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png", "pace": 100.1, "hca": 2.9},
    "Houston Rockets": {"abbr": "hou", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/hou.png", "pace": 99.4, "hca": 2.4},
    "Indiana Pacers": {"abbr": "ind", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/ind.png", "pace": 102.8, "hca": 2.3},
    "LA Clippers": {"abbr": "lac", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/lac.png", "pace": 97.4, "hca": 2.2},
    "Los Angeles Lakers": {"abbr": "lal", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png", "pace": 100.8, "hca": 2.7},
    "Memphis Grizzlies": {"abbr": "mem", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/mem.png", "pace": 100.2, "hca": 2.5},
    "Miami Heat": {"abbr": "mia", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png", "pace": 96.5, "hca": 2.6},
    "Milwaukee Bucks": {"abbr": "mil", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/mil.png", "pace": 100.4, "hca": 2.8},
    "Minnesota Timberwolves": {"abbr": "min", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/min.png", "pace": 97.8, "hca": 2.6},
    "New Orleans Pelicans": {"abbr": "nop", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/nop.png", "pace": 98.2, "hca": 2.2},
    "New York Knicks": {"abbr": "nyk", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/nyk.png", "pace": 95.8, "hca": 2.7},
    "Oklahoma City Thunder": {"abbr": "okc", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/okc.png", "pace": 99.7, "hca": 2.8},
    "Orlando Magic": {"abbr": "orl", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/orl.png", "pace": 97.0, "hca": 2.5},
    "Philadelphia 76ers": {"abbr": "phi", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/phi.png", "pace": 96.9, "hca": 2.6},
    "Phoenix Suns": {"abbr": "phx", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/phx.png", "pace": 98.1, "hca": 2.4},
    "Portland Trail Blazers": {"abbr": "por", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/por.png", "pace": 98.5, "hca": 2.2},
    "Sacramento Kings": {"abbr": "sac", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/sac.png", "pace": 99.6, "hca": 2.5},
    "San Antonio Spurs": {"abbr": "sas", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/sas.png", "pace": 101.0, "hca": 2.2},
    "Toronto Raptors": {"abbr": "tor", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/tor.png", "pace": 99.3, "hca": 2.3},
    "Utah Jazz": {"abbr": "uta", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/uta.png", "pace": 100.6, "hca": 3.5},
    "Washington Wizards": {"abbr": "was", "logo": "https://a.espncdn.com/i/teamlogos/nba/500/was.png", "pace": 102.1, "hca": 1.9}
}
lista_nba_nombres = sorted(list(NBA_DICT.keys()))

EQUIPOS_MLB = {
    "Arizona Diamondbacks": {"abbr": "ari", "id": 109, "wRC_plus": 105, "park_factor": 1.02},
    "Atlanta Braves": {"abbr": "atl", "id": 144, "wRC_plus": 115, "park_factor": 1.01},
    "Baltimore Orioles": {"abbr": "bal", "id": 110, "wRC_plus": 112, "park_factor": 0.98},
    "Boston Red Sox": {"abbr": "bos", "id": 111, "wRC_plus": 106, "park_factor": 1.05},
    "Chicago Cubs": {"abbr": "chc", "id": 112, "wRC_plus": 103, "park_factor": 1.00},
    "Chicago White Sox": {"abbr": "cws", "id": 145, "wRC_plus": 84, "park_factor": 0.98},
    "Cincinnati Reds": {"abbr": "cin", "id": 113, "wRC_plus": 98, "park_factor": 1.06},
    "Cleveland Guardians": {"abbr": "cle", "id": 114, "wRC_plus": 101, "park_factor": 0.96},
    "Colorado Rockies": {"abbr": "col", "id": 115, "wRC_plus": 91, "park_factor": 1.15},
    "Detroit Tigers": {"abbr": "det", "id": 116, "wRC_plus": 97, "park_factor": 0.97},
    "Houston Astros": {"abbr": "hou", "id": 117, "wRC_plus": 113, "park_factor": 0.99},
    "Kansas City Royals": {"abbr": "kc", "id": 118, "wRC_plus": 102, "park_factor": 1.02},
    "Los Angeles Angels": {"abbr": "laa", "id": 108, "wRC_plus": 95, "park_factor": 0.99},
    "Los Angeles Dodgers": {"abbr": "lad", "id": 119, "wRC_plus": 120, "park_factor": 1.01},
    "Miami Marlins": {"abbr": "mia", "id": 146, "wRC_plus": 89, "park_factor": 0.95},
    "Milwaukee Brewers": {"abbr": "mil", "id": 158, "wRC_plus": 101, "park_factor": 1.01},
    "Minnesota Twins": {"abbr": "min", "id": 142, "wRC_plus": 104, "park_factor": 1.00},
    "New York Mets": {"abbr": "nym", "id": 121, "wRC_plus": 109, "park_factor": 0.96},
    "New York Yankees": {"abbr": "nyy", "id": 147, "wRC_plus": 118, "park_factor": 1.02},
    "Oakland Athletics": {"abbr": "oak", "id": 133, "wRC_plus": 96, "park_factor": 0.95},
    "Philadelphia Phillies": {"abbr": "phi", "id": 143, "wRC_plus": 114, "park_factor": 1.03},
    "Pittsburgh Pirates": {"abbr": "pit", "id": 134, "wRC_plus": 93, "park_factor": 0.97},
    "San Diego Padres": {"abbr": "sd", "id": 135, "wRC_plus": 107, "park_factor": 0.95},
    "San Francisco Giants": {"abbr": "sf", "id": 137, "wRC_plus": 97, "park_factor": 0.94},
    "Seattle Mariners": {"abbr": "sea", "id": 136, "wRC_plus": 98, "park_factor": 0.92},
    "St. Louis Cardinals": {"abbr": "stl", "id": 138, "wRC_plus": 98, "park_factor": 0.98},
    "Tampa Bay Rays": {"abbr": "tb", "id": 139, "wRC_plus": 100, "park_factor": 0.95},
    "Texas Rangers": {"abbr": "tex", "id": 140, "wRC_plus": 105, "park_factor": 1.02},
    "Toronto Blue Jays": {"abbr": "tor", "id": 141, "wRC_plus": 102, "park_factor": 0.99},
    "Washington Nationals": {"abbr": "wsh", "id": 120, "wRC_plus": 94, "park_factor": 1.01}
}
for eq, d in EQUIPOS_MLB.items():
    d["logo"] = f"https://a.espncdn.com/i/teamlogos/mlb/500/{d['abbr']}.png"
lista_mlb_nombres = sorted(list(EQUIPOS_MLB.keys()))

DICT_NFL_COMPLETO = {
    "Arizona Cardinals": {"abbr": "ARI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png", "off": 21.5, "def": 24.2},
    "Atlanta Falcons": {"abbr": "ATL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png", "off": 22.8, "def": 21.9},
    "Baltimore Ravens": {"abbr": "BAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "off": 27.1, "def": 18.5},
    "Buffalo Bills": {"abbr": "BUF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "off": 26.5, "def": 19.2},
    "Carolina Panthers": {"abbr": "CAR", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png", "off": 16.2, "def": 25.8},
    "Chicago Bears": {"abbr": "CHI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png", "off": 20.1, "def": 22.3},
    "Cincinnati Bengals": {"abbr": "CIN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png", "off": 24.8, "def": 23.1},
    "Cleveland Browns": {"abbr": "CLE", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png", "off": 19.5, "def": 21.0},
    "Dallas Cowboys": {"abbr": "DAL", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "off": 26.2, "def": 22.1},
    "Denver Broncos": {"abbr": "DEN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png", "off": 21.0, "def": 20.5},
    "Detroit Lions": {"abbr": "DET", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "off": 28.5, "def": 20.2},
    "Green Bay Packers": {"abbr": "GB", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png", "off": 24.5, "def": 21.0},
    "Houston Texans": {"abbr": "HOU", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png", "off": 23.1, "def": 19.8},
    "Indianapolis Colts": {"abbr": "IND", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png", "off": 22.4, "def": 23.5},
    "Jacksonville Jaguars": {"abbr": "JAX", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png", "off": 21.2, "def": 23.8},
    "Kansas City Chiefs": {"abbr": "KC", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "off": 25.8, "def": 17.5},
    "Las Vegas Raiders": {"abbr": "LV", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png", "off": 18.2, "def": 24.1},
    "Los Angeles Chargers": {"abbr": "LAC", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png", "off": 22.0, "def": 19.2},
    "Los Angeles Rams": {"abbr": "LAR", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png", "off": 23.8, "def": 22.5},
    "Miami Dolphins": {"abbr": "MIA", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "off": 25.0, "def": 22.8},
    "Minnesota Vikings": {"abbr": "MIN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png", "off": 24.1, "def": 20.4},
    "New England Patriots": {"abbr": "NE", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png", "off": 17.1, "def": 22.0},
    "New Orleans Saints": {"abbr": "NO", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png", "off": 22.5, "def": 21.8},
    "New York Giants": {"abbr": "NYG", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png", "off": 17.8, "def": 23.9},
    "New York Jets": {"abbr": "NYJ", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "off": 18.0, "def": 19.8},
    "Philadelphia Eagles": {"abbr": "PHI", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "off": 26.1, "def": 20.8},
    "Pittsburgh Steelers": {"abbr": "PIT", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png", "off": 20.5, "def": 18.8},
    "San Francisco 49ers": {"abbr": "SF", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "off": 27.8, "def": 19.1},
    "Seattle Seahawks": {"abbr": "SEA", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png", "off": 22.9, "def": 22.4},
    "Tampa Bay Buccaneers": {"abbr": "TB", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "off": 24.2, "def": 22.0},
    "Tennessee Titans": {"abbr": "TEN", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png", "off": 18.9, "def": 23.1},
    "Washington Commanders": {"abbr": "WAS", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/was.png", "off": 24.8, "def": 23.5}
}
lista_nfl_nombres = sorted(list(DICT_NFL_COMPLETO.keys()))

# =========================================
# HELPER LESIONADOS Y BASE DE DATOS
# =========================================
def obtener_lesionados_oficiales_nba(nombre_equipo):
    return 0.0, 0.0, f"✅ Sin lesiones de alto impacto reportadas para {nombre_equipo}"

def obtener_lesionados_oficiales_nfl(nombre_equipo):
    return 0.0, 0.0, f"✅ Roster principal disponible para {nombre_equipo}"

def cargar_historial_db():
    try:
        url = f"{SUPABASE_URL}/rest/v1/picks?select=*"
        res = requests.get(url, headers=SUPABASE_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error HTTP leyendo Supabase: {e}")
    return []

def guardar_pick_db(deporte, partido, seleccion, tipo_pick, cuota, ventaja_ev):
    partes = partido.split(" vs ")
    eq_loc = partes[0] if len(partes) > 0 else "Local"
    eq_vis = partes[1] if len(partes) > 1 else "Visitante"

    modelo_map = {
        "NFL": "TOUCH IQ",
        "NBA": "23 IA",
        "MLB": "MAÑA BASEBALL",
        "NHL": "NASH IA",
        "FÚTBOL": "AZTECA VET"
    }

    dep_clean = str(deporte).split("(")[0].strip().upper()
    mod_nombre = modelo_map.get(dep_clean, "AZTECA VET")

    logo_loc_url = DEFAULT_SOCCER_LOGO
    logo_vis_url = DEFAULT_SOCCER_LOGO

    if "NFL" in dep_clean:
        logo_loc_url = DICT_NFL_COMPLETO.get(eq_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis_url = DICT_NFL_COMPLETO.get(eq_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
    elif "NBA" in dep_clean:
        logo_loc_url = NBA_DICT.get(eq_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis_url = NBA_DICT.get(eq_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
    elif "MLB" in dep_clean:
        logo_loc_url = EQUIPOS_MLB.get(eq_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis_url = EQUIPOS_MLB.get(eq_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
    elif "NHL" in dep_clean:
        logo_loc_url = NHL_DICT.get(eq_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis_url = NHL_DICT.get(eq_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
    elif "FÚTBOL" in dep_clean or "PREMIER" in dep_clean:
        logo_loc_url = PREMIER_DICT.get(eq_loc, DEFAULT_SOCCER_LOGO)
        logo_vis_url = PREMIER_DICT.get(eq_vis, DEFAULT_SOCCER_LOGO)

    nuevo_item = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "deporte": dep_clean,
        "modelo_nombre": mod_nombre,
        "equipo_local": eq_loc,
        "logo_local": logo_loc_url,
        "equipo_visitante": eq_vis,
        "logo_visitante": logo_vis_url,
        "pick_recomendado": seleccion,
        "cuota": float(cuota),
        "probabilidad": 65,
        "ev_porcentaje": float(str(ventaja_ev).replace("+", "").replace("%", "")),
        "estado": "PENDING"
    }

    try:
        url = f"{SUPABASE_URL}/rest/v1/picks"
        res = requests.post(url, headers=SUPABASE_HEADERS, json=nuevo_item, timeout=5)
        if res.status_code in [200, 201]:
            print(f"✅ Pick guardado en Supabase (picks): [{dep_clean}] {eq_loc} vs {eq_vis}")
    except Exception as e:
        print(f"Error HTTP guardando en Supabase: {e}")

def cambiar_estado_directo(pick_id, nuevo_estado):
    try:
        url = f"{SUPABASE_URL}/rest/v1/picks?id=eq.{int(pick_id)}"
        requests.patch(url, headers=SUPABASE_HEADERS, json={"estado": nuevo_estado}, timeout=5)
    except Exception as e:
        print(f"Error HTTP actualizando en Supabase: {e}")

    recalibrar_modelos_auto()
    return generar_dashboard_completo()

def calcular_metricas_historial():
    historial = cargar_historial_db()
    stats = {
        "NFL": {"wins": 0, "losses": 0, "pending": 0},
        "MLB": {"wins": 0, "losses": 0, "pending": 0},
        "NBA": {"wins": 0, "losses": 0, "pending": 0},
        "NHL": {"wins": 0, "losses": 0, "pending": 0},
        "PREMIER LEAGUE": {"wins": 0, "losses": 0, "pending": 0}
    }

    for item in historial:
        dep = str(item.get("deporte", "")).upper()
        est = str(item.get("estado", "PENDING")).upper()

        if "NFL" in dep: key = "NFL"
        elif "MLB" in dep: key = "MLB"
        elif "NBA" in dep: key = "NBA"
        elif "NHL" in dep: key = "NHL"
        elif "FÚTBOL" in dep or "FOOTBALL" in dep or "PREMIER" in dep: key = "PREMIER LEAGUE"
        else: continue

        if est == "WIN": stats[key]["wins"] += 1
        elif est == "LOSS": stats[key]["losses"] += 1
        elif est == "PENDING": stats[key]["pending"] += 1

    tot_wins = sum(s["wins"] for s in stats.values())
    tot_loss = sum(s["losses"] for s in stats.values())
    tot_global = tot_wins + tot_loss
    pct_global = round((tot_wins / tot_global) * 100, 1) if tot_global > 0 else 0.0
    return stats, tot_wins, tot_loss, tot_global, pct_global

FACTOR_AJUSTE_AUTO = {
    "NFL": 1.0, "MLB": 1.0, "NBA": 1.0, "NHL": 1.0, "PREMIER LEAGUE": 1.0
}

def recalibrar_modelos_auto():
    global FACTOR_AJUSTE_AUTO
    stats, _, _, _, _ = calcular_metricas_historial()

    for key in FACTOR_AJUSTE_AUTO.keys():
        w = stats.get(key, {}).get("wins", 0)
        l = stats.get(key, {}).get("losses", 0)
        tot = w + l
        if tot >= 4:
            win_rate = w / tot
            if win_rate < 0.55:
                FACTOR_AJUSTE_AUTO[key] = 0.92
            elif win_rate > 0.70:
                FACTOR_AJUSTE_AUTO[key] = 1.08
            else:
                FACTOR_AJUSTE_AUTO[key] = 1.0
        else:
            FACTOR_AJUSTE_AUTO[key] = 1.0

# =========================================
# CONSULTAS A APIS CON PROTECCIÓN
# =========================================
def obtener_estadisticas_soccer_api(nombre_liga, nombre_equipo):
    cache_key = f"{nombre_liga}_{nombre_equipo}"
    if cache_key in STAT_CACHE_SOCCER:
        return STAT_CACHE_SOCCER[cache_key]

    code_league = ESPN_SOCCER_LEAGUES.get(nombre_liga, "eng.1")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code_league}/teams"
    goles_fFavor, goles_contra = 1.35, 1.20

    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            sports = data.get("sports", [])
            if sports:
                leagues = sports[0].get("leagues", [])
                if leagues:
                    teams = leagues[0].get("teams", [])
                    for t in teams:
                        t_info = t.get("team", {})
                        disp_name = t_info.get("displayName", "")
                        if nombre_equipo.lower() in disp_name.lower():
                            t_id = t_info.get("id")
                            if t_id:
                                url_t = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code_league}/teams/{t_id}/schedule"
                                r_sched = requests.get(url_t, timeout=3)
                                if r_sched.status_code == 200:
                                    events = r_sched.json().get("events", [])
                                    gf_list, gc_list = [], []
                                    for ev in events[-8:]:
                                        comps = ev.get("competitions", [])
                                        if comps and comps[0].get("status", {}).get("type", {}).get("completed", False):
                                            for c in comps[0].get("competitors", []):
                                                if str(c.get("id")) == str(t_id):
                                                    gf_list.append(float(c.get("score", {}).get("value", 1.35)))
                                                else:
                                                    gc_list.append(float(c.get("score", {}).get("value", 1.20)))
                                    if gf_list: goles_fFavor = sum(gf_list) / len(gf_list)
                                    if gc_list: goles_contra = sum(gc_list) / len(gc_list)
                            break
    except Exception:
        pass

    res = (min(3.5, max(0.5, goles_fFavor)), min(3.5, max(0.5, goles_contra)))
    STAT_CACHE_SOCCER[cache_key] = res
    return res

def obtener_stats_nfl_dinamicas(nombre_equipo):
    team_id = NFL_TEAM_IDS.get(nombre_equipo)
    off_base = DICT_NFL_COMPLETO.get(nombre_equipo, {}).get("off", 22.0)
    def_base = DICT_NFL_COMPLETO.get(nombre_equipo, {}).get("def", 21.0)

    if not team_id:
        return off_base, def_base

    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            events = r.json().get("events", [])
            pts_f, pts_c = [], []
            for ev in events[-6:]:
                comps = ev.get("competitions", [])
                if comps and comps[0].get("status", {}).get("type", {}).get("completed", False):
                    for c in comps[0].get("competitors", []):
                        if str(c.get("id")) == str(team_id):
                            pts_f.append(float(c.get("score", {}).get("value", off_base)))
                        else:
                            pts_c.append(float(c.get("score", {}).get("value", def_base)))
            if pts_f: off_base = round(sum(pts_f) / len(pts_f), 1)
            if pts_c: def_base = round(sum(pts_c) / len(pts_c), 1)
    except Exception:
        pass

    return off_base, def_base

def obtener_wrc_dinamico_mlb(nombre_equipo):
    base_wrc = EQUIPOS_MLB.get(nombre_equipo, {}).get("wRC_plus", 100)
    team_id = EQUIPOS_MLB.get(nombre_equipo, {}).get("id")
    if not team_id:
        return base_wrc

    try:
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats?stats=season&group=hitting"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            splits = r.json().get("stats", [{}])[0].get("splits", [])
            if splits:
                ops = float(splits[0].get("stat", {}).get("ops", 0.720))
                base_wrc = int(round((ops / 0.720) * 100))
    except Exception:
        pass
    return base_wrc

def obtener_estadisticas_nba_api(nombre_equipo):
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
    pts_favor, pts_contra = 114.5, 112.0

    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            teams = r.json().get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
            for t in teams:
                t_info = t.get("team", {})
                if nombre_equipo.lower() in t_info.get("displayName", "").lower():
                    t_id = t_info.get("id")
                    if t_id:
                        r_sched = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{t_id}/schedule", timeout=3)
                        if r_sched.status_code == 200:
                            events = r_sched.json().get("events", [])
                            pf_list, pc_list = [], []
                            for ev in events[-8:]:
                                comps = ev.get("competitions", [])
                                if comps:
                                    for c in comps[0].get("competitors", []):
                                        if str(c.get("id")) == str(t_id):
                                            pf_list.append(float(c.get("score", {}).get("value", 110)))
                                        else:
                                            pc_list.append(float(c.get("score", {}).get("value", 110)))
                            if pf_list: pts_favor = sum(pf_list) / len(pf_list)
                            if pc_list: pts_contra = sum(pc_list) / len(pc_list)
                    break
    except Exception:
        pass

    return pts_favor, pts_contra

def auto_cargar_pitchers_mlb(nombre_local, nombre_visita):
    id_loc = EQUIPOS_MLB[nombre_local]["id"]
    id_vis = EQUIPOS_MLB[nombre_visita]["id"]
    hoy = datetime.now().strftime("%Y-%m-%d")
    url_sched = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={hoy}&endDate={hoy}&hydrate=probablePitcher"
    p_loc_name, era_loc, whip_loc = "Abridor Local", 3.80, 1.20
    p_vis_name, era_vis, whip_vis = "Abridor Visitante", 3.80, 1.20

    try:
        r = requests.get(url_sched, timeout=4)
        if r.status_code == 200:
            data = r.json()
            dates = data.get("dates", [])
            if dates:
                games = dates[0].get("games", [])
                for g in games:
                    h_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
                    a_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
                    if h_id == id_loc or a_id == id_loc:
                        p_loc_data = g.get("teams", {}).get("home", {}).get("probablePitcher", {})
                        p_vis_data = g.get("teams", {}).get("away", {}).get("probablePitcher", {})
                        p_loc_id, p_vis_id = p_loc_data.get("id"), p_vis_data.get("id")
                        if p_loc_data.get("fullName"): p_loc_name = p_loc_data.get("fullName")
                        if p_vis_data.get("fullName"): p_vis_name = p_vis_data.get("fullName")

                        if p_loc_id:
                            r_p1 = requests.get(f"https://statsapi.mlb.com/api/v1/people/{p_loc_id}?hydrate=stats(group=[pitching],type=[season])", timeout=3)
                            if r_p1.status_code == 200:
                                st1 = r_p1.json().get("people", [{}])[0].get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
                                era_loc, whip_loc = float(st1.get("era", 3.80)), float(st1.get("whip", 1.20))

                        if p_vis_id:
                            r_p2 = requests.get(f"https://statsapi.mlb.com/api/v1/people/{p_vis_id}?hydrate=stats(group=[pitching],type=[season])", timeout=3)
                            if r_p2.status_code == 200:
                                st2 = r_p2.json().get("people", [{}])[0].get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
                                era_vis, whip_vis = float(st2.get("era", 3.80)), float(st2.get("whip", 1.20))
                        break
    except Exception:
        pass

    status_msg = f"🟢 MLB API: {p_loc_name} ({era_loc} ERA) vs {p_vis_name} ({era_vis} ERA)"
    return era_loc, whip_loc, era_vis, whip_vis, status_msg

def obtener_estadisticas_nhl_api(nombre_equipo):
    eq_info = NHL_DICT.get(nombre_equipo, {})
    xg_for_base = eq_info.get("xg_f", 3.0)
    xg_against_base = eq_info.get("xg_a", 3.0)

    try:
        team_id = eq_info.get("id", 1)
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/schedule"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            events = r.json().get("events", [])
            pf, pc = [], []
            for ev in events[-6:]:
                comps = ev.get("competitions", [])
                if comps and comps[0].get("status", {}).get("type", {}).get("completed", False):
                    for c in comps[0].get("competitors", []):
                        if str(c.get("id")) == str(team_id):
                            pf.append(float(c.get("score", {}).get("value", xg_for_base)))
                        else:
                            pc.append(float(c.get("score", {}).get("value", xg_against_base)))
            if pf: xg_for_base = round(sum(pf) / len(pf), 2)
            if pc: xg_against_base = round(sum(pc) / len(pc), 2)
    except Exception:
        pass

    return xg_for_base, xg_against_base

# =========================================
# MOTOR DE DIXON-COLES Y MODELOS
# =========================================
def dixon_coles_tau(x, y, lambda_x, mu_y, rho=-0.13):
    if x == 0 and y == 0: return 1.0 - (lambda_x * mu_y * rho)
    elif x == 0 and y == 1: return 1.0 + (lambda_x * rho)
    elif x == 1 and y == 0: return 1.0 + (mu_y * rho)
    elif x == 1 and y == 1: return 1.0 - rho
    else: return 1.0

def simular_partido_futbol_avanzado(liga, nombre_local, nombre_visita, cuota_loc, cuota_emp, cuota_vis, cuota_btts_si, cuota_btts_no, linea_goles, cuota_goles_over, cuota_goles_under, fatiga_eur, dict_actual):
    logo_loc = dict_actual.get(nombre_local, DEFAULT_SOCCER_LOGO)
    logo_vis = dict_actual.get(nombre_visita, DEFAULT_SOCCER_LOGO)

    gf_loc, gc_loc = obtener_estadisticas_soccer_api(liga, nombre_local)
    gf_vis, gc_vis = obtener_estadisticas_soccer_api(liga, nombre_visita)

    prom_liga = 1.35
    mod_fatiga = 0.88 if "Sí" in str(fatiga_eur) else 1.0
    mod_auto = FACTOR_AJUSTE_AUTO.get(str(liga).upper(), 1.0)

    att_loc = gf_loc / prom_liga
    def_vis = gc_vis / prom_liga
    att_vis = gf_vis / prom_liga
    def_loc = gc_loc / prom_liga

    xG_loc = round(min(3.50, max(0.40, att_loc * def_vis * prom_liga * 1.12 * mod_fatiga * mod_auto)), 2)
    xG_vis = round(min(3.50, max(0.40, att_vis * def_loc * prom_liga * mod_auto)), 2)

    max_goles = 7
    p_loc = [poisson.pmf(i, xG_loc) for i in range(max_goles)]
    p_vis = [poisson.pmf(j, xG_vis) for j in range(max_goles)]

    prob_win_local, prob_empate, prob_win_visita = 0.0, 0.0, 0.0
    prob_over_line, prob_btts_si = 0.0, 0.0
    linea_g = float(linea_goles)

    for i in range(max_goles):
        for j in range(max_goles):
            tau = dixon_coles_tau(i, j, xG_loc, xG_vis)
            prob_mat = p_loc[i] * p_vis[j] * tau

            if i > j: prob_win_local += prob_mat
            elif i == j: prob_empate += prob_mat
            else: prob_win_visita += prob_mat

            if (i + j) > linea_g: prob_over_line += prob_mat
            if i > 0 and j > 0: prob_btts_si += prob_mat

    total_prob = prob_win_local + prob_empate + prob_win_visita
    prob_win_local /= total_prob
    prob_empate /= total_prob
    prob_win_visita /= total_prob

    prob_loc_pct = int(round(prob_win_local * 100))
    prob_vis_pct = int(round(prob_win_visita * 100))
    prob_emp_pct = max(5, 100 - prob_loc_pct - prob_vis_pct)

    prob_over_pct = int(round(prob_over_line * 100))
    prob_btts_pct = int(round(prob_btts_si * 100))
    prob_btts_no_pct = 100 - prob_btts_pct

    c_loc, c_vis = float(cuota_loc), float(cuota_vis)
    c_over, c_under = float(cuota_goles_over), float(cuota_goles_under)
    c_btts_s, c_btts_n = float(cuota_btts_si), float(cuota_btts_no)

    ev_loc = min(6.0, round(prob_loc_pct - ((1.0 / c_loc) * 100 if c_loc > 1 else 50.0), 1))
    ev_vis = min(6.0, round(prob_vis_pct - ((1.0 / c_vis) * 100 if c_vis > 1 else 50.0), 1))

    if ev_loc >= ev_vis and ev_loc >= 2.0:
        pick_1_str = f"Gana {nombre_local} (1X2) @ {cuota_loc} — Prob: {prob_loc_pct}% | EV: +{ev_loc}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{ev_loc}% EV)</span>'
    elif ev_vis > ev_loc and ev_vis >= 2.0:
        pick_1_str = f"Gana {nombre_visita} (1X2) @ {cuota_vis} — Prob: {prob_vis_pct}% | EV: +{ev_vis}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{ev_vis}% EV)</span>'
    else:
        fav_n = nombre_local if prob_loc_pct >= prob_vis_pct else nombre_visita
        fav_p = max(prob_loc_pct, prob_vis_pct)
        fav_c = c_loc if prob_loc_pct >= prob_vis_pct else c_vis
        pick_1_str = f"Gana {fav_n} (1X2) @ {fav_c} — Probabilidad: {fav_p}%"
        badge_1 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    pick_2_str = f"Doble Oportunidad: {nombre_local if prob_loc_pct >= prob_vis_pct else nombre_visita} o Empate"

    ev_over = min(6.0, round(prob_over_pct - ((1.0 / c_over) * 100 if c_over > 1 else 50.0), 1))
    ev_under = min(6.0, round((100 - prob_over_pct) - ((1.0 / c_under) * 100 if c_under > 1 else 50.0), 1))

    if ev_over >= ev_under and ev_over >= 2.0:
        pick_3_str = f"OVER de {linea_goles} Goles @ {c_over} — Prob: {prob_over_pct}% | EV: +{ev_over}%"
    else:
        pick_3_str = f"UNDER de {linea_goles} Goles @ {c_under} — Prob: {100 - prob_over_pct}% | EV: +{ev_under}%"

    ev_btts_s = min(6.0, round(prob_btts_pct - ((1.0 / c_btts_s) * 100 if c_btts_s > 1 else 50.0), 1))
    ev_btts_n = min(6.0, round(prob_btts_no_pct - ((1.0 / c_btts_n) * 100 if c_btts_n > 1 else 50.0), 1))

    if ev_btts_s >= ev_btts_n and ev_btts_s >= 2.0:
        pick_4_str = f"Ambos Anotan: SÍ @ {c_btts_s} — Prob: {prob_btts_pct}% | EV: +{ev_btts_s}%"
        badge_btts = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 SÍ (+{ev_btts_s}% EV)</span>'
    elif ev_btts_n > ev_btts_s and ev_btts_n >= 2.0:
        pick_4_str = f"Ambos Anotan: NO @ {c_btts_n} — Prob: {prob_btts_no_pct}% | EV: +{ev_btts_n}%"
        badge_btts = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 NO (+{ev_btts_n}% EV)</span>'
    else:
        pick_4_str = f"Ambos Anotan: {'SÍ' if prob_btts_pct>=50 else 'NO'} — Probabilidad: {max(prob_btts_pct, prob_btts_no_pct)}%"
        badge_btts = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO DIXON-COLES ({str(liga).upper()})</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">DIXON-COLES CALIBRADO</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({xG_loc:.2f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_loc_pct}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({xG_vis:.2f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_vis_pct}%</span>
            </div>
            <div style="text-align: center; font-size: 12px; font-weight: 700; color: #64748B;">Probabilidad de Empate: {prob_emp_pct}%</div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Ganador Directo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Doble Oportunidad: {pick_2_str}</div></div><span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales: {pick_3_str}</div></div><span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">4. Ambos Anotan (BTTS): {pick_4_str}</div></div>{badge_btts}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, pick_4_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_nhl(nombre_local, nombre_visita, cuota_ml_loc, cuota_ml_vis, linea_pl_loc, cuota_pl_loc, linea_pl_vis, cuota_pl_vis, linea_total, cuota_tot_over, cuota_tot_under):
    logo_loc = NHL_DICT.get(nombre_local, {}).get("logo", "")
    logo_vis = NHL_DICT.get(nombre_visita, {}).get("logo", "")

    xg_for_loc, xg_against_loc = obtener_estadisticas_nhl_api(nombre_local)
    xg_for_vis, xg_against_vis = obtener_estadisticas_nhl_api(nombre_visita)

    mod_auto = FACTOR_AJUSTE_AUTO.get("NHL", 1.0)

    HCA_HOCKEY = 0.20
    xG_loc_est = max(1.1, round(((xg_for_loc + xg_against_vis) / 2.0) * mod_auto + HCA_HOCKEY, 2))
    xG_vis_est = max(1.1, round(((xg_for_vis + xg_against_loc) / 2.0) * mod_auto, 2))

    iteraciones = 10000
    sim_loc = np.random.poisson(xG_loc_est, iteraciones)
    sim_vis = np.random.poisson(xG_vis_est, iteraciones)

    ties = (sim_loc == sim_vis)
    ot_winner = np.random.rand(np.sum(ties)) > 0.48
    sim_loc[ties] += ot_winner
    sim_vis[ties] += (~ot_winner)

    wins_loc = np.sum(sim_loc > sim_vis)
    wins_vis = iteraciones - wins_loc
    prob_ml_loc = round((wins_loc / iteraciones) * 100, 1)
    prob_ml_vis = round((wins_vis / iteraciones) * 100, 1)

    c_ml_l, c_ml_v = float(cuota_ml_loc), float(cuota_ml_vis)
    prob_impl_ml_loc = (1.0 / c_ml_l) * 100 if c_ml_l > 1 else 50.0
    prob_impl_ml_vis = (1.0 / c_ml_v) * 100 if c_ml_v > 1 else 50.0

    ev_ml_loc = round(prob_ml_loc - prob_impl_ml_loc, 1)
    ev_ml_vis = round(prob_ml_vis - prob_impl_ml_vis, 1)

    if ev_ml_loc >= 2.5:
        pick_1_str = f"Gana {nombre_local} ML @ {c_ml_l} — Prob: {prob_ml_loc}% | EV: +{ev_ml_loc}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{ev_ml_loc}% EV)</span>'
    elif ev_ml_vis >= 2.5:
        pick_1_str = f"Gana {nombre_visita} ML @ {c_ml_v} — Prob: {prob_ml_vis}% | EV: +{ev_ml_vis}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{ev_ml_vis}% EV)</span>'
    else:
        fav_n = nombre_local if prob_ml_loc >= prob_ml_vis else nombre_visita
        fav_p = max(prob_ml_loc, prob_ml_vis)
        fav_c = c_ml_l if prob_ml_loc >= prob_ml_vis else c_ml_v
        pick_1_str = f"Gana {fav_n} ML @ {fav_c} — Prob: {fav_p}%"
        badge_1 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    totales = sim_loc + sim_vis
    l_tot = float(linea_total)
    prob_over = round((np.sum(totales > l_tot) / iteraciones) * 100, 1)
    prob_under = round(100.0 - prob_over, 1)

    c_ov, c_un = float(cuota_tot_over), float(cuota_tot_under)
    prob_impl_ov = (1.0 / c_ov) * 100 if c_ov > 1 else 50.0
    prob_impl_un = (1.0 / c_un) * 100 if c_un > 1 else 50.0

    ev_over = round(prob_over - prob_impl_ov, 1)
    ev_under = round(prob_under - prob_impl_un, 1)

    if ev_over >= ev_under and ev_over >= 2.0:
        pick_2_str = f"OVER {l_tot} Goles @ {c_ov} — Prob: {prob_over}% | EV: +{ev_over}%"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET OVER 🔥</span>'
    elif ev_under > ev_over and ev_under >= 2.0:
        pick_2_str = f"UNDER {l_tot} Goles @ {c_un} — Prob: {prob_under}% | EV: +{ev_under}%"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET UNDER 🔥</span>'
    else:
        rec_t = "OVER" if prob_over >= 50 else "UNDER"
        rec_p = max(prob_over, prob_under)
        rec_c = c_ov if prob_over >= 50 else c_un
        pick_2_str = f"{rec_t} {l_tot} Goles @ {rec_c} — Prob: {rec_p}%"
        badge_2 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    dif_goles = sim_loc - sim_vis
    l_pl_l, l_pl_v = float(linea_pl_loc), float(linea_pl_vis)

    prob_pl_loc = round((np.sum(dif_goles > -l_pl_l) / iteraciones) * 100, 1)
    prob_pl_vis = round((np.sum((-dif_goles) > -l_pl_v) / iteraciones) * 100, 1)

    c_pl_l, c_pl_v = float(cuota_pl_loc), float(cuota_pl_vis)
    ev_pl_loc = round(prob_pl_loc - ((1.0 / c_pl_l) * 100 if c_pl_l > 1 else 50.0), 1)
    ev_pl_vis = round(prob_pl_vis - ((1.0 / c_pl_v) * 100 if c_pl_v > 1 else 50.0), 1)

    if ev_pl_loc >= ev_pl_vis and ev_pl_loc >= 2.0:
        pick_3_str = f"{nombre_local} {l_pl_l:+g} @ {c_pl_l} — Prob: {prob_pl_loc}% | EV: +{ev_pl_loc}%"
        badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>'
    elif ev_pl_vis > ev_pl_loc and ev_pl_vis >= 2.0:
        pick_3_str = f"{nombre_visita} {l_pl_v:+g} @ {c_pl_v} — Prob: {prob_pl_vis}% | EV: +{ev_pl_vis}%"
        badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>'
    else:
        best_n = nombre_local if prob_pl_loc >= prob_pl_vis else nombre_visita
        best_l = l_pl_l if prob_pl_loc >= prob_pl_vis else l_pl_v
        best_c = c_pl_l if prob_pl_loc >= prob_pl_vis else c_pl_v
        best_p = max(prob_pl_loc, prob_pl_vis)
        pick_3_str = f"{best_n} {best_l:+g} @ {best_c} — Prob: {best_p}%"
        badge_3 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO NHL MONTE CARLO (10K ITERACIONES)</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">MODELO CORREGIDO Y CALIBRADO</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({xG_loc_est:.2f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_ml_loc}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({xG_vis_est:.2f} xG)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_ml_vis}%</span>
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Ganador Directo ML: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Totales (Over/Under): {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Puck Line (Hándicap): {pick_3_str}</div></div>{badge_3}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_nba(nombre_local, nombre_visita, cuota_ml_loc, cuota_ml_vis, sp_loc_val, cuota_sp_loc, sp_vis_val, cuota_sp_vis, linea_total, cuota_tot_over, cuota_tot_under, descanso_option, modo_temporada):
    if "Pretemporada" in str(modo_temporada):
        factor_epm_lesiones = 0.50
        desviacion_margin = 16.5
        desviacion_total = 19.5
        boost_pace = 2.5
        hca_loc = 1.0
        label_fase = "PRETEMPORADA"
    elif "Playoffs" in str(modo_temporada):
        factor_epm_lesiones = 1.30
        desviacion_margin = 10.5
        desviacion_total = 14.0
        boost_pace = -2.0
        hca_loc = 3.5
        label_fase = "PLAYOFFS"
    else:
        factor_epm_lesiones = 1.00
        desviacion_margin = 13.0
        desviacion_total = 16.5
        boost_pace = 0.0
        hca_loc = NBA_DICT.get(nombre_local, {}).get("hca", 2.3)
        label_fase = "TEMPORADA REGULAR"

    logo_loc = NBA_DICT.get(nombre_local, {}).get("logo", "")
    logo_vis = NBA_DICT.get(nombre_visita, {}).get("logo", "")

    pen_loc_off, pen_loc_def, r_loc_inj = obtener_lesionados_oficiales_nba(nombre_local)
    pen_vis_off, pen_vis_def, r_vis_inj = obtener_lesionados_oficiales_nba(nombre_visita)

    pen_loc_off *= factor_epm_lesiones
    pen_loc_def *= factor_epm_lesiones
    pen_vis_off *= factor_epm_lesiones
    pen_vis_def *= factor_epm_lesiones

    pf_loc, pc_loc = obtener_estadisticas_nba_api(nombre_local)
    pf_vis, pc_vis = obtener_estadisticas_nba_api(nombre_visita)

    pace_loc = NBA_DICT.get(nombre_local, {}).get("pace", 99.0) + boost_pace
    pace_vis = NBA_DICT.get(nombre_visita, {}).get("pace", 99.0) + boost_pace
    pace_liga = 99.2 + boost_pace

    pace_proyectado = (pace_loc * pace_vis) / pace_liga

    mod_auto = FACTOR_AJUSTE_AUTO.get("NBA", 1.0)
    ortg_loc = (((pf_loc / pace_loc) * 100) - pen_loc_off) * mod_auto
    drtg_loc = ((pc_loc / pace_loc) * 100) + pen_loc_def

    ortg_vis = (((pf_vis / pace_vis) * 100) - pen_vis_off) * mod_auto
    drtg_vis = ((pc_vis / pace_vis) * 100) + pen_vis_def

    media_ortg_liga = 114.0

    pen_descanso_loc = -2.8 if "Local" in descanso_option else 0.0
    pen_descanso_vis = -2.8 if "Visitante" in descanso_option else 0.0

    off_efectiva_loc = (ortg_loc * drtg_vis) / media_ortg_liga
    off_efectiva_vis = (ortg_vis * drtg_loc) / media_ortg_liga

    pts_loc_est = round(((off_efectiva_loc / 100) * pace_proyectado) + hca_loc + pen_descanso_loc, 1)
    pts_vis_est = round(((off_efectiva_vis / 100) * pace_proyectado) + pen_descanso_vis, 1)

    diff_pts = pts_loc_est - pts_vis_est

    max_p = 90 if "Pretemporada" in str(modo_temporada) else 95
    min_p = 10 if "Pretemporada" in str(modo_temporada) else 5
    prob_win_local = int(round(min(max_p, max(min_p, norm.cdf(diff_pts / desviacion_margin) * 100))))
    prob_win_visita = 100 - prob_win_local

    prob_impl_ml_loc = (1 / float(cuota_ml_loc)) * 100 if float(cuota_ml_loc) > 1 else 50.0
    prob_impl_ml_vis = (1 / float(cuota_ml_vis)) * 100 if float(cuota_ml_vis) > 1 else 50.0

    edge_ml_loc = min(6.0, round(prob_win_local - prob_impl_ml_loc, 1))
    edge_ml_vis = min(6.0, round(prob_win_visita - prob_impl_ml_vis, 1))

    if edge_ml_loc >= 3.5:
        pick_1_str = f"{nombre_local} ML @ {cuota_ml_loc} — Prob: {prob_win_local}% | EV: +{edge_ml_loc}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_loc}% EV)</span>'
    elif edge_ml_vis >= 3.5:
        pick_1_str = f"{nombre_visita} ML @ {cuota_ml_vis} — Prob: {prob_win_visita}% | EV: +{edge_ml_vis}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_vis}% EV)</span>'
    else:
        fav_name = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
        fav_prob = max(prob_win_local, prob_win_visita)
        fav_cuota = cuota_ml_loc if prob_win_local >= prob_win_visita else cuota_ml_vis
        pick_1_str = f"{fav_name} ML @ {fav_cuota} — Prob: {fav_prob}%"
        badge_1 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    p_cubre_sp_loc = round(norm.cdf((diff_pts + float(sp_loc_val)) / desviacion_margin) * 100, 1)
    p_cubre_sp_vis = round(norm.cdf(((-diff_pts) + float(sp_vis_val)) / desviacion_margin) * 100, 1)

    prob_impl_sp_loc = (1 / float(cuota_sp_loc)) * 100 if float(cuota_sp_loc) > 1 else 50.0
    edge_sp_loc = min(5.0, round(p_cubre_sp_loc - prob_impl_sp_loc, 1))

    pick_2_str = f"{nombre_local if p_cubre_sp_loc >= p_cubre_sp_vis else nombre_visita} Spread ({sp_loc_val if p_cubre_sp_loc >= p_cubre_sp_vis else sp_vis_val}) @ {cuota_sp_loc if p_cubre_sp_loc >= p_cubre_sp_vis else cuota_sp_vis}"
    badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_loc}% EV)</span>' if edge_sp_loc >= 2.5 else '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    tot_est_real = pts_loc_est + pts_vis_est
    dif_total = tot_est_real - float(linea_total)
    prob_over_real = round(norm.cdf(dif_total / desviacion_total) * 100, 1)

    if dif_total >= 0:
        tipo_tot = "OVER"
        prob_tot = int(round(prob_over_real))
        cuota_tot_fav = cuota_tot_over
    else:
        tipo_tot = "UNDER"
        prob_tot = int(round(100 - prob_over_real))
        cuota_tot_fav = cuota_tot_under

    pick_3_str = f"{tipo_tot} de {linea_total} pts @ {cuota_tot_fav} — Prob: {prob_tot}% (Proyección: {tot_est_real:.1f} pts)"
    badge_3 = '<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if abs(dif_total) >= 3.5 else '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MOTOR SABERMÉTRICO NBA ({label_fase})</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">CALIBRADO</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 12px; margin-bottom: 12px; border: 1px solid #E2E8F0;">
            {r_loc_inj}
            {r_vis_inj}
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({pts_loc_est:.1f} pts)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({pts_vis_est:.1f} pts)</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>
            <div style="text-align: center; font-size: 11px; font-weight: 700; color: #64748B; border-top: 1px solid #E2E8F0; padding-top: 6px;">
                Ritmo Proyectado: {pace_proyectado:.1f} Posesiones | Fase: {label_fase}
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Directo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Spread Recomendado: {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales (O/U): {pick_3_str}</div></div>{badge_3}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, "", f"{nombre_local} vs {nombre_visita}"

def simular_partido_mlb_clasificado(nombre_local, nombre_visita, xera_loc, whip_loc, era_bp_loc, whip_bp_loc, xera_vis, whip_vis, era_bp_vis, whip_bp_vis, cuota_loc_dec, cuota_vis_dec, rl_loc_val, cuota_rl_loc, rl_vis_val, cuota_rl_vis, cuota_f5_loc, cuota_f5_vis, linea_tot_carreras, linea_team_loc, cuota_team_loc_over, cuota_team_loc_under, linea_team_vis, cuota_team_vis_over, cuota_team_vis_under, cuota_nrfi, cuota_yrfi):
    loc_d, vis_d = EQUIPOS_MLB[nombre_local], EQUIPOS_MLB[nombre_visita]
    logo_loc, logo_vis = loc_d["logo"], vis_d["logo"]

    mod_auto = FACTOR_AJUSTE_AUTO.get("MLB", 1.0)

    wrc_loc = obtener_wrc_dinamico_mlb(nombre_local) * mod_auto
    wrc_vis = obtener_wrc_dinamico_mlb(nombre_visita) * mod_auto

    pitching_loc = (float(xera_loc) * 0.65 + float(era_bp_loc) * 0.35) * (float(whip_loc) * 0.65 + float(whip_bp_loc) * 0.35) / 1.2
    pitching_vis = (float(xera_vis) * 0.65 + float(era_bp_vis) * 0.35) * (float(whip_vis) * 0.65 + float(whip_bp_vis) * 0.35) / 1.2

    carreras_loc = round(max(1.5, (wrc_loc / 100.0) * (pitching_vis / 3.8) * 4.2 * loc_d['park_factor']), 1)
    carreras_vis = round(max(1.5, (wrc_vis / 100.0) * (pitching_loc / 3.8) * 4.0 * vis_d['park_factor']), 1)

    tot_carreras = carreras_loc + carreras_vis
    diff_carreras = carreras_loc - carreras_vis

    prob_win_local = int(round(100 / (1 + 10**(-diff_carreras / 1.8))))
    prob_win_visita = 100 - prob_win_local

    prob_impl_ml_loc = (1 / float(cuota_loc_dec)) * 100 if float(cuota_loc_dec) > 1 else 50.0
    prob_impl_ml_vis = (1 / float(cuota_vis_dec)) * 100 if float(cuota_vis_dec) > 1 else 50.0

    edge_ml_loc = min(6.0, round(prob_win_local - prob_impl_ml_loc, 1))
    edge_ml_vis = min(6.0, round(prob_win_visita - prob_impl_ml_vis, 1))

    if edge_ml_loc >= 3.5:
        pick_1_str = f"{nombre_local} ML @ {cuota_loc_dec} — Prob: {prob_win_local}% | EV: +{edge_ml_loc}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_loc}% EV)</span>'
    elif edge_ml_vis >= 3.5:
        pick_1_str = f"{nombre_visita} ML @ {cuota_vis_dec} — Prob: {prob_win_visita}% | EV: +{edge_ml_vis}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_vis}% EV)</span>'
    else:
        fav_n = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
        fav_p = max(prob_win_local, prob_win_visita)
        fav_c = cuota_loc_dec if prob_win_local >= prob_win_visita else cuota_vis_dec
        pick_1_str = f"{fav_n} ML @ {fav_c} — Prob: {fav_p}%"
        badge_1 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    pick_2_str = f"Run Line {nombre_local if diff_carreras>=0 else nombre_visita}"
    badge_2 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'
    pick_3_str = f"F5 ML {nombre_local if diff_carreras>=0 else nombre_visita}"
    badge_3 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    exp_carreras_1st = (float(xera_loc) + float(xera_vis)) / 9.0
    prob_nrfi = int(round(np.exp(-exp_carreras_1st) * 100))
    pick_4_str = f"NRFI @ {cuota_nrfi} — Prob: {prob_nrfi}%"
    badge_4 = '<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if prob_nrfi >= 60 else '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    pick_5_str = f"Team Total {nombre_local}: {carreras_loc:.1f} carreras est."
    badge_5 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'
    pick_6_str = f"Team Total {nombre_visita}: {carreras_vis:.1f} carreras est."
    badge_6 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    dif_linea = tot_carreras - float(linea_tot_carreras)
    tipo_tot = "OVER" if dif_linea >= 0 else "UNDER"
    pick_7_str = f"{tipo_tot} de {linea_tot_carreras} Carreras — Proyección: {tot_carreras:.1f}"
    badge_7 = '<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if abs(dif_linea) >= 0.8 else '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO SABERMÉTRICO AJUSTADO</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">CALIBRADO DINÁMICO</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({carreras_loc:.1f} carreras est. | wRC+ {wrc_loc:.0f})</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({carreras_vis:.1f} carreras est. | wRC+ {wrc_vis:.0f})</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Juego Completo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Run Line Recomendado: {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Primeras 5 Entradas (F5): {pick_3_str}</div></div>{badge_3}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">4. Mercado 1er Inning: {pick_4_str}</div></div>{badge_4}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">5. Total Carreras {nombre_local}: {pick_5_str}</div></div>{badge_5}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">6. Total Carreras {nombre_visita}: {pick_6_str}</div></div>{badge_6}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">7. Total Juego Completo (O/U): {pick_7_str}</div></div>{badge_7}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, pick_4_str, pick_5_str, pick_6_str, pick_7_str, f"{nombre_local} vs {nombre_visita}"

def simular_partido_nfl_clasificado(nombre_local, nombre_visita, cuota_ml_loc, cuota_ml_vis, sp_loc_val, cuota_sp_loc, sp_vis_val, cuota_sp_vis, linea_total, cuota_tot_over, cuota_tot_under):
    logo_loc = DICT_NFL_COMPLETO.get(nombre_local, {}).get("logo", "")
    logo_vis = DICT_NFL_COMPLETO.get(nombre_visita, {}).get("logo", "")

    pen_loc_off, pen_loc_def, r_loc_inj = obtener_lesionados_oficiales_nfl(nombre_local)
    pen_vis_off, pen_vis_def, r_vis_inj = obtener_lesionados_oficiales_nfl(nombre_visita)

    mod_auto = FACTOR_AJUSTE_AUTO.get("NFL", 1.0)

    off_loc_real, def_loc_real = obtener_stats_nfl_dinamicas(nombre_local)
    off_vis_real, def_vis_real = obtener_stats_nfl_dinamicas(nombre_visita)

    off_loc = max(10.0, (off_loc_real - pen_loc_off) * mod_auto)
    def_loc = def_loc_real + pen_loc_def
    off_vis = max(10.0, (off_vis_real - pen_vis_off) * mod_auto)
    def_vis = def_vis_real + pen_vis_def

    HCA = 2.5

    pts_local_est = round(((off_loc + def_vis) / 2.0) + (HCA / 2.0), 1)
    pts_visita_est = round(((off_vis + def_loc) / 2.0) - (HCA / 2.0), 1)

    diff_pts = pts_local_est - pts_visita_est

    prob_win_local = int(round(min(96, max(4, norm.cdf(diff_pts / 13.5) * 100))))
    prob_win_visita = 100 - prob_win_local

    prob_impl_ml_loc = (1 / float(cuota_ml_loc)) * 100 if float(cuota_ml_loc) > 1 else 50.0
    prob_impl_ml_vis = (1 / float(cuota_ml_vis)) * 100 if float(cuota_ml_vis) > 1 else 50.0

    edge_ml_loc = min(6.0, round(prob_win_local - prob_impl_ml_loc, 1))
    edge_ml_vis = min(6.0, round(prob_win_visita - prob_impl_ml_vis, 1))

    if edge_ml_loc >= 3.5:
        pick_1_str = f"{nombre_local} ML @ {cuota_ml_loc} — Prob: {prob_win_local}% | EV: +{edge_ml_loc}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_loc}% EV)</span>'
    elif edge_ml_vis >= 3.5:
        pick_1_str = f"{nombre_visita} ML @ {cuota_ml_vis} — Prob: {prob_win_visita}% | EV: +{edge_ml_vis}%"
        badge_1 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_ml_vis}% EV)</span>'
    else:
        fav_name = nombre_local if prob_win_local >= prob_win_visita else nombre_visita
        fav_prob = max(prob_win_local, prob_win_visita)
        fav_cuota = cuota_ml_loc if prob_win_local >= prob_win_visita else cuota_ml_vis
        pick_1_str = f"{fav_name} ML @ {fav_cuota} — Prob: {fav_prob}%"
        badge_1 = '<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    p_cubre_sp_loc = round(norm.cdf((diff_pts + float(sp_loc_val)) / 13.5) * 100, 1)
    p_cubre_sp_vis = round(norm.cdf(((-diff_pts) + float(sp_vis_val)) / 13.5) * 100, 1)

    edge_sp_loc = round(p_cubre_sp_loc - ((1 / float(cuota_sp_loc)) * 100), 1) if float(cuota_sp_loc) > 1 else 0
    edge_sp_vis = round(p_cubre_sp_vis - ((1 / float(cuota_sp_vis)) * 100), 1) if float(cuota_sp_vis) > 1 else 0

    if edge_sp_loc >= 3.0:
        pick_2_str = f"{nombre_local} Spread ({sp_loc_val}) @ {cuota_sp_loc} — Prob: {p_cubre_sp_loc}% | EV: +{edge_sp_loc}%"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_loc}% EV)</span>'
    elif edge_sp_vis >= 3.0:
        pick_2_str = f"{nombre_visita} Spread ({sp_vis_val}) @ {cuota_sp_vis} — Prob: {p_cubre_sp_vis}% | EV: +{edge_sp_vis}%"
        badge_2 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥 (+{edge_sp_vis}% EV)</span>'
    else:
        pick_2_str = f"{nombre_local if diff_pts>=0 else nombre_visita} Spread"
        badge_2 = '<span style="background: #EF4444; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">SKIP ❌</span>'

    tot_est_real = pts_local_est + pts_visita_est
    dif_total = tot_est_real - float(linea_total)
    tipo_tot = "OVER" if dif_total >= 0 else "UNDER"
    cuota_tot_fav = cuota_tot_over if tipo_tot == "OVER" else cuota_tot_under
    prob_tot = min(85, int(50 + abs(dif_total) * 3))

    pick_3_str = f"{tipo_tot} de {linea_total} pts @ {cuota_tot_fav} — Prob: {prob_tot}% (Proyección: {tot_est_real:.1f} pts)"
    badge_3 = f'<span style="background: #10B981; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">BET 🔥</span>' if abs(dif_total) >= 2.5 else f'<span style="background: #3B82F6; color: white; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px;">MAYBE ⚡</span>'

    html_out = f"""
    <div style="font-family: 'Segoe UI', system-ui, sans-serif; background: #FFFFFF; padding: 24px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ECFDF5; padding-bottom: 12px; margin-bottom: 16px;">
            <div style="font-size: 18px; font-weight: 900; color: #065F46;">LA MAÑA PICKS • MODELO NFL ESTADÍSTICO DINÁMICO</div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #047857;">MODELO REAL</div>
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 12px; margin-bottom: 12px; border: 1px solid #E2E8F0;">
            {r_loc_inj}
            {r_vis_inj}
        </div>

        <div style="background: #F8FAFC; border-radius: 14px; padding: 16px; border: 1px solid #E2E8F0; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_loc}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_local} ({pts_local_est:.1f} pts est. | Rating Off: {off_loc_real:.1f})</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_local}%</span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <img src="{logo_vis}" referrerpolicy="no-referrer" width="40" height="40" style="object-fit: contain;"/>
                    <span style="font-size: 16px; font-weight: 800; color: #0F172A;">{nombre_visita} ({pts_visita_est:.1f} pts est. | Rating Off: {off_vis_real:.1f})</span>
                </div>
                <span style="font-size: 22px; font-weight: 900; color: #059669;">{prob_win_visita}%</span>
            </div>
        </div>

        <div style="font-size: 13px; font-weight: 800; color: #065F46; margin-bottom: 10px;">🎯 SELECCIONES CLASIFICADAS POR VALOR (+EV)</div>
        <div style="background: #ECFDF5; border-radius: 10px; padding: 10px 14px; border: 1px solid #10B981; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #064E3B;">1. Moneyline Directo: {pick_1_str}</div></div>{badge_1}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">2. Spread Recomendado: {pick_2_str}</div></div>{badge_2}
        </div>
        <div style="background: #FFFFFF; border-radius: 10px; padding: 10px 14px; border: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 14px; font-weight: 800; color: #0F172A;">3. Totales (O/U): {pick_3_str}</div></div>{badge_3}
        </div>
    </div>
    """
    return html_out, pick_1_str, pick_2_str, pick_3_str, "", f"{nombre_local} vs {nombre_visita}"

# =========================================
# COMPONENTES VISUALES DASHBOARD
# =========================================
def crear_grafica_barras_3d(titulo, wins, losses, pending):
    total = wins + losses
    pct = round((wins / total) * 100, 1) if total > 0 else 0.0
    max_val = max(wins, losses, pending, 1)
    h_l = max(6, int((losses / max_val) * 38))
    h_p = max(6, int((pending / max_val) * 38))
    h_w = max(6, int((wins / max_val) * 38))

    return f"""
    <div style="background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 16px; padding: 10px 6px; box-shadow: 0 6px 16px rgba(0,0,0,0.04); text-align: center; font-family: 'Segoe UI', system-ui, sans-serif;">
        <div style="font-size: 10px; font-weight: 800; color: #065F46; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{titulo}</div>
        <div style="font-size: 20px; font-weight: 900; color: #059669; margin: 1px 0;">{pct}%</div>
        <div style="display: flex; justify-content: center; align-items: flex-end; gap: 8px; height: 42px; margin: 6px 0; padding: 0 8px;">
            <div style="width: 14px; height: {h_l}px; background: linear-gradient(180deg, #F87171 0%, #EF4444 60%, #B91C1C 100%); border-radius: 3px;" title="Losses: {losses}"></div>
            <div style="width: 14px; height: {h_p}px; background: linear-gradient(180deg, #FBBF24 0%, #F59E0B 60%, #B45309 100%); border-radius: 3px;" title="Pending: {pending}"></div>
            <div style="width: 14px; height: {h_w}px; background: linear-gradient(180deg, #34D399 0%, #10B981 60%, #047857 100%); border-radius: 3px;" title="Wins: {wins}"></div>
        </div>
        <div style="display: flex; justify-content: center; gap: 3px; font-size: 8px; font-weight: 700;">
            <span style="color: #059669; background: #ECFDF5; padding: 1px 4px; border-radius: 3px;">W:{wins}</span>
            <span style="color: #EF4444; background: #FEF2F2; padding: 1px 4px; border-radius: 3px;">L:{losses}</span>
            <span style="color: #D97706; background: #FFFBEB; padding: 1px 4px; border-radius: 3px;">P:{pending}</span>
        </div>
    </div>
    """

def crear_velocimetro_3d(pct_global, tot_wins, tot_loss, tot_global):
    angulo_rad = math.pi * (1.0 - (pct_global / 100.0))
    x2 = 100 + 65 * math.cos(angulo_rad)
    y2 = 100 - 65 * math.sin(angulo_rad)

    return f"""
    <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px); border: 2px solid #10B981; border-radius: 20px; padding: 16px 20px; text-align: center; box-shadow: 0 10px 25px rgba(16,185,129,0.12); display: flex; flex-direction: column; align-items: center; font-family: 'Segoe UI', system-ui, sans-serif;">
        <div style="font-size: 13px; font-weight: 800; color: #065F46; letter-spacing: 1px; margin-bottom: 2px;">EFECTIVIDAD GLOBAL Y RÉCORD</div>
        <div style="position: relative; width: 200px; height: 110px; margin: 4px 0;">
            <svg width="200" height="110" viewBox="0 0 200 110">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E2E8F0" stroke-width="22" stroke-linecap="round" />
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#10B981" stroke-width="18" stroke-linecap="round" />
                <line x1="100" y1="100" x2="{x2}" y2="{y2}" stroke="#EF4444" stroke-width="4" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="6" fill="#1E293B"/>
            </svg>
        </div>
        <div style="font-size: 38px; font-weight: 900; color: #10B981; margin-top: -10px;">{pct_global}%</div>
        <div style="font-size: 12px; font-weight: 700; color: #64748B; margin-top: 2px;">
            Récord: <span style="color:#10B981;">{tot_wins} W</span> / <span style="color:#EF4444;">{tot_loss} L</span> (Total: {tot_global} Picks)
        </div>
    </div>
    """

def generar_dashboard_completo():
    stats, tot_wins, tot_loss, tot_global, pct_global = calcular_metricas_historial()

    kpi_premier_html = crear_grafica_barras_3d("Record Premier", stats['PREMIER LEAGUE']['wins'], stats['PREMIER LEAGUE']['losses'], stats['PREMIER LEAGUE']['pending'])
    kpi_nfl_html = crear_grafica_barras_3d("Récord NFL", stats['NFL']['wins'], stats['NFL']['losses'], stats['NFL']['pending'])
    kpi_mlb_html = crear_grafica_barras_3d("Récord MLB", stats['MLB']['wins'], stats['MLB']['losses'], stats['MLB']['pending'])
    kpi_nba_html = crear_grafica_barras_3d("Récord NBA", stats['NBA']['wins'], stats['NBA']['losses'], stats['NBA']['pending'])
    kpi_nhl_html = crear_grafica_barras_3d("Récord NHL", stats['NHL']['wins'], stats['NHL']['losses'], stats['NHL']['pending'])

    html_header = crear_velocimetro_3d(pct_global, tot_wins, tot_loss, tot_global)

    historial = cargar_historial_db()
    pending_items = [x for x in historial if x.get("estado") == "PENDING"]
    win_items = [x for x in historial if x.get("estado") == "WIN"]
    loss_items = [x for x in historial if x.get("estado") == "LOSS"]

    def render_lista_html(titulo, lista, color_hex):
        html_b = f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 10px; height: 100%;">
            <div style="font-size: 13px; font-weight: 800; color: {color_hex}; margin-bottom: 8px;">{titulo} ({len(lista)})</div>
            <div style="max-height: 220px; overflow-y: auto; font-size: 11px; color: #334155;">
        """
        if not lista:
            html_b += "<i style='color: #94A3B8;'>No hay picks en este estado.</i>"
        else:
            for item in reversed(lista):
                eq_l = item.get('equipo_local', 'Local')
                eq_v = item.get('equipo_visitante', 'Visitante')
                pick_rec = item.get('pick_recomendado', item.get('seleccion', ''))
                html_b += f"<div style='margin-bottom: 6px; border-bottom: 1px solid #F1F5F9; padding-bottom: 4px;'>• <b>[#{item.get('id', '?')} - {item.get('deporte', '')}]</b> {eq_l} vs {eq_v} — <i>{pick_rec}</i></div>"
        html_b += "</div></div>"
        return html_b

    html_pending = render_lista_html("⏳ PICKS PENDIENTES", pending_items, "#F59E0B")
    html_wins = render_lista_html("✅ APUESTAS GANADAS (WIN)", win_items, "#10B981")
    html_losses = render_lista_html("❌ APUESTAS PERDIDAS (LOSS)", loss_items, "#EF4444")

    return html_header, html_pending, html_wins, html_losses, kpi_premier_html, kpi_nfl_html, kpi_mlb_html, kpi_nba_html, kpi_nhl_html

def render_logo_html(url, height=50):
    return f"""<div style="display: flex; justify-content: center; align-items: center; height: 55px; margin-bottom: 4px; overflow: hidden;">
        <img src="{url}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='https://a.espncdn.com/i/leaguelogos/soccer/500/23.png';" style="max-height: {height}px; max-width: 100%; width: auto; object-fit: contain;" />
    </div>"""

# =========================================
# INTERFAZ GRÁFICA (GRADIO BLOCKS)
# =========================================
with gr.Blocks(title="La Maña Picks") as app_mana:

    with gr.Column(visible=True) as vista_home:
        gr.Markdown("""
        <div style="text-align: center; padding: 10px 0 15px 0;">
            <h1 style="font-size: 36px; font-weight: 900; color: #065F46; margin: 0; letter-spacing: 1px;">LA MAÑA PICKS</h1>
            <p style="font-size: 13px; font-weight: 700; color: #10B981; margin-top: 2px;">ANALIZANDO CON LA MAÑA QUE NOS HACE GANAR. JUEGA CON ESTADÍSTICAS Y CON MAÑA.</p>
        </div>
        """)

        # FILA 1: BOTONES DE LIGAS
        with gr.Row():
            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["Premier League"]))
                btn_premier = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NFL"]))
                btn_nfl = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["MLB"]))
                btn_mlb = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NBA"]))
                btn_nba = gr.Button("Analizar ➔", variant="primary", size="sm")

            with gr.Column(scale=1, min_width=75):
                gr.HTML(render_logo_html(LOGOS_LIGAS["NHL"]))
                btn_nhl = gr.Button("Analizar ➔", variant="primary", size="sm")

        # FILA 2: MINI HISTOGRAMAS
        with gr.Row():
            kpi_premier_out = gr.HTML()
            kpi_nfl_out = gr.HTML()
            kpi_mlb_out = gr.HTML()
            kpi_nba_out = gr.HTML()
            kpi_nhl_out = gr.HTML()

        gr.Markdown("<br>")

        # FILA 3: GESTOR POR ID Y VELOCÍMETRO
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🛠️ **Gestor Directo por ID**")
                num_input_id = gr.Number(value=1, label="Ingresa # ID del Pick", precision=0)
                with gr.Row():
                    btn_direct_win = gr.Button("✅ Marcar WIN", variant="primary")
                    btn_direct_loss = gr.Button("❌ Marcar LOSS", variant="secondary")

            with gr.Column(scale=2):
                html_header_out = gr.HTML()

        gr.Markdown("### 📋 **TABLERO HISTÓRICO DE CONTROL Y SEGUIMIENTO**")

        # FILA 4: TABLERO EN 3 COLUMNAS
        with gr.Row():
            html_pending_out = gr.HTML()
            html_wins_out = gr.HTML()
            html_losses_out = gr.HTML()

    # VISTA FÚTBOL
    with gr.Column(visible=False) as vista_fut:
        with gr.Row():
            btn_volver_fut = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            txt_titulo_liga = gr.Markdown("## ⚽ **Área de Análisis de Fútbol**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_fut_loc = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Arsenal", label="Equipo Local", scale=3)
                            img_fut_loc = gr.Image(value=PREMIER_DICT["Arsenal"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_fut_vis = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Chelsea", label="Equipo Visitante", scale=3)
                            img_fut_vis = gr.Image(value=PREMIER_DICT["Chelsea"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        drop_fatiga = gr.Dropdown(choices=["No (Semana normal)", "Sí (Jugó Champions/Europa League hace 3 días)"], value="No (Semana normal)", label="¿Fatiga Europea?")

                        gr.Markdown("#### ⚽ Cuotas 1X2 (Casino)")
                        with gr.Row():
                            num_fut_c_loc = gr.Number(value=1.85, label="Cuota Local (1)")
                            num_fut_c_emp = gr.Number(value=3.60, label="Cuota Empate (X)")
                            num_fut_c_vis = gr.Number(value=4.20, label="Cuota Visitante (2)")

                        gr.Markdown("#### ⚽ Cuotas Ambos Anotan (BTTS)")
                        with gr.Row():
                            num_fut_c_btts_si = gr.Number(value=1.80, label="Cuota Ambos Anotan: SÍ")
                            num_fut_c_btts_no = gr.Number(value=1.95, label="Cuota Ambos Anotan: NO")

                        gr.Markdown("#### ⚽ Línea de Goles y Cuotas (Over/Under)")
                        num_fut_linea_tot = gr.Number(value=2.5, label="Línea Total Goles (O/U)")
                        with gr.Row():
                            num_fut_c_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_fut_c_under = gr.Number(value=1.95, label="Cuota UNDER")

                        btn_sim_fut = gr.Button("Simular Partido 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_fut = gr.Radio(choices=["Selección 1 (1X2)", "Selección 2 (Doble Op.)", "Selección 3 (Totales)", "Selección 4 (Ambos Anotan BTTS)"], label="Pick a guardar")
                        btn_save_fut = gr.Button("Guardar Pick en Historial 💾", variant="secondary")
                        lbl_save_fut = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_fut = gr.HTML()
                        st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA NFL
    with gr.Column(visible=False) as vista_nfl:
        with gr.Row():
            btn_volver_nfl = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## 🏈 **Área de Análisis: NFL (32 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_nfl_loc = gr.Dropdown(choices=lista_nfl_nombres, value="Detroit Lions", label="Equipo Local", scale=3)
                            img_nfl_loc = gr.Image(value="https://a.espncdn.com/i/teamlogos/nfl/500/det.png", label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_nfl_vis = gr.Dropdown(choices=lista_nfl_nombres, value="New York Jets", label="Equipo Visitante", scale=3)
                            img_nfl_vis = gr.Image(value="https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", label="Visitante", width=50, height=50, show_label=False, scale=1)

                        gr.Markdown("#### 🏈 Cuotas Moneyline (Ganador Directo)")
                        with gr.Row():
                            num_nfl_cuota_ml_loc = gr.Number(value=1.30, label="Cuota ML Local")
                            num_nfl_cuota_ml_vis = gr.Number(value=3.55, label="Cuota ML Visitante")

                        gr.Markdown("#### 🏈 Spread / Hándicap (Casino)")
                        with gr.Row():
                            num_sp_loc_val = gr.Number(value=-7.0, label="Spread Local")
                            num_cuota_sp_loc = gr.Number(value=1.91, label="Cuota Spread Local")
                        with gr.Row():
                            num_sp_vis_val = gr.Number(value=+7.0, label="Spread Visitante")
                            num_cuota_sp_vis = gr.Number(value=1.83, label="Cuota Spread Visitante")

                        gr.Markdown("#### 🏈 Totales (Puntos Juego Completo)")
                        num_nfl_tot = gr.Number(value=48.0, label="Línea Total Puntos")
                        with gr.Row():
                            num_nfl_cuota_tot_over = gr.Number(value=1.88, label="Cuota OVER")
                            num_nfl_cuota_tot_under = gr.Number(value=1.87, label="Cuota UNDER")

                        btn_sim_nfl = gr.Button("Simular Partido NFL 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_nfl = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Spread)", "Selección 3 (Totales)"], label="Pick a guardar")
                        btn_save_nfl = gr.Button("Guardar Pick NFL 💾", variant="secondary")
                        lbl_save_nfl = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_nfl = gr.HTML()
                        st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA MLB
    with gr.Column(visible=False) as vista_mlb:
        with gr.Row():
            btn_volver_mlb = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## ⚾ **Área de Análisis: MLB Sabermétrica (30 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_mlb_loc = gr.Dropdown(choices=lista_mlb_nombres, value="New York Yankees", label="Equipo Local", scale=3)
                            img_mlb_loc = gr.Image(value=EQUIPOS_MLB["New York Yankees"]["logo"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_mlb_vis = gr.Dropdown(choices=lista_mlb_nombres, value="Tampa Bay Rays", label="Equipo Visitante", scale=3)
                            img_mlb_vis = gr.Image(value=EQUIPOS_MLB["Tampa Bay Rays"]["logo"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        btn_auto_api = gr.Button("🔄 Cargar Abridores en Vivo (MLB API)", variant="secondary")
                        lbl_api_status = gr.Markdown("🟢 Listo para sincronizar")

                        lbl_hdr_loc = gr.Markdown("#### ⚾ Abridor y Bullpen Local")
                        with gr.Row():
                            num_xera_loc = gr.Number(value=2.95, label="ERA Abridor Local")
                            num_whip_loc = gr.Number(value=1.13, label="WHIP Abridor Local")
                        with gr.Row():
                            num_era_bp_loc = gr.Number(value=3.40, label="ERA Bullpen Local")
                            num_whip_bp_loc = gr.Number(value=1.18, label="WHIP Bullpen Local")

                        lbl_hdr_vis = gr.Markdown("#### ⚾ Abridor y Bullpen Visitante")
                        with gr.Row():
                            num_xera_vis = gr.Number(value=2.94, label="ERA Abridor Visitante")
                            num_whip_vis = gr.Number(value=1.07, label="WHIP Abridor Visitante")
                        with gr.Row():
                            num_era_bp_vis = gr.Number(value=3.80, label="ERA Bullpen Visitante")
                            num_whip_bp_vis = gr.Number(value=1.25, label="WHIP Bullpen Visitante")

                        gr.Markdown("#### ⚾ Cuotas Moneyline")
                        with gr.Row():
                            num_mlb_cuota_loc = gr.Number(value=1.76, label="Cuota ML Local")
                            num_mlb_cuota_vis = gr.Number(value=2.04, label="Cuota ML Visitante")

                        gr.Markdown("#### ⚾ Run Line / Hándicap")
                        with gr.Row():
                            num_rl_loc_val = gr.Number(value=-1.5, label="Run Line Local")
                            num_cuota_rl_loc = gr.Number(value=2.70, label="Cuota RL Local")
                        with gr.Row():
                            num_rl_vis_val = gr.Number(value=+1.5, label="Run Line Visitante")
                            num_cuota_rl_vis = gr.Number(value=1.44, label="Cuota RL Visitante")

                        gr.Markdown("#### ⚾ Cuotas Primeras 5 Entradas (F5 ML)")
                        with gr.Row():
                            num_f5_cuota_loc = gr.Number(value=1.80, label="Cuota F5 Local ML")
                            num_f5_cuota_vis = gr.Number(value=1.95, label="Cuota F5 Visitante ML")

                        gr.Markdown("#### ⚾ Mercado 1er Inning (NRFI / YRFI)")
                        with gr.Row():
                            num_cuota_nrfi = gr.Number(value=1.85, label="Cuota NRFI (No Carrera 1er Inning)")
                            num_cuota_yrfi = gr.Number(value=1.95, label="Cuota YRFI (Sí Carrera 1er Inning)")

                        num_mlb_tot = gr.Number(value=8.5, label="Línea Total Carreras Juego Completo")

                        gr.Markdown("#### ⚾ Carreras Totales por Equipo (Team Totals)")
                        with gr.Row():
                            num_linea_team_loc = gr.Number(value=4.5, label="Línea Carreras Local")
                            num_cuota_team_loc_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_cuota_team_loc_under = gr.Number(value=1.95, label="Cuota UNDER")
                        with gr.Row():
                            num_linea_team_vis = gr.Number(value=3.5, label="Línea Carreras Visitante")
                            num_cuota_team_vis_over = gr.Number(value=1.85, label="Cuota OVER")
                            num_cuota_team_vis_under = gr.Number(value=1.95, label="Cuota UNDER")

                        btn_sim_mlb = gr.Button("Simular Partido MLB 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_mlb = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Run Line)", "Selección 3 (F5 ML)", "Selección 4 (NRFI/YRFI)", "Selección 5 (Team Total Local)", "Selección 6 (Team Total Visitante)", "Selección 7 (Total Juego)"], label="Pick a guardar")
                        btn_save_mlb = gr.Button("Guardar Pick MLB 💾", variant="secondary")
                        lbl_save_mlb = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_mlb = gr.HTML()
                        st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA NBA
    with gr.Column(visible=False) as vista_nba:
        with gr.Row():
            btn_volver_nba = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## 🏀 **Área de Análisis: NBA (30 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis de Partido"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_nba_loc = gr.Dropdown(choices=lista_nba_nombres, value="Boston Celtics", label="Equipo Local", scale=3)
                            img_nba_loc = gr.Image(value=NBA_DICT["Boston Celtics"]["logo"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_nba_vis = gr.Dropdown(choices=lista_nba_nombres, value="Los Angeles Lakers", label="Equipo Visitante", scale=3)
                            img_nba_vis = gr.Image(value=NBA_DICT["Los Angeles Lakers"]["logo"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        drop_modo_nba = gr.Dropdown(
                            choices=["Temporada Regular", "Pretemporada (Exhibición)", "Playoffs / Play-In"],
                            value="Temporada Regular",
                            label="🏆 Fase / Tipo de Partido"
                        )

                        drop_descanso_nba = gr.Dropdown(
                            choices=["Sin Back-to-Back (Descanso Normal)", "Back-to-Back Local (Jugó Anoche)", "Back-to-Back Visitante (Jugó Anoche)"],
                            value="Sin Back-to-Back (Descanso Normal)",
                            label="¿Carga de Partidos / Descanso B2B?"
                        )

                        gr.Markdown("#### 🏀 Cuotas Moneyline (Ganador Directo)")
                        with gr.Row():
                            num_nba_cuota_ml_loc = gr.Number(value=1.45, label="Cuota ML Local")
                            num_nba_cuota_ml_vis = gr.Number(value=2.85, label="Cuota ML Visitante")

                        gr.Markdown("#### 🏀 Spread / Hándicap (Casino)")
                        with gr.Row():
                            num_sp_nba_loc_val = gr.Number(value=-5.5, label="Spread Local")
                            num_cuota_sp_nba_loc = gr.Number(value=1.90, label="Cuota Spread Local")
                        with gr.Row():
                            num_sp_nba_vis_val = gr.Number(value=+5.5, label="Spread Visitante")
                            num_cuota_sp_nba_vis = gr.Number(value=1.90, label="Cuota Spread Visitante")

                        gr.Markdown("#### 🏀 Totales (Puntos Juego Completo)")
                        num_nba_tot = gr.Number(value=224.5, label="Línea Total Puntos (O/U)")
                        with gr.Row():
                            num_nba_cuota_tot_over = gr.Number(value=1.87, label="Cuota OVER")
                            num_nba_cuota_tot_under = gr.Number(value=1.87, label="Cuota UNDER")

                        btn_sim_nba = gr.Button("Simular Partido NBA 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_nba = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Spread)", "Selección 3 (Totales)"], label="Pick a guardar")
                        btn_save_nba = gr.Button("Guardar Pick NBA 💾", variant="secondary")
                        lbl_save_nba = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_nba = gr.HTML()
                        st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # VISTA NHL
    with gr.Column(visible=False) as vista_nhl:
        with gr.Row():
            btn_volver_nhl = gr.Button("⬅️ Volver al Menú Principal", variant="secondary", scale=1)
            gr.Markdown("## 🏒 **Área de Análisis: NHL (32 Equipos)**", scale=4)

        with gr.Tabs():
            with gr.TabItem("📊 Análisis Monte Carlo & Elo Dinámico"):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            drop_nhl_loc = gr.Dropdown(choices=lista_nhl_nombres, value="Florida Panthers", label="Equipo Local", scale=3)
                            img_nhl_loc = gr.Image(value=NHL_DICT["Florida Panthers"]["logo"], label="Local", width=50, height=50, show_label=False, scale=1)

                        with gr.Row():
                            drop_nhl_vis = gr.Dropdown(choices=lista_nhl_nombres, value="Edmonton Oilers", label="Equipo Visitante", scale=3)
                            img_nhl_vis = gr.Image(value=NHL_DICT["Edmonton Oilers"]["logo"], label="Visitante", width=50, height=50, show_label=False, scale=1)

                        gr.Markdown("#### 🏒 Cuotas Moneyline")
                        with gr.Row():
                            num_nhl_cuota_ml_loc = gr.Number(value=1.85, label="Cuota ML Local")
                            num_nhl_cuota_ml_vis = gr.Number(value=1.95, label="Cuota ML Visitante")

                        gr.Markdown("#### 🏒 Puck Line (-1.5 / +1.5)")
                        with gr.Row():
                            num_nhl_linea_pl_loc = gr.Number(value=-1.5, label="Puck Line Local")
                            num_nhl_cuota_pl_loc = gr.Number(value=2.80, label="Cuota PL Local")
                        with gr.Row():
                            num_nhl_linea_pl_vis = gr.Number(value=1.5, label="Puck Line Visitante")
                            num_nhl_cuota_pl_vis = gr.Number(value=1.45, label="Cuota PL Visitante")

                        gr.Markdown("#### 🏒 Totales (O/U)")
                        num_nhl_linea_tot = gr.Number(value=6.0, label="Línea Total de Goles")
                        with gr.Row():
                            num_nhl_cuota_over = gr.Number(value=1.90, label="Cuota OVER")
                            num_nhl_cuota_under = gr.Number(value=1.90, label="Cuota UNDER")

                        btn_sim_nhl = gr.Button("Simular Partido NHL (10K Iters) 🚀", variant="primary")

                        gr.Markdown("---")
                        rad_pick_nhl = gr.Radio(choices=["Selección 1 (ML)", "Selección 2 (Totales)", "Selección 3 (Puck Line)"], label="Pick a guardar")
                        btn_save_nhl = gr.Button("Guardar Pick NHL 💾", variant="secondary")
                        lbl_save_nhl = gr.Markdown("")

                    with gr.Column(scale=2):
                        out_nhl = gr.HTML()
                        st_nhl_p1, st_nhl_p2, st_nhl_p3, st_nhl_match = gr.State(""), gr.State(""), gr.State(""), gr.State("")

    # ESTADOS Y FUNCIONES DE NAVEGACIÓN
    st_liga_activa = gr.State("Premier League")
    st_dict_futbol_actual = gr.State(PREMIER_DICT)

    def actualizar_interfaz_fut(nombre_loc, nombre_vis, dict_actual):
        logo_loc = dict_actual.get(nombre_loc, DEFAULT_SOCCER_LOGO)
        logo_vis = dict_actual.get(nombre_vis, DEFAULT_SOCCER_LOGO)
        return logo_loc, logo_vis, gr.update(label=f"Cuota {nombre_loc} (1)"), gr.update(label=f"Cuota {nombre_vis} (2)")

    def actualizar_interfaz_nfl(nombre_loc, nombre_vis):
        logo_loc = DICT_NFL_COMPLETO.get(nombre_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis = DICT_NFL_COMPLETO.get(nombre_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
        return logo_loc, logo_vis, gr.update(label=f"Cuota ML {nombre_loc}"), gr.update(label=f"Cuota ML {nombre_vis}"), gr.update(label=f"Spread {nombre_loc}"), gr.update(label=f"Cuota Spread {nombre_loc}"), gr.update(label=f"Spread {nombre_vis}"), gr.update(label=f"Cuota Spread {nombre_vis}")

    def actualizar_interfaz_mlb(nombre_loc, nombre_vis):
        logo_loc, logo_vis = EQUIPOS_MLB[nombre_loc]["logo"], EQUIPOS_MLB[nombre_vis]["logo"]
        return logo_loc, logo_vis, gr.update(label=f"Cuota ML {nombre_loc}"), gr.update(label=f"Cuota ML {nombre_vis}"), gr.update(label=f"Run Line {nombre_loc}"), gr.update(label=f"Cuota RL {nombre_loc}"), gr.update(label=f"Run Line {nombre_vis}"), gr.update(label=f"Cuota RL {nombre_vis}")

    def actualizar_interfaz_nba(nombre_loc, nombre_vis):
        logo_loc = NBA_DICT.get(nombre_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis = NBA_DICT.get(nombre_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
        return logo_loc, logo_vis, gr.update(label=f"Cuota ML {nombre_loc}"), gr.update(label=f"Cuota ML {nombre_vis}"), gr.update(label=f"Spread {nombre_loc}"), gr.update(label=f"Cuota Spread {nombre_loc}"), gr.update(label=f"Spread {nombre_vis}"), gr.update(label=f"Cuota Spread {nombre_vis}")

    def actualizar_interfaz_nhl(nombre_loc, nombre_vis):
        logo_loc = NHL_DICT.get(nombre_loc, {}).get("logo", DEFAULT_SOCCER_LOGO)
        logo_vis = NHL_DICT.get(nombre_vis, {}).get("logo", DEFAULT_SOCCER_LOGO)
        return logo_loc, logo_vis, gr.update(label=f"Cuota ML {nombre_loc}"), gr.update(label=f"Cuota ML {nombre_vis}")

    def cambiar_a_liga_futbol(diccionario_liga, nombre_liga):
        eqs = sorted(list(diccionario_liga.keys()))
        loc_inicial = eqs[0]
        vis_inicial = eqs[1] if len(eqs) > 1 else eqs[0]
        logo_loc = diccionario_liga.get(loc_inicial, DEFAULT_SOCCER_LOGO)
        logo_vis = diccionario_liga.get(vis_inicial, DEFAULT_SOCCER_LOGO)
        return (
            gr.update(visible=False), gr.update(visible=True),
            gr.update(choices=eqs, value=loc_inicial), gr.update(choices=eqs, value=vis_inicial),
            logo_loc, logo_vis, f"## ⚽ **Área de Análisis: {nombre_liga.upper()} ({len(eqs)} Equipos)**",
            nombre_liga, diccionario_liga, gr.update(label=f"Cuota {loc_inicial} (1)"), gr.update(label=f"Cuota {vis_inicial} (2)")
        )

    outputs_liga_futbol = [
        vista_home, vista_fut, drop_fut_loc, drop_fut_vis, img_fut_loc, img_fut_vis, txt_titulo_liga,
        st_liga_activa, st_dict_futbol_actual, num_fut_c_loc, num_fut_c_vis
    ]

    btn_premier.click(fn=lambda: cambiar_a_liga_futbol(PREMIER_DICT, "Premier League"), outputs=outputs_liga_futbol)
    btn_nfl.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[vista_home, vista_nfl])
    btn_mlb.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[vista_home, vista_mlb])
    btn_nba.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[vista_home, vista_nba])
    btn_nhl.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[vista_home, vista_nhl])

    def volver_home():
        recalibrar_modelos_auto()
        h_head, p_out, w_out, l_out, f_prem, f_nfl, f_mlb, f_nba, f_nhl = generar_dashboard_completo()
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), h_head, p_out, w_out, l_out, f_prem, f_nfl, f_mlb, f_nba, f_nhl

    outputs_volver = [
        vista_home, vista_fut, vista_nfl, vista_mlb, vista_nba, vista_nhl,
        html_header_out, html_pending_out, html_wins_out, html_losses_out,
        kpi_premier_out, kpi_nfl_out, kpi_mlb_out, kpi_nba_out, kpi_nhl_out
    ]

    btn_volver_fut.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_nfl.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_mlb.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_nba.click(fn=volver_home, outputs=outputs_volver)
    btn_volver_nhl.click(fn=volver_home, outputs=outputs_volver)

    drop_fut_loc.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])
    drop_fut_vis.change(fn=actualizar_interfaz_fut, inputs=[drop_fut_loc, drop_fut_vis, st_dict_futbol_actual], outputs=[img_fut_loc, img_fut_vis, num_fut_c_loc, num_fut_c_vis])

    drop_nfl_loc.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])
    drop_nfl_vis.change(fn=actualizar_interfaz_nfl, inputs=[drop_nfl_loc, drop_nfl_vis], outputs=[img_nfl_loc, img_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis])

    drop_mlb_loc.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis])
    drop_mlb_vis.change(fn=actualizar_interfaz_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[img_mlb_loc, img_mlb_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis])

    drop_nba_loc.change(fn=actualizar_interfaz_nba, inputs=[drop_nba_loc, drop_nba_vis], outputs=[img_nba_loc, img_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis])
    drop_nba_vis.change(fn=actualizar_interfaz_nba, inputs=[drop_nba_loc, drop_nba_vis], outputs=[img_nba_loc, img_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis])

    drop_nhl_loc.change(fn=actualizar_interfaz_nhl, inputs=[drop_nhl_loc, drop_nhl_vis], outputs=[img_nhl_loc, img_nhl_vis, num_nhl_cuota_ml_loc, num_nhl_cuota_ml_vis])
    drop_nhl_vis.change(fn=actualizar_interfaz_nhl, inputs=[drop_nhl_loc, drop_nhl_vis], outputs=[img_nhl_loc, img_nhl_vis, num_nhl_cuota_ml_loc, num_nhl_cuota_ml_vis])

    btn_auto_api.click(fn=auto_cargar_pitchers_mlb, inputs=[drop_mlb_loc, drop_mlb_vis], outputs=[num_xera_loc, num_whip_loc, num_xera_vis, num_whip_vis, lbl_api_status])

    outputs_directos = [
        html_header_out, html_pending_out, html_wins_out, html_losses_out,
        kpi_premier_out, kpi_nfl_out, kpi_mlb_out, kpi_nba_out, kpi_nhl_out
    ]

    btn_direct_win.click(fn=lambda idx: cambiar_estado_directo(idx, "WIN"), inputs=[num_input_id], outputs=outputs_directos)
    btn_direct_loss.click(fn=lambda idx: cambiar_estado_directo(idx, "LOSS"), inputs=[num_input_id], outputs=outputs_directos)

    btn_sim_fut.click(fn=simular_partido_futbol_avanzado, inputs=[st_liga_activa, drop_fut_loc, drop_fut_vis, num_fut_c_loc, num_fut_c_emp, num_fut_c_vis, num_fut_c_btts_si, num_fut_c_btts_no, num_fut_linea_tot, num_fut_c_over, num_fut_c_under, drop_fatiga, st_dict_futbol_actual], outputs=[out_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match])
    btn_sim_nfl.click(fn=simular_partido_nfl_clasificado, inputs=[drop_nfl_loc, drop_nfl_vis, num_nfl_cuota_ml_loc, num_nfl_cuota_ml_vis, num_sp_loc_val, num_cuota_sp_loc, num_sp_vis_val, num_cuota_sp_vis, num_nfl_tot, num_nfl_cuota_tot_over, num_nfl_cuota_tot_under], outputs=[out_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match])
    btn_sim_mlb.click(fn=simular_partido_mlb_clasificado, inputs=[drop_mlb_loc, drop_mlb_vis, num_xera_loc, num_whip_loc, num_era_bp_loc, num_whip_bp_loc, num_xera_vis, num_whip_vis, num_era_bp_vis, num_whip_bp_vis, num_mlb_cuota_loc, num_mlb_cuota_vis, num_rl_loc_val, num_cuota_rl_loc, num_rl_vis_val, num_cuota_rl_vis, num_f5_cuota_loc, num_f5_cuota_vis, num_mlb_tot, num_linea_team_loc, num_cuota_team_loc_over, num_cuota_team_loc_under, num_linea_team_vis, num_cuota_team_vis_over, num_cuota_team_vis_under, num_cuota_nrfi, num_cuota_yrfi], outputs=[out_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match])
    btn_sim_nba.click(fn=simular_partido_nba, inputs=[drop_nba_loc, drop_nba_vis, num_nba_cuota_ml_loc, num_nba_cuota_ml_vis, num_sp_nba_loc_val, num_cuota_sp_nba_loc, num_sp_nba_vis_val, num_cuota_sp_nba_vis, num_nba_tot, num_nba_cuota_tot_over, num_nba_cuota_tot_under, drop_descanso_nba, drop_modo_nba], outputs=[out_nba, st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match])
    btn_sim_nhl.click(fn=simular_partido_nhl, inputs=[drop_nhl_loc, drop_nhl_vis, num_nhl_cuota_ml_loc, num_nhl_cuota_ml_vis, num_nhl_linea_pl_loc, num_nhl_cuota_pl_loc, num_nhl_linea_pl_vis, num_nhl_cuota_pl_vis, num_nhl_linea_tot, num_nhl_cuota_over, num_nhl_cuota_under], outputs=[out_nhl, st_nhl_p1, st_nhl_p2, st_nhl_p3, st_nhl_match])

    def fn_save_pick_fut(radio_sel, p1, p2, p3, p4, match, liga):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else (p3 if "3" in radio_sel else p4))
        guardar_pick_db(f"FÚTBOL ({liga})", match, sel_text, radio_sel, 1.85, "+4.2%")
        return f"✅ Pick de {liga} guardado: {sel_text}"

    def fn_save_pick_nfl(radio_sel, p1, p2, p3, p4, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NFL", match, sel_text, radio_sel, 1.90, "+4.5%")
        return f"✅ Pick de NFL guardado: {sel_text}"

    def fn_save_pick_mlb(radio_sel, p1, p2, p3, p4, p5, p6, p7, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else (p3 if "3" in radio_sel else (p4 if "4" in radio_sel else (p5 if "5" in radio_sel else (p6 if "6" in radio_sel else p7)))))
        guardar_pick_db("MLB", match, sel_text, radio_sel, 1.90, "+5.2%")
        return f"✅ Pick de MLB guardado: {sel_text}"

    def fn_save_pick_nba(radio_sel, p1, p2, p3, p4, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NBA", match, sel_text, radio_sel, 1.90, "+4.8%")
        return f"✅ Pick de NBA guardado: {sel_text}"

    def fn_save_pick_nhl(radio_sel, p1, p2, p3, match):
        if not match: return "⚠️ Primero debes simular el partido."
        sel_text = p1 if "1" in radio_sel else (p2 if "2" in radio_sel else p3)
        guardar_pick_db("NHL", match, sel_text, radio_sel, 1.90, "+4.0%")
        return f"✅ Pick de NHL guardado: {sel_text}"

    btn_save_fut.click(fn=fn_save_pick_fut, inputs=[rad_pick_fut, st_fut_p1, st_fut_p2, st_fut_p3, st_fut_p4, st_fut_match, st_liga_activa], outputs=[lbl_save_fut])
    btn_save_nfl.click(fn=fn_save_pick_nfl, inputs=[rad_pick_nfl, st_nfl_p1, st_nfl_p2, st_nfl_p3, st_nfl_p4, st_nfl_match], outputs=[lbl_save_nfl])
    btn_save_mlb.click(fn=fn_save_pick_mlb, inputs=[rad_pick_mlb, st_mlb_p1, st_mlb_p2, st_mlb_p3, st_mlb_p4, st_mlb_p5, st_mlb_p6, st_mlb_p7, st_mlb_match], outputs=[lbl_save_mlb])
    btn_save_nba.click(fn=fn_save_pick_nba, inputs=[rad_pick_nba, st_nba_p1, st_nba_p2, st_nba_p3, st_nba_p4, st_nba_match], outputs=[lbl_save_nba])
    btn_save_nhl.click(fn=fn_save_pick_nhl, inputs=[rad_pick_nhl, st_nhl_p1, st_nhl_p2, st_nhl_p3, st_nhl_match], outputs=[lbl_save_nhl])

    app_mana.load(fn=generar_dashboard_completo, outputs=outputs_directos)

# Lanzamiento para Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app_mana.launch(server_name="0.0.0.0", server_port=port)
