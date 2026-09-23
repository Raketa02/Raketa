/**
 * The passport's one rule about a ring: **the ceiling tick is drawn only while the rating is
 * still an Initial estimate**, and only where a ceiling was served.
 */

import { passportCeiling } from './passport';

describe('the ceiling tick on a passport card', () => {
  it('is drawn on an Initial estimate whose ceiling was served', () => {
    expect(passportCeiling({ status: 'initial_estimate', confidenceCeiling: 30 })).toBe(30);
  });

  it('is not drawn once real results have moved the rating', () => {
    // The ceiling is the questionnaire's; a rating matches have moved is no longer bound by it,
    // and a tick would say it was.
    expect(passportCeiling({ status: 'calibrating', confidenceCeiling: 30 })).toBeUndefined();
    expect(passportCeiling({ status: 'stable', confidenceCeiling: 30 })).toBeUndefined();
  });

  it('is never invented where no ceiling was served', () => {
    // `GET /ratings` serves none today, and a copy of the number is what 7.8's amendment
    // removed: the tick waits for the read to carry it.
    expect(passportCeiling({ status: 'initial_estimate' })).toBeUndefined();
    expect(
      passportCeiling({ status: 'initial_estimate', confidenceCeiling: undefined }),
    ).toBeUndefined();
  });
});
