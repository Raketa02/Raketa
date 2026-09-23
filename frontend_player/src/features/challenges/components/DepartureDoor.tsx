/**
 * **The departure's door** — *Leave the game*, met from a **conversation row** on Chats, before
 * the court is whole or after ([#427](https://github.com/Raketa02/Raketa/issues/427),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §1, §6) — and since
 * [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §4 **the one place a game is left from**: the game screen's *Leave this game* and the
 * challenge screen's door are gone, so a player who wants out goes where every seat is left.
 *
 * **Named for the shape rather than the word.** A *door*: what a Chats row reveals when it is
 * swiped. The act is `useLeaveGame`, pending never optimistic, and the sheet in front of it is
 * `LeaveSheet`.
 *
 * ## It hands the surface a door and draws the sheet itself
 *
 * A render prop rather than a control, because the surface that carries it decides what a door
 * looks like there — a control behind a swiped card on the list — and this feature never learns
 * which. What the surface gets is an `ActDoor`: the act's word, a way to open the sheet, the
 * accessibility action a row offers a listener in place of the swipe, and the ref the sheet
 * returns focus to. The sheet is rendered **here**, as a sibling of whatever the surface drew, so
 * the act's whole shape — words, pending, refusal — is one file's. And what the surface drew is
 * hidden from a screen reader while the sheet is up (`behindOverlay`): one label on the door and
 * on the sheet's act, so the first press can only reach the door and the second can only reach
 * the act.
 *
 * ## What is the door's and what is the act's
 *
 * When the sheet is up, where focus returns, and what a refusal costs and when it is paid are
 * **`useActDoor`'s** — the same rule for this door and for `RemovalDoor`, held once
 * ([#428](https://github.com/Raketa02/Raketa/issues/428)). What is this file's is the act, the
 * sheet and the words: `useLeaveGame`, `LeaveSheet` with the list's one line, and
 * `leaveRefusalMessage` for the four codes the route documents, over `challengeErrorMessage`'s
 * fallback. Success is the reply: `useLeaveGame` writes it into the challenge list and drops the
 * room the court opened from the conversations list, so both rows are gone the moment the reply
 * lands and before any re-read (#427: *gone without a refetch*).
 *
 * ## The sheet says what the leaving does, off the row the list holds
 *
 * **The one line changes when the leaving would end the court**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §9): the reader is the only other accepted seat and nobody is deciding, which is the ending
 * rule read a move ahead, and `game_id` says whether that *calls the game off — for {name} too*
 * or *closes this court for {name}*. The rule is `leavingWouldEnd`'s, read off the challenge's
 * row on the list this feature already holds for the tab bar (`useLeavingWouldEnd`). The row can
 * be a beat behind the server; the server's answer is what happens, said on the sheet as every
 * refusal here is.
 */

import type { ReactNode } from 'react';
import { View } from 'react-native';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { behindOverlay } from '@/shared/ui';

import { useLeaveGame } from '../hooks/useChallenge';
import { useLeavingWouldEnd } from '../hooks/useChallenges';
import { useActDoor, type ActDoor } from '../hooks/useActDoor';

import { LEAVE_THE_GAME, leaveFromTheListBody, leaveRefusalMessage } from './leaveGamePresentation';
import { LeaveSheet } from './LeaveSheet';

/** The name the row's accessibility action goes by — see `ActDoorAsk.actionName`. */
const LEAVE_ACTION = 'leave-the-game';

export interface DepartureDoorProps {
  /** The challenge whose seat the reader gives up. */
  readonly challengeId: string;
  /**
   * The surface's own answer to a refusal, beside the words. Absent on the list, whose reads are
   * the two lists re-read by the door — kept on the door's shape (`useActDoor`'s) for a surface
   * that has a read of its own.
   */
  readonly onRefusal?: (error: AppError) => void;
  /**
   * What the surface does once the reply has landed — `useActDoor`'s: nothing on the list, whose
   * row goes on the reply.
   */
  readonly onDone?: () => void;
  /** The surface, drawn around the door it is handed. */
  readonly children: (door: ActDoor) => ReactNode;
}

export function DepartureDoor({ challengeId, onRefusal, onDone, children }: DepartureDoorProps) {
  const leave = useLeaveGame();
  const online = useIsOnline();
  const ends = useLeavingWouldEnd(challengeId);
  const { door, confirming, close, confirm } = useActDoor({
    act: leave,
    challengeId,
    label: LEAVE_THE_GAME,
    actionName: LEAVE_ACTION,
    onRefusal,
    onDone,
  });

  return (
    <>
      {/* One label on the door and on the sheet's act, on `CallOff`'s line: what is under the
          sheet is hidden from a screen reader while it is up, so the first press can only reach
          the door and the second can only reach the act. The sheet is a **sibling** of the
          element carrying these props, never a child, or it would hide itself. */}
      <View {...behindOverlay(confirming)}>{children(door)}</View>

      <LeaveSheet
        visible={confirming}
        onClose={close}
        onLeave={confirm}
        returnFocusTo={door.control}
        body={leaveFromTheListBody(ends)}
        busy={leave.isPending}
        refusal={leave.error === null ? undefined : leaveRefusalMessage(leave.error)}
        offline={!online}
      />
    </>
  );
}
