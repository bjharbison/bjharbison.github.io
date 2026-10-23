# bjharbison.github.io

The project hub at **https://bjharbison.github.io**: one page listing every public repo on this account, with an **Open demo** button for any repo that has GitHub Pages turned on.

## How it updates

`.github/workflows/build.yml` runs `scripts/build.py`, which reads the account's repos from the GitHub API, renders `template.html` into `_site/index.html`, and deploys it to Pages. It runs:

- every 6 hours, so new repos and newly published demos show up on their own
- on every push to `main`
- on demand: **Actions → Build project hub → Run workflow**

Nothing is committed back to the repo; the generated page lives only in the Pages deployment.

## What gets listed

- Public repos owned by this account. Private repos are never listed, and forks and this repo itself are skipped.
- A repo gets a lit lamp and an **Open demo** button when GitHub Pages is on for it. The link is the repo's *Website* field if set (handy when the app isn't `index.html`, e.g. `.../trapline/trapline.html`), otherwise `https://bjharbison.github.io/<repo>/`.
- The description and topics come from each repo's **About** box on GitHub, so edit them there.

## Tweaks (optional)

Create `hub.json` in the repo root to hide, pin, or override links:

```json
{
  "hide": ["some-scratch-repo"],
  "pin": ["chessmaster", "trapline"],
  "live_url": { "aegis-ms": "https://bjharbison.github.io/aegis-ms/app/AEGIS_MS.html" }
}
```

Pinned repos go first, in the order listed; everything else is sorted by most recent push.

## Run locally

```bash
GITHUB_TOKEN=<optional token> python3 scripts/build.py
# open _site/index.html
```

Standard library only; no dependencies.

## One-time setup

**Settings → Pages → Build and deployment → Source: GitHub Actions.**
