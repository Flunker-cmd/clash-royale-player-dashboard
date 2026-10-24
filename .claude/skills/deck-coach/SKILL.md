---
name: deck-coach
description: Coach the player's Clash Royale decks from the repo's data. Use when the player asks how to improve their Main deck, wants a War deck plan, starts or follows up an Experiment, or declares a new Main deck or war plan.
---

# Deck coach

The terms (Main deck, Experiment, Verdict, War deck plan, Collection, Meta deck) are defined in `GLOSSARY.md`; use them exactly.

**Code computes, you coach.** Every number you state (records, win rates, levels, elixir averages, overlaps) is quoted from `coach.py` output. Your own contribution is judgement: which change is worth testing, and why.

## Steps

1. Run `git pull` so the Battle history GitHub Actions has committed is local. Done when the pull succeeds.
2. Run `python coach.py status` and read it: Battle history span, Main deck with levels and record, every Experiment with its Verdict, the Active war deck plan. Done when you can state each pending Experiment's progress.
3. Take the branch below that matches the request.
4. Answer with facts and hypotheses visibly separated, and state when the evidence is weak.

## Branches

**Improve the Main deck.** Report pending Experiments first: a new swap now shares battles with them. Propose one or two swaps, each with its reason and a success criterion of the form "at least X % wins over N battles". Check every proposed deck with `python coach.py check-deck CARD ...` and fix it until `problems` is empty.

**Start an Experiment** (the player accepts a swap). Append an event to `coaching-log.json`, then publish it: commit, `git pull --rebase` (Actions commits data every two hours), push.

```json
{"type": "experimentStarted", "id": "skeletons-for-bats", "at": "2026-10-24T18:00:00Z",
 "out": ["Bats"], "in": ["Skeletons"], "criterion": {"battles": 15, "winRate": 55}}
```

The swap applies to the Main deck from `at`. Experiments may overlap; `sharedWith` in the status shows how many battles they share, and you say so whenever you present their results.

**Follow up Experiments.** Report each Verdict with its record and `sharedWith`. A Verdict is advice only: after a failed Experiment, offer the reverse swap; the Main deck changes only when the player says so.

**Declare a Main deck or war plan** (the player says which deck they now play). Append `{"type": "mainDeckDeclared", "at": ..., "cards": [8 names]}` or `{"type": "warDeckPlanDeclared", "at": ..., "decks": [[8 names] x 4]}`, then publish it as above.

**Build a War deck plan.** Draw from the whole Collection (`python coach.py collection`), using observed war decks (`python coach.py decks --war`) as the baseline whose records are known. Write the four decks to a scratch JSON file and run `python coach.py check-war-plan FILE` until `problems` is empty. War battles are few, so judge war decks by coherence and card levels more than by records.

## Evidence

- 1-3 battles is an anecdote, 4-9 a direction, 10+ a stronger signal; none proves a deck optimal.
- One controlled change at a time per swap, so the result can be attributed.
- Card roles, synergies and counters are coaching hypotheses: name the cards they rest on.
- Balance changes and Meta decks come from an online lookup made in this session, cited with source and date. A Meta deck is a comparison point, never evidence about the player's results.
