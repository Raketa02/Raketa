/**
 * The information mark — a serif italic *i*, white on a 14pt circle.
 *
 * **A serif mark inside a sans-serif app, because the information mark is a symbol rather
 * than text and the serif form is the one people recognise** (design-system 5.4). It is
 * the only non-app family in the system.
 *
 * It appears in two places that look like one object and are: the info note's glyph (5.4)
 * and the mark that opens an anchored popover (7.6). One implementation — correction #8
 * is about exactly this, three components the prototype kept second copies of.
 *
 * **Decorative, always.** Whatever it sits in carries the name: the note's sentence says
 * the same thing, and the popover's mark is a button with its own label. A screen reader
 * announcing "i" before every explanation is noise.
 *
 * `onDark` is 5.2's repaint. React Native has no colour cascade, so a dark card's children
 * take the `onDark*` tokens rather than inheriting anything — the `info` circle is `night2`
 * and would disappear into a `night` card.
 */

import { Platform, StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

export interface InfoGlyphProps {
  readonly onDark?: boolean;
}

export function InfoGlyph({ onDark = false }: InfoGlyphProps) {
  return (
    <View
      style={[s.glyph, onDark ? s.onDark : undefined]}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      <Text style={s.mark}>i</Text>
    </View>
  );
}

const s = StyleSheet.create({
  glyph: {
    width: theme.size.infoGlyph,
    height: theme.size.infoGlyph,
    borderRadius: theme.size.infoGlyph / 2,
    backgroundColor: theme.color.info,
    alignItems: 'center',
    justifyContent: 'center',
  },
  onDark: { backgroundColor: theme.color.onDarkFill },
  mark: {
    ...theme.type.tag,
    fontFamily: Platform.select({
      ios: theme.font.serif.ios,
      default: theme.font.serif.android,
    }),
    fontStyle: 'italic',
    color: theme.color.surface,
  },
});
