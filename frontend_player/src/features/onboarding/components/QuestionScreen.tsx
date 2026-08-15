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
 * **Tapping an answer selects it; the confirm control submits it.** The confirm is the
 * deliberate submission of one answer — a mis-tap costs nothing. It is present from the
 * first question so the control never appears from nowhere, and **its label is identical
 * on every question, including the last**: the engine decides it has enough information
 * *after* the answer arrives, so the client cannot know which question is the last one and
 * a changing label would claim otherwise. It no longer has to — answering creates nothing
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)).
 *
 * **A player can walk back over the questions they have answered, and it costs nothing.**
 * The served transcript arrives with every step, so moving issues no request at all and
 * shows the answer they gave as they gave it. Movement is the header's back control and
 * the forward control below; the navigator draws where they are and never moves them,
 * because ten tappable segments across the content width is a 26pt target against the
 * 44pt minimum. This slice **only moves** — changing an answer is its own act, with its
 * own confirmation, and is not built here.
 *
 * **Leaving is still not going back.** The close control in the header opens a confirm
 * offering to continue later, to stop rating this sport, or to carry on. Every exit below
 * is a `replace`: walking back inside the run is one thing, and a route the player can be
 * dropped into the middle of is another.
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
  QuestionNavigator,
  Tag,
  theme,
} from '@/shared/ui';

import type { AnswerOption } from '../domain/Assessment';
import type { Sport } from '../domain/Sport';
import { positionOf } from '../domain/onboardingPass';
import { outstandingPosition, questionAt, standingPosition } from '../domain/questionNavigation';
import { useAbandonAssessment } from '../hooks/useAbandonAssessment';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAnswerQuestion } from '../hooks/useAnswerQuestion';
import { useAssessment } from '../hooks/useAssessment';
import { useDeferredRuns } from '../store/deferredRuns.store';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { LeaveAssessmentSheet } from './LeaveAssessmentSheet';
import { OnboardingChrome } from './OnboardingChrome';
import { difficultyTag } from './difficultyTag';
import { navigatorLabel } from './navigatorLabel';
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
  const defer = useDeferredRuns((state) => state.defer);

  const pass = useOnboardingPass((state) => state.pass);
  /**
   * Always present by the time this screen renders: the route admits nobody whose sport is
   * outside the running pass, and begins a pass of one sport when there is none — which is
   * the resumed run. `positionOf` still answers *nothing* for a sport it cannot place,
   * because that is the honest answer and it is the reason the route can turn those
   * players away rather than draw them an eyebrow claiming a position in no pass.
   */
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
   * Where the player is standing, and what is drawn there.
   *
   * **Both are read from the step, never remembered.** The served transcript is the run's
   * whole past on every read, so a run resumed after four answers stands at question five
   * — on this device, on a second one, or after a reinstall — and every one of those four
   * can be walked back to from a cache that already holds them. A client counting what it
   * had itself shown could only ever say "question 1".
   *
   * `movedTo` is where the player walked, and `undefined` is *not* a position: it means
   * they have not walked anywhere and follow the end of the run, which is what keeps them
   * on the question their last answer produced. It is never sent anywhere and never
   * recorded — moving is a local act, and this slice does not revise.
   */
  const [movedTo, setMovedTo] = useState<number>();
  const answered = step?.transcript.length ?? 0;
  const at = standingPosition(step, movedTo);
  const showing = questionAt(step, at);
  /** The recorded answer, on a question already answered. Absent on the outstanding one. */
  const recorded = showing?.answer;

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
   * Moving, and it is the whole of what this slice does with an answered question.
   *
   * **Neither costs a request.** The transcript arrived with the step, so walking back to
   * question two from question eight and forward again touches the network not at all —
   * which is what makes looking free, and what "revisable" has to mean before it can mean
   * anything else.
   *
   * Forward onto the outstanding question clears the pin rather than setting it to that
   * position: from there the player follows the end of the run again, so the next answer
   * does not leave them standing behind it.
   */
  const end = outstandingPosition(step);
  const goBack = at > 1 ? () => setMovedTo(at - 1) : undefined;
  const goForward = () => setMovedTo(at + 1 >= end ? undefined : at + 1);

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
          title={showing?.question.category ?? sportLabel(sport)}
          // Back through the run, never out of it — the way out is the close control on
          // the other side of the header, and the two must not be confused for each other.
          onBack={goBack}
          backLabel="Previous question"
          right={
            <CloseControl
              ref={closeControl}
              onPress={() => setConfirmingExit(true)}
              accessibilityLabel="Leave this rating"
              accessibilityHint="Offers continuing later or stopping this sport"
            />
          }
          progress={
            step === undefined ? undefined : (
              <QuestionNavigator
                answered={answered}
                outstanding={question !== undefined}
                at={at}
                accessibilityLabel={navigatorLabel(at, answered)}
              />
            )
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

          {showing !== undefined ? (
            <>
              <View style={s.meta}>
                <Text style={s.counter}>{`Question ${showing.position}`}</Text>
                <DifficultyTag tier={showing.question.tier} />
              </View>

              <Card>
                {/* The situation is a shaded header inside the same card as the question,
                    and the hairline is the fold between them — one object, two sections. */}
                <View style={s.situation}>
                  <Text style={s.situationEyebrow}>Picture this</Text>
                  <Text style={s.situationText}>{showing.question.situation}</Text>
                </View>

                <Hairline>
                  <Text style={s.question}>{showing.question.text}</Text>
                  <Text style={s.qualifier}>{showing.question.qualifier}</Text>
                </Hairline>
              </Card>

              {/* An answered question is shown as it was answered. Nothing here is
                  pressable: this slice moves over answers and does not change them, and a
                  selection that led nowhere would be a promise the screen cannot keep. */}
              {showing.question.options.map((option) =>
                recorded === undefined ? (
                  <AnswerCard
                    key={option.id}
                    option={option}
                    selected={option.id === selectedOptionId}
                    onPress={() =>
                      setChoice({ questionId: showing.question.id, optionId: option.id })
                    }
                  />
                ) : (
                  <RecordedAnswer key={option.id} option={option} chosen={option.id === recorded} />
                ),
              )}
            </>
          ) : null}
        </ScrollView>

        {showing !== undefined ? (
          <View style={s.action}>
            {/* A stale-step conflict never reaches here — it is recovered as a re-read, so
                a double-tapped confirm leaves the player on the correct question with
                nothing to dismiss. What is left is a genuine failure, and the retry is the
                confirm control itself, with the selection still made. */}
            {answer.error !== null && recorded === undefined ? (
              <Note variant="coral" accessibilityRole="alert">
                {onboardingErrorMessage(answer.error)}
              </Note>
            ) : null}

            {recorded === undefined ? (
              <Button
                label={CONFIRM_LABEL}
                size="lg"
                disabled={selectedOptionId === undefined}
                busy={answer.isPending}
                busyLabel="Submitting…"
                accessibilityHint="Submits this answer and moves the questionnaire on"
                onPress={submit}
              />
            ) : (
              // Forward over ground already covered. It sends nothing — the answer at the
              // next position is already in hand — so it is a move and never a second way
              // to submit.
              <Button
                label="Next question"
                size="lg"
                accessibilityHint="Returns towards the question you are being asked"
                onPress={goForward}
              />
            )}
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

/**
 * One option on a question the player has already answered.
 *
 * The alternatives are shown alongside the chosen one, because re-reading what you agreed
 * to means re-reading what you turned down — and the chosen one carries a **word**, not
 * only a border, for the same reason the live question's selection does.
 *
 * It is a card rather than a pressable card: nothing on an answered question can be
 * operated yet, and a control that looks operable and is not is worse than one that does
 * not look it.
 */
function RecordedAnswer({
  option,
  chosen,
}: {
  readonly option: AnswerOption;
  readonly chosen: boolean;
}) {
  return (
    <View accessible accessibilityLabel={chosen ? `${option.text}. Your answer.` : option.text}>
      <Card style={[s.answer, chosen ? s.chosen : undefined]}>
        <Text style={s.answerText}>{option.text}</Text>
        {chosen ? <Text style={s.selectedMark}>Your answer</Text> : null}
      </Card>
    </View>
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
  // The selected border a chosen answer carries on the live question, on a card that
  // cannot be pressed to acquire it. Selection is a state, not an action, so it is `ink`
  // — and the word beside it is what carries the state where the colour cannot.
  chosen: { borderColor: theme.color.ink },
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
