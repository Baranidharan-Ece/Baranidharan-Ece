
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = "Baranidharan-Ece"
TOKEN = os.environ["GH_TOKEN"]
OUTPUT = Path("dist/activity-graph.svg")

# Fetch public GitHub activity
url = f"https://api.github.com/users/{USERNAME}/events?per_page=100"
request = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-Activity-Graph"
    }
)

with urllib.request.urlopen(request, timeout=30) as response:
    events = json.load(response)

# Count public activity over the last 30 days
today = datetime.now(timezone.utc).date()
start = today - timedelta(days=29)
counts = Counter()

tracked = {
    "PushEvent", "PullRequestEvent", "IssuesEvent",
    "IssueCommentEvent", "PullRequestReviewEvent",
    "CreateEvent", "CommitCommentEvent"
}

for event in events:
    if event.get("type") not in tracked:
        continue

    event_date = datetime.fromisoformat(
        event["created_at"].replace("Z", "+00:00")
    ).date()

    if start <= event_date <= today:
        counts[event_date] += 1

days = [start + timedelta(days=i) for i in range(30)]
values = [counts[d] for d in days]

# Create a custom dark-theme SVG line graph
width, height = 900, 310
left, right, top, bottom = 55, 25, 50, 55
plot_w = width - left - right
plot_h = height - top - bottom
max_value = max(max(values), 1)
points = []

for i, value in enumerate(values):
    x = left + i * plot_w / 29
    y = top + plot_h - (value / max_value) * plot_h
    points.append((x, y))

line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
area = (
    f"{left},{top + plot_h} " + line +
    f" {left + plot_w},{top + plot_h}"
)

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<rect width="100%" height="100%" rx="18" fill="#0d1117"/>',
    '<text x="55" y="30" fill="#c9d1d9" font-size="19" font-family="Arial" font-weight="bold">PUBLIC GITHUB ACTIVITY</text>',
    '<text x="55" y="47" fill="#8b949e" font-size="11" font-family="Arial">Last 30 days · Event-based activity</text>'
]

for i in range(5):
    y = top + i * plot_h / 4
    label = round(max_value * (4 - i) / 4)
    svg.append(
        f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#30363d" stroke-dasharray="4 5"/>'
    )
    svg.append(
        f'<text x="{left - 12}" y="{y + 4:.1f}" fill="#8b949e" font-size="11" text-anchor="end" font-family="Arial">{label}</text>'
    )

svg.append(f'<polygon points="{area}" fill="#238636" opacity="0.18"/>')
svg.append(f'<polyline points="{line}" fill="none" stroke="#3fb950" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')

for i, (x, y) in enumerate(points):
    if values[i] > 0:
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#3fb950" stroke="#0d1117" stroke-width="1.5"/>')

for i in [0, 6, 13, 20, 29]:
    x = left + i * plot_w / 29
    label = days[i].strftime("%b %d")
    svg.append(
        f'<text x="{x:.1f}" y="{height - 23}" fill="#8b949e" font-size="11" text-anchor="middle" font-family="Arial">{escape(label)}</text>'
    )

total = sum(values)
svg.append(
    f'<text x="{width - right}" y="30" fill="#3fb950" font-size="16" text-anchor="end" font-family="Arial" font-weight="bold">{total} events</text>'
)
svg.append("</svg>")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Graph generated: {OUTPUT} ({total} public events)")
