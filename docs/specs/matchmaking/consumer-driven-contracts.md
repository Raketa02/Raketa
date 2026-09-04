# What the matcher demands of `player_score`, `matches`, `cases` — and of `rating`

The matcher declares the facts it requires. Whoever builds those contexts satisfies the
contract however they like — **this document has no opinion on their aggregates, events,
storage or state machines**, and a section here that starts describing how `matches` works
internally has left its lane.

Decided by [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md), resolving
[What the matcher demands of player_score, matches and cases](https://github.com/Raketa02/Raketa/issues/163)
on the map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**Why this is written down at all.** The engine reads the Player Score's strands *separately*
(§9.3.4), because they are weighed oppositely in the two modes — *keeps plans* is close to
worthless for a friendly beside sportsmanship and worth two and a half times it for a counted
game. The Player Score is one number in the UI. Left unwritten, the obvious thing to ship is
that number — and the strand-decomposition argument dies without anybody noticing until the
term is wired up. **An unwritten demand is satisfiable by accident.**

> **Amended twice, and the provider has landed.**
> [ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md) **struck *confirms
> results*** — the pair this paragraph originally used as its example — because an unconfirmed
> result is a fact about a pair and a strand is a verdict about a person.
> [ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)
> then built `player_score` over **two** of the five survivors, so the demand below is no longer
> a promise: it is executed. Where this document says *`player_score` does not exist*, read
> ADR-0140.

---

## The five ports

One provider signs one contract. The split is by who supplies the fact, never by how fresh it
has to be.

**One of the five now has two, and the bend is recorded rather than absorbed**
([#253](https://github.com/Raketa02/Raketa/issues/253), ADR-0098's amendment banner).
`challenges` ships and signs `MatchHistoryQuery` beside the still-unwritten `matches`, because
the seam runs *through* `pairwise_counterparts`: `ACCEPTED` and `DECLINED` are challenge facts
and `PLAYED` is `matches`'. Splitting the port to match would cut the 500-counterpart bound in
half, and two bounded reads merged by a caller is not a bounded read.

| Port | Provider | Supplies |
| --- | --- | --- |
| `PlayerScoreQuery` | `player_score` | The five strands with their evidence, and the published score |
| `MatchHistoryQuery` | `challenges` **and** `matches` | The searcher's pairwise history, the per-player open-challenge count, and the origin key. `challenges` answers all of it except `PLAYED`, `PLANNED_NEVER_PLAYED` and the late-change threshold |
| `AccountHoldQuery` | `cases` | One live boolean per player. Already standing from [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) |
| `AtStakeQuery` | `rating` | What a counted win and a counted loss against one opponent would do to the searcher's Level |
| `AccountStatusQuery` | `users` | The set of accounts that may not be shown. Gate 8, from [ADR-0124](../../adr/0124-the-matcher-gates-account-state-never-age.md) |

**The last two are different, and the difference is stated rather than left to be noticed.**
`cases` **does not exist**; `player_score`, `challenges` and `games` do — the first over the
other two (ADR-0140) — and between them the latter
answer the whole of `MatchHistoryQuery` ([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md)).
`rating` exists too — at `backend/app/modules/rating/`, with its engines at
`app/engines/racketskill/` — and what was missing there was not a context but a **rule**. That
rule has since been written ([ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
so `AtStakeQuery` has a real adapter and the last of the three null objects it was wired to is
gone. The port is here rather than in a second document because the value of this file is being
*the one place* a build agent finds every demand the matcher makes outward. Splitting it by
does-the-provider-exist would make a reader check two places to be sure they had them all.

`users` exists outright, with **nothing missing at all** — `is_active` ships, `UserDisabled`
ships, and `auth` already refuses a disabled account four ways. `AccountStatusQuery` is therefore
the one port with a **real adapter on day one**, and the contract suite runs against it rather
than against a fake standing in for an unwritten context. It is here for the same reason
`AtStakeQuery` is: this file is *the one place* a build agent finds every demand the matcher makes
outward, and splitting it by does-the-provider-exist would make a reader check two places to be
sure they had them all.

Delivery of the indexed half is the backend's existing transactional outbox
([ADR-0003](../../adr/0003-transactional-outbox-for-event-delivery.md)), as §7.3 describes.
**The transport is settled elsewhere; this document contracts the facts.**

---

## `PlayerScoreQuery`

### The five strands, and what each one counts

> **Two of them are live** (ADR-0140): *shows up*, out of plans that settled either way, and
> *answers challenges*, out of invitations whose day is over. The other three have no provider
> and are **absent from a reading** rather than published at nought. *Confirms results* is not
> in the table below at all: it was **withdrawn**, and a withdrawn demand leaves no row.

Every strand crosses as **the published value, its numerator and denominator, and the moment of
the most recent observation**. The matcher reads the value the player is shown and never
re-derives it — a card explaining a match with a number the player's own profile disagrees with
is worse than a card that says nothing.

| Strand | Denominator — the opportunity | Numerator — the good outcome |
| --- | --- | --- |
| **Shows up** | Plans that settled: a game somebody said had happened, or a **ghost** whose entry window closed on silence | The ones that were played. **A ghost is charged to every seat**, because nobody proposed and nobody countered |
| **Answers challenges** | **Invitations** whose day is over — a seat somebody was actually *asked* to take, which is a seat with a deadline | Answered inside the day. **A decline counts**: what this prices is silence, not judgement |
| **Keeps plans** | Plans agreed | Plans that reached their scheduled moment without a **late** change by this player |
| **Settles up** | Court shares that fell due | Shares settled **without a case being opened** |
| **Sportsmanship** | Ratings received | *(a mean of 1–5, not a ratio — crosses as mean plus rating count)* |

**Two of these are corrections, not transcriptions.**

- ***Settles up* is the historical record, never the live case.** The prototype collapses the
  strand to `0.15` while an unsettled share is open (`social-prototype-v1.html:3376`). That
  conflates the strand with the gate. The open case is the **Hold** and does its work there;
  the strand counts what happened. The matcher never reads `cases` to score.
- ***Keeps plans* needs one threshold, published.** *"One late change in six months"* is
  hardcoded prose in the prototype (`:3379`) with no denominator behind it. The contract demands
  `matches` publish **the single threshold that makes *late* mean one thing**. A per-case
  judgement is not a fact and cannot be contracted.

Two more are worth stating because they will surprise a reader:

- ***Settles up* depends on court money, which this map rules out of scope.** It stands down,
  and so do *keeps plans* and *sportsmanship* — two of the five are live (ADR-0140). Expected,
  not a defect.
- **The player-facing weights are not the matcher's weights.** The Player Score screen blends
  the strands at **35/20/12/10/8** (`:3374-3380`, less the struck strand's 15); the ruleset
  weighs them per mode at **33/33, 29/23, 18/15, 13/12, 7/17**. Both are right. This is
  precisely why the matcher must read strands and not the blend. **The two vectors total
  differently on purpose**: a ruleset weight map is validated as summing to a hundred so each
  number reads as a share of a term's budget, where the published blend's basis is the strands a
  player actually has.

### Opponent variety — **withdrawn**

Demanded as a **seventh published statistic that is explicitly not a strand**, on behalf of two
consumers: the familiarity sign flip (§9.4) and the welcoming-record modifier.
[#164](https://github.com/Raketa02/Raketa/issues/164) struck the first — the sign reads declared
tags only. [#175](https://github.com/Raketa02/Raketa/issues/175) struck the second — variety says
you get around, not that you are willing to play somebody who might be bad, and the welcoming
record reduces to its one input the tag terms do not already pay for.

**A consumer-driven contract with no consumer is withdrawn, not carried.** The whole discipline is
that a demand is executable against a provider; a demand nobody reads is a demand nobody notices
going wrong, and a contract suite is exactly where an unread row goes quietly stale. ADR-0098 is
amended to say so. If a later term wants variety, it returns as **that term's** demand and signs
for it — which also means it arrives with a consumer who can say what shape it needs.

### The published score, demanded once and read by one consumer

Beside the strands, and **not instead of them**: the **published Player Score** the player sees
on their own profile, the 35/20/12/10/8 blend renormalised over whatever is there, out of a
hundred.

It has exactly one consumer **in the matcher** — the **reliability floor**, whose
`published_score_bar` is ruleset data (`app/engines/matchfit/ruleset.py`, `ReliabilityRules`).
It is **the one deliberate place the matcher reads the blend instead of the strands**, and it is
written down here so it does not later read as an oversight or as this contract being quietly
relaxed: a penalty justified by a figure that exists nowhere a human can look is unexplainable,
and a player working their visible score back up must be able to watch the penalty lift.

**The player card is a second reader, and it is not a second computation** (ADR-0140). It prints
the same figure, reached through a port at assembly time — never off the candidate index, which
[ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md) reserves
for what a player changes about themselves. The weights themselves belong to `player_score` and
not to a ruleset: a weight release must not change what somebody's own profile says about them.

**It may never be weighed as a term, and it may never stand in for the strands.** A reading with
no strand in it is not a reading — which is what stops *shipped as one blended number* passing
through this door instead of the front one.

### The absence rule, and the two standing-down powers

**No record is not a bad record.** A player without a score is not `0.5` and not `0`: the term
returns `NoEvidence`, is dropped from the sum, and the remaining weights renormalise (§10).
This is the same principle the rating engine already applies to skill.

The matcher's *entire* policy over these facts is the power to stand a strand down. It applies
no decay of its own — the score is a memory and fades with new evidence on the provider's side;
a second decay here would double-count.

| Constant | Start | What it does | Falsified by |
| --- | --- | ---: | --- |
| `RELIABILITY_MIN_OBSERVATIONS` | 3 | A strand below it is `NoEvidence` **on its own**; the surviving strands renormalise *inside* the reliability term | Ghost rate and answer rate regressed on strand value, split by observation count. If one-observation strands predict as well as five, the bar is too high |
| `RELIABILITY_HORIZON_DAYS` | 365 | If the most recent observation **across all strands** is older, the whole term stands down | Return rate of matches made on evidence older than a year |

Both are **ruleset configuration** under [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)'s
frozen ruleset version, never code, never environment-selected. Both are inventions of this
map — **§24's constants table has no reliability freshness constant at all** — which is why
each owes a falsifier.

The horizon is one number over the whole score rather than six, because the strands share one
cause: this player stopped playing. It is deliberately generous. It is a refusal to rank on a
fossil, not a decay.

---

## `MatchHistoryQuery`

### The pairwise read: it travels with the search

Every `matches` fact the matcher wants except the open-challenge count is a fact about a
**pair**. The candidate index is one row per `(player, sport)` (§7.2) and there is nowhere in
it to put a pair.

[ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) already
answered this for blocks, and the answer transfers: **the searcher's own set travels in the
`SearchContext`; the index holds nothing.** One bounded read, keyed on the searcher, at search
time.

| Demanded | Bound | Why |
| --- | --- | --- |
| The searcher's pairwise counterparts, each outcome distinguishable — **accepted**, **declined**, **played**, **planned-never-played** — each **tallied**: how many times, and when it last happened | The most recent **500** **counterparts**, not events | A searcher has played tens of people. An unbounded read is how one long-standing player's search becomes slow for everyone |
| Every challenge currently open between the searcher and anyone | **Unbounded** | It is a §7.5 never-stale fact and it is small by construction |
| Open challenge count, **per player** | The index row | Not pairwise. Advisory, for ranking on load (§7.2, §14.4) — never the last word |
| **The late-change threshold** — how close to the scheduled moment a change has to be to count as *late* | One published number for the platform | Demanded here rather than of `player_score` because *late* is a fact about a **plan**, and the context that owns plans owns what the word means. It takes no pair, no plan and no case, which is what makes a per-case judgement unexpressible |

**A count and not a latest outcome, because familiarity needs both halves.** `strength` is
`0.5 ^ (days_since_last / FAMILIARITY_HALF_LIFE_DAYS) × (1 − FAMILIARITY_DEPTH_PHI ⁿ)`, where
`n` is **games played together** ([`ranking-weights.md`](ranking-weights.md) §8). One outcome and
one moment per counterpart feeds the decay and never the depth. Tallying also keeps an accept
visible under a later decline, which a single latest outcome erases — and the previous-decline
signal and familiarity would then both be reading the same lost history.

**A ghost game is two facts, and they go different places.** As a per-player reliability signal
it is `player_score`'s input and the matcher never sees it separately. As a **pairwise** outcome
it is here, distinguishable from a game that was played, because familiarity must be able to
tell them apart.

### What fails how

| Read | On failure | Why |
| --- | --- | --- |
| Block set (`BlockQuery`, ADR-0095) | **The search refuses** | A gate that cannot be evaluated excludes |
| Hold flag (`AccountHoldQuery`, ADR-0095) | **The search refuses** | Same |
| Disabled set (`AccountStatusQuery`, ADR-0124) | **The search refuses** | Same. Read **once per search as a set**, beside the block set — never a per-row query |
| Pairwise history | **Fails soft** — familiarity and the previous-decline signal stand down, the search proceeds | Losing a game because we could not remember who you played in March is a worse outcome than a slightly duller list |
| Open challenge between the pair | **Fails soft** | §7.5's *the matcher proposes, the backend disposes* re-verifies on the shortlist. It is embarrassment with a backstop, not a safety failure |
| The strands (`PlayerScoreQuery`) | **Fails soft** — the reliability term stands down | Which is what it does for anybody with no record anyway, so a failure costs a term and never the search |
| At stake (`AtStakeQuery`) | **Fails soft** — the block is not drawn | Derived rather than quoted: it is what the card already does for a pair with no Level between them |

These are separate reads carried in one context object. Bundling them into one read would make
the strictest fact's failure mode everybody's.

### The origin key — the join that cannot be reconstructed

**Every challenge names its origin**, as a required, non-nullable value: either the
`(search_id, position)` it was sent from, or an explicit case saying it came from somewhere
else.

Never an optional field. The first caller who finds it inconvenient omits it, the loss is
silent, and §19.2 is right that there is no backfill — a search not joined to its outcome is
evidence that no longer exists. What is recorded on the *search* side belongs to
[The search-side telemetry](https://github.com/Raketa02/Raketa/issues/169); this contract owns
only the demand that the other end carry the key.

---

## `AccountHoldQuery`

**One live boolean per player, and nothing else.** Settled by
[ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md): live,
both directions — a held *searcher* is refused at the entry point, not merely hidden from
others — and fail-closed. Its only adapter today is `NoHoldsExist`.

**`AccountHoldQuery` is not `AccountStatusQuery`, and they are not merged.** *Held* and
*disabled* are different truths, from different contexts, with different lifecycles and different
remedies. One boolean with two meanings is a gate that fails for unrelated reasons under one
reason code (ADR-0124).

**The matcher never reads `cases` to score.** A held player is both excluded by the gate and
carrying a low *settles up*. **That double reach is intended.** It is written down here so
nobody later tidies away the apparent duplication by removing one of them: the gate is absolute
and the strand is weighed, and they answer different questions about the same event.

---

## `AccountStatusQuery`

**The set of account ids that may not be shown**, resolved live from `users` **once per search**
and applied at generation as a set membership — the block set's shape, and never a query per
candidate row.

| | |
| --- | --- |
| **Direction** | **Candidate-side only** |
| **On failure** | **Closed** — the search refuses |
| **Freshness** | Live. **Never an index column** |
| **Told** | **Nobody** — invisible to the searcher, like a block |

**Candidate-side only is a fact, not a leniency.** ADR-0095 makes the Hold bidirectional because
a *held* player can still log in and run a search. A **disabled** one cannot get past
`get_current_user`, so `auth` closes the searcher side before the matcher is reached; a second
check there would assert something the request could not have carried.

**Never an index column.** A stale *active* flag means a disabled account is shown to a stranger,
which makes staleness cost **safety** — the one thing
[ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md) exists
to prevent. Account state is also not a fact a player changes *about themselves*: an
administrator may change it.

**What the contract does not cover.** Account **erasure** — nothing in this repository deletes an
account, and erasure is a platform-wide obligation rather than a matchmaking demand. If it
arrives, it arrives as a change to what this port means by *may not be shown*, and the gate's
name does not change.

---

## `AtStakeQuery`

**A pair of signed deltas for one `(searcher, opponent, sport)`**, and the game must be one that
would be counted. It is what the competitive candidate card shows up front — `+0,07` against
`−0,05` — computed from both ratings and the searcher's own confidence. Added by
[The six places the prototype and the design document disagree](https://github.com/Raketa02/Raketa/issues/164),
which kept a prototype behaviour the design document never mentions.

**Nobody but `rating` may compute it, and that is why there is a port here at all.** The
number needs the result-update rule — a K-factor over the searcher's confidence, and an
expected score over the two μ values. Three parties could plausibly do the arithmetic and none
of them may:

- **The client** cannot, under
  [ADR-0021](../../adr/0021-kernel-in-backend-clients-derive-by-comparison.md). This is a rule
  with constants, not a countdown toward a supplied instant.
- **The matcher** cannot, under this document's own standing rule: it reads what the player is
  shown and never re-derives it. A K-factor is the rating engine's opinion about the rating
  engine, and a second implementation of it is exactly the failure ADR-0021 exists to prevent.
- **This document** cannot specify the maths, for the same reason it has no opinion on how
  `games` works internally. It demands the fact and stops — and ADR-0139 is where the maths was
  decided, in the context that owns it.

**For-fun games are never counted** (§23 Q11), so the field is competitive-only — which the
prototype already enforces at `:2460`. In for-fun it is not absent-because-unavailable; it is
**meaningless**, and the card renders nothing.

**The rule exists now** ([ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
and the adapter is `RatingResultUpdateRule` — which calls the *same function* that moves a Level
when the game is played, so a card promising `+0,07` and an update delivering something else is
not a state two callers of one function can reach. `NoResultUpdateRuleExists` is deleted, on the
rule a null object is written under: the fact its name asserted stopped being true.

**The field is still absent rather than zero** whenever either party holds no rating in that
sport, and that absence is measured: there is nothing to price the pairing against. A zero would
be invented — it would claim a counted game against this opponent moves the searcher's Level by
nothing, which is false about every opponent. The card simply omits the block.

**It is priced head-to-head, and in a four that is a decision rather than an oversight.** The
figure carries the sport's own weighting — a doubles result is half the evidence about any one
of the four — but the *pairing* it prices is you against the person on the card, because the
other two seats are unknown when the card is drawn and averaging against an imaginary partner
would invent the one thing the read has no basis for.

---

## What happens while none of these contexts exist

The rule, and it will be faced again by every context that lands later:

> **A gate may be honestly empty; a term may never be honestly neutral.**

The test is whether a zero would be **measured** or **invented**.

| Fact | Today | Which, and why |
| --- | --- | --- |
| Hold flag | **True-over-empty** | Nobody can be held because nothing can hold anybody. A real, measured absence |
| Open challenge count | **True-over-empty**, and **live** since [#253](https://github.com/Raketa02/Raketa/issues/253) | Seats awaiting that player's answer, across every sport, counted from the seats and the clock. Everybody asked gets a count, and a zero is measured — the shape did not change when the provider arrived, which is the property this rule was chosen for |
| Pending challenge between a pair | **True-over-empty**, and **live** | Every counterpart in every challenge that has not ended. Still **soft**, and still out of the read-back: this is embarrassment, and the send's re-check is the backstop |
| The strands | **Two live, three `NoEvidence`** since ADR-0140 | *Shows up* and *answers challenges* are folded from `games` and `challenges`; the other three have no provider. A player with no record is **absent from the answer**, never a zero — that zero would be *invented*, and no record is not a bad record |
| Pairwise history → previous accept · previous decline | **Live** since [#253](https://github.com/Raketa02/Raketa/issues/253) | `SeatAccepted → ACCEPTED` and `SeatDeclined → DECLINED`, and nothing else does. A **lapse tallies nowhere** — silence is not a judgement — and a challenge born of a mutual yes tallies nothing, because nobody answered anything |
| Pairwise history → familiarity | **`NoEvidence`** | *You have never played this person* is still true of everyone: a challenge accepted is not a game played, so `games_played_together` is `0` and the modifier is absent rather than firing identically on every candidate |
| Origin key | Demanded from day one | The search half of §19.2's chain ships now; the outcome half joins it when `matches` lands |
| At stake | **Absent** | Nobody's Level has ever moved on a result, because the rule that moves it is not written. A zero would claim a counted game changes nothing, which is false about every opponent — so the field is omitted and the card shows no block |

---

## How the demand is made binding

**The contract suite is parameterised over every registered implementation of each port,
including the null one.** `NoHoldsExist` proves the degradation table above, green, today —
named for the fact it asserts rather than for being empty. `NoPlayerScoresExist`,
`NoResultUpdateRuleExists` and `ChallengesButNobodyHasPlayed` were the same convention over the
same table, and **all three are gone**, each on the day its own stated fact stopped being true
([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md),
[ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md),
[ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
That is the intended end of a null object named for a fact, and in every case the swap was one
row in the register. **The one left is a gate**, which is this section's own rule showing
through rather than a coincidence: every *term* now has a provider.

**The arrangement belongs to the port and never to one implementation**, and where a provider
ships, the suite arranges a real world through that context's aggregate rather than an `INSERT`
([ADR-0029](../../adr/0029-seed-data-through-aggregates-never-in-production.md)). For
`MatchHistoryQuery` that arrangement **splits in two**, and the split is said out loud: the
challenge half is arranged and asserted, and `PLAYED`, `PLANNED_NEVER_PLAYED` and
`late_change_threshold` stay shape-only until `matches` signs, because nobody can arrange them
yet.

Registering a real adapter enrols it in the suite automatically. It either satisfies the
contract or the build is red. **There is no skipped test to go stale**, and no version of
*shipped as one blended number* that passes — which is the entire point, and the reason this is
an ADR rather than a paragraph.
