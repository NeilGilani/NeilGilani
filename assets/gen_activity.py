#!/usr/bin/env python3
"""Recent-activity block for the profile README.

Lists the public repositories pushed to most recently, with the subject of each
one's latest non-chore commit, between <!--ACTIVITY:START--> / <!--ACTIVITY:END-->.
Everything comes from the GitHub API at run time, so the list can only ever show
work that actually happened. Run daily by .github/workflows/profile.yml.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

USER = "NeilGilani"
SKIP = {"NeilGilani", "hilothefunnydog123-coder"}  # the profile repo itself
ROWS = 5
# Scheduled jobs that commit data refreshes are not "work"; leave them out.
AUTOMATED = re.compile(r"^(chore|ci|merge)\b|^registry: re-score|^data: refresh", re.I)
API = "https://api.github.com"
HERE = os.path.dirname(__file__)
README = os.path.join(os.path.dirname(HERE), "README.md")


def get(url: str):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-activity",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.load(resp)


def latest_commit(repo: str):
    """Newest commit on the default branch that isn't housekeeping or a bot."""
    for c in get(f"{API}/repos/{USER}/{repo}/commits?per_page=20"):
        if ((c.get("author") or {}).get("login") or "").endswith("[bot]"):
            continue
        subject = c["commit"]["message"].splitlines()[0].strip()
        if not AUTOMATED.search(subject):
            return subject, c["commit"]["committer"]["date"][:10]
    return None


def rows():
    out = []
    for r in get(f"{API}/users/{USER}/repos?sort=pushed&per_page=40&type=owner"):
        if r["fork"] or r["archived"] or r["private"] or r["name"] in SKIP:
            continue
        found = latest_commit(r["name"])
        if not found:
            continue
        subject, when = found
        if len(subject) > 78:
            subject = subject[:75].rstrip() + "..."
        subject = subject.replace("|", "\\|").replace("`", "'")
        out.append((when, r["name"], r["html_url"], subject))
        if len(out) == ROWS * 2:  # a few spares, then order by commit date
            break
    return sorted(out, reverse=True)[:ROWS]


def build_block(items) -> str:
    lines = ["<!--ACTIVITY:START-->", "",
             "| date | repository | latest commit |", "|:--|:--|:--|"]
    for when, name, url, subject in items:
        lines.append(f"| `{when}` | [{name}]({url}) | {subject} |")
    lines += ["", "<!--ACTIVITY:END-->"]
    return "\n".join(lines)


def inject(block: str) -> None:
    with open(README) as f:
        text = f.read()
    pattern = re.compile(r"<!--ACTIVITY:START-->.*?<!--ACTIVITY:END-->", re.DOTALL)
    if not pattern.search(text):
        print("no ACTIVITY markers in README; skipping")
        return
    with open(README, "w") as f:
        f.write(pattern.sub(lambda _: block, text))


def main() -> None:
    try:
        items = rows()
    except Exception as exc:  # network/API trouble: keep yesterday's block
        print(f"activity fetch failed ({exc}); leaving README unchanged")
        return
    if items:
        inject(build_block(items))
        print(f"activity updated: {len(items)} rows")


if __name__ == "__main__":
    main()
