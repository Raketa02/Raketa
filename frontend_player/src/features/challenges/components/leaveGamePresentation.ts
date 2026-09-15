/**
 * **Every word the departure says** — *Leave this game* on the game screen, its busy label, the
 * sheet in front of it, and the second door to the same act: *Leave the game* revealed on a Chats
 * row and drawn on the challenge screen before the court is whole
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.8 and §22.10,
 * [#418](https://github.com/Raketa02/Raketa/issues/418),
 * [#427](https://github.com/Raketa02/Raketa/issues/427)).
 *
 * A deck of its own rather than rows in `challengeDetailPresentation.ts`, because that deck is the
 * challenge screen's and this act is pressed on the **game** screen and on the **Chats** list: copy
 * lives beside the act that says it, and the act is composed onto those surfaces through
 * `types.ts`.
 *
 * ## The withdraw's shape, and the difference that reworded it
 *
 * `WithdrawSheet`'s exact shape a third time — a title naming the **moment** rather than the act,
 * body lines, the act named once on the control that carries it out, a dismissal named by what it
 * does. What differs is what the sheet has to say: the call-off ends the game and the room, and its
 * second line exists to say so (§22.9; the withdraw's own deck, which said the same of a court, is
 * retired with #428); a departure destroys **nothing** — the others keep the game, the plan and
 * the room
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md))
 * — so the first line says what survives, and the second says the one thing the leaver gives up:
 * `already_asked_at` keeps them out of this court's pool for as long as it stands, and nobody is
 * asked twice on one challenge.
 *
 * **Nothing here says the pair rule releases**, on the withdraw's own line (`the-words.md` §22.3):
 * that is a fact about what becomes possible afterwards, and a confirmation is not the place to
 * sell a consequence.
 */

import type { AppError } from '@/shared/errors';
import { playerName } from '@/shared/formatting/playerName';

import type { LeavingEnds } from '../domain/challenge';

import { challengeErrorMessage } from './challengeErrorMessage';

/**
 * The control, on the game screen — **quiet, destructive, and last**, behind the sheet below.
 *
 * The visible label is the whole sentence, so it is the accessible name too: unlike the retired
 * `Withdraw`, which said one word and named what it withdrew to a listener, there is no shorter
 * form that a reader would want.
 */
export const LEAVE_THIS_GAME = 'Leave this game';

/** The departure while it is in flight, on the control that carries it out. */
export const LEAVING = 'Leaving…';

/** The title names the moment, so the act is named once — by {@link LEAVE_THE_GAME}. */
export const LEAVE_SHEET_TITLE = 'Before you leave';

/**
 * The three bodies, in order: what survives, what the leaver gives up, and that it cannot be
 * undone. The first line is the whole reason the act exists (#411: *the others keeping what they
 * agreed rather than starting over*), and the second is the one cost that is theirs alone.
 */
export const LEAVE_SHEET_BODY = [
  'The others keep the game and can fill your seat.',
  "You can't be asked back into this one.",
  'This cannot be undone.',
] as const;

/**
 * The act, on the sheet that confirms it — and, since #427, the control a Chats row reveals and
 * the challenge screen draws before the court is whole. One label on the control and on the
 * sheet's act, on `Send the challenge`'s precedent: the act is named once, and what is under the
 * sheet is hidden while it is up.
 */
export const LEAVE_THE_GAME = 'Leave the game';

/** The sheet's dismissal, **named by what it does** — never just *Close*. */
export const LEAVE_SHEET_CLOSE_LABEL = 'Stay in';

/**
 * **The one line the list's sheet says** — the consequence, as the author fixed it
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §6): the seat, and the chat, in one breath. The two are one fact — nobody is in the chat
 * separately from being on the court — and the line exists so that leaving the chat is not a
 * surprise about leaving the game.
 *
 * One line where the game screen's sheet has three, because what it stands in for differs: that
 * sheet is reached from a screen about a game the reader has been looking at, and its lines say
 * what survives and what the leaver gives up; this one is reached from a list, one swipe deep, and
 * has to say what the act **is** before anything about its cost. The dismissal, the title and the
 * act are the game screen's own, so the two sheets read as one act met twice.
 */
export const LEAVE_FROM_THE_LIST_BODY =
  "Your seat opens for someone else and you'll leave the chat.";

/**
 * **The line the sheet says instead, when the leaving would end the court** — the reader is the
 * only other accepted seat and no seat is awaiting, read off the row the list holds
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §9). Which of the two it is, `game_id` decides: on a game the departure **calls the game off**
 * — for the one person left, too, which is the whole reason the line exists — and on a court that
 * never became one it **closes the court** for them. Both keep the list line's second fact, the
 * chat, because on either the room goes with the act. `{name}` is the whole name (ADR-0171), and
 * `?` where `users` has lost them.
 *
 * On the game screen's own sheet this line **replaces** the first of its three — *The others keep
 * the game and can fill your seat* is false of a leaving that calls it off — and the other two
 * stand, because they are still true.
 */
export function leavingEndsLine(ends: LeavingEnds): string {
  const name = playerName(ends.theOneLeft);

  return ends.court === 'a-game'
    ? `Leaving now calls the game off — for ${name} too. Your chat goes with it.`
    : `Leaving now closes this court for ${name}. Your chat goes with it.`;
}

/**
 * **What the list's sheet says** — the ending line where the leaving would end the court, and
 * today's line otherwise. One function, so the door and the screen behind it cannot disagree.
 */
export function leaveFromTheListBody(ends: LeavingEnds | undefined): readonly string[] {
  return [ends === undefined ? LEAVE_FROM_THE_LIST_BODY : leavingEndsLine(ends)];
}

/**
 * **What the game screen's sheet says** — its three lines, with the first replaced by the ending
 * line where the leaving would call the game off. See {@link leavingEndsLine} for why it
 * replaces rather than precedes.
 */
export function leaveThisGameBody(ends: LeavingEnds | undefined): readonly string[] {
  if (ends === undefined) return LEAVE_SHEET_BODY;
  const [, ...stillTrue] = LEAVE_SHEET_BODY;
  return [leavingEndsLine(ends), ...stillTrue];
}

/**
 * *This one is already over* — `challenge_is_over`'s sentence, **named once** because two sheets
 * say it: the departure's here, and the removal's (`challengeDetailPresentation.ts`), which meets
 * the same fact about the same court through another door ([#428](https://github.com/Raketa02/Raketa/issues/428)).
 */
export const THIS_ONE_IS_OVER = 'This one is already over.';

/**
 * **What the sheet says when the departure is refused** — the four codes the route documents,
 * each a sentence, over `challengeErrorMessage`'s fallback for everything else.
 *
 * On the game screen these four are **re-reads and no words**: the games list is what that screen
 * folds its arm from, and the fold the re-read lands on is the sentence. A list row has no such
 * fold — a room whose game's moment has passed is drawn exactly as one whose moment is ahead — so
 * the refusal is told in words on the sheet, as the ticket asks, and the lists are re-read once
 * the sheet is dismissed, so that a court that has genuinely ended goes when the server says it has
 * and not while its sentence is being read.
 *
 * Each names the fact and never the mechanism: *the time you agreed has passed* rather than *the
 * moment guard*, *this one is over* rather than *the challenge has ended*. `challenge_not_found` is
 * one code for three cases on the wire — it does not exist, you are not on its court, your seat is
 * not an accepted one — chosen so that a departure's refusal *"must not confirm that you were on
 * this court a moment ago"*; the sentence says the one thing true of all three and confirms
 * nothing about before.
 */
export const LEAVE_REFUSED: Readonly<Record<string, string>> = {
  game_moment_has_passed: "The time you agreed has passed, so there's nothing to leave now.",
  challenge_is_over: THIS_ONE_IS_OVER,
  game_is_history: 'This game has already happened, or never will.',
  challenge_not_found: "You don't hold a seat on this court.",
};

/**
 * The sentence a refused departure writes on the list's sheet: the deck's own where the code has
 * one, and the feature's sentence for every other write otherwise — `account_held`, a connection
 * that was not there, a code this build has never seen.
 */
export function leaveRefusalMessage(error: AppError): string {
  const own = error.code === undefined ? undefined : LEAVE_REFUSED[error.code];
  return own ?? challengeErrorMessage(error);
}
