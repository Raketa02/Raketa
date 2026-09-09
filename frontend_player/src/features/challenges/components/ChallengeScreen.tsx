/**
 * **One challenge, and the two answers** — the screen a row in the Chats inbox opens.
 *
 * A **state-keyed surface over the six standings and two sides**, and never a `GameStanding`: a
 * challenge with no acceptance has no game to key a screen on, which is why there are two
 * state-keyed surfaces in this app and not one
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §2). Which
 * arm is drawn is `challengeArm`'s answer and never this file's — the sentence, the card block
 * and the controls are three readings of **one** fold, so the screen cannot say *They're waiting
 * on you* over a court it is also refusing to let you answer.
 *
 * **`ON` has an arm and no door.** Nothing navigates here — the game's own standing owns the card
 * the moment a game exists — and the arm exists so a stale route resolves to a sentence rather
 * than to a blank screen.
 *
 * ## The affordance is never removed without the space saying what took it
 *
 * §2.4's obligation, and it is discharged **by construction** rather than by a rule this file
 * remembers. The buttons and the standing sentence come out of the same fold, so there is no
 * state in which the controls are gone and the sentence has not changed: a refetch that lands
 * `LAPSED` draws *Your day ran out* in the same render that stops drawing `I'm in`, and a refusal
 * that re-reads does the same one round trip later. **The buttons are replaced by the sentence,
 * never by nothing.**
 *
 * **The offer may expire under the finger, and it is let to.** The read sits at `staleTime: 0`
 * with the app's own focus refetch, so a redraw can take **I'm in** away while the player is
 * looking at it. A mis-tap prevented beats a mis-tap refused.
 *
 * ## Offline is the shipped pattern exactly
 *
 * `BuilderScreen`'s: **the pair greys out, and one amber note sits above them** — not one per
 * button, which would say the same thing twice about one connection. The sentence is the shared
 * `does-not-resume` value unchanged, and **there is no third value**: the two split on
 * resumption, and a third keyed to the act would break the only distinction that function has.
 *
 * ## The forecast is drawn once, and the cards are drawn per person
 *
 * *The same figure rides on every card, because a forecast is a fact about the game rather than
 * about one person* — so it is the screen's line and not the card's, and a doubles court states
 * it once instead of three times. What is genuinely per pairing stays on the card: the Fit, the
 * distance, the reasons, the concern and what is at stake.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import {
  PROVISIONAL_WORD,
  balanceReading,
  forecastAssumption,
  forecastHeading,
} from '@/features/play/types';
import { sportLabel } from '@/features/onboarding/types';
import { ShellScreen } from '@/features/shell/types';
import { useCurrentUser } from '@/features/auth/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';

import { useIsOnline } from '@/shared/lib/platform';
import { durationLeft } from '@/shared/formatting/durations';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';
import { Button, Note, theme } from '@/shared/ui';

import { answerRefusal } from '../domain/answerRefusal';
import { challengeArm, seatsAwaiting, type ChallengeDetail } from '../domain/challengeDetail';
import { useAnswerSeat, useChallenge } from '../hooks/useChallenge';
import type { SeatAnswerAct } from '../use-cases/answerSeat';

import { ChallengeCard } from './ChallengeCard';
import { challengeErrorMessage } from './challengeErrorMessage';
import {
  IM_IN,
  NOT_THIS_TIME,
  NO_CHALLENGE_HERE,
  pairingAbsenceLine,
} from './challengeDetailPresentation';
import {
  CHALLENGE_SCREEN_TITLE,
  answerWindowLine,
  standingLine,
  yourAnswerWindowLine,
} from './challengePresentation';

export interface ChallengeScreenProps {
  /** Validated by `schemas/routeParams.ts` before it reaches here; the route does that. */
  readonly challengeId: string;
}

export function ChallengeScreen({ challengeId }: ChallengeScreenProps) {
  const { data, isPending, error, refetch } = useChallenge(challengeId);
  const me = useCurrentUser().data?.id;

  if (data === undefined || me === undefined) {
    // **Who the reader is counts as still coming.** `useCurrentUser` is seeded by bootstrap and
    // answers first almost always, but *almost* is what the terminal sentence cannot afford:
    // drawn while it is in flight it says no challenge of yours has this address about a
    // challenge that is on screen a frame later.
    const arriving = isPending || (me === undefined && error === null);

    return (
      <ShellScreen title={CHALLENGE_SCREEN_TITLE} onBack={router.back}>
        {/* Three states with one sentence each, and none of them invents a fourth: the read is
            still coming, it failed, or no challenge of yours has this address — which is also
            what a sport this build cannot name resolves to. 10.1 forbids a spinner in this
            slot, so the first of the three draws nothing at all. */}
        {arriving ? null : error !== null ? (
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
        ) : (
          <Text style={s.line}>{NO_CHALLENGE_HERE}</Text>
        )}
      </ShellScreen>
    );
  }

  return <Arrangement detail={data} playerId={me} onReRead={() => void refetch()} />;
}

function Arrangement({
  detail,
  playerId,
  onReRead,
}: {
  readonly detail: ChallengeDetail;
  readonly playerId: string;
  readonly onReRead: () => void;
}) {
  const arm = challengeArm(detail, playerId);
  const answer = useAnswerSeat();
  const online = useIsOnline();

  /**
   * Which of the two is in flight, so the pressed control is the one that goes busy.
   *
   * Route-local and cleared by the reply, because it is a fact about a press rather than about
   * the challenge: leaving the screen throws it away, which is right for a tap nobody is
   * waiting on any more.
   */
  const [pressed, setPressed] = useState<SeatAnswerAct>();

  const refusal = answer.error === null ? undefined : answerRefusal(answer.error);
  const cards = arm.kind === 'answer' || arm.kind === 'arranging';
  const sentence = arm.kind === 'unreadable' ? OUT_OF_DATE_GAP : standingLine(arm.facts);

  function send(act: SeatAnswerAct): void {
    setPressed(act);
    answer.mutate(
      { challengeId: detail.challengeId, act },
      {
        onSettled: () => setPressed(undefined),
        onError: (failed) => {
          const next = answerRefusal(failed);
          // A stale tap is a re-read, not a toast: the standing the read comes back with **is**
          // the sentence, and both of the sentences it can land on are already written.
          if (next.kind === 'READ_IT_BACK') onReRead();
          // It is gone, or it was never yours, and one code says both on purpose. There is
          // nothing behind this screen, so it is not a screen to leave the player on.
          if (next.kind === 'LEAVE') router.back();
        },
      },
    );
  }

  // The court's own forecast, off whichever card carries one: it is the same figure on all of
  // them, so the first is the answer rather than a choice.
  const forecast = detail.seats.flatMap((seat) => seat.card?.pairing.forecast ?? [])[0];

  return (
    <ShellScreen
      title={CHALLENGE_SCREEN_TITLE}
      eyebrow={sportLabel(detail.sport)}
      onBack={router.back}
      action={
        arm.kind === 'answer' ? (
          <View style={s.answers}>
            {/* The deadline **stated, never counted down** — folded against the response's own
                `read_at` and never against this phone's clock. It gates nothing: the buttons
                beside it are drawn from the standing the platform sent. */}
            {arm.answerBy === undefined ? null : (
              <Text style={s.line}>
                {yourAnswerWindowLine(durationLeft(arm.answerBy, detail.readAt))}
              </Text>
            )}

            {/* This feature's own table, and **no new copy** for the two refusals that re-read:
                they are handled by reading, and what they end up saying is the standing above.
                A connection that was not there maps to the same `does-not-resume` sentence the
                note below states, which is the one value the two share by construction. */}
            {refusal?.kind === 'SAY_SO' ? (
              <Note variant="coral" accessibilityRole="alert">
                {challengeErrorMessage(refusal.error)}
              </Note>
            ) : null}

            {/* One note above the pair rather than one per button, which would say the same
                thing twice about one connection. */}
            {online ? null : <Note variant="amber">{offlineMessage('does-not-resume')}</Note>}

            <View style={s.pair}>
              <Button
                label={NOT_THIS_TIME}
                variant="secondary"
                style={s.answerControl}
                busy={pressed === 'decline'}
                disabled={!online || answer.isPending}
                onPress={() => send('decline')}
              />
              <Button
                label={IM_IN}
                style={s.answerControl}
                busy={pressed === 'accept'}
                disabled={!online || answer.isPending}
                onPress={() => send('accept')}
              />
            </View>
          </View>
        ) : undefined
      }
    >
      <Text style={s.standing}>{sentence}</Text>

      {/* The organiser's own reading of the wait: §14's second sentence, once per seat, because
          the window is the seat's and a seat invited later starts its own day. */}
      {arm.kind === 'arranging' && arm.facts.side === 'organiser'
        ? seatsAwaiting(detail).map((seat, at) => (
            <Text key={`awaiting-${at}`} style={s.line}>
              {answerWindowLine({
                player: seat.player,
                duration: durationLeft(seat.answerBy, detail.readAt),
              })}
            </Text>
          ))
        : null}

      {/* The arrangement always answers, whatever the pairing could do — so the absence is a
          sentence in the cards' place and never a refusal to draw the screen. */}
      {cards && detail.pairingAbsence !== undefined ? (
        <Text style={s.line}>
          {pairingAbsenceLine(detail.pairingAbsence, sportLabel(detail.sport))}
        </Text>
      ) : null}

      {cards && forecast !== undefined ? (
        <View style={s.forecast}>
          <Text style={s.forecastHeading}>{forecastHeading(detail.seats.length)}</Text>
          {/* §B9's balance word beside the figure, because Part 13 forbids colour alone — and
              here there is no tint at all, so the word is the whole of it. `balanceReading` and
              not `balanceLabel`: the difference is one separator, and it is the difference
              between the two registers — a middot is a visual join, a comma is the pause a
              spoken clause needs. */}
          <Text style={s.line}>{balanceReading(forecast.pct)}</Text>

          {/* The word and its caveat are **two nodes and not one sentence**, which is
              `BuilderScreen`'s own shape: the caveat is the assumption's own line beneath the
              figure, and a join written here would be copy with no home in a deck. `null` covers
              *nothing was assumed* and *a code this build has no words for* alike, and the word
              above is what says there was one either way. */}
          {forecast.provisional ? <Text style={s.line}>{PROVISIONAL_WORD}</Text> : null}
          {forecast.provisional && forecast.assumption !== null ? (
            <Text style={s.line}>{forecastAssumption(forecast.assumption)}</Text>
          ) : null}
        </View>
      ) : null}

      {cards
        ? detail.seats.flatMap((seat, at) =>
            seat.card === undefined || seat.playerId === undefined
              ? []
              : [
                  <ChallengeCard
                    key={`seat-${at}`}
                    playerId={seat.playerId}
                    card={seat.card}
                    seats={detail.seats.length}
                  />,
                ],
          )
        : null}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  // The sibling state-keyed surface's own role: `GameScreen` draws its standing line at `h2`
  // over `ink`, and two screens whose whole job is stating a standing state it the same way.
  standing: { ...theme.type.h2, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  forecast: { gap: theme.space.xs },
  forecastHeading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  answers: { gap: theme.space.sm },
  pair: { flexDirection: 'row', gap: theme.space.sm },
  answerControl: { flex: 1 },
});
