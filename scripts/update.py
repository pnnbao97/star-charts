"""Daily update: append today's star count and re-render every chart.

Run by the scheduled workflow. Reads the public stargazers_count of each
tracked repo (GITHUB_TOKEN is used only to avoid anonymous rate limits;
no scope beyond public data is needed), records one point per UTC day,
and re-renders the SVGs.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render_charts

ROOT = Path(__file__).resolve().parent.parent


def fetch_star_count(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "star-charts-updater",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["stargazers_count"]


def write_data(path, data):
    """Write the data file with one point per line for readable diffs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ",\n".join(f'    ["{d}", {s}]' for d, s in data["points"])
    text = ('{\n  "repo": "%s",\n  "points": [\n%s\n  ]\n}\n'
            % (data["repo"], lines))
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    data_files = sorted(ROOT.glob("data/*/*.json"))
    if not data_files:
        sys.exit("no data files found; run scripts/backfill.py first")

    today = datetime.now(timezone.utc).date()
    failures = 0
    for path in data_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        repo = data["repo"]
        try:
            count = fetch_star_count(repo)
        except Exception as exc:
            print(f"WARN {repo}: fetch failed ({exc}), keeping last state")
            failures += 1
            count = None

        if count is not None:
            iso = today.isoformat()
            if data["points"] and data["points"][-1][0] == iso:
                data["points"][-1][1] = count
            else:
                data["points"].append([iso, count])
            write_data(path, data)

        owner, name = repo.split("/")
        render_charts(data, ROOT / "charts" / owner / name, updated=today)
        print(f"{repo}: {data['points'][-1][1]} stars")

    if failures == len(data_files):
        sys.exit("every repo failed to update")


if __name__ == "__main__":
    main()
