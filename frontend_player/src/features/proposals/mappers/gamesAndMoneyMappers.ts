/**
 * **Games & money, off the wire and back** — the wire boundary for the two limits (#554). Nothing
 * narrows on the way in: every field is drawn, and *Off* is `null` on both sides.
 */

import type { components } from '@/generated/schema';

import type { GamesAndMoney, Limits } from '../domain/gamesAndMoney';

type Schemas = components['schemas'];

export function toGamesAndMoney(wire: Schemas['GamesAndMoneyResponse']): GamesAndMoney {
  return {
    gamesPerWeek: wire.games_per_week,
    mostIllPayGrosze: wire.most_ill_pay_grosze,
    gamesPerWeekRange: {
      least: wire.games_per_week_range.least,
      most: wire.games_per_week_range.most,
    },
    ceilingChoicesGrosze: wire.most_ill_pay_choices_grosze,
  };
}

/** Both values, every time — the route replaces the pair. */
export function toGamesAndMoneyRequest(limits: Limits): Schemas['GamesAndMoneyRequest'] {
  return {
    games_per_week: limits.gamesPerWeek,
    most_ill_pay_grosze: limits.mostIllPayGrosze,
  };
}
