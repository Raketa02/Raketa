/**
 * The result screen — one reader, and every rendering the conversation has.
 *
 * `ADR-0060` made this a route rather than a card or a sheet, on two facts neither
 * of which is about taste: **the card's action row holds one action** and
 * `confirmResult` needs two, because `ADR-0048` forbids a bare rejection so the
 * second is not optional; and **entry is typing where the card is for reading**, so
 * putting a pad inside a night card runs it past a 320pt screen on its own.
 *
 * ## It renders by situation, and there is no screen identifier
 *
 * `ADR-0060` again. Entry, the two audience renderings of a live proposal, the
 * counter, the settled result and the unscored ending are one route resolving the
 * **same situation the card resolved** — so the sentence at the top comes from
 * Now's own table, and what is drawn under it is composed from the server's three
 * booleans, the score on the table and the two clocks. Nothing here holds a
 * rendering enum, and nothing switches on the situation's name: the only block that
 * is keyed on it is the ending, which is resolved in `mappers/` where a wire code
 * may be named at all.
 *
 * ## The hero clock, and the sentence beside it
 *
 * `ADR-0060`: *"the remaining time is the largest figure on the screen, next to the
 * sentence that says nobody has to do anything. Silence is what settles this
 * result, so the screen that asks for a tap has to say what happens without one."*
 * The acceptance grace is the quieter second line and is drawn **only while it
 * runs**, because a screen that hid it would say *settled* half an hour early.
 *
 * ## A refusal is not a second shape
 *
 * `ADR-0070`. A side that has already spoken, a result that settled while her
 * screen was open, a deadline that ran out, a leaver tapping through a stale screen
 * — every one comes back as **what a success returns**, so there is one code path
 * here and the screen simply redraws. The single exception is a score no format of
 * this sport could produce, which is about what she **typed**: it rejects, and it
 * is the one failure that gets a sentence of its own.
 *
 * ## A leaver is offered nothing, and is not told her match never existed
 *
 * She resolves normally, with the three booleans false: the score reads the right
 * way round for her, because she played half an evening, and there is no control on
 * the screen. That is `ADR-0030`'s rule and the reason the route does not 404 her.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  SIDE_FALLBACK,
  countdownLabel,
  remainingMs,
  scoreBoardRows,
  useMomentClock,
  type Moment,
} from '@/features/now/types';
import type { AppError } from '@/shared/errors';
import {
  Button,
  Card,
  CloseControl,
  Note,
  Row,
  ScoreBoard,
  ScreenHeader,
  theme,
} from '@/shared/ui';

import type { Result } from '../domain/Result';
import {
  clearRowInPad,
  emptyPad,
  padFrom,
  padHasUnfinishedRow,
  padIsSendable,
  padSets,
  selectInPad,
  typeInPad,
  type ScorePad,
} from '../domain/scorePad';
import { useResult } from '../hooks/useResult';
import { useAcceptResult, useProposeScore } from '../hooks/useResultWrites';

import { ScorePadView } from './ScorePadView';
import {
  ACCEPT_LABEL,
  ASKED_LINE,
  CANCEL_ENTRY_LABEL,
  CLOSE_LABEL,
  CORRECT_LABEL,
  COUNTER_LABEL,
  LOAD_FAILED,
  PAD_CLEAR_LABEL,
  PAD_UNFINISHED,
  RESULT_TITLE,
  RETRY_LABEL,
  SEND_LABEL,
  SETTLEMENT_LABEL,
  TURNED_UP_LABEL,
  WAITING_LINE,
  countdownAccessibilityLabel,
  graceLine,
  silenceLine,
  turnedUpOf,
  writeFailureLine,
} from './resultCopy';

/** The body, so *has an answer arrived* is a structural question rather than a phrase. */
export const RESULT_BODY_ID = 'result-body';
export const HERO_CLOCK_ID = 'result-hero-clock';
export const GRACE_ID = 'result-grace';
export const ENDING_ID = 'result-ending';

export interface ResultScreenProps {
  readonly matchId: string;
  /** Where closing goes. The route owns navigation; this screen owns the screen. */
  readonly onClose: () => void;
}

export function ResultScreen({ matchId, onClose }: ResultScreenProps) {
  const result = useResult(matchId);
  const propose = useProposeScore(matchId);
  const accept = useAcceptResult(matchId);

  const screen = result.data;
  // One failure line for both writes: only one of them can be in flight, because
  // each is behind a control the other's rendering does not draw.
  const failure = propose.error ?? accept.error;

  return (
    // Both edges, unlike every screen under `(tabs)`: this route is pushed over the
    // tab bar rather than sitting inside it, so the bottom inset is this screen's to
    // spend and a button parked in it would be under the home bar.
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={s.content}>
        <ScreenHeader
          title={RESULT_TITLE}
          eyebrow={screen?.where.clubName}
          right={<CloseControl onPress={onClose} accessibilityLabel={CLOSE_LABEL} />}
        />

        {screen === undefined ? (
          result.error !== null ? (
            <Card style={s.card}>
              <Text style={s.failure}>{LOAD_FAILED}</Text>
              <Button
                label={RETRY_LABEL}
                variant="secondary"
                onPress={() => void result.refetch()}
              />
            </Card>
          ) : null
        ) : (
          <Loaded
            screen={screen}
            failure={failure}
            busy={propose.isPending || accept.isPending}
            onSend={(sets) => propose.mutate({ sets })}
            onAccept={() => accept.mutate()}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

/**
 * The screen once there is an answer to draw.
 *
 * Split out so the clock is armed over the moments of a screen that exists — a hook
 * cannot be conditional, and a clock over an absent screen would be a timer running
 * against nothing.
 */
function Loaded({
  screen,
  failure,
  busy,
  onSend,
  onAccept,
}: {
  readonly screen: Result;
  readonly failure: AppError | null;
  readonly busy: boolean;
  readonly onSend: (sets: readonly (readonly [number, number])[]) => void;
  readonly onAccept: () => void;
}) {
  // Both of this screen's moments, so one clock repaints them and two countdowns can
  // never disagree about what time it is by a render.
  const moments = useMemo(() => momentsOn(screen), [screen]);
  const now = useMomentClock(moments);

  const countdown = useCallback(
    (moment: Moment | undefined): string | undefined => {
      if (moment === undefined) return undefined;
      const left = remainingMs(moment, now);
      // A moment that does not parse is a contract failure rather than a state, and
      // the answer is *there is no countdown here* rather than a figure in decades —
      // the same answer a card's clock gives.
      return left === undefined ? undefined : countdownLabel(left);
    },
    [now],
  );

  const score = screen.result.score;
  // Entry is the rendering with nothing else on it, so the pad is open from the
  // start; a correction and a counter are reached from a screen whose first job is
  // to show what is already on the table, so their pad opens behind a control.
  const entering = screen.mayEnter && score === undefined;
  const [typed, setTyped] = useState<ScorePad | undefined>(undefined);

  // A fresh answer closes the pad. After a send that landed, what she typed is on
  // the table above — leaving the pad open would offer her the same act again with
  // her own numbers still in it.
  useEffect(() => setTyped(undefined), [screen]);

  const pad = typed ?? (entering ? emptyPad() : undefined);
  const sides = score === undefined ? SIDE_FALLBACK : scoreBoardRows(score).map((row) => row.name);

  const settlement = countdown(screen.settlementDeadline);
  const grace = countdown(screen.acceptanceGrace);

  return (
    <View style={s.body} testID={RESULT_BODY_ID}>
      <Card style={s.card}>
        {/* What the match is doing, in the words the card she tapped used. */}
        {screen.status !== undefined ? <Text style={s.line}>{screen.status.line}</Text> : null}

        {/* The hero: the largest figure on the screen, and beside it the sentence
            that says what happens if she does nothing (`ADR-0060`). Absent once the
            answer is in — a settled result and an unscored evening count to nothing
            rather than to zero, and the ending below says so instead. */}
        {settlement === undefined ? null : (
          <View style={s.hero}>
            <Text style={s.heroLabel}>{SETTLEMENT_LABEL}</Text>
            <Text
              style={s.heroClock}
              testID={HERO_CLOCK_ID}
              accessibilityLabel={countdownAccessibilityLabel(settlement)}
            >
              {settlement}
            </Text>
            <Text style={s.line}>{silenceLine(screen.result.proposals)}</Text>
          </View>
        )}

        {/* The quieter clock, present only while it runs. */}
        {grace === undefined ? null : (
          <Text style={s.grace} testID={GRACE_ID}>
            {graceLine(grace)}
          </Text>
        )}

        {/* Who turned up, on a match that has been played. Sent rather than derived:
            *one less than the seats* stops being minus one the moment a doubles
            match loses two people. */}
        {screen.counts.turnedUp === undefined ? null : (
          <Row
            label={TURNED_UP_LABEL}
            value={turnedUpOf(screen.counts.turnedUp, screen.counts.seats)}
            accessibilityLabel={`${TURNED_UP_LABEL}, ${turnedUpOf(screen.counts.turnedUp, screen.counts.seats)}`}
          />
        )}
      </Card>

      {/* What is on the table, with both sides named and hers first (`ADR-0060`).
          The line above it says whether she is being asked or is waiting, and is
          drawn only while the conversation is live: once it has settled, the ending
          says what it is instead. */}
      {score === undefined ? null : (
        <Card style={s.card}>
          {screen.result.agreed ? null : (
            <Text style={s.line}>{screen.result.proposedBy === 0 ? WAITING_LINE : ASKED_LINE}</Text>
          )}
          <ScoreBoard rows={scoreBoardRows(score)} />
        </Card>
      )}

      {/* How it ended, on the two situations that end it. */}
      {screen.ending === undefined ? null : (
        <Note variant="base" title={screen.ending.title}>
          <View style={s.ending} testID={ENDING_ID}>
            {screen.ending.lines.map((line) => (
              <Text key={line} style={s.line}>
                {line}
              </Text>
            ))}
          </View>
        </Note>
      )}

      {pad === undefined ? (
        <View style={s.acts}>
          {/* Accepting, and the modification that is the only way to disagree.
              There is no third control: a bare rejection is refused by having no
              shape to send one in (`ADR-0048`), not by a validator turning one
              away. */}
          {screen.mayAccept ? (
            <Button label={ACCEPT_LABEL} size="lg" busy={busy} onPress={onAccept} />
          ) : null}
          {screen.mayCounter ? (
            <Button
              label={COUNTER_LABEL}
              variant="secondary"
              size="lg"
              // A counter opens an **empty** pad. Pre-filling it with the score it
              // is countering puts her one tap from a "different" score identical
              // to the one on the table — which consumes her side's one proposal
              // and then lets silence uncount the match.
              onPress={() => setTyped(emptyPad())}
            />
          ) : null}
          {screen.mayEnter && score !== undefined ? (
            <Button
              label={CORRECT_LABEL}
              variant="secondary"
              size="lg"
              // A correction opens on what is already there: she is editing her own
              // side's sentence, not writing a different one.
              onPress={() => setTyped(padFrom(score))}
            />
          ) : null}
        </View>
      ) : (
        <View style={s.acts}>
          <Card style={s.card}>
            <ScorePadView
              pad={pad}
              sides={sides}
              onType={(value) => setTyped(typeInPad(pad, value))}
              onSelect={(row, side) => setTyped(selectInPad(pad, { row, side }))}
            />
          </Card>

          {/* The one thing the pad refuses to send, said rather than left as a
              missing button: a row holding one number and waiting for the other. */}
          {padHasUnfinishedRow(pad) ? <Text style={s.grace}>{PAD_UNFINISHED}</Text> : null}

          {padIsSendable(pad) ? (
            <Button label={SEND_LABEL} size="lg" busy={busy} onPress={() => onSend(padSets(pad))} />
          ) : null}
          <Button
            label={PAD_CLEAR_LABEL}
            variant="secondary"
            onPress={() => setTyped(clearRowInPad(pad))}
          />
          {/* The way back out of a pad she opened. Entry has none: there is nothing
              behind it to leave as it is. */}
          {entering ? null : (
            <Button
              label={CANCEL_ENTRY_LABEL}
              variant="secondary"
              onPress={() => setTyped(undefined)}
            />
          )}
        </View>
      )}

      {failure !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {writeFailureLine(failure)}
        </Note>
      ) : null}
    </View>
  );
}

/**
 * The two moments this screen draws, in no particular order.
 *
 * Selecting fields is not deriving from them: nothing below computes a value the
 * server did not send.
 */
function momentsOn(screen: Result): readonly Moment[] {
  return [screen.settlementDeadline, screen.acceptanceGrace].filter(
    (moment): moment is Moment => moment !== undefined,
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: { paddingBottom: theme.space.xxxl },
  body: { paddingHorizontal: theme.space.lg, gap: theme.space.sm },
  card: { gap: theme.space.xs },
  acts: { gap: theme.space.xs },
  ending: { gap: theme.space.xs },
  hero: { gap: theme.space.xxs },
  heroLabel: { ...theme.type.flab, color: theme.color.muted },
  // The largest figure on the screen, which is `ADR-0060`'s instruction rather than
  // a preference: silence settles this, so the thing that happens without her is
  // what the screen leads with.
  heroClock: { ...theme.num.xl, ...theme.tabular, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.ink },
  grace: { ...theme.type.tiny, color: theme.color.muted },
  failure: { ...theme.type.tiny, color: theme.color.muted },
});
