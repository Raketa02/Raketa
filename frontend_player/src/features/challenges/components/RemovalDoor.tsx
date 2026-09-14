/**
 * **The removal's door** — *Remove the challenge*, met from the organiser's **Chats row** or from
 * the **challenge screen**, while nobody has joined
 * ([#428](https://github.com/Raketa02/Raketa/issues/428),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4, §6).
 *
 * **The withdraw, met as a door.** The act is `useWithdrawChallenge` unchanged in what it sends —
 * the same route *Call it off* posts from the game screen — and what this file is, is the door a
 * row reveals and an arm draws, on `DepartureDoor`'s exact shape: a render prop handing the
 * surface an `ActDoor`, and the sheet drawn here as a sibling of whatever the surface drew, hidden
 * from a screen reader while the sheet is up. Whether the door is offered at all is not this
 * file's: the row asks `mayRemove` and the arm reads its `mayRemove`, one rule in `challenge.ts`,
 * so a swipe and a button cannot disagree about whose act this is.
 *
 * ## Which sheet, and which words
 *
 * `WithdrawSheet` — the withdrawal's own, the one *Call it off* draws — handed the removal's deck
 * from `challengeDetailPresentation.ts`: one line, that it is gone for the people asked too, and
 * the act named once on the door and on the sheet. The withdraw's three lines about a court people
 * had joined are retired with that reading; nobody ends such a court for the others any more.
 *
 * ## What the door does that the screen's old control did not
 *
 * The sheet stays up while the act is in flight and **says a refusal in words** —
 * `removeRefusalMessage`: *somebody's in now* for the one refusal a stale row invites, and the
 * departure's own sentence for a court that is already over — where the challenge screen's
 * withdraw re-read and said nothing. When the sheet is up, where focus returns, and what a refusal
 * costs beside the words and when it is paid are `useActDoor`'s, shared with the departure's door.
 *
 * ## Success is the reply, and the row goes with it
 *
 * `useWithdrawChallenge` writes the reply into the detail and — since this ticket — into the
 * challenge list, where the inbox drops an own removal at once (`belongsOnTheInbox`); so the
 * organiser's row is gone the moment the reply lands and before any re-read, as the leaver's is.
 * The room a court the organiser was alone in again still had is **invalidated rather than
 * patched**, on the withdraw's own line: the reply says nothing about a room. Nothing here
 * navigates: the reader is on a list, or on a screen whose next fold says *You withdrew this*.
 */

import type { ReactNode } from 'react';
import { View } from 'react-native';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { behindOverlay } from '@/shared/ui';

import { useWithdrawChallenge } from '../hooks/useChallenge';
import { useActDoor, type ActDoor } from '../hooks/useActDoor';

import {
  REMOVE_SHEET_BODY,
  REMOVE_SHEET_CLOSE_LABEL,
  REMOVE_SHEET_TITLE,
  REMOVE_THE_CHALLENGE,
  REMOVING,
  removeRefusalMessage,
} from './challengeDetailPresentation';
import { WithdrawSheet, type WithdrawWords } from './WithdrawSheet';

/** The name the row's accessibility action goes by — see `ActDoorAsk.actionName`. */
const REMOVE_ACTION = 'remove-the-challenge';

/** The withdrawal's sheet, in the words of a send taken back. */
const REMOVE_WORDS: WithdrawWords = {
  title: REMOVE_SHEET_TITLE,
  body: REMOVE_SHEET_BODY,
  act: REMOVE_THE_CHALLENGE,
  inFlight: REMOVING,
  closeLabel: REMOVE_SHEET_CLOSE_LABEL,
};

export interface RemovalDoorProps {
  /** The challenge the organiser takes back. */
  readonly challengeId: string;
  /**
   * The surface's own answer to a refusal, beside the words — the challenge screen re-reads the
   * detail its arm folds from. Absent on the list, whose reads are the two lists re-read by the
   * door.
   */
  readonly onRefusal?: (error: AppError) => void;
  /** What the surface does once the reply has landed — `DepartureDoor`'s prop, for its reason. */
  readonly onDone?: () => void;
  /** The surface, drawn around the door it is handed. */
  readonly children: (door: ActDoor) => ReactNode;
}

export function RemovalDoor({ challengeId, onRefusal, onDone, children }: RemovalDoorProps) {
  const remove = useWithdrawChallenge();
  const online = useIsOnline();
  const { door, confirming, close, confirm } = useActDoor({
    act: remove,
    challengeId,
    label: REMOVE_THE_CHALLENGE,
    actionName: REMOVE_ACTION,
    onRefusal,
    onDone,
  });

  return (
    <>
      {/* The sheet is a **sibling** of the element carrying these props, never a child, or it
          would hide itself — `DepartureDoor`'s line. */}
      <View {...behindOverlay(confirming)}>{children(door)}</View>

      <WithdrawSheet
        visible={confirming}
        onClose={close}
        onWithdraw={confirm}
        words={REMOVE_WORDS}
        returnFocusTo={door.control}
        busy={remove.isPending}
        refusal={remove.error === null ? undefined : removeRefusalMessage(remove.error)}
        offline={!online}
      />
    </>
  );
}
