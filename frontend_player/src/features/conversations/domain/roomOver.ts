/**
 * **A room that ended while it was on screen** — what the reader is told, folded from what the
 * room itself last said.
 *
 * ## Why the room cannot be told by the room
 *
 * A room without a game is over **exactly when its challenge is** (ADR-0164 §6): the standing
 * folds `DECLINED` in the same commit as the departure that emptied the court, and from that
 * instant every read of the room answers `conversation_not_found`, sweep or no sweep (ADR-0153
 * §5). The *{name} left* line is written by the outbox a second later, into a room nobody can
 * read any more, and the nudge that follows is what makes this phone ask and be told no. So the
 * one thing the reader most wants said — *who left* — is the one thing the stream can no longer
 * say, and the screen used to answer that by leaving
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.7 as it
 * was): the player was in a conversation, and then they were on the list, and the room they were
 * reading was gone ([#429](https://github.com/Raketa02/Raketa/issues/429)).
 *
 * ## What the room held is enough to say it
 *
 * The screen keeps what it last read — the members, the stream — and the ending rule
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §3: *a court is over when at most one player is on it and no seat is awaiting an answer*) is
 * enough to fold from those what must have happened, because a room without a game has exactly
 * these ways to end:
 *
 * - **It held the reader and others.** Members are the accepted seats, so at least two were
 *   accepted, and *at most one* now is: every other member **left** — an accepted seat changes
 *   only by being taken back, a withdrawal is refused once anybody has joined, and the reader's
 *   own departure is made from the list and never from inside the room. Ordinarily that is one
 *   person, told by name; two at once is a phone that missed the first line's nudge and is
 *   catching up, and both are named.
 * - **It held the reader alone.** Somebody had left while a seat was still deciding — the room
 *   stood, and said so as a line — and the last seat deciding has now said no or run out of
 *   time. Nobody else is coming.
 *
 * A room **with** a game is over for its own reasons — called off, or the grace after *we played*
 * running out — and the wire says which of them on the game's card, not here. The reader is told
 * the chat has ended and nothing more, because nothing more is this room's to say.
 *
 * ## What this is not
 *
 * It is a fold over the wire's own facts and the domain's own rule, exactly as `lineUpOf` is,
 * and it invents nothing a line would not have said: the member named is a member the room read
 * off the server, and *left* is the only answer the ending rule leaves. Its falsifier is a new
 * way for a room without a game to end that is not a departure — the day the backend adds one,
 * the first arm here names somebody who did not leave, and this note is where to look.
 */

import type { ConversationMember } from './membership';
import { othersIn } from './membership';
import type { ConversationRoom } from './room';

/** How the room ended, as far as what it last said can tell. */
export type RoomEnding =
  /** Everybody else in the room left it. Ordinarily one person; two is a phone catching up. */
  | { readonly kind: 'they-left'; readonly members: readonly ConversationMember[] }
  /** The reader was alone and the last seat deciding said no or ran out of time. */
  | { readonly kind: 'nobody-else-coming' }
  /** A room with a game, over for a reason the game's card says. */
  | { readonly kind: 'ended' };

/** The one fold, over the room as it was last read. */
export function roomEnding(
  room: Pick<ConversationRoom, 'gameId' | 'members'>,
  playerId: string,
): RoomEnding {
  if (room.gameId !== undefined) return { kind: 'ended' };

  const others = othersIn(room.members, playerId);
  return others.length === 0
    ? { kind: 'nobody-else-coming' }
    : { kind: 'they-left', members: others };
}
