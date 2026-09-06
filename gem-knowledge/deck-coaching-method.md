# Clash Royale Deck Coaching Method

Use this method when analyzing the player's exported decks.

## Evidence first

Start with the data quality: sample size, available deck categories, battle counts, result availability, and whether upgrade data exists. Separate observed facts from coaching hypotheses.

A practical confidence guide:

- 1-3 battles: anecdotal signal only.
- 4-9 battles: useful directional signal, still uncertain.
- 10 or more battles: stronger evidence, but not proof that a deck is optimal.

Win rate must always be read together with battle count, opponent context when available, and the cards' levels.

## Regular decks

Evaluate regular decks for repeatable ladder or normal-match use. Consider:

- Whether the deck has a clear win condition.
- Whether it has answers to common threats.
- Whether its average card levels make it practical for the player.
- Whether the observed results are strong enough to justify testing changes.

Prefer one controlled change at a time. Do not replace several cards and then attribute the result to one change.

## War decks

Evaluate war decks separately from regular decks. War decks may be constrained by collection rules, deck rotation, or the need to spread strong cards across multiple decks. A lower war win rate is not automatically evidence that the deck is bad.

When a `warDeckPlan` is supplied, treat it as a four-deck collection-building problem: a card used in one recommended war deck is unavailable to every other recommended war deck. Prefer the complete four-deck plan when the evidence supports it; otherwise report the number of feasible non-overlapping decks.

Consider:

- Whether the deck is coherent under war constraints.
- Whether cards are being reserved for other war decks.
- Whether the deck's role is clear.
- Whether the data identifies the mode reliably.

Do not merge a war deck's statistics with a regular deck using the same eight cards.

Use meta comparisons only when the supplied meta data identifies its source and date. A missing or stale meta snapshot is a data limitation, not permission to infer the current best decks.

## Recommendations

Prioritize recommendations in this order:

1. Fix a clear structural weakness using an already observed card when possible.
2. Recommend upgrades that are both relevant to the deck and realistic from the player's current levels.
3. Suggest a testable substitution with a clear success criterion.

Every recommendation should state what to change, why it might help, and what result would justify keeping it. If the export does not contain enough evidence, say that the correct action is to collect more battles.
