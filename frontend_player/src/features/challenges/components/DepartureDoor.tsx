/**
 * **The departure's door** — *Leave the game*, met from a **list row** or from the **challenge
 * screen**, before the court is whole or after ([#427](https://github.com/Raketa02/Raketa/issues/427),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §1, §6).
 *
 * **The same act as `LeaveGame`, met somewhere else — and named for the shape rather than the
 * word**, because two components an article apart would be one name. `LeaveGame` is the control
 * at the bottom of the game screen's plan lead; this is a *door*: what a Chats row reveals when it
 * is swiped, and what the challenge screen draws on its two live arms. The act is one —
 * `useLeaveGame`, pending never optimistic — and so is the sheet in front of it; what differs is
 * where the reader is standing when they meet it, and that decides two things this file exists to
 * hold.
 *
 * ## It hands the surface a door and draws the sheet itself
 *
 * A render prop rather than a control, because the surface that carries it decides what a door
 * looks like there — a control behind a swiped card on the list, a `secondary` button among the
 * arm's others on the challenge screen — and this feature never learns which. What every surface
 * gets is the same {@link LeaveDoor}: the act's word, a way to open the sheet, the accessibility
 * action a row offers a listener in place of the swipe, and the ref the sheet returns focus to.
 * The sheet is rendered **here**, as a sibling of whatever the surface drew, so the act's whole
 * shape — words, pending, refusal — is one file's whether it is met on a row or on a screen. And
 * what the surface drew is hidden from a screen reader while the sheet is up (`behindOverlay`),
 * on `CallOff`'s line: one label on the door and on the sheet's act, so the first press can only
 * reach the door and the second can only reach the act.
 *
 * ## The sheet is the surface, so it stays up
 *
 * On the game screen the sheet dismisses on confirm and the control it came from carries the
 * pending state and the refusal. Here there is no such control: the button a swipe reveals closes
 * with the row the moment it is pressed, and a list row has no sentence to explain a refusal with.
 * So the sheet stays up while the act is in flight and goes busy on its act, closes on success,
 * and on a refusal **says why in words** (`leaveRefusalMessage`) with the act still there to press
 * again. The words are the deck's — the four codes the route documents each have a sentence, and
 * everything else is the sentence every write in this feature says it with.
 *
 * ## What a refusal costs, beside the words — and it is paid when the sheet closes
 *
 * `actRefusal`'s fold still answers *which read to make next*: for every code that means *this
 * court is not what the row thought it was* the two lists are re-read, so a court that has
 * genuinely ended goes from the list when the server says it has — and the surface's own re-read,
 * where it has one, is `onRefusal`'s. The challenge screen passes its `actOnRefusal`, which
 * re-reads the detail the arm folds from; the list passes nothing, because the lists are the
 * whole of what it reads. Which lists, and how they are marked, is `useReReadCourtLists`' —
 * a hook, because a cache effect is `hooks/`' to declare and this file only decides *when*.
 *
 * **Both wait for *Stay in*.** The sheet is drawn inside the row it is about, and a re-read that
 * landed *this one is already over* would take the row away — and the sheet with it, mid-sentence.
 * The words are what the refusal buys the player, so they are read first; the re-read is owed and
 * paid the moment the sheet is dismissed, which is also when the row it removes has stopped being
 * looked at. The same order holds on the challenge screen, where the detail's re-read re-folds the
 * arm the door is drawn on.
 *
 * ## Success is the reply
 *
 * `useLeaveGame` writes the reply into the challenge list and drops the room the court opened from
 * the conversations list, so both rows are gone the moment the reply lands and before any re-read
 * (#427: *gone without a refetch*), and then re-reads the four lists the seat touched. Nothing here
 * navigates: the reader is on a list, or on a screen whose next fold says *You left*.
 */

import { useRef, useState, type ReactNode, type RefObject } from 'react';
import { View, type AccessibilityActionEvent, type AccessibilityActionInfo } from 'react-native';

import type { AppError } from '@/shared/errors';
import { useIsOnline } from '@/shared/lib/platform';
import { behindOverlay } from '@/shared/ui';

import { actRefusal } from '../domain/actRefusal';
import { useLeaveGame, useReReadCourtLists } from '../hooks/useChallenge';

import {
  LEAVE_FROM_THE_LIST_BODY,
  LEAVE_THE_GAME,
  leaveRefusalMessage,
} from './leaveGamePresentation';
import { LeaveSheet } from './LeaveSheet';

/**
 * The name a row's accessibility action goes by — a custom action, so the platform reads the
 * `label` beside it and the name is only what `onAccessibilityAction` matches on.
 */
const LEAVE_ACTION = 'leave-the-game';

/** What a surface is handed to draw the door with. */
export interface LeaveDoor {
  /** The act's word — on the revealed control, or on the screen's button. */
  readonly label: string;
  /** Open the sheet. The act itself is behind it, never here. */
  readonly open: () => void;
  /**
   * The host element the sheet returns focus to when it closes — the surface attaches it to
   * whatever it drew the door on, so a listener who declines is put back where they were. A
   * `RefObject<View>` rather than the sheet's own `FocusTarget`, because it is what a `ref` prop
   * takes and what the sheet takes both.
   */
  readonly control: RefObject<View>;
  /**
   * The same door for a listener, who cannot swipe: a row offers this in its actions rotor and
   * routes the event back through `onAccessibilityAction`. A screen that draws a button needs
   * neither — the button is already reachable.
   */
  readonly action: AccessibilityActionInfo;
  readonly onAccessibilityAction: (event: AccessibilityActionEvent) => void;
}

export interface DepartureDoorProps {
  /** The challenge whose seat the reader gives up. */
  readonly challengeId: string;
  /**
   * The surface's own answer to a refusal, beside the words — the challenge screen re-reads the
   * detail its arm folds from. Absent on the list, whose reads are the two lists re-read here.
   */
  readonly onRefusal?: (error: AppError) => void;
  /** The surface, drawn around the door it is handed. */
  readonly children: (door: LeaveDoor) => ReactNode;
}

export function DepartureDoor({ challengeId, onRefusal, children }: DepartureDoorProps) {
  const leave = useLeaveGame();
  const reReadCourtLists = useReReadCourtLists();
  const online = useIsOnline();

  /**
   * Whether the sheet is up, and **the element it hands focus back to.** Route-local, because it
   * is a fact about a press rather than about the court, and the ref is Part 13's rule for every
   * overlay in this app.
   */
  const [confirming, setConfirming] = useState(false);
  const control = useRef<View>(null);
  /**
   * A refusal whose re-read is owed — held until the sheet closes, so the words are read before
   * the read that may take the row, and the sheet, away. See the module note.
   */
  const owed = useRef<AppError>();

  function open(): void {
    // A refusal belongs to the press that caused it; a new press starts clean.
    leave.reset();
    owed.current = undefined;
    setConfirming(true);
  }

  /** *Stay in* — and whatever a refusal left owed is paid now that the words have been read. */
  function close(): void {
    setConfirming(false);
    const refused = owed.current;
    owed.current = undefined;
    if (refused === undefined) return;
    reReadCourtLists();
    onRefusal?.(refused);
  }

  /** The sheet asked; this is the answer. The sheet stays up until the reply says where it landed. */
  function go(): void {
    leave.mutate(challengeId, {
      onSuccess: () => setConfirming(false),
      onError: (error) => {
        owed.current = actRefusal(error).kind === 'SAY_SO' ? undefined : error;
      },
    });
  }

  const door: LeaveDoor = {
    label: LEAVE_THE_GAME,
    open,
    control,
    action: { name: LEAVE_ACTION, label: LEAVE_THE_GAME },
    onAccessibilityAction: (event) => {
      if (event.nativeEvent.actionName === LEAVE_ACTION) open();
    },
  };

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
        onLeave={go}
        returnFocusTo={control}
        body={[LEAVE_FROM_THE_LIST_BODY]}
        busy={leave.isPending}
        refusal={leave.error === null ? undefined : leaveRefusalMessage(leave.error)}
        offline={!online}
      />
    </>
  );
}
