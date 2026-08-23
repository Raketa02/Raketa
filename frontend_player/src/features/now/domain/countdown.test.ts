/**
 * The feature's one derivation, and the ask it feeds.
 *
 * Every case passes `now` rather than moving a clock, because the module takes it
 * as a parameter for exactly this reason.
 */

import type { MatchCard, ComposedScreen, Shelf } from './ComposedScreen';
import { momentsOnScreen, msUntilNextZero, remainingMs } from './countdown';

const NOON = Date.parse('2026-08-23T12:00:00Z');

function matchCard(overrides: Partial<MatchCard> = {}): MatchCard {
  return {
    kind: 'match',
    matchId: 'm-1',
    clock: undefined,
    claimExpiresAt: undefined,
    where: {
      clubId: 'c-1',
      clubName: 'Sunset Padel',
      zone: 'Europe/Warsaw',
      cover: 'indoor',
      distanceKm: undefined,
    },
    price: { amount: 3800, currency: 'PLN' },
    situation: 'forming',
    status: undefined,
    ...overrides,
  };
}

function screen(overrides: Partial<ComposedScreen> = {}): ComposedScreen {
  return {
    offers: { cards: [] },
    yourMatches: { cards: [] },
    shelves: { shelves: [] },
    debt: undefined,
    ...overrides,
  };
}

function shelf(cards: Shelf['cards']): Shelf {
  return { code: 'bestFit', title: 'Best fit for you', caption: undefined, cards };
}

describe('subtracting a moment from the current time', () => {
  it('answers what is left', () => {
    expect(remainingMs('2026-08-23T12:05:00Z', NOON)).toBe(5 * 60 * 1000);
  });

  it('goes negative once the moment has passed', () => {
    expect(remainingMs('2026-08-23T11:59:00Z', NOON)).toBe(-60 * 1000);
  });

  it('answers nothing at all for a moment that does not parse', () => {
    // A contract failure, not a state. A number here would render as decades.
    expect(remainingMs('not an instant', NOON)).toBeUndefined();
  });
});

describe('the moments a screen carries', () => {
  it('collects both slots on a match card, from all three regions', () => {
    const composed = screen({
      offers: { cards: [matchCard({ clock: '2026-08-23T12:04:00Z' })] },
      yourMatches: {
        cards: [
          matchCard({
            clock: '2026-08-23T19:00:00Z',
            claimExpiresAt: '2026-08-23T12:05:00Z',
          }),
        ],
      },
      shelves: { shelves: [shelf([matchCard({ clock: '2026-08-23T13:00:00Z' })])] },
    });

    expect([...momentsOnScreen(composed)].sort()).toEqual([
      '2026-08-23T12:04:00Z',
      '2026-08-23T12:05:00Z',
      '2026-08-23T13:00:00Z',
      '2026-08-23T19:00:00Z',
    ]);
  });

  it('has nothing to collect from a person or a club card', () => {
    const composed = screen({
      shelves: {
        shelves: [
          shelf([
            { kind: 'person', playerId: 'p-1', nickname: 'ada' },
            { kind: 'club', clubId: 'c-2', name: 'Kraków Padel', distanceKm: 2 },
          ]),
        ],
      },
    });

    expect(momentsOnScreen(composed)).toEqual([]);
  });
});

describe('when the next countdown reaches zero', () => {
  it('is the soonest moment that has not yet passed', () => {
    const composed = screen({
      offers: { cards: [matchCard({ clock: '2026-08-23T12:09:00Z' })] },
      yourMatches: { cards: [matchCard({ clock: '2026-08-23T12:03:00Z' })] },
    });

    expect(msUntilNextZero(composed, NOON)).toBe(3 * 60 * 1000);
  });

  it('skips a moment already behind us rather than answering zero', () => {
    // Answering zero would fetch on every render for the rest of the screen's life.
    const composed = screen({
      offers: { cards: [matchCard({ clock: '2026-08-23T11:00:00Z' })] },
      yourMatches: { cards: [matchCard({ clock: '2026-08-23T12:07:00Z' })] },
    });

    expect(msUntilNextZero(composed, NOON)).toBe(7 * 60 * 1000);
  });

  it('answers nothing when every moment has passed', () => {
    const composed = screen({
      offers: { cards: [matchCard({ clock: '2026-08-23T11:00:00Z' })] },
    });

    expect(msUntilNextZero(composed, NOON)).toBeUndefined();
  });

  it('answers nothing for a screen with no moments at all', () => {
    expect(msUntilNextZero(screen(), NOON)).toBeUndefined();
  });
});
