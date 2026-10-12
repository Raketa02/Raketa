import type { Sport } from '@/features/club-details/mappers';

import { gameName } from '../copy';
import type { CancelGivesBack, ClubHour, GameCourt } from '../mappers';

/** **The game a dialog asks about**: which booking, named as the page names it. */
export interface Asked {
  readonly id: string;
  /** *the 19:00 game on Sat 3 Oct*. */
  readonly name: string;
  readonly hour: ClubHour;
  readonly court: GameCourt;
  readonly sport: Sport;
}

/** **The game the cancel dialog asks about**, with what a cancel would do with its money. */
export interface AskedToCancel extends Asked {
  readonly givesBack: CancelGivesBack;
}

/** A row of the day, as the question about it names it. */
export function askedAbout(game: Omit<Asked, 'name'>): Asked {
  return {
    id: game.id,
    name: gameName(game.hour),
    hour: game.hour,
    court: game.court,
    sport: game.sport,
  };
}
