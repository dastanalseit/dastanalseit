#!/usr/bin/env python3
"""Build self-contained SVG art for a GitHub profile README."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "profile.json").read_text())
PALETTE = ("#1e1b35", "#3b236c", "#5b34a1", "#7c3aed", "#a78bfa")


class ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.days: dict[str, dict[str, int]] = {}
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in ("td", "rect") and values.get("data-date") and values.get("data-level"):
            level = int(values["data-level"] or 0)
            if not 0 <= level <= 4:
                raise ValueError(f"Unexpected contribution level: {level}")
            self.days[values["data-date"]] = {"level": level}

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def fetch() -> None:
    username = CONFIG["username"]
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
        raise ValueError("Invalid GitHub username")
    url = f"https://github.com/users/{username}/contributions"
    request = Request(url, headers={"User-Agent": "profile-readme-art/1.0"})
    with urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8")
    parser = ContributionParser()
    parser.feed(html)
    if len(parser.days) < 300:
        raise RuntimeError("GitHub contribution calendar was missing or changed")
    match = re.search(r"([\d,]+)\s+contributions?\s+in the last year", " ".join(parser.text), re.I)
    if not match:
        raise RuntimeError("GitHub contribution total was missing or changed")
    payload = {
        "as_of": date.today().isoformat(),
        "total": int(match.group(1).replace(",", "")),
        "days": dict(sorted(parser.days.items())),
    }
    (ROOT / "data" / "contributions.json").write_text(json.dumps(payload, indent=2) + "\n")


def frame(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{escape(title)}">\n'
        f'<title>{escape(title)}</title>\n'
        f'<rect width="{width}" height="{height}" rx="17" fill="#0d1024"/>\n'
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="16.5" '
        'fill="none" stroke="#5b34a1"/>\n'
        f'{body}</svg>\n'
    )


def portrait() -> None:
    tokens = (ROOT / "assets" / "avatar.pgm").read_text().split()
    if tokens[0] != "P2":
        raise ValueError("Expected ASCII PGM avatar")
    width, height, max_value = map(int, tokens[1:4])
    pixels = list(map(int, tokens[4:]))
    if max_value != 255 or len(pixels) != width * height:
        raise ValueError("Invalid avatar dimensions")
    ramp = "@%#*+=-:. "
    body = ['<defs>']
    for row in range(height):
        y = 53 + row * 5.0
        body.append(f'<clipPath id="r{row}"><rect x="17" y="{y-5:.1f}" width="0" height="6">'
                    f'<animate attributeName="width" from="0" to="385" dur=".7s" '
                    f'begin="{row*.033:.3f}s" fill="freeze"/></rect></clipPath>')
    body.append('</defs><text x="19" y="28" fill="#39d353" font-family="monospace" font-size="12">'
                f'{escape(CONFIG["username"])}@github:~$ cat avatar.txt</text>')
    for row in range(height):
        values = pixels[row * width:(row + 1) * width]
        chars = "".join(ramp[min(len(ramp)-1, max(0, round(v / 255 * (len(ramp)-1))))] for v in values)
        y = 53 + row * 5.0
        body.append(f'<text x="19" y="{y:.1f}" clip-path="url(#r{row})" '
                    'font-family="monospace" font-size="5.9" fill="#c9d1d9" '
                    f'xml:space="preserve">{escape(chars)}</text>')
    body.append('<text x="19" y="337" fill="#768390" font-family="monospace" '
                'font-size="10">// from my GitHub avatar</text>')
    (ROOT / "avatar-ascii.svg").write_text(frame(400, 350, "Animated ASCII avatar", "\n".join(body)))


def card() -> None:
    username = CONFIG["username"]
    rows = [
        ("NAME", CONFIG["name"]),
        ("LOCATION", CONFIG["location"]),
        ("FOCUS", CONFIG["focus"]),
        ("STACK", CONFIG["stack"]),
        ("BUILDING", CONFIG["building"]),
    ]
    body = [
        '<circle cx="24" cy="25" r="5" fill="#f85149"/>',
        '<circle cx="42" cy="25" r="5" fill="#d29922"/>',
        '<circle cx="60" cy="25" r="5" fill="#3fb950"/>',
        '<text x="82" y="29" fill="#768390" font-family="monospace" font-size="12">about.sh</text>',
        '<path d="M0 42H479" stroke="#303d4c"/>',
        f'<text x="25" y="80" fill="#39d353" font-family="monospace" font-size="19" font-weight="bold">'
        f'{escape(username)}@github</text>',
        '<path d="M25 92H452" stroke="#303d4c"/>',
    ]
    for i, (label, value) in enumerate(rows):
        y = 125 + i * 37
        body.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                    f'dur=".35s" begin="{.2+i*.2:.1f}s" fill="freeze"/>'
                    f'<text x="25" y="{y}" fill="#79c0ff" font-family="monospace" '
                    f'font-size="12">{escape(label)}</text>'
                    f'<text x="122" y="{y}" fill="#e6edf3" font-family="monospace" '
                    f'font-size="12">{escape(value)}</text></g>')
    body.append('<text x="25" y="330" fill="#768390" font-family="monospace" '
                'font-size="11">$ open to ideas, projects, and learning</text>')
    (ROOT / "info-card.svg").write_text(frame(480, 350, f"About {username}", "\n".join(body)))


def heatmap() -> None:
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    as_of = date.fromisoformat(data["as_of"])
    start = as_of - timedelta(days=(as_of.weekday() + 1) % 7 + 52 * 7)
    days = data["days"]
    body = [
        '<text x="25" y="35" fill="#a78bfa" font-family="monospace" '
        'font-size="14">$ ./contributions.sh</text>',
        f'<text x="25" y="62" fill="#e5e7eb" font-family="monospace" '
        f'font-size="18" font-weight="bold">{data["total"]:,} contributions in the last year</text>',
    ]
    previous_month = None
    for week in range(53):
        first = start + timedelta(days=week * 7)
        if first.month != previous_month and week < 50:
            body.append(f'<text x="{37+week*15}" y="89" fill="#8b949e" '
                        f'font-family="monospace" font-size="10">{first.strftime("%b")}</text>')
            previous_month = first.month
        for weekday in range(7):
            day = first + timedelta(days=weekday)
            if day > as_of:
                continue
            level = min(4, max(0, int(days.get(day.isoformat(), {}).get("level", 0))))
            x, y = 37 + week * 15, 101 + weekday * 15
            body.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" '
                        f'fill="{PALETTE[level]}" opacity="0"><animate attributeName="opacity" '
                        f'from="0" to="1" dur=".22s" begin="{.15+week*.018+weekday*.035:.3f}s" '
                        f'fill="freeze"/><title>{day.isoformat()}: level {level}</title></rect>')
    for weekday, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(f'<text x="8" y="{110+weekday*15}" fill="#8b949e" '
                    f'font-family="monospace" font-size="10">{label}</text>')
    body.append('<text x="680" y="230" fill="#8b949e" font-family="monospace" '
                'font-size="10">Less</text>')
    for i, color in enumerate(PALETTE):
        body.append(f'<rect x="{711+i*16}" y="221" width="11" height="11" rx="2" fill="{color}"/>')
    body.append('<text x="795" y="230" fill="#8b949e" font-family="monospace" '
                'font-size="10">More</text>')
    (ROOT / "contrib-heatmap.svg").write_text(frame(880, 250, "GitHub contribution calendar", "\n".join(body)))


def snake() -> None:
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    as_of = date.fromisoformat(data["as_of"])
    start = as_of - timedelta(days=(as_of.weekday() + 1) % 7 + 52 * 7)
    days = data["days"]
    body = [
        '<text x="25" y="31" fill="#a78bfa" font-family="monospace" '
        'font-size="14">$ ./follow-the-contributions.sh</text>',
    ]
    for week in range(53):
        for weekday in range(7):
            day = start + timedelta(days=week * 7 + weekday)
            if day > as_of:
                continue
            level = min(4, max(0, int(days.get(day.isoformat(), {}).get("level", 0))))
            x, y = 39 + week * 15, 51 + weekday * 15
            body.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" '
                        f'fill="{PALETTE[level]}"/>')
    points = [(44.5 + week * 15, 56.5 + weekday * 15)
              for weekday in range(7)
              for week in (range(53) if weekday % 2 == 0 else range(52, -1, -1))]
    path = "M" + " ".join(f"{x:g},{y:g}" if i == 0 else f"L{x:g},{y:g}"
                          for i, (x, y) in enumerate(points))
    body.append(f'<path d="{path}" fill="none" stroke="#a78bfa" '
                'stroke-opacity=".13" stroke-width="2"/>')
    for segment in range(7, -1, -1):
        size = 2.9 if segment else 5.2
        opacity = 0.22 + (7 - segment) * 0.1
        body.append(f'<circle r="{size}" fill="#c4b5fd" opacity="{opacity:.2f}">'
                    f'<animateMotion dur="36s" begin="-{1.4-segment*.16:.2f}s" '
                    f'repeatCount="indefinite" path="{path}"/></circle>')
    body.append('<text x="25" y="181" fill="#9ca3af" font-family="monospace" '
                'font-size="10">A little journey across the contribution graph</text>')
    (ROOT / "contrib-snake.svg").write_text(frame(880, 200, "Animated contribution snake", "\n".join(body)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=("fetch", "portrait", "card", "heatmap", "snake", "all"))
    args = parser.parse_args()
    if args.task == "fetch":
        fetch()
    elif args.task == "portrait":
        portrait()
    elif args.task == "card":
        card()
    elif args.task == "heatmap":
        heatmap()
    elif args.task == "snake":
        snake()
    else:
        portrait()
        card()
        heatmap()
        snake()


if __name__ == "__main__":
    main()
