/**
 * The level row — the level, the band's published name and the likely range, in that order —
 * which a booked game's players card cites under each handle (#574).
 */

import { levelRow } from './levelRow';

describe('the level row', () => {
  it('states the level, the band and the likely range, in that order', () => {
    expect(levelRow({ level: 2.71, band: 'Established', range: { low: 2.55, high: 2.87 } })).toBe(
      '2,71 · Established · likely 2,55 – 2,87',
    );
  });

  it('never calls the range a band', () => {
    // The bands are New · Developing · Established · Advanced; `2,55–2,87` is μ ± σ.
    const row = levelRow({ level: 2.71, band: 'Established', range: { low: 2.55, high: 2.87 } });

    expect(row).not.toMatch(/band/i);
    expect(row).toMatch(/likely/);
  });

  it('draws the band’s published name and never its edges', () => {
    expect(levelRow({ level: 4.02, band: 'Advanced', range: { low: 3.8, high: 4.24 } })).toBe(
      '4,02 · Advanced · likely 3,80 – 4,24',
    );
  });
});
