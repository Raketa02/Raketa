/**
 * Changing an answer — with what it costs put in front of the player, before it happens.
 *
 * **This is the second destructive act in onboarding and it is confirmed like the first.**
 * Abandoning a run gets a sheet naming what it discards
 * ({@link LeaveAssessmentSheet}); changing an answer discards every answer after it
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)) and gets the
 * same treatment. No new design decision is involved — the pattern is the one this app
 * already uses for putting a consequence in front of a player rather than performing it
 * silently.
 *
 * **A tap on an answered question opens this; it does not change anything.** That keeps
 * the question screen's one rule about answers intact — tapping selects, a deliberate
 * second act commits — and here the deliberate second act is the control below rather
 * than the screen's confirm, because what it commits to is not the same thing.
 *
 * **The cost is stated, never implied.** How many later answers go is the decision the
 * player is being asked to take, and it is different for a change at question two of nine
 * and one at question eight.
 *
 * **Keeping the answer is the primary and is last, where the thumb is** — the leave
 * sheet's rule, for the leave sheet's reason: the safe option is the easy one. It is also
 * what the scrim, the close control and the Android back gesture all do, which is what
 * makes a sheet safe to dismiss.
 *
 * **A failure keeps the sheet open** with the message above the control that retries it.
 * The retry is the same control, with the same option still chosen: a revision that never
 * reached the server must not cost the player the answers a successful one would have
 * kept.
 */

import { StyleSheet, Text } from 'react-native';

import { BottomSheet, Button, Note, theme, type FocusTarget } from '@/shared/ui';

import type { AppError } from '@/shared/errors';

import type { ProposedRevision } from '../domain/revision';

import { onboardingErrorMessage } from './onboardingErrorMessage';
import { revisionConsequence } from './revisionConsequence';

/** A change the player has asked for, with the words the question offered it in. */
export interface AnswerChange {
  readonly revision: ProposedRevision;
  readonly answerText: string;
}

export interface ChangeAnswerSheetProps {
  /** What is being asked about. Absent when nothing is, which is the sheet closed. */
  readonly change: AnswerChange | undefined;
  readonly onChange: () => void;
  /** Dismissal — the scrim, the close control, the Android back gesture, and the button. */
  readonly onKeep: () => void;
  readonly changing: boolean;
  readonly error: AppError | null;
  readonly returnFocusTo: FocusTarget;
}

export function ChangeAnswerSheet({
  change,
  onChange,
  onKeep,
  changing,
  error,
  returnFocusTo,
}: ChangeAnswerSheetProps) {
  return (
    <BottomSheet
      visible={change !== undefined}
      onClose={onKeep}
      title="Change this answer?"
      // Never just "Close": a screen reader announces the name out of any visual context,
      // and what this closes on is the answer they already have.
      closeLabel="Close and keep your answer"
      returnFocusTo={returnFocusTo}
    >
      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {onboardingErrorMessage(error)}
        </Note>
      ) : null}

      {change !== undefined ? (
        <>
          <Text style={s.instead}>{`Your answer becomes “${change.answerText}”.`}</Text>
          <Text style={s.cost}>{revisionConsequence(change.revision.discards)}</Text>
        </>
      ) : null}

      <Button
        label="Change my answer"
        variant="secondary"
        size="lg"
        busy={changing}
        busyLabel="Changing…"
        accessibilityHint="Records this answer instead and asks you the questions that follow from it"
        onPress={onChange}
      />

      <Button label="Keep my answer" size="lg" disabled={changing} onPress={onKeep} />
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  instead: { ...theme.type.h2, color: theme.color.ink },
  cost: { ...theme.type.tiny, color: theme.color.muted },
});
