/**
 * The review — every answer in one place, and the control that turns them into a rating.
 *
 * **This is the last moment anything can be corrected, and the first time a player sees
 * the whole account of themselves.** The questionnaire asks one question at a time, which
 * is right for answering and wrong for checking: until this screen the evidence behind a
 * Skill rating had never been visible as a whole, and the first time it was, it had already
 * been fused into a number
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)).
 *
 * **No Level, likely range or Confidence appears here, and that is a rule rather than an
 * omission.** The no-running-estimate rule applies to the review exactly as it applies to a
 * question — a player who can see the number while they can still edit their answers is
 * being invited to tune it, and every answer on this screen is still editable.
 *
 * **Each entry opens its own question.** Changing an answer is the questionnaire's act, not
 * this screen's: the change sheet names what it costs, the engine re-routes from there, and
 * the player is asked whatever follows from what they actually said. Rebuilding that here
 * would be a second place a change can happen, and a second place the cost could be
 * misstated.
 *
 * **The rating is created by one deliberate control, and nothing else on this screen
 * creates anything.** Answering never did; stopping never did. So the irreversible act is
 * one the player chose, on a screen that shows them what they are choosing on behalf of.
 *
 * **Leaving works exactly as it does from a question**, through the same hook and the same
 * sheet — reaching the end of the questionnaire must not be the one place in the flow with
 * no way out.
 *
 * The three loading branches are the question screen's, for the same reasons: a paused
 * query is offline rather than broken, and a failed read gets a message and a retry.
 */

import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  behindOverlay,
  Button,
  CloseControl,
  Hairline,
  Note,
  PressableCard,
  theme,
} from '@/shared/ui';

import type { Sport } from '../domain/Sport';
import { positionOf } from '../domain/onboardingPass';
import { answeredQuestions, type StandingQuestion } from '../domain/questionNavigation';
import { runStanding } from '../domain/runStanding';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAssessment } from '../hooks/useAssessment';
import { useCompleteAssessment } from '../hooks/useCompleteAssessment';
import { useLeaveAssessment } from '../hooks/useLeaveAssessment';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { CalculatingScreen } from './CalculatingScreen';
import { LeaveAssessmentSheet } from './LeaveAssessmentSheet';
import { OnboardingChrome } from './OnboardingChrome';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { passEyebrow } from './passEyebrow';
import { sportLabel } from './sportPresentation';

export interface ReviewScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function ReviewScreen({ assessmentId, sport }: ReviewScreenProps) {
  const assessment = useAssessment(assessmentId);
  const complete = useCompleteAssessment(assessmentId);

  const pass = useOnboardingPass((state) => state.pass);
  const position = positionOf(pass, sport);
  /** One hook owns leaving a sport, and one latch owns every departure from this screen. */
  const onwards = useAdvanceThroughPass(sport);
  const { advance, showResultOf, showQuestionAt } = onwards;
  const leave = useLeaveAssessment(assessmentId, onwards);

  const step = assessment.data;
  const standing = runStanding(step);
  const answers = answeredQuestions(step);
  const name = sportLabel(sport);

  /**
   * The rating is being made, and the screen says so for at least as long as that is worth
   * saying.
   *
   * **It also holds the routing below.** The finished step is in hand the moment the
   * request lands, so without this the result would replace the calculating screen after a
   * frame — which reads as a glitch rather than as the moment the rating came into
   * existence. When it drops, whatever the run now says is where the player goes, and that
   * is the one place the destination is decided.
   */
  const [calculating, setCalculating] = useState(false);

  /**
   * One press's worth of consequence, read at the moment of the press.
   *
   * **The second guard, and deliberately kept as one.** What ordinarily stops the second
   * tap is that the first one takes the control off the screen — the calculating view
   * replaces this whole screen. But `calculating` is state, so every press in a burst that
   * beats the re-render reads it as `false`; a ref is read when the press happens, which is
   * when the question is being asked. It is the latch `useAdvanceThroughPass` and the answer
   * path already use, for the same reason.
   *
   * The server is safe either way — a second completion records nothing and returns the
   * first one's result — but *one rating and one navigation* is this client's half of that,
   * and this is the one control in onboarding whose press cannot be taken back.
   */
  const sending = useRef(false);

  /**
   * Where the player belongs, whenever it is no longer here.
   *
   * The review is the screen for a run that has **stopped**; the other three readings each
   * belong somewhere else, and one of them is the ordinary end of this screen's own work.
   * They are alternatives, so they are one effect and one latch — a run that finishes while
   * an abandonment is departing must not navigate twice.
   *
   * `asking` is reached two ways and neither is exotic: the run was answered on a second
   * device, or this device's completion was refused because the run had moved, and the
   * recovery re-read a question. Both mean the same thing — go and answer it.
   */
  useEffect(() => {
    if (calculating) return;
    if (standing === 'rated') showResultOf(assessmentId);
    else if (standing === 'ended') advance();
    else if (standing === 'asking') showQuestionAt(assessmentId);
  }, [calculating, standing, assessmentId, showResultOf, advance, showQuestionAt]);

  const submit = () => {
    if (sending.current || calculating) return;
    sending.current = true;
    setCalculating(true);

    // Started with the request rather than after it, so the floor is measured from the
    // moment the player pressed — which is the moment they started waiting.
    const held = new Promise<void>((resolve) => {
      setTimeout(resolve, theme.motion.hold.calculating);
    });

    complete.mutate(undefined, {
      onSuccess: () => void held.then(() => setCalculating(false)),
      // A failure has nothing to hold for: the screen the player is waiting on cannot
      // arrive, so the wait ends and the message takes its place beside the retry.
      onError: () => setCalculating(false),
      onSettled: () => {
        sending.current = false;
      },
    });
  };

  if (calculating) return <CalculatingScreen sport={sport} />;

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top', 'bottom']} {...behindOverlay(leave.confirming)}>
        <OnboardingChrome
          eyebrow={passEyebrow(sport, position)}
          title="Check your answers"
          // No back control: there is no question behind this screen to return to, and
          // every answer is reachable from the list itself. The right slot is the way out
          // of the flow, exactly as it is on a question.
          right={
            <CloseControl
              ref={leave.returnFocusTo}
              onPress={leave.ask}
              accessibilityLabel="Leave this rating"
              accessibilityHint="Offers continuing later or stopping this sport"
            />
          }
        />

        <ScrollView contentContainerStyle={s.content}>
          {assessment.fetchStatus === 'paused' ? (
            <Note variant="amber">
              You&apos;re offline. Your answers are safe on the server, and they&apos;ll load as
              soon as you&apos;re back.
            </Note>
          ) : null}

          {assessment.isPending && assessment.fetchStatus !== 'paused' ? (
            <ActivityIndicator
              accessibilityLabel="Loading your answers"
              color={theme.color.muted}
            />
          ) : null}

          {assessment.error !== null ? (
            <View style={s.failure}>
              <Note variant="coral" accessibilityRole="alert">
                {onboardingErrorMessage(assessment.error)}
              </Note>
              <Button
                label="Try again"
                variant="secondary"
                onPress={() => void assessment.refetch()}
              />
            </View>
          ) : null}

          {answers.length > 0 ? (
            <>
              <Text style={s.intro}>
                {`This is everything your ${name} level will be built from. Tap an answer to change it — nothing is recorded until you get your level.`}
              </Text>

              {answers.map((answered) => (
                <ReviewEntry
                  key={`${answered.position}-${answered.question.id}`}
                  answered={answered}
                  onPress={() => showQuestionAt(assessmentId, answered.position)}
                />
              ))}
            </>
          ) : null}
        </ScrollView>

        {standing === 'stopped' ? (
          <View style={s.action}>
            {complete.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {onboardingErrorMessage(complete.error)}
              </Note>
            ) : null}

            <Button
              label={`Get my ${name} level`}
              size="lg"
              accessibilityHint="Creates your rating from these answers, which can't be changed afterwards"
              onPress={submit}
            />
          </View>
        ) : null}
      </SafeAreaView>

      <LeaveAssessmentSheet
        visible={leave.confirming}
        sport={sport}
        onKeepGoing={leave.keepGoing}
        onContinueLater={leave.continueLater}
        onAbandon={leave.stopRating}
        leaving={leave.leaving}
        error={leave.error}
        returnFocusTo={leave.returnFocusTo}
      />
    </>
  );
}

interface ReviewEntryProps {
  readonly answered: StandingQuestion;
  readonly onPress: () => void;
}

/**
 * One question and what the player said to it.
 *
 * **The whole card is the control**, because the whole card is the thing a player wants to
 * change — a separate `Change` affordance beside it would be a smaller target for the same
 * act, and would read as though the words above it were not what it operates on.
 *
 * The question is the card's body and the answer sits below the fold, which is the shape
 * the question screen already uses for one object with two sections.
 */
function ReviewEntry({ answered, onPress }: ReviewEntryProps) {
  /**
   * The option in its own words.
   *
   * Absent only if a served entry named an option its own question does not carry, which
   * the contract does not produce — the transcript is replayed with the question as it was
   * asked. Drawing the question without an answer is what that would deserve; inventing
   * one, or dropping the entry, would both misdescribe the run.
   */
  const chosen = answered.question.options.find((option) => option.id === answered.answer);

  return (
    <PressableCard
      onPress={onPress}
      accessibilityLabel={
        chosen === undefined
          ? `Question ${answered.position}. ${answered.question.text}`
          : `Question ${answered.position}. ${answered.question.text} Your answer: ${chosen.text}`
      }
      accessibilityHint="Opens this question so you can change your answer"
    >
      <Text style={s.entryEyebrow}>{`Question ${answered.position}`}</Text>
      <Text style={s.entryQuestion}>{answered.question.text}</Text>

      {chosen !== undefined ? (
        <Hairline style={s.entryAnswer}>
          <Text style={s.entryAnswerLabel}>Your answer</Text>
          <Text style={s.entryAnswerText}>{chosen.text}</Text>
        </Hairline>
      ) : null}
    </PressableCard>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  failure: { gap: theme.space.sm },
  intro: { ...theme.type.tiny, color: theme.color.muted },
  entryEyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  entryQuestion: { ...theme.type.question, color: theme.color.ink },
  entryAnswer: { gap: theme.space.xxs },
  entryAnswerLabel: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  entryAnswerText: { ...theme.type.h2, color: theme.color.ink },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
