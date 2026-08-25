/**
 * The poster's one contract: the same player id produces the same drawing, on this phone,
 * on their next one, and after a reinstall.
 */

import { COURT_POSTER_SPACE } from '@/shared/ui';

import { COURT_POSTER_COUNT, COURT_POSTER_FRAMINGS, courtPosterFor } from './courtPosterFraming';

const PLAYER = '11111111-2222-4333-8444-555555555555';

describe('the poster a player has', () => {
  it('is the same one every time it is asked for', () => {
    expect(courtPosterFor(PLAYER)).toEqual(courtPosterFor(PLAYER));
  });

  it('is not derived from anything but the id — nothing is stored and nothing is seeded', () => {
    // A second, unrelated id in between: a hash that had a counter or a cursor in it would
    // hand back a different poster on the way back.
    const first = courtPosterFor(PLAYER);
    courtPosterFor('99999999-8888-4777-8666-555555555555');

    expect(courtPosterFor(PLAYER)).toEqual(first);
  });

  it('is a different one for a different player, at least usually', () => {
    const posters = new Set(
      Array.from({ length: 200 }, (_unused, at) => JSON.stringify(courtPosterFor(`player-${at}`))),
    );

    // Not all 48 — 200 ids into 48 posters will collide — but a hash that spread badly
    // would land most of them on a handful, and that is what this catches.
    expect(posters.size).toBeGreaterThan(COURT_POSTER_COUNT / 2);
  });

  it('varies its framing and its ball independently', () => {
    const posters = Array.from({ length: 400 }, (_unused, at) => courtPosterFor(`p-${at}`));

    const framings = new Set(posters.map((poster) => JSON.stringify(poster.view)));
    const balls = new Set(posters.map((poster) => JSON.stringify(poster.ball)));

    // Tied together, the ball would take exactly one position per framing and there would
    // be as many distinct balls as framings.
    expect(framings.size).toBe(COURT_POSTER_FRAMINGS.length);
    expect(balls.size).toBeGreaterThan(framings.size);
  });
});

describe('every framing this file hands out', () => {
  it('is a window inside the court the design system draws', () => {
    for (const view of COURT_POSTER_FRAMINGS) {
      expect(view.x).toBeGreaterThanOrEqual(0);
      expect(view.y).toBeGreaterThanOrEqual(0);
      expect(view.x + view.width).toBeLessThanOrEqual(COURT_POSTER_SPACE.width);
      expect(view.y + view.height).toBeLessThanOrEqual(COURT_POSTER_SPACE.height);
    }
  });

  it('keeps its ball inside itself, whichever framing was chosen', () => {
    for (let at = 0; at < 400; at += 1) {
      const { view, ball } = courtPosterFor(`p-${at}`);

      expect(ball.x).toBeGreaterThan(view.x);
      expect(ball.x).toBeLessThan(view.x + view.width);
      expect(ball.y).toBeGreaterThan(view.y);
      expect(ball.y).toBeLessThan(view.y + view.height);
    }
  });
});

describe('what a poster never carries', () => {
  it('is a colour — every field it has is geometry', () => {
    // Every colour in the palette already means something, so a hue chosen by a hash would
    // be assigning meaning to a hash. There is nowhere for one to go, and this is what
    // keeps it that way.
    const poster = courtPosterFor(PLAYER);

    expect(Object.keys(poster).sort()).toEqual(['ball', 'view']);
    expect(Object.values(poster).flatMap((part) => Object.values(part))).toEqual(
      expect.arrayContaining([expect.any(Number)]),
    );
  });
});
