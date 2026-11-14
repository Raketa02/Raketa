# The player record — the spec set

**What the app draws when you tap a player's face.**

`SH.player`, the **player record** — a description of a *person*, answering *who is this* — opens
from a face on a Games card, a game's details, a booked game, Fill in, *Post a game* and a group's
Members, and about yourself from You (the header card and *How others see you*). It is built
(`backend/app/modules/player_record`, `frontend_player/src/features/player_record`). The set was
written when its one door was the balance-forecast card on the Play tab, where the tap opened
`SH.whyfit`; that card and that sheet went with Classic play (2026-10-06, #569), and what the set
says about them is its history.

| File | What it decides |
| --- | --- |
| [`the-player-record.md`](the-player-record.md) | The whole piece of work: the audit against what this platform holds, the five collisions with accepted records and what to do about each, the backend context and its citation-gated route, the wire, the client feature, the design-system amendments, and the build order |

## Read this first

**Four things the design asks for cannot be honestly drawn**, and each is an accepted refusal
rather than an unbuilt feature. They are argued in §2 and summarised in §2.6:

| Asked for | Why it does not ship |
| --- | --- |
| *active now* | ADR-0107 / ADR-0106 §5 — this product has no presence indicator |
| languages | no field exists anywhere, and the `Language` modifier was **struck** as a nationality proxy under ADR-0096 |
| *Confirms results* | **struck, and it stays struck** — ADR-0137: an unconfirmed result is a fact about a pair, and a strand is a verdict about a person. What ships in its place is **Answers about results** (ADR-0160), a different measurement over the same events: it counts answers, a counter scores exactly as an acceptance does, and only silence is a miss |
| *Sportsmanship, by opponents* | the strand stands down: no surface on this platform lets anybody rate anybody, and turning it on retunes every published score in the product |

> **2026-10-11, [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md):**
> *Answers about results* left the record with every other strand. Player reliability is points
> from 100, with a band, *New*, and four counts — *Shows up*, *Keeps plans*, *Being late* and
> *Results left in dispute*. Silence on a score costs nothing.

> **2026-11-14, [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
> §2 (Q131):** **a record opens for any reader**, except across a block made by either side, or when
> the subject has *Show me to new people* off and shares no group, no game and no friendship with the
> reader; both read the one *This record isn't available*. The disclosure strands this set describes
> are now the exceptions under that switch, not the only way in. **An admitted reader sees all of the
> subject's photos**, in their order, where the record showed only the first. It opens from any face in
> Home's rows, and the vibe sheet reads it.

**Everything else ships**, and one item the design asks for comes *back* from a withdrawal:
**opponent variety** returns as this context's own demand, which is what ADR-0098's amendment
said would happen when a consumer finally arrived.

## What sits above this

1. [`frontend_player/docs/design-system.md`](../../../frontend_player/docs/design-system.md) —
   **locked**. This set's five changes arrive as
   [Part 16](../../../frontend_player/docs/design-system.md#part-16--amendments-after-locking)
   rows, scheduled in §7. None of them is a new colour, size or radius.
2. [`../matchmaking/the-words.md`](../matchmaking/the-words.md) — the app's one copy deck. The
   strings this set adds are listed in [`the-player-record.md`](the-player-record.md) §9.
3. The ADRs. Six records, listed in §8 — two new, four amendments. **§10's first ticket is all
   of them**, because three of the five collisions are decisions, and building past a decision
   is how a refusal quietly becomes a feature.

## The sibling sets

- [`../matchmaking/`](../matchmaking/README.md) — the copy deck.
