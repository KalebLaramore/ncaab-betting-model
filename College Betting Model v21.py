# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 00:07:23 2026

@author: klara
"""



# -*- coding: utf-8 -*-
import os
import re
from typing import Dict, List, Optional, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

# ============================================================
# CONFIG (edit only this section)
# ============================================================

ODDS_API_KEY = "ODDS_API_KEY"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"

SPORT_KEY = "basketball_ncaab"

# Broaden region coverage
REGION = "us,us2"

# include h2h so events don’t disappear when spreads/totals aren’t posted yet
MARKETS = "spreads,totals,h2h"

ODDS_FORMAT = "american"
DATE_FORMAT = "iso"

HTML_FOLDER = r"C:\Users\klara"
TORVIK_HTML_TODAY = os.path.join(HTML_FOLDER, "torvik_schedule_today.html")
TORVIK_HTML_TOMORROW = os.path.join(HTML_FOLDER, "torvik_schedule_tomorrow.html")

SLATE_MODE = "today"  # "today" | "tomorrow" | "both"

# ---- SIDE filters (your core rules) ----
MIN_SIDE_PROB = 0.70
MIN_SIDE_EDGE = 3.5

# ---- TOTALS filters (updated to stop bad UNDERS) ----
MIN_OVER_EDGE = 6.5
MIN_UNDER_EDGE = 10.0

LOW_TOTAL_CUTOFF = 142.0
LOW_TOTAL_UNDER_EDGE = 14.0

MAX_UNDER_BLOWOUT_SPREAD = 0.0

# ---- ML filter (updated) ----
MIN_ML_PROB = 0.65
MAX_ML_FAV_SPREAD = 3.0
MIN_ML_SPREAD_EDGE = 1.0  # Torvik spread must be >= 1 point better than DK

MATCH_MIN_SCORE = 78

# DK-first but fallback to any book so games don’t “disappear”
FALLBACK_TO_ANY_BOOK = True

NETWORK_TAIL_PATTERN = re.compile(
    r"""
    \b(
        # Major networks / streams
        espn\+|espn2|espn|espnu|espnews|
        cbssn|cbs|fox|fs1|fs2|btn|accn|secn|
        acc\ network|sec\ network|big\ ten\ network|pac\-?12|p12|
        peacock|tru(tv)?|tbs|tnt|
        flosports|flo\s?sports|
        msgsn|msg|msg2|sny|
        # Conf/league networks
        mwn|mw\ network|
        summit\ league\ network|
        # Altitude / Midco
        midco(\s*sports(\s*net)?)?|
        altitude(\s*2)?(\s*sports)?|
        # Tournament TV shorthands that show up in Torvik matchup cells
        horz\-?t|nec\-?t|pat\-?t|a10\-?t|caa\-?t|mvc\-?t|soc\-?t|wcc\-?t|
        # "NEC Front Row" and similar
        nec\ front\ row|
        # CW variants
        the\ cw\ network|cw\ network|the\ cw|cw|
        abc|nbc
    )\b.*$
    """,
    re.IGNORECASE | re.VERBOSE
)
MASCOT_TOKENS = {
    "hawks","eagles","tigers","lions","bears","wildcats","bulldogs","panthers","cougars","wolves","wolfpack",
    "rams","raiders","rebels","pirates","knights","spartans","wolverines","cardinals","falcons","bison","hornets",
    "crusaders","minutemen","zips","chippewas","bobcats","broncos","aztecs","aggies","terriers","gaels","jaspers",
    "peacocks","mountaineers","jaguars","vaqueros","deacons","hoyas","bearcats","musketeers","devils","redhawks",
    "billikens","cavaliers","hokies","heels","gophers","rockets","vikings","sycamores","beacons","mastodons",
    "islanders","rattlers","privateers","lumberjacks","cowboys","colonels","demons","braves","bengals","explorers",
    "spiders","owls","phoenix","tribe","trojans","huskies", "sun", "devils",
    "tarheels","yellowjackets","sundevils","hornedfrogs","redwolves","warhawks",
    "bulls","shockers","hurricanes","salukis","quakers","razorbacks", "seminoles", "billikens",
    "penguins","norse","aces","bluejays","mavericks","gauchos","matadors","titans","highlanders",
}

# keep YOUR alias dict as-is (unchanged)
ALIAS_EXACT = {
    # A&M family (critical)
    "texas aandm": "texas am",
    "texas a and m": "texas am",
    "texas a m": "texas am",
    "texas am": "texas am",
    
    # --- George Washington / GW / GWU ---
    "gw": "george washington",
    "gwu": "george washington",
    "george washington u": "george washington",
    "george washington university": "george washington",
    "george washington revolutionaries": "george washington",
    "george washington colonials": "george washington",
    
    # --- Saint Louis / St Louis / SLU ---
    "st louis": "saint louis",
    "st. louis": "saint louis",
    "slu": "saint louis",
    "saint louis billikens": "saint louis",
    
    # --- Florida State ---
    "florida st": "florida state",
    "florida st.": "florida state",
    "florida state seminoles": "florida state",
    
    # --- George Washington (GW / GWU) ---
    "george washington": "george washington",
    "gw": "george washington",
    "gwu": "george washington",
    "george washington revolutionaries": "george washington",
    "george washington colonials": "george washington",
    
    # --- Saint Louis (SLU / St. Louis) ---
    "saint louis": "saint louis",
    "st louis": "saint louis",
    "st. louis": "saint louis",
    "slu": "saint louis",
    "saint louis billikens": "saint louis",
    
    # ---- St. abbreviations (common) ----
    "florida st": "florida state",
    "cleveland st": "cleveland state",
    "wright st": "wright state",
    "chicago st": "chicago state",
    
    # ---- Saint names ----
    "st louis": "saint louis",
    "st. louis": "saint louis",
    "saint louis billikens": "saint louis",
    
    "st bonaventure": "st bonaventure",     # keep canonical key stable
    "st. bonaventure": "st bonaventure",
    "saint bonaventure": "st bonaventure",
    "st bonaventure bonnies": "st bonaventure",
    
    # ---- Le Moyne ----
    "le moyne": "le moyne",
    "lemoyne": "le moyne",
    "le moyne dolphins": "le moyne",
    
    # ---- Oakland + Mercyhurst (optional but safe) ----
    "oakland golden grizzlies": "oakland",
    "mercyhurst lakers": "mercyhurst",
    
    "arizona st.": "arizona state",
    "arizona st": "arizona state",
    
    "alcorn st.": "alcorn state",
    "alcorn st": "alcorn state",
    
    # --- Arizona State variants (Odds feed / DK / other books) ---
    "arizona st.": "arizona state",
    "arizona st": "arizona state",
    "arizona state sun devils": "arizona state",
    "arizona st sun devils": "arizona state",
    
    # --- Alcorn State variants ---
    "alcorn st.": "alcorn state",
    "alcorn st": "alcorn state",
    "alcorn state braves": "alcorn state",
    
    # --- “St.” abbreviations that pop all the time ---
    "arizona st": "arizona state",
    "alcorn st": "alcorn state",
    
    # --- Ole Miss / Mississippi variants ---
    "ole miss": "mississippi",
    "mississippi rebels": "mississippi",
    
    # --- Kansas + Arizona State / Vanderbilt + Mississippi should now match once the above work ---

    # --- Liberty ---
    "liberty flames": "liberty",
    "liberty": "liberty",

    # --- Winthrop ---
    "winthrop eagles": "winthrop",
    "winthrop": "winthrop",

    # --- Saint Francis ---
    "saint francis pa": "saint francis",
    "st francis pa": "saint francis",
    "st francis (pa)": "saint francis",
    "saint francis (pa)": "saint francis",
    "st francis": "saint francis",
    "saint francis": "saint francis",

    # --- LIU ---
    "liu brooklyn": "liu",
    "liu post": "liu",
    "long island": "liu",
    "long island university": "liu",
    "liu": "liu",

    # --- UMKC / Kansas City ---
    "umkc": "kansas city",
    "missouri kansas city": "kansas city",
    "missouri-kansas city": "kansas city",
    "kc": "kansas city",
    "kansas city roos": "kansas city",
    "kansas city": "kansas city",

    # --- North Dakota ---
    "north dakota": "north dakota",
    "north dakota fighting hawks": "north dakota",

    # --- UC Riverside ---
    "uc riverside": "uc riverside",
    "ucr": "uc riverside",

    # --- Cal State Bakersfield ---
    "cal st bakersfield": "cal state bakersfield",
    "csu bakersfield": "cal state bakersfield",
    "cal state bakersfield": "cal state bakersfield",

    # Nicknames / common alternates
    "mizzou": "missouri",
    "missouri tigers": "missouri",

    # Charleston
    "college of charleston": "charleston",
    "charleston cougars": "charleston",

    # North Carolina A&T
    "north carolina a and t": "north carolina at",
    "north carolina a t": "north carolina at",
    "nc a and t": "north carolina at",
    "nc at": "north carolina at",
    "north carolina at": "north carolina at",
    "north carolina a&t": "north carolina at",

    # IU Indy / IUPUI
    "iupui": "iu indy",
    "iu indianapolis": "iu indy",
    "indiana university indianapolis": "iu indy",
    "iu indy": "iu indy",

    # Wright State
    "wright st": "wright state",
    "wright state raiders": "wright state",

    # UT Martin / Little Rock
    "tennessee martin": "ut martin",
    "ut martin": "ut martin",
    "arkansas little rock": "little rock",
    "ualr": "little rock",
    "little rock trojans": "little rock",

    # Prairie View / Mississippi Valley State
    "prairie view a and m": "prairie view am",
    "prairie view a&m": "prairie view am",
    "prairie view": "prairie view am",
    "mississippi valley st": "mississippi valley state",
    "mvsu": "mississippi valley state",
    "mississippi valley": "mississippi valley state",

    # Cal State campuses
    "cal st northridge": "cal state northridge",
    "csun": "cal state northridge",
    "cal st fullerton": "cal state fullerton",
    "csuf": "cal state fullerton",
    "cal st bakersfield": "cal state bakersfield",

    # UC campuses
    "uc santa barbara": "uc santa barbara",
    "ucsb": "uc santa barbara",
    "uc davis": "uc davis",
    "cal davis": "uc davis",
    "uc riverside": "uc riverside",
    "ucr": "uc riverside",
}

def safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None

def strip_rank_prefix(name: str) -> str:
    s = (name or "").strip()
    return re.sub(r"^\s*#?\s*\d+\s+", "", s).strip()

def _apply_aliases(s: str) -> str:
    return ALIAS_EXACT.get(s, s)

def clean_team(raw: str) -> str:
    s = (raw or "").strip()
    s = strip_rank_prefix(s)

    s = NETWORK_TAIL_PATTERN.sub("", s).strip()

    s = s.replace("&", " and ").replace("-", " ").replace("’", "'").replace("‘", "'")
    s = s.lower()

    s = re.sub(r"\buniv(ersity)?\b", "university", s)

    s = re.sub(r"\ba\s*&\s*m\b", "am", s)
    s = re.sub(r"\ba\s+and\s+m\b", "am", s)
    s = re.sub(r"\ba\s*&\s*t\b", "at", s)
    s = re.sub(r"\ba\s+and\s+t\b", "at", s)

    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()

    s = re.sub(r"\bst\b$", "state", s)

    s = re.sub(r"^\s*unc\s+", "north carolina ", s)
    s = re.sub(r"^\s*cal\s+st\s+", "cal state ", s)

    # ✅ add these two lines
    s = re.sub(r"^arizona st\b", "arizona state", s)
    s = re.sub(r"^alcorn st\b", "alcorn state", s)

    s = _apply_aliases(s)
    return s

# ✅ FIXED: only strip true mascots, never campus words
def base_school_key(cleaned: str) -> str:
    toks = (cleaned or "").split()
    if not toks:
        return ""

    # apply aliases to the full cleaned string first
    full = _apply_aliases(" ".join(toks).strip())
    toks = full.split()

    # only strip if tail is a known mascot token
    while len(toks) >= 2 and toks[-1] in MASCOT_TOKENS:
        toks = toks[:-1]

    base = " ".join(toks).strip()
    base = _apply_aliases(base)
    return base


# ============================================================
# TORVIK: parse saved schedule HTML
# ============================================================

def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _extract_matchup_from_td(td) -> Tuple[Optional[str], Optional[str]]:
    txt = " ".join(td.stripped_strings)
    txt = re.sub(r"\s+", " ", txt).strip()
    if not re.search(r"\sat\s", txt, flags=re.IGNORECASE):
        return None, None
    away_raw, home_raw = re.split(r"\s+at\s+", txt, maxsplit=1, flags=re.IGNORECASE)
    away_raw = strip_rank_prefix(away_raw)
    home_raw = strip_rank_prefix(home_raw)

    away_raw = NETWORK_TAIL_PATTERN.sub("", away_raw).strip()
    home_raw = NETWORK_TAIL_PATTERN.sub("", home_raw).strip()
    return away_raw, home_raw

def _parse_trank_cell(text: str) -> Dict:
    t = re.sub(r"\s+", " ", (text or "")).strip()

    prob = None
    mprob = re.search(r"\((\d{1,3})\s*%\)", t)
    if mprob:
        prob = int(mprob.group(1)) / 100.0

    pick_team = None
    spread = None
    m = re.search(r"^(.*?)\s+([+-]?\d+(?:\.\d+)?)\b", t)
    if m:
        pick_team = m.group(1).strip()
        spread = safe_float(m.group(2))

    score_1 = None
    score_2 = None
    ms = re.search(r"(\d{2,3})\s*-\s*(\d{2,3})", t)
    if ms:
        score_1 = int(ms.group(1))
        score_2 = int(ms.group(2))

    return {
        "torvik_cell": t,
        "torvik_pick_team": pick_team,
        "torvik_spread": spread,
        "torvik_prob": prob,
        "proj_score_1": score_1,
        "proj_score_2": score_2,
    }

def load_torvik_games_from_saved_html(html_path: str) -> List[Dict]:
    if not os.path.exists(html_path):
        return []

    soup = BeautifulSoup(_read_file(html_path), "lxml")

    schedule_table = None
    for tbl in soup.find_all("table"):
        headers = [(" ".join(th.stripped_strings)).upper() for th in tbl.find_all("th")]
        header_line = " | ".join(headers)
        if "MATCHUP" in header_line and ("T-RANK" in header_line or "TRANK" in header_line):
            schedule_table = tbl
            break

    if schedule_table is None:
        return []

    headers = [(" ".join(th.stripped_strings)).strip().upper() for th in schedule_table.find_all("th")]
    idx_matchup = next((i for i, h in enumerate(headers) if "MATCHUP" in h), None)
    idx_trank = next((i for i, h in enumerate(headers) if ("T-RANK" in h or "TRANK" in h)), None)
    if idx_matchup is None or idx_trank is None:
        return []

    games = []
    for tr in schedule_table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) <= max(idx_matchup, idx_trank):
            continue

        away_raw, home_raw = _extract_matchup_from_td(tds[idx_matchup])
        if not away_raw or not home_raw:
            continue

        trank_text = " ".join(tds[idx_trank].stripped_strings)
        parsed = _parse_trank_cell(trank_text)
        if parsed["torvik_spread"] is None or parsed["torvik_prob"] is None:
            continue

        away_key = clean_team(away_raw)
        home_key = clean_team(home_raw)

        games.append({
            "away_raw": away_raw,
            "home_raw": home_raw,
            "away_key": away_key,
            "home_key": home_key,
            "away_base": base_school_key(away_key),
            "home_base": base_school_key(home_key),
            **parsed,
        })

    return games

def load_torvik_slate(mode: str) -> List[Dict]:
    mode = (mode or "").lower().strip()
    out: List[Dict] = []
    if mode in ("today", "both"):
        out += load_torvik_games_from_saved_html(TORVIK_HTML_TODAY)
    if mode in ("tomorrow", "both"):
        out += load_torvik_games_from_saved_html(TORVIK_HTML_TOMORROW)
    return out


# ============================================================
# ODDS API: DK-first + fallback + “don’t disappear”
# ============================================================

def fetch_spreads_totals(bookmakers: Optional[str] = "draftkings") -> List[Dict]:
    url = f"{ODDS_API_BASE}/sports/{SPORT_KEY}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGION,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": DATE_FORMAT,
    }
    if bookmakers:
        params["bookmakers"] = bookmakers

    r = requests.get(url, params=params, timeout=30)

    # ✅ FIX: DK-only can return 401 even when the key is valid -> fall back automatically
    if r.status_code == 401 and params.get("bookmakers"):
        print("WARNING: DK-only request returned 401. Falling back to all books (no bookmakers filter)...")
        params.pop("bookmakers", None)
        r = requests.get(url, params=params, timeout=30)

    r.raise_for_status()
    data = r.json()

    rows = []
    for ev in data:
        home = ev.get("home_team")
        away = ev.get("away_team")
        if not home or not away:
            continue

        bms = ev.get("bookmakers", [])

        # Keep event for matching even if no markets posted
        if not bms:
            home_key = clean_team(home)
            away_key = clean_team(away)
            rows.append({
                "event_id": ev.get("id"),
                "start_time": ev.get("commence_time"),
                "home_raw_dk": home,
                "away_raw_dk": away,
                "home_base_dk": base_school_key(home_key),
                "away_base_dk": base_school_key(away_key),
                "book_key": "none",
                "dk_home_spread": None,
                "dk_away_spread": None,
                "dk_total": None,
            })
            continue

        for bm in bms:
            bm_key = bm.get("key") or ""

            spreads_market = None
            totals_market = None
            for m in bm.get("markets", []):
                if m.get("key") == "spreads":
                    spreads_market = m
                elif m.get("key") == "totals":
                    totals_market = m

            home_spread = away_spread = None
            if spreads_market and spreads_market.get("outcomes"):
                for o in spreads_market["outcomes"]:
                    if o.get("name") == home:
                        home_spread = safe_float(o.get("point"))
                    elif o.get("name") == away:
                        away_spread = safe_float(o.get("point"))

            total_line = None
            if totals_market and totals_market.get("outcomes"):
                for o in totals_market["outcomes"]:
                    if str(o.get("name", "")).lower() == "over":
                        total_line = safe_float(o.get("point"))
                        break

            home_key = clean_team(home)
            away_key = clean_team(away)

            rows.append({
                "event_id": ev.get("id"),
                "start_time": ev.get("commence_time"),
                "home_raw_dk": home,
                "away_raw_dk": away,
                "home_base_dk": base_school_key(home_key),
                "away_base_dk": base_school_key(away_key),
                "book_key": bm_key,
                "dk_home_spread": home_spread,
                "dk_away_spread": away_spread,
                "dk_total": total_line,
            })

    return rows

def pick_best_book_per_game(rows: List[Dict], prefer: str = "draftkings") -> List[Dict]:
    by_event: Dict[str, List[Dict]] = {}
    for r in rows:
        eid = r.get("event_id") or ""
        by_event.setdefault(eid, []).append(r)

    chosen = []
    for eid, lst in by_event.items():
        dk_row = next((x for x in lst if x.get("book_key") == prefer), None)
        if dk_row:
            chosen.append({**dk_row, "book_used": prefer})
            continue

        usable = [x for x in lst if (x.get("dk_home_spread") is not None or x.get("dk_total") is not None)]
        if usable:
            chosen.append({**usable[0], "book_used": usable[0].get("book_key")})
        else:
            chosen.append({**lst[0], "book_used": lst[0].get("book_key")})

    return chosen

# ============================================================
# MATCH Torvik -> Odds (swap-safe + unordered team-set)
# ============================================================

def best_match(key: str, candidates: List[str]) -> Tuple[Optional[str], int]:
    best = None
    best_score = -1
    for c in candidates:
        sc = max(fuzz.ratio(key, c), fuzz.token_set_ratio(key, c))
        if sc > best_score:
            best_score = sc
            best = c
    return best, best_score

def match_torvik_to_dk(torvik_games: List[Dict], dk_games: List[Dict]) -> Tuple[List[Dict], List[Tuple]]:
    dk_by_pair = {(g["away_base_dk"], g["home_base_dk"]): g for g in dk_games}
    dk_by_pair_swapped = {(g["home_base_dk"], g["away_base_dk"]): g for g in dk_games}

    # unordered match bucket
    dk_by_set: Dict[frozenset, Dict] = {}
    for g in dk_games:
        k = frozenset([g["away_base_dk"], g["home_base_dk"]])
        if k not in dk_by_set:
            dk_by_set[k] = g
        else:
            cur = dk_by_set[k]
            cur_has = (cur.get("dk_home_spread") is not None) or (cur.get("dk_total") is not None)
            new_has = (g.get("dk_home_spread") is not None) or (g.get("dk_total") is not None)
            if new_has and not cur_has:
                dk_by_set[k] = g

    dk_home_bases = sorted(set(g["home_base_dk"] for g in dk_games))
    dk_away_bases = sorted(set(g["away_base_dk"] for g in dk_games))

    matched = []
    unmatched = []

    for tv in torvik_games:
        key = (tv["away_base"], tv["home_base"])

        exact = dk_by_pair.get(key)
        if exact:
            matched.append({**tv, **exact, "swapped": False})
            continue

        sw = dk_by_pair_swapped.get(key)
        if sw:
            matched.append({**tv, **sw, "swapped": True})
            continue

        set_key = frozenset([tv["away_base"], tv["home_base"]])
        gset = dk_by_set.get(set_key)
        if gset:
            swapped_flag = (gset["home_base_dk"] == tv["away_base"] and gset["away_base_dk"] == tv["home_base"])
            matched.append({**tv, **gset, "swapped": swapped_flag})
            continue

        # fuzzy exact
        best_away, sA = best_match(tv["away_base"], dk_away_bases)
        best_home, sH = best_match(tv["home_base"], dk_home_bases)
        if best_away and best_home and sA >= MATCH_MIN_SCORE and sH >= MATCH_MIN_SCORE:
            g = dk_by_pair.get((best_away, best_home))
            if g:
                matched.append({**tv, **g, "swapped": False})
                continue

        # fuzzy swapped
        best_away_sw, sA2 = best_match(tv["away_base"], dk_home_bases)
        best_home_sw, sH2 = best_match(tv["home_base"], dk_away_bases)
        if best_away_sw and best_home_sw and sA2 >= MATCH_MIN_SCORE and sH2 >= MATCH_MIN_SCORE:
            g = dk_by_pair_swapped.get((best_away_sw, best_home_sw))
            if g:
                matched.append({**tv, **g, "swapped": True})
                continue

        unmatched.append((tv["away_raw"], tv["home_raw"], tv["away_base"], tv["home_base"]))

    return matched, unmatched

# ============================================================
# SPREAD LOGIC (swap-safe)
# ============================================================

def torvik_to_home_spread(g: Dict) -> Optional[float]:
    tv_spread = g.get("torvik_spread")
    if tv_spread is None:
        return None

    pick = g.get("torvik_pick_team") or ""
    pick_base = base_school_key(clean_team(pick))

    home_base = g["home_base"]
    away_base = g["away_base"]

    score_home = max(fuzz.ratio(pick_base, home_base), fuzz.token_set_ratio(pick_base, home_base))
    score_away = max(fuzz.ratio(pick_base, away_base), fuzz.token_set_ratio(pick_base, away_base))

    return tv_spread if score_home >= score_away else -tv_spread

def dk_spreads_in_torvik_frame(g: Dict) -> Tuple[Optional[float], Optional[float]]:
    if not g.get("swapped"):
        return g.get("dk_home_spread"), g.get("dk_away_spread")
    else:
        return g.get("dk_away_spread"), g.get("dk_home_spread")

def compute_side_pick(g: Dict) -> Optional[Dict]:
    prob = g.get("torvik_prob")
    if prob is None or prob < MIN_SIDE_PROB:
        return None

    tv_home = torvik_to_home_spread(g)
    if tv_home is None:
        return None

    dk_home, dk_away = dk_spreads_in_torvik_frame(g)
    if dk_home is None or dk_away is None:
        return None

    edge = abs(dk_home - tv_home)
    if edge < MIN_SIDE_EDGE:
        return None

    if tv_home < dk_home:
        pick_team = g["home_raw"]
        pick_line = dk_home
    else:
        pick_team = g["away_raw"]
        pick_line = dk_away

    proj = None
    a = g.get("proj_score_1")
    b = g.get("proj_score_2")
    if isinstance(a, int) and isinstance(b, int):
        proj = f"{a}-{b}"

    return {
        "matchup": f"{g['away_raw']} @ {g['home_raw']}",
        "pick": f"{pick_team} {pick_line:+.1f}",
        "torvik_prob": prob,
        "torvik_home_spread": tv_home,
        "dk_home_spread": dk_home,
        "edge_points": edge,
        "book_used": g.get("book_used", "draftkings"),
        "swapped_dk_event": bool(g.get("swapped")),
        "start_time": g.get("start_time"),
        "torvik_proj_score": proj,
    }

# ============================================================
# ML LOGIC (updated)
# ============================================================

def compute_ml_pick(g: Dict) -> Optional[Dict]:
    prob = g.get("torvik_prob")
    if prob is None or prob < MIN_ML_PROB:
        return None

    tv_home = torvik_to_home_spread(g)
    if tv_home is None:
        return None

    dk_home, dk_away = dk_spreads_in_torvik_frame(g)
    if dk_home is None or dk_away is None:
        return None

    # Torvik favorite + DK favorite must agree
    torvik_fav = "home" if tv_home < 0 else "away"
    dk_fav = "home" if dk_home < 0 else "away"
    if torvik_fav != dk_fav:
        return None

    # favored by less than threshold
    dk_fav_spread = abs(dk_home) if dk_fav == "home" else abs(dk_away)
    if dk_fav_spread >= MAX_ML_FAV_SPREAD:
        return None

    # require mini-edge in the same direction
    edge_pts = abs(dk_home - tv_home)
    if edge_pts < MIN_ML_SPREAD_EDGE:
        return None

    pick_team = g["home_raw"] if dk_fav == "home" else g["away_raw"]

    proj = None
    a = g.get("proj_score_1")
    b = g.get("proj_score_2")
    if isinstance(a, int) and isinstance(b, int):
        proj = f"{a}-{b}"

    return {
        "matchup": f"{g['away_raw']} @ {g['home_raw']}",
        "pick": f"{pick_team} ML",
        "torvik_prob": prob,
        "torvik_home_spread": tv_home,
        "dk_home_spread": dk_home,
        "dk_fav_spread_abs": dk_fav_spread,
        "edge_points": edge_pts,
        "book_used": g.get("book_used", "draftkings"),
        "start_time": g.get("start_time"),
        "torvik_proj_score": proj,
    }

# ============================================================
# TOTALS LOGIC (updated)
# ============================================================

def torvik_projected_total(g: Dict) -> Optional[float]:
    a = g.get("proj_score_1")
    b = g.get("proj_score_2")
    if isinstance(a, int) and isinstance(b, int):
        return float(a + b)
    return None

def compute_total_pick(g: Dict) -> Optional[Dict]:
    dk_total = g.get("dk_total")
    if dk_total is None:
        return None

    proj_total = torvik_projected_total(g)
    if proj_total is None:
        return None

    diff = proj_total - dk_total
    edge = abs(diff)
    pick_side = "OVER" if diff > 0 else "UNDER"

    if pick_side == "OVER":
        if edge < MIN_OVER_EDGE:
            return None
    else:
        # blowout protection
        tv_home = torvik_to_home_spread(g)
        if tv_home is not None and abs(tv_home) >= MAX_UNDER_BLOWOUT_SPREAD:
            return None

        # low total under protection
        if dk_total <= LOW_TOTAL_CUTOFF:
            if edge < LOW_TOTAL_UNDER_EDGE:
                return None
        else:
            if edge < MIN_UNDER_EDGE:
                return None

    return {
        "matchup": f"{g['away_raw']} @ {g['home_raw']}",
        "pick": f"{pick_side} {dk_total:.1f}",
        "torvik_proj_total": proj_total,
        "dk_total": dk_total,
        "edge_points": edge,
        "book_used": g.get("book_used", "draftkings"),
        "start_time": g.get("start_time"),
    }

# ============================================================
# MAIN
# ============================================================

def main():
    if not ODDS_API_KEY or ODDS_API_KEY.strip() == "":
        print("ERROR: Paste your Odds API key into ODDS_API_KEY in CONFIG.")
        return

    print(f"\nLoading Torvik schedule from saved HTML (mode={SLATE_MODE})...")
    torvik_games = load_torvik_slate(SLATE_MODE)
    print(f"Loaded Torvik matchups: {len(torvik_games)}")

    if len(torvik_games) == 0:
        print("\nTORVIK LOAD = 0 usually means:")
        print(" - wrong HTML file path, OR")
        print(" - saved HTML doesn't include the table (JS-only), OR")
        print(" - file is empty / not updated.\n")
        print("Check these files exist:")
        print(" ", TORVIK_HTML_TODAY)
        print(" ", TORVIK_HTML_TOMORROW)
        return

    print("\nFetching odds (DK-first; fallback if missing)...")

    dk_only_rows = fetch_spreads_totals(bookmakers="draftkings")
    print(f"DraftKings rows parsed: {len(dk_only_rows)}")

    rows = dk_only_rows
    if FALLBACK_TO_ANY_BOOK:
        all_rows = fetch_spreads_totals(bookmakers=None)
        print(f"All-books rows parsed: {len(all_rows)}")
        rows = all_rows

    games = pick_best_book_per_game(rows, prefer="draftkings")
    print(f"Games after DK-first selection: {len(games)}")

    joined, unmatched = match_torvik_to_dk(torvik_games, games)

    print("\n=== TEAM MATCH DEBUG ===")
    print(f"Matched games: {len(joined)} / {len(torvik_games)} (Torvik rows)")
    print(f"Unmatched: {len(unmatched)}")
    for row in unmatched[:40]:
        print(" ", row)

    side_rows = []
    ml_rows = []
    total_rows = []

    # Dedup priority: SIDE > ML (don’t double-pick same game)
    side_matchups = set()

    for g in joined:
        s = compute_side_pick(g)
        if s:
            side_rows.append(s)
            side_matchups.add(s["matchup"])

    for g in joined:
        ml = compute_ml_pick(g)
        if ml and ml["matchup"] not in side_matchups:
            ml_rows.append(ml)

        t = compute_total_pick(g)
        if t:
            total_rows.append(t)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)

    if side_rows:
        df_side = pd.DataFrame(side_rows).sort_values(["torvik_prob", "edge_points"], ascending=[False, False])
        print("\n=== QUALIFYING SIDE PLAYS (Torvik vs Book) ===")
        print(df_side.to_string(index=False))
    else:
        print("\nNo qualifying SIDE plays under current rules.")

    if ml_rows:
        df_ml = pd.DataFrame(ml_rows).sort_values(
            ["torvik_prob", "dk_fav_spread_abs", "edge_points"],
            ascending=[False, True, False]
        )
        print("\n=== QUALIFYING ML PLAYS (prob>=0.65, fav<4.0, mini-edge>=1.0) ===")
        print(df_ml.to_string(index=False))
    else:
        print("\nNo qualifying ML plays under current rules.")

    if total_rows:
        df_tot = pd.DataFrame(total_rows).sort_values(["edge_points"], ascending=False)
        print("\n=== QUALIFYING TOTAL PLAYS (UNDER protected) ===")
        print(df_tot.to_string(index=False))
    else:
        print("\nNo qualifying TOTAL plays under current rules.")

if __name__ == "__main__":
    main()
    
    
    
    