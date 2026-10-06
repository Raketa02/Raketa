/**
 * **The mark's confirmation** — *Before you say so* ([#560](https://github.com/Raketa02/Raketa/issues/560);
 * the Games & Fill in mechanics §15.3), on the leave sheet's shape (`proposals`' `LeaveSheet`): a
 * real modal over `BottomSheet`, a title naming **the moment** so the act is named once — by the
 * control that carries it out — a dismissal named by what it does, and focus landing on the title
 * rather than on the act.
 *
 * **It draws no refusal and no pending state**, the game screen's line: confirming dismisses it, and
 * the mark then happens on the row that opened it — busy there, a refusal said in the pinned footer
 * beside the screen's other acts. A sheet that stayed up holding a failure would be a modal over the
 * sentence that explains it.
 */

import { StyleSheet, Text, View } from 'react-native';

import type { NamedPlayer } from '@/shared/formatting/playerName';
import { BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import {
  NO_SHOW_SHEET_CLOSE_LABEL,
  NO_SHOW_SHEET_TITLE,
  didNotComeLabel,
  noShowSheetBody,
} from './gamePresentation';

export interface NoShowSheetProps {
  /** Who would be marked — `undefined` while the sheet is down. */
  readonly who: NamedPlayer | undefined;
  readonly onClose: () => void;
  /** Confirming. The caller makes the mark and puts the sheet away. */
  readonly onMark: () => void;
  /** The block the sheet was opened from. Focus returns there on close. */
  readonly returnFocusTo: FocusTarget;
}

export function NoShowSheet({ who, onClose, onMark, returnFocusTo }: NoShowSheetProps) {
  return (
    <BottomSheet
      visible={who !== undefined}
      onClose={onClose}
      title={NO_SHOW_SHEET_TITLE}
      closeLabel={NO_SHOW_SHEET_CLOSE_LABEL}
      returnFocusTo={returnFocusTo}
    >
      {who === undefined ? null : (
        <>
          <View style={s.block}>
            {noShowSheetBody(who).map((line) => (
              <Text key={line} style={s.body}>
                {line}
              </Text>
            ))}
          </View>
          <View style={s.action}>
            <Button label={didNotComeLabel(who)} size="lg" onPress={onMark} />
          </View>
        </>
      )}
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  action: { paddingTop: theme.space.md },
});
