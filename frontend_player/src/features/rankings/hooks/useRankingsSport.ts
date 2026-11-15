/**
 * **Which sport the Rankings page is on, and the pill's sports** ([#775](https://github.com/Raketa02/Raketa/issues/775);
 * the rankings mechanics §9).
 *
 * The page opens on the sport it was asked for — the trophy's, or the one a pass returns to — else on
 * the trophy's own sport off Home's read (a tap made before Home answered carries none), else on the
 * sport the deck last showed (`groups`' own judgement of the phone's last pick), else padel. It
 * **draws no sport until it knows which** (ADR-0188 §4: no screen draws one choice and then jumps to
 * another), so with nothing asked it waits for Home's read and then the deck's two, the phone's and
 * the ratings'. A ratings read that fails is no level anywhere for this purpose: padel, and all four
 * in the app's order — the page still opens, and a sport with no level says so on its card.
 *
 * **A pick is held while the page is up and kept nowhere.** The phone remembers the view (#777), not
 * the sport: the trophy's sport is the latest result's, and the deck's last sport is the deck's.
 */

import { useState } from 'react';

import { useDeckSport } from '@/features/groups/types';
import { useSkillRatings } from '@/features/onboarding/types';
import { useHomeRanking } from '@/features/proposals/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { openingSport, pillSports } from '../domain/ranking';

export interface RankingsSport {
  /** The pill's sports, rated first — `undefined` while the ratings are read. */
  readonly sports: readonly Sport[] | undefined;
  /** The sport the page is on — `undefined` until it is known. */
  readonly sport: Sport | undefined;
  readonly pick: (sport: Sport) => void;
}

export function useRankingsSport(asked: Sport | undefined): RankingsSport {
  const { sports, opening } = useOpeningSport(asked);
  const [picked, setPicked] = useState<Sport>();

  return { sports, sport: picked ?? opening, pick: setPicked };
}

/** **The pill's sports, and the sport a ranking opens on** — before anything is picked. */
export interface OpeningSport {
  /** All four, rated first — `undefined` while the ratings are read. */
  readonly sports: readonly Sport[] | undefined;
  /** The sport asked for, else the trophy's, else the deck's, else padel — `undefined` until known. */
  readonly opening: Sport | undefined;
}

/**
 * **The reads behind the opening sport and the pill** — the page's, and Home's Top 10 row's
 * ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home rows mechanics §10.3), which opens
 * on the same sport the trophy would and offers the same four, asking for none in particular.
 */
export function useOpeningSport(asked?: Sport): OpeningSport {
  const ratings = useSkillRatings();
  const deck = useDeckSport();
  const trophy = useHomeRanking();

  const unrated = ratings.isError;
  const rated = unrated ? [] : ratings.data?.map((rating) => rating.sport);

  return {
    sports: rated === undefined ? undefined : pillSports(rated),
    opening: openingSport(asked, {
      trophy: trophy === undefined ? undefined : (trophy?.sport ?? null),
      deck: unrated && deck === undefined ? null : deck,
    }),
  };
}
