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
  /**
   * The h1 — **optional since [#414](https://github.com/Raketa02/Raketa/issues/414)**, whose
   * plan lead is the first screen the design draws with an eyebrow and no title. Forwarded, not
   * designed: `ScreenHeader` makes the eyebrow the heading where there is none.
   */
  readonly title?: string;
  readonly eyebrow?: string;
  /** Pinned below the scroller and above the tab bar. Absent when there is nothing to press. */
  readonly action?: ReactNode;
  /**
   * The way back, for a screen that has one — **forwarded, not designed.**
   *
   * The module note below has said since this component was written that *"the day a Play
   * screen has a way back of its own it is a prop forwarded, not a control designed"*, and the
   * first screen to have one is not a Play screen: a game pushed over the Now tab is genuinely
   * pushed, so what is behind it is a place the player came from rather than whatever the
   * router happened to be holding. Absent everywhere else, which is what keeps 10.3's chevron
   * opt-in.
   */
  readonly onBack?: () => void;
  readonly children: ReactNode;
}

/**
 * The back control is **opt-in and forwarded**, never drawn by default: every tab root is a
 * screen a tab press arrives at, and 10.3 makes the chevron opt-in precisely so a screen with
 * nothing behind it does not draw one. `ScreenHeader` already took `onBack`, so the first screen
 * with a way back of its own — a game pushed over the Now tab — is a prop passed through rather
 * than a control designed.
 */
export function ShellScreen({ title, eyebrow, action, onBack, children }: ShellScreenProps) {
  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader title={title} eyebrow={eyebrow} onBack={onBack} />

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
