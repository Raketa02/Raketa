/**
 * The question route.
 *
 * **This slice ends here.** It fetches the outstanding question and renders the two parts
 * of the reading order that the flow needs to be demonstrably complete — the category as
 * the screen heading, and the question itself. The situation header, the difficulty tag,
 * the answer options, the confirm control and the whole submit loop are the adaptive
 * question loop (#24), which extends this screen rather than replacing it.
 *
 * The category is the heading and **the question is never the page title**, because a
 * title is read last on a screen the eye scans top-down.
 *
 * There is no back control. An answer's numeric meaning depends on the difficulty tier it
 * was asked at, and that tier was chosen from the estimate as it stood — so revising an
 * earlier answer would silently change what every later answer meant (ADR-0017).
 */

import { useRouter } from "expo-router";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button, Card, Note, theme } from "@/shared/ui";

import type { Sport } from "../domain/Sport";
import { ratingPosition } from "../domain/sportQueue";
import { useAssessment } from "../hooks/useAssessment";
import { useSportQueue } from "../store/sportQueue.store";

import { OnboardingChrome } from "./OnboardingChrome";
import { onboardingErrorMessage } from "./onboardingErrorMessage";
import { sportLabel } from "./sportPresentation";

export interface QuestionScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function QuestionScreen({ assessmentId, sport }: QuestionScreenProps) {
  const router = useRouter();
  const assessment = useAssessment(assessmentId);
  const queue = useSportQueue((state) => state.queue);

  const position = ratingPosition(queue, sport);
  const question = assessment.data?.question;

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
          <Card>
            <Text style={s.question}>{question.text}</Text>
            <Text style={s.qualifier}>{question.qualifier}</Text>
          </Card>
        ) : null}

        {/* Nothing outstanding: the run finished elsewhere — a second device, or a
            questionnaire completed since the gate read it. The result screen (#25) takes
            this branch over and routes to the rating instead of offering the way out. */}
        {assessment.isSuccess && question === undefined ? (
          <View style={s.failure}>
            <Note variant="mint">This rating is already finished.</Note>
            <Button label="Go to Rakieta" variant="secondary" onPress={() => router.replace("/")} />
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
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
  question: { ...theme.type.question, color: theme.color.ink },
  qualifier: { ...theme.type.tiny, color: theme.color.muted },
});
