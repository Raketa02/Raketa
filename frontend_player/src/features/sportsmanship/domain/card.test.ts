/**
 * The join — a card is ids, and the words come from the game it is drawn on.
 *
 * `GET /sportsmanship` answers *ids and nothing else*: what the people are called and which
 * sport it was come from the games list the card is drawn beside, joined on `game_id`, because
 * repeating them would be a second copy of an evening's description and the day the two
 * disagreed the card would name somebody the game did not.
 */

import { cardOnCourt, type OpenCard, type RatedCourt } from './card';

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
    { playerId: ME, name: 'ada' },
    { playerId: KASIA, name: 'kasia_w' },
    { playerId: TOMEK, name: 'tomek.p' },
    { playerId: MAREK, name: 'marekb' },
  ],
};

/** Both opponents **and** your partner — the person who saw you play closest. */
const CARD: OpenCard = { gameId: GAME, players: [KASIA, TOMEK, MAREK] };

describe('a card on its court', () => {
  it('names everybody the card asks about, in the line-up’s own order', () => {
    const drawn = cardOnCourt([CARD], DOUBLES);

    expect(drawn?.subjects).toEqual([
      { playerId: KASIA, name: { kind: 'player', name: 'kasia_w' } },
      { playerId: TOMEK, name: { kind: 'player', name: 'tomek.p' } },
      { playerId: MAREK, name: { kind: 'player', name: 'marekb' } },
    ]);
  });

  it('carries the sport, which is what tells a padel evening from a squash one', () => {
    const drawn = cardOnCourt([CARD], DOUBLES);

    expect(drawn?.court.sport).toBe('padel');
  });

  /**
   * The list read answers about **every** court still waiting, and the screen asking is about
   * one — so picking the wrong row would put another evening's people on this evening's card,
   * which is the one way this join can be wrong and still render.
   */
  it('takes this court’s card out of a list that holds other people’s evenings', () => {
    const other: OpenCard = { gameId: OTHER_GAME, players: [KASIA] };
    const singles: RatedCourt = {
      gameId: OTHER_GAME,
      sport: 'squash',
      seats: [
        { playerId: ME, name: 'ada' },
        { playerId: KASIA, name: 'kasia_w' },
      ],
    };

    expect(cardOnCourt([other, CARD], DOUBLES)?.card.gameId).toBe(GAME);
    expect(cardOnCourt([other, CARD], singles)?.card.gameId).toBe(OTHER_GAME);
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

    const drawn = cardOnCourt([CARD], lost);

    expect(drawn?.subjects[1]).toEqual({ playerId: TOMEK, name: { kind: 'unknown' } });
  });

  /**
   * **The ordinary answer**, and it covers all four absences at once: not a day old, week run
   * out, already answered, result not settled. Every one of them is *not on the server\'s list*,
   * and none of them is re-derived here — which is why there is nothing else to assert about
   * them and nothing to draw differently for any of them.
   */
  it('draws nothing when this court is not on the list', () => {
    expect(cardOnCourt([], DOUBLES)).toBeUndefined();
    expect(cardOnCourt([{ gameId: OTHER_GAME, players: [KASIA] }], DOUBLES)).toBeUndefined();
  });
});
