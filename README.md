# clash-royale-player-dashboard

[Open the published dashboard](https://flunker-cmd.github.io/clash-royale-player-dashboard/)

Personal Clash Royale deck analytics for player `#URUQ09LVG`.

## What it does

- Fetches player profile, battle log, and card data through GitHub Actions.
- Shows observed decks and win-rate signals from the available battle log.
- Highlights cards that have room for upgrades.
- Keeps API credentials out of the browser.

Deck recommendations are intentionally cautious: the official API exposes a limited battle log, so a small sample cannot prove that one deck is better than another. Meta comparison is prepared as an optional reviewed `meta.json` data source and is not invented from the official API response.

`meta.json` is intentionally empty in the starter project. Populate it only from a trusted, permitted data source before using meta-based suggestions.

## Setup

1. Create a repository named `clash-royale-player-dashboard`.
2. Add the repository secret `CLASH_ROYALE_TOKEN` under **Settings > Secrets and variables > Actions**.
3. Ensure the API token's IP allowlist permits GitHub Actions.
4. Enable GitHub Pages from the repository's `main` branch and root folder.
5. Run **Actions > Fetch Player Data > Run workflow** once.

The scheduled workflow refreshes data every two hours. To use another player, change `CLASH_ROYALE_PLAYER_TAG` in `.github/workflows/fetch.yml`.

## Local checks

```powershell
python -m unittest discover -s tests -v
```

The live API fetch requires `CLASH_ROYALE_TOKEN`; never put that token in `index.html` or committed JSON fixtures.
