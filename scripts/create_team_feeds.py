from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_feeds import NBA_TEAMS, build_rss, TEAMS_DIR

def main():
    TEAMS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for slug, info in NBA_TEAMS.items():
        abbrev = info["abbrev"]
        team_path = TEAMS_DIR / f"{abbrev}.xml"
        if not team_path.exists():
            xml = build_rss(
                f"HoopsHype Rumors - {info['name']}",
                f"{info['name']} trade rumors and free agency buzz from HoopsHype",
                "https://www.hoopshype.com/rumors/",
                [],
            )
            with open(team_path, "w", encoding="utf-8") as f:
                f.write(xml)
            count += 1
    print(f"Created {count} team feed files")

if __name__ == "__main__":
    main()
