/**
 * The wire boundary, with no renderer — the order the list keeps, and the one field whose
 * absence would mean something.
 */

import type { Wire } from '@/test-support/transport';

import type { StarsGiven } from '../domain/stars';

import { toAnswerTheCardRequest, toOpenCards } from './sportsmanshipMappers';

const GAME = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const OTHER_GAME = '1a2b3c4d-0000-4000-8000-000000000009';
const KASIA = 'aaaaaaaa-0000-4000-8000-000000000001';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

describe('the cards, read', () => {
  it('carries the game and everybody else on that court', () => {
    const served: Wire['OpenCardsResponse'] = {
      cards: [{ game_id: GAME, players: [KASIA, TOMEK] }],
    };

    expect(toOpenCards(served)).toEqual([{ gameId: GAME, players: [KASIA, TOMEK] }]);
  });

  /**
   * **Soonest to expire first**, and it is the one thing about this list a client could not
   * compute: expiry runs from the evening, and the games list beside it is ordered newest
   * arrangement first. So nothing re-sorts it.
   */
  it('keeps the served order', () => {
    const served: Wire['OpenCardsResponse'] = {
      cards: [
        { game_id: OTHER_GAME, players: [KASIA] },
        { game_id: GAME, players: [TOMEK] },
      ],
    };

    expect(toOpenCards(served).map((card) => card.gameId)).toEqual([OTHER_GAME, GAME]);
  });

  it('reads an empty list as an empty list, which is the ordinary answer', () => {
    expect(toOpenCards({ cards: [] })).toEqual([]);
  });
});

describe('a card, answered', () => {
  it('sends the stars in the order they were assembled', () => {
    const given: readonly StarsGiven[] = [
      { playerId: KASIA, stars: 5 },
      { playerId: TOMEK, stars: 3 },
    ];

    expect(toAnswerTheCardRequest(given)).toEqual({
      ratings: [
        { player_id: KASIA, stars: 5 },
        { player_id: TOMEK, stars: 3 },
      ],
    });
  });

  /**
   * **`ratings` is present, empty included.** The field is optional on the wire and an empty
   * list is an *answer* — it closes the card without rating anybody — so omitting it would
   * spell the same act two ways and leave the server to decide they were one.
   */
  it('sends an empty list rather than omitting the field', () => {
    const body = toAnswerTheCardRequest([]);

    expect(body).toEqual({ ratings: [] });
    expect(Object.hasOwn(body, 'ratings')).toBe(true);
  });
});
