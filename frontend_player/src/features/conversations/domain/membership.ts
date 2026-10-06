/**
 * **Who is in the room, who the response names, and who a `{name}` slot may name.**
 *
 * Membership is derived from the booked game's line-up — who is on its court right now, a leaver
 * gone and a rescue who took the seat in (ADR-0146 §7) — and it is **never stored**. That is the
 * server's fold; what is here is what a client may do with it.
 *
 * ## Two lists, one shape, and which one a sentence reads
 *
 * A system line carries an `actor_id` and never a handle, so *"a handle correction reaches the
 * whole backlog for free"* — and the price of that is a lookup. It used to be a lookup over the
 * **members**, and the one line whose actor is never a member showed why that was the wrong list
 * ([#409](https://github.com/Raketa02/Raketa/issues/409), ADR-0148's 2026-09-11 amendment): a
 * *no* is not an accepted seat, so a third player declining a doubles court drew `? said no`. The
 * wire now names **everybody the response names** under `people` — the members, and every actor
 * and author in the entries carried, one face read — and `{name}` and the author label are filled
 * from there. A member is always among them, so one read answers both.
 *
 * `members` stays what it was: **who is on the court right now**, the gate on every route, and
 * what the header and the row draw faces for. A typist is one too (ADR-0156), so the typing
 * sentence keeps reading the roster. **A person is the shape; a member is that shape under a
 * narrower claim** — the two are one type here because the generated client gets two structurally
 * equal schemas and has to decide that a member *is* a person, which this file does once. The cost
 * is that the compiler cannot tell the lists apart: `othersIn(people, …)` would compile and draw a
 * leaver's face on the row. **Which list a caller reads is guarded by inspection**, and
 * the rule is short enough to hold — faces, the author-label threshold and the typing sentence read
 * `members`; every `{name}` and every author reads `people`.
 *
 * There is still exactly one rule about the slot: **a line names somebody the response named, or
 * it names nobody.** An actor `people` cannot answer for draws the unknown player's `?`, exactly as
 * an unnameable seat does everywhere else in the app, rather than a name read out of `values`.
 *
 * ## The room moves with the court, and it draws what it has
 *
 * A seat left and not yet taken is a member fewer. **It draws the members it has**: a row with
 * four faces for a three-member room would be drawing the court rather than the room, and there is
 * nothing here that pads a membership out to a seat count. `people` pads nothing either:
 * it is who the response *named*, and somebody on it who left is a name a line needs, never a face
 * the row draws.
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
 * One person this response names — **a name and a face, and nothing else.**
 *
 * No Level, no band, no area, no score: those are a *card*'s, and a card is what a searcher reads
 * to decide about a game that might happen. Everybody here was on this court or spoke in this
 * room.
 */
export interface ConversationPerson {
  readonly playerId: string;
  /**
   * The whole name, and absent for an account `users` can no longer name. The person keeps
   * their place either way — a member dropped would draw a three-person doubles court, and an
   * actor dropped would leave a line naming nobody.
   */
  readonly name?: string;
  /**
   * A short-lived signed link to their photograph, minted for the response it arrived on.
   * Absent when they have no photograph, and absent with `photo_id` — the two travel as a pair.
   */
  readonly photoUrl?: string;
}

/**
 * One person who has agreed to be on this court **right now** — the same shape under a narrower
 * claim. Being on the list is the fact; the face is a person's.
 */
export type ConversationMember = ConversationPerson;

/**
 * One person, as somebody a sentence can name.
 *
 * `unknown` where `users` can no longer answer for the account — the person keeps their place and
 * every sentence that would have named them draws the `?`, which is `seatName`'s rule one context
 * over.
 */
export function personName(person: ConversationPerson): NamedPlayer {
  return person.name === undefined ? { kind: 'unknown' } : { kind: 'player', name: person.name };
}

/** Everybody in the room but the reader, in the order the fold answered them. */
export function othersIn(
  members: readonly ConversationMember[],
  playerId: string,
): readonly ConversationMember[] {
  return members.filter((member) => member.playerId !== playerId);
}

/**
 * The person with this id, as somebody a sentence can name — or the unknown player.
 *
 * Handed `people` by every `{name}` slot and author label, and the roster by the typing sentence
 * alone. Two states draw the `?` and they are deliberately one case: a line with no actor at all,
 * and an actor whose handle `users` can no longer answer for. Neither has a word to draw, and
 * inventing a difference would be a claim about which.
 */
export function personNamed(
  people: readonly ConversationPerson[],
  playerId: string | undefined,
): NamedPlayer {
  const person = people.find((one) => one.playerId === playerId);

  return person === undefined ? { kind: 'unknown' } : personName(person);
}

/**
 * **Everybody every held page names, one face per person** — the newest page's, then whoever each
 * page backward adds.
 *
 * The lists arrive newest first, which is the order the pages are held in, and the first face seen
 * for an id is kept: the newest page is the read the room is folded against, and a page backward
 * names people the room's first read could not have known about — it never re-names one it did.
 * A page's `people` is *not the roster and not a superset of it*, so merging is the only reading
 * of it that leaves a name behind; replacing would forget the members the moment the first older
 * page landed.
 */
export function mergedPeople(
  pages: readonly (readonly ConversationPerson[])[],
): readonly ConversationPerson[] {
  const held = new Map<string, ConversationPerson>();

  for (const page of pages) {
    for (const person of page) {
      if (!held.has(person.playerId)) held.set(person.playerId, person);
    }
  }

  return [...held.values()];
}
