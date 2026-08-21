# ADR-0081 — A seat is never taken until it is paid, and a seat claim is the right to buy one

- **Status:** Accepted
- **Date:** 2026-08-21
- **Upholds:** `CONTEXT.md`'s *"there is no window in which a seat is taken and unpaid by the taker"* — by putting the window somewhere else
- **Completes:** [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)'s open call, which said accepting *"locks the seat for a short payment window"* and left the five minutes as a placeholder
- **Extends:** [ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md)'s cause enumeration, declared complete by [ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md)
- **Answers:** the five-minutes half of [#48](https://github.com/Raketa02/Raketa/issues/48)

## Context

An open call is a race — *a seat just opened, first to take it* — and ADR-0061 settled that first
to accept wins and holds the seat for a short payment window, the card disappearing for everybody
else and returning if the payment lapses. It carried five minutes as a placeholder and named the
money chain as the owner. This is that ticket.

Three things had to be established before the window could be described at all.

**Paying is not instant, and its duration is not ours.** A share is bought from Raketa online —
counter cash is available to invited players on a private court only
([ADR-0059](0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md)), never to a
marketplace seat. So taking a seat means a bank round trip: a six-digit code typed into a banking
app, or a card with a confirmation step. Without a window, two players race through that and one
loses **after** entering their details. With one, a seat three people want is invisible while
nobody is buying it.

**And the obvious word for it is spent twice over.** `CONTEXT.md` already spells a seat's three
states — **paid · held · empty** — where **held** means *a name on a seat and no money*, an
invitation not yet paid, living for hours and given to a player by a person. A payment window is
minutes long and taken by the taker. Worse, a held seat lends its player's level to a match's
forecast, so widening `held` would put a payer's level into a forecast for five minutes and take it
out again when their card declines. **`lock` is unavailable too** — it names the moment a private
court stops being cancellable and nobody may leave
([ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md),
[ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md)), and `withdrawnBeforeLock`
is already a cause on the ledger. **`Claim` alone is spent too** — it is half of the onboarding
assessment's `claim`/`demonstration` pair, *a statement about standing*. So the term is
compounded, exactly as **court hold** is compounded to survive alongside a **held** seat.

**The glossary forbids the window outright.** Its seat entry ends: *"Joining an open match means
paying: there is no window in which a seat is taken and unpaid by the taker."*

## Decision

**We will never let a seat be taken and unpaid. What a player takes while they pay is a seat
claim — the exclusive right to buy one seat, for five minutes.**

### A seat claim is not a seat state

A seat claim is its own short-lived record naming a match, a seat, a player and an expiry. **The
seat is untouched**: still `empty`, still absent from the fill count, still not helping the match hold a
court, still imputed by the forecast rather than carrying the claimant's level. The glossary
sentence survives **word for word**, because nobody has taken a seat unpaid — they have taken the
place in the queue in front of it.

Refused: widening `held` (one word naming two things with opposite lifetimes, opposite origins and
opposite claims on a forecast — the collision that cost a day when *club card* turned out to be two
things), and a fourth seat state (which grows a branch in every place that switches on one,
including the fill count, the forecast, the hold ladder and the card's copy).

### A seat claim is how any seat is taken

**One rule for both doors.** A seat offered to you and a seat you found yourself are the same race
when it is the last one; *offered seats behave differently* is a second rule nobody will remember.
So tapping to take any seat opens one.

**One live claim per player**, so nobody parks three seats across three matches. **Thirty seconds
before the same player may re-claim the same seat** — enough to break a tap-loop, not enough to
cost a mistyped PIN a Saturday game. Nothing else is charged for a lapse: the one mechanism that
would have — the player's score, whose four strands include **payment failures** — is deliberately
dark, and every movement feeding it was withdrawn by
[ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md). It stays the right home for this
the day the score is real, and starting it is not this ticket's to do.

### Five minutes, and a running claim is honoured past the cutoff

**Five minutes from the tap.** Long enough for somebody who is driving, in a shop or on another
court; short enough that a seat offered hours before the match loses nothing meaningful.

**A claim already running is honoured to its end, including past `joinCut`.** A player who taps at
13:29 against a 13:30 cutoff pays at 13:33 and plays. Nobody may **start** a claim after joining
closes. The distinction is the difference between a deadline and a trapdoor, and it costs one
comparison.

**A live claim silences the offer's pending waves; a lapse resumes them.** Nobody is ever buzzed
about a seat that is not takeable at that instant — which is the single failure the offer design
exists to avoid ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md),
[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md)). The mechanism already exists:
ADR-0076 requires a match boundary to be able to silence the channel's pending sends, because
`joinCut` does exactly this. **Nobody is told twice** — a lapse does not re-notify and does not
restart the offer, or one indecisive player buzzes the same four people three times about one seat.

**An expiry is a match wake, not a channel send.** It changes who may take a seat, so it belongs on
the record that owns seats, under `next_wake_at` — and the handler re-derives rather than acting on
the stored reason ([ADR-0076](0076-the-schedule-is-a-column-a-wake-is-a-look-and-there-is-no-list-of-boundaries.md)).

### One rule ends a claim, whatever ended it

**A claim ends when its five minutes run out, when the player abandons it, or when the match itself
ends underneath it** — a club selling the court, a format that can no longer be met, a commit
deadline passed unfilled. There is no second rule for the second case, because there cannot be:
ending a claim on our side cannot catch a bank confirmation already in flight.

### A seat claim is a fact on the card, never a 37th situation

The claimant's own screen has to say so, or the five minutes runs out while they look at a card
counting down to something else. It rides in the **spine**, beside the fit badge and the emphasis
flag — the fields ADR-0070 put there because they are the composition's judgement rather than the
match's:

- **It takes the card's one clock slot.** Not the offer's expiry: *1:30 to pay* is the thing about
  to happen to this player. The offers region's *soonest-to-expire* order reads the same slot, so a
  claim under pressure sorts to the top without a second rule.
- **It lets the card say *finish paying*** — copy, and the client's, like every other sentence
  ([ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)).

**Refused: a 37th situation.** ADR-0072 reached 36 and ADR-0070 made additions cheap, but a claim is
about the **viewer**, not the match — Kuba has one, Zofia does not, same match — and
[ADR-0040](0040-one-ladder-resolves-a-situation.md) fixes that `waitlisted` is *the one* situation
only a viewer can be in. A second would make that sentence a coincidence. **Refused harder: nothing
on the wire**, which is the only option that actually loses the seat, silently.

**This is the second thing to enter ADR-0070's screen-facts slot, and it enters on its own
argument** — the card already has a clock the server fills, and a claim is the one fact that must
own it. The slot is not an invitation, exactly as ADR-0070 recorded when the debt line took it.

### A payment that arrives for a seat that is gone is refunded, and the reason has a name

A bank answers when it answers. A confirmation can land after the claim it was paying for has
ended — because the five minutes ran out and somebody else bought the seat, or because the match
died mid-payment. **The money genuinely moved, so the ledger says so and we give it back**: a
`player → Raketa` movement with cause `shareOnline`, then a compensating `REV-` movement with cause
**`claimLapsed`** ([ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md) — nothing is
amended and nothing is deleted).

**This is the second cause not generated by a terminal situation**, alongside `settlementReopened`,
and for the same reason: it explains a movement the player's current situation does not. ADR-0073
declared the enumeration complete against the 36-situation walk; that walk is still complete, and
this cause was never in its scope.

Refused: **holding the claim open until the bank answers** — which makes five minutes mean *five
minutes, or longer if your bank is slow*, i.e. no deadline for the one player whose bank is
slowest. Refused: **giving the seat to a late payment if it happens to still be free** — the answer
to *is this seat mine* would depend on a race the player cannot see, and two people could be told
different things about one seat inside the same second.

## Consequences

**Easier**

- **Nobody loses at the last step.** The player who tapped first is the player who gets the seat,
  and a declined card costs them the seat rather than the argument.
- **The glossary needs no exception.** *A seat is never taken until it is paid* stays literally
  true, which is what keeps the fill count, the hold ladder and the forecast honest without any of
  them learning a new state.
- **One rule covers both doors and every ending**, so the number of places that must agree about
  what a half-bought seat is stays at one.
- **The claimant's card tells them the truth about their own five minutes**, using a clock slot that
  already exists and a spine that already carries the screen's judgement.

**Harder**

- **A seat three people want can be invisible for five minutes while nobody is buying it**, and
  because Now refreshes only when somebody pulls it
  ([ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md)), they do not see it return the
  instant it does. This is the cost of the choice and there is no version without it.
- **We will refund payments that bought nothing**, with a support conversation attached, and the
  volume is set by how slow the slowest bank is — a number nobody has measured.
- **A new record with a lifetime measured in minutes**, which must be reaped, must not leak, and is
  the first thing in Matches whose expiry is not a match boundary.
- **Nothing punishes a serial claimant beyond thirty seconds and one-at-a-time.** The structural
  limits are the whole defence until the player score exists.

**Neutral**

- `seatOffered`'s exclusive hour above 24 h and a claim are different things at different scales;
  a claim is a sub-interval of that hour and takes the clock while it runs.
- The provider integration that makes any of this real is out of scope; what is fixed here is the
  shape it must satisfy — a claim it cannot extend, and an answer it may deliver late.
