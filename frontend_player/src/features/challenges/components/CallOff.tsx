/**
 * ***Call it off*** — the control on the game screen, the withdraw's sheet reworded in front of it,
 * and what a refusal costs it ([#419](https://github.com/Raketa02/Raketa/issues/419),
 * [ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).
 *
 * **The withdraw, grown to a reopened court.** A court that has been a game and lost somebody is
 * `LINE_UP_INCOMPLETE` again, and the withdraw is its exit too: the challenge is withdrawn exactly
 * as a half-built court is, the game reaches its fourth end in the same act, and the room is
 * destroyed as it is for any withdrawal. So the act is `useWithdrawChallenge`, the sheet is
 * `WithdrawSheet` handed `callOffPresentation.ts`' words, and this file is the control that puts
 * the two on a screen that is not this feature's — composed by `features/plans` into the game
 * screen's `courtActs` slot, the shape `LeaveGame` already takes.
 *
 * ## Who may, and it is answered here
 *
 * The organiser's — or, once the organiser's own seat is open, any remaining player's (#411 rule
 * 4). The organiser is a **challenge** fact and a game carries none, so the answer is a join:
 * `useHoldsTheExit` reads the challenge list the tab bar already holds, keyed by the game's
 * `challengeId`, and folds `holdsTheExit` over the row for the reader it looks up itself, as the
 * list's other readers do. It is asked **inside** this component
 * rather than by the composer, so `features/plans` never learns what an organiser is: what the
 * composer hands in is the one rule that is its own — *a seat is open* — and this feature adds
 * the one that is its own. Both fail soft into no control, and the join is over a list the app
 * already keeps rather than a detail read for one boolean — asked only while `offered`, so a
 * full court's screen does not refetch that list for an answer it would not draw.
 *
 * ## Only while a seat is open, and not only while the moment is ahead
 *
 * A full court that will not play has no such control — its window lapses into *Never played*, as
 * today — so `offered` is the composer's *a seat is open*. The moment does **not** gate it: the
 * withdraw is not guarded by the agreed moment (*a court whose game's window has already closed
 * is withdrawn all the same*), so on a short court past its moment this is the one act left,
 * after the fill and the leave have both stood down.
 *
 * **It is a prop and not a mount**, for `LeaveGame`'s reason: a mutate-level `onSuccess` does not
 * fire on a component that has unmounted mid-flight, and the composer's rule flips under the act
 * the moment the re-read lands — which is exactly when this one's success is being carried out.
 *
 * ## Quiet, destructive, behind a confirmation, and above *Leave this game*
 *
 * `secondary`, because ending a game for everybody is never the primary act on a screen about it;
 * the sheet, because it is irreversible and reaches other people; above the leave, because the
 * design puts the act that ends the game before the act that only takes one person out of it.
 *
 * **One label on the control and on the sheet's act**, on `SEND_CHALLENGE_LABEL`'s precedent —
 * and, on the challenge screen's, what is under the sheet is hidden from a screen reader while it
 * is up (`behindOverlay`), so the first press can only reach the control and the second can only
 * reach the act. The sheet is a **sibling** of the block that carries those props, never a child,
 * or it would hide itself along with everything else.
 *
 * ## What a refusal costs — `actRefusal`'s fold, on a different screen
 *
 * `challenge_not_found` **leaves the screen**. `withdraw_is_the_organisers`,
 * `not_a_half_built_line_up` and `challenge_is_over` — *this court is not what the screen thought
 * it was* — **re-read and say nothing**: the games list is what the screen folds its arm from,
 * and the fold the re-read lands on is the sentence; the re-read is the composer's (`onReRead`),
 * because the read is theirs. `account_held` and everything else is **said**, in the sentence
 * every write in this feature says it with.
 *
 * ## Success stays
 *
 * The hook re-reads the games, the plans, the rooms and the challenges. Nothing here navigates:
 * the screen is about a game that still exists — it has an ending now — and the games list
 * coming back with `CALLED_OFF` is what re-folds it into the called-off arm, plan and doors gone,
 * this control with them.
 */

import { useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { Button, Note, behindOverlay, theme } from '@/shared/ui';

import { actRefusal } from '../domain/actRefusal';
import { useWithdrawChallenge } from '../hooks/useChallenge';
import { useHoldsTheExit } from '../hooks/useChallenges';

import { actOnRefusal } from './actOnRefusal';
import {
  CALL_IT_OFF,
  CALL_OFF_SHEET_BODY,
  CALL_OFF_SHEET_CLOSE_LABEL,
  CALL_OFF_SHEET_TITLE,
  CALLING_IT_OFF,
} from './callOffPresentation';
import { challengeErrorMessage } from './challengeErrorMessage';
import { WithdrawSheet, type WithdrawWords } from './WithdrawSheet';

/** The withdraw's sheet, in the words of a game being called off. */
const CALL_OFF_WORDS: WithdrawWords = {
  title: CALL_OFF_SHEET_TITLE,
  body: CALL_OFF_SHEET_BODY,
  act: CALL_IT_OFF,
  closeLabel: CALL_OFF_SHEET_CLOSE_LABEL,
};

export interface CallOffProps {
  /** The challenge behind the game — the record the withdraw lands on. */
  readonly challengeId: string;
  /**
   * Whether calling it off is offered right now — the composer's rule, a seat being open. Who
   * may is this feature's rule, added here. Off, nothing is drawn unless a call-off is already
   * in flight; see the module note.
   */
  readonly offered: boolean;
  /**
   * What a stale tap costs: **a re-read, never a toast.** The composer holds the games read this
   * screen folds from, so the composer re-reads it; the fold it lands on is the sentence.
   */
  readonly onReRead: () => void;
}

export function CallOff({ challengeId, offered, onReRead }: CallOffProps) {
  const withdraw = useWithdrawChallenge();
  const holdsTheExit = useHoldsTheExit(challengeId, offered);
  const online = useIsOnline();

  /** Whether the confirmation is up, and the control it hands focus back to — Part 13's rule. */
  const [confirming, setConfirming] = useState(false);
  const control = useRef<View>(null);

  /** The sheet asked; this is the answer. Success stays: the re-read is the redraw. */
  function go(): void {
    setConfirming(false);
    withdraw.mutate(challengeId, { onError: (error) => actOnRefusal(error, onReRead) });
  }

  const refusal = withdraw.error === null ? undefined : actRefusal(withdraw.error);

  // Either rule off and nothing in flight: nothing to draw. A call-off in flight keeps its busy
  // control until the reply says where it landed.
  if (!(offered && holdsTheExit) && !withdraw.isPending) return null;

  return (
    <>
      <View style={s.block} {...behindOverlay(confirming)}>
        {refusal?.kind === 'SAY_SO' ? (
          <Note variant="coral" accessibilityRole="alert">
            {challengeErrorMessage(refusal.error)}
          </Note>
        ) : null}

        {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}

        <View ref={control}>
          <Button
            label={CALL_IT_OFF}
            variant="secondary"
            busy={withdraw.isPending}
            busyLabel={CALLING_IT_OFF}
            disabled={!online}
            onPress={() => {
              withdraw.reset();
              setConfirming(true);
            }}
          />
        </View>
      </View>

      <WithdrawSheet
        visible={confirming}
        onClose={() => setConfirming(false)}
        onWithdraw={go}
        words={CALL_OFF_WORDS}
        returnFocusTo={control}
      />
    </>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
});
