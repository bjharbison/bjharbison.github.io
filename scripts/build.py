#!/usr/bin/env python3
"""Build the project hub page from the GitHub account's public repositories.

Run by .github/workflows/build.yml. Locally:

    GITHUB_TOKEN=... python3 scripts/build.py            # live from the API
    python3 scripts/build.py --from-json sample.json     # from a saved repo list

Writes _site/index.html and _site/repos.json. Standard library only.
"""
import argparse
import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.request

OWNER = os.environ.get("HUB_OWNER", "bjharbison")
ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template.html"
OUT = ROOT / "_site"
CONFIG = ROOT / "hub.json"


def fetch_repos(token):
    """All public, owner-owned repos, following pagination."""
    repos, page = [], 1
    while True:
        url = f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": f"{OWNER}-hub-builder",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        if not isinstance(batch, list):
            sys.exit(f"Unexpected API response: {batch}")
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def load_config():
    """Optional hub.json: {"hide": ["repo"], "pin": ["repo"], "live_url": {"repo": "https://..."}}"""
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    return {}


def normalize(raw, cfg):
    hide = set(cfg.get("hide", []))
    pin = cfg.get("pin", [])
    live_override = cfg.get("live_url", {})
    out = []
    for r in raw:
        name = r["name"]
        if r.get("private") or r.get("fork") or name in hide:
            continue
        if name.lower() == f"{OWNER}.github.io".lower():
            continue
        live = live_override.get(name)
        if not live and r.get("has_pages"):
            live = (r.get("homepage") or "").strip() or f"https://{OWNER}.github.io/{name}/"
        out.append({
            "name": name,
            "description": (r.get("description") or "").strip(),
            "code_url": r["html_url"],
            "live_url": live,
            "language": r.get("language"),
            "topics": r.get("topics") or [],
            "updated": (r.get("pushed_at") or r.get("updated_at") or "")[:10],
            "archived": bool(r.get("archived")),
            "pinned": name in pin,
        })
    pin_rank = {n: i for i, n in enumerate(pin)}
    out.sort(key=lambda x: x["updated"], reverse=True)
    out.sort(key=lambda x: pin_rank.get(x["name"], len(pin)))
    return out


def fmt_date(iso):
    try:
        d = dt.date.fromisoformat(iso)
    except ValueError:
        return ""
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def row(p):
    e = html.escape
    live = bool(p["live_url"])
    status = "Live demo" if live else "Code only"
    meta = [x for x in [p["language"], "Archived" if p["archived"] else None] if x]
    links = []
    if live:
        links.append(f'<a class="go" href="{e(p["live_url"])}">Open demo</a>')
    links.append(f'<a href="{e(p["code_url"])}">Code</a>')
    topics = "".join(f"<li>{e(t)}</li>" for t in p["topics"][:6])
    search = " ".join([p["name"], p["description"], p["language"] or "", *p["topics"]]).lower()
    return f"""
<li class="proj{' is-live' if live else ''}" data-live="{int(live)}" data-name="{e(p['name'].lower())}" data-updated="{e(p['updated'])}" data-search="{e(search)}">
  <span class="lamp" role="img" aria-label="{status}" title="{status}"></span>
  <div class="body">
    <h2>{e(p['name'])}</h2>
    {f'<p class="desc">{e(p["description"])}</p>' if p['description'] else '<p class="desc empty">No description yet.</p>'}
    <div class="meta">
      {''.join(f'<span>{e(m)}</span>' for m in meta)}
      {f'<ul class="topics">{topics}</ul>' if topics else ''}
    </div>
  </div>
  <div class="side">
    <time datetime="{e(p['updated'])}">Updated {e(fmt_date(p['updated']))}</time>
    <div class="links">{''.join(links)}</div>
  </div>
</li>"""


def render(projects):
    live_n = sum(1 for p in projects if p["live_url"])
    built = dt.datetime.now(dt.timezone.utc)
    page = TEMPLATE.read_text()
    subs = {
        "{{OWNER}}": html.escape(OWNER),
        "{{TOTAL}}": str(len(projects)),
        "{{LIVE}}": str(live_n),
        "{{CODE}}": str(len(projects) - live_n),
        "{{BUILT}}": built.strftime("%b %-d, %Y at %H:%M UTC"),
        "{{ROWS}}": "".join(row(p) for p in projects)
            or '<li class="none">No public repositories yet. Make a repo public and it appears here on the next build.</li>',
    }
    for k, v in subs.items():
        page = page.replace(k, v)
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-json", help="build from a saved GitHub API repo list instead of the API")
    args = ap.parse_args()
    if args.from_json:
        raw = json.loads(pathlib.Path(args.from_json).read_text())
    else:
        raw = fetch_repos(os.environ.get("GITHUB_TOKEN"))
    projects = normalize(raw, load_config())
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render(projects))
    (OUT / "repos.json").write_text(json.dumps(projects, indent=1))
    print(f"Built {len(projects)} projects ({sum(1 for p in projects if p['live_url'])} live) -> {OUT}")


if __name__ == "__main__":
    main()
