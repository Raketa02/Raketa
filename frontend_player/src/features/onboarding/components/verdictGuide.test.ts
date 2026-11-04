/**
 * **The guide's steps over the verdict** — what each one cuts out, where its arrow points, and
 * which stands beside its mark. Where the bubbles land on a phone is `Guide.test`'s and
 * `guideGeometry.test`'s; the walk is `theGuideOnYourRating.test`.
 */

import type { MutableRefObject } from 'react';
import type { View } from 'react-native';

import { verdictGuide, type VerdictSpotlights } from './Verdict';

const ref = (): MutableRefObject<View | null> => ({ current: null });

const spotlit: VerdictSpotlights = {
  level: { figure: ref(), mark: ref() },
  range: { figure: ref(), mark: ref() },
  confidence: { figure: ref(), mark: ref() },
};

describe('the guide’s steps over the verdict', () => {
  it('walks the level, the range and the ring, each cut out with its mark as the arrow’s', () => {
    const steps = verdictGuide(spotlit, 30);

    expect(steps.map((step) => step.title)).toEqual([
      'Your Level',
      'Your likely range',
      'Confidence',
    ]);
    expect(steps[0]?.target).toBe(spotlit.level.figure);
    expect(steps[0]?.pointAt).toBe(spotlit.level.mark);
    expect(steps[2]?.pointAt).toBe(spotlit.confidence.mark);
  });

  it('stands only the level’s bubble beside its mark — the ⓘ on top of a large number', () => {
    expect(verdictGuide(spotlit, 30).map((step) => step.besideMark)).toEqual([true, false, false]);
  });
});
