/**
 * A room, as this build reads one.
 *
 * `GET /conversations` is *every room you are a member of, the ones that moved last first* — and
 * **every room is a booked game's**: opened when the game is booked, filed under its booking, its
 * members the game's court as it stands, and **destroyed rather than delisted** once the episode it
 * was opened for is over
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
 * So nothing here has a shelf life to apply.
 *
 * ## No standing, and no pill
 *
 * There is none on the wire and none derived here. ADR-0148 §6's *the last line is what a pill
 * would have said* is a **product** argument and not only a wire one, and the only pill this
 * client could draw would be joined client-side off another feature's read — a cross-feature join
 * feature-first Clean Architecture otherwise refuses
 * ([ADR-0009](../../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)). The
 * state-keyed surfaces are Home and the game's details; this is a row.
 *
 * ## The order is the server's
 *
 * *Ordered by the last entry, newest first*, and a room where nothing has happened yet orders on
 * the moment it opened. Nothing re-sorts here: re-deriving it would need `last_entry`'s own
 * timestamp compared against an opening this list does not carry, and the two would first
 * disagree about exactly the room the wire is being careful about.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { Entry } from './entry';
import type { ConversationMember, ConversationPerson } from './membership';

export interface Conversation {
  readonly conversationId: string;
  /**
   * **The booking the room is filed under** — the join a booked game's details and Home's cards
   * find their chat by (`useBookingRoom`, `useBookingRooms`). A room is opened only by a booked
   * game, so every room has one ([#577](https://github.com/Rakieta02/Rakieta/issues/577)).
   */
  readonly bookingId: string;
  /** What the game is. The row's own identifying fact, beside the handles. */
  readonly sport: Sport;
  /** Who is on the game's court **right now** — see `membership.ts`. */
  readonly members: readonly ConversationMember[];
  /**
   * Everybody this row names — the members, and whoever `last_entry` is about — resolved in the
   * same read. **A superset of `members`**, and what `{name}` is filled from: the actor of a
   * `SEAT_LEFT` line was never on the court ([#409](https://github.com/Rakieta02/Rakieta/issues/409)).
   */
  readonly people: readonly ConversationPerson[];
  /**
   * The newest thing in the room, or nothing.
   *
   * **Absent is a real state rather than an edge case**: the opening writes no line, so a room
   * whose game was just booked has no entry at all.
   */
  readonly lastEntry?: Entry;
}
