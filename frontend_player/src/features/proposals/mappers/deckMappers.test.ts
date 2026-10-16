/**
 * The deck off the wire: nulls become absences, the kind is read into the switch's spelling, and a
 * weekday outside the week is not drawn.
 */

import {
  ANIA,
  deckCard,
  EWA,
  groupDeck,
  KUBA,
  overlapCells,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';

import { toDeckCard, toGroupDeck, toWireKind } from './deckMappers';

describe('a card’s kind of court (#677)', () => {
  it('reads Indoor or Outdoor as the server promises it, and nothing where it promises neither', () => {
    expect(toDeckCard(deckCard({ indoor: true }))).toMatchObject({ indoor: true });
    expect(toDeckCard(deckCard({ indoor: false }))).toMatchObject({ indoor: false });
    expect(toDeckCard(deckCard({ indoor: null }))).not.toHaveProperty('indoor');
  });
});

describe('a card', () => {
  it('reads every field the card draws', () => {
    const read = toDeckCard(
      deckCard({
        type: 'CHALLENGE',
        kind: 'FOR_FUN',
        challenger: { player_id: KUBA().player_id, name: 'Kuba Wiśniewski' },
        in_count: 2,
        version_count: 2,
        court: 'BOOK_IT_NOW',
        no_free_cancellation: true,
      }),
    );

    expect(read).toMatchObject({
      type: 'CHALLENGE',
      kind: 'forFun',
      challenger: { playerId: KUBA().player_id, name: 'Kuba Wiśniewski' },
      startsAt: '2026-10-03T14:00:00Z',
      club: { name: 'Bonarka Arena' },
      shareGrosze: 3200,
      inCount: 2,
      versionCount: 2,
      openSeatsAfterYourYes: 3,
      court: 'BOOK_IT_NOW',
      noFreeCancellation: true,
      forecast: { pct: 87, provisional: false },
      overlap: { grade: 'SLIM', game: { day: 6, range: 'AFTERNOON' } },
    });
    expect(read?.overlap.cells).toHaveLength(21);
  });

  it('turns a null into an absence — no name, no photograph, no Level, no forecast', () => {
    const read = toDeckCard(
      deckCard({
        club: { id: 'gone', name: null },
        sides: {
          yours: [youTile()],
          theirs: [ANIA({ name: null, level: null }), EWA({ photo_url: 'https://p/e.jpg' })],
        },
        forecast: null,
      }),
    );

    expect(read?.club).toEqual({ id: 'gone' });
    expect(read?.forecast).toBeUndefined();
    const [ania, ewa] = read?.sides.theirs ?? [];
    expect(ania).toEqual({ playerId: ANIA().player_id, isYou: false, isIn: false });
    expect(ewa?.photoUrl).toBe('https://p/e.jpg');
    expect(read?.sides.yours[0]?.isYou).toBe(true);
  });

  it('reads a challenge whose poster withdrew as nobody named', () => {
    expect(
      toDeckCard(deckCard({ type: 'CHALLENGE', challenger: null }))?.challenger,
    ).toBeUndefined();
  });

  it('drops a cell on a day outside the week, and a card whose own game is on one', () => {
    const cells = [
      ...overlapCells(),
      { day: 8, range: 'MORNING' as const, shade: 'BRIGHT' as const },
    ];
    expect(
      toDeckCard(
        deckCard({ overlap: { grade: 'HIGH', cells, game: { day: 6, range: 'EVENING' } } }),
      )?.overlap.cells,
    ).toHaveLength(21);
    expect(
      toDeckCard(
        deckCard({ overlap: { grade: 'HIGH', cells, game: { day: 0, range: 'EVENING' } } }),
      ),
    ).toBeUndefined();
  });
});

describe('the deck', () => {
  it('reads the segments, the badge, the cap and the cards in the order dealt', () => {
    const first = deckCard({
      in_count: 1,
      sides: { yours: [youTile(), ZOFIA()], theirs: [ANIA({ is_in: true })] },
    });
    const second = deckCard();
    const read = toGroupDeck(
      groupDeck({
        cards: [first, second],
        capped_weeks: [{ starts_on: '2026-09-28', booked: 2 }],
      }),
    );

    expect(read.segments).toEqual([
      { kind: 'competitive', count: 2 },
      { kind: 'forFun', count: 0 },
    ]);
    expect(read.gamesBadge).toBe(1);
    expect(read.gamesPerWeek).toBe(2);
    expect(read.cappedWeeks).toEqual([{ startsOn: '2026-09-28', booked: 2 }]);
    expect(read.cards.map((card) => card.proposalId)).toEqual([
      first.proposal_id,
      second.proposal_id,
    ]);
  });

  it('writes the kind back in the wire’s spelling', () => {
    expect(toWireKind('competitive')).toBe('COMPETITIVE');
    expect(toWireKind('forFun')).toBe('FOR_FUN');
  });
});
