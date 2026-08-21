# ADR-0054 — Now refreshes when it is asked, never on a timer

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md) chose polling over a live
socket and fixed the cadence: *"the client composes on open and on pull-to-refresh, and polls at
**30 s while foregrounded and never while backgrounded**"* — configuration over `focusManager`
and `onlineManager` rather than machinery. The thirty seconds did two jobs: it bounded staleness
without a socket, and it was the reason nothing on the screen ever had to admit being stale.

Two things then moved. [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) settles
that the device holds no rules and no predictive future, so the timer became the *only* thing
keeping a screen honest. And the product owner ruled the timer out for v1 outright: a background
loop pulling the whole screen every thirty seconds is machinery to build, tune, and debug, in
exchange for a freshness nobody asked for on a surface where the player's own arrival is already
the overwhelming majority of the reads.

That is a reversal, not a refinement, and reversing it silently would leave the next session
reading ADR-0038 and building the timer.

## Decision

**We will refresh Now only when something asks. There is no timer anywhere in the client.**

**ADR-0038's polling cadence is superseded. Everything else in that ADR stands** — most of all
the frame protocol written down and deferred in
[`deltas/live-delivery.md`](../specs/now/deltas/live-delivery.md), the four forwards-compatibility
fields, and the named trigger for building the channel. This ADR replaces one clause.

**Four things count as asking, and they are the only four:**

1. **Arrival.** The player opens the app, or switches back to it from another app. Arriving is
   the same event as pulling; treating them as one rule is what stops the first screen of a
   session being the least trustworthy one.
2. **Pull-to-refresh.**
3. **An action.** Joining a match, taking a seat, entering a score. The response to the action
   updates the screen off the player's own tap — no pull required. Per
   [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) this is an **update**, one
   card, never a recompose: order is a property of the composed screen and only a compose may
   change it.
4. **A countdown reaching zero.** The client says *the clock you gave me has run out, and you
   will know more than I do*, and fetches. It decides nothing and renders nothing of its own —
   this is a fetch trigger, not a derivation, and ADR-0053 governs what the client may compute.
   It exists because a visibly expired timer above a live-looking button is the one place where
   *"nothing until asked"* looks broken rather than static.

**The screen still never admits staleness.** ADR-0038's Rule IV holds and the residual is now
bounded by the player's behaviour rather than by us. No card carries a stale marker; no banner
appears; no *"can't reach Raketa."*

**Loading is shown twice, differently.** A **cold open** shows a shimmer over the screen —
nothing is restored from the last launch, so there is no stale card to tap and no offer to
resurrect. A **pull-to-refresh** keeps the current screen exactly where it is and shows a loading
indicator at the top. The distinction is deliberate: a shimmer says *there is nothing here yet*;
the pull indicator says *what you are reading is real and I am checking*. Neither is a staleness
marker.

**`frontend_club/` follows the same rule.** A club sees fresh data when it refreshes; nothing
ticks on a desk laptop either. This is the one place the decision has an unmeasured cost — a
manager watching forty matches has a screen whose staleness affects players other than the
person holding it — and the session that builds the first console screen is where that gets
argued, not here.

**A flag or a settings toggle for the timer is refused**, for ADR-0038's own reason: it pays the
full build cost and ships a path that rots untested.

## Consequences

**Easier**

- There is no loop to write, no interval to tune, no background-vs-foreground gate, no
  interaction between a timer and a mutation in flight. The v1 client gets materially smaller.
- Server load becomes proportional to attention rather than to installs. A phone in a pocket
  costs nothing.
- The four triggers are all *events a player caused*, which makes any freshness bug reproducible
  by describing what the player did.

**Harder**

- **A player who leaves Now open reads a frozen screen.** Someone joining her match, or a seat
  opening, reaches her only when she next arrives, pulls, acts, or a countdown lands. The one
  thing on Now that expires inside a day — an offered seat — is covered by its own notification
  ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md)), which is now carrying more weight
  than it was given for.
- **Rule IV's residual is no longer a number.** ADR-0038 could say *thirty seconds*; we can say
  only *until she asks*. The rule that no card admits staleness is unchanged, but the honesty
  argument behind it is thinner, and that is a conscious trade for v1 simplicity.
- **Two ADRs must now be read together to know how Now is delivered.** The index note is
  load-bearing.

**Neutral**

- Nothing here revives the socket. Sub-second delivery still waits on a feature that earns it on
  its own terms — live scoring, in-match chat, a spectator view.
