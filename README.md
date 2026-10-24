# clash-royale-player-dashboard

Personal Clash Royale deck coaching for player `#URUQ09LVG`, done locally with Claude Code against the data in this repo. There is no web dashboard any more; see [docs/adr/0001-local-coaching-without-dashboard.md](docs/adr/0001-local-coaching-without-dashboard.md).

## How it works

- **GitHub Actions** fetches the player profile and battle log every two hours and appends new battles to `battle-history.json`. The API only returns the latest ~30 battles, so the history is what lets Experiments be judged over time.
- **`coach.py`** computes everything that has a correct answer: deck records, Experiment Verdicts, card levels, elixir averages and War deck plan checks. Run `python coach.py status` for an overview.
- **`coaching-log.json`** records the declared Main deck, started Experiments and the Active war deck plan.
- **Claude Code** coaches through the project skill in `.claude/skills/deck-coach/`. Ask things like "how do I improve my main deck?" or "suggest four new war decks".

Domain terms are defined in [GLOSSARY.md](GLOSSARY.md).

## Setup

1. Add the repository secret `CLASH_ROYALE_TOKEN` under **Settings > Secrets and variables > Actions**.
2. Ensure the API token's IP allowlist permits the RoyaleAPI proxy.
3. Run **Actions > Fetch Player Data > Run workflow** once.

To use another player, change `CLASH_ROYALE_PLAYER_TAG` in `.github/workflows/fetch.yml`.

## Local checks

```powershell
python -m unittest discover -s tests -v
```

The live API fetch requires `CLASH_ROYALE_TOKEN`; never put that token in committed files.
