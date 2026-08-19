"""One-time backfill of a repo's star history.

Usage: python scripts/backfill.py owner/repo

Uses the `gh` CLI for authentication (star timestamps require an
authenticated call with push access on the charted repo). Run this
locally, never in CI. Reconstructs the cumulative curve from the
timestamps of the stars that still exist today, so past unstars are
invisible; from today on, update.py records one observed total per day.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render_charts
from update import write_data

ROOT = Path(__file__).resolve().parent.parent


def gh_api(path, header=None):
    cmd = ["gh", "api", path]
    if header:
        cmd += ["-H", header]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        sys.exit(f"gh api {path} failed:\n{result.stderr}")
    return result.stdout


def main():
    if len(sys.argv) != 2 or sys.argv[1].count("/") != 1:
        sys.exit("usage: python scripts/backfill.py owner/repo")
    repo = sys.argv[1]

    info = json.loads(gh_api(f"repos/{repo}"))
    repo = info["full_name"]  # canonical casing
    total = info["stargazers_count"]
    print(f"{repo}: {total} stars, fetching timestamps...")

    timestamps = []
    page = 1
    while True:
        raw = gh_api(
            f"repos/{repo}/stargazers?per_page=100&page={page}",
            header="Accept: application/vnd.github.star+json",
        )
        batch = json.loads(raw)
        if not batch:
            break
        timestamps += [e["starred_at"] for e in batch if "starred_at" in e]
        print(f"  page {page}: {len(timestamps)} collected", flush=True)
        if len(batch) < 100 or page >= 400:
            break
        page += 1

    days = sorted(ts[:10] for ts in timestamps)
    points = []
    count = 0
    for day in days:
        count += 1
        if points and points[-1][0] == day:
            points[-1][1] = count
        else:
            points.append([day, count])

    # Anchor the curve at today's official total.
    today = datetime.now(timezone.utc).date().isoformat()
    if points and points[-1][0] == today:
        points[-1][1] = total
    else:
        points.append([today, total])

    owner, name = repo.split("/")
    data = {"repo": repo, "points": points}
    data_path = ROOT / "data" / owner / f"{name}.json"
    write_data(data_path, data)
    render_charts(data, ROOT / "charts" / owner / name,
                  updated=datetime.now(timezone.utc).date())
    print(f"wrote {data_path} ({len(points)} points) and charts/{owner}/{name}/")


if __name__ == "__main__":
    main()
