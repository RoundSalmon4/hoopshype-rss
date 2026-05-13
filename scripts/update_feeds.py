import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
import urllib.request
import time

BASE_DIR = Path(__file__).resolve().parent.parent
RSS_DIR = BASE_DIR / "rss"
TEAMS_DIR = RSS_DIR / "teams"
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "state.json"

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

TEAM_NAME_TO_ABBREV = {info["name"].lower(): info["abbrev"] for info in NBA_TEAMS.values()}

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

def extract_url_id(url):
    m = re.search(r"/(\d+)/?$", url)
    return m.group(1) if m else url.strip("/").split("/")[-1]

def fetch_news_sitemap():
    body = fetch_url("https://www.hoopshype.com/news-sitemap.xml")
    if not body:
        return None
    parser = ET.XMLParser()
    root = ET.fromstring(body, parser=parser)
    S = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    N = "{http://www.google.com/schemas/sitemap-news/0.9}"
    I = "{http://www.google.com/schemas/sitemap-image/1.1}"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    entries = []
    for url_elem in root.findall(f"{S}url"):
        loc_elem = url_elem.find(f"{S}loc")
        if loc_elem is None:
            continue
        loc = loc_elem.text.strip()
        # SSRF prevention: only allow URLs from hoopshype.com
        parsed = urlparse(loc)
        if parsed.netloc not in ("www.hoopshype.com", "hoopshype.com"):
            continue
        if "/sports/nba/rumors/" not in loc:
            continue
        news = url_elem.find(f"{N}news")
        title = news.find(f"{N}title").text.strip() if news is not None and news.find(f"{N}title") is not None else ""
        pub = news.find(f"{N}publication_date").text.strip() if news is not None and news.find(f"{N}publication_date") is not None else ""
        image_elem = url_elem.find(f"{I}image")
        image = image_elem.find(f"{I}loc").text.strip() if image_elem is not None and image_elem.find(f"{I}loc") is not None else ""
        try:
            pub_date = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        except:
            pub_date = None
        if pub_date is not None and pub_date >= cutoff:
            entries.append({"url": loc, "title": title, "pub_date": pub, "pub_date_obj": pub_date, "image": image})
    return entries

def fetch_article_data(url):
    html = fetch_url(url)
    if not html:
        return None
    result = {"teams": [], "body": "", "headline": "", "pub_date": ""}
    for m in re.finditer(r'<script[^>]*type=["\']?application/ld\+json["\']?[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            ld = json.loads(m.group(1))
            result["headline"] = ld.get("headline", "")
            result["pub_date"] = ld.get("datePublished", "")
            for kw in ld.get("keywords", []):
                if kw.startswith("tag:"):
                    tag_name = kw[4:]
                    if tag_name.lower() in TEAM_NAME_TO_ABBREV:
                        result["teams"].append(tag_name)
        except:
            pass
    article = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
    if article:
        parts = []
        for p in re.finditer(r"<p[^>]*>(.*?)</p>", article.group(1), re.DOTALL):
            text = re.sub(r"<[^>]+>", "", p.group(1)).strip()
            if len(text) > 20:
                parts.append(text)
        result["body"] = parts[0] if parts else ""
    return result

def fetch_rumors_data():
    html = fetch_url("https://www.hoopshype.com/rumors/")
    if not html:
        print("Failed to fetch hoopshype rumors page")
        return None
    build_id = extract_build_id(html)
    if not build_id:
        print("Could not extract Next.js build ID")
        return None
    data_url = f"https://www.hoopshype.com/_next/data/{build_id}/rumors.json"
    json_str = fetch_url(data_url)
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return None

def parse_rumors_from_api(data):
    rumors = []
    pp = data.get("pageProps", {})
    ds = pp.get("dehydratedState", {})
    for q in ds.get("queries", []):
        qk = q.get("queryKey", "")
        if isinstance(qk, list) and len(qk) > 1 and qk[1] == "asset_by_ssts":
            for page in q.get("state", {}).get("data", {}).get("pages", []):
                for asset in page.get("searchAssets", {}).get("assets", []):
                    rumor = _parse_api_asset(asset)
                    if rumor:
                        rumors.append(rumor)
    return rumors

def _parse_api_asset(asset):
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
                    clean = re.sub(r"<[^>]+>", "", val)
                    body += re.sub(r"\s+", " ", clean).strip() + " "
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
            parser = ET.XMLParser()
            return ET.parse(str(path), parser=parser).getroot()
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
    print("Fetching HoopsHype rumors data...")
    entries = fetch_news_sitemap()
    all_rumors = []
    used_sitemap = False

    if entries:
        used_sitemap = True
        print(f"  Found {len(entries)} rumor URLs in the last 48h from sitemap")
        state = load_state()
        published = set(state.get("published", []))
        new_entries = [e for e in entries if extract_url_id(e["url"]) not in published]

        if new_entries:
            print(f"  {len(new_entries)} new rumors to scrape...")
            for i, entry in enumerate(new_entries):
                rid = extract_url_id(entry["url"])
                print(f"    [{i+1}/{len(new_entries)}] Fetching article...", end=" ")
                article = fetch_article_data(entry["url"])
                if not article:
                    print("SKIP (fetch failed)")
                    continue
                body = article.get("body", "")
                teams = [{"name": t} for t in article.get("teams", [])]
                rumor = {
                    "id": rid,
                    "headline": article.get("headline") or entry["title"],
                    "url": entry["url"],
                    "pub_date": article.get("pub_date") or entry["pub_date"],
                    "source": "",
                    "body": body,
                    "teams": teams,
                }
                all_rumors.append(rumor)
                print(f"OK ({len(teams)} teams)")
                time.sleep(0.5)
        else:
            print("  No new rumors to scrape.")
    else:
        print("  Sitemap failed, falling back to API...")

    if not used_sitemap:
        data = fetch_rumors_data()
        if data:
            api_rumors = parse_rumors_from_api(data)
            if api_rumors:
                state = load_state()
                published = set(state.get("published", []))
                for r in api_rumors:
                    if r["id"] not in published:
                        all_rumors.append(r)
                print(f"  Got {len(api_rumors)} API rumors ({len([r for r in api_rumors if r['id'] not in published])} new)")

    if not all_rumors:
        print("No new rumors to publish.")
        return

    state = load_state()
    published = set(state.get("published", []))
    all_rumors = [r for r in all_rumors if r["id"] not in published]

    if not all_rumors:
        print("No new rumors to publish.")
        return

    print(f"  {len(all_rumors)} new rumors to add")
    state.setdefault("published", []).extend(r["id"] for r in all_rumors)
    state["published"] = state["published"][-10000:]

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
    all_items = existing_items + [make_rss_item(r) for r in all_rumors]
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(build_rss("HoopsHype Rumors - All", "All NBA trade rumors and free agency buzz from HoopsHype", "https://www.hoopshype.com/rumors/", all_items))
    print(f"  Wrote all.xml ({len(all_items)} items)")

    rumors_by_team = {}
    for rumor in all_rumors:
        for team in rumor["teams"]:
            tname = team.get("name", "")
            if not tname:
                continue
            abbrev = TEAM_NAME_TO_ABBREV.get(tname.lower())
            if abbrev:
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
