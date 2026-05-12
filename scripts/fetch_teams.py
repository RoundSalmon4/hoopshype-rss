import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_feeds import fetch_rumors_data, parse_teams, NBA_TEAMS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def main():
    print("Fetching hoopshype data...")
    data, build_id = fetch_rumors_data()
    if not data:
        print("Failed to fetch data")
        return
    teams = parse_teams(data)
    if not teams:
        print("No teams found")
        return
    team_cache = {}
    for tag_id, info in teams.items():
        abbrev = info.get("abbrev", "")
        team_cache[tag_id] = {
            "abbrev": abbrev,
            "name": info.get("name", ""),
            "location": info.get("location", ""),
            "nickname": info.get("nickname", ""),
            "contentTag": tag_id,
        }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "team_cache.json", "w") as f:
        json.dump(team_cache, f, indent=2)
    print(f"Saved {len(team_cache)} teams to team_cache.json")

if __name__ == "__main__":
    main()
