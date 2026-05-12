import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
RSS_DIR = BASE_DIR / "rss"
TEAMS_DIR = RSS_DIR / "teams"
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "state.json"
TEAM_CACHE_FILE = DATA_DIR / "team_cache.json"

HEADERS = {"User-Agent": "hoopshype-rss/1.0"}
TIMEOUT = 30

NBA_TEAMS = {
    "atlanta-hawks": {"abbrev": "atl", "name": "Atlanta Hawks"},
    "boston-celtics": {"abbrev": "bos", "name": "Boston Celtics"},
    "brooklyn-nets": {"abbrev": "bkn", "name": "Brooklyn Nets"},
    "charlotte-hornets": {"abbrev": "cha", "name": "Charlotte Hornets"},
    "chicago-bulls": {"abbrev": "chi", "name": "Chicago Bulls"},
    "cleveland-cavaliers": {"abbrev": "cle", "name": "Cleveland Cavaliers"},
    "dallas-mavericks": {"abbrev": "dal", "name": "Dallas Mavericks"},
    "denver-nuggets": {"abbrev": "den", "name": "Denver Nuggets"},
    "detroit-pistons": {"abbrev": "det", "name": "Detroit Pistons"},
    "golden-state-warriors": {"abbrev": "gsw", "name": "Golden State Warriors"},
    "houston-rockets": {"abbrev": "hou", "name": "Houston Rockets"},
    "indiana-pacers": {"abbrev": "ind", "name": "Indiana Pacers"},
    "los-angeles-clippers": {"abbrev": "lac", "name": "Los Angeles Clippers"},
    "los-angeles-lakers": {"abbrev": "lal", "name": "Los Angeles Lakers"},
    "memphis-grizzlies": {"abbrev": "mem", "name": "Memphis Grizzlies"},
    "miami-heat": {"abbrev": "mia", "name": "Miami Heat"},
    "milwaukee-bucks": {"abbrev": "mil", "name": "Milwaukee Bucks"},
    "minnesota-timberwolves": {"abbrev": "min", "name": "Minnesota Timberwolves"},
    "new-orleans-pelicans": {"abbrev": "nop", "name": "New Orleans Pelicans"},
    "new-york-knicks": {"abbrev": "nyk", "name": "New York Knicks"},
    "oklahoma-city-thunder": {"abbrev": "okc", "name": "Oklahoma City Thunder"},
    "orlando-magic": {"abbrev": "orl", "name": "Orlando Magic"},
    "philadelphia-76ers": {"abbrev": "phi", "name": "Philadelphia 76ers"},
    "phoenix-suns": {"abbrev": "phx", "name": "Phoenix Suns"},
    "portland-trail-blazers": {"abbrev": "por", "name": "Portland Trail Blazers"},
    "sacramento-kings": {"abbrev": "sac", "name": "Sacramento Kings"},
    "san-antonio-spurs": {"abbrev": "sas", "name": "San Antonio Spurs"},
    "toronto-raptors": {"abbrev": "tor", "name": "Toronto Raptors"},
    "utah-jazz": {"abbrev": "uta", "name": "Utah Jazz"},
    "washington-wizards": {"abbrev": "was", "name": "Washington Wizards"},
}

def fetch_url(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def extract_build_id(html):
    m = re.search(r'/_next/static/([^/]+)/_buildManifest\.js', html)
    return m.group(1) if m else None

def fetch_rumors_data():
    html = fetch_url("https://www.hoopshype.com/rumors/")
    if not html:
        print("Failed to fetch hoopshype rumors page")
        return None, None
    build_id = extract_build_id(html)
    if not build_id:
        print("Could not extract Next.js build ID")
        return None, None
    data_url = f"https://www.hoopshype.com/_next/data/{build_id}/rumors.json"
    json_str = fetch_url(data_url)
    if not json_str:
        print("Failed to fetch rumors JSON data")
        return None, None
    try:
        return json.loads(json_str), build_id
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return None, None

def parse_teams(data):
    pp = data.get("pageProps", {})
    ds = pp.get("dehydratedState", {})
    teams_info = {}
    for q in ds.get("queries", []):
        qk = q.get("queryKey", "")
        if isinstance(qk, list) and len(qk) > 1 and qk[0] == "NBA":
            sdata = q.get("state", {}).get("data", {})
            teams_wrapper = sdata.get("teams", {})
            if isinstance(teams_wrapper, dict):
                for team in teams_wrapper.get("teams", []):
                    if team.get("isAllStar"):
                        continue
                    slug = team.get("teamName", "").lower().replace(" ", "-")
                    abbrev = NBA_TEAMS.get(slug, {}).get("abbrev", slug.replace("-", "")[:3])
                    teams_info[team.get("contentTag", "")] = {
                        "abbrev": abbrev,
                        "name": team.get("teamName", ""),
                        "location": team.get("location", ""),
                        "nickname": team.get("nickname", ""),
                    }
    return teams_info

def parse_rumors(data):
    rumors = []
    pp = data.get("pageProps", {})
    ds = pp.get("dehydratedState", {})
    for q in ds.get("queries", []):
        qk = q.get("queryKey", "")
        if isinstance(qk, list) and len(qk) > 1 and qk[1] == "asset_by_ssts":
            for page in q.get("state", {}).get("data", {}).get("pages", []):
                for asset in page.get("searchAssets", {}).get("assets", []):
                    rumor = parse_rumor_item(asset)
                    if rumor:
                        rumors.append(rumor)
    return rumors

def parse_rumor_item(asset):
    try:
        story_id = asset.get("id", "")
        headline = asset.get("headline", "")
        if not headline or not story_id:
            return None
        page_url = ""
        pu = asset.get("pageURL", {})
        if isinstance(pu, dict):
            page_url = pu.get("long", "")
        pub_date = asset.get("initialPublishDate", "")
        source = asset.get("source", "")
        body = ""
        for part in (asset.get("contentBody") or []):
            if isinstance(part, dict):
                val = part.get("value", "")
                if val:
                    clean = re.sub(r'<[^>]+>', '', val)
                    body += re.sub(r'\s+', ' ', clean).strip() + " "
        teams = []
        for tw in (asset.get("tags") or []):
            if isinstance(tw, dict):
                tag = tw.get("tag", {})
                if isinstance(tag, dict) and tag.get("vocabulary") == "Organizations":
                    teams.append({"name": tag.get("displayName", ""), "id": tag.get("id", "")})
        return {"id": story_id, "headline": headline, "url": page_url, "pub_date": pub_date, "source": source, "body": body.strip(), "teams": teams}
    except Exception as e:
        print(f"  Error parsing rumor: {e}")
        return None

def make_rss_item(rumor):
    item = ET.Element("item")
    ET.SubElement(item, "title").text = rumor["headline"]
    ET.SubElement(item, "link").text = rumor["url"]
    guid = ET.SubElement(item, "guid", isPermaLink="false")
    guid.text = f"hoopshype-{rumor['id']}"
    desc = rumor["body"]
    if rumor["source"]:
        desc = f"[Source: {rumor['source']}] {desc}"
    ET.SubElement(item, "description").text = desc[:500]
    if rumor["pub_date"]:
        try:
            dt = datetime.fromisoformat(rumor["pub_date"].replace("Z", "+00:00"))
            ET.SubElement(item, "pubDate").text = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
        except:
            pass
    return item

def build_rss(title, description, link, items):
    rss = ET.Element("rss", version="2.0")
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = title
    ET.SubElement(ch, "description").text = description
    ET.SubElement(ch, "link").text = link
    ET.SubElement(ch, "language").text = "en-us"
    for item in items:
        ch.append(item)
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)

def read_xml(path):
    if path.exists():
        try:
            return ET.parse(str(path)).getroot()
        except:
            pass
    return None

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"published": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def create_placeholder_feeds():
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    for info in NBA_TEAMS.values():
        abbrev = info["abbrev"]
        team_path = TEAMS_DIR / f"{abbrev}.xml"
        if not team_path.exists():
            xml = build_rss(
                f"HoopsHype Rumors - {info['name']}",
                f"{info['name']} trade rumors and free agency buzz from HoopsHype",
                f"https://www.hoopshype.com/rumors/",
                [],
            )
            with open(team_path, "w", encoding="utf-8") as f:
                f.write(xml)

def update_feeds():
    print("Fetching hoopshype rumors data...")
    data, build_id = fetch_rumors_data()
    if not data:
        print("Failed to get data, exiting.")
        return

    print("Parsing teams...")
    teams_info = parse_teams(data)
    print(f"  Found {len(teams_info)} NBA teams")

    print("Parsing rumors...")
    all_rumors = parse_rumors(data)
    print(f"  Found {len(all_rumors)} rumors")

    if not all_rumors:
        print("No rumors found, nothing to update.")
        return

    state = load_state()
    new_rumors = [r for r in all_rumors if r["id"] not in state.get("published", [])]

    if not new_rumors:
        print("No new rumors to publish.")
        return

    print(f"  {len(new_rumors)} new rumors to add")
    state.setdefault("published", []).extend(r["id"] for r in new_rumors)
    state["published"] = state["published"][-500:]

    RSS_DIR.mkdir(parents=True, exist_ok=True)
    create_placeholder_feeds()

    print("Updating all-rumors feed...")
    all_path = RSS_DIR / "all.xml"
    existing = read_xml(all_path)
    existing_items = []
    if existing is not None:
        ch = existing.find("channel")
        if ch is not None:
            existing_items = list(ch.findall("item"))
    all_items = existing_items + [make_rss_item(r) for r in new_rumors]
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(build_rss("HoopsHype Rumors - All", "All NBA trade rumors and free agency buzz from HoopsHype", "https://www.hoopshype.com/rumors/", all_items))
    print(f"  Wrote all.xml ({len(all_items)} items)")

    rumors_by_team = {}
    for rumor in new_rumors:
        for team in rumor["teams"]:
            if team["id"] in teams_info:
                abbrev = teams_info[team["id"]]["abbrev"]
                rumors_by_team.setdefault(abbrev, []).append(rumor)

    print("Updating team feeds...")
    for info in NBA_TEAMS.values():
        abbrev = info["abbrev"]
        team_path = TEAMS_DIR / f"{abbrev}.xml"
        existing_team = read_xml(team_path)
        existing_team_items = []
        if existing_team is not None:
            ch = existing_team.find("channel")
            if ch is not None:
                existing_team_items = list(ch.findall("item"))
        team_rumors = rumors_by_team.get(abbrev, [])
        if not team_rumors and existing_team_items:
            continue
        all_team_items = existing_team_items + [make_rss_item(r) for r in team_rumors]
        with open(team_path, "w", encoding="utf-8") as f:
            f.write(build_rss(f"HoopsHype Rumors - {info['name']}", f"{info['name']} trade rumors and free agency buzz from HoopsHype", "https://www.hoopshype.com/rumors/", all_team_items))
        if team_rumors:
            print(f"  Updated {abbrev}.xml (+{len(team_rumors)} items, total {len(all_team_items)})")

    save_state(state)
    print("Done!")

if __name__ == "__main__":
    update_feeds()
