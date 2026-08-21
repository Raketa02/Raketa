# ADR-0065 — A seat you asked for pierces a Focus, and we send only when the named seat changes

- **Status:** Accepted
- **Date:** 2026-08-21
- **Amends:** [ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) — its
  *"Both platforms do the same thing"* rule, **narrowed to retraction**; and its recorded
  fallback for the silent update, **replaced**. Its wording rule, its collapse rule, its
  ranking, its tap rule and its no-Inbox rule stand.
  Also narrows [ADR-0052](0052-a-vacancy-is-offered-not-announced.md)'s treatment of
  notification permission as a **binary**.

> **Scope note.** [ADR-0067](0067-the-quiet-replacement-is-evidenced-and-the-extra-message-waits.md)
> narrows this record on two points. The *"Only the count changes"* row below conditions iOS's
> quiet replacement on **[#26](https://github.com/Raketa02/Raketa/issues/26)'s** device
> measurement; that measurement moved to
> [#37](https://github.com/Raketa02/Raketa/issues/37) when #26 split, and the row is otherwise
> unchanged — the extra message ships **off** until that ticket lands, even though the rule
> behind it is now evidenced. And the stated cost — *"`+N more` undercounts on Android"* —
> **understates it for v1**: with the iOS message off, it undercounts on both platforms until
> the named seat changes. The count still prints. Everything else here stands as written.

## Context

[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) settled that a seat a
player **asked for** buzzes and a seat we **chose for them** updates the line silently. It did
not settle how loud the buzz is.

It is 08:00 on Monday and Ania has a Focus on. A seat opens on the Tuesday padel match she is
on standby for. By 11:00, when she next unlocks her phone, the seat is usually gone. **For the
one message Now depends on, the difference between piercing a Focus and not is the value of the
message.**

[#25](https://github.com/Raketa02/Raketa/issues/25) established that Apple's **Time Sensitive**
interruption level is a **self-serve capability needing no Apple approval** — cheaper than
[ADR-0052](0052-a-vacancy-is-offered-not-announced.md) assumed. So nothing technical forces the
answer either way, on either platform. Three facts decided it.

**Apple limits the level by the clock of the event.** The HIG: *"Use the Time Sensitive
interruption level **only for notifications that are relevant in the moment** … make sure the
notification is about an event that's happening now or **will happen within an hour**"*, and
*"**Never** use the Time Sensitive interruption level to send a marketing notification."* A
Tuesday match told about on Monday morning is thirty-five hours away.

**Android has no per-message loudness lever at all.** `interruptionLevel` is iOS-only, and
[#25](https://github.com/Raketa02/Raketa/issues/25)'s field table is explicit that `channelId`
is *"the only Android importance/sound lever"* — there is no per-message alert-once field in
Expo's push API. Loudness on Android is a property of the **channel**, and a channel is a switch
the player can see and throw. Beyond that, channel-level Do Not Disturb bypass requires
**user-granted Notification Policy Access**, a second permission prompt on a phone that already
has to grant `POST_NOTIFICATIONS`. *(Apple's rule is quoted from primary source; the Android DND
fact is the one claim on this record that [#25](https://github.com/Raketa02/Raketa/issues/25) did
not verify — Android's reference pages did not render — and it should be confirmed on
[#26](https://github.com/Raketa02/Raketa/issues/26). If it is wrong, only the "we do not ask"
sentence changes; nothing else on this record rests on it.)*

**Revocation is readable.** `UNNotificationSettings.timeSensitiveSetting` (iOS 15+) returns
`enabled` / `disabled` / `notSupported`. It is invisible to the **server**, but not to the
**client** — which changes "she simply stops getting seats she could have taken" from a fact into
a choice.

## Decision

### The seat is the event, not the match

**Standby offers ship at `interruptionLevel: 'time-sensitive'`, and the justification on record is
the seat's clock, not the match's.** [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)
tells every eligible player at once, first-come, with no exclusive hold — so the thing that expires
within Apple's hour is **the player's chance**, not the fixture. The message is transactional, not
promotional: a seat she explicitly asked to be told about has become available, and it is gone in
minutes.

**The rejected alternative is the one that looks like a compromise.** Gating Time Sensitive on the
*match's* proximity — loud inside some window before Tuesday 19:00, quiet outside it — silences
exactly the Monday-morning case that motivates this record, while silencing nothing that is
actually racing. If we ever cannot defend *the seat is the event* to ourselves, the answer is
plain `active` for every standby offer. **Never a window keyed to the match.**

### The platforms diverge on loudness, and that is not what ADR-0062's parity line was about

**iOS goes loud; Android does what it can.** One channel at `IMPORTANCE_HIGH` — sound and a
heads-up — which **Do Not Disturb still silences**. Ania-on-Android hears nothing at 08:00, and
we accept that.

**We do not ask for Notification Policy Access.** A second permission prompt, for Do Not Disturb
bypass, to win one seat, on a phone that must already grant `POST_NOTIFICATIONS` and cannot be
asked twice ([#25](https://github.com/Raketa02/Raketa/issues/25): two denials on Android are
permanent) — the ask costs more of the pool than the seats it wins.

[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md)'s *"both platforms do the same
thing"* was decided about **retraction**, where divergence bought a second behaviour to maintain
forever and an offer that dies on force-quit. **That rule is narrowed to retraction.** Loudness
diverges for the opposite reason: it costs one field set once and buys a real fill on every iPhone.

### One Android channel

**Not two.** *Seats you asked for* and *seats we found you* as separate channels reads as a
kindness and is a mute switch on rungs 3–7 — the players who never asked, who are therefore
likeliest to throw it, and whom [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)'s
open call depends on. It drains the pool with **no server-side signal that it happened**. One
channel means muting standby costs a player the seats she actually wants, which is the honest
price of the switch.

### We send only when the named seat changes

The **named seat** is the one the line names; the rest are a count.
[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md) ranks a seat asked for above
one we chose, soonest-to-expire inside each group. **That ranking is over the whole live set on
every dispatch, not within one dispatch** — so a chosen seat arriving while a standby seat holds
the line never takes the line, and the server re-sends the winner with a bumped count.

Which makes the count-only update a message in its own right, and Android has no way to send it
quietly. So:

| | What is sent |
|---|---|
| **The named seat changes** | A message, on both platforms. iOS `time-sensitive` if it is a standby seat, `passive` if we chose it; Android the one channel, which alerts |
| **Only the count changes** | **Android: nothing.** iOS: a `passive` collapse-replacement re-stating the named seat — **if and only if** [#26](https://github.com/Raketa02/Raketa/issues/26)'s device measurement proves `passive` genuinely silences a collapse replacement. If it does not, iOS sends nothing either |

**This replaces [ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md)'s recorded
fallback.** *"If it buzzes, every replacement buzzes"* would re-buzz a player about **the seat she
already knows about**, once per unrelated chosen seat — worse than noisy, and the exact
interruption the collapse rule exists to prevent. *Send only when the named seat changes* needs
nothing measured, and it is already Android's behaviour by construction. **So a failed measurement
does not produce a second design: it collapses both platforms onto one identical rule.**

The cost is that **`+N more` undercounts on Android** until the named seat changes. The count is
decoration on a line whose whole job is to make her open Now, where the truth is.

### Revocation is reported, and nothing branches on it

**The client reads `timeSensitiveSetting` and reports it with the push token.** The cascade does
**not** demote a player who has revoked: she keeps her standby priority, still gets the seat, and
still sees the line when she next looks. Demoting her would quietly cost her seats as a punishment
for a settings choice — a worse outcome than the one it prevents.

**It is observability, and that is the point.** If a large fraction of players revoke, this record's
central judgement was wrong, and reporting the setting is the only way we would ever learn it.

This narrows [ADR-0052](0052-a-vacancy-is-offered-not-announced.md)'s treatment of notification
permission as a **binary**: there is a third state, *permitted but downgraded*, in which a player
is counted as reachable and is functionally unreachable inside a Focus. **`notSupported` is a
fourth value and not a synonym for `disabled`** — a player on an iPad was never going to get a
Focus-piercing alert and has refused nothing.

### The one line belongs to offers

The collapse id / tag is keyed to the **player**, so
[ADR-0062](0062-a-notification-is-a-prompt-to-look-not-a-record.md)'s *"one live message per
player, ever"* reads literally: the next kind of message we ever send would silently evict a live
seat from a lock screen.

**It does not.** *One live message* was earned as a **frequency control on offers** — the N−1
fan-out [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md) created was the
problem it solved. **Any future message kind gets its own collapse id and stacks beside the
offer line.** Nothing else sends today ([ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)'s
result confirmation deliberately sends no push), so this costs a sentence now and would be
expensive to discover later.

## Consequences

**Easier**

- **The Monday-morning case works on iOS**, which is the case the whole channel exists for. A
  standby seat reaches a player inside a Focus, at the moment it is worth reaching her.
- **One rule for what gets sent**, on both platforms and in both branches of the device
  measurement: *when the named seat changes*. The measurement now only decides whether iOS gets an
  **extra** quiet message, never what the product does.
- **The Apple capability is settled**, which makes
  [#26](https://github.com/Raketa02/Raketa/issues/26) one visit to the console rather than two.
- **One Android switch**, so a player who mutes us makes one decision with visible consequences,
  rather than silently starving the cascade.

**Harder**

- **Android is a quieter product than iOS**, permanently and by choice. A player in Do Not Disturb
  gets nothing until she looks, and the fix we declined is a permission ask.
- **`+N more` undercounts on Android**, so the two platforms show different numbers on the same
  facts.
- **The Time Sensitive justification is a judgement, not a fact.** *The seat is the event* is
  defensible and is not what the HIG's example describes. If App Review disagrees, the fallback is
  `active` and the Monday-morning case is lost.
- **We now hold a per-player setting we deliberately do not act on**, which will look like an
  oversight to anyone who finds it before they find this record.

**Neutral**

- The wording, the collapse rule, the ranking, the tap-re-reads rule, the *"That seat has gone"*
  line and the absence of an Inbox are untouched. This record governs **how loud a message is and
  when one is sent at all**.
- The transport is untouched: `interruptionLevel` and `channelId` are both plain fields on Expo's
  push API and on bare APNs/FCM alike ([#25](https://github.com/Raketa02/Raketa/issues/25)).
