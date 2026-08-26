# What the matcher demands of `player_score`, `matches`, `cases` — and of `rating`

The matcher declares the facts it requires. Whoever builds those contexts satisfies the
contract however they like — **this document has no opinion on their aggregates, events,
storage or state machines**, and a section here that starts describing how `matches` works
internally has left its lane.

Decided by [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md), resolving
[What the matcher demands of player_score, matches and cases](https://github.com/Raketa02/Raketa/issues/163)
on the map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**Why this is written down at all.** The engine reads the Player Score's six strands
*separately* (§9.3.4), because *confirms results* is close to worthless for a friendly and
close to essential for a counted game. The Player Score is one number in the UI. Left
unwritten, the obvious thing to ship is that number — and the strand-decomposition argument
dies without anybody noticing until the term is wired up. **An unwritten demand is satisfiable
by accident.**

---

## The four ports

One provider signs one contract. The split is by who supplies the fact, never by how fresh it
has to be.

| Port | Provider | Supplies |
| --- | --- | --- |
| `PlayerScoreQuery` | `player_score` | The six strands with their evidence, and opponent variety |
| `MatchHistoryQuery` | `matches` | The searcher's pairwise history, the per-player open-challenge count, and the origin key |
| `AccountHoldQuery` | `cases` | One live boolean per player. Already standing from [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) |
| `AtStakeQuery` | `rating` | What a counted win and a counted loss against one opponent would do to the searcher's Level |

**The fourth one is different, and the difference is stated rather than left to be noticed.**
`player_score`, `matches` and `cases` **do not exist**. `rating` does — it is at
`backend/app/modules/rating/`, with its engine at `app/engines/racketskill/`, and the matcher
already reads μ and σ from it. What is missing is not a context but a **rule**: the
result-update rule and its K-factor, which arrive with `matches` and are out of scope on this
map. The port is here anyway, in this document rather than a second one, because the value of
this file is being *the one place* a build agent finds every demand the matcher makes outward.
Splitting it by does-the-provider-exist would make a reader check two places to be sure they
had them all.

Delivery of the indexed half is the backend's existing transactional outbox
([ADR-0003](../../adr/0003-transactional-outbox-for-event-delivery.md)), as §7.3 describes.
**The transport is settled elsewhere; this document contracts the facts.**

---

## `PlayerScoreQuery`

### The six strands, and what each one counts

Every strand crosses as **the published value, its numerator and denominator, and the moment of
the most recent observation**. The matcher reads the value the player is shown and never
re-derives it — a card explaining a match with a number the player's own profile disagrees with
is worse than a card that says nothing.

| Strand | Denominator — the opportunity | Numerator — the good outcome |
| --- | --- | --- |
| **Shows up** | Games that reached their scheduled moment with this player seated | Games attended |
| **Answers challenges** | Challenges received that fell due | Challenges answered inside the window |
| **Confirms results** | Counted games played | Results confirmed inside the window |
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

- ***Settles up* depends on court money, which this map rules out of scope.** It will stand
  down long after the other five are live. Expected, not a defect.
- **The player-facing weights are not the matcher's weights.** The Player Score screen blends
  the strands at 35/20/15/12/10/8 (`:3374-3380`); §9.3.4 weighs them per mode at 25/32, 22/22,
  24/4, 14/14, 10/12, 5/16. Both are right. This is precisely why the matcher must read strands
  and not the blend.

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
| The searcher's pairwise counterparts, each outcome distinguishable — **accepted**, **declined**, **played**, **planned-never-played** — with their moments | The most recent **500** | A searcher has played tens of people. An unbounded read is how one long-standing player's search becomes slow for everyone |
| Every challenge currently open between the searcher and anyone | **Unbounded** | It is a §7.5 never-stale fact and it is small by construction |
| Open challenge count, **per player** | The index row | Not pairwise. Advisory, for ranking on load (§7.2, §14.4) — never the last word |

**A ghost game is two facts, and they go different places.** As a per-player reliability signal
it is `player_score`'s input and the matcher never sees it separately. As a **pairwise** outcome
it is here, distinguishable from a game that was played, because familiarity must be able to
tell them apart.

### What fails how

| Read | On failure | Why |
| --- | --- | --- |
| Block set (`BlockQuery`, ADR-0095) | **The search refuses** | A gate that cannot be evaluated excludes |
| Hold flag (`AccountHoldQuery`, ADR-0095) | **The search refuses** | Same |
| Pairwise history | **Fails soft** — familiarity and the previous-decline signal stand down, the search proceeds | Losing a game because we could not remember who you played in March is a worse outcome than a slightly duller list |
| Open challenge between the pair | **Fails soft** | §7.5's *the matcher proposes, the backend disposes* re-verifies on the shortlist. It is embarrassment with a backstop, not a safety failure |

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

**The matcher never reads `cases` to score.** A held player is both excluded by the gate and
carrying a low *settles up*. **That double reach is intended.** It is written down here so
nobody later tidies away the apparent duplication by removing one of them: the gate is absolute
and the strand is weighed, and they answer different questions about the same event.

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
  `matches` works internally. It demands the fact and stops.

**For-fun games are never counted** (§23 Q11), so the field is competitive-only — which the
prototype already enforces at `:2460`. In for-fun it is not absent-because-unavailable; it is
**meaningless**, and the card renders nothing.

**Today the rule does not exist**, so the only adapter is `NoResultUpdateRuleExists` and the
field is **absent, never zero**. A zero here would be invented — it would claim a counted game
against this opponent moves the searcher's Level by nothing, which is false about every
opponent. The card simply omits the block.

---

## What happens while none of these contexts exist

The rule, and it will be faced again by every context that lands later:

> **A gate may be honestly empty; a term may never be honestly neutral.**

The test is whether a zero would be **measured** or **invented**.

| Fact | Today | Which, and why |
| --- | --- | --- |
| Hold flag | **True-over-empty** | Nobody can be held because nothing can hold anybody. A real, measured absence |
| Open challenge count | **True-over-empty**, at `0` | No challenge has ever been sent by anyone. A real zero |
| Pending challenge between a pair | **True-over-empty**, empty set | Same |
| The six strands, opponent variety | **`NoEvidence`** | Nobody has failed to turn up because nobody has ever been due to. A zero here would be *invented*, and no record is not a bad record |
| Pairwise history → familiarity | **`NoEvidence`** | *You have never played this person* is true of everyone, and a modifier firing identically on every candidate changes no ranking while printing a sentence on every card |
| Origin key | Demanded from day one | The search half of §19.2's chain ships now; the outcome half joins it when `matches` lands |
| At stake | **Absent** | Nobody's Level has ever moved on a result, because the rule that moves it is not written. A zero would claim a counted game changes nothing, which is false about every opponent — so the field is omitted and the card shows no block |

---

## How the demand is made binding

**The contract suite is parameterised over every registered implementation of each port,
including the null one.** `NoPlayerScoresExist`, `NoMatchHistoryExists` and
`NoResultUpdateRuleExists` prove the degradation table above, green, today — named for the
facts they assert rather than for being empty, in `NoHoldsExist`'s style.

Registering a real adapter enrols it in the suite automatically. It either satisfies the
contract or the build is red. **There is no skipped test to go stale**, and no version of
*shipped as one blended number* that passes — which is the entire point, and the reason this is
an ADR rather than a paragraph.
