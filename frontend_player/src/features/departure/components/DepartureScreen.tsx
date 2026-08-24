/**
 * The departure screen — what leaving is worth, and the one control that takes it.
 *
 * `ADR-0086`. It is the route the *leave a match* control on Now opens, and it
 * exists because the act needs a money line **a card demonstrably cannot give it
 * room for**: four outcomes with a marker on each, and beside the quote its three
 * reasons.
 *
 * ## The screen is the confirmation
 *
 * One primary button carrying the quote, and **no third step**. A confirm dialog
 * over a screen whose entire job is to state the consequence asks the same
 * question twice, and the refuse-and-re-present rule already gives her the only
 * correction that matters — what is true now, rather than a sentence about a rule.
 *
 * ## A refusal is not a second shape
 *
 * `ADR-0070`. Every way this act can stop applying — the quote fell, the match
 * started, it was cancelled, `ADR-0046`'s lock closed, she has already left — comes
 * back as **what a success returns**: the same screen, recomposed. So there is one
 * code path here, the screen simply redraws, and the player *sees* that she cannot
 * leave rather than being told it by a dialog she has to dismiss. What tells the
 * two apart is `applied`, and it is a field on the answer rather than something
 * derived from `mayDepart` still being true — deriving it would be a rule, and
 * `ADR-0053` leaves the phone none.
 *
 * ## Past the point of departure the control is absent, not refusing
 *
 * `mayDepart` is the server's boolean and no button is drawn without it. Nothing is
 * added in its place either: the situation line above already says what the match
 * is doing — *Ready to play*, *Cancelled* — which is the reason, and a second
 * sentence explaining the missing control would be the refusal `ADR-0086` says not
 * to draw.
 *
 * ## Nothing here mentions transferring a seat
 *
 * `ADR-0086`: it is the leaver's best outcome and it belongs to the invite flow,
 * which this map rules out — *"advertising a door that is not there is worse than
 * the gap."* `departureDiscipline.test.ts` walks this feature so it cannot arrive
 * by accident.
 */

import { useCallback, useMemo, useRef } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { countdownLabel, remainingMs, useMomentClock, type Moment } from '@/features/now/types';
import { formatMoney } from '@/shared/lib/formatting';
import { Button, Card, CloseControl, Note, Row, ScreenHeader, theme } from '@/shared/ui';

import type { Departure, OutcomeRow } from '../domain/Departure';
import { departureRequestKey } from '../domain/requestKey';
import { useDeparture } from '../hooks/useDeparture';
import { useLeaveMatch } from '../hooks/useLeaveMatch';

import { OutcomeTable } from './OutcomeTable';
import {
  CLOSE_LABEL,
  DEPARTURE_TITLE,
  DONE_LABEL,
  LEFT_TITLE,
  LOAD_FAILED,
  OUTCOMES_HEADING,
  REASON_LABEL,
  REFUSED_LINE,
  REFUSED_TITLE,
  RETRY_LABEL,
  WRITE_FAILED,
  countdownAccessibilityLabel,
  paidOfSeats,
} from './departureCopy';

export const REFUSAL_ID = 'departure-refusal';
export const APPLIED_ID = 'departure-applied';
export const CLOCK_ID = 'departure-clock';

export interface DepartureScreenProps {
  readonly matchId: string;
  /** Where closing goes. The route owns navigation; this screen owns the screen. */
  readonly onClose: () => void;
}

export function DepartureScreen({ matchId, onClose }: DepartureScreenProps) {
  const departure = useDeparture(matchId);
  const leave = useLeaveMatch(matchId);

  // One key for this visit to the screen, and every press within it re-sends the
  // same one. A press that timed out and a press she was not sure registered are
  // both the same intent, and the server answers a repeat with what the first one
  // did rather than applying a second departure. See `domain/requestKey.ts`.
  const idempotencyKey = useRef<string>();
  idempotencyKey.current ??= departureRequestKey(matchId);

  const screen = departure.data;
  const quote = screen?.quote;

  const onLeave = useCallback(() => {
    if (quote === undefined || idempotencyKey.current === undefined) return;
    leave.mutate({ quote: quote.outcome, idempotencyKey: idempotencyKey.current });
  }, [leave, quote]);

  return (
    // Both edges, unlike every screen under `(tabs)`: this route is pushed over
    // the tab bar rather than sitting inside it, so the bottom inset is this
    // screen's to spend and a button parked in it would be under the home bar.
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={s.content}>
        <ScreenHeader
          title={DEPARTURE_TITLE}
          eyebrow={screen?.where.clubName}
          right={<CloseControl onPress={onClose} accessibilityLabel={CLOSE_LABEL} />}
        />

        {screen === undefined ? (
          departure.error !== null ? (
            <Card style={s.card}>
              <Text style={s.failure}>{LOAD_FAILED}</Text>
              <Button
                label={RETRY_LABEL}
                variant="secondary"
                onPress={() => void departure.refetch()}
              />
            </Card>
          ) : null
        ) : (
          <Loaded
            screen={screen}
            applied={leave.data?.applied}
            refused={leave.data !== undefined && leave.data.applied === undefined}
            failed={leave.error !== null}
            busy={leave.isPending}
            onLeave={onLeave}
            onClose={onClose}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

/**
 * The screen once there is an answer to draw.
 *
 * Split out so the clock is armed over the moments of a screen that exists — a
 * hook cannot be conditional, and a clock over an absent screen would be a timer
 * running against nothing.
 */
function Loaded({
  screen,
  applied,
  refused,
  failed,
  busy,
  onLeave,
  onClose,
}: {
  readonly screen: Departure;
  readonly applied: Departure['quote'] | undefined;
  readonly refused: boolean;
  readonly failed: boolean;
  readonly busy: boolean;
  readonly onLeave: () => void;
  readonly onClose: () => void;
}) {
  // Every moment this screen holds, so one clock repaints all of them and two
  // countdowns can never disagree about what time it is by a render.
  const moments = useMemo(() => momentsOn(screen), [screen]);
  // Now's loop, not a second one. It was this feature's until the result route
  // became the third screen to want a countdown, which is the trigger the hook that
  // lived here recorded for promoting it (`Raketa02/Raketa#90`).
  const now = useMomentClock(moments);

  const countdown = useCallback(
    (moment: Moment | undefined): string | undefined => {
      if (moment === undefined) return undefined;
      const left = remainingMs(moment, now);
      // A moment that does not parse is a contract failure rather than a state,
      // and the answer is *there is no countdown here* rather than a figure in
      // decades — the same answer a card's clock gives.
      return left === undefined ? undefined : countdownLabel(left);
    },
    [now],
  );

  const commitment = countdown(screen.commitmentDeadline);

  return (
    <View style={s.body}>
      <Card style={s.card}>
        {/* What the match is doing, in the words the card she tapped used. On a
            screen with one match on it this is also *why* — a control that is not
            there because the match has started is explained by the line saying it
            has. There is no second metadata line under it: the club is the
            eyebrow, and a roof and a distance are facts about playing rather than
            about leaving. */}
        {screen.status !== undefined ? <Text style={s.line}>{screen.status.line}</Text> : null}

        {/* The three reasons behind the quote, drawn beside it. They ride at the
            top level of the answer rather than only inside the situation half,
            because that half is the one a phone reads only when it knows the name
            — and a fact the screen must always draw cannot live only there. */}
        {commitment === undefined ? null : (
          <Row
            label={REASON_LABEL.commitment}
            value={
              <Text style={s.clock} testID={CLOCK_ID}>
                {commitment}
              </Text>
            }
            accessibilityLabel={`${REASON_LABEL.commitment}, ${countdownAccessibilityLabel(commitment)}`}
          />
        )}
        <Row
          label={REASON_LABEL.seat}
          value={formatMoney(screen.price)}
          divided={commitment !== undefined}
          accessibilityLabel={`${REASON_LABEL.seat}, ${formatMoney(screen.price)}`}
        />
        <Row
          label={REASON_LABEL.paid}
          value={paidOfSeats(screen.counts.paid, screen.counts.seats)}
          divided
          accessibilityLabel={`${REASON_LABEL.paid}, ${paidOfSeats(screen.counts.paid, screen.counts.seats)}`}
        />
        {/* A held seat is a name with no money behind it, so it is its own number
            and never folded into the one above (`counting is by money`). Drawn
            only when there are any: a row reading `0` invites the reading that
            somebody is holding nothing. */}
        {screen.counts.held > 0 ? (
          <Row
            label={REASON_LABEL.held}
            value={String(screen.counts.held)}
            divided
            accessibilityLabel={`${REASON_LABEL.held}, ${screen.counts.held}`}
          />
        ) : null}
      </Card>

      <View style={s.section}>
        <Text style={s.heading} accessibilityRole="header">
          {OUTCOMES_HEADING}
        </Text>
        <Card style={s.card}>
          <OutcomeTable outcomes={screen.outcomes} countdownFor={(row) => countdown(row.opensAt)} />
        </Card>
      </View>

      {refused ? (
        <Note variant="amber" title={REFUSED_TITLE} accessibilityRole="alert">
          <Text style={s.noteBody} testID={REFUSAL_ID}>
            {REFUSED_LINE}
          </Text>
        </Note>
      ) : null}

      {applied?.copy !== undefined ? (
        <Note variant="mint" title={LEFT_TITLE} accessibilityRole="alert">
          <Text style={s.noteBody} testID={APPLIED_ID}>
            {applied.copy.left}
          </Text>
        </Note>
      ) : null}

      {failed ? (
        <Note variant="coral" accessibilityRole="alert">
          {WRITE_FAILED}
        </Note>
      ) : null}

      {/* The one button, and it carries the quote. Absent — never disabled and
          never refusing — when the server says she may not leave: past the point
          of departure no door is offered that will not open. Absent too for a
          quote this build cannot name, because a control whose consequence the app
          cannot state is the one outcome worse than silence. */}
      {screen.mayDepart && screen.quote.copy !== undefined ? (
        <Button label={screen.quote.copy.leaving} size="lg" busy={busy} onPress={onLeave} />
      ) : null}

      {/* The way out of a screen that has nothing left to ask. It appears with the
          acknowledgement rather than replacing the close control, so the departure
          she just made is what she confirms her way out of. */}
      {applied !== undefined ? (
        <Button label={DONE_LABEL} variant="secondary" size="lg" onPress={onClose} />
      ) : null}
    </View>
  );
}

/**
 * Every moment the screen draws, in no particular order.
 *
 * Selecting fields is not deriving from them: nothing below computes a value the
 * server did not send. The spine's own clock slot is **not** here, because this
 * screen does not draw it — a repaint armed for a countdown no reader watches is
 * a phone woken for nothing.
 */
function momentsOn(screen: Departure): readonly Moment[] {
  const rows = screen.outcomes
    .map((row: OutcomeRow) => row.opensAt)
    .filter((moment): moment is Moment => moment !== undefined);

  return screen.commitmentDeadline === undefined ? rows : [screen.commitmentDeadline, ...rows];
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: { paddingBottom: theme.space.xxxl },
  body: { paddingHorizontal: theme.space.lg, gap: theme.space.sm },
  section: { gap: theme.space.xs },
  card: { gap: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.muted },
  line: { ...theme.type.tiny, color: theme.color.ink },
  clock: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  noteBody: { ...theme.type.tiny, color: theme.color.ink },
  failure: { ...theme.type.tiny, color: theme.color.muted },
});
