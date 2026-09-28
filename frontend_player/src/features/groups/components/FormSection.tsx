/**
 * **One of New group's three sections** — its label over its control, on the page (the 2026-09-27
 * mocks, which took the form out of its cards).
 *
 * The label is drawn here rather than by the field, so all three sit the same distance from what
 * they name — a field's own label sits closer to its box than a chip row's could. The control
 * still carries its own name for a listener; this is the drawing.
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export function FormSection({
  label,
  children,
}: {
  readonly label: string;
  readonly children: ReactNode;
}) {
  return (
    <View style={s.section}>
      <Text style={s.label}>{label}</Text>
      {children}
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.sm },
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
});
