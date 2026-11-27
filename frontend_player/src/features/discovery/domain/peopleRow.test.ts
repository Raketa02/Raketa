/**
 * **A friend write, drawn on a people row as read** (the Home rows mechanics §13; #822) — the one card
 * moves, the order and everybody else stand, and so does the total: it moves with the next read.
 */

import type { FriendRelation } from '@/features/friends/types';

import { withRelation, type PeopleRow } from './peopleRow';

interface Card {
  readonly playerId: string;
  readonly relation: FriendRelation;
}

const card = (playerId: string): Card => ({ playerId, relation: 'NONE' });

describe('a friend write on a people row', () => {
  const zofia = card('p-zofia');
  const karol = card('p-karol');
  const row: PeopleRow<Card> = {
    people: [zofia, karol],
    total: 14,
  };

  it('moves the one card, and leaves the order and everybody else as read', () => {
    const asked = withRelation(row, 'p-karol', 'SENT');

    expect(asked.people.map((one) => one.playerId)).toEqual(['p-zofia', 'p-karol']);
    expect(asked.people[0]).toBe(zofia);
    expect(asked.people[1]?.relation).toBe('SENT');
  });

  it('keeps the total as read', () => {
    expect(withRelation(row, 'p-karol', 'SENT').total).toBe(14);
  });

  it('draws nothing new for somebody the row does not hold', () => {
    expect(withRelation(row, 'p-nobody', 'SENT').people).toEqual(row.people);
  });
});
