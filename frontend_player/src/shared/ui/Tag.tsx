/**
 * The tag, per design-system 6.4 — the status pill.
 *
 * **A tag is never pressable.** A pressable pill is a chip, and the two look close enough
 * that the only thing keeping them apart is this rule: a control that cannot be operated
 * must not offer the affordance of one.
 *
 * A long tag truncates rather than breaking the row it sits in, because a row that reflows
 * because of a status is a row whose layout depends on server copy.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

export type TagVariant = 'base' | 'ok' | 'hot' | 'warn' | 'bad' | 'onDark';

export interface TagProps {
  readonly label: string;
  readonly variant?: TagVariant;
  /**
   * A 6pt square in a sport's identity colour. The dot is decoration — the label beside
   * it always says the same thing, so colour is never the only carrier.
   */
  readonly dot?: string;
  /** Defaults to `label`. Set it when the word alone is cryptic out of context. */
  readonly accessibilityLabel?: string;
}

export function Tag({ label, variant = 'base', dot, accessibilityLabel }: TagProps) {
  return (
    <View style={[s.tag, SURFACE[variant]]}>
      {dot !== undefined ? (
        <View
          style={[s.dot, { backgroundColor: dot }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      ) : null}
      <Text
        style={[s.label, LABEL[variant]]}
        numberOfLines={1}
        accessibilityLabel={accessibilityLabel}
      >
        {label}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    paddingVertical: theme.space.xxs,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.tag,
    // `alignSelf`, so a tag in a row is its own width rather than the row's.
    alignSelf: 'flex-start',
  },
  // Square, not round: the round form is the sport dot, and the two mean different things.
  dot: { width: theme.size.sportDot, height: theme.size.sportDot },
  label: { ...theme.type.tag },
});

const SURFACE = StyleSheet.create({
  base: { backgroundColor: theme.color.line2 },
  ok: { backgroundColor: theme.color.mintSoft },
  hot: { backgroundColor: theme.color.coralSoft },
  warn: { backgroundColor: theme.color.amberSoft },
  bad: { backgroundColor: theme.color.redSoft },
  onDark: { backgroundColor: theme.color.onDarkTag },
});

const LABEL = StyleSheet.create({
  base: { color: theme.color.muted },
  ok: { color: theme.color.mintInk },
  hot: { color: theme.color.coralInk },
  warn: { color: theme.color.amber },
  bad: { color: theme.color.red },
  onDark: { color: theme.color.surface },
});
