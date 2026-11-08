/**
 * **The hero's *It's a game!*, composed from the copy** ([#787](https://github.com/Raketa02/Raketa/issues/787);
 * design system 12.2, mocks 7–8) — the splash's `stageDeckPresentation`: who faces whom, the letters
 * over each poster, and the line under the word.
 *
 * - **The sides are the front card's**, the side the swipe completed first: `karol.t` and You
 *   against `ania.k` and `kuba.w`.
 * - **The letters are the yes screen's** (`handleInitials`, ADR-0167 §3, as its note of 2026-11-08
 *   extends it to this picture): *KT*, *AK*, *KW* over the posters, and **none over You**.
 * - **The line is the booked court's**: *Saturday 16:00 · Ogrody 33 · Court 6 · 27 zł each* — the
 *   front card's hour as a booked game says the day, its club, the court the booking gave it, and
 *   its share.
 */

import { handleInitials } from '@/shared/formatting/playerName';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import type { CourtPosterLook } from '@/shared/ui';

import {
  STAGE_CARD_WORDS,
  STAGE_CAST,
  STAGE_CLUB,
  STAGE_DECK_COPY,
  STAGE_SPLASH_COPY,
  STAGE_YOU_LOOK,
  type StagePerson,
} from './stageHeroCopy';

/** One face on the splash: its poster, and the letters over it — none for You. */
export interface SplashFace {
  readonly key: string;
  readonly look: CourtPosterLook;
  readonly letters?: string;
}

const COPY = STAGE_SPLASH_COPY;
const { karol, ania, kuba } = STAGE_CAST;

const faceOf = (person: StagePerson): SplashFace => ({
  key: person.nickname,
  look: person.look,
  letters: handleInitials(person.nickname),
});

/** The reader, bare. */
const YOU: SplashFace = { key: 'you', look: STAGE_YOU_LOOK };

/** Everything the splash draws — see the module note. */
export const STAGE_SPLASH = {
  yours: [faceOf(karol), YOU],
  theirs: [faceOf(ania), faceOf(kuba)],
  versus: COPY.versus,
  word: COPY.word,
  line: [
    COPY.when,
    STAGE_CLUB,
    COPY.court,
    `${formatZloty(STAGE_DECK_COPY.front.shareGrosze)} ${COPY.each}`,
  ].join(STAGE_CARD_WORDS.lineJoin),
} as const satisfies {
  readonly yours: readonly SplashFace[];
  readonly theirs: readonly SplashFace[];
  readonly versus: string;
  readonly word: string;
  readonly line: string;
};
