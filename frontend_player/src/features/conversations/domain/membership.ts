/**
 * **Who is in the room, and who a `{name}` slot may name.**
 *
 * Membership is derived from whichever record is currently arranging — the challenge's accepted
 * seats until the line-up completes, the game's frozen line-up after (ADR-0146 §7) — and it is
 * **never stored**. That is the server's fold; what is here is what a client may do with it, and
 * there is exactly one rule: **a line names somebody who is in the room, or it names nobody.**
 *
 * A system line carries an `actor_id` and never a handle, so *"a handle correction reaches the
 * whole backlog for free"* — and the price of that is this lookup. An actor the membership cannot
 * answer for draws the unknown player's `?`, exactly as an unnameable seat does everywhere else
 * in the app, rather than a name read out of `values`.
 *
 * ## The room grows, and it draws what it has
 *
 * A doubles room whose line-up is still filling has two members and will have four. **It draws
 * the members it has**: a row with four faces for a two-member room would be drawing the court
 * rather than the room
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.3), and
 * there is nothing here that pads a membership out to a seat count.
 *
 * ## `{name}` is a handle and never *You*
 *
 * A system line is a **third-person record of what happened in a room** — *Zofia P. set the
 * place* — read identically by everybody in it. `playerName`'s `you` arm is for a sentence
 * addressed to its reader, and two of §23's seven sentences are ungrammatical with it (*You is
 * in*). So the actor is named by the handle they chose, whole, which is ADR-0107's rule and not
 * an exception to it.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

/**
 * One person who has agreed to be on this court right now — **a handle and a face, and nothing
 * else.**
 *
 * No Level, no band, no area, no score: those are a *card*'s, and a card is what a searcher reads
 * to decide about a game that might happen. These people have already agreed to play.
 */
export interface ConversationMember {
  readonly playerId: string;
  /**
   * The whole handle, and absent for an account `users` can no longer name. The member keeps
   * their place either way — dropping them would draw a three-person doubles court.
   */
  readonly nickname?: string;
  /**
   * A short-lived signed link to their photograph, minted for the response it arrived on.
   * Absent when they have no photograph, and absent with `photo_id` — the two travel as a pair.
   */
  readonly photoUrl?: string;
}

/**
 * One member, as somebody a sentence can name.
 *
 * `unknown` where `users` can no longer answer for the account — the member keeps their place and
 * every sentence that would have named them draws the `?`, which is `seatName`'s rule one context
 * over.
 */
export function memberName(member: ConversationMember): NamedPlayer {
  return member.nickname === undefined
    ? { kind: 'unknown' }
    : { kind: 'player', nickname: member.nickname };
}

/** Everybody in the room but the reader, in the order the fold answered them. */
export function othersIn(
  members: readonly ConversationMember[],
  playerId: string,
): readonly ConversationMember[] {
  return members.filter((member) => member.playerId !== playerId);
}

/**
 * The member with this id, as somebody a sentence can name — or the unknown player.
 *
 * Two states draw the `?` and they are deliberately one case: a line with no actor at all, and an
 * actor whose handle `users` can no longer answer for. Neither has a word to draw, and inventing
 * a difference would be a claim about which.
 */
export function memberNamed(
  members: readonly ConversationMember[],
  playerId: string | undefined,
): NamedPlayer {
  const member = members.find((one) => one.playerId === playerId);

  return member === undefined ? { kind: 'unknown' } : memberName(member);
}
