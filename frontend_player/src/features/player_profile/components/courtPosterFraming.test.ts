/**
 * The poster's one contract: the same player id produces the same drawing, on this phone,
 * on their next one, and after a reinstall.
 */

import { COURT_POSTER_POSES, POSTER_HUES } from '@/shared/ui';

import { COURT_POSTER_COUNT, courtPosterFor } from './courtPosterFraming';

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

  it('varies its hue and its pose independently', () => {
    const posters = Array.from({ length: 400 }, (_unused, at) => courtPosterFor(`p-${at}`));

    const hues = new Set(posters.map((poster) => poster.hue.light));
    const pairs = new Set(posters.map((poster) => `${poster.hue.light} ${poster.pose}`));

    // Tied together, one hue would take exactly one pose and there would be as many pairs
    // as hues — which is the forty-eight collapsing to sixteen this file exists to prevent.
    expect(hues.size).toBe(POSTER_HUES.length);
    expect(pairs.size).toBeGreaterThan(hues.size);
  });

  it('draws every hue and every pose the design system published', () => {
    const posters = Array.from({ length: 400 }, (_unused, at) => courtPosterFor(`q-${at}`));

    expect(new Set(posters.map((poster) => poster.hue))).toEqual(new Set(POSTER_HUES));
    expect(new Set(posters.map((poster) => poster.pose))).toEqual(new Set(COURT_POSTER_POSES));
  });
});

describe('how many distinct posters there are', () => {
  it('is sixteen hues by three poses, and never fewer than the forty-eight it was', () => {
    expect(COURT_POSTER_COUNT).toBe(POSTER_HUES.length * COURT_POSTER_POSES.length);
    // The eight framings by six ball positions are gone; the count they justified is not a
    // number to quietly lower, so it is held here rather than recomputed and forgotten.
    expect(COURT_POSTER_COUNT).toBeGreaterThanOrEqual(48);
  });
});

describe('what a poster never carries', () => {
  it('is a fact — a hue and a pose are the whole of it, and neither says anything', () => {
    // A player whose pose is `serve` is not a server, and the handedness a pose appears to
    // show is not theirs. A poster is shown and never read: nothing may take an input from
    // it, and the smallest guarantee of that is that there is nothing in it to take.
    const poster = courtPosterFor(PLAYER);

    expect(Object.keys(poster).sort()).toEqual(['hue', 'pose']);
  });
});
