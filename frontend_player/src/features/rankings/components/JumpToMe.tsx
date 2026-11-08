/**
 * **The floating *You · 212th*** (the screens §5.3; the words §30.7;
 * [#776](https://github.com/Raketa02/Raketa/issues/776)) — at the foot, above the tab bar, over the
 * list: a `dark` button, the place card's own colour (Part 16, 2026-11-08).
 *
 * **It shows while the reader's row is off screen**, and waits for the list's first report rather than
 * flashing up before it: `seen` is `undefined` until the list has said. **A jump that is refused says
 * why where the button stood**, with *Try again*, until a jump lands.
 */

import { StyleSheet, View } from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { Button, theme } from '@/shared/ui';

import type { Jump } from '../hooks/useGeneral';

import { RANKINGS_COPY, jumpButtonLabel } from './rankingsCopy';

export function JumpToMe({
  jump,
  seen,
  onPress,
}: {
  readonly jump: Jump;
  /** Whether the reader's row is on screen — `undefined` until the list first says. */
  readonly seen: boolean | undefined;
  readonly onPress: () => void;
}) {
  if (jump.failure !== undefined) {
    return (
      <View style={s.foot}>
        <ReadFailure error={jump.failure.error} onRetry={jump.failure.retry} />
      </View>
    );
  }
  if (seen !== false) return null;
  return (
    <View style={[s.foot, s.centred]} pointerEvents="box-none">
      <Button
        label={jumpButtonLabel(jump.place)}
        accessibilityHint={RANKINGS_COPY.jumpHint}
        variant="dark"
        onPress={onPress}
      />
    </View>
  );
}

/** How much of the list's foot the button covers — the list keeps that much clear below its last row. */
export const JUMP_ROOM = theme.size.btn + 2 * theme.size.gutter;

const s = StyleSheet.create({
  foot: {
    position: 'absolute',
    left: theme.size.gutter,
    right: theme.size.gutter,
    bottom: theme.size.gutter,
  },
  centred: { alignItems: 'center' },
});
