/**
 * A room, as this build reads one.
 *
 * `GET /conversations` is *"every room you are a member of, the ones that moved last first"* —
 * opened by the first acceptance and grown by each one after it, and **destroyed rather than
 * delisted** once the episode it was opened for is over
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
 * That is deliberately the opposite of `GET /challenges`, which keeps ended challenges and says
 * so: the difference is the difference between a record and a room, and it is why nothing here
 * has a shelf life to apply.
 *
 * ## No standing, and no pill
 *
 * There is none on the wire and none derived here. ADR-0148 §6's *the last line is what a pill
 * would have said* is a **product** argument and not only a wire one, and the only pill this
 * client could now draw would be joined client-side off the games cache — a cross-feature join
 * feature-first Clean Architecture otherwise refuses
 * ([ADR-0009](../../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md)). The
 * state-keyed surfaces are the challenge screen and the game screen; this is a row.
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
   * The challenge whose first acceptance opened it.
   *
   * **Nothing on the row draws it, and that is not what it is for.** It is the id the *challenge*
   * screen joins on to find its own door into the room: no route serves a challenge its
   * conversation, ADR-0146 forbids one context knowing the other's ids, and
   * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
   * §3 settles the shape for the same question one context over — **a client join over this list,
   * failing soft.** Finding no room draws no door, which is the ordinary state rather than an
   * error: a room opens on the first acceptance, so a challenge nobody has answered has none.
   */
  readonly challengeId: string;
  /**
   * The game this room's line-up completed into, once the teller has noted it — absent until
   * then, and on every room whose court is still filling.
   *
   * On the row for one reader: the screen that has just said *I'm in* and been told `ON`. That
   * reply means a game exists — it is opened inline with the accept — while the room learns which
   * off the outbox a moment later, so a push that waited only for the room would land in one that
   * draws no plan card yet (`useAwaitedChatDoor`). No row draws it; the header's *Details* reads
   * the room's own copy.
   */
  readonly gameId?: string;
  /** What they are arranging. The row's own identifying fact, beside the handles. */
  readonly sport: Sport;
  /** Who has agreed to be on this court **right now** — see `membership.ts`. */
  readonly members: readonly ConversationMember[];
  /**
   * Everybody this row names — the members, and whoever `last_entry` is about — resolved in the
   * same read. **A superset of `members`**, and what `{name}` is filled from: the actor of a
   * `SEAT_LEFT` line was never on the court ([#409](https://github.com/Raketa02/Raketa/issues/409)).
   */
  readonly people: readonly ConversationPerson[];
  /**
   * The newest thing in the room, or nothing.
   *
   * **Absent is a real state rather than an edge case**: the opening writes no line, so a room
   * whose first acceptance is its whole history has no entry at all.
   */
  readonly lastEntry?: Entry;
}
