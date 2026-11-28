/**
 * **Somebody is typing** — who is drawn, when the roster is trusted, and how often the heartbeat
 * goes out
 * ([ADR-0156](../../../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md),
 * [#404](https://github.com/Rakieta02/Rakieta/issues/404)).
 *
 * ## Typing is not query cache state
 *
 * It is ephemeral, it moves no `seq`, and it must never invalidate a query or touch the stream's
 * data. What arrives is a **roster** — the frame's `player_ids` — and what is drawn is a fold over
 * that roster, the reader, and the channel it came in on. Nothing here is stored past the screen.
 *
 * ## The clear is the empty frame, and the client's own net is the channel — not a clock
 *
 * The server sends a typing frame **when the answer changes and never on a tick**: somebody who
 * types for a minute produces one frame, and the empty frame when their heartbeat expires is the
 * only clear there is. That settles what the client's second safety net can be. The ticket asked
 * for an expiry, and a clock is the wrong instrument on this wire: a timer from the last frame
 * would clear the indicator on exactly the person it exists for, and nothing would ever re-draw
 * it, because from the server's side nothing changed. **What can fail to deliver the clear is the
 * channel**, so that is what the net is keyed on — {@link shownTypists} draws a roster only while
 * the channel is live. A severed stream, a backgrounded app and a phone with no signal all drop
 * the indicator the moment the channel says so, and on reconnect the server's first check is due
 * immediately with its own memory reset, so anybody still typing is announced again.
 *
 * **What that net does not cover, stated rather than hidden:** a stream that dies without the
 * port noticing — a half-open connection that raises no error and no close, on a phone the OS
 * still calls online. The channel reads `live`, no clear can arrive, and a roster stands until the
 * token's `exp` closes the stream, roughly fifteen minutes. It is the same blind spot a nudge has
 * on that channel — a room that looks live and is not — and it is bounded by the same deadline.
 * A last-resort clock would close it at the price of clearing a real typist at that many minutes,
 * and on this wire any client clock is a guess about a person; the guess is not taken here, and
 * the residual is the record's to weigh (§3.6, Part 16).
 *
 * ## Never the reader
 *
 * The server filters the reader out of their own room's frame, and {@link typists} filters again.
 * The ticket asks for the second guard by name — *a composer drawing an indicator for the person
 * using it is the most visible possible bug* — and a set difference is what it costs.
 */

import type { LiveStreamStatus } from '@/shared/lib/platform';

/**
 * How often the heartbeat goes out while somebody is typing — the route's own number, mirrored.
 *
 * Three seconds against the server's five-second expiry: a beat lands most of a cadence before its
 * predecessor lapses, so the other side's indicator holds on somebody who never paused. **The two
 * are one decision** and the server asserts the ordering; this is the client's half of it.
 */
export const TYPING_CADENCE_MS = 3000;

/** Who is typing, as drawn: the frame's order, each person once, and never the reader. */
export function typists(
  playerIds: readonly string[],
  readerId: string | undefined,
): readonly string[] {
  return playerIds.filter((id, at) => id !== readerId && playerIds.indexOf(id) === at);
}

/** The roster while the channel is live, and nobody on any other channel. See the module note. */
export function shownTypists(
  status: LiveStreamStatus,
  roster: readonly string[],
): readonly string[] {
  return status === 'live' ? roster : [];
}

/**
 * Whether a keystroke should post a heartbeat now — the throttle, as a rule rather than a timer.
 *
 * The first keystroke always posts, so the other side learns at once; after that a beat goes out
 * when a cadence has passed since the last one. Nothing here schedules anything: a player who
 * stops typing simply stops asking, and the server's expiry does the rest.
 */
export function beatIsDue(lastBeatAt: number | undefined, now: number): boolean {
  return lastBeatAt === undefined || now - lastBeatAt >= TYPING_CADENCE_MS;
}
