/**
 * The done screen: everything this onboarding pass produced, in one place, and what it is
 * worth.
 *
 * **The cards are what the player just walked through, not what they are rated at.** The
 * two differ for anyone who arrived here with a rating already — a resumed tennis run
 * belonging to a player rated at padel — and this screen answers the first question. The
 * runs are the pass's, which is the concept that records them; every number in a card is
 * Query's, read back through the key the result screen filled.
 *
 * **The sentence under the cards is the point of the screen.** A player who leaves
 * believing their Level is a judgement has been mis-served by it: these are hypotheses,
 * they are made to be tested, and real matches are what narrow them.
 *
 * **Where Confidence stopped, and why, is two different sentences.** Everyone leaves at or
 * below the ceiling, but a rating held *by* the ceiling and one held by its own evidence
 * are not the same rating, and telling a player who reached the ceiling that their answers
 * left something unsettled would be a small lie about them. The rule is
 * `domain/confidenceLimit`, which reads the engine's number rather than repeating its
 * arithmetic.
 *
 * Every figure is drawn in a mono, tabular role. That is not decoration here: several
 * ratings sit one under another, and a column of levels that shifts as its digits change
 * is the exact thing tabular figures exist to stop.
 */

import { useRouter } from 'expo-router';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, Card, Hairline, Note, Row, theme } from '@/shared/ui';

import { confidenceLimit, type ConfidenceLimit } from '../domain/confidenceLimit';
import type { RatedRun } from '../domain/onboardingPass';
import { useRunResults, type RunResult } from '../hooks/useRunResults';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { OnboardingChrome } from './OnboardingChrome';
import { ratingStatusLabel } from './bandPresentation';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { formatConfidence, formatLevel, formatRange } from './ratingFormat';
import { sportColour, sportLabel } from './sportPresentation';

/**
 * One reference, module-level, for the no-pass answer.
 *
 * A selector that built a fresh `[]` each call would return a new identity every time the
 * store notified, and the screen would re-render itself forever.
 */
const NOTHING_RATED: readonly RatedRun[] = [];

/**
 * The two ways a Confidence can be where it is, said as two different sentences.
 *
 * Client copy, like the band meanings and unlike the evidence trail: the wire carries the
 * two numbers and the engine's own reason for them, and this is the app explaining what the
 * comparison between them means.
 *
 * The ceiling is the engine's, so each sentence takes it rather than closing over a copy —
 * a retune moves the number in the sentence with no release involved. A rating that arrives
 * without one gets **no sentence at all**; see `RatingCard`.
 */
const CONFIDENCE_LIMIT_NOTE: Readonly<Record<ConfidenceLimit, (ceiling: number) => string>> = {
  ceiling: (ceiling) =>
    `This reached the ${ceiling}% a questionnaire can prove. Nothing you answered held it back — only playing can raise it.`,
  evidence: (ceiling) =>
    `This sits below the ${ceiling}% a questionnaire can prove, because your answers left more to settle rather than because of the ceiling.`,
};

export function DoneScreen() {
  const router = useRouter();
  // Empty with no pass running, which is the same as a pass that rated nothing: this
  // screen accounts for *this* walk, and there is nothing to account for. Reachable only
  // by deep link — the flow arrives here through the pass that produced the cards.
  const rated = useOnboardingPass((state) => state.pass?.rated ?? NOTHING_RATED);
  const results = useRunResults(rated);

  // Which engine produced these, said out loud, because the data screen claims it is kept
  // and a claim the player can check is worth more than one they cannot. Deduplicated:
  // two sports rated a minute apart were rated by the same engine, and saying so twice
  // reads as two facts.
  const engines = [
    ...new Set(
      results
        .map((entry) => entry.query.data?.result?.engineVersion)
        .filter((version): version is string => version !== undefined),
    ),
  ];

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      {/* No progress bar. The bar measures which sport is being rated, and none is —
          claiming a full bar for a player who stopped after the first of two would be the
          one dishonest thing this screen could say about the run. */}
      <OnboardingChrome eyebrow="Raketa" title="Your starting ratings" />

      <ScrollView contentContainerStyle={s.content}>
        {rated.length === 0 ? (
          <Note variant="amber">
            There are no ratings from this session to show. You can rate any sport whenever you
            like.
          </Note>
        ) : null}

        {results.map((entry) => (
          <RatingCard key={entry.run.assessmentId} entry={entry} />
        ))}

        <Note variant="info" title="These are hypotheses, not verdicts">
          Every rating here is a starting estimate, made to be tested. Real matches are what narrow
          the range — and they can move a Level in either direction. Nothing here is a judgement
          about you.
        </Note>

        {engines.length > 0 ? (
          <Text style={s.footnote}>{`Produced by rating engine ${engines.join(', ')}`}</Text>
        ) : null}
      </ScrollView>

      <View style={s.action}>
        <Button
          label="Continue"
          size="lg"
          onPress={() => router.replace('/notifications')}
          accessibilityHint="Explains being told when a seat opens up"
        />
      </View>
    </SafeAreaView>
  );
}

interface RatingCardProps {
  readonly entry: RunResult;
}

/**
 * One sport's rating.
 *
 * The sport's identity colour is the left rail — the same 3pt rail the note and the band
 * card use — and the sport's **name** sits beside it, because a rail is not readable and a
 * colour is never the only carrier of anything.
 *
 * Every row is one accessibility element and names its sport, so a screen reader moving
 * down a screen of several cards never reads a bare "Level, 2,71" with no idea whose.
 */
function RatingCard({ entry: { run, query } }: RatingCardProps) {
  const sport = sportLabel(run.sport);
  const result = query.data?.result;
  const ceiling = result?.confidenceCeiling;

  return (
    <Card style={[s.card, { borderLeftColor: sportColour(run.sport) }]}>
      <Text style={s.sport}>{sport}</Text>

      {query.isPending ? (
        <ActivityIndicator
          accessibilityLabel={`Loading your ${sport} rating`}
          color={theme.color.muted}
        />
      ) : null}

      {query.error !== null ? (
        <View style={s.failure}>
          <Note variant="coral" accessibilityRole="alert">
            {onboardingErrorMessage(query.error)}
          </Note>
          <Button
            label="Try again"
            variant="secondary"
            size="sm"
            accessibilityLabel={`Try loading your ${sport} rating again`}
            onPress={() => void query.refetch()}
          />
        </View>
      ) : null}

      {query.isSuccess && result === undefined ? (
        <Note variant="amber">
          This assessment has no rating to show. You can rate {sport} again whenever you like.
        </Note>
      ) : null}

      {result !== undefined ? (
        <>
          <Hairline>
            <Row
              label="Level"
              value={<Figure>{formatLevel(result.level)}</Figure>}
              accessibilityLabel={`${sport} level: ${formatLevel(result.level)}`}
            />
            <Row
              divided
              label="Likely range"
              value={<Figure>{formatRange(result.range)}</Figure>}
              accessibilityLabel={`${sport} likely range: ${formatRange(result.range)}`}
            />
            <Row
              divided
              label="Confidence"
              value={<Figure>{formatConfidence(result.confidence)}</Figure>}
              accessibilityLabel={`${sport} confidence: ${formatConfidence(result.confidence)}`}
            />
            <Row
              divided
              label="Rating status"
              value={ratingStatusLabel(result.status)}
              accessibilityLabel={`${sport} rating status: ${ratingStatusLabel(result.status)}`}
            />
          </Hairline>

          {/* No ceiling served means the engine that produced this rating has been retired,
              so there is nothing to have held it *against* and the card says nothing about
              one — the same shape the result screen has for a missing confidence sentence.
              A fallback here would be the app's own number presented as the engine's. */}
          {ceiling !== undefined ? (
            <Text style={s.limit}>
              {CONFIDENCE_LIMIT_NOTE[confidenceLimit(result.confidence, ceiling)](ceiling)}
            </Text>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}

/** A figure in a row: mono and tabular, so the column of them lines up between cards. */
function Figure({ children }: { readonly children: string }) {
  return <Text style={s.figure}>{children}</Text>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  // 3pt, as the note's semantic rail and the result screen's band card are: the same
  // object doing the same job, here carrying the sport's identity rather than a meaning.
  card: { borderLeftWidth: 3 },
  sport: { ...theme.type.h2, color: theme.color.ink },
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  limit: { ...theme.type.tiny, color: theme.color.muted, marginTop: theme.space.sm },
  failure: { gap: theme.space.sm, marginTop: theme.space.sm },
  footnote: { ...theme.type.tiny, color: theme.color.muted },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
