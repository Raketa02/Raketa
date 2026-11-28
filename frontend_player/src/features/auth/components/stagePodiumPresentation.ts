/**
 * **Sign-up's podium, composed from the copy** ([#788](https://github.com/Rakieta02/Rakieta/issues/788);
 * design system 12.2, mock 5) — who stands on which step, the letters over each poster and the name
 * under it.
 *
 * - **You on the first step**, under mock 5's *TK* — copy, nobody's initials (`stageHeroCopy`'s note)
 *   — on the reader's poster, the one the splash draws them in.
 * - **`stas.w` on the second and `ines.d` on the third**, each under the letters the yes tile cuts
 *   from a nickname (`handleInitials`, ADR-0167 §3, as its note of 2026-11-09 extends it to this
 *   picture): *SW* and *ID*.
 * - **Each step reads its place**, 1, 2 and 3, as the live podium's do.
 */

import { handleInitials } from '@/shared/formatting/playerName';
import type { CourtPosterLook } from '@/shared/ui';

import { STAGE_CAST, STAGE_PODIUM_COPY, STAGE_YOU_LOOK, type StagePerson } from './stageHeroCopy';
import type { PodiumPlace } from './stagePodiumGeometry';

/** Somebody on the podium: the number on their step, their name under their tile, its letters. */
export interface PodiumPlayer {
  /** The number on their step — 1, 2 or 3. */
  readonly rank: number;
  readonly name: string;
  readonly letters: string;
  readonly look: CourtPosterLook;
}

/** `person` standing on the step numbered `rank`. */
const standing = (rank: number, person: StagePerson): PodiumPlayer => ({
  rank,
  name: person.nickname,
  letters: handleInitials(person.nickname),
  look: person.look,
});

/** Everything the podium draws — see the module note. */
export const STAGE_PODIUM: Readonly<Record<PodiumPlace, PodiumPlayer>> = {
  first: {
    rank: 1,
    name: STAGE_PODIUM_COPY.you,
    letters: STAGE_PODIUM_COPY.youLetters,
    look: STAGE_YOU_LOOK,
  },
  second: standing(2, STAGE_CAST.stas),
  third: standing(3, STAGE_CAST.ines),
};
