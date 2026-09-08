/**
 * The join — a card is ids, and the words come from the game beside it.
 *
 * `GET /sportsmanship` answers *ids and nothing else*: what the people are called and which
 * sport it was come from the games list the card is drawn beside, joined on `game_id`, because
 * repeating them would be a second copy of an evening's description and the day the two
 * disagreed the card would name somebody the game did not.
 */

import { cardsOnCourts, type OpenCard, type RatedCourt } from './card';

const GAME = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const OTHER_GAME = '1a2b3c4d-0000-4000-8000-000000000009';

const ME = '11111111-2222-4333-8444-555555555555';
const KASIA = 'aaaaaaaa-0000-4000-8000-000000000001';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const MAREK = 'cccccccc-0000-4000-8000-000000000003';

const DOUBLES: RatedCourt = {
  gameId: GAME,
  sport: 'padel',
  seats: [
    { playerId: ME, nickname: 'ada' },
    { playerId: KASIA, nickname: 'kasia_w' },
    { playerId: TOMEK, nickname: 'tomek.p' },
    { playerId: MAREK, nickname: 'marekb' },
  ],
};

/** Both opponents **and** your partner — the person who saw you play closest. */
const CARD: OpenCard = { gameId: GAME, players: [KASIA, TOMEK, MAREK] };

describe('a card on its court', () => {
  it('names everybody the card asks about, in the line-up’s own order', () => {
    const [drawn] = cardsOnCourts([CARD], [DOUBLES]);

    expect(drawn?.subjects).toEqual([
      { playerId: KASIA, name: { kind: 'player', nickname: 'kasia_w' } },
      { playerId: TOMEK, name: { kind: 'player', nickname: 'tomek.p' } },
      { playerId: MAREK, name: { kind: 'player', nickname: 'marekb' } },
    ]);
  });

  it('carries the sport, which is what tells a padel evening from a squash one', () => {
    const [drawn] = cardsOnCourts([CARD], [DOUBLES]);

    expect(drawn?.court.sport).toBe('padel');
  });

  it('keeps the served order, which is soonest to expire first', () => {
    const soonest: OpenCard = { gameId: OTHER_GAME, players: [KASIA] };
    const singles: RatedCourt = {
      gameId: OTHER_GAME,
      sport: 'squash',
      seats: [
        { playerId: ME, nickname: 'ada' },
        { playerId: KASIA, nickname: 'kasia_w' },
      ],
    };

    const drawn = cardsOnCourts([soonest, CARD], [DOUBLES, singles]);

    expect(drawn.map((one) => one.card.gameId)).toEqual([OTHER_GAME, GAME]);
  });

  /**
   * A seat `users` can no longer answer for. The seat keeps its place on the games screens and
   * the person keeps their place here: they were on the court and they can still be rated, so
   * the row draws the unknown player's `?` rather than dropping somebody from the card.
   */
  it('draws the unknown player for a seat with no handle left', () => {
    const lost: RatedCourt = {
      ...DOUBLES,
      seats: DOUBLES.seats.map((seat) => (seat.playerId === TOMEK ? { playerId: TOMEK } : seat)),
    };

    const [drawn] = cardsOnCourts([CARD], [lost]);

    expect(drawn?.subjects[1]).toEqual({ playerId: TOMEK, name: { kind: 'unknown' } });
  });

  /**
   * The games list is where every word on this card comes from, so a card whose game is not
   * in it has nothing to say — and that is a real state rather than a defensive one: a game
   * whose sport or whose court this build cannot read is dropped by the games mapper whole.
   */
  it('draws nothing for a card whose game is not on the list', () => {
    expect(cardsOnCourts([CARD], [])).toEqual([]);
  });
});
