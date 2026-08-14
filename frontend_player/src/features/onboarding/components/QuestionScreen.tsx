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
 * **There is no live estimate.** The player sees no running Level at any point, which is
 * why the design system's `[3,17 so far]` chip is deliberately absent from the meta row.
 */

import { useRouter } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button, Card, Hairline, Note, PressableCard, Tag, theme } from "@/shared/ui";

import type { AnswerOption, Question } from "../domain/Assessment";
import type { Sport } from "../domain/Sport";
import { ratingPosition } from "../domain/sportQueue";
import { useAnswerQuestion } from "../hooks/useAnswerQuestion";
import { useAssessment } from "../hooks/useAssessment";
import { useSportQueue } from "../store/sportQueue.store";

import { OnboardingChrome } from "./OnboardingChrome";
import { difficultyTag } from "./difficultyTag";
import { onboardingErrorMessage } from "./onboardingErrorMessage";
import { sportLabel } from "./sportPresentation";

/** Identical on every question. See the note above — this is a domain rule, not copy. */
const CONFIRM_LABEL = "Confirm answer";

export interface QuestionScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function QuestionScreen({ assessmentId, sport }: QuestionScreenProps) {
  const router = useRouter();
  const assessment = useAssessment(assessmentId);
  const answer = useAnswerQuestion(assessmentId);
  const queue = useSportQueue((state) => state.queue);

  const position = ratingPosition(queue, sport);
  const question = assessment.data?.question;
  const finished = assessment.isSuccess && question === undefined;

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
    question !== undefined && choice?.questionId === question.id
      ? choice.optionId
      : undefined;

  const number = useQuestionNumber(question);

  // The run is over: the outstanding question is gone and a rating exists. `replace`,
  // because the questionnaire has no way back — this is the one exit from the loop.
  useEffect(() => {
    if (!finished) return;
    router.replace({
      pathname: "/result/[assessmentId]",
      params: { assessmentId, sport },
    });
  }, [finished, router, assessmentId, sport]);

  const submit = () => {
    if (question === undefined || selectedOptionId === undefined) return;
    answer.mutate({ questionId: question.id, optionId: selectedOptionId });
  };

  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <OnboardingChrome
        eyebrow={`${sportLabel(sport)} · Rating ${position.index} of ${position.total}`}
        title={question?.category ?? sportLabel(sport)}
        position={position}
      />

      <ScrollView contentContainerStyle={s.content}>
        {/* Paused, not loading — see the picker: an offline query is held, not failed. */}
        {assessment.fetchStatus === "paused" ? (
          <Note variant="amber">
            You&apos;re offline. Your question will load as soon as you&apos;re back, and
            your answers so far are safe on the server.
          </Note>
        ) : null}

        {assessment.isPending && assessment.fetchStatus !== "paused" ? (
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
                onPress={() =>
                  setChoice({ questionId: question.id, optionId: option.id })
                }
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
  );
}

/**
 * Which question this is, counted from the ones this run has actually shown.
 *
 * **A resumed run restarts the count**, and that is a real limitation rather than a
 * choice: `AssessmentStepResponse` carries `questions_asked` only once the run is
 * finished, so while it is in progress the server never tells the client how many answers
 * are already behind it. Counting on the device is the honest half — it measures movement,
 * which is what the counter is for, and it is never a fraction, so it cannot imply a
 * length the flow does not have. The fix is a field on the in-progress step; it is filed
 * as a backend follow-up, because a client that remembered its own count would be
 * inventing history the moment the player switched devices.
 *
 * Counting *ids seen* rather than incrementing on submit is what keeps a recovered
 * duplicate submission from advancing the number twice.
 */
function useQuestionNumber(question: Question | undefined): number {
  const seen = useRef<string[]>([]);

  if (question !== undefined && !seen.current.includes(question.id)) {
    seen.current.push(question.id);
  }

  return question === undefined ? 0 : seen.current.indexOf(question.id) + 1;
}

/** Absent where the engine supplies no tier — the opening and layoff questions have none. */
function DifficultyTag({ tier }: { readonly tier: string | undefined }) {
  if (tier === undefined) return null;

  const tag = difficultyTag(tier);
  return (
    <Tag
      label={tag.label}
      variant={tag.variant}
      accessibilityLabel={`Difficulty: ${tag.label}`}
    />
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
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: theme.space.sm,
  },
  counter: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: "uppercase" },
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
    textTransform: "uppercase",
  },
  situationText: { ...theme.type.tiny, color: theme.color.ink },
  question: { ...theme.type.question, color: theme.color.ink },
  qualifier: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.xxs },
  answer: { flexDirection: "row", alignItems: "center", gap: theme.space.sm },
  answerText: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  selectedMark: {
    ...theme.type.eyebrow,
    color: theme.color.ink,
    textTransform: "uppercase",
  },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
