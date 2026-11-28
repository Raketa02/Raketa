/**
 * **A rescue that went while the player reached for it** — the blocking sheet a refused swipe yes
 * opens, in place of a toast that goes in 2.6 seconds ([#545](https://github.com/Rakieta02/Rakieta/issues/545);
 * the bug report's P1 on the rescue swipe). It names the reason the join gave — the seat taken, the
 * game called off at its cut-off or cancelled by its club (with the club's reason), the game
 * started, the seat no longer offered — says nothing was charged, and stays until the player closes
 * it: the one thing a player who tried to pay must read.
 */

import { StyleSheet, Text } from 'react-native';

import { BottomSheet, Button, theme } from '@/shared/ui';

import type { RescueGone } from '../domain/deck';

import { rescueGoneLine } from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY.rescueGone;

export interface RescueGoneSheetProps {
  /** Why the seat is gone, or `undefined` while there is nothing to say. */
  readonly gone: RescueGone | undefined;
  readonly onClose: () => void;
}

export function RescueGoneSheet({ gone, onClose }: RescueGoneSheetProps) {
  return (
    <BottomSheet
      visible={gone !== undefined}
      onClose={onClose}
      title={COPY.title}
      closeLabel={COPY.close}
    >
      {gone === undefined ? null : (
        <>
          <Text style={s.line}>{rescueGoneLine(gone)}</Text>
          <Button label={COPY.close} onPress={onClose} />
        </>
      )}
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  line: { ...theme.type.rlLabel, color: theme.color.muted },
});
