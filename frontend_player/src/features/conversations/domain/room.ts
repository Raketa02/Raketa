/**
 * **One room, opened** — the header and the page, from one fold.
 *
 * `domain/conversation.ts` beside this holds the **row**: a door in a list, with the members and
 * the last thing that happened. This is what is behind the door, and the two are separate types
 * rather than one with optional halves because they come off separate reads with separate
 * envelopes — `GET /conversations` folds *whether a row appears at all*, and
 * `GET /conversations/{id}` folds *this room and its newest page against one instant*.
 *
 * ## `read_at` is on this one, and it is what the room is folded against
 *
 * *"One instant for both, so members and entries can never disagree"* (ADR-0148 §10). It is what
 * every clock-shaped question on this screen is asked of — today's is whether the plan's agreed
 * day is **today** — and never `Date.now()`, on `durationLeft`'s own rule one context over: a
 * screen that mixed the two would state one fact against two readings of the clock.
 *
 * ## The beginning is `seq` 1, and there is no `has_more`
 *
 * ADR-0147's gapless sequence makes **`seq` 1 the beginning of the conversation**, so a flag
 * beside it would be the same fact twice
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.3). Paging
 * backward is *ask for what is before the oldest thing I hold*, and it stops when that is the
 * first entry there ever was.
 *
 * **No reader infers loss from a gap.** The gaplessness is the server's promise; nothing here
 * counts, compares or repairs a sequence, and {@link earlierThan} is the only thing in this
 * feature that reads a `seq` at all.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { Entry } from './entry';
import type { ConversationMember } from './membership';

export interface ConversationRoom {
  readonly conversationId: string;
  /**
   * The challenge whose first acceptance opened it.
   *
   * Mapped here and not on the row's twin, because this is where it has a reader: it is the id
   * a challenge screen joins on to find its own door back into the room.
   */
  readonly challengeId: string;
  /**
   * The game its line-up completed into, and **absent until it does**.
   *
   * The whole of what decides whether the header draws *Details*: a `LINE_UP_INCOMPLETE` room
   * has no game and no plan, so there is nothing for that door to open and **no door is drawn
   * rather than a dead one** ([#324](https://github.com/Raketa02/Raketa/issues/324)).
   */
  readonly gameId?: string;
  /** The instant the header and the page were folded — **one instant for both**. */
  readonly readAt: string;
  readonly sport: Sport;
  /** Who has agreed to be on this court right now. It grows one acceptance at a time. */
  readonly members: readonly ConversationMember[];
}

/**
 * A room and **everything of its stream this client is holding** — one page on arrival, and one
 * more with each backward step.
 *
 * The two are separate because they arrive separately and grow differently: the header comes off
 * the first read alone and is not resent, while the entries accumulate. Folding them into one
 * object with a mutable `entries` field would put the same list in two places, and the one nobody
 * updated is the one a screen would eventually draw.
 */
export interface OpenConversation {
  readonly room: ConversationRoom;
  /** Oldest first, which is the order the stream is drawn in and the order the wire sends. */
  readonly entries: readonly Entry[];
}

/**
 * The `seq` to page backward from, or nothing where the beginning is already held.
 *
 * `entries` is oldest first, so the cursor is the first one's — *give me what is before this*.
 * Nothing to page from at all is a room whose page came back empty, which is a room where
 * nothing has happened yet.
 */
export function earlierThan(entries: readonly Entry[]): number | undefined {
  const oldest = entries[0]?.seq;

  return oldest === undefined || oldest <= 1 ? undefined : oldest;
}

/**
 * **Is the author's handle drawn on a bubble** — the one fact about a conversation that decides
 * it, read once by the screen and handed down.
 *
 * *Drawn only where the conversation has more than two members* (§3.3). In a pair there is
 * nothing to disambiguate — the side and the ground say who spoke — and ADR-0107 forbids the
 * familiar form the prototype drew in fourteen of its twenty-two templates. It is a fact about
 * the **room**, so it is a prop from the screen and never a read inside the bubble, which is the
 * rule `the-play-components.md` §3 states about `sportName`.
 */
export function namesItsAuthors(members: readonly ConversationMember[]): boolean {
  return members.length > 2;
}
