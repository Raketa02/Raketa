/**
 * The wire boundary: what the mapper keeps, what it resolves, and what it drops.
 *
 * Every fixture below is typed from the generated schema, so a contract change
 * fails `pnpm typecheck` here rather than failing an assertion somewhere confusing.
 */

import { clubCard, emptyNow, matchCard, personCard, shelf } from '@/test-support/now';
import type { Wire } from '@/test-support/transport';

import { toComposedScreen } from './nowMappers';

/**
 * Index into a list, refusing an absent element rather than asserting one away.
 *
 * `noUncheckedIndexedAccess` is on, and a `!` here would be the one place in the
 * suite where a shape is claimed rather than checked — which is the shape of the
 * bug these tests exist to find.
 */
function nth<T>(list: readonly T[], index: number): T {
  const item = list[index];
  if (item === undefined) throw new Error(`no element at ${index} of ${list.length}`);
  return item;
}

describe('the three regions', () => {
  it('are present and empty for a player with nothing', () => {
    const screen = toComposedScreen(emptyNow());

    expect(screen.offers.cards).toEqual([]);
    expect(screen.yourMatches.cards).toEqual([]);
    expect(screen.shelves.shelves).toEqual([]);
    expect(screen.debt).toBeUndefined();
  });

  it('keep the server’s order rather than sorting anything', () => {
    const screen = toComposedScreen({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [
          matchCard({ matchId: 'second' }),
          matchCard({ matchId: 'first' }),
          matchCard({ matchId: 'third' }),
        ],
      },
    });

    expect(screen.yourMatches.cards.map((card) => card.matchId)).toEqual([
      'second',
      'first',
      'third',
    ]);
  });
});

describe('a match card', () => {
  it('carries both moments, and neither when the server sent neither', () => {
    const withClock = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            matchCard({
              matchId: 'm-1',
              clock: '2026-08-23T19:00:00Z',
              seatClaimExpiresAt: '2026-08-23T12:05:00Z',
            }),
          ],
        },
      }).offers.cards,
      0,
    );

    expect(withClock.clock).toBe('2026-08-23T19:00:00Z');
    expect(withClock.claimExpiresAt).toBe('2026-08-23T12:05:00Z');

    const bare = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: { stamp: 1, cards: [matchCard({ matchId: 'm-2' })] },
      }).offers.cards,
      0,
    );

    // `null` on the wire becomes absent here — one spelling of *nothing*, so no
    // reader has to know both.
    expect(bare.clock).toBeUndefined();
    expect(bare.claimExpiresAt).toBeUndefined();
  });

  it('resolves the situation to a sentence, with the spine’s own facts in it', () => {
    const card = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            matchCard({ matchId: 'm-1', situation: 'cancelledClub', clubName: 'Sunset Padel' }),
          ],
        },
      }).offers.cards,
      0,
    );

    expect(card.status?.line).toBe('Cancelled by Sunset Padel — everybody refunded.');
    expect(card.status?.tag).toBe('Cancelled');
    expect(card.status?.tone).toBe('ended');
  });

  it('formats the amount once, through the repo’s shared table', () => {
    const card = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [matchCard({ matchId: 'm-1', situation: 'confirmed', amount: 12000 })],
        },
      }).offers.cards,
      0,
    );

    expect(card.status?.line).toContain('120,00 zł');
    expect(card.price).toEqual({ amount: 12000, currency: 'PLN' });
  });

  it('leaves the sentence absent for a situation this build has never heard of', () => {
    // The one case a typecheck can never reach: an installed phone meeting a
    // thirty-seventh name. The card keeps its spine and loses exactly the thing that
    // is actually missing.
    const card = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            {
              ...matchCard({ matchId: 'm-1' }),
              situation: {
                situation: 'seatTransferred' as Wire['Situation'],
                facts: { hold: null, cause: null },
              },
            },
          ],
        },
      }).offers.cards,
      0,
    );

    expect(card.situation).toBe('seatTransferred');
    expect(card.status).toBeUndefined();
    expect(card.where.clubName).toBe('Sunset Padel');
    expect(card.price.amount).toBe(3800);
  });

  it('keeps the club’s zone, its roof and its distance on the spine', () => {
    const card = nth(
      toComposedScreen({
        ...emptyNow(),
        offers: { stamp: 1, cards: [matchCard({ matchId: 'm-1' })] },
      }).offers.cards,
      0,
    );

    expect(card.where.zone).toBe('Europe/Warsaw');
    expect(card.where.cover).toBe('indoor');
    expect(card.where.distanceKm).toBe(2.4);
  });
});

describe('a shelf', () => {
  it('takes its words from its code, because no title crosses the wire', () => {
    const shelves = toComposedScreen({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [shelf('bestFit', []), shelf('fullWorthWaiting', [], 'undeclaredPreferences')],
      },
    }).shelves.shelves;

    expect(nth(shelves, 0).title).toBe('Best fit for you');
    expect(nth(shelves, 0).caption).toBeUndefined();
    expect(nth(shelves, 1).title).toBe('Full, but worth waiting for');
    expect(nth(shelves, 1).caption).toBe(
      'Ordered on what we know — some of your preferences for this sport are not set.',
    );
  });

  it('has no title for a code this build has never heard of', () => {
    const shelves = toComposedScreen({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [shelf('mostBooked' as Wire['ShelfCode'], [])],
      },
    }).shelves.shelves;

    expect(nth(shelves, 0).code).toBe('mostBooked');
    expect(nth(shelves, 0).title).toBeUndefined();
  });

  it('holds all three card types, discriminated', () => {
    const cards = nth(
      toComposedScreen({
        ...emptyNow(),
        shelves: {
          stamp: 1,
          shelves: [
            shelf('newPlayers', [
              matchCard({ matchId: 'm-1' }),
              personCard('p-1', 'ada'),
              clubCard('c-1', 'Kraków Padel'),
            ]),
          ],
        },
      }).shelves.shelves,
      0,
    ).cards;

    expect(cards.map((card) => card.kind)).toEqual(['match', 'person', 'club']);
  });
});

describe('the one fact about the viewer', () => {
  it('carries the amount and the boolean, and never derives one from the other', () => {
    const screen = toComposedScreen({
      ...emptyNow(),
      debt: { owed: { amount: 3000, currency: 'PLN' }, blocked: true },
    });

    expect(screen.debt).toEqual({ owed: { amount: 3000, currency: 'PLN' }, blocked: true });
  });

  it('keeps a debt the server says blocks nothing', () => {
    // Concluding *she owes, therefore create is dead* would be a rule, and the phone
    // holds none.
    const screen = toComposedScreen({
      ...emptyNow(),
      debt: { owed: { amount: 3000, currency: 'PLN' }, blocked: false },
    });

    expect(screen.debt?.blocked).toBe(false);
  });
});
