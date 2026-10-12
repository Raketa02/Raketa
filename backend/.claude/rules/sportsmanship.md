---
paths:
  - "app/modules/sportsmanship/**"
---

# Sportsmanship

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **Sportsmanship stores, and it is the first aggregate here that is not event-sourced**
  ([ADR-0158](../../../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).
  `app/modules/sportsmanship/` is the eighth context, and it is the mirror image of the
  seventh: `player_score` keeps no record at all, and this one is the first part of the
  player record that keeps one — an aggregate, two tables and a migration. The exemption
  from *state changes emit domain events* is **argued rather than inherited**, on the terms
  that rule demands: a card is **born answered**, so a stream would be one event per card
  and a replay a `SELECT` with extra steps; **nothing subscribes**, so an outbox row would
  wait for nobody; and there is **no standing to derive**, which is the whole reason `games`
  replays. Five things are load-bearing and none is obvious from the code. **The collapse is
  the primary key** — `sportsmanship_rating` is keyed `(rater_id, subject_id)` and a later
  card *replaces* the earlier answer, because a read-time collapse is a rule the first
  reader to forget hands the farming problem back with a plausible number; the earlier
  answer is not archived, and the cost of that is named in the record. **Two tables, because
  the all-blank card has to close** — a blank is spelled by absence and nothing else, which
  is what makes *not rating leaves no record of the omission* structural, so the closure
  cannot live on the answers. **You rate everybody else on the court**, partner included, so
  there is no *side* in this context and rating yourself is refused by the same rule that
  refuses a stranger. **The matcher never reads it** — held by an `.importlinter` contract
  rather than by a test — and that is also why Player reliability stays the counted-only
  number, in points since #659. And **no individual
  rating reaches anybody in any shape**: the write answers `204`, the use case returns
  `None`, and `SportsmanshipLedger` has no method that answers *what did somebody say about
  me* — only *which of these cards are closed*, which is a fact about an act. **What this
  context publishes outward is a third port and never a method on that one**
  ([ADR-0158](../../../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)
  amendment, #382): `PublishedSportsmanshipQuery` answers the figure and how many different
  people it rests on — **one method, for every reader, the subject included**
  ([ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §5, #468). It used to answer a second question, a **coarse band** for the subject off a
  method that could not say the figure; ADR-0179 §5 retired the band with its three
  whole-star edges and accepted the subtraction ADR-0158 §2 refused, and its Consequences
  are where that cost is written — cite them, do not restate them. What blunts the cost is
  what this context keeps, and every fence has its test: the collapse costs that fold nothing, which is what
  the key bought — one row already is one person, so *the fifty most recent raters* is a
  `LIMIT` on a total order rather than a read-time collapse — nothing is trimmed at either
  end, there is no zero on the scale, no individual rating crosses on any route, and the
  matcher never reads it. The port and the record's demand are each pinned at one method,
  so a second resolution cannot return quietly. The word `stars` reaches no wire — the
  forbidden-fact sweep refuses that property name — so it crosses as `average` and
  `raters`. There are two reads here and neither touched the silence:
  `GET /api/v1/sportsmanship` lists the courts **waiting** for somebody's stars, as a game
  id and the people on it, and an open card is by definition one nobody has answered.
  It borrows one thing,
  `SettledCourts` over `games`' directory, whose adapter lives in **this** context the way
  `PlayerNames`' lives in `games`; *settled* there is narrowed to **played and over**,
  because a game called off or started short has nobody to rate, and a disputed game very
  much does — and so does a full court nobody recorded (`PLAYED_NO_SCORE`, #655), whose card
  runs from its **booked hour**, since nobody said when (*unscored* retired with the no-show
  report, #657; a game somebody **Didn't come** to is in neither set — no card). **The card's two
  clocks are domain and neither is configuration** (`domain/window.py`): it opens the day
  after the game — an answer given ten minutes after losing badly is not the answer wanted —
  and closes seven days later. Both edges run from `games`' `played_at`, which is *the moment
  somebody said we played* rather than the hour on court; it is never earlier than the game, so
  the day-after rule holds conservatively. Only a game nobody recorded, which has no such
  moment, runs from its booked hour (#655). Anchoring
  the close to a *settlement* instead would let an argument over the score restart somebody's
  week, and the price is named rather than discovered: a game two sides argued over settles up
  to a day into the week, so that one card is drawn for six days rather than seven. *Has it
  settled* stays the port's separate gate. **Nothing sweeps an expired card** — the expiry
  is a fold, because *not rating leaves no record of the omission* means there is no row for
  a job to correct — and the window governs the **prompt** and not the permission: a card
  that lapsed while somebody was typing is still answerable, which is the opposite of
  refusing one of two identical taps.
