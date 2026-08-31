/**
 * The arrangement every screen inside the five-tab shell wears, per design-system 10.1.
 *
 * ```
 * SafeAreaView
 *   ScreenHeader        pinned — it does not scroll away
 *   ScrollView          the page
 *   CTA                 conditional, and above the bar rather than in it
 * ```
 *
 * **The header pins.** The UI specification proposed the opposite and lost twice over
 * ([#227](https://github.com/Raketa02/Raketa/issues/227)): its argument is a viewport budget
 * computed against a 392 x 788 phone with *no safe areas at all*, so the number gets worse on
 * a real device rather than better — and this app has one header behaviour, already built
 * this way by `SocialStepLayout` and `OnboardingChrome`. Play's screens are the longest in
 * the product, and a title that scrolls off a ranked list is the case a pinned header earns
 * its 48pt on.
 *
 * **The CTA and the tab bar are flex siblings, never fixed elements** — and the bar is not
 * here. It is mounted once by `TabShell`, below the navigator, because a bar rendered per
 * screen is a bar that slides with the screen. What that leaves this component is the one
 * consequence 10.1 states: **the bottom inset is the bar's**, so the safe area taken here is
 * the top edge alone. Applied at both ends it is 34pt of nothing; applied at the wrong end
 * it is a CTA under the home indicator.
 *
 * The CTA is *conditional* rather than always drawn: a screen with nothing to press has
 * nothing pinned, and the court screen populating it on one of three branches
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)) is that same conditional read once
 * per branch.
 */

import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenHeader, theme } from '@/shared/ui';

export interface ShellScreenProps {
  readonly title: string;
  readonly eyebrow?: string;
  /** Pinned below the scroller and above the tab bar. Absent when there is nothing to press. */
  readonly action?: ReactNode;
  readonly children: ReactNode;
}

/**
 * No back control here, and none passed through: every screen the shell holds today is one a
 * tab press arrives at, and 10.3 makes the chevron opt-in precisely so a screen with nothing
 * behind it does not draw one. `ScreenHeader` already takes `onBack`, so the day a Play screen
 * has a way back of its own it is a prop forwarded, not a control designed.
 */
export function ShellScreen({ title, eyebrow, action, children }: ShellScreenProps) {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={title} eyebrow={eyebrow} />

      <ScrollView contentContainerStyle={s.content}>{children}</ScrollView>

      {action !== undefined ? <View style={s.action}>{action}</View> : null}
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
    paddingBottom: theme.space.md,
    gap: theme.space.sm,
  },
});
