/**
 * THROWAWAY PROTOTYPE — issue #11. Not production.
 *
 * Draws the 44 × 44pt reachable area around a control so question 3 is answered by
 * looking rather than by arithmetic. It is centred on the child and drawn behind it, so
 * where two controls' boxes OVERLAP the hitSlop is a lie — that overlap is the finding.
 */

import type { ReactNode } from 'react';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

export function TouchBox({
  children,
  show,
  style,
}: {
  readonly children: ReactNode;
  readonly show: boolean;
  readonly style?: StyleProp<ViewStyle>;
}) {
  return (
    <View style={[s.wrap, style]}>
      {show ? <View pointerEvents="none" style={s.box} /> : null}
      {children}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { justifyContent: 'center' },
  box: {
    position: 'absolute',
    alignSelf: 'center',
    minWidth: 44,
    left: -2,
    right: -2,
    height: 44,
    borderWidth: 1,
    borderColor: '#D9F24B',
    borderStyle: 'dashed',
    borderRadius: 4,
  },
});
