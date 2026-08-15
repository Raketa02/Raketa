/**
 * Onboarding's chrome: a header, and whatever the screen puts under it.
 *
 * **The bar that measured sports is gone, and the eyebrow is the sole carrier of which
 * sport of how many.** The two said the same thing, and the words are the half that is
 * readable at any font size — a filled rectangle is not. What replaces the bar on the
 * questionnaire is the question navigator, which measures the run rather than the pass:
 * the screen a player spends the longest on is the one that used to show no movement at
 * all, because a bar counting sports does not move for eight questions
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md),
 * design-system 12.1).
 *
 * So the strip under the header is a slot rather than a component. Screens with nothing to
 * measure — welcome, the picker, the result, the closing screens — pass nothing and draw a
 * header, which is what they always drew once the sports bar stopped being honest.
 *
 * The header's two slots are not the same thing and never were: the right slot is a way
 * *out* of the flow (the close control), and the left is the way *back* through it, which
 * the questionnaire now has.
 */

import { StyleSheet, View } from 'react-native';
import type { ReactNode } from 'react';

import { ScreenHeader, theme } from '@/shared/ui';

export interface OnboardingChromeProps {
  readonly title: string;
  readonly eyebrow?: string;
  /** The header's right slot — the close control, on the screens that can be left. */
  readonly right?: ReactNode;
  /** The header's left slot: back through the questionnaire, never out of it. */
  readonly onBack?: () => void;
  readonly backLabel?: string;
  /** The strip under the header. The questionnaire puts its navigator here. */
  readonly progress?: ReactNode;
}

export function OnboardingChrome({
  title,
  eyebrow,
  right,
  onBack,
  backLabel,
  progress,
}: OnboardingChromeProps) {
  return (
    <View>
      <ScreenHeader
        title={title}
        eyebrow={eyebrow}
        right={right}
        onBack={onBack}
        backLabel={backLabel}
      />
      {progress !== undefined ? <View style={s.progress}>{progress}</View> : null}
    </View>
  );
}

const s = StyleSheet.create({
  progress: { paddingHorizontal: theme.size.gutter, paddingBottom: theme.space.md },
});
