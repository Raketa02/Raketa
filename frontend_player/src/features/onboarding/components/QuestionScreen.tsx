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
 * 44pt minimum.
 *
 * **And they can change what they said.** Tapping a different option on an answered
 * question opens the change sheet, which names how many later answers the change discards
 * before it happens; tapping the option already recorded does nothing at all. Only two
 * acts on this screen cost a request — answering a new question, and changing an old
 * answer — and they are the same request, which is why a change lands on the same
 * mutation, with the same failure and the same retry in place.
 *
 * **The questionnaire stopping is not the rating existing.** When the engine has nothing
 * left to ask, the run sits in progress with every answer still revisable and the player
 * goes to the **review** — which is also where the review sends them back from, at whatever
 * question they want to change. So this screen is entered mid-run as readily as at the
 * start of one, and `at` is the only thing that ever says where.
 *
 * **Leaving is still not going back.** The close control in the header opens a confirm
 * offering to continue later, to stop rating this sport, or to carry on — the same one the
 * review offers, through the same hook, because reaching the end of the questionnaire must
 * not be the one place with no way out. Every exit below is a `replace`: walking back
 * inside the run is one thing, and a route the player can be dropped into the middle of is
 * another.
 *
 * **There is no live estimate.** The player sees no running Level at any point, which is
 * why the design system's `[3,17 so far]` chip is deliberately absent from the meta row.
 */

import { forwardRef, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { offlineMessage } from '@/shared/errors';
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
import type { Sport } from '@/shared/vocabulary/sport';
import { positionOf } from '../domain/onboardingPass';
import { outstandingPosition, questionAt, standingPosition } from '../domain/questionNavigation';
import { proposeRevision } from '../domain/revision';
import { runStanding } from '../domain/runStanding';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAnswerQuestion } from '../hooks/useAnswerQuestion';
import { useAssessment } from '../hooks/useAssessment';
import { useLeaveAssessment } from '../hooks/useLeaveAssessment';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { ChangeAnswerSheet, type AnswerChange } from './ChangeAnswerSheet';
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
  /**
   * Which question to open on, 1-based — what an entry on the review opens, and nothing
   * else sets it.
   *
   * **A starting point, not a position that is kept.** It seeds where the player stands and
   * every move after it is theirs; a run that has since grown or been truncated is clamped
   * to what still exists rather than refused, because the run is served fresh and the link
   * was made against an older one.
   */
  readonly at?: number;
}

export function QuestionScreen({ assessmentId, sport, at: openAt }: QuestionScreenProps) {
  const assessment = useAssessment(assessmentId);
  const answer = useAnswerQuestion(assessmentId);

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
  const { advance, showResultOf, showReviewOf } = onwards;
  /**
   * Leaving, in one place with the review's.
   *
   * Both screens offer the same way out and must offer it identically, and "identically" is
   * not a promise two copies can keep — this hook exists because *start the next sport and
   * go there* was written twice and had already drifted.
   */
  const leave = useLeaveAssessment(assessmentId, onwards);
  const step = assessment.data;
  const question = step?.question;
  /**
   * What the run is doing, in one reading shared with the review — see `runStanding`.
   *
   * **Three of the four readings are somewhere else's**, and none of them is "no question
   * left". That was the reading before abandonment, and then before the stop, and each time
   * it grew a case it could not tell apart: a player who abandoned padel elsewhere being
   * shown their padel rating, and then a player who had answered everything being shown a
   * result screen with no result on it.
   */
  const standing = runStanding(step);

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
   * recorded — moving is a local act, and only answering and changing are not.
   *
   * It is dropped after a change rather than adjusted, for the same reason: the transcript
   * is shorter than the one they walked into, and where they belong is wherever the engine
   * has just decided to ask them next.
   *
   * The review seeds it, which is the one thing that ever arrives from outside: opening an
   * entry is walking to that question, and it is the same walk from then on.
   */
  const [movedTo, setMovedTo] = useState<number | undefined>(openAt);
  const answered = step?.transcript.length ?? 0;
  const at = standingPosition(step, movedTo);
  const showing = questionAt(step, at);
  /** The recorded answer, on a question already answered. Absent on the outstanding one. */
  const recorded = showing?.answer;

  /**
   * The change being asked about, held until the player confirms it or keeps what they
   * had. It survives a failed request, which is the point: a revision that never reached
   * the server must not cost the player the option they had chosen.
   */
  const [proposed, setProposed] = useState<AnswerChange>();
  /**
   * Where focus returns when the change sheet closes.
   *
   * The answer they already gave, deliberately, rather than the option they tapped. The
   * tapped card is the one that may be about to stop being an option at all, and a player
   * who kept their answer is best returned to it — which is also why this ref stays
   * attached while the sheet closes, where one hung off the proposal would have emptied
   * in the same update.
   */
  const recordedAnswer = useRef<View | null>(null);

  /**
   * When this screen is not where the player belongs.
   *
   * One effect and one latch, because the three are alternatives: a run that finishes while
   * an abandonment is departing must not navigate twice.
   *
   * - **stopped** — the questionnaire has nothing left to ask, and the review is the last
   *   look before the rating exists. Gated on there being nothing here to show, which is
   *   what lets the review send a player *back* into a stopped run to change an answer:
   *   standing on question three of a run that has stopped, they are exactly where they
   *   asked to be, and walking off the end of it is what brings them back.
   * - **rated** — a rating exists, so the result screen has something to show. Reached from
   *   here only when the run was completed elsewhere; this device completes from the review.
   * - **ended** — abandoned elsewhere. Nothing to show and nothing to say, so the flow moves
   *   on exactly as an abandonment from this screen would.
   */
  useEffect(() => {
    if (standing === 'stopped' && showing === undefined) showReviewOf(assessmentId);
    else if (standing === 'rated') showResultOf(assessmentId);
    else if (standing === 'ended') advance();
  }, [standing, showing, assessmentId, showReviewOf, showResultOf, advance]);

  /**
   * One press's worth of consequence per press, on either control.
   *
   * `answer.isPending` cannot do this: it reaches a *later* render, and the second tap of
   * a double tap arrives before that render exists — so the busy control a player sees is
   * the state after the burst, not during it. A ref is read at the moment of the press,
   * which is when the question is being asked. It is the latch `useAdvanceThroughPass`
   * uses, for the same reason and released the same way: `onSettled`, so a failure leaves
   * the retry available.
   *
   * The server would survive the burst either way — a repeated answer names a question no
   * longer outstanding, and a repeated change names an option it already holds, so both
   * record nothing. That is a reason not to *panic* about it, not a reason to send three
   * writes and let the recovery paths sort out which of them was the player's.
   */
  const sending = useRef(false);

  const send = (questionId: string, optionId: string, onSuccess?: () => void) => {
    if (sending.current) return;
    sending.current = true;
    answer.mutate(
      { questionId, optionId },
      {
        onSuccess,
        onSettled: () => {
          sending.current = false;
        },
      },
    );
  };

  const submit = () => {
    if (question === undefined || selectedOptionId === undefined) return;
    send(question.id, selectedOptionId);
  };

  /**
   * Tapping an option on a question already answered.
   *
   * **It asks; it does not change.** What a change costs is knowable from the transcript
   * already in hand, so it is put in front of the player before anything is sent — and
   * `proposeRevision` is where "this is not a change at all" is decided, so re-selecting
   * the answer already recorded reaches nothing and shows nothing.
   */
  const askToChange = (option: AnswerOption) => {
    const revision = proposeRevision(step, at, option.id);
    if (revision === undefined) return;

    // A failure from an earlier change belongs to that change. Left standing, it would
    // greet the next one as though it had already failed.
    answer.reset();
    setProposed({ revision, answerText: option.text });
  };

  /**
   * Keeping the answer they have — the button, the scrim, the sheet's close control and
   * the Android back gesture, which are one act and so are one function.
   *
   * **Not while a change is in the air.** The request that discards their later answers is
   * already running; dismissing the sheet over it would leave the player watching a screen
   * that says nothing is happening, and resetting a mutation mid-flight drops the
   * callbacks this screen unlatches itself in. The sheet closes when the change lands.
   */
  const keepAnswer = () => {
    if (sending.current) return;
    setProposed(undefined);
    answer.reset();
  };

  /**
   * The change itself — the same mutation an answer uses, because it is the same request.
   *
   * On success the pin is dropped rather than moved: the transcript is now shorter than
   * the one they were standing in, and following the end of the run is what puts them on
   * the question the engine has just chosen from what they actually said. A failure
   * leaves everything where it is, sheet included, with the retry beside the message.
   */
  const change = () => {
    if (proposed === undefined) return;
    send(proposed.revision.questionId, proposed.revision.optionId, () => {
      setProposed(undefined);
      setMovedTo(undefined);
    });
  };

  /**
   * Moving — which is looking, and is not changing.
   *
   * **Neither costs a request.** The transcript arrived with the step, so walking back to
   * question two from question eight and forward again touches the network not at all —
   * which is what makes looking free, and what has to be true before "you can change your
   * mind" can be worth anything. A change is the one act here that spends a round trip.
   *
   * Forward onto the outstanding question clears the pin rather than setting it to that
   * position: from there the player follows the end of the run again, so the next answer
   * does not leave them standing behind it.
   */
  const end = outstandingPosition(step);
  const goBack = at > 1 ? () => setMovedTo(at - 1) : undefined;
  const goForward = () => setMovedTo(at + 1 >= end ? undefined : at + 1);
  /**
   * Where forward leads from the last answer of a **stopped** run: the review, because
   * there is no question past it.
   *
   * The control is the same move — one step towards the end of the run — but a player is
   * owed the name of the screen they are about to be on, and `Next question` on the last
   * answer of a run with no more questions is the one place this screen could promise
   * something that does not exist.
   */
  const forwardIsReview = question === undefined && at + 1 >= end;

  return (
    <>
      <SafeAreaView
        style={s.screen}
        edges={['top', 'bottom']}
        // A sheet is a real modal: while it is open nothing behind it is reachable by a
        // screen reader. Both sheets are siblings below, never children — inside here one
        // would hide itself along with the question.
        {...behindOverlay(leave.confirming || proposed !== undefined)}
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
              ref={leave.returnFocusTo}
              onPress={leave.ask}
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
              {offlineMessage('resumes')} Your answers so far are safe on the server.
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

              {/* One list, on every question. An answered one shows the option recorded
                  as selected and the alternatives beside it — re-reading what you agreed
                  to means re-reading what you turned down — and a press on an alternative
                  asks about a change rather than making one. */}
              {showing.question.options.map((option) => {
                const chosen = option.id === recorded;
                return (
                  <AnswerCard
                    key={option.id}
                    ref={chosen ? recordedAnswer : undefined}
                    option={option}
                    answered={recorded !== undefined}
                    selected={recorded === undefined ? option.id === selectedOptionId : chosen}
                    onPress={() =>
                      recorded === undefined
                        ? setChoice({ questionId: showing.question.id, optionId: option.id })
                        : askToChange(option)
                    }
                  />
                );
              })}
            </>
          ) : null}
        </ScrollView>

        {showing !== undefined ? (
          <View style={s.action}>
            {/* A stale-step conflict never reaches here — it is recovered as a re-read, so
                a double-tapped confirm leaves the player on the correct question with
                nothing to dismiss. What is left is a genuine failure, and the retry is the
                confirm control itself, with the selection still made.

                Only on the live question: the same mutation carries a change, and a
                change's failure belongs in the sheet the player is looking at, beside the
                control that retries it. */}
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
                label={forwardIsReview ? 'Back to your answers' : 'Next question'}
                size="lg"
                accessibilityHint={
                  forwardIsReview
                    ? 'Returns to the list of your answers'
                    : 'Returns towards the question you are being asked'
                }
                onPress={goForward}
              />
            )}
          </View>
        ) : null}
      </SafeAreaView>

      <ChangeAnswerSheet
        change={proposed}
        onChange={change}
        onKeep={keepAnswer}
        changing={answer.isPending}
        error={answer.error}
        returnFocusTo={recordedAnswer}
      />

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
  /** Whether this question is already answered, which is what a press here means. */
  readonly answered: boolean;
  readonly onPress: () => void;
}

/**
 * One answer, on a question being asked or on one already answered.
 *
 * **One component, because it is one thing to a player.** The card looks the same, is
 * reached the same way, and carries its state the same way; what differs is the word
 * beside the border and what a press leads to. Two components would be two answers to
 * "what does tapping an answer do", which is the mental model this screen has exactly one
 * of.
 *
 * **Selection is announced as state** rather than drawn only as a border — a state that
 * exists only as a colour excludes whoever cannot see that colour, which is why the word
 * is there too, and why the recorded answer says so in its name.
 *
 * The hint says what pressing does, and it is honest in all three cases: on a live
 * question pressing selects and never submits; on an answered one it offers a change; and
 * on the answer already recorded it does nothing at all, so there is nothing to promise.
 */
const AnswerCard = forwardRef<View, AnswerCardProps>(function AnswerCard(
  { option, selected, answered, onPress },
  ref,
) {
  return (
    <PressableCard
      ref={ref}
      onPress={onPress}
      selected={selected}
      accessibilityLabel={answered && selected ? `${option.text}. Your answer.` : option.text}
      accessibilityHint={answerHint(answered, selected)}
      style={s.answer}
    >
      <Text style={s.answerText}>{option.text}</Text>
      {selected ? (
        <Text style={s.selectedMark}>{answered ? 'Your answer' : 'Selected'}</Text>
      ) : null}
    </PressableCard>
  );
});

function answerHint(answered: boolean, selected: boolean): string | undefined {
  if (!answered) return 'Selects this answer';
  return selected ? undefined : 'Offers changing your answer to this one';
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
