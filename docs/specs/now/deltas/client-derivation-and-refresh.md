# Spec delta — what the client holds, and when the screen changes

**Governs over** `3-enrolled_match_engine_architecture.md` §4.1 (*"The client has the kernel"*)
and §4.2 (the three-layer render), `5-now_screen_architecture_review.md` **A6** (the transition
list), and the polling row of [`live-delivery.md`](live-delivery.md) §1. Everything else in all
three stands unchanged.

**The decisions:** [ADR-0053](../../../adr/0053-the-phone-holds-no-rules-and-only-subtracts.md) —
the phone holds no rules; its only power is subtracting. And
[ADR-0054](../../../adr/0054-now-refreshes-when-asked-never-on-a-timer.md) — Now refreshes when
it is asked, never on a timer.
**The reasoning:** [`Raketa02/Raketa#22`](https://github.com/Raketa02/Raketa/issues/22).

**No document in `docs/specs/` is edited.** This is delta kinds **(3) the build** — §4.2's layer
2 is not built — and **(5) the reversal**: A6's fix and `live-delivery.md`'s cadence are
withdrawn, not narrowed.

---

## 1. §4.1 — the client does not have the kernel, and gets nothing in its place

`§4.1` opens *"The kernel package ships to the server and both applications. That is already
established"*. Doc 5 A6 already ruled that premise **rejected**
([ADR-0021](../../../adr/0021-kernel-in-backend-clients-derive-by-comparison.md): the backend is
Python and cannot run in Expo). A6 then kept the *intent* and proposed a replacement. **The
intent is withdrawn too.**

`§4.1`'s table collapses to one row:

| §4.1 as written | What governs |
| --- | --- |
| Client may **re-derive the state from `card.record`** when a push is late | **Never.** No rules ship to any client, in any form |
| Client may **tick a countdown** | **Yes — and this is the whole permitted surface.** §3 below |
| Client may **flip optimistically at a predicted threshold** | **Never.** A countdown reaching zero does not change the card; it triggers a fetch (§4) |
| Client may **render correctly offline** | **No.** Offline, the client renders the last screen it asked for, unchanged |
| Client may **never write a derived value / send a conclusion / outrank a push / skip reconciliation** | Unchanged, and now vacuous — there is no derived value to write and nothing to reconcile |

*"Commands carry intent — `join this match` — never conclusions"* is **unchanged and still
load-bearing.**

## 2. §4.2 — there is no layer 2, so there are three fewer things to build

| §4.2 as written | What governs |
| --- | --- |
| 1. A push arrived → render the server's card. Authoritative | The **only** layer. A response arrived → render it |
| 2. `nextTransition` passed, no push within 3 s → re-derive locally, render, **mark provisional** | **Not built.** Nothing is derived locally, so nothing is provisional and nothing is marked |
| 3. A push arrives later → replace. Server always wins | Vacuous — there is never a client card for a server card to beat |

*"Layer 2 is what makes the screen feel instant… and correct in a basement"* — the basement case
is **not solved by a worse mechanism; it is not solved.** A player with no signal sees the last
screen she asked for and can see it is not moving. The instant-feeling half survives on the one
thing that still moves: the countdown.

## 3. A6 — the transition list is refused, and the card names its own moment instead

| Doc 5 A6's fix | What governs |
| --- | --- |
| `nextTransition: {at, becomes}` → `transitions: [{at, key, tone, facts}]` | **Refused.** The list solves offline threshold-crossing, and nothing crosses a threshold unprompted |
| The client crosses *several* thresholds offline holding no rule | The client crosses **none** |

*(A6's `{key, tone, facts}` shape was independently superseded by
[the state-vocabulary delta](state-vocabulary.md) — `{situation, facts}`, no tone. Both
corrections apply; neither rescues the list.)*

**What replaces it:** a card carries **the one moment it is about**, as an instant — the confirm
deadline, the start time, the offer's expiry — and the client subtracts. This is **not**
`nextTransition`: the moment a card is *about* and the moment a card next *changes* are routinely
different, and pointing a countdown at the latter drifts the number away from the words above it
(*"Starts in 15 min"* counting down to a commit deadline). **Naming the field belongs to the
`GET /now` wire contract**, which is unwritten.

`nextTransition` still ships, per
[ADR-0038](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md)'s
forwards-compatibility rule, and now has **no reader and no prospect of one**. So does
`serverTime`: the countdown runs on the device's own clock, uncorrected — server-side correction
was considered and refused as an edge case a network-synced phone does not produce.

## 4. `live-delivery.md` §1 — the cadence

| [`live-delivery.md`](live-delivery.md) §1 as written | What governs |
| --- | --- |
| *"The client polls at **30 s while foregrounded**, never while backgrounded — `focusManager` / `onlineManager` gate it"* | **Withdrawn.** No timer anywhere in the client |

**Four things count as asking, and they are the only four:**

1. **Arrival** — the app is opened, or switched back to from another app. The same rule as a
   pull, so the first screen of a session is not the least trustworthy one.
2. **Pull-to-refresh.**
3. **An action** — joining, taking a seat, entering a score. The response updates the screen off
   the player's own tap. Per
   [ADR-0032](../../../adr/0032-order-is-a-property-of-the-composed-screen.md) this is an
   **update** — one card — never a recompose, so the screen does not reshuffle under a thumb.
4. **A countdown reaching zero** — *the clock you gave me has run out, and you will know more
   than I do.* A fetch trigger, not a derivation.

Everything else in `live-delivery.md` is unchanged: the frame protocol stays written down and
unbuilt, and the trigger for building it is still a feature needing sub-second delivery on its
own terms.

## 5. Loading, and staleness

**Rule IV is unchanged** — *the read is the truth* — and **no card admits staleness**: no marker,
no dot, no *"updating…"*, no banner, no *"can't reach Raketa."* The residual is no longer a
number: ADR-0038 could say *thirty seconds*, and this says *until she asks*.

Loading appears twice and differently, and neither is a staleness marker:

| Moment | What she sees |
| --- | --- |
| **Cold open** | A shimmer over the screen. **Nothing is restored from the previous launch** — so no stale card is tappable and no dead offer is resurrected |
| **Pull-to-refresh** | The current screen stays exactly where it is, with a loading indicator at the top |

A shimmer says *there is nothing here yet*; the pull indicator says *what you are reading is real
and I am checking*.

## 6. The withdrawn offer

The client cannot know an offer has expired — it has no clock and no rules. In practice the
withdrawal happens when the player reaches for it: the action's own response replaces **that
card** with what is true (*"Zofia took that seat"*). The client never *starts* offering something
the server did not offer; it may only stop.

## 7. `frontend_club/`

Same rule, stated separately rather than inherited
([ADR-0005](../../../adr/0005-three-app-monorepo-ownership-boundaries.md)): a club sees fresh data
when it refreshes, nothing predictive ships to the console, and nothing ticks. The console's own
reason differs — it is a page redeployed at will, whereas the entire argument for shipping a phone
a field early is that a phone cannot be forced to update. **The unmeasured cost lands there**: a
manager watching forty matches holds a screen whose staleness affects players other than herself.
That is argued by the session that builds the first console screen, not here.
