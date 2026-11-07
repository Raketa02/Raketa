/**
 * ***Leave or call it off***, a friends game's sender's one way out before the cut-off — the
 * place of *Leave the game*, and a sheet with **two ways**
 * ([#760](https://github.com/Raketa02/Raketa/issues/760), over #752's; the friends mechanics §11.2;
 * the screens §9; the words §29.10):
 *
 * ```
 * [ Leave or call it off ]                                the door, on the details
 *
 * Before you leave                                       ✕
 * [ Call it off for everyone                          ]
 * [ Everyone is told, nobody pays, and the court goes  ]
 * [ back to Ogrody 33.                                 ]
 * [ Leave · the others play on                        ]
 * [ You pay nothing. Your friends keep the court; a    ]   Split
 * [ seat still empty on Fri 10:00 calls the game off…  ]
 * ```
 *
 * - ***Call it off for everyone*** — every hold and cover let go, nobody pays, the court the
 *   club's again (`POST /bookings/{id}/call-off`); the details then read *Called off*.
 * - ***Leave · the others play on*** — the departure (`POST /bookings/{id}/departure`): with
 *   **Split** the sender stops covering and it is an ordinary game, a seat still empty at the
 *   cut-off calling it off with nobody paying; with **Whole court** the sender still pays the court,
 *   and whoever takes their seat pays them their share back. Done, the player goes back to Home,
 *   as from any booked game they left.
 *
 * **This is the only door to calling it off** (the product owner, 2026-11-07): #759's separate
 * *Call it off* beside it went, since both pressed the same call-off, and the door's label names
 * both ways so a sender looking to call it off — the cover warning's third action — finds it. The
 * server reads *Call it off* (`can_call_off`) only where it also reads a leave before the cut-off,
 * so the sender always has this door wherever that button was. **Neither choice asks again**: the
 * sheet is the deliberate step, as any leave's is.
 *
 * **Each choice carries its line as the button's gloss** — a column of two answers whose labels
 * alone don't say what choosing one means, `Button`'s own case — and is named aloud with it. Both
 * are `secondary`: neither is the sheet's one primary act, and the sheet is what makes either
 * deliberate. **The sheet is the surface while either is in flight** (`LeaveTheGame`'s shape): the
 * act busy, a refusal said on it with both still there, the door hidden from a listener while it is
 * up. After the cut-off the sender is any late leaver, and the door is `LeaveTheGame`'s — *Leave
 * the game* again.
 */

import type { UseMutationResult } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { offlineMessage, type AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { showToast } from '@/shared/store/toast.store';
import { behindOverlay, BottomSheet, Button, Note, theme } from '@/shared/ui';

import type { LeavingKind, PayMode } from '../domain/vocabulary';
import { useCallOffFriendsGame } from '../hooks/useFriendsGameWrites';

import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import {
  callOffLine,
  callOffRefusal,
  glossedAnswerSpoken,
  playOnLine,
  senderLeftToast,
} from './friendsGamePresentation';
import { leaveRefusal } from './homePresentation';
import { LEAVE_SHEET_CLOSE_LABEL, LEAVE_SHEET_TITLE } from './leaveSheetCopy';

const COPY = FRIENDS_GAME_COPY.sendersLeave;

export interface SendersLeaveProps {
  readonly bookingId: string;
  readonly payMode: PayMode;
  /** The club the court goes back to — absent for one the read no longer names. */
  readonly club: string | undefined;
  /** The club's cut-off, which a Split game still short at calls itself off. */
  readonly cutOff: string | undefined;
  /** What whoever takes the Whole-court sender's seat pays them back. */
  readonly shareGrosze: number;
  /** The departure — the booked game's (`useLeaveBooking`). */
  readonly leave: UseMutationResult<LeavingKind, AppError, void>;
  /** Where the sender goes once they have left — Home. */
  readonly afterLeaving: () => void;
}

export function SendersLeave({
  bookingId,
  payMode,
  club,
  cutOff,
  shareGrosze,
  leave,
  afterLeaving,
}: SendersLeaveProps) {
  const online = useIsOnline();
  const [open, setOpen] = useState(false);
  const door = useRef<View>(null);
  const callOff = useCallOffFriendsGame(bookingId);
  const busy = leave.isPending || callOff.isPending;

  const callOffWords = callOffLine(club);
  const playOnWords = playOnLine(payMode, { cutOff, shareGrosze });
  const refusal =
    leave.error !== null
      ? leaveRefusal(leave.error)
      : callOff.error !== null
        ? callOffRefusal(callOff.error)
        : undefined;

  function close() {
    if (busy) return;
    setOpen(false);
    leave.reset();
    callOff.reset();
  }

  return (
    <>
      <View ref={door} {...behindOverlay(open)}>
        <Button label={COPY.door} variant="secondary" size="lg" onPress={() => setOpen(true)} />
      </View>

      <BottomSheet
        visible={open}
        onClose={close}
        title={LEAVE_SHEET_TITLE}
        closeLabel={LEAVE_SHEET_CLOSE_LABEL}
        returnFocusTo={door}
      >
        <View style={s.body} testID="senders-leave-sheet">
          {refusal === undefined ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {refusal}
            </Note>
          )}
          {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}
          <Button
            label={COPY.callOff}
            gloss={callOffWords}
            accessibilityLabel={glossedAnswerSpoken(COPY.callOff, callOffWords)}
            variant="secondary"
            size="lg"
            busy={callOff.isPending}
            busyLabel={COPY.calling}
            disabled={!online || leave.isPending}
            onPress={() => {
              leave.reset();
              callOff.mutate(undefined, {
                onSuccess: () => {
                  setOpen(false);
                  showToast({ message: COPY.calledOff, tone: 'ok' });
                },
              });
            }}
          />
          <Button
            label={COPY.playOn}
            gloss={playOnWords}
            accessibilityLabel={glossedAnswerSpoken(COPY.playOn, playOnWords)}
            variant="secondary"
            size="lg"
            busy={leave.isPending}
            busyLabel={COPY.leaving}
            disabled={!online || callOff.isPending}
            onPress={() => {
              callOff.reset();
              leave.mutate(undefined, {
                onSuccess: () => {
                  setOpen(false);
                  showToast({ message: senderLeftToast(payMode), tone: 'ok' });
                  afterLeaving();
                },
              });
            }}
          />
        </View>
      </BottomSheet>
    </>
  );
}

const s = StyleSheet.create({
  body: { paddingTop: theme.space.sm, gap: theme.space.sm },
});
