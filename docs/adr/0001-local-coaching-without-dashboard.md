---
status: accepted
---

# Coach locally with Claude Code; no dashboard, no Gemini export

Deck coaching used to mean copying an export from the GitHub Pages dashboard into a Gemini Gem. The Gem kept getting numbers wrong (records, level counts, elixir averages, card overlap), which grew its instructions into a long list of "count exactly" rules, and suggestions were never followed up because the battle log only holds the last ~30 battles. We decided to coach locally instead: Claude Code works directly against the repo, Python computes and validates everything that has a correct answer, and the AI only does the coaching judgement. The dashboard, the Gemini export and the Gem instructions are removed; the coaching method moves into a project skill.

## Consequences

- GitHub Actions stays, but only as a data collector that appends new battles to the Battle history. The API returns just the latest ~25–30 battles, so fetching only when a coaching session starts would lose battles.
- Each coaching session starts with `git pull` to get the data Actions has committed.
- Card balance and Meta decks are looked up online during a session, with source and date, rather than kept in the repo; `meta.json` is removed.
- The repo name still says "dashboard" even though there no longer is one.
