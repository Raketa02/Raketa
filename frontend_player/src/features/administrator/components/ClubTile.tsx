/**
 * **A club's tile** — its two letters on `night`, at a group monogram's sizes (club 5–7: *O3*).
 *
 * The group monogram's drawing (7.20) with the one thing a club is not served: a colour key. A
 * group's hue is fixed for it by the backend; a club has none, so its tile takes `night`, the
 * system's colour for avatars and dark cards — which is also what club 5–8 draw — and never a hue
 * picked from the group palette, where it would pass for a group's. Hidden from assistive
 * technology: the club's name is always beside it, drawn and spoken.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { clubLetters } from './administratorPresentation';

export function ClubTile({
  clubName,
  size,
}: {
  readonly clubName: string;
  readonly size: 'card' | 'row';
}) {
  const side = theme.size.monogram[size];

  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[
        s.tile,
        {
          width: side,
          height: side,
          borderRadius: Math.round(side * theme.size.monogram.radius),
        },
      ]}
    >
      <Text
        style={[s.letters, { fontSize: Math.round(side * theme.size.monogram.letters) }]}
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        {clubLetters(clubName)}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  tile: { alignItems: 'center', justifyContent: 'center', backgroundColor: theme.color.night },
  letters: {
    fontFamily: theme.font.sans[700],
    color: theme.color.surface,
    includeFontPadding: false,
  },
});
