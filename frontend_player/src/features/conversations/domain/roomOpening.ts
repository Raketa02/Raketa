/**
 * **A room on its way** — the two numbers behind waiting for the door a challenge's acceptance
 * opens.
 *
 * ## The room is opened after the accept has answered, and never by it
 *
 * `POST /challenges/{id}/accept` returns the challenge as it now stands and says nothing about a
 * conversation, because `challenges` may not know one exists (ADR-0146). The room is opened by
 * the **teller**, which hears `SeatAccepted` off the outbox and writes the room over the delivery
 * batch's own session
 * ([ADR-0110](../../../../../docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md),
 * `conversations/application/telling.py`). The outbox is polled — `EVENT_DELIVERY_POLL_INTERVAL_SECONDS`,
 * one second by default — so the list re-read the accept invalidates can land **before the room
 * exists**, and a screen that pushed the door on that one read would push nothing on most taps.
 *
 * ## So the door is waited for, briefly, and the wait has a bound
 *
 * `I'm in` is the one act in the app whose whole point is a room to talk in, so the screen keeps
 * re-reading the list until the join answers (`useAwaitedChatDoor`) — on a cadence a little
 * under the outbox's, because a poll slower than the thing it is waiting for adds a whole tick
 * to every wait — and gives up at a bound rather than for ever. A room that has not opened by
 * then is a delivery worker that is down or behind, and it opens whenever that worker catches up:
 * the screen still draws the door when the list next lands, so nothing is lost but the push.
 *
 * **This is not Play's rule bending.** *Nothing in Play background-refetches* is about a ranked
 * list moving under a finger; this is a list of rooms, re-read on the player's own press, stopping
 * on the answer, and bounded.
 */

/** How often the list is re-read while the room is expected. Under the outbox's own second. */
export const ROOM_OPENING_POLL_MS = 750;

/**
 * How long the room is given before the screen stops asking. Several outbox ticks, so a worker
 * that is merely behind still answers; and short enough that a worker that is down does not
 * leave a screen polling for a minute over a press the player made once.
 */
export const ROOM_OPENING_BOUND_MS = 6000;

/**
 * **The bound runs from the first answer after the wait began**, and not from the wait's own
 * beginning. The room is given six seconds to be written *after the list has been heard from*:
 * the wait is about a worker that is behind, and a list that is slow to answer at all — a cold
 * cache, a poor connection — is not charged against it. On a warm phone the two instants are a
 * few hundred milliseconds apart and the bound reads as the record's six seconds from the yes.
 *
 * Stated because it is also what lets the wait be seen under test: the screen that waits is
 * pushed the instant a yes is answered
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1), and the router harness runs every pending timer on every navigation, up to the longest —
 * so a bound armed at mount, before the push settles, has fired before the screen is looked at.
 * An answer lands after that, and a bound armed from it is the one a phone would arm.
 */
