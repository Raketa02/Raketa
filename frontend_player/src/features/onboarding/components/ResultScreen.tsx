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
 * ## The guide, on the first one a phone shows an account
 *
 * **The first _Your rating_ this phone shows an account runs a guide over the verdict's three
 * figures** — the level, the likely range, the confidence, one at a time in the ⓘ marks' own
 * words ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8,
 * `useRatingGuide`). Whatever the pass's origin, and once: *Got it*, *Skip* and the device's back
 * all end it, and the phone remembers it for that account, past sign-out. It is the third overlay here and a sibling like the
 * popover; **while it is up the root takes no touches**, so nothing beneath answers even where
 * the stage would let a touch through. The marks and their popover are unchanged.
 *
 * **The safe area is padding from the provider, never the native `SafeAreaView`.** The guide
 * measures the figures on the frame it opens on, which can be this screen's first; the native
 * view has no inset on that frame and moves the whole screen down by it on the next
 * (`TopSafeArea` says why), so the hole was cut a status bar above the level — an undimmed patch
 * of paper over the card, and the bubble over the number it explains.
 *
 * ## Where the flow goes from here
 *
 * **Rate the next sport they chose, or stop.** Stopping part-way is an ordinary outcome
 * rather than an abandonment: the player leaves with the ratings they produced and goes
 * back where the pass began, and a sport not rated today can be rated any time later. Which
 * sport is next is the pass's to answer, and with nothing after this one there is nothing to
 * offer — so the screen shows one control instead of pretending there is a choice. *Your
 * starting ratings*, the summary this used to lead to, repeated this screen and went with
 * [#730](https://github.com/Raketa02/Raketa/issues/730).
 *
 * **A pass begun at the Skill passport** ends there, its one control *See your ratings*,
 * because the passport *is* your ratings
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3), with the new card drawn. **A pass begun at Home** says *Back to Home*. This screen does
 * not know which it is showing — the card, the note, the trail and the ceiling tick are the
 * result's own either way. The new rating's Play intent is undeclared until the player
 * declares it, as every sport's is; nothing here asks — the deck does, on Games.
 *
 * **A pass begun on a group goes back to it**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §3, §5): its
 * last control is *Back to {group name}*, and *Done for now* goes there too. The name is the
 * route's to hand in, because the group is another feature's read; the way there is the gate's,
 * as the passport's is.
 *
 * **None of that is decided here.** `useAdvanceThroughPass` owns the whole transition and
 * the question screen calls the same hook, so the two screens cannot answer differently
 * again — which they did, over what a failed start does.
 */

import { useEffect } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { behindOverlay, Button, Card, Guide, Note, theme } from '@/shared/ui';

import type { AssessmentResult } from '../domain/AssessmentResult';
import type { Sport } from '@/shared/vocabulary/sport';
import { positionOf } from '../domain/onboardingPass';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAssessment } from '../hooks/useAssessment';
import { useRatingGuide } from '../hooks/useRatingGuide';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { EvidenceTrail } from './EvidenceTrail';
import { OnboardingChrome } from './OnboardingChrome';
import { useHardwareBack } from '@/shared/lib/platform';
import { bandPresentation } from './bandPresentation';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { passEyebrow } from './passEyebrow';
import {
  DONE_FOR_NOW,
  doneForNowHint,
  lastControlLabel,
  rateNextHint,
  rateNextLabel,
} from './resultPresentation';
import { formatRange } from '@/shared/formatting/ratingFormat';
import { sportLabel } from './sportPresentation';
import { STARTING_LABEL } from './startPresentation';
import {
  Verdict,
  VerdictPopover,
  useVerdictExplainer,
  useVerdictSpotlights,
  verdictGuide,
} from './Verdict';

/** Raised when the run ended on evidence the questionnaire could not settle. */
const CALIBRATION_ELEVATED = 'elevated';

export interface ResultScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
  /**
   * The name of the group a pass begun there returns to — the route reads it, since the group
   * is another feature's — and `undefined` for any other pass, or while it is being read.
   */
  readonly groupName?: string;
}

export function ResultScreen({ assessmentId, sport, groupName }: ResultScreenProps) {
  const assessment = useAssessment(assessmentId);
  const pass = useOnboardingPass((state) => state.pass);
  const position = positionOf(pass, sport);
  /**
   * **The device's back is claimed and refused, because this screen draws none.**
   *
   * Every screen in the questionnaire is reached by `replace`, so the group holds one entry,
   * and an unclaimed press would leave the app from under a rating just made. The way on is
   * the controls below; a press that does nothing is what the missing back control has
   * already said.
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
  // Both edges: this screen has no tab bar to take the bottom one.
  const insets = useSafeAreaInsets();

  // Which mark the popover is open on, if any. The card holds the refs and hands the pressed
  // one up, so the popover anchors to the mark it was opened from and returns focus to it.
  const explainer = useVerdictExplainer(result?.confidenceCeiling);

  // The guide's three figures, and whether this phone has yet to show it (ADR-0200 §8).
  const spotlit = useVerdictSpotlights();
  const guide = useRatingGuide(result !== undefined);

  /**
   * A rating exists for this sport, so the pass records it — the sport the way back stands on.
   *
   * Recorded **where the rating is shown** rather than where the run finished: the chip a group
   * pass lands on is the sport the player was told about, and a run whose result could not be
   * read is not something to land them on. Recording the same run twice is a no-op, which is
   * what makes a refetch or a remount free.
   */
  useEffect(() => {
    if (result === undefined) return;
    recordRun({ assessmentId, sport });
  }, [result, recordRun, assessmentId, sport]);

  return (
    <>
      <View
        style={[s.screen, { paddingTop: insets.top, paddingBottom: insets.bottom }]}
        // A popover is a real overlay: while one is open nothing behind it is reachable by
        // a screen reader. The popover is a sibling below, never a child — and so is the guide,
        // under which nothing here takes a touch either: it is modal.
        {...behindOverlay(explainer.open || guide.open)}
        pointerEvents={guide.open ? 'none' : 'auto'}
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
                spotlit={spotlit}
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
            // The last sport, and the label names what is actually next: back where the pass
            // began — the group, Home, or the passport's own *See your ratings*.
            <Button
              label={lastControlLabel(onwards.destination, groupName)}
              size="lg"
              onPress={onwards.advance}
            />
          ) : (
            <>
              <Button
                label={rateNextLabel(next)}
                size="lg"
                busy={onwards.advancing}
                busyLabel={STARTING_LABEL}
                accessibilityHint={rateNextHint(next)}
                onPress={onwards.advance}
              />
              <Button
                label={DONE_FOR_NOW}
                variant="secondary"
                size="lg"
                accessibilityHint={doneForNowHint(next)}
                onPress={onwards.stopHere}
              />
            </>
          )}
        </View>
      </View>

      <VerdictPopover {...explainer.popover} />
      <Guide
        visible={guide.open}
        steps={verdictGuide(spotlit, result?.confidenceCeiling)}
        onDone={guide.done}
      />
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
