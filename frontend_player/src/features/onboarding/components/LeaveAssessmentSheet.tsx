/**
 * The way out of the questionnaire — three doors, and they are not the same door.
 *
 * **Leaving and abandoning have opposite consequences**, so they are two controls rather
 * than one with a qualifier:
 *
 * - *Continue later* keeps the run in progress. Nothing is sent, nothing is lost, and the
 *   next launch lands back on the outstanding question.
 * - *Stop rating this sport* ends the run. Its answers are discarded and the sport is free
 *   to be rated again from the beginning.
 *
 * Both are reachable because either one alone breaks something. Without abandonment the
 * entry gate becomes a trap — a player who has decided against padel is routed into the
 * padel questionnaire on every launch, and the only escape is finishing a rating they did
 * not want. Without "continue later", any interruption costs every answer given, in a run
 * of up to ten questions.
 *
 * **The abandon control says what it discards, on the control itself.** This is the one
 * destructive action in onboarding: the questions behind the player can be walked back
 * over freely
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)), and this is
 * the control that throws their answers away. A player here expects that tapping something
 * does what it says, so it had better say it.
 *
 * Keeping going is the primary and is listed last, where the thumb is: the safe option
 * is the easy one, and the two ways out sit above it as deliberate choices.
 *
 * **None of this is back navigation, and that distinction survived ADR-0020.** The
 * questionnaire has a way back through it now; this is the way *out* of it, and the two
 * are different doors on opposite sides of the header.
 */

import { StyleSheet, Text } from 'react-native';

import { BottomSheet, Button, Note, PressableCard, theme, type FocusTarget } from '@/shared/ui';

import type { AppError } from '@/shared/errors';

import type { Sport } from '../domain/Sport';

import { onboardingErrorMessage } from './onboardingErrorMessage';
import { sportLabel } from './sportPresentation';

export interface LeaveAssessmentSheetProps {
  readonly visible: boolean;
  readonly sport: Sport;
  /** Dismissal — the scrim, the close control and the Android back gesture. */
  readonly onKeepGoing: () => void;
  readonly onContinueLater: () => void;
  readonly onAbandon: () => void;
  /** The abandon request is in flight, or the next sport is being started after it. */
  readonly leaving: boolean;
  readonly error: AppError | null;
  readonly returnFocusTo: FocusTarget;
}

export function LeaveAssessmentSheet({
  visible,
  sport,
  onKeepGoing,
  onContinueLater,
  onAbandon,
  leaving,
  error,
  returnFocusTo,
}: LeaveAssessmentSheetProps) {
  const name = sportLabel(sport);

  return (
    <BottomSheet
      visible={visible}
      onClose={onKeepGoing}
      title="Leave this rating?"
      // Not "Keep answering": that is the button below, and two controls announcing the
      // same name is a screen reader offering the same choice twice.
      closeLabel="Close and keep answering"
      returnFocusTo={returnFocusTo}
    >
      {/* The failure sits above the controls that caused it, and the abandon control
          below stays pressable — the server treats a second abandonment of the same run
          as a no-op, so pressing again is safe however far the first attempt got. */}
      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {onboardingErrorMessage(error)}
        </Note>
      ) : null}

      <LeaveOption
        title="Continue later"
        // Not "back to this question": the same sheet is offered from the review, where the
        // player has answered every question there is and none is outstanding.
        detail={`We'll bring you back to where you left off. Every answer you've given for ${name} is kept.`}
        hint="Leaves the questionnaire and keeps your answers"
        disabled={leaving}
        onPress={onContinueLater}
      />

      <LeaveOption
        title={`Stop rating ${name}`}
        detail={`The answers you've given for ${name} are discarded. You can rate ${name} again from the beginning any time.`}
        hint="Ends this rating and discards your answers"
        disabled={leaving}
        onPress={onAbandon}
      />

      <Button
        label="Keep answering"
        size="lg"
        busy={leaving}
        busyLabel="Leaving…"
        onPress={onKeepGoing}
      />
    </BottomSheet>
  );
}

interface LeaveOptionProps {
  readonly title: string;
  readonly detail: string;
  readonly hint: string;
  readonly disabled: boolean;
  readonly onPress: () => void;
}

/**
 * One way out, as a card rather than a button.
 *
 * A button carries a label and nothing else, and each of these needs a sentence saying
 * what happens to the answers — which is the only thing that tells the two apart. The
 * accessible name is the title, so the option is findable by what it is called, and the
 * consequence follows in the same element rather than as a hint a screen reader may be
 * configured not to read.
 */
function LeaveOption({ title, detail, hint, disabled, onPress }: LeaveOptionProps) {
  return (
    <PressableCard
      onPress={onPress}
      disabled={disabled}
      accessibilityLabel={`${title}. ${detail}`}
      accessibilityHint={hint}
      style={s.option}
    >
      <Text style={s.optionTitle}>{title}</Text>
      <Text style={s.optionDetail}>{detail}</Text>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  option: { gap: theme.space.xxs },
  optionTitle: { ...theme.type.h2, color: theme.color.ink },
  optionDetail: { ...theme.type.tiny, color: theme.color.muted },
});
