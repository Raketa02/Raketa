# ADR-0031 — The hold ladder is a floor at a given level of certainty

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

`3.1-enrolled_match_states_and_transitions.md` §2.1 publishes two hold rules that contradict
each other outright:

> | **11** | A club may set a maximum age for a soft hold | club setting, not a marketplace rule |
> | **12** | A club may hold **longer** than the ladder promises, never shorter | the ladder is a floor |

Rule 11 shortens a hold that Rule 12 says may never be shortened. The architecture review
(`5-now_screen_architecture_review.md` §B5) names the conflict and calls it *"a live decision
rather than a bug in shipped code"*, on the grounds that §9.3 lists both rules as specified but
unimplemented.

**That is wrong for v37.** Executing the prototype
([`Raketa02/Raketa#5`](https://github.com/Raketa02/Raketa/issues/5)) showed the V36 ecosystem
patch implements both, and implements them in the order that resolves the conflict in Rule 11's
favour: in `courtHold` (`netlify-deploy/index.html` lines 6254–6268) the **stale** test runs
first and converts a `{kind:'soft'}` hold to `{kind:'none', why:'stale'}`, while the **extended**
test only ever applies to an already-lapsed hold. A match at 2 of 4 paid, at T−120 h, under a
48-hour `maxHoldAge`, resolves `heldStale` — the court goes back on sale **five days** before the
ladder's own T−12 h rung would have released it. *"The ladder is a floor"* is false in the
running product.

The same function states the rule it is breaking. Three lines below the stale branch:

```js
/* demand-aware holding may only ever EXTEND. It is never allowed to release
   a court earlier than the ladder promised. */
```

Two further facts about the shipped implementation matter to the decision. The stale test is
guarded by `filled(m) < m.n-1`, so it can never fire on a match that is one seat short — a limit
nothing in the sources describes as deliberate. And it measures `(S.now - m.created)`, the age of
the **match**, while the copy it renders (*"a soft hold older than {age} h goes back on sale"*)
promises the age of the **hold** — and then prints `P.maxHoldAge`, the club's threshold, so a
hold that has sat 71 hours under a 48-hour cap reports *"48 h"*.

`rakieta-now-section-specification.md` Invariant 4 is the constraint the ticket nominated to
settle this: *a court is held in proportion to certainty, and the bar rises.*

The alternatives considered:

**Rule 12 governs; Rule 11 is narrowed to capping `heldExtended`.** A club may cap only the
generosity it granted itself, never the ladder's own hold. This keeps the floor absolutely and
is the reading that requires no restatement of anything. It also means a speculative hold on a
peak court can sit at 2 of 4 for a week and the club has no instrument to reclaim it, which is
the situation Rule 11 was written to address.

**Rule 11 governs and Rule 12 is deleted.** Honest about the shipped behaviour, and it discards
the one guarantee that makes a hold worth anything to the marketplace: without a floor, a club
may release at any moment and the ladder's promise is advisory.

**Rule 11 governs and Rule 12 is restated.** The one that survives contact with Invariant 4 —
see below.

## Decision

**We will let Rule 11 govern, and restate Rule 12 as: a club may hold longer than the ladder
promises, and never shorter *at the same level of certainty*.**

The two rules are not in conflict once it is seen that they price the same invariant on two
different axes. The ladder holds a court on the *premise* that certainty will rise. A match that
has sat at two paid seats for seventy-one hours has falsified that premise: releasing it is not
dropping below the floor, it is the floor's own condition failing. Invariant 4 says the bar
rises; a stale hold is one where it did not. Rule 11 measures certainty by elapsed time, the
ladder measures it by seats, and both are the same invariant.

**We will keep the `filled < n−1` guard, and specify it as deliberate.** A match one seat short
is never stale, whatever its age, because certainty *has* risen — that is precisely the level at
which the floor binds. What the shipped code arrived at accidentally becomes the rule: staleness
may reclaim a `far`-tier hold and may never touch a `near`-tier one.

**We will measure `maxHoldAge` from `heldSince`, not from match creation.** Rule 11 caps the
*hold*, and the reframing above is *certainty has not risen since we started holding* — so the
clock starts when the hold is first granted, not when the match was posted. A match that spent
sixty hours at one paid seat and then earned a hold has a fresh hold and an old match; under
match-age it is stale on arrival, which punishes exactly the match that just improved.
`heldSince` is a new stored fact: written when a hold is first granted, cleared when it lapses,
and rewritten if a hold is granted again.

**We will print the hold's real age.** `heldStale`'s copy promises the age and must render
`now − heldSince`, not the club's threshold.

**A hold that regains certainty is no longer stale.** Staleness is evaluated on the current
facts, not latched. A third payment on a stale 2-of-4 match takes it to `n−1`, the guard closes,
and the hold is live again — which is the answer to the question of what a payment landing after
a club's declared cap has lapsed should do. It re-earns the hold rather than arriving too late
for one.

## Consequences

**The marketplace's hold promise is now conditional, and the condition is legible.** A player
reading *"held until 4 h before play"* is reading a promise that holds while the match keeps
earning it. That is weaker than the sentence they see, and the copy must not overstate it — the
`heldStale` card is the place the weakening becomes visible, which is why its age must be true.

**`heldSince` is a new persisted fact on a context that is not modelled yet.** It has to exist in
the Matches aggregate from the first commit rather than be reconstructed later, because it cannot
be derived: nothing in the event history distinguishes *the hold was granted at T* from *the
second seat was paid at T* once a seat has since been vacated and refilled.

**Clubs gain a lever that can hurt the marketplace, and nothing here bounds it.** A club may set
`maxHoldAge` to one hour and functionally opt out of speculative holding altogether. Whether the
platform floors the value, and who authors it, is ClubPolicy's decision and is deliberately not
made here.

**`5-now_screen_architecture_review.md` §B5's premise is corrected in this repo but not in the
document.** The review says the rules are unimplemented; they ship. The document is an authority
we do not edit, so this ADR is the correction, and anyone reading B5 against v37 will find the
review understating the finding.

**Staleness being re-evaluable rather than latched means a card can go back.** `heldStale` →
`heldSoft` is a legal transition under this decision, and it reads as the court being un-released.
The alternative — latching the release — would mean a match that reached three paid seats still
showing a released court, which is worse. Any conformance suite that assumes hold state moves in
one direction is wrong.

**This does not settle who authors `maxHoldAge`, what it defaults to when absent, or whether a
club may set it at all.** Those are ClubPolicy, still unspecified on the map.
