# ADR-0025 — A counted match's pairing is elected before commitment and fixed after

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

In a four-player match the pairing decides the evening. Four players at 2,71 / 2,80 / 2,64 /
2,92 split one way give a gap of 0,0155 between team strengths and split another give 0,1825 —
an order of magnitude apart, from the same four people. So the platform does not merely filter
by level; it chooses the split and tells the player what that split will feel like.

Everything downstream inherits that choice. The balance percentage, the split bar, the two team
strengths and **At Stake** — the rating movement quoted to a player *before* they join — are all
computed from the strengths of the two teams the engine picked. The prototype's own review of
this notes the hole plainly: *"`atStake` uses the forecast's team strengths, so it inherits the
forecast's assumption that the best pairing will be used. If the club or players rearrange, the
stakes change."*

That is the problem. If four people can walk onto the court and pair up differently, then a
number the platform quoted as a commitment was a guess about human behaviour, and a rating moved
on a result produced by teams the player never agreed to. *A level is proved, never declared* —
but proving it against an arbitrary rearrangement proves something else.

The clock and commitment rules already give the moment this can hang off: a match **commits** at
the earlier of the club's cancellation window and T−12h, and only when it is full. Before
commitment, leaving is free and nothing is settled. After it, refunds become outcome-based and
the match is a real thing with a real court. There is already a line in the timeline where
"still being arranged" becomes "this is happening".

The alternatives considered:

- **Advisory everywhere**, as the prototype has it. Cheapest, and honest about the platform's
  actual power over four adults on a court. But it makes At Stake unquotable: either the
  platform stops showing what a match is worth, or it shows a number it cannot stand behind.
  The second is worse than the first, and the first removes the feature that makes joining a
  counted match a fair deal.
- **Binding everywhere.** Simple rule, one code path. But it makes the platform an officious
  presence in a friendly game between people who booked a court to mess about, and it earns
  nothing there — a friendly moves no rating, so nothing is at stake to protect.
- **Binding for counted matches, advisory for friendlies.** Two paths, and the split falls
  exactly where the consequence does.
- **Showing the rejected splits read-only**, which the prototype does for the line-up screen so
  that *"the second and third options are the evidence that the chosen one is best."* Under a
  binding pairing this is the worst available option: it manufactures the desire to play the
  other way and then refuses it.

## Decision

We will make the pairing **part of a counted match's record**, elected before commitment and
fixed after; a friendly's pairing is advisory and may be rearranged freely.

- **The engine proposes; the roster may elect.** All three splits are shown with their
  predicted balance. The default is the engine's choice. Any member of the roster may elect a
  different split, and the elected split replaces the default for everyone.
- **Election closes at commitment.** Up to the commitment marker the pairing is changeable. At
  commitment it is fixed, and At Stake's quote is a quote against *that* pairing. Nothing
  reopens it — not a late join, not a replacement — because a match that fills after the
  deadline commits on the spot, and a pairing that could change after commitment would reopen
  a promise that has already been relied on.
- **A friendly is advisory throughout.** The engine still proposes a split, still shows the
  alternatives, and nothing is recorded or fixed. No rating moves, so there is nothing to
  protect.
- **A replacement takes the seat, not the side.** When a player leaves a committed counted
  match and is replaced, the replacement inherits the departing player's position in the fixed
  pairing. The teams do not re-optimise, because re-optimising would silently revise the terms
  every other player already accepted. The forecast is recomputed and shown; the pairing is not.
- **An election is recorded as evidence.** Which split the engine chose and which the roster
  elected are both kept. A roster that consistently overrides in one direction is the strongest
  available falsification of the weaker-partner weighting in `teamStrength`, and it is a signal
  no other measurement produces.

## Consequences

**Easier**

- At Stake becomes a promise rather than an estimate: the quote and the eventual rating update
  are computed against the same two teams, and the player knew the deal before accepting it.
- The balance forecast on a committed match describes the match that will actually be played,
  which is what makes the number worth showing at all.
- The weaker-partner weighting — the single most opinionated constant in the matchmaking system
  — acquires a falsifying measurement it otherwise had no way to get.

**Harder**

- **Two paths through the line-up screen**, and the difference between them is invisible until
  a player looks for it. A counted match and a friendly will look nearly identical and behave
  differently, which is a real comprehension cost that copy has to carry.
- **The platform cannot actually enforce this.** Four people on a court can pair up however they
  like, and Raketa will never know. What is binding is the *record* and therefore the rating
  consequence, not the physical arrangement. This is a genuine weakness and it is accepted
  knowingly: the alternative is quoting stakes against nothing at all.
- **Election is a new concurrent write** on a match several people are looking at simultaneously,
  needing the same optimistic-concurrency posture as joining a seat.
- The replacement rule will occasionally produce a visibly worse pairing than a re-optimisation
  would, and a player will notice. That is the price of not revising accepted terms, and the
  forecast is recomputed so at least nobody is misled about it.

**Neutral**

- The engine is unaffected. It enumerates all three splits and ranks them, exactly as before;
  which one is *binding* is a fact the Matches context records, not something the pairing engine
  knows. Engines own no state and decide nothing about what their results mean
  ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md)).
- Singles has no pairing and is untouched by any of this.
