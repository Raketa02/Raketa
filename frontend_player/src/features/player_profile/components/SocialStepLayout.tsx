/**
 * The chrome every step of onboarding's second part wears, and the one move it owns.
 *
 * What is here is what must not be decided twice: the eyebrow that says how far through the
 * part a player is, and **the back control, which is absent on the first step**. That
 * absence is `stepBefore` answering rather than a prop each screen remembers to leave off —
 * behind step one is a rated Assessment's review, and an answer is revisable for as long as
 * its run is and no longer.
 *
 * **Back `replace`s**, so the part is a flat sequence of six screens with no stack behind
 * it: back can only ever reach the previous step, never the result or the review, because
 * there is no history entry holding one.
 *
 * ## The device's back is this control, and that is a fix rather than a nicety
 *
 * This docblock used to say that leaving the part by the system's own back gesture *"restarts
 * it at step one, which is exactly what
 * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md) says leaving
 * mid-part does."* **It did not restart anything.** The flat sequence above is the reason: one
 * history entry, so the thing under it is whatever was on screen before the part began —
 * welcome, one push behind the sport picker. Android's back popped to exactly there, and the
 * only way back into the part from welcome is to rate another sport.
 *
 * ADR-0090 forbids that in the same breath it is quoted for: *"Back and forward move freely
 * inside each part and never cross between them."* The restart it describes is what a **new
 * launch** does, through the entry gate, and a gesture is not a launch.
 *
 * So the step claims the press and answers it with **its own back control** — the previous
 * step where there is one, and nothing at all on step one, where `stepBefore` has already said
 * there is nowhere behind. A press that does nothing is what the missing control says out
 * loud; a press that walks out is a second, louder answer to a question this screen has
 * already answered.
 *
 * Forward is **not** here. Every step continues on its own terms — one is blocked until a
 * floor is met, one may be passed with nothing answered at all — and a shared control that
 * took a `disabled` and a `label` would be the six steps' differences squeezed through one
 * prop list — and the last one does not continue at all: it finishes (`ProfileFinish`).
 *
 * ## The chrome gets out of the keyboard's way, because one step types
 *
 * The intro is the first step of the part with a box to type in, and the action bar is pinned
 * under the scroller: on iOS the keyboard would cover *Next*, *Skip*, the counter and the
 * refusal under the box for exactly as long as the player is typing. So the layout wraps the
 * scroller and the bar in `KeyboardAvoidingView`, with `KEYBOARD_AVOIDANCE` deciding the
 * platform — the same value the sign-in, sign-up and conversation screens use — and taps on
 * the bar land while the keyboard is up rather than first dismissing it. On the five steps
 * with no keyboard it does nothing.
 */

import { useRouter } from 'expo-router';
import type { ReactNode } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE, useHardwareBack } from '@/shared/lib/platform';
import { ScreenHeader, behindOverlay, theme } from '@/shared/ui';

import { stepBefore, type SocialStep } from '../domain/socialSteps';

import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy, stepEyebrow } from './socialStepPresentation';

export interface SocialStepLayoutProps {
  readonly step: SocialStep;
  /** Overrides the plain position line when a step's own rule belongs in the chrome. */
  readonly eyebrow?: string;
  /** The step itself: what it asks, and the controls it asks with. */
  readonly children: ReactNode;
  /** Pinned below the scroll: whatever this step continues with. */
  readonly action: ReactNode;
  /**
   * Whether an overlay is open over this step.
   *
   * A `Modal` presents in its own native window, which hides the tree behind it from *that*
   * window and nothing more — the screen underneath still has to say it is unreachable, and
   * the element that says so has to be the root, which is this one. An overlay rendered
   * inside the element carrying `behindOverlay` would hide itself along with everything else,
   * so a step with a sheet renders it as a **sibling** of this layout and sets this while it
   * is up.
   */
  readonly overlaid?: boolean;
}

export function SocialStepLayout({
  step,
  eyebrow,
  children,
  action,
  overlaid = false,
}: SocialStepLayoutProps) {
  const router = useRouter();
  const previous = stepBefore(step);
  const goBack =
    previous === undefined ? undefined : () => router.replace(SOCIAL_STEP_PATH[previous]);

  // One answer, drawn as a control and given to the device — never two, which is how the
  // header and the gesture start disagreeing about where behind is.
  useHardwareBack(() => goBack?.());

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']} {...behindOverlay(overlaid)}>
      <ScreenHeader
        eyebrow={eyebrow ?? stepEyebrow(step)}
        title={stepCopy(step).title}
        onBack={goBack}
        backLabel={previous === undefined ? undefined : `Back to ${stepCopy(previous).title}`}
      />

      <KeyboardAvoidingView style={s.body} behavior={KEYBOARD_AVOIDANCE}>
        <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
          {children}
        </ScrollView>

        <View style={s.action}>{action}</View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { flex: 1 },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
