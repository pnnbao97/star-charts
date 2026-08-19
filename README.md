# star-charts

Self-hosted star history charts, updated daily by [a scheduled workflow](.github/workflows/update.yml) in this repository. No external service is involved in serving or updating them.

GitHub restricted the stargazers API in June 2026, which broke the hosted chart services (star-history.com and friends). This repo replaces them: the full history was backfilled once locally (`scripts/backfill.py`), and from then on the workflow appends one observed star count per UTC day (`scripts/update.py`) and re-renders the SVGs (`scripts/render.py`) using only the ephemeral `GITHUB_TOKEN` with `contents: write` on this repo — no stored credentials, no write access to the charted repos.

## Charts

### pnnbao97/VieNeu-TTS

<a href="https://github.com/pnnbao97/VieNeu-TTS/stargazers">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/pnnbao97/star-charts/main/charts/pnnbao97/VieNeu-TTS/dark.svg" />
    <img alt="Star history of pnnbao97/VieNeu-TTS" src="https://raw.githubusercontent.com/pnnbao97/star-charts/main/charts/pnnbao97/VieNeu-TTS/light.svg" />
  </picture>
</a>

## Adding a repo

```
python scripts/backfill.py owner/repo
git add -A && git commit -m "feat: track owner/repo" && git push
```

Backfill needs `gh` auth with push access on the charted repo (GitHub's restriction on reading star timestamps). History from before the backfill is reconstructed from the stars that still exist, so earlier unstars are invisible; from the backfill on, the chart records one observed total per day.

## Notes

- The daily commit (the "updated" date changes even when the count doesn't) keeps the scheduled workflow from being disabled by GitHub's 60-day inactivity rule.
- Do not rename the default branch — it is part of every embed URL.
