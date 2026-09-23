/**
 * **The withdrawal's confirmation** — `SH.propose`'s exact shape, a second time, and since
 * [#428](https://github.com/Raketa02/Raketa/issues/428) one sheet for the two acts the route
 * carries: *Remove the challenge* while nobody has joined, and *Call it off* on a court that has
 * been a game
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4, §5).
 *
 * The second irreversible act in this app that reaches other people, and it takes the shape the
 * first one already has ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §2.6): a real modal (9.1) with `accessibilityViewIsModal`, hidden siblings and Android back; a
 * title naming the **moment** rather than the act, so the act is named once by the control that
 * carries it out; a dismissal **named by what it does**; and **focus landing on the title rather
 * than on the first action**, because that action is the destructive one and landing focus there
 * would make the worst outcome the cheapest to trigger (§20.6).
 *
 * All five of those are `BottomSheet`'s already, which is the whole reason this file is short.
 *
 * ## One sheet, two decks, and neither is the default
 *
 * The route is one and the sheet is one; what changes is what the people on the court lose, and
 * that is a **deck handed in** (`WithdrawWords`) rather than a fourth copy of the shape. `CallOff`
 * hands in `callOffPresentation.ts`' — the game, and the room that goes with it; `RemovalDoor`
 * hands in the removal's, from `challengeDetailPresentation.ts` — a send taken back, gone for the
 * people asked too. The withdraw's own three lines, which named a court people had joined, are
 * retired with the reading that drew them: nobody ends such a court for the others any more. So
 * `words` is required, and a caller that forgot would fail to compile rather than say the wrong
 * thing about what its act ends.
 *
 * ## Two surfaces, one sheet, and what the second one needed
 *
 * On the **game screen** the sheet draws no refusal and no pending state, on `ProposeSheet`'s own
 * line: confirming dismisses it, and everything the act then does happens on the control that
 * opened it — pending on that control, a refusal beside it, where the player can act on it. A sheet
 * that stayed up holding a failure would be a modal over the sentence that explains it.
 *
 * From a **Chats row**, and on the challenge screen's arm that borrows the row's door, there is no
 * such control: the button a swipe reveals closes with the row the moment it is pressed, and a list
 * row has no sentence to explain a refusal with. So there the sheet **is** the surface — it stays
 * up while the act is in flight, its act goes busy under the deck's own word, and a refusal is said
 * on it in words with the act still there to press again. The three props that carry that are
 * optional and absent on the game screen, so that surface's sheet is unchanged — `LeaveSheet`'s
 * exact line, one act over.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { BottomSheet, Button, Note, theme, type FocusTarget } from '@/shared/ui';

/** The sentences and the act's name — one deck per act, and the shape is this sheet's. */
export interface WithdrawWords {
  readonly title: string;
  readonly body: readonly string[];
  readonly act: string;
  /** The act while it is in flight — read only where the sheet stays up to carry it. */
  readonly inFlight: string;
  readonly closeLabel: string;
}

export interface WithdrawSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Confirming. The caller runs the act — and, on the game screen, dismisses the sheet. */
  readonly onWithdraw: () => void;
  /** What the sheet says: the removal's deck, or a game being called off. */
  readonly words: WithdrawWords;
  /**
   * The control the sheet was opened from. Focus returns there on close.
   *
   * **Required, where `BottomSheet`'s own is optional**, for `ProposeSheet`'s reason: the screen
   * behind this one is hidden while it is up, so a caller that forgot would strand a listener in
   * front of an act they have just declined to take.
   */
  readonly returnFocusTo: FocusTarget;
  /** The act is in flight — the list's sheet stays up and says so on its act. */
  readonly busy?: boolean;
  /** The act was refused — the list's sheet says why, in words, with the act still there. */
  readonly refusal?: string;
  /** No connection — the act greys under one amber note, as every act in this feature does. */
  readonly offline?: boolean;
}

export function WithdrawSheet({
  visible,
  onClose,
  onWithdraw,
  words,
  returnFocusTo,
  busy = false,
  refusal,
  offline = false,
}: WithdrawSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={words.title}
      closeLabel={words.closeLabel}
      returnFocusTo={returnFocusTo}
    >
      <View style={s.block}>
        {words.body.map((line) => (
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
          label={words.act}
          size="lg"
          busy={busy}
          busyLabel={words.inFlight}
          disabled={offline}
          onPress={onWithdraw}
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
