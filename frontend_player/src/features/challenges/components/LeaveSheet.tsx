/**
 * **The departure's confirmation** — `WithdrawSheet`'s exact shape, a third time.
 *
 * The third irreversible act in this app that reaches other people, and it takes the shape the
 * first two already have: a real modal (9.1) with `accessibilityViewIsModal`, hidden siblings and
 * Android back; a title naming the **moment** rather than the act, so the act is named once by the
 * control that carries it out; a dismissal **named by what it does**; and **focus landing on the
 * title rather than on the first action**, because that action is the destructive one and landing
 * focus there would make the worst outcome the cheapest to trigger (§20.6).
 *
 * All five of those are `BottomSheet`'s already, which is the whole reason this file is short:
 * what a third sheet on that shape owes is its four sentences and the name of its act — and they
 * are `leaveGamePresentation.ts`', where the difference from the withdraw's is argued.
 *
 * ## What it does not draw
 *
 * **No refusal, and no pending state**, on `WithdrawSheet`'s own line: confirming here dismisses
 * the sheet, and everything the departure then does happens on the control that opened it —
 * pending on that control, and a refusal beside it, where the player can act on it. A sheet that
 * stayed up holding a failure would be a modal over the sentence that explains it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import {
  LEAVE_SHEET_BODY,
  LEAVE_SHEET_CLOSE_LABEL,
  LEAVE_SHEET_TITLE,
  LEAVE_THE_GAME,
} from './leaveGamePresentation';

export interface LeaveSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Confirming. The caller dismisses the sheet and runs the departure — see the module note. */
  readonly onLeave: () => void;
  /**
   * The control the sheet was opened from. Focus returns there on close.
   *
   * **Required, where `BottomSheet`'s own is optional**, for `WithdrawSheet`'s reason: the screen
   * behind this one is hidden while it is up, so a caller that forgot would strand a listener in
   * front of an act they have just declined to take.
   */
  readonly returnFocusTo: FocusTarget;
}

export function LeaveSheet({ visible, onClose, onLeave, returnFocusTo }: LeaveSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={LEAVE_SHEET_TITLE}
      closeLabel={LEAVE_SHEET_CLOSE_LABEL}
      returnFocusTo={returnFocusTo}
    >
      <View style={s.block}>
        {LEAVE_SHEET_BODY.map((line) => (
          <Text key={line} style={s.body}>
            {line}
          </Text>
        ))}
      </View>

      <View style={s.action}>
        <Button label={LEAVE_THE_GAME} size="lg" onPress={onLeave} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  action: { paddingTop: theme.space.md },
});
