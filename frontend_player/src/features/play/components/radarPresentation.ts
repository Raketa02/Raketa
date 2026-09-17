/**
 * Everything the **Radar** pane says — the tile's *you*, a ring's label, the counter between
 * ±, a level under a face, the card's six lines and its answered last line, the footer's
 * headline and its right-hand count, the hint by zoom state and the stacked sentence, a
 * stack's count and its spoken name, the empty reading, *Looking around…*, the failure and its
 * retry, the cluster's three spoken names, and the record sheet's foot
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §26, drawn by
 * [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7).
 *
 * §1's mechanism throughout — code → message, never message → message — and nothing here is a
 * template inlined in a component. The chip is the deck's own sentence and the deck's own
 * number (`wantToPlayYouChip`), the widen sentence is §17's (`WIDEN_IN_YOU`), and the radar
 * writes nothing about people: every word on a card is a figure the platform computed or a
 * name the player gave.
 *
 * ## The privacy line is the one constant
 *
 * The hint **always opens** with *Distance and bearing only — never an address, never a
 * street.* — at every width, while loading, and under the empty reading's headline, where §17's
 * widen sentence follows it instead of the movement sentence. It switches on the **zoom
 * state** and never on the selection: a selected card at 18 km across is still a field of faces
 * to move around, and the closest widths say what a tap earns there — a card, one at a time
 * (ADR-0176 §3). The failure is the one footer with no hint: *Try again* stands in its place.
 *
 * ## The sheet's foot cites, and writes one line of its own
 *
 * The two buttons are the deck's two words (`DECK_ANSWER_WORDS`, §20.5) and are spoken with the
 * person's name as the deck's buttons are, so a listener hears the same act on either surface.
 * *Wants to play you* is §10's tag — `INTEREST_RECEIVED`'s line, the builder's own — and *You
 * said yes* is the builder's plain tag; both are reached rather than re-typed, so a rewording
 * moves everywhere at once. The chat door is every chat door's words (`OPEN_THE_CHAT`, the
 * conversations feature's) and the court's line is the Chats row's own (`standingLine`). The
 * one sentence this surface writes is *You're matched*.
 *
 * ## The counter prints one decimal below 10 and a whole number above
 *
 * *5,4 km across* and *18 km across* are the ladder's own spellings; a pinch resting at 7,83
 * reads *7,8 km across* and one at 23,4 reads *23 km across*. Through the house's comma, which
 * has one home (`ratingFormat`), and never a template's `.replace`.
 */

import { formatDistanceKm, formatWidthKm } from '@/shared/formatting/ratingFormat';
import { counted } from '@/shared/formatting/counted';

import type { ZoomState } from '../domain/radarGeometry';
import type { RadarAnswer } from '../domain/reading';

import { WIDEN_IN_YOU } from './deckPresentation';
import { livenessLine } from './livenessPresentation';
import { DECK_ANSWER_WORDS, YOU_SAID_YES_WORD } from './playerCardPresentation';

/** Under the viewer's tile. Lower case, `tiny`. */
export const YOU_LABEL = 'you';

/** `5 km` — a ring's label, at the top of the circle. Whole kilometres: the series has no decimal. */
export function ringLabel(km: number): string {
  return `${km} km`;
}

/** `18 km across` · `5,4 km across` — the counter between ±, always drawn. */
export function widthAcross(widthKm: number): string {
  return `${formatWidthKm(widthKm)} across`;
}

/** `1,9 km` — the card's distance, one decimal, never below 0,1. */
export function cardDistance(distanceKm: number): string {
  return formatDistanceKm(distanceKm);
}

/** `✦ {fit} fit` — the Fit pill's word, after the figure the pill already draws. */
export const FIT_WORD = 'fit';

/** `{score} reliability` · `— reliability` — the reliability chip, labelled, and a dash when unwatched. */
export const RELIABILITY_WORD = 'reliability';

/** What the chip prints where the platform has watched nothing. */
export const UNWATCHED_MARK = '—';

/** The chip's figure — the score, or the dash. The card draws it in mono beside the word. */
export function reliabilityFigure(playerScore: number | undefined): string {
  return playerScore === undefined ? UNWATCHED_MARK : String(playerScore);
}

/** The chip as one sentence — `88 reliability` · `— reliability` — which is what the card says. */
export function reliabilityChip(playerScore: number | undefined): string {
  return `${reliabilityFigure(playerScore)} ${RELIABILITY_WORD}`;
}

/** `2 tags in common` · `1 tag in common` · `no tags in common` — a count, never a list. */
export function tagsInCommon(count: number): string {
  return count === 0 ? 'no tags in common' : `${counted(count, 'tag', 'tags')} in common`;
}

/** The card's last line — coral; the whole card is the target. */
export const TAP_FOR_THE_FULL_CARD = 'Tap for the full card ›';

/**
 * The card's last line **after an answer** — in place of the door, and the face never changes
 * (§26). The tag's words and the button's, each with the door's mark, so the line and the act
 * it records are one string.
 */
export const ANSWERED_LINE: Readonly<Record<RadarAnswer, string>> = {
  yes: `${YOU_SAID_YES_WORD} ›`,
  no: `${DECK_ANSWER_WORDS.pass} ›`,
};

// ---------------------------------------------------------------------------
// The record sheet's foot
// ---------------------------------------------------------------------------

/** The two buttons: the deck's two words, `secondary` and `primary`, the swipe's reading order. */
export const FOOT_ANSWER_WORDS: Readonly<Record<RadarAnswer, string>> = {
  no: DECK_ANSWER_WORDS.pass,
  yes: DECK_ANSWER_WORDS.accept,
};

/** The two buttons' spoken names — the act and the person, as the deck's buttons say them. */
export function footAnswerLabels(name: string): Readonly<Record<RadarAnswer, string>> {
  return { no: `${FOOT_ANSWER_WORDS.no}, ${name}`, yes: `${FOOT_ANSWER_WORDS.yes}, ${name}` };
}

/** A liker's line above the two buttons — §10's tag, the builder's, cited. */
export const WANTS_TO_PLAY_YOU = livenessLine('INTEREST_RECEIVED');

/** The reader's own yes, beside *Not today* — the builder's plain tag, cited. */
export const YOU_SAID_YES = YOU_SAID_YES_WORD;

/** A mutual, live: the one sentence the foot writes for itself. The door beside it is `OPEN_THE_CHAT`. */
export const YOURE_MATCHED = "You're matched";

/** `14 players in view` · `1 player in view` — recounted on every move. */
export function playersInView(count: number): string {
  return `${counted(count, 'player', 'players')} in view`;
}

/** `+3 off screen` · `all of them` — so the count is never mistaken for the population. */
export function offScreen(count: number): string {
  return count === 0 ? 'all of them' : `+${count} off screen`;
}

/** The one sentence that stays at every width. */
export const PRIVACY_LINE = 'Distance and bearing only — never an address, never a street.';

/**
 * The hint's second sentence, by zoom state: how to move while the field is faces, and — at
 * the closest widths, where a tap no longer flies anywhere far — that a tap is what earns a
 * card and the card is what leads to the profile (ADR-0176 §3: the card is the selection's).
 */
const HINT_BY_STATE: Readonly<Record<ZoomState, string>> = {
  wide: 'Drag to move, pinch or use ± to zoom, tap anybody to fly to them.',
  closer: 'Drag to move, pinch or use ± to zoom, tap anybody to fly to them.',
  closest: 'Tap anybody for their card, and the card for the full profile and the two answers.',
};

/** A third sentence at the floor, while a stack stands: what a numbered square is, and what a tap does to it. */
const STACKED_HINT = 'A number is players too close to tell apart; tap it to spread them.';

/**
 * The footer's hint: the privacy line, then the sentence the zoom state earns — and, while a
 * stack is drawn, the stacked sentence after it (ADR-0177 §2). A stack is a fact of the width
 * and the reading, never of the selection, so the rule *switches on the zoom state and never
 * on selection* holds.
 */
export function radarHint(state: ZoomState, stacked = false): string {
  const hint = `${PRIVACY_LINE} ${HINT_BY_STATE[state]}`;
  return stacked ? `${hint} ${STACKED_HINT}` : hint;
}

// ---------------------------------------------------------------------------
// A stack at the floor
// ---------------------------------------------------------------------------

/** `3` — what the marker prints: the count, mono, and nothing else. */
export function stackCount(members: number): string {
  return String(members);
}

/** `3 players close together` — a stack, spoken. */
export function stackLabel(members: number): string {
  return `${counted(members, 'player', 'players')} close together`;
}

/** What a tap on the marker does, spoken after the name: spread them, or fold them back. */
export function stackHint(open: boolean): string {
  return open ? 'Folds them back together.' : 'Spreads them out so each can be tapped.';
}

/** `Nobody within 10 km plays padel yet` — the reach is `pool.radius_km_used`; the sport in lower case. */
export function nobodyInReach(facts: {
  readonly reachKm: number;
  readonly sportName: string;
}): string {
  return `Nobody within ${facts.reachKm} km plays ${facts.sportName.toLowerCase()} yet`;
}

/** The empty reading's hint: the privacy line, then the deck's own sentence about the slider in You. */
export function emptyHint(): string {
  return `${PRIVACY_LINE} ${WIDEN_IN_YOU}`;
}

/** While the reading is on its way; the privacy line beneath. */
export const LOOKING_AROUND = 'Looking around…';

/** The failed reading's headline, and the retry in the hint's place. */
export const RADAR_FAILED = "The radar couldn't load";
export const TRY_AGAIN = 'Try again';

/** ± and ◉, spoken. */
export const ZOOM_IN_LABEL = 'Zoom in';
export const ZOOM_OUT_LABEL = 'Zoom out';
export const BACK_TO_YOU_LABEL = 'Back to you';

/** The glyphs on the cluster's three squares. Marks, never words: the words are the labels above. */
export const ZOOM_IN_MARK = '+';
export const ZOOM_OUT_MARK = '−';
