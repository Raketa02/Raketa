# The canonical Now state table — 35 contexts, 17 tags, one resolution ladder

Research output for `Raketa02/Raketa#5`. **Facts and citations only.** Where the sources
contradict each other this file quotes both sides, applies `now-section-domain-spec.md` §A.0's
ruling if §A.0 has one, and otherwise says *open* and stops. Deciding what `formingBack` should
become, or what the leaver sees, belongs to #7 and #8.

## Method, and what "verified" means here

The five prose sources were read directly. The v37 prototype was **executed**, not read about:
`2-rakieta-player-app-v37-netlify (2).zip` was unzipped to a single 498 698-byte
`netlify-deploy/index.html`, its one `<script>` block (lines 398–7331) extracted, and run under
Node 23 in a `vm` context with a proxy-stubbed DOM. Every claim tagged **[EXEC]** below is the
output of calling the prototype's own `matchState()` on constructed match records — no
reimplementation, no inference from prose.

Three executions back this document:

| Run | What it did | Scale |
|---|---|---|
| Enumeration | called every `ST[key](m)` and read `tag` / `tone` / `be` / `ctx` / `post` off the result | 35 keys |
| Ladder fuzz | built fresh records over a grid of club × seat-configuration × clock-offset × `vacated` × `committedAt` × one-of-16 flags, plus a private-match grid, and called `matchState()` on each | 280 224 records |
| Scenario sweep | rebooted the app and ran each of the prototype's own `SCEN` entries, then resolved every match in `S.matches`, discarding forced/gallery records | 89 scenarios |

**Source shorthand.** `UI` = `rakieta-now-section-ui-spec.md` · `SPEC` =
`rakieta-now-section-specification.md` · `DOM` = `now-section-domain-spec.md` · `3.1` =
`3.1-enrolled_match_states_and_transitions.md` · `3` =
`3-enrolled_match_engine_architecture.md` · `R5` = `5-now_screen_architecture_review.md` ·
`P` = the v37 prototype.

**Rung numbering.** Two numberings are in circulation and they differ by one. This document uses
`DOM` §E.1 / `3.1` §1.4 numbering — rungs **1–15**, no rung for the gallery short-circuit, plus
two post-pass wrappers **W1/W2**. `UI` §B6.1 and `SPEC` §E4 both count `m.forced` as rung 1 and
so number everything else one higher. When `R5` and this document say *"rung 9"* they mean the
`vacated`-without-commitment rung, which `UI`/`SPEC` call rung 10. Nothing behavioural turns on
this; it is a citation hazard only.

---

## 1. The reconciled table

**Verified count: 35 contexts, 17 tags.** [EXEC] `Object.keys(ST).length === 35`;
`new Set(map(ST, s => s.tag)).size === 17`.

`Facet A` is the card's **Court** line, `Facet B` its **Group** line (`UI` §B6.3 naming;
`P` field names `court` and `group`). `post: 1` suppresses the *Getting in* button.
Templates use `{f}` filled, `{n}` seats, `{cat}` court category, `{club}` club name.

| # | `key` | Tag | Tone | Facet A — Court | Facet B — Group | `post` | Rung | Exact predicate on that rung | Sources |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `inventoryLost` | Cancelled | **`bad`** ⚠ | `Gone — the last {cat} court was sold` | `{f} of {n} seats paid` | — | 1 | `m.inventoryLost` | UI SPEC DOM 3.1 R5 P |
| 2 | `cancelledClub` | Cancelled | `ended` | `Cancelled by {club}` | `everybody refunded` | — | 2 | `m.clubCancelled \|\| m.weather` | UI SPEC DOM 3.1 P |
| 3 | `cancelledIncomplete` | Cancelled | `ended` | `Released back to the club` | `{f} of {n} — it never filled` | — | 3 | `m.formCancelled` | UI SPEC DOM 3.1 R5 P |
| 4 | `cancelledCheckpoint` | Cancelled | `ended` | `Released back to the club` | `{n−1} of {n} — the seat was never refilled` | — | 4 | `m.checkpointCancelled` | UI SPEC DOM 3.1 R5 P |
| 5 | `playedNoShow` | Played | `idle` | `Settled` | `{n−1} of {n} played` | **1** | 5a | `now >= matchEnd(m)` ∧ `m.noShow` | UI SPEC DOM 3.1 R5 P |
| 6 | `playedShort` | Played | `idle` | `Settled` | `{n−1} of {n} played` | **1** | 5b | `now >= matchEnd(m)` ∧ `filled(m) < m.n` | UI SPEC DOM 3.1 R5 P |
| 7 | `completed` | Completed | `good` | `Settled` | `{n} of {n} played` | **1** | 5c | `now >= matchEnd(m)` ∧ `m.confirmed` | UI SPEC DOM 3.1 R5 P |
| 8 | `playedNoScore` | Played | `idle` | `Settled` | `{n} of {n} played` | **1** | 5d | `now >= matchEnd(m)` ∧ `now >= resultWindow(m)` (= `matchEnd + 30 min`) | UI SPEC DOM 3.1 P |
| 9 | `confirmResult` | Confirm the result | `watch` | `Settled` | `{n} of {n} played` | **1** | 5e | `now >= matchEnd(m)` ∧ `m.score` truthy | UI SPEC DOM 3.1 P |
| 10 | `needsResult` | Needs result | `watch` | `Settled` | `{n} of {n} played` | **1** | 5f | `now >= matchEnd(m)`, otherwise | UI SPEC DOM 3.1 R5 P |
| 11 | `waitlisted` | On standby | `idle` | `Fully paid by four other players` | `{n} of {n} · you are 2nd on the standby list` | — | 6 | `!mySeat(m) && S.waitlists.includes(m.id)` | UI SPEC DOM 3.1 R5 P |
| 12 | `privateOpen` | Reserved | `good` | `Yours · {club.court}` | `{f} of {n} · 1 seat open to the marketplace` | — | 7 | `m.kind === 'private'` ∧ `m.openSeats > 0` | UI SPEC DOM 3.1 P |
| 13 | `privatePartial` | Reserved | `good` | `Yours · {club.court}` | `{f} of {n} shares paid` | — | 7 | `m.kind === 'private'` ∧ `m.payModel === 'split'` | UI SPEC DOM 3.1 P |
| 14 | `privateReserved` | Reserved | `good` | `Yours · {club.court}` | `you invite whoever you like` | — | 7 | `m.kind === 'private'`, otherwise | UI SPEC DOM 3.1 P |
| 15 | `privateFull` | Reserved | `good` | `Yours · {club.court}` | `{n} of {n} shares paid` | — | **none** | **no rung produces it** — see §3 | UI SPEC DOM 3.1 P |
| 16 | `replacementTransfer` | Replacement pending | `watch` | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | 8a | `m.vacated && m.committedAt != null` ∧ `m.transferring` | UI SPEC DOM 3.1 P |
| 17 | `rescueLate` | Rescue active | `time` | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | 8b | `m.vacated && m.committedAt != null` ∧ `now >= d.check` (= `start − 2 h`) | UI SPEC DOM 3.1 P |
| 18 | `rescue` | Rescue active | `time` | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | 8c | `m.vacated && m.committedAt != null` ∧ `now >= d.rescue` (= `start − 4 h` doubles, `− 6 h` singles) · carries `alert` | UI SPEC DOM 3.1 R5 3 P |
| 19 | `replacement` | Replacement pending | `watch` | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | 8d | `m.vacated && m.committedAt != null`, otherwise · carries `alert` | UI SPEC DOM 3.1 R5 3 P |
| 20 | `protectedBack` | Court protected | `good` | `Still held · {cat} — three seats are still paid` | `{f} of {n} seats paid` | — | 9 | `m.vacated` (⇒ `committedAt == null`) ∧ `isProtected(m)` | UI SPEC DOM 3.1 R5 P |
| 21 | `formingBack` | Forming | **`watch`** | `Released — the court is no longer held` | `{f} of {n} seats paid` | — | 9 | `m.vacated` (⇒ `committedAt == null`) ∧ `!isProtected(m)` | UI SPEC DOM 3.1 R5 P |
| 22 | `ready` | Ready to play | `good` | `Court {courtName ?? club.court}` | `{n} of {n} · everybody expected` | — | 10a | `isFull(m)` ∧ `now >= m.start − 15 min` | UI SPEC DOM 3.1 P |
| 23 | `confirmedOnFill` | Confirmed | `good` | `{price} settled to the club` | `{n} of {n} · committed on the spot` | — | 10b | `isFull(m)` ∧ `m.committedAt != null` ∧ `committedOnFill(m)` (= `committedAt > d.commit + 60 s`) | UI SPEC DOM 3.1 P |
| 24 | `confirmed` | Confirmed | `good` | `{price} settled to the club` | `{n} of {n} · committed` | — | 10b | `isFull(m)` ∧ `m.committedAt != null` ∧ `!committedOnFill(m)` | UI SPEC DOM 3.1 P |
| 25 | `full` | Full | `good` | `Reserved · settles to the club at {commit HH:mm}` | `{n} of {n} seats paid` | — | 10c | `isFull(m)`, otherwise | UI SPEC DOM 3.1 R5 3 P |
| 26 | `clubHeld` | Court committed | `good` | `Committed by {club} · {cat}` | `{f} of {n} seats paid` | — | 11a | `isProtected(m)` ∧ `hold.why === 'club'` (from `m.courtLocked`) | UI SPEC DOM 3.1 P |
| 27 | `heldSoft` | Court held | `watch` | `Held · {cat} — {hold.note}` | `{f} of {n} seats paid` | — | 11b | `isProtected(m)` ∧ `hold.kind === 'soft'` (`why` `far`: `f ≥ 2` ∧ `>12 h`; `why` `near`: `f ≥ n−1` ∧ `>4 h`) | UI SPEC DOM 3.1 P |
| 28 | `protectedLate` | Court protected | `good` | `Protected · {cat}` | `{f} of {n} seats paid` | — | 11c | `isProtected(m)` ∧ hard hold ∧ `now >= d.commit` | UI SPEC DOM 3.1 R5 P |
| 29 | `protectedCourt` | Court protected | `good` | `Protected · {cat} — a private booking can no longer take it` | `{f} of {n} seats paid` | — | 11d | `isProtected(m)` ∧ hard hold, otherwise | UI SPEC DOM 3.1 R5 P |
| 30 | `heldReleased` | Court released | `watch` | `Released — back on sale at {club}` | `{f} of {n} seats paid` | — | 12 | `m.releasedAt != null && filled(m) >= 2 && now < d.check` | UI SPEC DOM 3.1 3 P |
| 31 | `formingHeld` | Forming | `idle` | `Not protected — no court is held yet` | `{f} of {n} paid · 1 seat held` | — | 13 | `m.seats.some(s => s.p && !s.paid)` | UI SPEC DOM 3.1 P |
| 32 | `formingLate` | Forming | `idle` | `Protected · {cat}` **or** `Not protected — no court is held yet` | `{f} of {n} seats paid` | — | 14 | `now >= d.commit` · two `ctx` variants keyed on `m.created >= d.commit` | UI SPEC DOM 3.1 R5 P |
| 33 | `forming` | Forming | `idle` | `Not held — the club is still selling this slot` | `{f} of {n} seats paid` | — | 15 | otherwise | UI SPEC DOM 3.1 R5 P |
| 34 | `heldStale` | Court released | `watch` | `Released — back on sale at {club}` | `{f} of {n} seats paid` | — | **W1** | after 1–15: `hold.why === 'stale'` ∧ key ∈ {`heldReleased`,`forming`,`formingLate`}. `stale` ⇐ `h.kind === 'soft'` ∧ `pol(club).maxHoldAge` set ∧ `(now − m.created)/h > maxHoldAge` ∧ `filled(m) < n−1` | UI SPEC DOM P |
| 35 | `heldExtended` | Court held | **`good`** | `Held · {cat} — beyond what the ladder guarantees` | `{f} of {n} seats paid` | — | **W2** | after 1–15: `hold.why === 'extended'` ∧ key ∈ {`heldReleased`,`forming`,`formingLate`,`heldSoft`}. `extended` ⇐ `h.kind === 'none'` ∧ `h.why ∈ {nearLapsed, farLapsed}` ∧ `m.clubExtended` ∧ `pol(club).probHold` | UI SPEC DOM P |

Two more facts the table cannot carry:

- **Alert strip.** Only `replacement` and `rescue` set `alert` (`UI` §B6.4, verbatim, verified
  in `P`). `replacementTransfer` and `rescueLate` do not, though they are the same tags.
- **Non-member rewrite.** After a key resolves, if `!mySeat(m) && key !== 'waitlisted'`, every
  line matching `/^You paid/` is replaced with `Your share would be {payable} · booking fee
  0,00 zł` (`P` lines 4007–4012; `UI` §B6.1; `SPEC` §E4). This is the only per-viewer variation
  in the whole resolver, and §4 shows what it does to a leaver.
- **`cta` / `left`.** `stateCard` reads `st.cta` and `st.left`; **no** entry in `ST` sets either
  (`UI` §B6.3 `[GAP]`, §G6.4). Every card falls back to `Open match`.

### Neither wrapper nor gallery covers everything

- `ST_ORDER` — the gallery's own list of contexts — contains **32** of the 35 keys. [EXEC]
  `inventoryLost`, `heldStale` and `heldExtended` are absent, and the group label
  `'Cancelled · four contexts'` sits above a list of three. The two wrapper states were added by
  the later V36 ecosystem patch (`P` lines 6271–6288) and `ST_ORDER` (line 4047) was never
  extended. Consequence: the prototype's own 35-context gallery renders 32.

---

## 2. Disagreement log

### D1 — How many contexts are there?

> **35 contexts.** 15 base rungs plus 2 wrapper rewrites.
> — `DOM` §E.1

> ```
>  1  inventoryLost → inventoryLost
>  … 15 otherwise → forming
> ```
> — `3.1` §1.4 (fifteen rungs, **no wrappers**, and Part 5 documents 33 keys)

**§A.0 rules:** *"State count | prototype **35** | docs 3/3.1/4 **33** | review 33 + leaver group
| **Normative here: 35**, and B1/B3 marked as GAPs."*

**Prototype agrees.** [EXEC] 35 `ST` keys. The 33/35 gap is exactly `heldStale` + `heldExtended`,
which a keyword scan confirms appear in `UI`, `SPEC` and `DOM` and in **neither** `3.1` nor `3`.
`3.1` §9.3 still lists hold Rules 11 and 12 as *"Specified but not implemented"* — true of the
build `3.1` describes, false of v37, which implements both in the V36 patch. `3.1` is describing
an earlier build; that is the whole disagreement.

### D2 — Which ladder ordering is authoritative?

Three orderings are published. Compared line by line they are **the same ordering**, twice
renumbered:

| Source | Rungs | `m.forced` counted? | Wrappers? |
|---|---|---|---|
| `3.1` §1.4 | 1–15 | no | **not present at all** |
| `UI` §B6.1 (*"order **is** the specification"*) | 1–16 | **yes, as rung 1** | yes, as an "override" after 16 |
| `SPEC` §E4 | 1–16 | **yes, as rung 1** | yes, as a "post-pass" |
| `DOM` §E.1 | 1–15 + W1/W2 | no | yes, named W1/W2 |

**No substantive conflict** — the guards and their order are identical in all four, and identical
to `P` lines 3965–4006. The only real difference is `3.1`'s omission of the wrappers (D1) and the
off-by-one in rung numbers. §A.0 does not adjudicate rung *numbering*; it does not have to, since
nothing behavioural depends on it. **Recorded, not open.**

### D3 — Rung 9: can it fire? (`R5` B1)

> The fact table writes `vacated` in one circumstance only:
> `vacated | player id | Written when: A committed player leaves`
> Rung 8 catches `vacated AND committedAt ≠ null`. Rung 9 needs `vacated AND committedAt = null`
> — a combination the fact table can never produce.
> — `R5` §B1

> | **Leaves, not committed** | seat cleared, **`paid = false`** | Full reversal. `filled` −1 → the ladder may release the court |
> | **Leaves, committed** | `vacated`, `vacatedAt`, **`paid` stays true** | Recovery group. |
> — `3.1` §3.2 (the same table; note that the uncommitted row writes **no** `vacated`)

> | **Leave, not committed** | −1, **seat unpaid** | may release | → `formingBack` · `protectedBack` |
> — `3.1` §6.2 (routes the very event whose fact row writes no `vacated`)

**§A.0 rules:** 35 contexts stand, *"with B1/B3 marked as GAPs"* — i.e. §A.0 accepts B1 as a
**gap in the documents**, and does not delete the two states. `DOM` §E.1 carries it as
`[GAP-E2 · B1]` and, importantly, adds the parenthetical `[SRC: 3.1 §1.2 fact table, and
`leaveMatch` sets `vacated` on every leave but `syncMatch` never clears it]`.

**The prototype does NOT agree with B1's first clause.** See §3 — `leaveMatch` writes `vacated`
on *every* leave, so rung 9 fires. **The prototype does agree with B1's second clause** (the
never-cleared pin). §A.0 rules on the *state count*, not on which of the two `vacated` write
rules is correct, so **which one wins is open.**

### D4 — Rung 5 vs rung 6 (`R5` B2)

> Rung 5 (`now ≥ matchEnd` → the post-play group) sits above rung 6 … and rung 5 has no test for
> whether the viewer is actually *in* the match.
> — `R5` §B2

`3.1` §1.4 and `UI` §B6.1 both publish the order with 5 above 6 and neither flags it.
**§A.0 is silent on rung order.** `DOM` §E.1 carries it as `[GAP-E1 · B2]` with a *proposal*, not
a ruling. **Open.** Prototype behaviour: confirmed, see §7.

### D5 — Is `protectedCourt` / `protectedLate` reachable?

> **⚠ `protectedCourt` and `protectedLate` are unreachable by any natural path for a 4-player
> open match.** For `n > 2`, a 3-of-4 match always yields `kind:'soft'`, which routes to
> `heldSoft`; a hard hold only arises when full, committed, locked or private, all of which are
> tested earlier in `matchState`. `[VERIFIED]`
> — `SPEC` §E2, Court-protected group

> `protectedCourt` — **Court protected** · **GUARD** — Protected, hard hold, one player needed,
> before commit … Three paid seats, so a compatible court is held until 4 h before play
> — `3.1` §5 / `SPEC` §E2 condition column

`3.1` §5 describes both as ordinary live states with IN/OUT transitions. `SPEC` says they are
gallery-only. **§A.0 is silent** — its table covers state *count*, not per-state reachability;
`DOM` §E.1/§E.2/§E.4 do not mention it either. **Open.** See §3 for what the prototype does.

### D6 — Hold Rules 11 and 12 (`R5` B5)

> | **11** | A club may set a maximum age for a soft hold | club setting, not a marketplace rule |
> | **12** | A club may hold **longer** than the ladder promises, never shorter | the ladder is a floor |
> — `3.1` §2.1

> Rule 11 … shortens a hold the ladder would have kept. Rule 12: … *"the ladder is a floor."*
> Both are listed in §9.3 as specified but unimplemented, so this is a live decision rather than
> a bug in shipped code.
> — `R5` §B5

**§A.0 is silent.** `DOM` §D.6 composes both wrappers without adjudicating precedence.
**Open** — but `R5`'s framing that this is "not a bug in shipped code" is wrong for v37, which
implements both and resolves the conflict in Rule 11's favour. See §7 B5.

### D7 — `heldStale`'s stated condition

> `heldStale` | `kind === 'soft'`, match age > club `maxHoldAge`, **and** `filled < n−1`
> — `SPEC` §E2, Held/released group

Matches `P` exactly. But `SPEC` §E2 also calls it *"the club returns a soft hold unfilled for
{age} hours"*, where `{age}` renders `pol(club).maxHoldAge` — the **threshold**, not the hold's
actual age (`P`: `age: P.maxHoldAge` in the `stale` hold object, and `ST.heldStale` prints
`h.age`). A hold that has sat 71 hours under a 48-hour cap says *"48 h"*. Cosmetic, unflagged by
any source, **not** adjudicated by §A.0. **Open, and minor.**

### D8 — `inventoryLost`'s tone

Every source that lists it says `tone: 'bad'`, and three of them flag it: `UI` §B6.3 ⚠ and §G6.1,
`SPEC` §E2 ⚠, `DOM` §E.2 `[GAP-E3]`. [EXEC] `ST_TONE` has exactly `good, watch, time, ended,
idle`; `'bad'` is not among them. **No disagreement — unanimous defect.** `DOM` §E.2 proposes
`ended` but marks it a *Proposal*, so the fix is **open**; the fact is not.

### D9 — Where does the leaver's card go?

> **Early exits:** you leave, or the match is cancelled. Both are terminal states with their own
> cards; neither removes the card immediately, because the explanation is the point.
> — `3.1` §0.2

> Now §8.4 filters `myMatches` on `I hold a seat AND I have not left` — so the card vanishes at
> exactly the moment the player has an open question about money.
> — `R5` §B3

> ### H9. "A match the player left should still show, since the money is still moving"
> — `SPEC` §H, heading only (the section is a list of rules that are *easy to get wrong*)

**§A.0 rules** only that B3 is a **GAP** against the 35 (*"35, and B1/B3 marked as GAPs"*). It
does not say what the leaver sees or whether new keys exist. **Open** — this is #7/#8's call.
`R5`'s reading of the filter is confirmed against `P`; see §4.

### D10 — `vacated` on a refilled match (`DOM` §E.4)

> | `vacated` set on a match with all seats filled | rung 8 fires, card says *"3 of 4 · the seat
> stays funded"* while 4 are seated | **no** — clear `vacated` on refill (`fillSeat` does;
> `syncMatch` does not) |
> — `DOM` §E.4

This row is **incomplete**, not wrong. It describes only the `committedAt != null` case. [EXEC]
with `committedAt == null` the same input falls to **rung 9**, not rung 8, and renders
`protectedBack` — *"a player left before commitment"* over a complete four. `DOM` §E.4 does not
cover that branch and §A.0 says nothing about it. **Open.**

### D11 — `waitlisted` on Now

> **⚠ A waitlisted match cannot appear on Now.** The strip filter requires `mySeat(m)`, and a
> waitlisted player holds no seat. `waitlisted` is reachable only through the gallery and the
> match detail screen. `[VERIFIED]` `[DERIVED]`
> — `SPEC` §E2, Standby group

Confirmed against `P` line 1607: `filter(m => mySeat(m) && !m.left && matchEnd(m)+KEEP_H*HOUR >
S.now)`. No source disagrees. Worth recording because it interacts with `R5` B2: the misrouting
B2 describes is real in the **resolver**, and on the current Now screen it is unobservable for
the same reason the leaver's card is unobservable. Both surface the moment the filter changes.

### D12 — `'You are 2nd on the standby list'`

`P` hardcodes the ordinal in `ST.waitlisted`'s group facet. `R5` §E4 and `UI` §G4 both call it *"a
precise rank for an unobserved event"*. `UI` §G4 recommends `you and five others are on standby`.
**§A.0 is silent** (it is a UI value, and `UI` is final on UI values — but `UI` states a
*recommendation*, not a value). **Open.**

---

## 3. Reachability — can each rung actually fire?

### Method

280 224 fresh match records were pushed through the prototype's own `matchState()`. A key counts
as **structurally reachable** if some input produced it; **operationally reachable** if some input
producing it can be produced by a writer that exists in the prototype (`joinMatch`, `leaveMatch`,
`fillSeat`, `dotransfer`, `syncMatch`, the seed, the scenario rail).

### Result

| Bucket | Keys |
|---|---|
| Reachable, ordinary operation | 30 of 35 — everything except the five below |
| Reachable, but only from a fact combination no writer produces | `protectedCourt`, `protectedLate` |
| Reachable, but the resulting card is then filtered off Now | `formingBack`, `protectedBack` |
| **Not reachable at all — no rung** | `privateFull` |

### `formingBack` / `protectedBack` — `R5` B1 is **refuted against the prototype** (and correct against the documents)

[EXEC] both keys are produced by the live ladder:

```
3 of 4 paid, T−30h, vacated='ola', committedAt=null   ->  protectedBack
2 of 4 paid, T−6h,  vacated='ola', committedAt=null   ->  formingBack
```

The reason is a single line in `leaveMatch` (`P` line 4486):

```js
m.vacated='me'; m.vacatedAt=S.now; m.left=true;
seat.p=null; seat.paid=out.kind!=='reversal';
```

`vacated` is written **before** the reversal/commitment branch, on **every** leave. `leaveOutcome`
returns `{kind:'reversal'}` for `!committedNow(m)`, so a pre-commitment leave produces exactly
`vacated ≠ null ∧ committedAt = null` — the combination `R5` B1 says cannot exist. B1's premise is
`3.1` §1.2's fact table (*"Written when: A committed player leaves"*), which the prototype
contradicts. `DOM` §E.1's `[GAP-E2]` already carries this parenthetically; `R5`'s own headline
does not.

**But B1's second clause is confirmed, and it is the more serious one.** [EXEC]:

```
3 of 4 paid + vacated                       ->  protectedBack
same, refilled to 4 of 4, vacated unchanged ->  protectedBack     <-- rung 9 beats rung 10
same, vacated cleared by hand               ->  full
```

`joinMatch` does **not** clear `vacated` (`P` lines 4459–4482 — verified by string search on the
function body); only `fillSeat` does (`m.vacated=null`, line 4515), and `fillSeat` is the
*replacement-found* path, which is only ever reached from the committed recovery group. A
pre-commitment vacancy refilled by an ordinary join therefore stays pinned in `protectedBack`
indefinitely. [EXEC] `vacatedAt = now − 48 h` still renders `protectedBack`: the 24-hour decay
`3.1` §5 documents (*"24 hours pass with no further change → `forming`"*) has **no mechanism**
anywhere in `P`.

**Third finding, unreported by any source.** `protectedBack`'s copy is *"Three of you are still
paid, so the court stays held until 4h before play"*, but its guard is `isProtected(m)`, which is
also satisfied by a **two-paid `far` soft hold**. [EXEC] at 2 of 4 paid, T−30 h, with `vacated`
set, the card reads `protectedBack` and tells two players that three of them are paid. No source
mentions this.

### `privateFull` — unreachable, and the only key with no rung at all

Rung 7 in full (`P` lines 3978–3980):

```js
else if(m.kind==='private'){
    k = m.openSeats>0?'privateOpen' : m.payModel==='split'?'privatePartial':'privateReserved';
}
```

Three outcomes, four keys. [EXEC] `privateFull` was produced **zero** times in 280 224 records
and appears in the prototype only via the forced gallery. `SPEC` §E2 flags it (*"⚠ `privateFull`
is unreachable through `matchState`"* `[VERIFIED]`); `UI` §B6.3, `DOM` §E.2 and `3.1` all list it
as an ordinary state without comment, and `R5` does not mention it. **It is one of the 35, and it
is the one the ladder cannot produce.**

### `protectedCourt` / `protectedLate` — reachable only from a fact combination nothing writes

Analytically: reaching rung 11c/11d requires `isProtected(m)` with `hold.kind === 'hard'`, and by
elimination `hold.why` must be `'committed'` — `'private'` is caught at rung 7, `'club'` at 11a,
`'full'` at rung 10, and every soft `why` at 11b. Rungs 8–9 must also have missed. So the guard is
exactly:

```
m.committedAt != null  ∧  !isFull(m)  ∧  !m.vacated  ∧  !m.courtLocked  ∧  m.kind !== 'private'
```

[EXEC] a hand-built record with that shape does yield `protectedCourt`. But `committedAt` is
written only by `syncMatch` under `S.now >= d.commit && isFull(m)`, and the only writers that
empty a paid seat afterwards are `leaveMatch` (which sets `vacated` in the same statement) and
`fillSeat` (which fills). No path produces committed-and-short without `vacated`. [EXEC] across
all 89 scenarios, excluding forced records, `protectedCourt` and `protectedLate` were produced
**0** times. `SPEC` §E2's `[VERIFIED]` claim holds; `3.1` §5's IN/OUT tables for both states
describe transitions that cannot occur.

### The scenario sweep, for completeness

Excluding the forced gallery, the prototype's own 89 scenarios produce 20 of the 35 keys at
set-up time. The 15 they do not are reachable but need a user action or a clock scrub the
scenario does not perform (`ready`, `completed`, `playedShort`, `playedNoShow`,
`replacementTransfer`, `cancelledClub`, `formingHeld`, the three untouched `private*`), or are the
five analysed above. This sweep is reported only as corroboration; the fuzz is the reachability
evidence.

---

## 4. Coverage the other way — positions with no context

### The player who left: `R5` B3 is **confirmed**

Two things happen to a leaver, and they compound.

**(a) The card is filtered off Now.** `P` line 1607:

```js
const ms=Object.values(S.matches).filter(m=>mySeat(m)&&!m.left&&matchEnd(m)+KEEP_H*HOUR>S.now)
```

`leaveMatch` sets `m.left=true` **and** clears `seat.p`, so the match fails the filter twice over.
[EXEC], immediately after a leave — committed or not — `mySeat(m) && !m.left` is false. `3.1` §0.2
promises the opposite: *"neither removes the card immediately, because the explanation is the
point."*

**(b) If the card is reached anyway, it addresses the leaver as a stranger.** The match detail
route still resolves, and the non-member rewrite then fires because `mySeat(m)` is now undefined.
[EXEC], leaving a committed match at T−9 h:

```
key: replacement · tag: Replacement pending
  Your share would be 38,00 zł · booking fee 0,00 zł      <-- was "You paid 38,00 zł"
  Their payment stays on the seat, so the court is safe
  The seat is offered at the normal 38,00 zł to compatible players
  They are refunded in full if somebody pays it
```

The person who is owed the money is told what the seat *would* cost them, and is referred to in
the third person as the party being refunded. There is no `key` in the 35 keyed on `m.left`, and
[EXEC] a string search confirms `m.left` is read in exactly one place in the whole file — the Now
filter above.

This matters because the outcome is genuinely undetermined at the moment of leaving.
`leaveOutcome` (`P` lines 1005–1013) returns four different positions — 100 % reversal, 100 % if a
full-price replacement pays, 50 % if a Rescue player pays, and, by omission, 0 % if neither
happens — and `3.1` §8.5 says the leaver was shown all four before leaving. Nothing renders which
one landed.

### Other positions with no context

| Position | Has a context? | Evidence |
|---|---|---|
| Player who left, pre-commitment | **no** | above |
| Player who left, post-commitment | **no** | above |
| Player who **transferred** their seat (`dotransfer`) | **no** | `P` line 4571 sets `m.left=true` without `vacated`; same filter, no key |
| Player who gave the seat away (`gift`) | **no** | same line, plus `m.sponsoredGuest=true` |
| Standby player, match still open | yes — `waitlisted` | but never on Now (D11) |
| Standby player, match played | **wrong context** — `needsResult` / `playedNoScore` | §7 B2 |
| Standby player, match cancelled | **wrong context** — `cancelledClub` etc. | §7 B2 |
| **Second** leaver, when two leave | **no** | `vacated` is a scalar; `R5` B8, `3.1` §9.3 |
| Non-member browsing a match | yes, via the rewrite | `UI` §B6.1 |

---

## 5. The 17-tag ↔ 35-context mapping, verified in both directions

`DOM` §E.2 claims this table. It was **rebuilt from the prototype** and then compared, rather than
copied.

### 35 → 17 (context to tag)

[EXEC] the enumeration in §1 is this direction. Compared against `DOM` §E.2 row by row:
**all 35 rows agree** on tag, tone and `be`, including the four `DOM` bolds (`formingBack` →
`watch`, `heldExtended` → `good`, `rescue`/`rescueLate` → `time`, `inventoryLost` → `bad`).
`DOM` §E.2 splits `Court held` and `Cancelled` across two rows each so that a tone difference is
visible; that is a presentation choice, not a discrepancy.

### 17 → 35 (tag to contexts) — the reverse map, rebuilt

| # | Tag | Arity | Contexts | Tones present |
|---|---|---|---|---|
| 1 | Forming | 4 | `forming`, `formingHeld`, `formingLate`, `formingBack` | `idle` ×3, **`watch`** ×1 |
| 2 | Court held | 2 | `heldSoft`, `heldExtended` | `watch`, **`good`** |
| 3 | Court released | 2 | `heldReleased`, `heldStale` | `watch` ×2 |
| 4 | Court committed | 1 | `clubHeld` | `good` |
| 5 | Court protected | 3 | `protectedCourt`, `protectedBack`, `protectedLate` | `good` ×3 |
| 6 | Full | 1 | `full` | `good` |
| 7 | Confirmed | 2 | `confirmed`, `confirmedOnFill` | `good` ×2 |
| 8 | Replacement pending | 2 | `replacement`, `replacementTransfer` | `watch` ×2 |
| 9 | Rescue active | 2 | `rescue`, `rescueLate` | `time` ×2 |
| 10 | Ready to play | 1 | `ready` | `good` |
| 11 | Needs result | 1 | `needsResult` | `watch` |
| 12 | Confirm the result | 1 | `confirmResult` | `watch` |
| 13 | Completed | 1 | `completed` | `good` |
| 14 | Played | 3 | `playedShort`, `playedNoShow`, `playedNoScore` | `idle` ×3 |
| 15 | On standby | 1 | `waitlisted` | `idle` |
| 16 | Reserved | 4 | `privateReserved`, `privatePartial`, `privateFull`, `privateOpen` | `good` ×4 |
| 17 | Cancelled | 4 | `cancelledIncomplete`, `cancelledCheckpoint`, `cancelledClub`, `inventoryLost` | `ended` ×3, **`bad`** ×1 |

Sum = 4+2+2+1+3+1+2+2+2+1+1+1+1+3+1+4+4 = **35**. ✓

**One-to-many for 10 of the 17 tags**, not 8. `DOM` §E.2's prose states *"one-to-many for 8 of
the 17 tags"*. Counting tags with arity > 1 in the table above: Forming, Court held, Court
released, Court protected, Confirmed, Replacement pending, Rescue active, Played, Reserved,
Cancelled = **10**. This is an arithmetic slip in `DOM` §E.2's prose, not in its table; the table itself is
correct and sums to 35. §A.0 has nothing to say about it.

**Three tags carry a tone split** — `Forming` (`idle` / `watch`), `Court held` (`watch` / `good`)
and `Cancelled` (`ended` / `bad`). Tag alone therefore does not determine the dot colour, which
matters for any `{key, tone, facts}` wire contract. `DOM` §E.2 marks all three in bold.

**`be` is not a function of the tag either.** `Court released` maps to `COURT_RELEASED` for
`heldReleased` and to `RELEASED` for `heldStale`; `Court held` maps to `COURT_HELD` and `HELD`;
`Reserved` maps to four different `be` values. The `be` field in `ST` is **not** the LIFE9
lifecycle — it is a fifteen-value legacy vocabulary. See §6.

---

## 6. Terminal states, illegal transitions, and degenerate inputs

### 6.1 Terminal states (`DOM` §E.3, `3.1` §7.4)

**Terminal, irreversible, card stays 24 h then becomes history:**
`inventoryLost`, `cancelledClub`, `cancelledIncomplete`, `cancelledCheckpoint`.

`3.1` §7.4 lists the same four and their entry conditions. `DOM` §E.3 adds: *"Post-play states are
terminal for the match but `needsResult → confirmResult → completed` still moves."* [EXEC] all
three transitions occur under the resolver, and `playedNoScore` closes the sequence at
`matchEnd + 30 min` regardless.

The 24-hour retention constant is `KEEP_H = 24` (`P` line 3561), applied in the Now filter, not in
the resolver — so a terminal card leaves Now by *filtering*, not by resolving to something else.

### 6.2 Illegal transitions (`DOM` §E.3)

- any terminal → non-terminal
- `committedAt` non-null → null (`3.1` §9.1 inv. 1; `3.1` §1.2 marks the field *"yes — never
  unwritten"*)
- `confirmed` → `full`
- `completed` → `needsResult`

**Caveat found in `P`:** the prototype's own scenario rail violates the second of these. `P` lines
4764 and 4795 both contain `m.committedAt=null` on a match that was committed. These are demo
resets, not product paths, but any conformance test lifted from the scenario rail will inherit
them.

### 6.3 Structurally unreachable, to be asserted (`DOM` §E.3, `3.1` §9.1 inv. 3–4)

```
committed AND no court        — Rule 3 pins the court hard
committed AND soft hold       — Rule 3 promotes it to hard
```

[EXEC] confirmed in `P`: `courtHold()` tests `m.committedAt != null` **third**, above every soft
tier, and returns `{kind:'hard', why:'committed'}` unconditionally. The invariant holds by
construction of `courtHold`, not by any check elsewhere — which is exactly why `DOM` says *assert,
do not assume*.

### 6.4 Degenerate inputs (`DOM` §E.4), each re-run against `P`

| Input | `DOM` §E.4 says | [EXEC] result | Verdict |
|---|---|---|---|
| `seats = []` | `isFull` vacuously true → rung 10 → `ready`/`full` | `isFull: true`, `filled: 0`, key `full` at T−30 h | **confirmed** |
| `vacated` set, all seats filled | rung 8 fires, group facet lies | true **only if `committedAt != null`**; with `committedAt == null` rung **9** fires → `protectedBack` | **incomplete** — see D10 |
| `noShow` on a future match | no effect until `matchEnd` | no effect; rung 5 not reached | **confirmed** |
| `score` before `matchEnd` | ignored until rung 5 | ignored | **confirmed** |
| `waitlisted` **and** holding a seat | rung 6 requires `!mySeat`, seat wins | seat wins | **confirmed** |
| both `formCancelled` and `checkpointCancelled` | rung 3 wins → `cancelledIncomplete` | `cancelledIncomplete` | **confirmed** |
| stale client posts a state key | reject by contract | n/a in `P` | not testable |

Four further degenerate inputs, not in `DOM` §E.4, tested for completeness:

| Input | [EXEC] result | Note |
|---|---|---|
| all four cancellation flags set at once | `inventoryLost` | rung 1 wins, as `3.1` §1.4's second load-bearing ordering requires |
| `now >= matchEnd` **and** `clubCancelled` | `cancelledClub` | cancellation beats play, as documented |
| `noShow` **and** `confirmed` **and** a score, past end | `playedNoShow` | 5a beats 5c; no source states the precedence |
| `committedAt` set on a 1-of-4 match | `protectedCourt` | the impossible input that makes rung 11d reachable (§3) |

### 6.5 The nine canonical lifecycle states, and how they relate

`SPEC` §E3 and `DOM` §D.15 both document `lifeOf(m)` — `FORMING, HELD, RELEASED, FUNDED,
CONFIRMED, AT_RISK, RECOVERING, PLAYED, CANCELLED` (`P` line 6305) — as *"nine states shared
verbatim with the console"*, and the V36 patch comment claims *"The seventeen player tags … are
now derived from these."*

**They are not derived from them.** [EXEC] `lifeOf` is an independent nine-rung ladder over the
same facts; nothing in `matchState` reads it and nothing in `lifeOf` reads `matchState`. Two
consequences worth recording before anyone builds a wire contract on it:

- `lifeOf` ignores `m.forced`, so on the gallery — the only screen that renders all the contexts
  — every context's lifecycle label is computed from the un-shimmed clock and is meaningless
  (`forming`, `cancelledIncomplete` and `playedShort` all report `HELD`).
- The `be` field inside `ST` is a **third** vocabulary, with fifteen values
  (`FORMING, COURT_HELD, COURT_RELEASED, COURT_PROTECTED, HELD, RELEASED, FULL_UNCOMMITTED,
  CONFIRMED, REPLACEMENT_PENDING, RESCUE_ACTIVE, COMPLETED, CANCELLED, RESERVED, PARTIALLY_PAID,
  FULLY_PAID, PUBLIC_SEATS_OPEN`, plus the literal `—` for `waitlisted`). It overlaps LIFE9 on
  five names and diverges on the rest. `DOM` §E.2's column header calls it *"Backend
  (LIFE9-adjacent)"*, which is accurate and is the only place any source acknowledges that there
  are three vocabularies rather than two.

---

## 7. Defects confirmed, with evidence

Each line is a fact about the sources or about executed prototype code. No fix is proposed here.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| **B1a** | *"Rung 9 cannot fire"* | **Refuted for the prototype; confirmed for the documents** | `P` line 4486 writes `vacated` on **every** leave, before the reversal branch. [EXEC] `protectedBack` and `formingBack` both resolve from live ladder inputs. `3.1` §1.2's fact table (*"Written when: A committed player leaves"*) and §3.2's uncommitted-leave row do make it unreachable — so B1 is right about the spec and wrong about the running code |
| **B1b** | *"`vacated` is never cleared … a match that refills would read `protectedBack` forever"* | **Confirmed** | [EXEC] 3-of-4 + `vacated`, refilled to 4-of-4 → still `protectedBack`; only clearing `vacated` yields `full`. `joinMatch` (`P` 4459) does not clear it; only `fillSeat` (`P` 4515) does, and only on the committed recovery path |
| **B1c** | *"The documented 24-hour decay has no mechanism"* | **Confirmed** | [EXEC] `vacatedAt = now − 48 h` still resolves `protectedBack`. No reference to `vacatedAt` exists anywhere in the ladder (`P` 3965–4006) |
| **B1d** | *(new — not in any source)* `protectedBack`'s copy asserts three paid seats; its guard accepts a two-seat `far` soft hold | **Confirmed** | [EXEC] 2 of 4 paid, T−30 h, `vacated` set → `protectedBack` with the line *"Three of you are still paid…"* |
| **B2** | *"A player on the standby list of a played match is asked to enter the score"* | **Confirmed** | [EXEC] `!mySeat`, `waitlists = [id]`, `now = matchEnd + 10 min` → `needsResult`, `post: 1`. At `matchEnd + 30 min` → `playedNoScore`. Rung 5 has no membership test and sits above rung 6. The same input with `clubCancelled` → `cancelledClub`, so B2's extension to the cancellation rungs also holds |
| **B3** | *"There is no state for the player who left"* | **Confirmed** | `P` line 1607 filter is `mySeat(m) && !m.left && …`; `m.left` is read nowhere else in the file's 7 334 lines. [EXEC] after a committed leave the detail card renders `replacement` with the leaver's own money line rewritten to *"Your share would be 38,00 zł"*. `3.1` §0.2 promises a card that stays |
| **B4** | *"`start` is not immutable, so the strip never reorders is false"* | **Confirmed at the spec level; unimplemented in `P`** | `3.1` §6.4: *"A successful Stage 4 moves the entire match half an hour later … the state does not move."* `P` line 1607 sorts on `a.start-b.start`. But `P` never assigns `m.start` — the `time_shift` consent request exists (lines 6357, 6855) and its acceptance changes no field. So the defect is real in the model and latent in the code |
| **B5** | *"Hold-ladder rules 11 and 12 contradict each other"* | **Confirmed — and `R5`'s "unimplemented in shipped code" is wrong for v37** | `3.1` §2.1 rules 11 and 12 quoted verbatim in D6. In `P`'s `courtHold` wrapper (lines 6254–6268) the **stale** test runs first and converts a `{kind:'soft'}` hold to `{kind:'none', why:'stale'}`; the **extended** test only applies to an already-lapsed hold. Rule 11 therefore *does* release a court earlier than the ladder promised, so *"the ladder is a floor"* is false in the shipped code. [EXEC] 2 of 4 paid at T−120 h with a 48 h `maxHoldAge` → `heldStale`, five days before the T−12 h rung. The guard `filled(m) < m.n-1` limits the damage to the `far` tier only |
| **B6** | *"`formingLate`'s two context lines key on a fact that is not stored"* | **Confirmed** | `3.1` §1.2's fact table has no `created` / `createdAt` row (twenty rows, checked). `P` `mkMatch` does store `created` (line 734) and `ST.formingLate` branches on `m.created >= deadlines(m).commit`. [EXEC] both variants render: *"the deadline has passed…"* vs *"it commits as soon as it is complete"* |
| **B7** | *"Two states claim to be the only one where a player loses money"* | **Confirmed** | `3.1` §5 `cancelledCheckpoint`: *"**This is the only outcome in the model where a player loses money**"*. `3.1` §5 `playedShort`: *"The leaver is refunded nothing and their reliability takes the hit."* `3.1` §5 `playedNoShow`: *"No refund, and no search could run."* Three claimants |
| **B8** | *"Two simultaneous leaves are not rare enough to leave unhandled"* | **Confirmed (source-level)** | `3.1` §9.3 states it itself: *"A second `vacated` overwrites the first."* `P` `mkMatch` declares `vacated` as a scalar (`vacated:null, vacatedAt:null`, line 746). No second-vacancy path exists to execute |

### Additional defects found, not attributed to any source finding

| Claim | Evidence |
|---|---|
| `ST_TONE['bad']` is `undefined`, so `inventoryLost` renders a colourless tag dot | [EXEC] `ST_TONE` keys are `good, watch, time, ended, idle`; `inventoryLost` declares `tone:'bad'`. Independently flagged by `UI` §B6.3/§G6.1, `SPEC` §E2 and `DOM` §E.2 `[GAP-E3]` — recorded here because it is the only tone value outside the enum |
| `privateFull` has no rung — the only one of the 35 the ladder cannot produce | [EXEC] 0 occurrences in 280 224 records; rung 7 has three outcomes for four keys. Flagged by `SPEC` §E2 only |
| `ST_ORDER` (the gallery) omits three of the 35 | [EXEC] 32 keys listed; `inventoryLost`, `heldStale`, `heldExtended` missing, and the label *"Cancelled · four contexts"* precedes a list of three |
| `st.cta` and `st.left` are read by `stateCard` and never written by any of the 35 | `UI` §B6.3 `[GAP]` and §G6.4; confirmed by inspection of all 35 `ST` entries |
| `heldStale` prints the club's threshold where the copy promises the hold's age | D7 |
| `lifeOf` ignores `m.forced`, so LIFE9 is wrong for every gallery context | [EXEC] §6.5 |

---

## 8. What remains open

§A.0 settles the **count** (35) and marks B1/B3 as gaps. It settles nothing else in this document.
The following are open, and this file deliberately does not close them:

1. **Which `vacated` write rule is correct** — `3.1` §1.2's *committed leaves only*, or `P`'s
   *every leave*. Rung 9's existence depends on the answer.
2. **What `formingBack` / `protectedBack` should become** once (1) is settled — including whether
   the 24-hour decay is a rung guard, a `syncMatch` write, or nothing.
3. **What the leaver sees**, and whether the Now filter changes. `R5` B3 proposes five new keys;
   `3.1` §0.2 promises a card; nothing rules.
4. **Whether rung 6 moves above rung 5** (and above 1–4).
5. **Whether hold Rule 11 or Rule 12 governs** when they collide.
6. **Whether `protectedCourt` / `protectedLate` are live states or fixtures**, and likewise
   `privateFull`.
7. **The `inventoryLost` tone value** — the defect is unanimous, the fix is a proposal.
8. **The standby ordinal** — `'2nd on the standby list'` vs a pool size.
9. **Which of the three vocabularies** (17 tags, 15 `be` values, 9 LIFE9 states) the wire contract
   carries.

---

### Provenance

Sources read on 2026-08-19, now committed at [`docs/specs/now/`](..):
`rakieta-now-section-ui-spec.md`, `rakieta-now-section-specification.md`,
`now-section-domain-spec.md`, `3.1-enrolled_match_states_and_transitions.md`,
`3-enrolled_match_engine_architecture.md`, `5-now_screen_architecture_review.md`, and
the v37 prototype zip → [`prototype-v37/netlify-deploy/index.html`](../prototype-v37/netlify-deploy/index.html)
(498 698 bytes, 7 334 lines; script block lines 398–7331) — **the netlify build, not the 7 261-line
`rakietaPlayerPrototype.html` the UI spec's line citations resolve against; see
[the set's README](../README.md#the-prototype-two-builds-and-why-that-matters)**. `1-now_screen_production_spec.md` was
present but is cited here only where `DOM` or `R5` quote it, consistent with `DOM` §A.0's
`[GAP-0]`.
