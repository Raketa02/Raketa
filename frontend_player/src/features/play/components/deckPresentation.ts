/**
 * Everything **Players** says around the card: the toggle that is its header, the chip beside
 * it, the Radar pane's one line, the counter pill, the two stamps, the two endings and their
 * buttons, the one toast an answer still raises, and the spoken result of every answer.
 *
 * §1's mechanism throughout — code → message, never message → message — and nothing here is a
 * template inlined in a component.
 *
 * ## The header is a toggle and a chip, and neither carries a count of cards
 *
 * The tab has no title row: *Deck | Radar* top-left is the header, Deck filled
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1), and top-right is the chip — *2 want to play you* — drawn from `pool.want_to_play_you`
 * and **not drawn at zero** (§4). It is the one count of *incoming* yeses the platform has ever
 * published, it names nobody, and it is the reason to swipe tonight. What is still not here is
 * any count of cards behind the one on screen: that number is the counter pill's, where it has
 * room to say it counts the whole pool.
 *
 * ## The counter says what is left, and it is true
 *
 * *8 left · 12 yeses to give* — `remaining + unanswered` and `cap − outstanding`, both off the
 * wire (§5). The first half was deliberately never shown while a hand was all the client knew;
 * `pool.remaining` is what makes it honest. The second half is the cap the mapper used to drop,
 * and it is drawn only once the interest read has landed — a pill saying *8 left* alone is true,
 * and one inventing a budget is not.
 *
 * ## The stamps are feedback and never controls
 *
 * *LET'S PLAY* and *NOT TODAY* — the two answers' own words, which are the buttons' — fade in
 * with the drag and are full at the threshold (§3). They are invisible at rest, hidden from
 * assistive technology, and never pressable; the words are here so the stamps and the spoken
 * names cannot drift apart.
 *
 * ## Two endings, and only one of them offers the reset
 *
 * They split on `players_in_range` (`domain/deckHand`), and the split is what makes both honest:
 * *You have seen everybody* draws the mock — the radius and how long a yes lives, both off the
 * wire — with **Show them again** and **Try the radar**; *Nobody in range* keeps its own
 * sentence and *widen it in You*, **without** the reset, which would deal nobody (§5). The number
 * in the sentence is the interest row's `ttl_days`, never a number this app holds.
 *
 * **The widen sentence names *You* and does not go there.** The remedy belongs to the screen
 * that owns the radius, and the deck's job is to say where it is rather than to grow a second
 * editor for it — the relaxation ladder is the pool's and a deal is offered no rungs at all.
 *
 * ## One toast, and a spoken result for every answer
 *
 * The stamp and the card leaving are the feedback, so the pass toast and the one-sided yes
 * toast retire (§3). What survives of them is the **spoken result**: a listener drags nothing and
 * sees no stamp, so every answer is announced with the sentence the toast used to say. The
 * mutual-naming-no-chat toast stays, verbatim — it is a true sentence about a mutual, and it
 * promises no game (ADR-0154 §3, §5); a mutual naming a challenge is the yes screen (ADR-0167).
 */

import { type ToastTone } from '@/shared/store/toast.store';

import { counted } from '@/shared/formatting/counted';

import type { DeckExit } from './deckStageGeometry';
import { DECK_ANSWER_WORDS } from './playerCardPresentation';

/** The two panes of the Players tab, as the toggle names them. Deck is the one it opens on. */
export const PANE_LABEL = {
  deck: 'Deck',
  radar: 'Radar',
} as const satisfies Readonly<Record<PlayersPane, string>>;

/** Which of the two the player is looking at. Component state, never a route (ADR-0169 §1). */
export type PlayersPane = 'deck' | 'radar';

/** The Radar pane's whole content until it is built. The em dash is an aside, not a colon. */
export const RADAR_LINE = 'Radar — not built yet';

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
 * The retry, and the one control a refused deal leaves.
 *
 * `retryTarget` answers **the-search** for a deal: it mints a record and there is nothing to
 * re-read, so the retry re-fires the act rather than re-reading a result.
 */
export const DEAL_AGAIN_LABEL = 'Deal again';

/**
 * `2 want to play you` — the chip, and the verb agrees with the count.
 *
 * Drawn at one and above (ADR-0169 §4): `0` is a measured nought, and the chip's slot is simply
 * empty. The count is people, never names.
 */
export function wantToPlayYouChip(count: number): string {
  return `${count} ${count === 1 ? 'wants' : 'want'} to play you`;
}

/**
 * `8 left · 12 yeses to give` — the counter pill, and `8 left` alone before the budget is known.
 *
 * Two facts, one pill: what is left counts the pool (`cardsLeft`) and the budget is the cap less
 * the outstanding (`yesesToGive`). The second half waits for the interest read rather than
 * printing a nought, because *0 yeses to give* is a claim the ceiling toast acts on.
 */
export function deckCounter(facts: { readonly left: number; readonly give?: number }): string {
  const left = `${facts.left} left`;
  if (facts.give === undefined) return left;
  return `${left} · ${counted(facts.give, 'yes', 'yeses')} to give`;
}

/**
 * The two stamps' words — the answers' own, which are the buttons' too.
 *
 * Read from `DECK_ANSWER_WORDS` rather than re-typed, so the stamp a drag reveals and the name
 * a button announces are one string; the capitals are the stamp's treatment, not the copy's.
 */
export const STAMP_WORDS: Readonly<Record<DeckExit, string>> = {
  yes: DECK_ANSWER_WORDS.accept,
  no: DECK_ANSWER_WORDS.pass,
};

/** The empty state a player reaches by answering everybody the deck could deal them. */
export const SEEN_EVERYBODY_TITLE = 'You have seen everybody';

/** The empty state a player reaches because there is nobody inside their radius. */
export const NOBODY_IN_RANGE_TITLE = 'Nobody in range yet';

/**
 * *Nobody new in 8 km today. Your yeses stay live for 21 days, so the ones you gave are still
 * working.* — the radius the deal ran on, and `ttl_days` off the interest read.
 *
 * The second sentence waits for the read: it states a number, and this app holds none of the
 * three (ADR-0127 §6). Without it the first sentence stands alone rather than guessing.
 */
export function seenEverybodyLine(facts: {
  readonly radiusKm: number;
  readonly ttlDays?: number;
}): string {
  const nobodyNew = `Nobody new in ${facts.radiusKm} km today.`;
  if (facts.ttlDays === undefined) return nobodyNew;
  return `${nobodyNew} Your yeses stay live for ${counted(facts.ttlDays, 'day', 'days')}, so the ones you gave are still working.`;
}

/** *Show them again* — `POST /deck/reset`, then a fresh deal. On the one ending it can help. */
export const SHOW_THEM_AGAIN_LABEL = 'Show them again';

/** *Try the radar* — flips the toggle. The pane says it is not built; the door is real. */
export const TRY_THE_RADAR_LABEL = 'Try the radar';

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
 * The spoken result of a pass — the retired toast's own words, said to a listener alone.
 *
 * §15's `playerName()` gives the **whole handle** — the prototype's `split(' ')[0]` invents a
 * familiar form nobody gave the platform — and the caller passes the name it already drew.
 */
export function passedAnnouncement(name: string): string {
  return `Not today, ${name}`;
}

/** The spoken result of a one-sided yes: nobody is notified, and the sentence says when it shows. */
export function interestAnnouncement(name: string): string {
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

/** What a yes's reply earns: a sentence said aloud, a toast, or a screen the mutation pushes. */
export type YesOutcome =
  | { readonly kind: 'announce'; readonly message: string }
  | { readonly kind: 'toast'; readonly message: string; readonly tone: ToastTone }
  | { readonly kind: 'screen' };

/**
 * Which of the three a yes earned, decided **here** rather than at the press.
 *
 * The screen holds the answer and this module holds the sentences, so choosing between them
 * belongs here — a branch at the call site would be a fourth place that has to know a mutual
 * without a game keeps the older words. It takes the answer's own shape, so a further arm
 * arrives as a field rather than as another nested conditional.
 *
 * A one-sided yes is **spoken and not shown** (ADR-0169 §3): the stamp was the feedback. A
 * mutual naming no chat is the one toast left. A mutual naming a challenge is the yes screen,
 * pushed by the mutation (`hooks/useDeck`) rather than from here — *Matched!* was a toast once
 * and a grey line gone in three seconds was the wrong size for the one tap that changed
 * something (ADR-0167 §1).
 */
export function yesOutcome(
  name: string,
  said: { readonly mutual: boolean; readonly challengeId: string | null },
): YesOutcome {
  if (!said.mutual) return { kind: 'announce', message: interestAnnouncement(name) };
  if (said.challengeId === null) return { kind: 'toast', message: mutualToast(name), tone: 'ok' };
  return { kind: 'screen' };
}
