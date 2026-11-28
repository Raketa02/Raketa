/**
 * **The departure's confirmation** — `WithdrawSheet`'s exact shape, a third time, and since
 * [#427](https://github.com/Rakieta02/Rakieta/issues/427) the one sheet the act has, wherever it is
 * met.
 *
 * The third irreversible act in this app that reaches other people, and it takes the shape the
 * first two already have: a real modal (9.1) with `accessibilityViewIsModal`, hidden siblings and
 * Android back; a title naming the **moment** rather than the act, so the act is named once by the
 * control that carries it out; a dismissal **named by what it does**; and **focus landing on the
 * title rather than on the first action**, because that action is the destructive one and landing
 * focus there would make the worst outcome the cheapest to trigger (§20.6).
 *
 * All five of those are `BottomSheet`'s already, which is the whole reason this file is short:
 * what a third sheet on that shape owes is its sentences and the name of its act — and they are
 * `leaveSheetCopy.ts`' beside it, moved here from the challenge's departure deck with the sheet
 * ([#574](https://github.com/Rakieta02/Rakieta/issues/574)), where the difference from the
 * withdraw's is argued.
 *
 * ## Two surfaces, one sheet, and what the second one needed
 *
 * On the **game screen** the sheet draws no refusal and no pending state, on `WithdrawSheet`'s own
 * line: confirming dismisses it, and everything the departure then does happens on the control
 * that opened it — pending on that control, a refusal beside it, where the player can act on it. A
 * sheet that stayed up holding a failure would be a modal over the sentence that explains it.
 *
 * From the **Chats list** there is no such control: the button a swipe reveals closes with the
 * row the moment it is pressed, and a list row has no sentence to explain a refusal with. So there
 * the sheet **is** the surface — it stays up while the act is in flight, its act goes busy, and a
 * refusal is said on it in words (`leaveRefusalMessage`) with the act still there to press again.
 * The three props that carry that are optional and absent on the game screen, so that surface's
 * sheet is unchanged; `body` is the fourth, because the two surfaces say different things about
 * the same act and the deck argues why.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { BottomSheet, Button, Note, theme, type FocusTarget } from '@/shared/ui';

import {
  LEAVE_SHEET_BODY,
  LEAVE_SHEET_CLOSE_LABEL,
  LEAVE_SHEET_TITLE,
  LEAVE_THE_GAME,
  LEAVING,
} from './leaveSheetCopy';

export interface LeaveSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Confirming. The caller runs the departure — and, on the game screen, dismisses the sheet. */
  readonly onLeave: () => void;
  /**
   * The control the sheet was opened from. Focus returns there on close.
   *
   * **Required, where `BottomSheet`'s own is optional**, for `WithdrawSheet`'s reason: the screen
   * behind this one is hidden while it is up, so a caller that forgot would strand a listener in
   * front of an act they have just declined to take.
   */
  readonly returnFocusTo: FocusTarget;
  /** What the sheet says. The game screen's three lines unless the surface says otherwise. */
  readonly body?: readonly string[];
  /** The act is in flight — the list's sheet stays up and says so on its act. */
  readonly busy?: boolean;
  /** The act was refused — the list's sheet says why, in words, with the act still there. */
  readonly refusal?: string;
  /** No connection — the act greys under one amber note, as every act in this feature does. */
  readonly offline?: boolean;
}

export function LeaveSheet({
  visible,
  onClose,
  onLeave,
  returnFocusTo,
  body = LEAVE_SHEET_BODY,
  busy = false,
  refusal,
  offline = false,
}: LeaveSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={LEAVE_SHEET_TITLE}
      closeLabel={LEAVE_SHEET_CLOSE_LABEL}
      returnFocusTo={returnFocusTo}
    >
      <View style={s.block}>
        {body.map((line) => (
          <Text key={line} style={s.body}>
            {line}
          </Text>
        ))}
      </View>

      {/* The sentence a refused act writes — on this sheet only where the surface has nowhere
          else to write it. `alert`, because it appeared without being asked for. */}
      {refusal === undefined ? null : (
        <View style={s.note}>
          <Note variant="coral" accessibilityRole="alert">
            {refusal}
          </Note>
        </View>
      )}

      {offline ? (
        <View style={s.note}>
          <Note variant="amber">{offlineMessage('does-not-resume')}</Note>
        </View>
      ) : null}

      <View style={s.action}>
        <Button
          label={LEAVE_THE_GAME}
          size="lg"
          busy={busy}
          busyLabel={LEAVING}
          disabled={offline}
          onPress={onLeave}
        />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  note: { paddingTop: theme.space.sm },
  action: { paddingTop: theme.space.md },
});
