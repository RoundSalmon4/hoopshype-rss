import json
import glob
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def merge_caches():
    merged = {}
    for cache_file in DATA_DIR.glob("team_cache_*.json"):
        with open(cache_file, "r") as f:
            data = json.load(f)
            merged.update(data)
        cache_file.unlink()
    if merged:
        with open(DATA_DIR / "team_cache.json", "w") as f:
            json.dump(merged, f, indent=2)
        print(f"Merged {len(merged)} teams into team_cache.json")
    else:
        print("No cache files to merge")

if __name__ == "__main__":
    merge_caches()
