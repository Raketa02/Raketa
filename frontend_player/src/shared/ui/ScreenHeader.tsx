/**
 * The screen header, per design-system 10.3 — eyebrow above, h1 below, an optional back
 * control and an optional right slot.
 *
 * **The back control is opt-in and stays that way.** Most screens are somewhere a player
 * arrived at rather than walked into, and a header that drew a chevron by default would
 * put that control on screen by omission — pointing at whatever the router happened to
 * have behind it. A screen that has a way back says so.
 *
 * The questionnaire is now one of them: a player may walk back over the questions they
 * have answered ([ADR-0020](../../../../docs/adr/0020-revisable-assessment-answers.md),
 * which supersedes ADR-0017's irreversibility rule), and this is the control they do it
 * with — 20pt, `muted`, on a 44 × 44 target, per design-system 10.3.
 *
 * The eyebrow labels a region you are READING. It is not `flab`, which labels a control
 * you are about to OPERATE — the two are not interchangeable (design-system 3.3).
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export interface ScreenHeaderProps {
  readonly title: string;
  readonly eyebrow?: string;
  /** A segmented control, a close control — whatever the screen pins to the right. */
  readonly right?: ReactNode;
  readonly onBack?: () => void;
  readonly backLabel?: string;
}

export function ScreenHeader({
  title,
  eyebrow,
  right,
  onBack,
  backLabel = 'Back',
}: ScreenHeaderProps) {
  return (
    <View style={s.header}>
      {onBack !== undefined ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={backLabel}
          onPress={onBack}
          // The visual chevron is 20pt; the reachable area is 44 x 44.
          hitSlop={theme.hit.infoMark}
          style={({ pressed }) => [s.back, pressed ? s.backPressed : undefined]}
        >
          <Text style={s.backMark}>{'‹'}</Text>
        </Pressable>
      ) : null}

      <View style={s.titles}>
        {eyebrow !== undefined ? <Text style={s.eyebrow}>{eyebrow}</Text> : null}
        <Text style={s.title} accessibilityRole="header">
          {title}
        </Text>
      </View>

      {right !== undefined ? <View style={s.right}>{right}</View> : null}
    </View>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.md,
  },
  titles: { flex: 1, gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  back: { alignItems: 'center', justifyContent: 'center' },
  backPressed: { opacity: 0.7 },
  backMark: { ...theme.type.h1, color: theme.color.muted },
  right: { alignItems: 'flex-end' },
});
