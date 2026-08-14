/**
 * The screen header, per design-system 10.3 — eyebrow above, h1 below, an optional back
 * control and an optional right slot.
 *
 * **The back control is opt-in and stays that way.** The questionnaire has no back
 * navigation at all — an answer's numeric meaning depends on the difficulty tier it was
 * asked at, so revising an earlier answer would silently change what every later answer
 * meant (ADR-0017). A header that drew a chevron by default would put that control on
 * screen by omission.
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
