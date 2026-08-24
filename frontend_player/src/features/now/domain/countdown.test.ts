/**
 * The feature's one derivation, and the ask it feeds.
 *
 * Every case passes `now` rather than moving a clock, because the module takes it
 * as a parameter for exactly this reason.
 */

import type { MatchCard, ComposedScreen, Shelf } from './ComposedScreen';
import {
  SECONDS_BAND_MS,
  countdownLabel,
  momentsOnScreen,
  msUntilNextZero,
  soonestMs,
  remainingMs,
  repaintDelayMs,
} from './countdown';

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
    departure: undefined,
    score: undefined,
    act: undefined,
    mayDepart: false,
    fit: undefined,
    emphasis: false,
    ...overrides,
  };
}

function screen(overrides: Partial<ComposedScreen> = {}): ComposedScreen {
  return {
    offers: { cards: [] },
    yourMatches: { cards: [] },
    shelves: { blocks: [] },
    debt: undefined,
    ...overrides,
  };
}

function shelf(cards: Shelf['cards']): Shelf {
  return { kind: 'shelf', code: 'bestFit', title: 'Best fit for you', caption: undefined, cards };
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
      shelves: { blocks: [shelf([matchCard({ clock: '2026-08-23T13:00:00Z' })])] },
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
        blocks: [
          // A door holds no cards and no moment of its own, so a screen showing one
          // still arms nothing.
          { kind: 'door', code: 'noRunYet', copy: { line: 'x', action: 'y' } },
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

  it('answers the same three ways for a bare list of moments', () => {
    // The same loop, over the moments a screen off Now is counting to rather than
    // over a composed screen — one implementation, because two would eventually
    // differ on the case above and only one of them would be tested.
    expect(soonestMs(['2026-08-23T12:03:00Z', '2026-08-23T12:09:00Z'], NOON)).toBe(3 * 60 * 1000);
    expect(soonestMs(['2026-08-23T11:00:00Z', '2026-08-23T12:07:00Z'], NOON)).toBe(7 * 60 * 1000);
    expect(soonestMs(['2026-08-23T11:00:00Z'], NOON)).toBeUndefined();
    expect(soonestMs([], NOON)).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// What the clock slot reads, and how often it is redrawn
// ---------------------------------------------------------------------------

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

describe('the countdown reads in four bands', () => {
  it('draws a clock face under ten minutes', () => {
    // `ADR-0088`'s own spelling. The seconds are the point: this is the band in
    // which a seat claim's five minutes run out.
    expect(countdownLabel(4 * MINUTE + 37 * SECOND)).toBe('4:37');
    expect(countdownLabel(90 * SECOND)).toBe('1:30');
    expect(countdownLabel(9 * SECOND)).toBe('0:09');
  });

  it('draws minutes, then hours, then days above it', () => {
    // The three lower bands are `docs/value-formatting.md`'s duration row verbatim
    // — space before the unit — so a length of time reads the same here as it does
    // in the club console.
    expect(countdownLabel(42 * MINUTE)).toBe('42 min');
    expect(countdownLabel(2 * HOUR + 14 * MINUTE)).toBe('2 h 14 min');
    expect(countdownLabel(3 * DAY + 4 * HOUR)).toBe('3 d 4 h');
  });

  it('drops a zero component rather than printing it', () => {
    expect(countdownLabel(2 * HOUR)).toBe('2 h');
    expect(countdownLabel(3 * DAY)).toBe('3 d');
  });

  it('reads zero for a moment already behind us, never a negative', () => {
    // Reaching zero is the fourth ask, so the answer is already on its way: the
    // card holds still and says so. An empty string would collapse the slot under
    // the player's thumb, and a negative would say a match starts in −4 minutes.
    expect(countdownLabel(0)).toBe('0:00');
    expect(countdownLabel(-90 * SECOND)).toBe('0:00');
  });

  it('never prints a digit the cadence cannot keep true', () => {
    // The one property that ties the two halves together: seconds appear in
    // exactly the band that repaints every second. A label showing `:07` while the
    // screen redraws once a minute is `ADR-0053`'s *"frozen number reads as broken
    // rather than static"*, arrived at by drawing instead of by polling.
    const withSeconds = /:\d\d$/;

    expect(withSeconds.test(countdownLabel(SECONDS_BAND_MS - 1))).toBe(true);
    expect(repaintDelayMs(SECONDS_BAND_MS - 1)).toBe(SECOND);

    expect(withSeconds.test(countdownLabel(SECONDS_BAND_MS))).toBe(false);
    expect(repaintDelayMs(SECONDS_BAND_MS + 1)).toBe(MINUTE);
  });

  it('switches on the same instant in both halves', () => {
    expect(countdownLabel(SECONDS_BAND_MS)).toBe('10 min');
    expect(repaintDelayMs(SECONDS_BAND_MS)).toBe(SECOND);
  });
});

describe('the repaint cadence', () => {
  it('arms nothing when nothing on the screen is counting', () => {
    // A screen of cancelled and played cards costs a phone in a pocket nothing.
    expect(repaintDelayMs(undefined)).toBeUndefined();
  });

  it('follows the soonest moment on the screen, not each card', () => {
    // One screen-wide clock (`ADR-0088`). A card three weeks out redraws once a
    // second while a seat claim beside it is running, which is the cheap half of
    // the bargain that keeps the claim honest.
    const claim = matchCard({ matchId: 'claim', claimExpiresAt: '2026-08-23T12:04:00Z' });
    const distant = matchCard({ matchId: 'far', clock: '2026-09-12T18:00:00Z' });

    const soonest = msUntilNextZero(screen({ yourMatches: { cards: [distant, claim] } }), NOON);

    expect(repaintDelayMs(soonest)).toBe(SECOND);
  });
});
