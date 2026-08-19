"""Render star-history SVG charts (light + dark) from a data file.

Pure stdlib, no dependencies. Charts are deterministic for a given
data file so re-renders produce no spurious diffs.
"""

import math
from datetime import date

WIDTH, HEIGHT = 800, 420
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 78, 36, 64, 56

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

THEMES = {
    "light": {
        "text": "#24292f",
        "muted": "#57606a",
        "grid": "#d0d7de",
        "line": "#e0524e",
        "area": "#e0524e",
        "dot": "#e0524e",
    },
    "dark": {
        "text": "#e6edf3",
        "muted": "#8b949e",
        "grid": "#30363d",
        "line": "#ff7b72",
        "area": "#ff7b72",
        "dot": "#ff7b72",
    },
}

FONT = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


def _fmt_stars(n):
    return f"{n:,}"


def _fmt_date(d):
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def _fmt_tick_date(d, span_days):
    if span_days > 300:
        return f"{MONTHS[d.month - 1]} {d.year}"
    return f"{MONTHS[d.month - 1]} {d.day}"


def _nice_step(raw):
    """Round raw up to a 1/2/2.5/5 x 10^k step."""
    if raw <= 0:
        return 1
    exp = math.floor(math.log10(raw))
    frac = raw / 10 ** exp
    for nice in (1, 2, 2.5, 5, 10):
        if frac <= nice:
            return nice * 10 ** exp
    return 10 ** (exp + 1)


def render_svg(points, repo, theme_name, updated=None):
    """points: list of (date, stars) tuples, sorted ascending."""
    t = THEMES[theme_name]
    dates = [p[0] for p in points]
    stars = [p[1] for p in points]

    x0, x1 = dates[0].toordinal(), dates[-1].toordinal()
    if x1 == x0:
        x1 = x0 + 1
    span_days = x1 - x0

    y_max_data = max(stars)
    y_step = _nice_step(y_max_data / 4)
    y_max = y_step * math.ceil(max(y_max_data, 1) / y_step)

    plot_w = WIDTH - MARGIN_L - MARGIN_R
    plot_h = HEIGHT - MARGIN_T - MARGIN_B

    def sx(d):
        return MARGIN_L + (d.toordinal() - x0) / (x1 - x0) * plot_w

    def sy(v):
        return MARGIN_T + plot_h - v / y_max * plot_h

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="Star history of {repo}">'
    )

    # Title and subtitle
    parts.append(
        f'<text x="{MARGIN_L}" y="30" font-family="{FONT}" font-size="18" '
        f'font-weight="600" fill="{t["text"]}">Star history of {repo}</text>'
    )
    subtitle = f"{_fmt_stars(stars[-1])} stars"
    if updated is not None:
        subtitle += f" · updated {_fmt_date(updated)}"
    parts.append(
        f'<text x="{MARGIN_L}" y="50" font-family="{FONT}" font-size="12" '
        f'fill="{t["muted"]}">{subtitle}</text>'
    )

    # Horizontal grid lines + y labels
    v = 0
    while v <= y_max:
        y = sy(v)
        parts.append(
            f'<line x1="{MARGIN_L}" y1="{y:.1f}" x2="{WIDTH - MARGIN_R}" y2="{y:.1f}" '
            f'stroke="{t["grid"]}" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        parts.append(
            f'<text x="{MARGIN_L - 8}" y="{y + 4:.1f}" font-family="{FONT}" '
            f'font-size="12" text-anchor="end" fill="{t["muted"]}">{_fmt_stars(int(v))}</text>'
        )
        v += y_step

    # X ticks: ~5 evenly spaced dates
    n_ticks = min(5, len(dates)) if len(dates) > 1 else 1
    tick_days = sorted({x0 + round(i * (x1 - x0) / max(n_ticks - 1, 1))
                        for i in range(n_ticks)})
    for od in tick_days:
        d = date.fromordinal(od)
        x = sx(d)
        parts.append(
            f'<text x="{x:.1f}" y="{HEIGHT - MARGIN_B + 24}" font-family="{FONT}" '
            f'font-size="12" text-anchor="middle" fill="{t["muted"]}">'
            f'{_fmt_tick_date(d, span_days)}</text>'
        )

    # Area fill under the line
    coords = [(sx(d), sy(v)) for d, v in points]
    line_path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                         for i, (x, y) in enumerate(coords))
    baseline = MARGIN_T + plot_h
    area_path = (line_path
                 + f" L{coords[-1][0]:.1f},{baseline:.1f}"
                 + f" L{coords[0][0]:.1f},{baseline:.1f} Z")
    parts.append(f'<path d="{area_path}" fill="{t["area"]}" fill-opacity="0.10"/>')
    parts.append(
        f'<path d="{line_path}" fill="none" stroke="{t["line"]}" '
        f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # End dot + count label
    ex, ey = coords[-1]
    parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{t["dot"]}"/>')
    label = _fmt_stars(stars[-1])
    lx = min(ex + 8, WIDTH - MARGIN_R)
    anchor = "start" if ex + 60 < WIDTH - MARGIN_R else "end"
    if anchor == "end":
        lx = ex - 8
    parts.append(
        f'<text x="{lx:.1f}" y="{ey - 8:.1f}" font-family="{FONT}" font-size="13" '
        f'font-weight="600" text-anchor="{anchor}" fill="{t["line"]}">{label}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def render_charts(data, out_dir, updated=None):
    """Write light.svg and dark.svg for a parsed data dict into out_dir."""
    import os
    points = [(date.fromisoformat(d), s) for d, s in data["points"]]
    points.sort(key=lambda p: p[0])
    os.makedirs(out_dir, exist_ok=True)
    for theme in ("light", "dark"):
        svg = render_svg(points, data["repo"], theme, updated=updated)
        with open(os.path.join(out_dir, f"{theme}.svg"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(svg + "\n")
