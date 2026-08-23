/**
 * The result screen: one sport's Skill rating, and the reasoning behind it.
 *
 * **A rating is never only a number.** The screen leads with the Level, but shows it inside
 * its likely range, with its Confidence and its Band — two players both showing 3,0 at very
 * different Uncertainties are not the same player, and nothing here may imply they are.
 *
 * **The evidence trail is the point of the screen** and lives in its own component. What
 * this one owns is the verdict above it: the Level, the range, the ring, the bar, the band
 * card, and the three information marks that explain the figures none of which is
 * self-explanatory.
 *
 * ## The rules that are easy to break here
 *
 * - **Band boundaries come from the response.** They are deliberately uneven, they were
 *   wrong once already, and this client restates them nowhere. The level bar's own segment
 *   boundaries are drawing values and are never printed.
 * - **Confidence is drawn on the full 0–100 scale with the ceiling marked**, never rescaled
 *   so that a questionnaire's maximum fills the ring. Everyone leaves onboarding at or
 *   below the ceiling; the tick is what stops a short arc reading as failure, and it is
 *   what keeps the same component honest when matches later push Confidence to 75%.
 * - **Nothing on this screen decides anything about the rating.** Labels and sentences are
 *   the server's, directions are the engine's, and the client renders them in the order it
 *   was given them.
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
 *
 * **None of that is decided here.** `useAdvanceThroughPass` owns the whole transition and
 * the question screen calls the same hook, so the two screens cannot answer differently
 * again — which they did, over what a failed start does.
 */

import { useEffect, useRef, useState, type MutableRefObject } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  behindOverlay,
  Button,
  Card,
  ConfidenceRing,
  DarkCard,
  Hairline,
  InfoMark,
  LevelBar,
  Note,
  Popover,
  Row,
  theme,
} from '@/shared/ui';

import type { AssessmentResult } from '../domain/AssessmentResult';
import type { Sport } from '../domain/Sport';
import { positionOf } from '../domain/onboardingPass';
import { useAdvanceThroughPass } from '../hooks/useAdvanceThroughPass';
import { useAssessment } from '../hooks/useAssessment';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { EvidenceTrail } from './EvidenceTrail';
import { OnboardingChrome } from './OnboardingChrome';
import { BAND_NAMES, bandPresentation, ratingStatusLabel } from './bandPresentation';
import { onboardingErrorMessage } from './onboardingErrorMessage';
import { passEyebrow } from './passEyebrow';
import { formatConfidence, formatLevel, formatRange } from './ratingFormat';
import { sportLabel } from './sportPresentation';

type ExplainerKey = 'level' | 'range' | 'confidence';

type Explainers = Readonly<Record<ExplainerKey, { readonly title: string; readonly body: string }>>;

/**
 * The three figures with an information mark. **None of them is self-explanatory**, which
 * is the reason each has one: a player can ask what a term means at the moment they meet
 * it, rather than being expected to have read something first.
 *
 * This is the app's own copy, not the engine's — the wire carries no definition of what a
 * Level *is*. The one number in it is the ceiling, which the engine serves rather than the
 * app knowing, so the copy is built per result instead of being a module constant: retuning
 * the ceiling moves this sentence with it and no release is involved.
 *
 * **With no ceiling served, the sentence naming one goes.** The rest still holds — what
 * Confidence is, and that matches are what raise it — but a rating whose engine has been
 * retired has no number for "at most", and inventing one would say a retired engine was
 * measured against a limit that did not exist when it ran.
 */
function explainers(ceiling: number | undefined): Explainers {
  return {
    level: {
      title: 'Your Level',
      body: 'Where you sit on the 1,00–5,00 scale for this sport. It is an estimate rather than a grade, and it is meant to move — real matches are what settle it.',
    },
    range: {
      title: 'Your likely range',
      body: 'Where we think your Level really sits. A wide range means we are less sure, not that you are weaker: it narrows as you play, without your Level having to move at all.',
    },
    confidence: {
      title: 'Confidence',
      body:
        ceiling === undefined
          ? 'How sure we are, not how good you are. It starts low because a questionnaire is all we have to go on — we have not seen you play yet. Matches are what raise it.'
          : `How sure we are, not how good you are. A questionnaire can prove at most ${ceiling}% — the mark on the ring — because we have not seen you play yet. Matches are what raise it.`,
    },
  };
}

/**
 * `MutableRefObject`, not the shared `FocusTarget`: the same ref is handed to `InfoMark`
 * as a *ref* and to `Popover` as a focus target, and `RefObject<View | null>` is covariant
 * — it will not go where a `Ref<View>` is wanted.
 */
type MarkRefs = Readonly<Record<ExplainerKey, MutableRefObject<View | null>>>;

/** Raised when the run ended on evidence the questionnaire could not settle. */
const CALIBRATION_ELEVATED = 'elevated';

export interface ResultScreenProps {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export function ResultScreen({ assessmentId, sport }: ResultScreenProps) {
  const assessment = useAssessment(assessmentId);
  const pass = useOnboardingPass((state) => state.pass);
  const position = positionOf(pass, sport);
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

  // One ref per mark: the popover anchors to the mark it was opened from and returns
  // focus to it on close, which is one prop doing both jobs.
  const [explainer, setExplainer] = useState<ExplainerKey>();
  const marks: MarkRefs = {
    level: useRef<View | null>(null),
    range: useRef<View | null>(null),
    confidence: useRef<View | null>(null),
  };

  const result = assessment.data?.result;

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

  /**
   * Which mark the popover belongs to, **held past the close**. Dropping it the moment
   * `explainer` clears would empty the card while it is still fading out and — the part
   * that matters — leave the close with no trigger to return accessibility focus to.
   * Written during render rather than kept in a second state, which could disagree.
   */
  const closing = useRef<ExplainerKey>('level');
  if (explainer !== undefined) closing.current = explainer;
  const explaining = explainer ?? closing.current;
  const explained = explainers(result?.confidenceCeiling)[explaining];

  return (
    <>
      <SafeAreaView
        style={s.screen}
        edges={['top', 'bottom']}
        // A popover is a real overlay: while one is open nothing behind it is reachable by
        // a screen reader. The popover is a sibling below, never a child.
        {...behindOverlay(explainer !== undefined)}
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
            <Verdict result={result} marks={marks} onExplain={setExplainer} />
          ) : null}

          {result?.confidenceReason !== undefined ? (
            <Note variant="info">{result.confidenceReason.sentence}</Note>
          ) : null}

          {result !== undefined && result.calibrationPriority === CALIBRATION_ELEVATED ? (
            <Note variant="base" title="We will want matches sooner">
              Your answers left something unsettled, so this estimate is queued for real matches to
              confirm. It changes who you are matched with, never where you sit.
            </Note>
          ) : null}

          {result !== undefined ? (
            <EvidenceTrail contributions={result.contributions} wideners={result.wideners} />
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
            // Stopping here is an outcome, not an abandonment: nothing is discarded and
            // nothing is sent. Where it leads is the pass's answer — the closing screens
            // for a walk through onboarding, and **Now filtered to this sport** for a
            // sport picked up at Now's door (`ADR-0084`).
            //
            // The label follows the destination rather than the other way round: *See
            // your ratings* on a button that lands on the home screen is the app telling
            // her where she is going and then going somewhere else.
            <Button
              label={onwards.destination.kind === 'now' ? 'See what’s on' : 'See your ratings'}
              size="lg"
              onPress={onwards.advance}
            />
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

      <Popover
        visible={explainer !== undefined}
        trigger={marks[explaining]}
        title={explained.title}
        body={explained.body}
        closeLabel={`Close ${explained.title}`}
        onClose={() => setExplainer(undefined)}
      />
    </>
  );
}

interface VerdictProps {
  readonly result: AssessmentResult;
  readonly marks: MarkRefs;
  readonly onExplain: (key: ExplainerKey) => void;
}

/**
 * The upper half: the four figures that have to be read together, then the bar, then the
 * band card whose left rail is the only place a band colour appears outside the bar.
 */
function Verdict({ result, marks, onExplain }: VerdictProps) {
  const band = bandPresentation(result.band.name);
  const level = formatLevel(result.level);
  const range = formatRange(result.range);
  const confidence = formatConfidence(result.confidence);

  return (
    <>
      <DarkCard>
        <View style={s.verdict}>
          <View style={s.figures}>
            <View style={s.figureHead}>
              <Text style={s.eyebrowOnDark}>Your level</Text>
              <InfoMark
                ref={marks.level}
                onDark
                onPress={() => onExplain('level')}
                accessibilityLabel="What your Level means"
              />
            </View>
            <Text style={s.level}>{level}</Text>

            <View style={s.figureHead}>
              <Text style={s.rangeValue}>{range}</Text>
              <Text style={s.rangeLabel}>likely range</Text>
              <InfoMark
                ref={marks.range}
                onDark
                onPress={() => onExplain('range')}
                accessibilityLabel="What your likely range means"
              />
            </View>
          </View>

          <View style={s.ring}>
            {/* The ceiling is the engine's and arrives with the rating. Absent, the ring
                draws no tick and its name states the one number it has — see
                `AssessmentResult.confidenceCeiling`. */}
            <ConfidenceRing
              value={result.confidence}
              ceiling={result.confidenceCeiling}
              label="Confidence"
              accessibilityLabel={
                result.confidenceCeiling === undefined
                  ? `Confidence ${confidence}`
                  : `Confidence ${confidence}, out of the ${result.confidenceCeiling}% a questionnaire can prove`
              }
            />
            <InfoMark
              ref={marks.confidence}
              onDark
              onPress={() => onExplain('confidence')}
              accessibilityLabel="What Confidence means"
            />
          </View>
        </View>

        <View style={s.bar}>
          <LevelBar
            level={result.level}
            range={result.range}
            band={band?.key}
            bandNames={BAND_NAMES}
            variant="onDark"
            legend={{ mark: 'Your level', bracket: 'Likely range' }}
            accessibilityLabel={`Level ${level} of 5,00, likely range ${range}, band ${result.band.name}`}
          />
        </View>

        <Hairline variant="onDark">
          <Row
            variant="onDark"
            label="Band"
            value={result.band.name}
            accessibilityLabel={`Band: ${result.band.name}`}
          />
          <Row
            variant="onDark"
            divided
            label="Rating status"
            value={ratingStatusLabel(result.status)}
            accessibilityLabel={`Rating status: ${ratingStatusLabel(result.status)}`}
          />
          <Row
            variant="onDark"
            divided
            label="Questions asked"
            value={String(result.questionsAsked)}
            accessibilityLabel={`Questions asked: ${result.questionsAsked}`}
          />
        </Hairline>
      </DarkCard>

      {/* The band's own ink on the left rail — the only place a band colour appears outside
          the bar. The edges printed here are the response's, never the bar's drawing
          values, and a band this build cannot name still shows its name and its numbers. */}
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
    </>
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
  verdict: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figures: { flex: 1, gap: theme.space.xxs },
  figureHead: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  eyebrowOnDark: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
  },
  level: { ...theme.num.levelHero, ...theme.tabular, color: theme.color.surface },
  rangeValue: { ...theme.num.s, ...theme.tabular, color: theme.color.surface },
  rangeLabel: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  ring: { alignItems: 'center', gap: theme.space.xxs },
  bar: { marginTop: theme.space.lg },
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
