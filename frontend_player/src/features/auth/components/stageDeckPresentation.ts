/**
 * **Sign-in's three miniature cards, composed from the copy**
 * ([#786](https://github.com/Raketa02/Raketa/issues/786); design system 12.2, mock 2) — the deck's
 * `deckPresentation`: every line a card draws is put together here from `stageHeroCopy`'s words,
 * names and figures, through the app's own formatters, and the card is handed plain props.
 *
 * - **Front, straight**: a padel game waiting for a fourth — *Seat open · ⏱ 21 h 00*, `karol.t`,
 *   `ania.k` and `kuba.w` paid, and the reader's dashed volt seat, *You complete it*.
 * - **Left, turned**: a tennis single, *Picked for you*, with `marek.z` — one row of two tall tiles.
 * - **Right, turned**: a squash *Fill in · seat open* — their side on top, both paid (the side with
 *   more people in, the live card's rule), the reader's seat and one empty seat under it.
 */

import { formatLevel, formatPercent, formatZloty } from '@/shared/formatting/ratingFormat';
import { balanceTone } from '@/shared/vocabulary/balancePresentation';

import type { MiniGameCardProps, MiniSeat } from './MiniGameCard';
import type { DeckPlace } from './stageDeckGeometry';
import {
  STAGE_CARD_WORDS,
  STAGE_CAST,
  STAGE_CLUB,
  STAGE_DECK_COPY,
  type StagePerson,
} from './stageHeroCopy';

const WORDS = STAGE_CARD_WORDS;
const { karol, ania, kuba, marek, stas, ola } = STAGE_CAST;
const { front, left, right } = STAGE_DECK_COPY;

/** A person's tile: their poster, their nickname, and their Level — *2,75 · paid* on a booked game. */
function personSeat(person: StagePerson, paid: boolean): MiniSeat {
  const level = formatLevel(person.level);
  return {
    kind: 'person',
    name: person.nickname,
    line: paid ? `${level}${WORDS.lineJoin}${WORDS.paid}` : level,
    look: person.look,
  };
}

/** The reader's own seat, offered. */
const yourSeat = (words: string): MiniSeat => ({ kind: 'yours', words });

/** One side of the forecast bar — `karol.t + You`. */
const sideOf = (...names: readonly string[]): string => names.join(WORDS.sideJoin);

/** The forecast: its figure, its tone, and the two sides, yours first. */
function forecastOf(pct: number, yours: string, theirs: string): MiniGameCardProps['forecast'] {
  return { figure: formatPercent(pct), tone: balanceTone(pct), labels: [yours, theirs] };
}

/** The booking strip: *Sat 16:00 · Ogrody 33*, and the share. */
function bookingOf(card: {
  readonly when: string;
  readonly shareGrosze: number;
}): MiniGameCardProps['booking'] {
  return {
    when: `${card.when}${WORDS.lineJoin}${STAGE_CLUB}`,
    share: formatZloty(card.shareGrosze),
  };
}

/** The three cards — see the module note. Built once: nothing about them changes. */
export const STAGE_DECK_CARDS: Readonly<Record<DeckPlace, MiniGameCardProps>> = {
  front: {
    ribbon: { words: front.ribbon, tone: 'seatOpen', clock: front.clock },
    rows: [
      [personSeat(karol, true), personSeat(ania, true)],
      [personSeat(kuba, true), yourSeat(WORDS.youCompleteIt)],
    ],
    forecast: forecastOf(
      front.forecast,
      sideOf(karol.nickname, WORDS.you),
      sideOf(ania.nickname, kuba.nickname),
    ),
    booking: bookingOf(front),
  },
  left: {
    ribbon: { words: left.ribbon, tone: 'dealt' },
    rows: [[personSeat(marek, false), yourSeat(WORDS.youCompleteIt)]],
    forecast: forecastOf(left.forecast, WORDS.you, marek.nickname),
    booking: bookingOf(left),
  },
  right: {
    ribbon: { words: right.ribbon, tone: 'fillIn', clock: right.clock },
    rows: [
      [personSeat(ola, true), personSeat(stas, true)],
      [yourSeat(WORDS.youQuestion), { kind: 'empty' }],
    ],
    forecast: forecastOf(right.forecast, WORDS.you, sideOf(stas.nickname, ola.nickname)),
    booking: bookingOf(right),
  },
};
