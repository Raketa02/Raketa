/**
 * Games & money off the wire and back: the two limits and the form's offer read whole, and a save
 * sending both values with *Off* as `null`.
 */

import { toGamesAndMoney, toGamesAndMoneyRequest } from './gamesAndMoneyMappers';

describe('Games & money', () => {
  it('reads the two limits and what the form offers', () => {
    expect(
      toGamesAndMoney({
        games_per_week: 4,
        most_ill_pay_grosze: 4500,
        games_per_week_range: { least: 1, most: 7 },
        most_ill_pay_choices_grosze: [3500, 4500, 6000],
      }),
    ).toEqual({
      gamesPerWeek: 4,
      mostIllPayGrosze: 4500,
      gamesPerWeekRange: { least: 1, most: 7 },
      ceilingChoicesGrosze: [3500, 4500, 6000],
    });
  });

  it('sends both values, and Off as null', () => {
    expect(toGamesAndMoneyRequest({ gamesPerWeek: 2, mostIllPayGrosze: null })).toEqual({
      games_per_week: 2,
      most_ill_pay_grosze: null,
    });
  });
});
