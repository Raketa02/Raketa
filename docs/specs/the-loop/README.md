# The loop — the spec set

**What the app draws between a challenge being answered and a result moving a level.**

Produced by the map
[Closing the loop — a challenge answered, a game talked about, a result that moves a level](https://github.com/Raketa02/Raketa/issues/321),
whose destination is the loop this set specifies: *a player sends a challenge, another player sees
it and answers it, the accepted line-up becomes a game, the two of them talk about it and agree a
day, an hour and a club, and the result they agree moves both levels* — every step through the app
rather than through a seed script.

These are **operative documents, not inputs.** Everything in them is decided, and every decision
cites the record that made it. The input documents this map argued against are
[`../player-app/`](../player-app/README.md) and the prototype in
[`../matchmaking/`](../matchmaking/README.md); nothing is decided because it appears in either.

| File | What it decides |
| --- | --- |
| [`the-loop-screens.md`](the-loop-screens.md) | The routes, and what each of the five surfaces draws and does — the Chats tab, the challenge screen, the conversation with its plan card, Now, and the one state-detail surface both tabs open |
| [`the-loop-components.md`](the-loop-components.md) | Where one component stops and the next begins, across two new client features and one that grows a screen |

**The sentences are not here.** Every string and every accessible name this map adds lives in
[`../matchmaking/the-words.md`](../matchmaking/the-words.md), §22–§24, beside the challenge copy
§13 and §14 have owned since [#234](https://github.com/Raketa02/Raketa/issues/234). That file is
the app's one copy deck and it did not move: a dozen documents and as many docstrings cite it by
relative path, and its home is a fact about its history rather than about its scope.

**The Play tab's counterparts are [`../matchmaking/the-play-screens.md`](../matchmaking/the-play-screens.md)
and [`../matchmaking/the-play-components.md`](../matchmaking/the-play-components.md)**, produced by
the previous map. This set is their sibling in shape and cites them where a rule is shared; where
this map amended one of them, the amendment is in that file and says so.

## What sits above these

Both documents are **subordinate** to the client's own two, and to the ADRs:

1. [`frontend_player/docs/design-system.md`](../../../frontend_player/docs/design-system.md) —
   **locked**. A number in it never moves; changes arrive as
   [Part 16](../../../frontend_player/docs/design-system.md#part-16--amendments-after-locking)
   amendments, and this map's are scheduled by
   [#338](https://github.com/Raketa02/Raketa/issues/338).
2. [`frontend_player/docs/architecture.md`](../../../frontend_player/docs/architecture.md) — which
   gains its first live-surface section, carried by the first client build ticket.
3. The ten ADRs this map wrote, [ADR-0142](../../adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
   through [ADR-0151](../../adr/0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md),
   [ADR-0153](../../adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md),
   which was filed outside the map and moved the conversation's lifetime, and the root
   [`CONTEXT.md`](../../../CONTEXT.md)'s Conversation and Plan sections, which name every domain
   term these documents use.

Where any of them disagrees with what is here, **they win** — and the disagreement is a defect in
these files rather than a decision.
