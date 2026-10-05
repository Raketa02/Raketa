/**
 * **Show at the desk** — the reader's check-in code on the game's day: a QR code, and the short
 * code under it to read out when the camera will not ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A4.1; the mechanics §15.1).
 *
 * On paper, as the forecast is: a desk's camera reads dark modules on white, and the card is the
 * quiet zone around them. The QR is one element, spoken as what it is; the short code is spoken a
 * character at a time, because *K7M2QX* read as a word is not what the club types.
 */

import { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

import { Card, theme } from '@/shared/ui';

import type { CheckIn } from '../domain/home';

import { HOME_GAME_COPY } from './homeCopy';
import { shortCodeSpoken } from './homePresentation';
import { qrDrawing } from './qrPath';

const COPY = HOME_GAME_COPY.details;

/** The quiet zone a reader needs around the modules, in modules — the standard's four. */
const QUIET = 4;

export function CheckInCard({ checkIn }: { readonly checkIn: CheckIn }) {
  const drawing = useMemo(() => qrDrawing(checkIn.qrPayload), [checkIn.qrPayload]);
  const side = drawing.size + 2 * QUIET;

  return (
    <Card style={s.card}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {COPY.showAtTheDesk}
      </Text>
      <View style={s.code} accessible accessibilityRole="image" accessibilityLabel={COPY.qrSpoken}>
        <Svg
          width={theme.size.checkIn.code}
          height={theme.size.checkIn.code}
          viewBox={`${-QUIET} ${-QUIET} ${side} ${side}`}
          testID="check-in-qr"
        >
          <Rect x={-QUIET} y={-QUIET} width={side} height={side} fill={theme.color.surface} />
          <Path d={drawing.path} fill={theme.color.ink} />
        </Svg>
      </View>
      <Text style={s.short} accessibilityLabel={shortCodeSpoken(checkIn.shortCode)}>
        {checkIn.shortCode}
      </Text>
      <Text style={s.line}>{COPY.deskLine}</Text>
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm, alignItems: 'center' },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    alignSelf: 'flex-start',
  },
  code: { padding: theme.space.xs },
  short: { ...theme.num.xl, ...theme.tabular, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
