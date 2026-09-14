/**
 * **A door onto an act that reaches other people** — what the two doors a Chats row can reveal
 * have in common, held once ([#427](https://github.com/Raketa02/Raketa/issues/427),
 * [#428](https://github.com/Raketa02/Raketa/issues/428)).
 *
 * `DepartureDoor` (*Leave the game*) and `RemovalDoor` (*Remove the challenge*) are one shape met
 * with two acts: a surface is handed a {@link ActDoor} and draws it however a door looks there — a
 * control behind a swiped card, a `secondary` button among an arm's others — and the door draws
 * its own sheet beside whatever the surface drew. What differs between them is the act, the sheet
 * and the words; what is the same is **when the sheet is up, where focus returns, and what a
 * refusal costs and when it is paid** — and a rule written twice is a rule that drifts, so it is
 * here and each door is the act, the sheet and the words alone.
 *
 * ## The sheet is the surface, so it stays up
 *
 * On the game screen a sheet dismisses on confirm and the control it came from carries the
 * pending state and the refusal. A door has no such control: the button a swipe reveals closes
 * with the row the moment it is pressed, and a list row has no sentence to explain a refusal with.
 * So the sheet stays up while the act is in flight, closes on success, and on a refusal stays for
 * the words the door's deck writes on it, with the act still there to press again.
 *
 * ## What a refusal costs beside the words — and it is paid when the sheet closes
 *
 * `actRefusal`'s fold still answers *which read to make next*: for every code that means *this
 * court is not what the row thought it was* the two lists a court is drawn on are re-read
 * (`useReReadCourtLists`), so a court that has genuinely ended goes from the list when the server
 * says it has — and the surface's own re-read, where it has one, is `onRefusal`'s. The challenge
 * screen passes its `actOnRefusal`, which re-reads the detail the arm folds from; the list passes
 * nothing, because the lists are the whole of what it reads.
 *
 * **Both wait for the dismissal.** The sheet is drawn inside the row it is about, and a re-read
 * that landed *this one is already over* would take the row away — and the sheet with it,
 * mid-sentence. The words are what the refusal buys the player, so they are read first; the
 * re-read is owed and paid the moment the sheet is dismissed, which is also when the row it removes
 * has stopped being looked at. The same order holds on the challenge screen, where the detail's
 * re-read re-folds the arm the door is drawn on.
 *
 * ## Success is the reply
 *
 * Each act's hook writes its reply where the rows read from, so what should be gone is gone the
 * moment the reply lands and before any re-read; nothing here navigates. The reader is on a list,
 * or on a screen whose next fold says what happened.
 */

import { useRef, useState, type RefObject } from 'react';
import type { AccessibilityActionEvent, AccessibilityActionInfo, View } from 'react-native';
import type { UseMutationResult } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { actRefusal } from '../domain/actRefusal';
import type { AnsweredChallenge } from '../domain/challengeDetail';

import { useReReadCourtLists } from './useChallenge';

/** What a surface is handed to draw a door with. */
export interface ActDoor {
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

export interface ActDoorAsk {
  /** The act, as its own hook returns it — pending never optimistic, the reply already written. */
  readonly act: UseMutationResult<AnsweredChallenge, AppError, string>;
  /** The challenge the act lands on. */
  readonly challengeId: string;
  /** The act's word, on the door and in the rotor. */
  readonly label: string;
  /**
   * The name a row's accessibility action goes by — a custom action, so the platform reads the
   * `label` beside it and the name is only what `onAccessibilityAction` matches on.
   */
  readonly actionName: string;
  /**
   * The surface's own answer to a refusal, beside the words — the challenge screen re-reads the
   * detail its arm folds from. Absent on the list, whose reads are the two lists re-read here.
   * `| undefined` so a door hands its own optional prop straight through.
   */
  readonly onRefusal?: ((error: AppError) => void) | undefined;
}

/** What a door gets back: the thing it hands the surface, and the three things its sheet needs. */
export interface ActDoorHandle {
  /** What the surface is handed. */
  readonly door: ActDoor;
  /** Whether the sheet is up — the surface hides what it drew behind it while it is. */
  readonly confirming: boolean;
  /** The sheet's dismissal — and whatever a refusal left owed is paid here. */
  readonly close: () => void;
  /** The sheet's act, confirmed. The sheet stays up until the reply says where it landed. */
  readonly confirm: () => void;
}

export function useActDoor({
  act,
  challengeId,
  label,
  actionName,
  onRefusal,
}: ActDoorAsk): ActDoorHandle {
  const reReadCourtLists = useReReadCourtLists();

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
    act.reset();
    owed.current = undefined;
    setConfirming(true);
  }

  function close(): void {
    setConfirming(false);
    const refused = owed.current;
    owed.current = undefined;
    if (refused === undefined) return;
    reReadCourtLists();
    onRefusal?.(refused);
  }

  function confirm(): void {
    act.mutate(challengeId, {
      onSuccess: () => setConfirming(false),
      onError: (error) => {
        owed.current = actRefusal(error).kind === 'SAY_SO' ? undefined : error;
      },
    });
  }

  return {
    confirming,
    close,
    confirm,
    door: {
      label,
      open,
      control,
      action: { name: actionName, label },
      onAccessibilityAction: (event) => {
        if (event.nativeEvent.actionName === actionName) open();
      },
    },
  };
}
