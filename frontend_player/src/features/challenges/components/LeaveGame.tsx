/**
 * ***Leave this game*** — the control at the bottom of the game screen, the sheet in front of it,
 * and what a refusal costs it ([#418](https://github.com/Raketa02/Raketa/issues/418),
 * [ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
 *
 * **A challenge act, drawn on a game.** The seat that reopens is the challenge's, so the act, its
 * route and its words are this feature's — and the surface is the game screen's plan lead, which
 * `features/games` draws and `features/plans` composes. So this is one component, exported
 * through `types.ts`, that the composition hands into the screen's last slot the way it hands
 * the plan into the plan slot: the screen draws it in order and cannot read it, and this feature
 * never learns which screen it is on.
 *
 * ## Whether it is drawn is the composer's decision, and it is one rule
 *
 * The control is drawn **only while the agreed moment is ahead** (#411 rule 1): past it the
 * server refuses with `game_moment_has_passed`, and a control the act would refuse is a promise
 * the app cannot keep. The moment is the plan's, and the plan is `features/plans`' — so that
 * feature reads `momentHasPassed` off the same ladder that names the card, and hands the answer
 * in as `offered`. Nothing here asks.
 *
 * **It is a prop and not a mount**, deliberately. A mutate-level `onSuccess` does not fire on a
 * component that has unmounted mid-flight, and the composer's rule can flip under a leave in
 * flight — a focus refetch landing past the moment while the `POST` is out. Drawn as a prop, the
 * component stays mounted, draws nothing once the act is no longer offered and nothing is in
 * flight, and still goes back when the reply lands.
 *
 * ## Quiet, destructive, behind a confirmation, and last
 *
 * `secondary`, because leaving is never the primary act on a screen about a game you are in; the
 * sheet, because it is irreversible and reaches other people; last, because a destructive control
 * belongs under everything the screen exists to offer. **Not on the card, not in the chat** —
 * the author's rule (#411 rule 8).
 *
 * ## What a refusal costs — `actRefusal`'s fold, on a different screen
 *
 * `challenge_not_found` **leaves the screen**: no challenge of yours has that id, and there is
 * nothing behind this screen to stay on. The four codes that mean *this game is not what the
 * screen thought it was* — `not_a_game_yet`, `challenge_is_over`, `game_is_history`,
 * `game_moment_has_passed` — **re-read and say nothing**: the games list is what the screen
 * folds its arm from, and the fold the re-read lands on is the sentence. The re-read is the
 * composer's (`onReRead`), because the read is theirs: this feature holds no games query, and a
 * second one here would be a second clock. `account_held` and everything else is **said**, in
 * the sentence every write in this feature says it with.
 *
 * ## Success goes back
 *
 * The hook re-reads the games, the plans and the rooms; the leaver's card is gone from the rail
 * because the server no longer lists it. What is left for this component is the way out — `back`
 * — because the screen it was on is a screen about a game the reader is no longer in, whichever
 * door they came in by.
 */

import { useRef, useState } from 'react';
import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { offlineMessage, type AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { Button, Note, theme } from '@/shared/ui';

import { actRefusal } from '../domain/actRefusal';
import { useLeaveGame } from '../hooks/useChallenge';

import { challengeErrorMessage } from './challengeErrorMessage';
import { LEAVE_THIS_GAME, LEAVING } from './leaveGamePresentation';
import { LeaveSheet } from './LeaveSheet';

export interface LeaveGameProps {
  /** The challenge behind the game — the record the seat reopens on. */
  readonly challengeId: string;
  /**
   * Whether leaving is offered right now — the composer's rule, the agreed moment being ahead.
   * Off, nothing is drawn unless a leave is already in flight; see the module note.
   */
  readonly offered: boolean;
  /**
   * What a stale tap costs: **a re-read, never a toast.** The composer holds the games read this
   * screen folds from, so the composer re-reads it; the fold it lands on is the sentence, and the
   * control disappears with the rung or the moment.
   */
  readonly onReRead: () => void;
}

export function LeaveGame({ challengeId, offered, onReRead }: LeaveGameProps) {
  const leave = useLeaveGame();
  const online = useIsOnline();

  /**
   * Whether the confirmation is up, and **the control it hands focus back to.**
   *
   * Route-local, because it is a fact about a press rather than about the game, and the ref is
   * Part 13's rule for every overlay in this app: without it a listener who declines the app's
   * third irreversible act is returned to the top of the screen with no idea what happened.
   */
  const [confirming, setConfirming] = useState(false);
  const control = useRef<View>(null);

  /** What a refusal costs, carried out — see the module note. */
  function actOn(error: AppError): void {
    const next = actRefusal(error);
    if (next.kind === 'READ_IT_BACK') onReRead();
    if (next.kind === 'LEAVE') router.back();
  }

  /** The sheet asked; this is the answer. */
  function go(): void {
    setConfirming(false);
    leave.mutate(challengeId, { onSuccess: () => router.back(), onError: actOn });
  }

  const refusal = leave.error === null ? undefined : actRefusal(leave.error);

  // The rule flipped under a leave that is not in flight: nothing to draw, and nothing to wait
  // for. A leave in flight keeps its busy control until the reply says where it landed.
  if (!offered && !leave.isPending) return null;

  return (
    <View style={s.block}>
      {/* The sentence a refused act writes, and **no new copy for the ones that re-read**: they
          are handled by reading, and what they end up saying is the screen's own fold. */}
      {refusal?.kind === 'SAY_SO' ? (
        <Note variant="coral" accessibilityRole="alert">
          {challengeErrorMessage(refusal.error)}
        </Note>
      ) : null}

      {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}

      {/* A `View` around the button, because focus has to land on a **host element** this
          component holds a ref to and `Button` is a component — `WithdrawSheet`'s own shape. */}
      <View ref={control}>
        <Button
          label={LEAVE_THIS_GAME}
          variant="secondary"
          busy={leave.isPending}
          busyLabel={LEAVING}
          disabled={!online}
          onPress={() => {
            leave.reset();
            setConfirming(true);
          }}
        />
      </View>

      <LeaveSheet
        visible={confirming}
        onClose={() => setConfirming(false)}
        onLeave={go}
        returnFocusTo={control}
      />
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
});
