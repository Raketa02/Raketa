# ADR-0106 — Evidence crosses as a closed vocabulary: a weight is configuration, an evidence shape is contract

- **Status:** Accepted
- **Date:** 2026-08-26

> **Checked 2026-09-05 against [#306](https://github.com/Rakieta02/Rakieta/issues/306) and
> [#312](https://github.com/Rakieta02/Rakieta/issues/312) — the first batch of fields this record
> had to classify — and nothing here changed.** This is a confirmation rather than an amendment,
> recorded because a rule that has never been exercised is a rule nobody knows the cost of. The competitive card grew five fields —
> `player_card.player_score`, `counted_games`, `last_five` and `review`, and `at_stake` on the
> candidate — and §3's test answered each of them the same way: **none is a weight, so every one
> of them is contract**. They are card fields rather than evidence variants, so they cross on
> [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)'s assembly seam and no
> variant of the closed union gained a member; the price §3 sets — a client release rather than
> a ruleset release — is the price all five paid.
>
> **§4 is the clause that did the work, and it now binds five more fields.** Every one of them is
> **omitted rather than nought or false**, each on its own condition — nothing watched, nobody
> looked, a mode where a counted result is meaningless. One of the five is the interesting case,
> because it is the first place a **measured** zero met a field that must spell absence: `games`
> answers a real nought to its own callers, and the card refuses to print one, because *nought
> games* and *no record* would be one absence in two spellings. The Consequences below predict
> exactly this for `player_score`, in the future tense; the tense is what expired.
>
> **§5 is untouched and was tested rather than trusted.** `last_five` carries outcomes in order
> and **no dates at any granularity** — five events with moments beside them is *last seen* —
> and the refusal is asserted centrally over the emitted contract rather than per route. §6 is
> untouched: `RELIABILITY` had never fired for anybody and now fires for anybody the platform
> has watched, which is a variant clients have been able to render since day one finally
> arriving with something in it — and an evidence kind a build cannot read still renders a named
> gap rather than a shorter list.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** The ranking is gone (#580), and with it every evidence variant — the modifier, liveness, inclusion and gate reason codes, the relaxation `ask`, the challenge `window` and `search_candidate.terms` — so §1, §2, §3 and §5 govern nothing that runs, and no weight is left to configure. Two rules outlived the matcher and still bind: §4's two spellings of absence (omitted where a field does not apply, `null` for a measured nothing), as the player record and a booked game's pairing serialise them, and §6's named gap, which the player app draws for any closed code it does not know (`shared/vocabulary/outOfDate.ts`).

## Context

Two rules this repository already holds point in opposite directions the moment the matcher
has to serialise a reason.

**[ADR-0022](0022-kernel-negative-space-and-constant-homes.md), extended to the matcher by
§12.1 of `matchmaking-engine.md`:** the backend
emits machine codes and never display text. Evidence crosses structured —
`{"kind": "availability_overlap", "shared_count": 4, "next_slot": {...}, "days_away": 5}` —
and the client writes *"4 shared slots · next Tuesday evening."* This is settled and nothing
here reopens it.

**[ADR-0006](0006-backend-owns-api-contract.md):** the backend owns the contract, emits it as
`openapi.player.json`, and the client **generates** its wire types from that document, never
hand-writing a DTO that mirrors a backend response. `check-contract-drift.sh` regenerates and
diffs in CI, so a contract change shipped without its client types fails the build.

`search-telemetry.md` then makes the stored
`search_candidate.terms` column **deliberately opaque** JSONB — *"stamped with
`ruleset_version` and its shape is allowed to change between rulesets, which is exactly what a
relational schema would fight."* That is right for storage, and it was written about storage.

**The collision is what happens if the wire mirrors the store.** An open blob generates into
TypeScript as `Record<string, unknown>`. The client then hand-writes the evidence types after
all — ADR-0006's exact failure, arriving not because anybody broke the rule but through a hole
in the schema where the rule has nothing to bite on. And the failure is **silent**: an
evidence kind the client does not know renders as nothing at all, on the one screen whose
entire promise is that it shows its working. A missing reason line looks identical to a term
that stood down, which [ADR-0098](0098-matcher-demands-as-executable-contracts.md) spent a
whole record making distinguishable.

Underneath sits a distinction [ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)
drew and did not have to finish: **engine version** stamps how the maths works, **ruleset
version** stamps what the numbers were. A ruleset is frozen configuration, released as a
named dataset. What ADR-0093 did not say is whether a ruleset may change the *shape* of what
a term reports, as opposed to the *values* it reports — and that turns out to be the line
between a configuration release and an API release.

One further force, particular to this product's clients: `frontend_player/` ships to app
stores. A deployed build can be months older than the backend, so *"the client regenerates"*
is true of the repository and false of the phone in somebody's hand.

## Decision

**We will treat the evidence vocabulary as part of the API contract, and the numbers inside it
as configuration.**

### 1. The wire carries a closed, discriminated evidence union

Every term's evidence crosses as a variant keyed by `kind`, and the union of variants is
enumerated in `openapi.player.json`. The client generates an exhaustive type and a renderer
per variant. This is §12.1's structure with its openness removed: the same objects, named.

The same applies to every other closed vocabulary the response carries — modifier codes,
liveness reason codes, inclusion reasons, gate reason codes, the relaxation `ask`, the
challenge `window` (ADR-0100),
`optimised_for`. Sports, tags, day parts and intents cross as the platform's **existing**
machine codes; a second spelling of a closed vocabulary is how two systems begin disagreeing
about the same word.

### 2. Storage stays opaque, and the two are allowed to differ

`search_candidate.terms` remains JSONB. This is not the two-homes defect
ADR-0104 removed: that was one
number in two stores **free to disagree about the same question**. These two serialisations
answer different questions. The row must still deserialise in five years under a ruleset
nobody runs any more; the wire type must be exhaustive *today*, for the ruleset that is
live. Openness is the right property for the first and the wrong one for the second.

The guard is one test: **every evidence kind the currently loaded ruleset can emit is present
in the wire union.** A ruleset that can produce a kind the contract does not publish fails to
load, on §11's own malformed-ruleset rule.

### 3. A weight is configuration; an evidence shape is contract

- Releasing a ruleset that changes **weights, constants, thresholds or bounds** — no contract
  change, no client work, no regeneration. This is what ADR-0093's ruleset version is for and
  it is unaffected.
- Releasing a ruleset that **adds, removes or reshapes an evidence variant** is an **API
  change**: `make gen-api`, committed in the same change, or `check-contract-drift.sh` goes
  red.

That is the friction we want, in the place we want it. A weight is a hypothesis about ranking
and should be cheap to move. An evidence shape is a promise about what the product can
explain, and a promise the client has to be able to keep.

### 4. Absence has two spellings, and they mean different things

- **Omitted** — this field does not apply here. `at_stake` in a for-fun search: §23 Q11 makes
  a for-fun game never counted, so the number is *meaningless*, not unavailable.
- **`null`** — this field applies, and the answer is a measured nothing that is itself a
  recorded fact. `rung_offers: null` means the offers were **not computed at all** because the
  shortlist cleared `MIN_SHORTLIST`, which is that constant's own falsifier;
  `best_withheld_fit: null` means nothing was withheld, which is not `0`.

This is [ADR-0098](0098-matcher-demands-as-executable-contracts.md)'s test — *would a zero be
measured or invented* — carried to serialisation, and it generates into two different
TypeScript types (`field?: T` against `field: T | null`), so the client is forced to handle
them differently. That is the point.

### 5. No Liveness number crosses, ever

§12.2 makes the two numbers a type boundary inside the engine. At the wire it is a schema
fact: a candidate carries `fit` and a list of liveness **reason codes**, and there is no field
a Liveness offset could be written to. The printed Fit is the only number a player is asked to
trust, and the moment it silently contains *"they open the app a lot"* it stops meaning what
it says.

### 6. An unknown evidence kind is a named gap, never silence

A deployed client older than the contract will meet a `kind` it cannot render. It **drops that
reason from the card** — the card shows three reasons out of eight and always did — and in the
*Why 78?* breakdown it renders a **named gap** saying this app is out of date, never an empty
row and never a silently shorter list.

The breakdown has to add up. A term quietly vanishing from it is the same class of lie as a
recomputed score, and it is worse for being invisible: the player sees a Fit of 78 explained
by contributions that sum to 61 and has no way to know why. Adding a variant therefore stays
backwards-compatible — old clients keep working — without being backwards-*silent*.

## Consequences

**A matchmaking-only experiment can now require a client release.** Adding a field to an
evidence variant — *"how many of the four shared slots are next week"* — is no longer a
ruleset release; it touches `openapi.player.json`, the generated types, and CI. This is the
main cost and it is deliberate: it prices the difference between tuning a weight and changing
what the product claims it can explain. Experiments that only move numbers stay free.

**The client can render every reason exhaustively, and a compiler says so.** A missing variant
is a type error at build time rather than a blank line on a card in production.

**Two serialisations of one set of facts now exist on purpose,** and one test stands between
them. If that test is ever deleted the drift is silent for exactly as long as nobody releases
a ruleset with a new kind — which is the failure mode to watch, and the reason the check is a
load failure rather than a lint.

**Old clients degrade visibly rather than quietly.** The named gap is a slightly worse screen
than a perfectly rendered one and a much better screen than a plausible wrong one — the same
trade ADR-0099 took on the honest empty
state, and §18's standing rule: degrade
honestly, never fabricate.

**The absence rule binds every context that later serialises a matcher fact,** not just this
one. When `matches` and `player_score` land, their absent facts cross by the same two
spellings — which is what stops *"we have no record"* and *"the record says zero"* collapsing
into one nullable column somewhere downstream. **This came true and it came true the hard
way** (see the amendment at the top): `games` and `player_score` landed, and the card's
`counted_games` is the one place a provider's **measured** zero meets a field that must spell
absence — so the adapter drops the row rather than carrying the nought through, and the
inversion is written at the seam where it happens rather than left to a nullable column.
