/**
 * **Live · not live · held** — what the room says about itself, folded from the channel and the
 * account.
 *
 * ## Why this is `domain/` and not three lines in the screen
 *
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §2.3 puts
 * it here by name, and the falsifier it gives is *"a not-live line on a cold open, before any
 * connect attempt has failed"*. Both of
 * [ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
 * §8's conditions — **only in the foreground, and only after a connect attempt has failed** — are
 * exactly the kind that survive a first build inside a component and get quietly dropped by the
 * second, because nothing about a `status === 'lost'` check looks incomplete. Here they are two
 * arms of a `switch` a test can drive.
 *
 * **The one place *never on a cold open* is deliberately not honoured is a phone with no signal**,
 * and the two halves of #365 are what settle it: *a severed stream, a dead subscriber, a Redis
 * outage and a phone with no signal all produce the same thing* is an acceptance criterion, and it
 * would be false if a room opened offline said nothing. The rule against a cold-open line is about
 * a **flash during a handshake** — §3.6's *or every open flashes it* — and offline is not a
 * handshake: `onlineManager` has already established that no attempt can succeed, so the port
 * reports `lost` without making one. Nothing here decides that; it is stated here because this is
 * where the rule it bends is written down.
 *
 * ## The three states are not three facts about one thing
 *
 * **Not live is about reading and held is about writing**, and they can both be true — a held
 * account on a phone with no signal. §3.6 asks for **one** note above the composer, so this fold
 * picks, and it picks the one that closes a control: *held*'s own sentence already promises that
 * reading works, which is the whole of what the *not live* sentence would have added.
 *
 * **`live` is not a claim, it is the absence of one.** It is what the fold answers whenever there
 * is nothing to say — an open channel, a channel still opening, and a channel deliberately closed
 * behind a backgrounded app are one answer, because in all three the honest thing to draw is
 * nothing.
 *
 * ## The held arm is unreachable in this build, and that is recorded rather than hidden
 *
 * **Nothing on this platform can open a case.** `account_held` is a real backend refusal on every
 * write — the send, the three slot writes and the lock — but the hold query's only registered
 * implementation is the null object, so
 * no account can be in one and `make seed` cannot put one there
 * ([`backend/app/seeds/plans.py`](../../../../../backend/app/seeds/plans.py) says the same thing
 * from the other side). This is a **named exception** to the map's reachability constraint rather
 * than an oversight: the arm exists because the wire can produce it, `liveState.test.ts` and
 * `roomLiveness.test.tsx` are what drive it, and the day a case can be opened neither the fold nor
 * the screen changes.
 *
 * **What the exception costs, stated where the next person will find it:** the pre-emptive half of
 * §3.6 — *you never tap into silence and you are never told off for having tapped* — is bought
 * with **one** tap in this build, because no read on this API serves the hold and the only signal
 * is a refusal. {@link writeStanding} is where that is written down and where a read would replace
 * it.
 */

import type { AppError } from '@/shared/errors';
import type { LiveStreamStatus } from '@/shared/lib/platform';

/** What the account may do here — **reading is never in question** (ADR-0148 §9). */
export type WriteStanding = 'ordinary' | 'held';

/** What the room draws about itself. Exactly one of the three, always. */
export type LiveState =
  /** Nothing to say. An open channel, one still opening, and one closed for the background. */
  | 'live'
  /** A connect attempt has failed and the reader is looking at the room. One amber line. */
  | 'not-live'
  /** The account cannot write. One amber note, and every control that writes greyed under it. */
  | 'held';

/**
 * The one fold, over the channel's own standing and the account's.
 *
 * A `switch` over the port's union rather than a chain of booleans, so a status added to the
 * channel fails to compile here — which is the one place a new one has to be answered.
 */
export function liveState(stream: LiveStreamStatus, writing: WriteStanding): LiveState {
  if (writing === 'held') return 'held';

  switch (stream) {
    case 'lost':
      return 'not-live';
    case 'connecting':
    case 'live':
    case 'closed':
      return 'live';
  }
}

/**
 * **Whether the account may write here**, read off the refusals that are the only thing that says
 * so.
 *
 * A hold reaches this client exactly one way: `account_held`, a `403` on a write. **No read
 * serves it** — not `GET /conversations/{id}`, not the authenticated player — so there is nothing
 * to ask before the first tap, and this is the honest producer rather than the one §3.6 describes.
 * The moment a read carries the fact, this function takes it instead and nothing above it moves.
 *
 * **Every write on the screen is a producer, and the fold takes all of them.** A hold is a fact
 * about the account rather than about the act that met it, so the send, the three slot chips and
 * the lock are five ways of learning one thing — and a room that folded only its own send would
 * draw a coral *something went wrong* under a plan write while the composer beside it stayed
 * open, which is the one fact said in two registers that the amber note exists to prevent. The
 * plan's refusals arrive off the mutation cache through `features/plans`' public surface, which is
 * how the room already reads what it is still sending.
 *
 * It is a **derivation and not a stored flag**, which is what keeps it from being a second store —
 * and what that costs is stated rather than glossed: a refusal lives exactly as long as the
 * mutation that got it, so **leaving the room and coming back ungreys everything and the player
 * taps into the hold again.** For the send that is the moment the room unmounts; for a plan write
 * it is the mutation cache's own `gcTime` after the card lets go of it, since the cache is what
 * the room reads the plan's refusals off — so a hold met on the card outlasts a walk away and back
 * by a few minutes, and then repeats exactly as the send's does. Nothing in this build can lift a
 * hold, so that repeat is a lie about the account rather than a stale reading — and it is still
 * the honest shape, because the fix is a read that serves the fact and not a flag this client
 * keeps about a state it cannot see.
 */
export function writeStanding(refusals: readonly (AppError | null | undefined)[]): WriteStanding {
  return refusals.some((refusal) => refusal?.code === 'account_held') ? 'held' : 'ordinary';
}
