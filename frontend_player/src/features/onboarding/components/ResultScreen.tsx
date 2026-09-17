/**
 * The result screen: one sport's Skill rating, and the reasoning behind it.
 *
 * **A rating is never only a number.** The screen leads with the Level, but shows it inside
 * its likely range, with its Confidence and its Band — two players both showing 3,0 at very
 * different Uncertainties are not the same player, and nothing here may imply they are.
 *
 * **The evidence trail is the point of the screen** and lives in its own component. So does
 * the verdict above it — `Verdict`, the dark card with the Level, the range, the ring, the
 * bar and the three information marks — because the Skill passport draws the same card once
 * per rating ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What this screen owns is what is the run's alone: the *Questions asked* row it hands
 * the card, the band card under it, the notes, the trail, and where the flow goes next.
 *
 * ## The rules that are easy to break here
 *
 * - **Band boundaries come from the response.** They are deliberately uneven, they were
 *   wrong once already, and this client restates them nowhere. The band card prints the edges
 *   it was sent.
 * - **Nothing on this screen decides anything about the rating.** Every label and every
 *   figure on the verdict and in the trail is the server's, directions are the engine's,
 *   and the client renders them in the order it was given them.
 * - **The note under the verdict is the app's own, and it is the one sentence here that is.**
 *   It used to be the engine's `confidenceReason`, which explained *why this Confidence and
 *   not another* — a true sentence answering a question a player meeting their first rating
 *   is not asking. What they need said, in words, is that the number is provisional and that
 *   matches are what settle it. That is a product claim about how Raketa works, so it is
 *   client copy, and it is shown for every rating rather than only when the engine happened
 *   to send a reason.
 *
 * The popovers are rendered as **siblings** of the screen root, never inside it: the root
 * spreads `behindOverlay` while one is open, and an overlay inside that element would hide
 * itself along with everything else.
 *
 * ## Where the flow goes from here
 *
 * **Rate the next sport they chose, or stop.** Stopping part-way is an ordinary outcome
 * rather than an abandonment: the player leaves with the ratings they produced and goes
 * into the app, and a sport not rated today can be rated any time later. Which sport is
 * next is the pass's to answer, and with nothing after this one there is nothing to
 * offer — so the screen shows one control instead of pretending there is a choice.
 *
 * Either way the summary comes first: the done screen is where a run is accounted for, and
 * a player who stopped after one rating is owed that account as much as one who finished.
 * **That is now true of every player**, including one who still owes a Player profile — the
 * six social steps used to sit between the last rating and the screen that shows it, and
 * they now sit on the far side of it.
 *
 * **None of that is decided here.** `useAdvanceThroughPass` owns the whole transition and
 * the question screen calls the same hook, so the two screens cannot answer differently
 * again — which they did, over what a failed start does.
 */

import { useEffect } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { behindOverlay, Button, Card, Note, theme } from '@/shared/ui';

import type { AssessmentResult } from '../domain/AssessmentResult';
import type { Sport } from '@/shared/vocabulary/sport';
import { positionOf } from '../domain/onboardingPass';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAssessment } from '../hooks/useAssessment';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { EvidenceTrail } from './EvidenceTrail';
import { OnboardingChrome } from './OnboardingChrome';
import { useHardwareBack } from '@/shared/lib/platform';
import { bandPresentation } from './bandPresentation';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { passEyebrow } from './passEyebrow';
import { formatRange } from '@/shared/formatting/ratingFormat';
import { sportLabel } from './sportPresentation';
import { Verdict, VerdictPopover, useVerdictExplainer } from './Verdict';

/** Raised when the run ended on evidence the questionnaire could not settle. */
const CALIBRATION_ELEVATED = 'elevated';

/**
 * What the last sport leads to, as the control that leads there.
 *
 * **One label, because there is now one destination.** The end of the queue is the end of
 * the first part for everybody: the summary of what this walk produced. Whether six more
 * steps follow it is the done screen's question, so this screen no longer needs to know —
 * and no longer says *Finish setting up* to a player who is about to be shown their
 * ratings.
 */
const SEE_YOUR_RATINGS = 'See your ratings';

export interface ResultScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function ResultScreen({ assessmentId, sport }: ResultScreenProps) {
  const assessment = useAssessment(assessmentId);
  const pass = useOnboardingPass((state) => state.pass);
  const position = positionOf(pass, sport);
  /**
   * **The device's back is claimed and refused, because this screen draws none.**
   *
   * Every screen in onboarding is reached by `replace`, so the group holds one entry per push
   * — and the push behind this one is the welcome screen, from which the only way forward is
   * to rate a sport again. An unclaimed press popped to exactly there.
   * [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back and
   * forward move freely inside each part and never cross between them."* A press that does
   * nothing is what the missing back control has already said.
   */
  useHardwareBack(() => {});

  /**
   * Leaving this sport, in one place — the same hook the question screen calls.
   *
   * This screen used to hold its own copy of the move and had **no error branch at all**,
   * so a failed "rate the next sport" did nothing visible: no message, no retry, nothing
   * to tell the player the tap had been heard. The hook owns the latch and the failure,
   * and the destination below is only ever read to *label* a control.
   */
  const onwards = useAdvanceThroughPass(sport);
  const next = onwards.destination.kind === 'rate' ? onwards.destination.sport : undefined;
  const recordRun = useOnboardingPass((state) => state.record);

  const result = assessment.data?.result;

  // Which mark the popover is open on, if any. The card holds the refs and hands the pressed
  // one up, so the popover anchors to the mark it was opened from and returns focus to it.
  const explainer = useVerdictExplainer(result?.confidenceCeiling);

  /**
   * A rating exists for this sport, so this run belongs on the summary.
   *
   * Recorded **where the rating is shown** rather than where the run finished: what the
   * done screen lists is what the player was told, and a run whose result could not be
   * read is not something to promise them a card for. Recording the same run twice is a
   * no-op, which is what makes a refetch or a remount free.
   */
  useEffect(() => {
    if (result === undefined) return;
    recordRun({ assessmentId, sport });
  }, [result, recordRun, assessmentId, sport]);

  return (
    <>
      <SafeAreaView
        style={s.screen}
        edges={['top', 'bottom']}
        // A popover is a real overlay: while one is open nothing behind it is reachable by
        // a screen reader. The popover is a sibling below, never a child.
        {...behindOverlay(explainer.open)}
      >
        {/* The eyebrow carries which sport of how many, and nothing else does: the bar
            that used to repeat it under the header measured sports, and sports are no
            longer what onboarding's progress indicator measures (ADR-0020). */}
        <OnboardingChrome eyebrow={passEyebrow(sport, position)} title="Your rating" />

        <ScrollView contentContainerStyle={s.content}>
          {assessment.isPending ? (
            <ActivityIndicator accessibilityLabel="Loading your rating" color={theme.color.muted} />
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

          {/* A finished run carries a rating. A run that ended some other way does not, and
              saying so is better than a screen that stays empty without explaining why. */}
          {assessment.isSuccess && result === undefined ? (
            <Note variant="amber">
              This assessment has no rating to show. It was either stopped or is still unfinished —
              you can rate {sportLabel(sport)} again whenever you like.
            </Note>
          ) : null}

          {result !== undefined ? (
            <>
              <Verdict
                rating={result}
                questionsAsked={result.questionsAsked}
                onExplain={explainer.explain}
              />
              <BandCard result={result} />
            </>
          ) : null}

          {result !== undefined ? (
            <Note variant="info" title="This is a starting point, not a verdict">
              {`We worked this out from a handful of questions, so think of it as our best guess at ` +
                `where you sit. We won't be sure until you have played a few matches — that is what ` +
                `tells us whether we got you right, and it is what tightens the range. Play, and this ` +
                `settles itself.`}
            </Note>
          ) : null}

          {result !== undefined && result.calibrationPriority === CALIBRATION_ELEVATED ? (
            <Note variant="base" title="We will want matches sooner">
              Your answers left something unsettled, so this estimate is queued for real matches to
              confirm. It changes who you are matched with, never where you sit.
            </Note>
          ) : null}

          {result !== undefined ? (
            <EvidenceTrail contributions={result.contributions} level={result.level} />
          ) : null}
        </ScrollView>

        <View style={s.action}>
          {/* Starting the next sport is the only thing this screen can fail at, and a
              failed start changed nothing — so the retry is the control that failed, with
              the reason above it. The same note the question screen uses, because it is
              the same failure; until the advance rule was shared this branch was missing
              here entirely and a failed tap was silently ignored. */}
          {onwards.error !== null ? (
            <Note variant="coral" accessibilityRole="alert">
              {onboardingErrorMessage(onwards.error)}
            </Note>
          ) : null}

          {next === undefined ? (
            // The last sport, and the label names what is actually next: the summary of
            // this walk. It is the same screen whether or not the player still owes a
            // Player profile — the done screen asks that, one press further on.
            <Button label={SEE_YOUR_RATINGS} size="lg" onPress={onwards.advance} />
          ) : (
            <>
              <Button
                label={`Rate ${sportLabel(next)}`}
                size="lg"
                busy={onwards.advancing}
                busyLabel="Starting…"
                accessibilityHint={`Starts the ${sportLabel(next)} questions`}
                onPress={onwards.advance}
              />
              <Button
                label="Done for now"
                variant="secondary"
                size="lg"
                accessibilityHint={`Keeps the ratings you have and skips ${sportLabel(next)}`}
                onPress={onwards.stopHere}
              />
            </>
          )}
        </View>
      </SafeAreaView>

      <VerdictPopover {...explainer.popover} />
    </>
  );
}

/**
 * The band card under the verdict — the band's own ink on the left rail, the only place a
 * band colour appears outside the bar.
 *
 * The edges printed here are the response's, never the bar's drawing values, and a band this
 * build cannot name still shows its name and its numbers. It is the run's and not the card's:
 * the passport draws the ladder under its cards instead, where every band is named once.
 */
function BandCard({ result }: { readonly result: AssessmentResult }) {
  const band = bandPresentation(result.band.name);

  return (
    <Card
      style={[
        s.bandCard,
        band === undefined ? undefined : { borderLeftColor: theme.band[band.key].ink },
      ]}
    >
      <Text style={s.bandName}>{result.band.name}</Text>
      <Text style={s.bandEdges}>
        {`Levels ${formatRange({ low: result.band.lower, high: result.band.upper })}`}
      </Text>
      {band === undefined ? null : <Text style={s.bandMeaning}>{band.meaning}</Text>}
    </Card>
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
  // 3pt, as the note's semantic rail is: this is the same object doing the same job.
  bandCard: { borderLeftWidth: 3 },
  bandName: { ...theme.type.cardTitle, color: theme.color.ink },
  bandEdges: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  bandMeaning: { ...theme.type.tiny, color: theme.color.ink, marginTop: theme.space.xxs },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
