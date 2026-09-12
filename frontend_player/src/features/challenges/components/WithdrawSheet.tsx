/**
 * **The withdraw's confirmation** — `SH.propose`'s exact shape, a second time.
 *
 * The second irreversible act in this app that reaches other people, and it takes the shape the
 * first one already has ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §2.6): a real modal (9.1) with `accessibilityViewIsModal`, hidden siblings and Android back; a
 * title naming the **moment** rather than the act, so the act is named once by the control that
 * carries it out; a dismissal **named by what it does**; and **focus landing on the title rather
 * than on the first action**, because that action is the destructive one and landing focus there
 * would make the worst outcome the cheapest to trigger (§20.6).
 *
 * All five of those are `BottomSheet`'s already, which is the whole reason this file is short:
 * what a second sheet on that shape owes is its four sentences and the name of its act.
 *
 * ## The same sheet, reworded, on a court that has been a game
 *
 * The withdraw reaches a reopened court and calls the game off in the act
 * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)), and the
 * confirmation is **this sheet with different words** rather than a fourth copy of its shape: the
 * act is the same route, the second body line — the room goes with it — is the same consequence,
 * and what changes is what the people still in it lose. So the deck is a prop, defaulting to the
 * withdraw's own; `CallOff` hands in `callOffPresentation.ts`', and the challenge screen hands in
 * nothing ([#419](https://github.com/Raketa02/Raketa/issues/419)).
 *
 * ## The second body line is what earns the sheet
 *
 * ADR-0142 chose **destroyed, not delisted** — the conversation and everything written in it go
 * with the challenge — and a confirmation that did not say so would be hiding the only
 * consequence the player cannot undo. It is the one line here that is not a restatement of
 * *irreversible*.
 *
 * ## What it does not draw
 *
 * **No refusal, and no pending state**, on `ProposeSheet`'s own line: confirming here dismisses
 * the sheet, and everything the withdraw then does happens on the control that opened it —
 * pending on that control, and a refusal beside it, where the player can act on it. A sheet that
 * stayed up holding a failure would be a modal over the sentence that explains it.
 *
 * **And it says nothing about the pair rule releasing.** That is a fact about what becomes
 * possible afterwards, and a confirmation is not the place to sell a consequence
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.3).
 */

import { StyleSheet, Text, View } from 'react-native';

import { BottomSheet, Button, theme, type FocusTarget } from '@/shared/ui';

import {
  WITHDRAW_SHEET_BODY,
  WITHDRAW_SHEET_CLOSE_LABEL,
  WITHDRAW_SHEET_TITLE,
  WITHDRAW_THE_CHALLENGE,
} from './challengeDetailPresentation';

/** The four sentences and the act's name — one deck per surface, and the shape is this sheet's. */
export interface WithdrawWords {
  readonly title: string;
  readonly body: readonly string[];
  readonly act: string;
  readonly closeLabel: string;
}

/** The withdraw's own words, and the default: a half-built court, ended. */
const WITHDRAW_WORDS: WithdrawWords = {
  title: WITHDRAW_SHEET_TITLE,
  body: WITHDRAW_SHEET_BODY,
  act: WITHDRAW_THE_CHALLENGE,
  closeLabel: WITHDRAW_SHEET_CLOSE_LABEL,
};

export interface WithdrawSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Confirming. The caller dismisses the sheet and runs the withdraw — see the module note. */
  readonly onWithdraw: () => void;
  /** What the sheet says. The withdraw's own unless the surface is a game that is being called off. */
  readonly words?: WithdrawWords;
  /**
   * The control the sheet was opened from. Focus returns there on close.
   *
   * **Required, where `BottomSheet`'s own is optional**, for `ProposeSheet`'s reason: the screen
   * behind this one is hidden while it is up, so a caller that forgot would strand a listener in
   * front of an act they have just declined to take.
   */
  readonly returnFocusTo: FocusTarget;
}

export function WithdrawSheet({
  visible,
  onClose,
  onWithdraw,
  words = WITHDRAW_WORDS,
  returnFocusTo,
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

      <View style={s.action}>
        <Button label={words.act} size="lg" onPress={onWithdraw} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xs },
  body: { ...theme.type.tiny, color: theme.color.ink },
  action: { paddingTop: theme.space.md },
});
