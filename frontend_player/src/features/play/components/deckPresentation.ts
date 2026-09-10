/**
 * Everything **Match me** says: the segment above it, the two sentences under the card, the
 * two empty states, and the three toasts an answer raises.
 *
 * §1's mechanism throughout — code → message, never message → message — and nothing here is a
 * template inlined in a component.
 *
 * ## The segment carries the name and no number
 *
 * `Match me · 3` was the count of the player's own outstanding yeses, printed on the control
 * that reaches the deck. It is **struck**, because the position it was in is the position a
 * count of *cards waiting* would be in, and that is what it was read as: a number beside a
 * surface that deals one person at a time says how many people are behind that person, and a
 * deal is at most ten cards out of a pool nobody sees the size of — the same *`{n} left`* the
 * deck refused on the card itself (`domain/deckHand`).
 *
 * The figure is not lost and was never only here: it is the sentence the empty state prints,
 * `outgoingYeses` below, where it has room to say what it counts. `MATCH_ME_TITLE` is now the
 * whole of the segment's half, spoken and drawn alike, which is also why neither has a function
 * any more.
 *
 * ## The footer is a promise, and both halves of it are load-bearing
 *
 * The prototype's footer reads *"Passing is silent — nobody is told, nothing is scored"* and
 * *"Long-press the photo for the full record."* The first sentence survives and grows a
 * clause; the second **pointed at `SH.player`, which K-7 removed**, so it was a promise with
 * nothing behind it. [#231](https://github.com/Raketa02/Raketa/issues/231) repointed a card's
 * long press at *Why 78?*, and
 * [#270](https://github.com/Raketa02/Raketa/issues/270) ships the promise and its target
 * together rather than advertising a gesture again.
 *
 * The pass sentence is [ADR-0128](../../../../../docs/adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)'s
 * own instinct, in words: the suppression is **deck-only**, so *"pass on somebody tonight,
 * find them third in your shortlist tomorrow"* is a named cost, and *"if that reads as the
 * product ignoring you, the fix is a sentence on the deck about what a pass does, never a
 * wider suppression."* This is that sentence. It says nobody is told and it says the pass does
 * not reach a search, because those are the two things a player would otherwise infer wrongly
 * in opposite directions.
 *
 * ## Two empty states, and only one of them may give advice
 *
 * They split on `players_in_range` (`domain/deckHand`), and the split is what makes the advice
 * honest: *widen* is addressed to somebody with nobody in range, never to somebody who has
 * answered everybody. **There is no *Show them again*.** The prototype's button clears every
 * pass at once, which makes `PASS_SUPPRESS` unmeasurable and the suppression a suggestion —
 * so what stands in its place is the honest ending: the pool it came from, and the count of
 * the player's **own outgoing** yeses.
 *
 * **The widen sentence names *You* and does not go there.** The remedy belongs to the screen
 * that owns the radius, and the deck's job is to say where it is rather than to grow a second
 * editor for it — the relaxation ladder is the pool's and a deal is offered no rungs at all.
 */

import { type ToastTone } from '@/shared/store/toast.store';

import { counted } from '@/shared/formatting/counted';

/** The screen's title, and the segment's own word for it. */
export const MATCH_ME_TITLE = 'Match me';

/**
 * The deck's own version of *no rated sport*.
 *
 * Unreachable from the flow — the Play tab is behind a rating — and written for the reason
 * `FindAGameStanding` represents the branch at all: the alternative is a chip row of nothing
 * over a deck that would be refused, with no sentence saying why.
 */
export const NO_RATED_SPORT_LINE = 'Rate a sport first, and the deck has somebody to deal you.';

/** What the spinner over a deal in flight announces. */
export const DEALING_LABEL = 'Dealing';

/**
 * The retry, and the one control this screen has.
 *
 * `retryTarget` answers **the-search** for a deal: it mints a record and there is nothing to
 * re-read, so the retry re-fires the act rather than re-reading a result. It is the same
 * control the player presses when a deal is spent, which is why there is one word for both.
 */
export const DEAL_AGAIN_LABEL = 'Deal again';

/**
 * The two sentences under the card.
 *
 * The first is what a pass does — silent, and **deck-only**. The second is the footer promise,
 * and it names the gesture and what the gesture opens; it is drawn on the deck and nowhere
 * else, because the pool's two cards reach the same sheet on a plain press.
 */
export const DECK_FOOTER = [
  'Passing is silent — nobody is told, and they can still turn up in a search.',
  'Hold a card to see how its Fit was worked out.',
] as const;

/** The empty state a player reaches by answering everybody the deck could deal them. */
export const SEEN_EVERYBODY_TITLE = "That's everybody for now";

/** The empty state a player reaches because there is nobody inside their radius. */
export const NOBODY_IN_RANGE_TITLE = 'Nobody in range yet';

/**
 * *Widen in You* — the one piece of advice that survives on this surface, and the only Play
 * screen that gives it.
 *
 * Drawn **only** where `radius_clamp` is false. A player already at the ceiling of their own
 * slider cannot widen, and telling them to is the product asking for something they cannot
 * give (`the-words.md` §17).
 */
export const WIDEN_IN_YOU =
  'Your search radius lives in You. Widening it is what brings more people into range.';

/**
 * What the player has to show for a deck they have answered out.
 *
 * It states the **mechanism** rather than a promise: a one-sided yes is silent and becomes
 * visible only when the other person goes looking for a game, so the sentence says when they
 * will see it and never that they have been told.
 */
export function outgoingYeses(outstanding: number): string {
  if (outstanding === 0) return "You haven't said yes to anybody in this sport yet.";
  return `${counted(outstanding, 'person', 'people')} you said yes to will see it the next time they look for a game.`;
}

/**
 * The three toasts an answer raises, each naming the player it is about.
 *
 * §15's `playerName()` gives the **whole handle** — the prototype's `split(' ')[0]` invents a
 * familiar form nobody gave the platform — and the caller passes the name it already drew.
 */
export function passedToast(name: string): string {
  return `Not today, ${name}`;
}

/** A one-sided yes: nobody is notified, and the sentence says exactly when it becomes visible. */
export function interestToast(name: string): string {
  return `Noted — ${name} sees it the next time they look for a game`;
}

/**
 * A mutual the platform opened **no game for**, and the sentence it had before it could.
 *
 * **There is no notification**: nothing in this repository can push anything, so the sentence
 * says how the other person finds out rather than implying they have been told.
 *
 * **It must not say why there is no game, and it must not say that there is none**
 * ([ADR-0154](../../../../../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md)
 * §3, §5). A missing `challenge_id` is one answer covering two causes — the pair already have
 * a game *being arranged*, or a gate refused — and which of those it is deliberately does not
 * cross the wire. Drawing the absence as a state of its own would hand the sender the second
 * one, which is the trace ADR-0095 guarantees a block never leaves. So this is kept **exactly**
 * as it read before the field existed: it is a true sentence about a mutual, and it promises
 * no game.
 */
export function mutualToast(name: string): string {
  return `You both said yes — ${name} sees it the next time they open Raketa`;
}

/**
 * A mutual the platform **has a game for**, which is the ordinary one.
 *
 * The tap answers with the challenge these two now have — the one it just opened, or the one
 * an earlier mutual opened that is not finished with — so the screen can stop leaving a player
 * to wonder where it went (ADR-0154 §1).
 *
 * **It names Chats and calls the thing nothing at all.** A mutual-born singles court is `ON`
 * from birth, and a doubles one is a side short — *"a half-built court is not a game the pair
 * have, it is a game they are still making"* — so both *your game is on* and *your game* are
 * wrong for half the sports. What is true either way is that the two of them now share a row
 * and a room in that tab, and that is the whole of what this says. There is no deep link
 * because a toast carries no action here; the row is the door, and it is already there.
 */
export function mutualChallengeToast(name: string): string {
  return `You both said yes — ${name} is in your Chats now`;
}

/**
 * Which of the three a yes earned, decided **here** rather than at the press.
 *
 * The screen holds the answer and this module holds the sentences, so choosing between them
 * belongs here — a branch at the call site would be a fourth place that has to know a mutual
 * without a game keeps the older words. It takes the answer's own shape, so a fourth arm
 * arrives as a field rather than as another nested conditional.
 */
export function yesToast(
  name: string,
  said: { readonly mutual: boolean; readonly challengeId: string | null },
): { readonly message: string; readonly tone: ToastTone } {
  if (!said.mutual) return { message: interestToast(name), tone: 'base' };
  if (said.challengeId === null) return { message: mutualToast(name), tone: 'ok' };
  return { message: mutualChallengeToast(name), tone: 'ok' };
}
