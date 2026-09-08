# The player record — the spec set

**What the app draws when you tap a person on the balance-forecast card.**

Today that gesture opens `SH.whyfit` — an explanation of a *pairing*, answering *why 77*. This
set replaces it with `SH.player`, the **player record** — a description of a *person*,
answering *who is this*. Both sheets survive; §6.3 gives each its own gesture.

| File | What it decides |
| --- | --- |
| [`the-player-record.md`](the-player-record.md) | The whole piece of work: the audit against what this platform holds, the five collisions with accepted records and what to do about each, the backend context and its citation-gated route, the wire, the client feature, the design-system amendments, and the build order |

## Read this first

**Four things the design asks for cannot be honestly drawn**, and each is an accepted refusal
rather than an unbuilt feature. They are argued in §2 and summarised in §2.6:

| Asked for | Why it does not ship |
| --- | --- |
| *active now* | ADR-0107 / ADR-0106 §5 — this product has no presence indicator, and Liveness crosses only as a reason code |
| languages | no field exists anywhere, and the `Language` modifier was **struck** as a nationality proxy under ADR-0096 |
| *Confirms results* | **struck, and it stays struck** — ADR-0137: an unconfirmed result is a fact about a pair, and a strand is a verdict about a person. What ships in its place is **Answers about results** (ADR-0156), a different measurement over the same events: it counts answers, a counter scores exactly as an acceptance does, and only silence is a miss |
| *Sportsmanship, by opponents* | the strand stands down: no surface on this platform lets anybody rate anybody, and turning it on retunes every published score in the product |

**Everything else ships**, and one item the design asks for comes *back* from a withdrawal:
**opponent variety** returns as this context's own demand, which is what ADR-0098's amendment
said would happen when a consumer finally arrived.

## What sits above this

1. [`frontend_player/docs/design-system.md`](../../../frontend_player/docs/design-system.md) —
   **locked**. This set's five changes arrive as
   [Part 16](../../../frontend_player/docs/design-system.md#part-16--amendments-after-locking)
   rows, scheduled in §7. None of them is a new colour, size or radius.
2. [`../matchmaking/the-words.md`](../matchmaking/the-words.md) — the app's one copy deck.
   Every string this set adds lands there as **§25**, and three of its existing sections are
   amended (§20.4.1, §20.6, §20.8).
3. The ADRs. Six records, listed in §8 — two new, four amendments. **§10's first ticket is all
   of them**, because three of the five collisions are decisions, and building past a decision
   is how a refusal quietly becomes a feature.

## The sibling sets

- [`../matchmaking/`](../matchmaking/README.md) — the Play tab, whose forecast card is this
  sheet's first entry point.
- [`../the-loop/`](../the-loop/README.md) — the chat header and the game screen, which are the
  route's next two citations. The route is built to accept them; this set draws neither.
