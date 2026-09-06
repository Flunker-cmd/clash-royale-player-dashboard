# Player Analysis Export Schema

The live player data is published as `player-analysis.json`:

https://raw.githubusercontent.com/Flunker-cmd/clash-royale-player-dashboard/main/player-analysis.json

## Top-level fields

- `player`: player identity and trophy context.
- `sampleSize`: number of usable battles included in the analysis.
- `regularDecks`: observed decks from regular matches.
- `warDecks`: observed decks from war-related matches.
- `warDeckPlan`: up to four observed war decks selected without reusing a card between decks.
- `recentBattles`: recent usable battles with deck category and result.
- `upgradeCandidates`: cards with a known current level below their known maximum level.

## Deck fields

Each item in `regularDecks` or `warDecks` can contain:

- `label`: human-readable card list.
- `category`: `regular` or `war`.
- `cards`: cards observed in the deck.
- `battles`: number of observed battles using this card combination in this category.
- `wins`: observed wins.
- `winRate`: observed win percentage, not a guaranteed prediction.
- `metaScore`: optional overlap score against the supplied reviewed meta snapshot; absent or zero means no usable meta match.

`warDeckPlan` uses the same deck fields. It is a proposed collection allocation, not proof that the decks are optimal. If it contains fewer than four decks, the available evidence did not support four non-overlapping candidates.

## Battle fields

Recent battle records may include:

- `deck`: cards used in the battle.
- `deckLabel`: human-readable card list.
- `category`: `regular` or `war`.
- `won`: `true`, `false`, or `null` when the result cannot be determined.
- `type`: source game mode or battle type when available.
- `date`: battle timestamp when available.

## Interpretation limits

This is an observed battle-log sample, not a complete account history. Missing fields are unknown, not zero. A deck with few battles has weak evidence even if its win rate is high. Do not infer cards, levels, or battle results that are absent from the file.
