# ADR-0124 — The matcher gates account state, never age

- **Status:** Accepted
- **Date:** 2026-08-26
- **§1 narrowed 2026-09-25 by [ADR-0185](0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md) §5**: age is a precondition of **playing**, not of holding an account. An account an Invitation created isn't attested, and *Start playing* asks before anything player-side; sign-up still refuses without it, and no Skill rating exists without one. *Adults only* and *attestation, not verification* stand.

## Context

[`matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.1 lists eight gates.
Seven name a fact and a provider. The eighth reads **"Below the age or eligibility threshold —
whatever that policy turns out to be"**, and it is the only row in the table whose *Live today*
column says `policy` rather than a context.

[`the-engine.md`](../specs/matchmaking/the-engine.md) §3 carried it forward as row 8 of ten,
marked ⚠ **no policy, no field, no decision** — the only row of the roster with nothing behind
it. Resolving [#189](https://github.com/Raketa02/Raketa/issues/189) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
settles it, and the settling is not one decision but two, because **the row held two rules and
neither was the one it looked like.**

### The age half has no field, no policy, and no place here

`RegisterUserCommand` is `email, nickname, password`. `UserRegistered` carries no date of birth.
Nothing in `backend/app` mentions age except `social_tags.py`, which mentions it to forbid it:
*"never about the person rather than the game — age, looks, body and 'looking for' are a
different product's vocabulary."*

So the gate has no input — and §7.2's privacy line makes that permanent for the index, where
**date of birth is one of six names a build-failing assertion refuses**
([`the-candidate-index.md`](../specs/matchmaking/the-candidate-index.md) §3).
[ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s rule — *a protected
characteristic may gate; it may never score* — **permits** an age gate, so the privacy line is
not what refuses it. What refuses it is that **there is no policy to enforce**: the platform has
never decided whether it admits players under 18.

That decision is not the matcher's. It is *may you hold an account*, not *may these two be shown
to each other*, and those are different contexts. The matcher only ever meets account-holders.

### The eligibility half was a real gate, and it is live today

*Eligibility* looked like vagueness to strike — a gate whose name has two meanings is a gate
nobody can test. It is not. There is an exclusion under it that the roster never named and that
has a provider **today**:

`User.is_active` exists. `UserDisabled` exists. `login` and `refresh_token` both refuse a
disabled account with `account_disabled`, and `get_current_user` refuses it too.

**Nothing in the matchmaking design has ever read it.**
[`the-candidate-index.md`](../specs/matchmaking/the-candidate-index.md) §2 tails
`player_profile`, `rating` and `auth` — never `users` — so a disabled account keeps its index row
and remains a candidate indefinitely. The roster's ten gates ask about blocks, holds, photos,
ratings, radius, opt-in, gender and level. None asks whether the account still works.

## Decision

**Row 8 is replaced by one gate that reads account state, and the age rule leaves this map.**

### 1. Age is an account precondition, in `users`, and it is not a gate here

The platform is **adults only**, and that is enforced where accounts are created, not where
candidates are generated. §9.1's row 8 is **struck** from the gate roster; the roster stays at
ten because the eligibility half is replaced in place.

The rule is **an attestation at sign-up — one boolean — and never a date of birth**, so §7.2's
sentence stays literally true of the whole system and not only of the index. It is filed outside
this map as [#191](https://github.com/Raketa02/Raketa/issues/191), split per app because one
session changes one app ([#192](https://github.com/Raketa02/Raketa/issues/192) backend,
[#193](https://github.com/Raketa02/Raketa/issues/193) player app), on the
[#176](https://github.com/Raketa02/Raketa/issues/176) precedent for a decision made here that
owes code elsewhere. **It is an attestation and not age verification** — it records that the
question was asked and answered, and claims nothing more.

**If the platform ever admits minors, this is reopened as a matching gate and not amended into
one.** An under-18 pairing rule would need an age *band* per player, would bind all six pairs of
a four ([ADR-0116](0116-in-a-four-every-gate-binds-all-six-pairs.md)), and would owe a
safeguarding design — guardian consent, a reporting story — that this platform does not have.
That is a different decision with a different cost, and inheriting this record's number would
disguise it as a revision.

### 2. Gate 8 is **Account active**, read live, candidate-side, failing closed

| | |
| --- | --- |
| **Reads** | `AccountStatusQuery` — a **fifth port**, against `users` |
| **When** | Once per search, as a **set**, beside the block set — never a per-row query |
| **Direction** | **Candidate-side only** |
| **On failure** | **Closed** — the search refuses, as `BlockQuery` and `AccountHoldQuery` already do |
| **Told** | **Nobody.** Invisible to the searcher, like a block |
| **Day one** | ✅ **live** — the provider exists |

**Candidate-side only, and that is a fact rather than a leniency.**
[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) makes the Hold
bidirectional because a *held* player can still log in and run a search; a **disabled** one
cannot get past `get_current_user`, so the searcher side is closed by `auth` before the matcher
is reached. A second check there would assert something the request could not have carried.

**A fifth port and not a fold into `AccountHoldQuery`.** *Held* and *disabled* are different
truths, from different contexts, with different lifecycles and different remedies. One boolean
with two meanings is a gate that fails for unrelated reasons under one reason code, and the
provider that would sign that contract does not exist yet while this one does.
[`consumer-driven-contracts.md`](../specs/matchmaking/consumer-driven-contracts.md) already
proves the pattern is not reserved for absent contexts: `AtStakeQuery` reads `rating`, which
shipped.

**Live, and never an index column.** A stale *active* column means a disabled account is shown to
a stranger, which breaks
[ADR-0111](0111-the-index-holds-only-what-a-player-changes-about-themselves.md)'s invariant by
construction: staleness there costs **quality, never safety**. Account state is also not a fact a
player changes *about themselves* in the profile sense — an administrator may change it — so it
fails the index's admission test on both counts.

**A per-player property, spent at generation**, like every gate that is not about a pair. It
costs one set membership per candidate.

### 3. The word *eligibility* is struck, not reassigned

The gate is named **Account active** and reads exactly one fact. Anything else the word might
have covered — club membership, league eligibility — belongs to `clubs`, which is out of scope,
and would arrive as its own named gate with its own record.

**Account erasure stays fog.** The gate asks *may this account be used*, which today is
`is_active`. Nothing in this repository deletes an account, and erasure is a platform-wide
obligation rather than a matchmaking rule.

## Consequences

- **The roster stays at ten and one row changes provider.** `the-engine.md` §3's row 8 goes from
  the only ⚠ **open** row to ✅ **live** — the roster's *last* undecided gate is closed, and it is
  closed by a provider that shipped before the map was drawn.

- **A gap that was live becomes a gap that is filed.** Until this gate is built, a disabled
  account is a candidate. That was true before this record and unnoticed; it is now a line in
  §3 and a day-one item in §16.

- **`AccountStatusQuery` needs no consumer-driven contract stub.** The other four ports exist
  because their providers do not ([#163](https://github.com/Raketa02/Raketa/issues/163)); this
  one has a real adapter on day one, and the contract suite runs against it rather than against a
  fake standing in for a context nobody has written.

- **The system-wide privacy claim is now as strong as the index's.** §7.2's six forbidden names
  were an assertion about one data structure. With no date of birth collected anywhere and an
  attestation in its place, *the value is not in the process* is true of the process and not only
  of the row — which is the sentence ADR-0096 rests on, now resting on less.

- **The map's vocabulary gains a distinction it needed.** A **held account** and a **disabled
  account** are two gates that sound alike, from two contexts, and `CONTEXT.md` now says so. The
  next gate that reads *account state* has to say which one it means.

- **The eighteen-month version of this is worse, and that is the argument for the record.** A
  build agent meeting §9.1 row 8 unreviewed implements *whatever that policy turns out to be* by
  guessing at it, and the most available guess is a date-of-birth column — the one field six
  documents forbid by name.
