/**
 * **Who the stage's hero draws, and every name, figure and line on its pictures**
 * ([#786](https://github.com/Raketa02/Raketa/issues/786), PRD #783; design system 12.2). Copy is
 * code: the miniature cards draw nothing that is not here.
 *
 * ## The cast
 *
 * Nicknames, never the mocks' *Karol T.*: a tile shows the nickname a player chose (ADR-0199 §1),
 * and these were picked so their letters are the mocks' — `karol.t` is KT, `ania.k` AK, `kuba.w`
 * KW, `marek.z` MZ, `stas.w` SW — which is what the splash (#787) and the podium (#788) draw over
 * a poster. **Each carries their poster's look** beside the name, so the same person is the same
 * face on every picture the hero draws: a hue and a pose out of `CourtPoster`'s own closed sets,
 * picked to be the colour mock 2 draws them in, since nobody here has an id for the hash to frame.
 * The club is *Ogrody 33*, the mocks' own.
 *
 * ## The cards
 *
 * Mock 2's three, as PRD #783 names them. **Where the mock hides something behind the front card,
 * this file fills it in so the drawing is whole**, and nobody sees it: the tennis single's second
 * tile is the reader's, the squash game's other player is `ola.m`, and its figure, its clock line
 * and the single's share are plausible rather than read off the mock.
 *
 * ## The loop and *It's a game!*
 *
 * The front card is picked up with the real deck's **I'M IN** — its words, uppercased by the stamp,
 * with no price (#787). Swiped off, it becomes mocks 7–8's splash: the front card's four people face
 * to face — `karol.t` and **You** against `ania.k` and `kuba.w` — and the yes screen's word over the
 * court the last yes booked. **You is a poster with no letters**: the reader's own face is not the
 * hero's to draw, and nobody here is `TK`.
 */

import type { CourtPosterLook } from '@/shared/ui';
import { POSTER_HUES } from '@/shared/ui';

/** Somebody the hero draws: the nickname on their tile, their Level, and their poster. */
export interface StagePerson {
  readonly nickname: string;
  readonly level: number;
  readonly look: CourtPosterLook;
}

/** The people on the hero's pictures — see the module note. */
export const STAGE_CAST = {
  karol: { nickname: 'karol.t', level: 2.75, look: { hue: POSTER_HUES[2], pose: 'serve' } },
  ania: { nickname: 'ania.k', level: 2.68, look: { hue: POSTER_HUES[15], pose: 'lunge' } },
  kuba: { nickname: 'kuba.w', level: 2.8, look: { hue: POSTER_HUES[6], pose: 'serve' } },
  marek: { nickname: 'marek.z', level: 3.15, look: { hue: POSTER_HUES[0], pose: 'forehand' } },
  stas: { nickname: 'stas.w', level: 3.05, look: { hue: POSTER_HUES[9], pose: 'lunge' } },
  ola: { nickname: 'ola.m', level: 2.94, look: { hue: POSTER_HUES[12], pose: 'forehand' } },
} as const satisfies Readonly<Record<string, StagePerson>>;

/** The reader's poster on the splash — the gold-green mocks 7–8 draw their tile in, bare. */
export const STAGE_YOU_LOOK: CourtPosterLook = { hue: POSTER_HUES[0], pose: 'serve' };

/** The words the miniature cards share — the real card's own, kept equal by eye, not by import. */
export const STAGE_CARD_WORDS = {
  /** The reader, in a forecast side. */
  you: 'You',
  /** After a Level on a booked game's tile. */
  paid: 'paid',
  /** The reader's seat when their yes fills the game. */
  youCompleteIt: 'You complete it',
  /** The reader's seat while another is open too. */
  youQuestion: 'You?',
  /** Between a Level and *paid*, and between a court's hour and its club. */
  lineJoin: ' · ',
  /** Between two people on one side of the forecast bar. */
  sideJoin: ' + ',
} as const;

/** The club every card's court is at — the mocks' own. */
export const STAGE_CLUB = 'Ogrody 33';

/** The three cards, as mock 2 deals them. Shares are grosze, as the wire's are. */
export const STAGE_DECK_COPY = {
  /** Front, straight: a padel game waiting for a fourth — the reader's yes completes it. */
  front: {
    ribbon: 'Seat open',
    clock: '21 h 00',
    forecast: 91,
    when: 'Sat 16:00',
    shareGrosze: 2700,
  },
  /** Left, turned: a tennis single somebody was picked for. */
  left: { ribbon: 'Picked for you', forecast: 74, when: 'Thu 19:00', shareGrosze: 3200 },
  /** Right, turned: a squash game whose seat opened, with one more empty. */
  right: {
    ribbon: 'Fill in · seat open',
    clock: '2 h',
    forecast: 88,
    when: 'Thu 21:00',
    shareGrosze: 3000,
  },
} as const;

/** On the front card as it is picked up — the real deck's yes, uppercased by the stamp. */
export const STAGE_STAMP = 'I’m in';

/** What *It's a game!* says in the hero — the yes screen's own word, and the booked court. */
export const STAGE_SPLASH_COPY = {
  word: 'It’s a game!',
  versus: 'vs',
  /** The front card's *Sat 16:00*, as a booked game's line says the day. */
  when: 'Saturday 16:00',
  court: 'Court 6',
  /** After the share — *27 zł each*. */
  each: 'each',
} as const;
