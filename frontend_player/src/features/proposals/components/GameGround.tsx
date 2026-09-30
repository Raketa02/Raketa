/**
 * **The game card's ground** — one gradient down its own box, from `gameGroundTop` to
 * `gameGroundFoot` (Part 16 2026-09-30), drawn behind whatever the box holds. The deck's card and a
 * game's details draw the same ground, so it is drawn once.
 *
 * `preserveAspectRatio="none"` makes a 1 × 1 drawing fill whatever height the box is, so the stops
 * are shares of the card; the gradient's id is per instance, as the poster's is, because three
 * cards are on the stage at once.
 */

import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { theme } from '@/shared/ui';

export function GameGround() {
  const ground = `${useId()}-ground`;
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <Svg width="100%" height="100%" viewBox="0 0 1 1" preserveAspectRatio="none">
        <Defs>
          <LinearGradient id={ground} x1="0" y1="0" x2="0" y2="1">
            <Stop offset={0} stopColor={theme.color.gameGroundTop} />
            <Stop offset={1} stopColor={theme.color.gameGroundFoot} />
          </LinearGradient>
        </Defs>
        <Rect x={0} y={0} width={1} height={1} fill={`url(#${ground})`} />
      </Svg>
    </View>
  );
}
