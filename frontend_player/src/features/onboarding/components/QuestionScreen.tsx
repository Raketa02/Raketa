/**
 * The question screen — the whole adaptive loop, on one screen.
 *
 * **There is one question screen and it renders whatever arrives.** The opening "have you
 * played this sport" question and the layoff question are ordinary questions from the
 * engine's bank with their own categories, not screens of their own — which is also why a
 * first-timer finishes the assessment in a single answer.
 *
 * Reading order is fixed and deliberate: **category → progress → situation → question →
 * answers**. The category is the screen heading and the question is never the page title,
 * because a title is read last on a screen the eye scans top-down.
 *
 * **Tapping an answer selects it; the confirm control submits it.** The confirm is what
 * earns the irreversibility — an explicit moment to commit removes any need for a timed
 * undo window, and a mis-tap costs nothing. It is present from the first question so the
 * control never appears from nowhere, and **its label is identical on every question,
 * including the last**: the engine decides it has enough information *after* the answer
 * arrives, so the client cannot know which question is the last one and a changing label
 * would claim otherwise. (`busyLabel` is about the request in flight, not about which
 * question this is; nothing about it implies an end.)
 *
 * **There is no back control, and none may be added.** An answer's numeric meaning depends
 * on the difficulty tier it was asked at, and that tier was chosen from the estimate as it
 * stood — so revising an earlier answer would silently change what every later answer
 * meant (ADR-0017). Nothing here pushes a route either: the next question replaces this
 * one's data in place, so the device back gesture has no answered question to return to.
 *
 * **There is a way out, and it is not back navigation.** The close control in the header
 * opens a confirm offering to continue later, to stop rating this sport, or to carry on.
 * Leaving the questionnaire is not revisiting an answer, and every exit below is a
 * `replace`: no path here returns the player to a question they have already answered.
 *
 * **There is no live estimate.** The player sees no running Level at any point, which is
 * why the design system's `[3,17 so far]` chip is deliberately absent from the meta row.
 */

import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  behindOverlay,
  Button,
  Card,
  CloseControl,
  Hairline,
  Note,
  PressableCard,
  Tag,
  theme,
} from '@/shared/ui';

import type { AnswerOption } from '../domain/Assessment';
import type { Sport } from '../domain/Sport';
import { positionOf } from '../domain/onboardingPass';
import { useAbandonAssessment } from '../hooks/useAbandonAssessment';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAnswerQuestion } from '../hooks/useAnswerQuestion';
import { useAssessment } from '../hooks/useAssessment';
import { useDeferredRuns } from '../store/deferredRuns.store';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { LeaveAssessmentSheet } from './LeaveAssessmentSheet';
import { OnboardingChrome } from './OnboardingChrome';
import { difficultyTag } from './difficultyTag';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { passEyebrow } from './passEyebrow';
import { sportLabel } from './sportPresentation';

/** Identical on every question. See the note above — this is a domain rule, not copy. */
const CONFIRM_LABEL = 'Confirm answer';

export interface QuestionScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function QuestionScreen({ assessmentId, sport }: QuestionScreenProps) {
  const router = useRouter();
  const assessment = useAssessment(assessmentId);
  const answer = useAnswerQuestion(assessmentId);
  const abandon = useAbandonAssessment(assessmentId);
  const beginIfAbsent = useOnboardingPass((state) => state.beginIfAbsent);
  const defer = useDeferredRuns((state) => state.defer);

  /**
   * A run reached with no pass running is a pass of one sport, and saying so **during the
   * first render** is the whole requirement: the chrome reads a position immediately, and
   * an effect flushes after that render has already happened. Doing it from the entry gate
   * was rejected for the same reason — its redirect fires before an effect would run.
   *
   * The ref makes it once-per-mount; `beginIfAbsent` makes it harmless when the picker has
   * already begun one. It is only safe to begin conditionally because ending is now
   * reliable — otherwise this would adopt a finished walk's queue, which is the defect it
   * exists to fix wearing a new interface.
   */
  const begun = useRef(false);
  if (!begun.current) {
    begun.current = true;
    beginIfAbsent([sport]);
  }

  const pass = useOnboardingPass((state) => state.pass);
  /** Absent for a sport outside the pass — reachable by deep link. The bar then goes. */
  const position = positionOf(pass, sport);
  /**
   * Leaving this sport, in one place. The screen holds no navigation and no latch of its
   * own: which route each answer means, and what a failed start does, are the hook's, and
   * the result screen calls the same one so the two cannot disagree again.
   */
  const onwards = useAdvanceThroughPass(sport);
  const { advance, showResultOf } = onwards;
  const step = assessment.data;
  const question = step?.question;
  /**
   * **An abandoned run has no question either — and no rating.** Before abandonment
   * existed, "nothing left to ask" could only mean "there is a result"; it cannot now,
   * and reading it that way would show a player who stopped rating padel a screen
   * announcing their padel rating is ready. This is the run being ended somewhere else —
   * another device, or a link to a run that is already over — because abandoning from
   * this screen navigates rather than waiting to be told.
   */
  const endedWithoutRating = step?.status === 'abandoned';
  const finished = assessment.isSuccess && question === undefined && !endedWithoutRating;

  const [confirmingExit, setConfirmingExit] = useState(false);
  const closeControl = useRef<View | null>(null);

  /**
   * The selection is held with the question it belongs to, so it clears itself when the
   * next question arrives and **survives a failed submission**, which is the whole point:
   * a player who lost their connection must not also lose the answer they just gave.
   */
  const [choice, setChoice] = useState<{
    readonly questionId: string;
    readonly optionId: string;
  }>();
  const selectedOptionId =
    question !== undefined && choice?.questionId === question.id ? choice.optionId : undefined;

  /**
   * Which question this is: the answers already behind the run, plus one.
   *
   * **The count is read from the step, never recomputed or remembered here.** It is the
   * replayed transcript's length, so a run resumed after four answers reads as question
   * five — on this device, on a second one, or after a reinstall. A client counting what
   * it had itself shown could only ever say "question 1", because the transcript never
   * lived on the device. The outstanding question is deliberately not in the server's
   * count, which is what the plus one is.
   */
  const number = step === undefined ? 0 : step.questionsAsked + 1;

  // The run is over: the outstanding question is gone and a rating exists.
  useEffect(() => {
    if (!finished) return;
    showResultOf(assessmentId);
  }, [finished, showResultOf, assessmentId]);

  // Ended elsewhere, with no rating to show. There is nothing to say about a run that is
  // simply gone, so the flow moves on the same way an abandonment from here would.
  useEffect(() => {
    if (!endedWithoutRating) return;
    advance();
  }, [endedWithoutRating, advance]);

  const submit = () => {
    if (question === undefined || selectedOptionId === undefined) return;
    answer.mutate({ questionId: question.id, optionId: selectedOptionId });
  };

  /**
   * Nothing is sent. The run stays in progress with every answer intact, and the gate is
   * told to leave it alone until the next launch — which is what makes this a way out
   * rather than a redirect back to the question one frame later.
   */
  const continueLater = () => {
    setConfirmingExit(false);
    defer(assessmentId);
    router.replace('/');
  };

  /**
   * The confirm stays open until the flow has somewhere to be, so a failure on either
   * half — the abandonment or the next sport's opening question — lands in front of the
   * player beside the control that retries it. Pressing again re-abandons, which the
   * server treats as a no-op, and tries the departure again.
   */
  const stopRatingThisSport = () => {
    abandon.mutate(undefined, { onSuccess: advance });
  };

  // The abandon request, then the next sport's opening question: one departure to the
  // player, and either half can fail.
  const leaving = abandon.isPending || onwards.advancing;

  return (
    <>
      <SafeAreaView
        style={s.screen}
        edges={['top', 'bottom']}
        // A sheet is a real modal: while it is open nothing behind it is reachable by a
        // screen reader. The sheet is a sibling below, never a child — inside here it
        // would hide itself along with the question.
        {...behindOverlay(confirmingExit)}
      >
        <OnboardingChrome
          eyebrow={passEyebrow(sport, position)}
          title={question?.category ?? sportLabel(sport)}
          position={position}
          right={
            <CloseControl
              ref={closeControl}
              onPress={() => setConfirmingExit(true)}
              accessibilityLabel="Leave this rating"
              accessibilityHint="Offers continuing later or stopping this sport"
            />
          }
        />

        <ScrollView contentContainerStyle={s.content}>
          {/* Paused, not loading — see the picker: an offline query is held, not failed. */}
          {assessment.fetchStatus === 'paused' ? (
            <Note variant="amber">
              You&apos;re offline. Your question will load as soon as you&apos;re back, and your
              answers so far are safe on the server.
            </Note>
          ) : null}

          {assessment.isPending && assessment.fetchStatus !== 'paused' ? (
            <ActivityIndicator
              accessibilityLabel="Loading your question"
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

          {question !== undefined ? (
            <>
              <View style={s.meta}>
                <Text style={s.counter}>{`Question ${number}`}</Text>
                <DifficultyTag tier={question.tier} />
              </View>

              <Card>
                {/* The situation is a shaded header inside the same card as the question,
                    and the hairline is the fold between them — one object, two sections. */}
                <View style={s.situation}>
                  <Text style={s.situationEyebrow}>Picture this</Text>
                  <Text style={s.situationText}>{question.situation}</Text>
                </View>

                <Hairline>
                  <Text style={s.question}>{question.text}</Text>
                  <Text style={s.qualifier}>{question.qualifier}</Text>
                </Hairline>
              </Card>

              {question.options.map((option) => (
                <AnswerCard
                  key={option.id}
                  option={option}
                  selected={option.id === selectedOptionId}
                  onPress={() => setChoice({ questionId: question.id, optionId: option.id })}
                />
              ))}
            </>
          ) : null}
        </ScrollView>

        {question !== undefined ? (
          <View style={s.action}>
            {/* A stale-step conflict never reaches here — it is recovered as a re-read, so
                a double-tapped confirm leaves the player on the correct question with
                nothing to dismiss. What is left is a genuine failure, and the retry is the
                confirm control itself, with the selection still made. */}
            {answer.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {onboardingErrorMessage(answer.error)}
              </Note>
            ) : null}

            <Button
              label={CONFIRM_LABEL}
              size="lg"
              disabled={selectedOptionId === undefined}
              busy={answer.isPending}
              busyLabel="Submitting…"
              accessibilityHint="Your answer cannot be changed afterwards"
              onPress={submit}
            />
          </View>
        ) : null}
      </SafeAreaView>

      <LeaveAssessmentSheet
        visible={confirmingExit}
        sport={sport}
        onKeepGoing={() => setConfirmingExit(false)}
        onContinueLater={continueLater}
        onAbandon={stopRatingThisSport}
        leaving={leaving}
        error={abandon.error ?? onwards.error}
        returnFocusTo={closeControl}
      />
    </>
  );
}

/** Absent where the engine supplies no tier — the opening and layoff questions have none. */
function DifficultyTag({ tier }: { readonly tier: string | undefined }) {
  if (tier === undefined) return null;

  const tag = difficultyTag(tier);
  return (
    <Tag label={tag.label} variant={tag.variant} accessibilityLabel={`Difficulty: ${tag.label}`} />
  );
}

interface AnswerCardProps {
  readonly option: AnswerOption;
  readonly selected: boolean;
  readonly onPress: () => void;
}

/**
 * One answer. Individually reachable, and **selection is announced as state** rather than
 * drawn only as a border — a state that exists only as a colour excludes whoever cannot
 * see that colour, which is why the word is there too.
 *
 * The hint says what pressing does, because pressing an answer here does *not* submit it.
 */
function AnswerCard({ option, selected, onPress }: AnswerCardProps) {
  return (
    <PressableCard
      onPress={onPress}
      selected={selected}
      accessibilityLabel={option.text}
      accessibilityHint="Selects this answer"
      style={s.answer}
    >
      <Text style={s.answerText}>{option.text}</Text>
      {selected ? <Text style={s.selectedMark}>Selected</Text> : null}
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
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  counter: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  // Bled to the card's edges and back up over its padding, so the shaded block reads as a
  // header of the card rather than a panel floating inside it.
  situation: {
    backgroundColor: theme.color.paper2,
    marginHorizontal: -theme.space.md,
    marginTop: -theme.space.md,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.sm,
    borderTopLeftRadius: theme.radius.card,
    borderTopRightRadius: theme.radius.card,
    gap: theme.space.xxs,
  },
  situationEyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  situationText: { ...theme.type.tiny, color: theme.color.ink },
  question: { ...theme.type.question, color: theme.color.ink },
  qualifier: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
  answer: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  answerText: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  selectedMark: {
    ...theme.type.eyebrow,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
