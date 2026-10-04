# ADR-0096 — A gender preference is a mutual gate the scorer cannot see

- **Status:** Accepted
- **Date:** 2026-08-26
- **§6 amended by [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)** — the owner's own profile read,
  `GET /players/me/profile`, is the one response shape that carries `gender` and
  `gender_preference` out; every shape a stranger reads stays clean, and §21's test asserts both
  halves.
- **§3's reach narrowed by [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)'s
  amendment of 2026-10-02.** The preference governs who a player is **matched** with. It does not
  reach the account **running an official group** the player joined, which opens their record
  without it ([#566](https://github.com/Raketa02/Raketa/issues/566)). Every surface that
  introduces one player to another, and every co-member of a group, is still gated by it.

## Context

The matchmaking engine applies its gates before anything is scored
([`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.1).
Whether a player may say *I want to play with women* — or with men, or with anybody — is the
one question the design document explicitly declines to answer by default. Its §23 Q8 calls
it *"the sharpest what-this-product-refuses-to-be line in the whole design"* and recommends a
middle path: support it **only as a format declaration attached to a game** — *mixed doubles*,
*women's doubles* — and **never as a browse filter over individuals**, handling the safety
concern instead through public-place first games and the block machinery. This record settles
[#160](https://github.com/Raketa02/Raketa/issues/160), and it **overrules that
recommendation**.

**Why the middle path does not exist here.** The document's distinction is honest only where a
game *already exists* and a player chooses to join it — an open invitation, where the
composition rule is a property of the thing being joined rather than a filter over people. The
map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
rules open invitations and gatherings **out of scope** — they are the social half of the
prototype. Inside scope, the only doubles surface is a searcher building their own four (§9.9).
Declare *women's doubles* there and the engine hands back a shortlist for the three empty
seats: a gender-filtered list of individuals, whatever the container is labelled. Producing it
requires either a gender field in the index or a gender-derived exclusion set computed
server-side — the browse filter, one layer down and out of sight. The compromise collapses
into the thing it was meant to avoid, so the choice is between having the feature and not
having it.

**What the repository has.** Nothing. `grep -rni gender backend/app` returns no match; sign-up
and onboarding never ask; **no ADR mentions gender at all**. The rule lives only in the input
document (§7.2, §23 Q8) and as a standing preference on the map, so nothing accepted is being
contradicted — a map preference is being amended by the map's owner.

Two repository facts do bear on it. `app/kernel/sports.py` records a sibling refusal in its
own words — *"There is deliberately no `Format` dimension… Reintroducing formats is a new
decision, not a gap to be filled"* — which is precisely what §23 Q8's *mixed doubles* would
have done through a side door. And [`CONTEXT.md`](../../CONTEXT.md) rules that a social tag is
*"never about the person rather than the game — age, looks, body and 'looking for' are a
different product's vocabulary."* A gender preference is not a tag and that rule survives
untouched; it is recorded here so the two are not read as contradicting each other later.

The alternatives considered and rejected:

- **§23 Q8's format-on-a-game.** Rejected: the surface that would make it honest is out of
  scope, and inside scope it is the same mechanism wearing a better name.
- **Nothing in v1.** Rejected by the product owner. A player who wants to play only with women,
  or only with men, or who does not care, is expressing an ordinary preference about who they
  spend ninety minutes on a court with; refusing it does not make the want go away, it makes
  the platform the wrong place to satisfy it.
- **A gender field on the candidate index, readable by anything.** Rejected — see Decision 1.
- **ADR-0095's `exclude_player_ids` pattern**, resolving the preference server-side into ids.
  Rejected on scale: a block set is tens of rows, a gender exclusion set is half a city —
  25 000 ids per search for the index §7.2 sizes at 50 000 players.
- **A one-directional filter** over the searcher's own results. Rejected — see Decision 3.
- **A weight rather than a gate.** Rejected: *only women* does not mean *mostly women, and here
  is a man at 71*.

## Decision

### 1. The scorer never receives it; the gate is its only reader

ADR-0093 split the matcher in two: the state in `app/modules/matchmaking/`, the pure scorer in
`app/engines/matchfit/`. The split carries the guarantee.

**Gender sits on the candidate index row used for generation and gating, and is absent from
the type handed to the scorer.** §7.2's sentence — *"a term cannot read a protected
characteristic because the value is not in the process"* — therefore stays **literally true**:
the scorer's input genuinely does not carry it, so no term, hand-written or otherwise, can
weigh it.

§7.2's schema test does not die; it moves, and becomes two assertions, both failing the build:

1. **Type-level.** The scorer's input type contains no gender field — the forbidden-field-name
   assertion the document already describes, retargeted from the index row to
   `app/engines/matchfit/`.
2. **Call-site.** The field name appears nowhere under `app/engines/matchfit/`, and inside
   `app/modules/matchmaking/` the gate is its only reader.

The first is the guarantee. The second is what catches somebody quietly threading the value
through later. Every other name on §7.2's list — name, photo, email, date of birth,
nationality, precise location — is untouched: those fields still do not exist at all.

### 2. Two types, not one, and neither is an inference

| Term | Values | Shape |
| --- | --- | --- |
| **Gender** | `WOMAN`, `MAN`, `PREFER_NOT_TO_SAY` | A field on `PlayerProfile`. Per person, never per sport. Self-declared, freely changed |
| **Gender preference** | `WOMEN_ONLY`, `MEN_ONLY`, `ANY` | Durable, on `PlayerProfile`, defaulting to `ANY` |

`PREFER_NOT_TO_SAY` matches only an `ANY` search and never a constrained one. It is **the same
shape as Play intent's `NO_PREFERENCE`** (ADR-0094): an explicit answer, never a null, and
never confused with *I have not been asked*.

This makes the field a statement about **which searches a player wishes to appear in**, not a
ruling by the platform on who anybody is. A player whose identity is not on that list chooses
the answer that puts them where they want to be seen, or takes `PREFER_NOT_TO_SAY` and appears
in unconstrained searches only. The platform adjudicates nothing.

The words are plain on purpose. A euphemism would have failed the engine's third refusal — it
never produces something it cannot explain in one sentence.

**The field is required**, asked once at profile creation, with `PREFER_NOT_TO_SAY` as a
first-class answer — the ruling §23 Q2 already accepted for Play intent, for the same reason:
optional collection silently shrinks the constrained pool at exactly the moment the pool is
smallest. The **preference** is optional and defaults to `ANY`. Existing players are asked on
next open; at eleven players that is not a migration.

### 3. The gate is mutual

A ninth gate joins §9.1's table, marked **policy** rather than engineering — like the age
threshold already there, the engine enforces whatever the policy says and does not decide it.

**It reads both sides.** A candidate is eligible only if they pass the searcher's preference
**and** the searcher passes theirs. This is ADR-0095's block shape reused deliberately — *a
directed record with a symmetric effect* — and it is the whole difference between this and a
dating filter. A one-directional filter protects a woman's *search* and leaves her *inbox*
open to every man who searched `ANY`: her preference would govern only what she sees, never
what reaches her, which is the exact failure mode that makes these filters feel unsafe to the
people they exist for. One extra comparison buys the other half.

Mutuality is why the preference is **durable** rather than per-search: it has to be evaluated
against a player when somebody else searches and they are not present. A per-search setting
cannot bind the other direction at all. A **per-search override may narrow, never widen** — a
player whose durable setting is `ANY` may search women-only tonight; nobody may widen past
another player's durable setting, because that setting is evaluated independently.

Mutuality has a cost the player must be told about: setting `WOMEN_ONLY` makes them invisible
to men entirely, including men searching `ANY`. **The client says so at the moment of
setting**, from a reason code — ADR-0022 unchanged. Learning it from silence is not acceptable.

### 4. Never relaxed, applied before enumeration, and it does not evict

**No relaxation rung reaches it.** §9.1's rule is unqualified and this gate inherits it: a thin
pool plus `WOMEN_ONLY` yields the honest empty state, never a quiet widening into men. It also
inherits `CONTEXT.md`'s paired invariant from ADR-0095 — *a gate that cannot be evaluated
excludes.*

**In doubles it binds every seat**, and is applied at candidate generation (§9.2), before §9.9
enumerates combinations — so the group objective is drawn from an already-eligible pool and
never sees the constraint. A player shares a court with all four for ninety minutes; binding
only the partner seat would be incoherent.

*(Amended by [ADR-0116](0116-in-a-four-every-gate-binds-all-six-pairs.md): **every seat** was
read here as every seat **against the searcher**, who is in only three of a four's six pairs —
leaving a `WOMEN_ONLY` player open to every man a third party seats beside her, which is the
failure mutuality was chosen to prevent. Eligibility for a seat is a property of a combination,
so the other three pairs are checked inside enumeration as an admissibility mask. This ADR's own
sentence is the argument, applied one step further than it was applied. The group objective still
never **scores** on the constraint, and the fenced scorer type is untouched — the mask is built in
the module where the I/O is, before the pure scorer is called.)*

**Seats already accepted are facts, not candidates.** Changing a preference changes future
searches; it never retroactively evicts somebody who has already said yes.

### 5. Asymmetric feedback, deliberately

A candidate can vanish two ways, and the searcher learns about exactly one of them:

- **Your own constraint** narrowed the result — you are told, by reason code. It is your
  setting and it is actionable.
- **Their preference** excluded you — you are told nothing, ever, on any surface.

Surfacing the second leaks a third party's choice and invites them to be sought out. Same
instinct as ADR-0095's silent block, applied where it belongs.

### 6. It does not cross the wire outward

`SearchContext` carries a gender preference **in**. **No response shape carries a gender
value out**, and no card renders one. §21's existing test — no response shape can carry a
decline, a block or a hold — is extended by the same assertion.

§23 Q1 shows a candidate's declared *intent* on their card because it is their own word about
themselves, and names the risk: it becoming a status label. Intent has `NO_PREFERENCE` as its
defence. Gender has none, and the photo gate already means every card carries a photo, so a
badge would add no information and only a label.

## Consequences

**Easier**

- An ordinary preference about who a player spends ninety minutes with is expressible, and
  expressible *mutually* — which is more than the browse filters this design was written in
  reaction to ever offered the people they were supposed to protect.
- §7.2's guarantee survives in a stronger form than prose. It is a type boundary the build
  enforces, not a review checklist, and ADR-0093's split is what pays for it.
- The gate needs no context that does not exist. Unlike the block and the hold, both sides of
  it are on `PlayerProfile` today.

**Harder**

- **A protected characteristic is now collected, and required.** It must be erasable, it is
  regulated — single-sex service provision is not the engine's call — and *collected once* is
  irreversible in a way a schema migration is not.
- **The pool fragments.** Every constrained searcher sees a fraction of the city, and under
  mutuality every constrained *candidate* is invisible to part of it. At eleven players this
  is severe, and it lands directly on
  [The thin-pool experience](https://github.com/Raketa02/Raketa/issues/166) and
  [The five numbers](https://github.com/Raketa02/Raketa/issues/167), which must now model the
  gate's effect on coverage rather than assume one pool.
- **`PREFER_NOT_TO_SAY` costs its holder reach**, and the honest framing of that cost is a copy
  problem nobody has solved yet.
- **Two comparisons and two fields on the gate path**, plus a required onboarding step on a
  flow ADR-0090 already checkpoints.

**Neutral**

- §23 Q8 is overruled, not amended: the recommendation was *format on a game, never a filter on
  people*, and this is a filter on people, made mutual. §7.2 is amended — the index may hold
  the field, the scorer may not. §9.1 gains a ninth row.
- `app/kernel/sports.py`'s refusal of a `Format` dimension **stands undisturbed**, and this
  record is the reason it was tested: *mixed doubles* would have reintroduced formats to answer
  a question that turned out to be about people, not games. A search carries a sport and never
  a format; the sport fixes the seat count.
- `CONTEXT.md`'s social-tag rule stands. Gender is not a tag, is not player-authored, and is
  never rendered on a card — the vocabulary that rule protects is unchanged.
- The map's standing rule is amended by the same decision that produced this record: the ADR
  wins by default, but where the prototype or the design document is demonstrably better —
  argued on matchmaking quality or player value, not preference — the document wins and the ADR
  is amended to say so.
