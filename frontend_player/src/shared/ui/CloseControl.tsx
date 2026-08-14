/**
 * The close mark — a 28pt circle on `line2`, per design-system 9.1.
 *
 * 9.1 specifies it as part of the bottom sheet, but the moment a sheet opens there are
 * two of them on screen: the control in the header that opened it, and the sheet's own.
 * They are the same object, so there is one implementation — the prototype kept second
 * copies of three components and recorded that they had drifted (correction #8).
 *
 * **The label is required and is never just "Close".** A screen reader announces the
 * name on its own, out of any visual context, so "Close" says nothing about what is
 * about to close.
 *
 * The visual is 28; the reachable area is larger than the 44pt minimum via `hitSlop`
 * (design-system 6.5). The pressed appearance is declared, because there is no hover.
 */

import { forwardRef } from 'react';
import { Pressable, StyleSheet, Text, type View } from 'react-native';

import { theme } from './theme';

export interface CloseControlProps {
  readonly onPress: () => void;
  /** What closes — "Leave this rating", not "Close". */
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
}

/**
 * The ref is forwarded because this is the control a sheet returns focus to when it
 * closes — see `BottomSheet`. Nothing else needs it.
 */
export const CloseControl = forwardRef<View, CloseControlProps>(function CloseControl(
  { onPress, accessibilityLabel, accessibilityHint },
  ref,
) {
  return (
    <Pressable
      ref={ref}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      hitSlop={theme.hit.infoMark}
      style={({ pressed }) => [s.control, pressed ? s.pressed : undefined]}
    >
      {/* A multiplication sign, not a lowercase x — the x has a baseline and sits low
          in the circle. Hidden from assistive tech: the control carries the name. */}
      <Text style={s.mark} accessibilityElementsHidden importantForAccessibility="no">
        {'×'}
      </Text>
    </Pressable>
  );
});

const s = StyleSheet.create({
  control: {
    width: theme.size.sheetClose,
    height: theme.size.sheetClose,
    borderRadius: theme.size.sheetClose / 2,
    backgroundColor: theme.color.line2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { backgroundColor: theme.color.line },
  mark: { ...theme.type.h2, color: theme.color.muted },
});
