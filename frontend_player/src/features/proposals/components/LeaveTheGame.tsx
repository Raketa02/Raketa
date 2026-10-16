/**
 * ***Leave the game*** — at the foot of a booked game's details, with the line under it stating
 * what leaving costs at this moment, behind today's *Before you leave* sheet with the new words
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A4.1, details 10; the
 * mechanics §13).
 *
 * **What it costs is the read's** (`leaving`, #544; said on the sheet, never under the door): before the club's cut-off nothing is taken and
 * the hold on the card is let go (Q113), after it the share stays taken, and — while a full game
 * waits for one payment — nobody has paid and leaving withdraws the yes. The server folds it on its
 * own clock and quotes the same words the departure answers with; nothing here works out a refund.
 *
 * **The door's shape is the group exit's** (`ExitDoor`): the sheet is the surface while the act is
 * in flight — its act busy, a refusal said on it in words with the act still there — and the door
 * is hidden from a listener while it is up, one label on the door and on the act. Success is a toast
 * saying what happened — before the cut-off, that nothing was taken (Q113); **from a booked
 * game the player goes back to Home**, which no longer holds it, and from a game still filling the
 * details stay, read again.
 *
 * **Two acts behind one door**: a booked game's departure (`POST /bookings/{id}/departure`), and on
 * the details of a full game that waits for one payment, the yes withdrawn (#625: *Leave the game
 * with its sheet*, sent as the withdrawal) — the same words, the same sheet.
 *
 * The door is 6.1's `secondary` where details 10 draws dark red text — the group exit's call, for
 * its reason: red is *ended badly* (1.3), and the sheet is what makes it deliberate (Part 16).
 */

import type { UseMutationResult } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { behindOverlay, Button, theme } from '@/shared/ui';

import type { Leaving } from '../domain/home';
import type { LeavingKind } from '../domain/vocabulary';

import { leaveRefusal, leavingSheetBody, leftToast } from './homePresentation';
import { LeaveSheet } from './LeaveSheet';
import { LEAVE_THE_GAME } from './leaveSheetCopy';

export interface LeaveTheGameProps {
  /** What leaving costs now — the read's. */
  readonly leaving: Leaving;
  /**
   * The departure — a booked game's (`useLeaveBooking`), or, on a full game that waits for one
   * payment, the yes withdrawn (`useLeaveWhileWaiting`). It answers which of the three it was.
   */
  readonly act: UseMutationResult<LeavingKind, AppError, void>;
  /** Where the player goes once they have left — Home from a booked game; nowhere from the details. */
  readonly afterLeaving?: () => void;
}

export function LeaveTheGame({ leaving, act: leave, afterLeaving }: LeaveTheGameProps) {
  const online = useIsOnline();
  const [open, setOpen] = useState(false);
  const door = useRef<View>(null);

  function close() {
    setOpen(false);
    leave.reset();
  }

  function confirm() {
    leave.mutate(undefined, {
      onSuccess: (left) => {
        setOpen(false);
        showToast({ message: leftToast(left), tone: 'ok' });
        afterLeaving?.();
      },
    });
  }

  return (
    <>
      <View ref={door} style={s.door} {...behindOverlay(open)}>
        {/* The button alone: what leaving costs is said on the sheet it opens. */}
        <Button
          label={LEAVE_THE_GAME}
          variant="secondary"
          size="lg"
          onPress={() => setOpen(true)}
        />
      </View>

      <LeaveSheet
        visible={open}
        onClose={close}
        onLeave={confirm}
        returnFocusTo={door}
        body={leavingSheetBody(leaving)}
        busy={leave.isPending}
        refusal={leave.error === null ? undefined : leaveRefusal(leave.error)}
        offline={!online}
      />
    </>
  );
}

const s = StyleSheet.create({
  door: { gap: theme.space.xs },
});
