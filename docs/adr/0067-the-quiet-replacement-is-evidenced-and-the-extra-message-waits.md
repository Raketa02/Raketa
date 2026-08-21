# ADR-0067 — The quiet replacement is evidenced, and the extra message it buys waits for APNs

- **Status:** Accepted
- **Date:** 2026-08-21
- **Amends:** [ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) — **lifts the
  one rule it accepted provisionally**, and corrects two things in the reasoning around it. Its
  wording rule, its collapse rule, its ordering, its tap-re-reads rule and its no-Inbox rule are
  untouched. Also narrows
  [ADR-0065](0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
  on one pointer and one cost.

## Context

[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) shipped one rule
provisionally: that `interruption-level: passive` genuinely silences an `apns-collapse-id`
**replacement**. Apple documents each field and has never documented the two together, so the
record said outright that the answer is *"a fact about devices"* and named the measurement it
was waiting for.

[#36](https://github.com/Raketa02/Raketa/issues/36) went looking for that fact and found the
door shut. `xcrun simctl push`'s entire published contract is a bundle id and a JSON body — no
headers channel exists for `apns-collapse-id` to travel in, and ten pushes across four payload
placements produced ten fresh random identifiers. That is structural, not a missing flag.

**But it was the wrong door.** Apple documents that a remote `apns-collapse-id` *becomes* the
[`UNNotificationRequest.identifier`](https://developer.apple.com/documentation/usernotifications/unnotificationrequest/identifier)
— *"If you use the same identifier when scheduling a new notification, the system removes the
previously scheduled notification with that identifier and replaces it with the new one."* So
#36 drove that field directly. Backgrounded, fully authorized: a live identifier reposted at
`passive` produced **no banner destination and `canTurnOnDisplay: 0`**; the *same* identifier
at `active` produced both. **The interruption level is evaluated on the delivered notification
regardless of whether it is a first post or a replacement.**

What that does not exercise is **APNs**. The two paths share the daemon, the request object,
the identifier semantics and the SpringBoard destination logic, and Apple does not document
that they make the presentation decision at the same point — there is no Apple page on
Simulator notification fidelity at all. #36's own words: **strong evidence, not proof.**

### What is actually at stake is one quiet message

The framing this decision arrived in was that ADR-0062's *fallback* branch had become the
unevidenced one. It had — but that fallback was already gone.
[ADR-0065](0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)
withdrew it: *"if it buzzes, every replacement buzzes"* would re-buzz a player about **the seat
she already knows about**, which is the exact interruption the collapse rule exists to prevent.
What replaced it — *send only when the named seat changes* — needs nothing measured and is
already Android's behaviour by construction, so a failed measurement collapses both platforms
onto one identical rule rather than producing a second design.

ADR-0065 states the consequence plainly: **the measurement now only decides whether iOS gets an
*extra* quiet message, never what the product does.** Concretely, one behaviour hangs on it —
whether iOS refreshes the `+N more` count when a chosen seat arrives while a standby seat holds
the line. Android already declines that message and the undercount is already accepted.

So the question is not whether to bet the product on a proxy. It is whether the map carries a
**provisional** decision into a destination defined as *"every decision settled and written
down"* — while the unmeasured branch changes no behaviour a player can observe.

## Decision

### The rule is evidenced, and ADR-0062 is no longer provisional

**We will treat #36's identifier-path measurement as sufficient.** ADR-0062's silent-update
rule stands as accepted without qualification, and its provisional paragraph is spent. The
`.p8`, the console visit and the iPhone on [#37](https://github.com/Raketa02/Raketa/issues/37)
are still owed — but they are owed for provisioning and for a **confirmation with a prior**,
not for a decision the map is missing.

### What made this proxy sufficient, stated so the next one can be argued

Three conditions held together, and we record them because this map will meet the shape
again — a fact measurable only through a proxy, on a platform whose vendor declines to document
the equivalence:

1. **The vendor documents the identity between the two paths.** Not a resemblance we inferred:
   Apple states that the remote header *becomes* the local field. The proxy drives the same
   property, not an analogue of it.
2. **The mechanism under test is shared, and the divergence would have to be in a part neither
   path owns.** Same daemon, same request object, same destination logic.
3. **The failure branch costs nothing.** If APNs disagrees, the conservative behaviour is
   already built, already Android's, and already what ships.

**All three, or it does not lift.** Condition 3 is the one that does the work: a proxy is
enough when being wrong is cheap, and this bar is not a general licence to measure things
sideways. It has one instance, which is why it lives here rather than in a record of its own.

### The extra message stays off until the hop is measured

**Believing the rule and shipping the message it buys are two acts, and we separate them.**
The iOS count-refresh on a count-only change ships **off**, exactly as
[ADR-0065](0065-a-seat-you-asked-for-pierces-a-focus-and-we-send-only-when-the-named-seat-changes.md)'s
table already conditions it — the pointer there reads
[#26](https://github.com/Raketa02/Raketa/issues/26) and should read
[#37](https://github.com/Raketa02/Raketa/issues/37), which is where that measurement went when
#26 split. #37 flips it on.

The asymmetry decides it. If the APNs hop diverges, shipping it on buzzes a player about a seat
she already knows about — the failure ADR-0062 and ADR-0065 both exist to prevent. Shipping it
off costs a stale count on a line whose whole job is to make her open Now, where the truth is.
It also gives #37 a result that *changes* something, which a pure confirmation otherwise lacks.

### `+N more` prints anyway

Under the line above, the count undercounts on **both** platforms in v1, not only on Android as
ADR-0065 recorded it. **It prints unchanged.** Dropping it would make the lock-screen line's
*shape* depend on a measurement, so #37 would return as a copy change and a layout change
rather than a flag flip — the second design ADR-0065 spent its argument avoiding. Rewording it
to something unfalsifiable (*"and others"*) was refused: that is a permanent vagueness bought
to cover a temporary gap, against a record whose whole premise is that the line is true.

The failure is quiet and in the right direction — an undercount hides seats, and a hidden seat
sends her to Now.

### Two corrections to ADR-0062's reasoning, neither of which changes its rule

1. **Its recorded fallback is superseded, not merely unevidenced.** ADR-0062 reads *"if it
   buzzes, the fallback is that every replacement buzzes."* ADR-0065 replaced that with *send
   only when the named seat changes*. A reader arriving at ADR-0062's paragraph today should
   take the fallback from ADR-0065 and the confidence from here.
2. **Its *"Apple switches that off during testing"* worry cites the wrong mechanism.** That
   sentence points at the **silent-push power budget** — *"These limits are disabled when
   testing your app from Xcode"* — which is a statement about background delivery rate limits.
   **Apple documents no development-time override of notification presentation.** The hazard is
   real where ADR-0062 first found it, in the removal path it rejected; it does not obviously
   apply to `interruption-level` at all.

## Consequences

**Easier**

- **The map carries no provisional decision into its destination.** The push branch is settled
  on evidence rather than on a purchase nobody has made.
- **[#37](https://github.com/Raketa02/Raketa/issues/37) is de-risked without being skipped.**
  Its first measurement becomes a confirmation against a stated prior, which is a cheaper thing
  to hold an iPhone for, and it keeps a real job: flipping the count-refresh on.
- **A failed APNs measurement now costs nothing at all.** Before this record it would have
  triggered a fallback design; after it, it leaves a flag off.

**Harder**

- **We have accepted a rule on a measurement of a path we do not ship.** If Apple ever decides
  presentation at a different point over APNs, this record is the one that was wrong, and the
  cost lands on players as an unwanted buzz rather than on us as a build failure.
- **`+N more` undercounts everywhere in v1**, and the record that states the undercount as an
  Android cost (ADR-0065) now understates it. Somebody reading only ADR-0065 gets a smaller
  number than the truth.
- **Two acts that look like one are deliberately kept apart** — the rule is believed and the
  message is off — and that reads as hedging until the asymmetry is read with it. It is the
  kind of thing a later session tidies away by switching the flag on "since it's decided
  anyway."
- **A stated bar with one instance invites over-application.** Condition 3 is load-bearing and
  is the one most easily dropped: a proxy measurement behind an expensive failure branch is not
  this decision, whatever the first two conditions say.

**Neutral**

- Nothing about what a notification *claims* moves. ADR-0062's past-tense wording, its
  one-live-message collapse, its ranking, its tap-re-reads rule and its refusal of an Inbox
  line are untouched, as is ADR-0065's Time Sensitive decision and its one Android channel.
- The provisioning work is unchanged in both halves.
  [#26](https://github.com/Raketa02/Raketa/issues/26) stays ungated and takeable;
  [#37](https://github.com/Raketa02/Raketa/issues/37) still waits on the Apple Developer
  Program membership, and still must be worked before the first build leaves the team.
