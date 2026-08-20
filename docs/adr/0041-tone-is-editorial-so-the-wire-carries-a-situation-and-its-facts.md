# ADR-0041 — Tone is editorial, so the wire carries a situation and its facts

- **Status:** Accepted
- **Date:** 2026-08-20

## Context

[ADR-0040](0040-one-ladder-resolves-a-situation.md) settles which vocabulary the ladder produces.
This one settles what of it crosses the wire.

`5-now_screen_architecture_review.md` A5 proposes `{key, tone, facts}` and puts copy on the
client, resting on [ADR-0022](0022-kernel-negative-space-and-constant-homes.md) and the glossary's
own line: *"**Copy is not formatting**: the sentence behind an unavailability code is each app's
own."* The open question was which of the vocabularies `key` is, and whether `tone` earns a field.

**The 17 tags were never a candidate, and the framing hid why.** They are display strings —
`Court held`, `Rescue active`, `On standby`, `Confirm the result` — in English, on a Polish
product. A tag *is* copy. Putting it on the wire reverses the decision that put copy on the
client, in the same payload that honours it. The state-table research confirms it was never
load-bearing either: the tag does not determine the tone (`Forming` splits `idle`/`watch`,
`Court held` splits `watch`/`good`) and does not determine `be` (`Court released` maps to two
values, `Reserved` to four).

**Tone is a different question, because it is not a string.** But `situation → tone` is a total
function over 33 rows, and the client already holds a 33-row table for copy, so tone can be a
column of it. Two facts push the same way:

- **[ADR-0037](0037-the-fit-badge-shouts-once-and-only-about-a-seat.md)'s precedent cuts against
  shipping it.** The `emphatic` flag ships from the server precisely because emphasis depends on
  *the other cards on the screen* — a fact the client cannot have. Tone depends only on the
  situation, and the client is holding the situation.
- **The server cannot ship the colour anyway.** [The native-kit
  delta](../specs/now/deltas/native-kit.md) made tone surface-aware: `ST_TONE.idle` is
  `rgba(255,255,255,.45)` on the dark card and `muted` on the light one, because one hex cannot
  promise legibility on two surfaces. What a `tone` field would carry is a semantic token that
  the client then resolves against a surface — a lookup handed across a network to be looked up
  again.

There is also a defect that only makes sense once tone's home is decided. `deltas/native-kit.md`
records that [ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md) *"already moves
`inventoryLost`'s tone to `ended`"*, resolving the long-standing `ST_TONE['bad'] is undefined`
gap that four separate documents flag. **ADR-0031 says nothing about tone, and neither does any
other ADR.** The retone was agreed in conversation and never landed anywhere. It is a dangling
citation, and where it should land depends on who owns tone.

## Decision

**We will carry `{situation, facts}` on the wire. Neither the tag nor the tone crosses it.**

**The tag is copy and belongs to each client, in its own voice.** The 33-row content contract
becomes a client copy table, Polish first, and the two clients are free to word the same
situation differently — which is what
[ADR-0005](0005-three-app-monorepo-ownership-boundaries.md) already assumes about two apps with
different jobs.

**Tone is not a fact about the match; it is an editorial judgement about how loudly to say it.**
That is the same class as copy, and it goes to the same place. We extend the glossary's line
accordingly: the sentence behind a code is each app's own, **and so is the alarm attached to
it.** A per-client tone is the point rather than the price — a console watching forty matches
wants different alarm from a player watching one, and a shared tone would force the quieter of
the two on both.

**Tone resolves to a colour on the client, against the surface it lands on**, per the native-kit
delta. There is no server-side notion of the colour of a situation.

**The `inventoryLost` retone stops being an ADR's business.** With tone client-owned, the defect
dissolves into a row of a client table: the player app maps `inventoryLost` to `ended` like the
other three cancellations. `deltas/native-kit.md`'s citation of ADR-0031 is corrected by [the
state-vocabulary delta](../specs/now/deltas/state-vocabulary.md) rather than by editing that
delta's reasoning, which is sound.

**A5 is amended by spec delta, never by editing the document.**
[ADR-0036](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md) governs: `5-now_screen_architecture_review.md`
keeps its bytes and its 486-citation neighbourhood, and the delta records that `{key, tone, facts}`
became `{situation, facts}`. A5 is a review finding rather than a UI authority, so nothing here
touches a document that is final on the screen.

**What `facts` contains is not decided here.** It belongs to the `GET /now` wire contract, along
with the field names on the card.

## Consequences

**Easier**

- Locale stops being a backend concern and a wording change stops being a backend release, which
  is A5's whole argument, now applying to one more thing than A5 claimed.
- Each client says the same fact in the voice its audience needs, without negotiating a shared
  register with the other.
- The `ST_TONE['bad']` class of defect cannot recur on the wire: an unmapped tone is a missing
  row in one client's table and a compile error there, not a colourless dot shipped to
  everybody.
- The payload gets smaller, and the one field it drops is the one that would have been looked up
  twice.

**Harder**

- **Two clients can disagree about how alarming a situation is, and nothing catches it.** This is
  accepted deliberately, and it is real: the same match may read calm on the console and urgent
  on the phone, with no test that fails.
- **Retuning urgency across the product needs a release of each client**, and the phone's is an
  app-store release with the update lag [ADR-0008](0008-player-mobile-securestore-direct-api.md)
  already names. A server-side tone field would have been one deploy.
- **The client table is bigger than A5 estimated** — 33 rows of copy *and* tag *and* tone, in
  each client. That duplication is ADR-0005's accepted cost showing up in a concrete place, and
  this is the largest single instance of it so far.
- **No single source for tone exists in the repo any more.** Two tables have to be kept in step
  by intent rather than by mechanism, and the first person to notice they have drifted will be a
  user.
