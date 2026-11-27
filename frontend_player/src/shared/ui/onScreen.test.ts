/**
 * **What of a card is on screen** (#804; the Home rows mechanics §9.2, call 2) — at least half of it,
 * across the page's scroll and the rail's, worked through on a 390-wide phone: content 360, a peeking
 * card 266,4 wide, a step of 275,4, the first card 15 in.
 */

import {
  ON_SCREEN_SHARE,
  cardsOnScreen,
  followable,
  scrollToReveal,
  shareInside,
} from './onScreen';

describe('the share of a span inside a view', () => {
  it('is whole inside, none outside, and the part that overlaps between', () => {
    expect(shareInside({ from: 100, size: 200 }, { from: 0, size: 700 })).toBe(1);
    expect(shareInside({ from: 800, size: 200 }, { from: 0, size: 700 })).toBe(0);
    expect(shareInside({ from: 600, size: 200 }, { from: 0, size: 700 })).toBe(0.5);
    expect(shareInside({ from: -150, size: 200 }, { from: 0, size: 700 })).toBe(0.25);
  });

  it('is none for a span with no size', () => {
    expect(shareInside({ from: 10, size: 0 }, { from: 0, size: 700 })).toBe(0);
  });
});

describe('the cards on screen', () => {
  const RAIL = { count: 4, lead: 15, cardWidth: 266.4, step: 275.4 };

  it('is at least half — half counts', () => {
    expect(ON_SCREEN_SHARE).toBe(0.5);
  });

  it('a rail at its start: the first card, never the one peeking under half', () => {
    // The second card stands 290,4 to 556,8: 99,6 of 266,4 in a 390 view — 0,37.
    expect(cardsOnScreen(RAIL, { from: 0, size: 390 }, 1)).toEqual([0]);
  });

  it('a rail scrolled between two cards: both, each over half', () => {
    // 140 along: the first card's last 141,4 of 266,4 left (0,53), the second's first 239,6 in (0,90).
    expect(cardsOnScreen(RAIL, { from: 140, size: 390 }, 1)).toEqual([0, 1]);
    // 150 along, the first is 131,4 in: 0,49, under half.
    expect(cardsOnScreen(RAIL, { from: 150, size: 390 }, 1)).toEqual([1]);
  });

  it('a rail half up the screen: only a card wholly along it is half seen', () => {
    // 140 along, at 0,6 upright: the first 0,53 × 0,6 = 0,32; the second 0,90 × 0,6 = 0,54.
    expect(cardsOnScreen(RAIL, { from: 140, size: 390 }, 0.6)).toEqual([1]);
    expect(cardsOnScreen(RAIL, { from: 0, size: 390 }, 0.5)).toEqual([0]);
    expect(cardsOnScreen(RAIL, { from: 0, size: 390 }, 0.49)).toEqual([]);
  });

  it('a rail off the screen: none', () => {
    expect(cardsOnScreen(RAIL, { from: 0, size: 390 }, 0)).toEqual([]);
  });
});

describe('a followed value', () => {
  it('is nothing until set, and tells every follower each time it moves, until they stop', () => {
    const value = followable<number>();
    const heard: (number | undefined)[] = [];
    const stop = value.follow(() => heard.push(value.get()));

    expect(value.get()).toBeUndefined();
    value.set(3);
    value.set(undefined);
    stop();
    value.set(5);

    expect(heard).toEqual([3, undefined]);
    expect(value.get()).toBe(5);
  });
});

/**
 * **Where a page scrolls to show a line just unfolded** (#820; the brief: *the page eases down just
 * enough to bring it into view*) — a page 700 tall, scrolled 1000 down.
 */
describe('where a page scrolls to show a stretch of it', () => {
  const band = { from: 1000, size: 700 };

  it('stays where it is while the stretch’s foot is in view', () => {
    expect(scrollToReveal({ from: 1200, size: 300 }, band)).toBeUndefined();
    expect(scrollToReveal({ from: 1400, size: 300 }, band)).toBeUndefined();
  });

  it('scrolls just far enough to stand its foot at the page’s foot', () => {
    expect(scrollToReveal({ from: 1500, size: 300 }, band)).toBe(1100);
  });

  it('stands its head at the page’s head when it is taller than the page shows', () => {
    expect(scrollToReveal({ from: 1500, size: 900 }, band)).toBe(1500);
  });

  it('never scrolls back up to show it', () => {
    expect(scrollToReveal({ from: 900, size: 900 }, band)).toBeUndefined();
  });
});
