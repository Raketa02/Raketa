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
 * there is no history entry holding one. Leaving the part by the system's own back gesture
 * restarts it at step one, which is exactly what
 * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md) says leaving
 * mid-part does.
 *
 * Forward is **not** here. Every step continues on its own terms — one is blocked until a
 * floor is met, one may be passed with nothing answered at all — and a shared control that
 * took a `disabled` and a `label` would be the six steps' differences squeezed through one
 * prop list.
 */

import { useRouter } from 'expo-router';
import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

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
}

export function SocialStepLayout({ step, eyebrow, children, action }: SocialStepLayoutProps) {
  const router = useRouter();
  const previous = stepBefore(step);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScreenHeader
        eyebrow={eyebrow ?? stepEyebrow(step)}
        title={stepCopy(step).title}
        onBack={
          previous === undefined ? undefined : () => router.replace(SOCIAL_STEP_PATH[previous])
        }
        backLabel={previous === undefined ? undefined : `Back to ${stepCopy(previous).title}`}
      />

      <ScrollView contentContainerStyle={s.content}>{children}</ScrollView>

      <View style={s.action}>{action}</View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
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
