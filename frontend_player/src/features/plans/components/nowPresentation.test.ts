/**
 * **What the card says, and the three rules that decide it**: the figure takes one of three
 * shapes, the line takes whatever the figure did not, and the gloss is one rule for three rungs
 * with one override.
 *
 * The ladder is `ladder.test.ts`'s and the fold is `gameCard.test.ts`'s; what is asserted here is
 * only the words, against the copy deck rather than against strings wherever a sentence has a
 * home.
 */

import type { Game } from '@/features/games/types';

import { GAME_CARD_NAMES, GAME_DOORS } from '../domain/gameCard';

import {
  CARD_TAG,
  doorLabel,
  GAMES_HEADING,
  NOTHING_LEFT_TO_AGREE,
  cardEyebrow,
  cardFigure,
  cardGloss,
  cardLine,
  cardLineSpoken,
  gameCardLabel,
  gamesHeading,
} from './nowPresentation';
import { STILL_TO_AGREE } from './planPresentation';
import type { Plan } from '../domain/slots';

const GAME_ID = '11111111-0000-4000-8000-000000000001';
const READ_AT = '2026-09-12T09:00:00Z';

const SINGLES_SEATS: Game['seats'] = [
  { side: 'A', playerId: 'me', nickname: 'me_' },
  { side: 'B', playerId: 'them', nickname: 'tomek.p' },
];

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: GAME_ID,
    challengeId: '22222222-0000-4000-8000-000000000002',
    sport: 'padel',
    standing: 'AWAITING_ENTRY',
    seats: SINGLES_SEATS,
    plannedAt: '2026-09-08T09:00:00Z',
    entryClosesAt: '2026-09-19T09:00:00Z',
    proposals: [],
    readAt: READ_AT,
    ...over,
  };
}

function plan(over: Partial<Plan> = {}): Plan {
  return { gameId: GAME_ID, ...over };
}

describe('the heading', () => {
  it('carries the count, which is the one number on this screen', () => {
    expect(gamesHeading(3)).toBe(`${GAMES_HEADING} · 3`);
  });
});

describe('the tag', () => {
  it('names every card this build can draw, and none it cannot', () => {
    const named = GAME_CARD_NAMES.filter((name) => CARD_TAG[name] !== undefined);

    expect(named).toHaveLength(GAME_CARD_NAMES.length - 1);
    expect(CARD_TAG.unreadable).toBeUndefined();
  });

  /** Amber is a clock running. The two quiet endings are neither amber nor red. */
  it('spends urgency on the three cards a clock is running on, and on no others', () => {
    const amber = GAME_CARD_NAMES.filter((name) => CARD_TAG[name]?.variant === 'warn');

    expect(amber).toEqual(['needs-result', 'today', 'confirm']);
    expect(CARD_TAG.uncounted?.variant).toBe('base');
    expect(CARD_TAG['never-played']?.variant).toBe('base');
  });
});

describe('the eyebrow', () => {
  it('reads the court off the seats, and marks only a friendly', () => {
    expect(cardEyebrow(game())).toBe('Singles');
    expect(cardEyebrow(game({ kind: 'FRIENDLY' }))).toBe('Singles · Friendly');
  });

  it('says Doubles for a court of four', () => {
    const four: Game['seats'] = [
      ...SINGLES_SEATS,
      { side: 'A', playerId: 'a', nickname: 'ola_k' },
      { side: 'B', playerId: 'b', nickname: 'marekb' },
    ];

    expect(cardEyebrow(game({ seats: four }))).toBe('Doubles');
  });

  /** A kind this build cannot read drops its clause; every other word on the card stands. */
  it('draws a game whose kind it cannot read as a game', () => {
    const { kind: _dropped, ...unknown } = game({ kind: 'FRIENDLY' });

    expect(cardEyebrow(unknown)).toBe('Singles');
  });
});

describe('the figure and the line, and the hour printed once', () => {
  it('is the hour where there is one, with the day falling to the line', () => {
    const agreed = plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' });

    expect(cardFigure(agreed)).toEqual({ kind: 'hour', value: '18:00' });
    expect(cardLine(agreed)).toBe('Saturday · Zabłocie Sport');
  });

  it('is the weekday where there is a day and no hour, and the line never repeats it', () => {
    const agreed = plan({ place: 'Zabłocie Sport', day: '2026-09-19' });

    expect(cardFigure(agreed)).toEqual({ kind: 'weekday', value: 'Saturday' });
    expect(cardLine(agreed)).toBe('Zabłocie Sport');
  });

  it('is nothing where no day is agreed, and the line is the place alone', () => {
    expect(cardFigure(plan({ place: 'Zabłocie Sport' }))).toBeUndefined();
    expect(cardLine(plan({ place: 'Zabłocie Sport' }))).toBe('Zabłocie Sport');
  });

  it('has no line at all where nothing has been agreed', () => {
    expect(cardFigure(undefined)).toBeUndefined();
    expect(cardLine(undefined)).toBeUndefined();
  });

  /** §20.4: the visible label truncates, the spoken one never does. */
  it('shortens the place for the eye and speaks it whole', () => {
    const long = plan({ place: 'Zabłocie Sport, court 3' });

    expect(cardLineSpoken(long)).toContain('court 3');
    expect(cardLine(long)).not.toBe(cardLineSpoken(long));
  });
});

describe('the gloss', () => {
  const facts = (over: Partial<Game> = {}, agreed?: Plan) => ({
    game: game(over),
    plan: agreed,
    playerId: 'me',
  });

  it('names the next unfilled slot, in slot order, and only that one', () => {
    expect(cardGloss('planning', facts())).toBe(`${STILL_TO_AGREE}: where`);
    expect(cardGloss('planning', facts({}, plan({ place: 'Zabłocie Sport' })))).toBe(
      `${STILL_TO_AGREE}: the day`,
    );
    expect(
      cardGloss('planning', facts({}, plan({ place: 'Zabłocie Sport', day: '2026-09-19' }))),
    ).toBe(`${STILL_TO_AGREE}: the hour`);
  });

  /** One rule for three rungs — *Today* is the case that justifies it. */
  it('is the same rule on Today, which may genuinely still be missing an hour', () => {
    expect(
      cardGloss('today', facts({}, plan({ place: 'Zabłocie Sport', day: '2026-09-12' }))),
    ).toBe(`${STILL_TO_AGREE}: the hour`);
  });

  it('says nothing is left once all three are filled', () => {
    const full = plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' });

    expect(cardGloss('game-on', facts({}, full))).toBe(NOTHING_LEFT_TO_AGREE);
    expect(cardGloss('today', facts({}, full))).toBe(NOTHING_LEFT_TO_AGREE);
  });

  it('overrides the slot rule with the time left when a result is owed', () => {
    expect(cardGloss('needs-result', facts({ entryClosesAt: '2026-09-13T09:00:00Z' }))).toBe(
      '24 hours left',
    );
  });

  /** Everything that is not a rung already has a sentence, and it is `features/games`'. */
  it('says what an ended game is, in the sentence the screen behind it says', () => {
    expect(cardGloss('counted', facts({ standing: 'CONFIRMED' }))).toBe('Agreed.');
    expect(cardGloss('uncounted', facts({ standing: 'UNSCORED' }))).toBe('Nobody agreed a score.');
  });
});

describe('what the card announces', () => {
  /**
   * §24.5: the tag, the eyebrow, the figure and line, the gloss, then the door's verb — and the
   * sport, because a listener has no picture of the court and the tag's dot is legal only where
   * the sport is named.
   */
  it('says the card’s name, the sport, what is agreed, the gloss and the door’s verb', () => {
    const said = gameCardLabel({
      name: 'game-on',
      sportName: 'Padel',
      game: game(),
      plan: plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' }),
      playerId: 'me',
      door: 'open',
    });

    expect(said).toBe(
      'Game on. Padel, singles. 18:00. Saturday · Zabłocie Sport. Nothing left to agree. Open',
    );
  });

  it('ends with nothing extra where the card carries no door', () => {
    const said = gameCardLabel({
      name: 'counted',
      sportName: 'Padel',
      game: game({ standing: 'CONFIRMED' }),
      plan: undefined,
      playerId: 'me',
      door: undefined,
    });

    expect(said).toBe('Counted. Padel, singles. Agreed.');
    for (const door of GAME_DOORS) expect(said).not.toContain(doorLabel(door));
  });
});
