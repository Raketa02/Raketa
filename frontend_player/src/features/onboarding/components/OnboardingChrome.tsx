/**
 * Onboarding's chrome: a header, and a progress bar that measures **sports**.
 *
 * Sports are the one denominator the player actually chose. Question count is unknowable
 * by design — the engine stops when one more answer would no longer move the Band — so
 * there is no honest per-question denominator, and a bar that invented one would be
 * lying about a flow whose whole premise is that it explains itself.
 *
 * The bar therefore says *which sport you are on*, not how far through it you are, and
 * the eyebrow says the same thing in words: a filled rectangle is not readable at any
 * font size, and colour is never the only carrier of a state.
 *
 * There is no back control, here or anywhere else in the questionnaire (ADR-0017). The
 * right slot is a different thing entirely: a way *out* of the flow is not a way back to
 * an answer, and the question screen puts its close control there.
 */

import { StyleSheet, View } from 'react-native';
import type { ReactNode } from 'react';

import { Bar, ScreenHeader, theme } from '@/shared/ui';

import type { RatingPosition } from '../domain/onboardingPass';

export interface OnboardingChromeProps {
  readonly title: string;
  readonly eyebrow?: string;
  /** Absent before a pass exists — welcome and the picker have nothing to measure. */
  readonly position?: RatingPosition;
  /** The header's right slot. Never a back control — see above. */
  readonly right?: ReactNode;
}

export function OnboardingChrome({ title, eyebrow, position, right }: OnboardingChromeProps) {
  return (
    <View>
      <ScreenHeader title={title} eyebrow={eyebrow} right={right} />
      {position !== undefined ? (
        <View style={s.progress}>
          <Bar
            now={position.index}
            total={position.total}
            fill={theme.color.coral}
            accessibilityLabel={`Rating ${position.index} of ${position.total}`}
          />
        </View>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  progress: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.md },
});
