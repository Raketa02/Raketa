/**
 * **A game still filling, in detail** — what a card or its **i**, a *You’re in* row and a live yes
 * open (the screens A4.2, Q75; details mocks 5–10 for the layout;
 * [#553](https://github.com/Rakieta02/Rakieta/issues/553), [#557](https://github.com/Rakieta02/Rakieta/issues/557);
 * the order is the For-fun mocks 3–6's since [#836](https://github.com/Rakieta02/Rakieta/issues/836)).
 *
 * ```
 * ‹  [faces]  karol.t, zofia.b, ania.k    — or *Only you*, alone on it
 *             Padel                                              the sport and kind: the tag is the state
 * ┌ BALANCE FORECAST ───────────────────────────┐   the top card, read first — a competitive game's
 * │ 2,65            gap −0,09             2,74 │   full forecast (`shared/ui`'s `ForecastBlock`,
 * │ [ You + Zofia ▓▓▓▓▓░░░░░░░░ Ania + Ewa ]   │   #839; for fun 3): both sides and the gap, the
 * │ 73%  Fairly even · A counted game — …      │   bar, the % and its word, the counted sentence,
 * │ [ If you win +0,08 ] [ If you lose −0,07 ] │   and the stakes — two tiles or none. Never on
 * └─────────────────────────────────────────────┘   For fun, which opens instead on
 * ┌ SOCIAL VIBE ────────────────────────────────┐   the Social vibe card (`shared/ui`'s
 * │ 67%  Good vibe                              │   `SocialVibeCard`, #840; for fun 7): the deck
 * │ [████████████████░░░░░░░░]                  │   card's %, its word and the bar below, then
 * │                  You  magda filip kuba      │   your tags' rows — a dot under each carrier,
 * │ ▌🍻 Stays for a drink  ●             ●      │   You first, then the tiles' order; a row
 * │  🔁 Here for a regular game ●               │   only you have in grey
 * └─────────────────────────────────────────────┘
 * ┌ ● Filling · 1 of 4 in ─────────────────────┐   the dark card — the status, the tiles with IN,
 * │ [tile] [tile]  ── KAROL + YOU VS … ──       │   the vs line, and the court on an accent line:
 * │ [tile] [tile]                               │
 * │ ▎WHERE  Bonarka Arena  3,1 km               │   the club and its distance, never a court number
 * │ ▎DAY    Saturday 3 Oct                      │
 * │ ▎TIME   16:00  until 17:00                  │
 * │ ▎YOUR SHARE  32 zł  if it fills · book by … │   — while one payment is awaited, on a line
 * │                                             │     under the share: Waiting for one payment ·
 * │ [ Not this time ] [        I'm in         ] │     until 14:40 · Nobody pays until it's in
 * └─────────────────────────────────────────────┘   the foot: Pay 32 zł on the last seat; or
 * ┌ Slim overlap … the grid ────────────────────┐   [ Withdraw ], [ Leave the game ], [ Confirm your
 *                                                    payment ] · who is free once two are In
 * ```
 *
 * ## One read, and the server says what the reader may do
 *
 * **`GET /proposals/{id}`** (#542) is the whole of it: who is In, the sides, the kind's own card — a
 * competitive game's forecast with both side strengths, the gap and what is at stake, or a For-fun
 * game's Social vibe with who at the table carries each of the reader's tags (#833) — the
 * club and its distance, the share and the book-by, the overlap, the status — *Filling · 2 of 4
 * in*, *Waiting for one payment* in amber, booked, or how it ended unfilled — and **`actions`, what
 * the reader may do now**, in the screen's order. *Waiting for one payment* (#625, #626; Q111)
 * carries *Waiting for one payment · until 14:40 · Nobody pays until it's in* under the share — and
 * to the payer *Confirm your payment by 14:40*, their own time, under it while it runs, there and on
 * a game gone back to filling meanwhile. Nothing about the game is kept by the screen: every
 * answer re-reads the details (`reread`), and each button is busy until the read has landed — so a
 * yes said here is drawn as the server has it, your tile In and *Withdraw* in place of the answers,
 * and a withdraw puts them back. A reader still deciding sees their own card as the deck deals it; a
 * reader In sees everybody In, the open seats empty.
 *
 * ## The actions
 *
 * - **I'm in / Not this time** — the deck's two answers, sent and refused the same way
 *   (`refusalMessage`, `refusalOutcome`): a refusal the player can mend is a toast and the screen
 *   stays; a game that is over, full or no longer theirs is a toast and *back*. *Not this time* is
 *   final, so it goes back too. **The fill is the deck's** (`useFillYes`): *I'm in* with nothing
 *   saved opens the payment setup first; on the last seat it reads ***Pay 32 zł***, because that yes
 *   books the game and moves money (Q124), and counts ten seconds behind *Undo* — busy meanwhile —
 *   and a yes that books the game leaves this screen under *It's a game!*. What the last seat does
 *   is the deck's own rule read off the seats and the In count (`courtOfDetails`), because the
 *   details carry no court state.
 * - **Withdraw** while the reader is In — free and silent.
 * - **Leave the game** in its place while the full game waits for one payment (#625): the sheet says
 *   nobody has paid and leaving withdraws the yes, and it is sent as the withdrawal, which puts the
 *   game back to filling (`LeaveTheGame`, the booked game's door).
 * - **Confirm your payment** while the reader's seat waits on a refused share (#541): the fill's
 *   confirmation, on the payment the read names, naming their time to pay while it runs (Q109).
 *
 * **No Chat, no court number**: a game still filling has neither (A4.2). A game the reader was never
 * dealt is `proposal_not_found`, said in one sentence; before the read lands the screen waits with
 * the muted spinner, says it resumes while offline, and says why a read failed with the retry. An
 * answer given offline is held and sent on reconnect, and the amber note says so.
 */

import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { formatDistanceKm } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import {
  behindOverlay,
  Button,
  courtSeatCount,
  ForecastBlock,
  Note,
  ScreenHeader,
  SocialVibeCard,
  theme,
  useTabBarReach,
} from '@/shared/ui';
import { COUNTED_GAME_SENTENCE } from '@/shared/vocabulary/forecastPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import { chargesAtOnce, peopleOn, refusalOutcome, rowsOf, type DeckPerson } from '../domain/deck';
import {
  completesTheGame,
  detailsCanRunOut,
  paymentDueOf,
  topCardOf,
  yesOnDetails,
  type ProposalDetails,
} from '../domain/details';
import { LEAVING_WHILE_WAITING, paymentWindowAt } from '../domain/home';
import type { GameKind } from '../domain/vocabulary';
import { gameDayOf, weekdayAt } from '../domain/when';
import { useFillYes } from '../hooks/useFillYes';
import { useAnswerCard, useWithdrawYes } from '../hooks/useGroupDeck';
import { useLatest } from '../hooks/useLatest';
import { useReadClock } from '../hooks/useHome';
import { useLeaveWhileWaiting, useProposal } from '../hooks/useProposal';

import {
  barLabels,
  clubName,
  detailsDay,
  detailsShareWords,
  detailsStatus,
  forecastSides,
  othersTitle,
  refusalMessage,
  shareWords,
  timeWords,
  yesButtonLabel,
} from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { PROPOSAL_STATUS_INK, sportWords } from './homePresentation';
import { PROPOSALS_COPY } from './proposalsCopy';
import { CardTag } from './CardTag';
import { GameFacts, type FactWords } from './GameFacts';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { LeaveTheGame } from './LeaveTheGame';
import { OthersFaces } from './OthersFaces';
import { OverlapGrid } from './OverlapGrid';
import { ReadFailed } from './ReadFailed';

const COPY = PROPOSALS_COPY;

export interface GameDetailsScreenProps {
  readonly groupId: string;
  readonly proposalId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
}

export function GameDetailsScreen({ groupId, proposalId, sport, kind }: GameDetailsScreenProps) {
  const read = useProposal(proposalId);
  const details = read.data ?? undefined;

  if (details === undefined) {
    // Never dealt to this reader — or in a sport this build cannot name: the one sentence.
    const gone = read.data === null || read.error?.code === 'proposal_not_found';
    return (
      <SafeAreaView style={s.screen} edges={['top']}>
        <ScreenHeader compact onBack={() => router.back()} backLabel={COPY.game.back} />
        <View style={s.body}>
          {read.fetchStatus === 'paused' ? (
            <Note variant="amber">{offlineMessage('resumes')}</Note>
          ) : gone ? (
            <Note>{COPY.game.gone}</Note>
          ) : read.error !== null ? (
            <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
          ) : (
            <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
          )}
        </View>
      </SafeAreaView>
    );
  }

  return (
    <Details
      details={details}
      groupId={groupId}
      sport={sport}
      kind={kind}
      receivedAt={read.dataUpdatedAt}
    />
  );
}

function Details({
  details,
  groupId,
  sport,
  kind,
  receivedAt,
}: {
  readonly details: ProposalDetails;
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly receivedAt: number;
}) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const { proposalId, actions } = details;
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  // A booked game leaves this screen — but only while it is still the one on screen: the ten
  // seconds can outlive it, and *back* from wherever the player went instead would be a stray.
  const here = useRef(true);
  useEffect(
    () => () => {
      here.current = false;
    },
    [],
  );
  const leave = () => {
    if (here.current) router.back();
  };
  const dealtIn = { groupId, sport, kind };
  const fill = useFillYes(dealtIn, leave);
  const yesOn = yesOnDetails(details);

  const refused = (error: AppError) => {
    showToast({ message: refusalMessage(error), tone: 'bad' });
    if (refusalOutcome(error.code) === 'gone') router.back();
  };
  const answer = useAnswerCard(
    groupId,
    (error, asked) => {
      if (fill.takesRefusal(error, asked, () => landYesLater.current())) return;
      refused(error);
    },
    fill.onAnswered,
  );
  const withdraw = useWithdrawYes(groupId, refused);
  const leaveWaiting = useLeaveWhileWaiting(groupId, proposalId);

  /**
   * This game's yes is booking: counting down behind *Undo*, and then on its way once the ten seconds
   * are up — _Booking…_ through both, never _Pay_ again while the money moves (`decisions.md` §3.3).
   */
  const booking = fill.counting === proposalId || fill.sending(proposalId);
  /** Another booking counts, and this yes would move money too — one window at a time. */
  const held = !booking && fill.held(yesOn);
  /** An answer is on its way here — this game's yes booking among them. */
  const busy = answer.isPending || withdraw.isPending || booking;
  const paused = answer.isPaused || withdraw.isPaused;

  /** The yes given: ten seconds behind *Undo* on the last seat, else sent at once. */
  const landYes = () => {
    if (fill.held(yesOn)) return;
    if (fill.waits(yesOn)) {
      fill.book(yesOn);
      return;
    }
    answer.mutate({ proposalId, said: 'yes', card: yesOn });
  };
  /** `landYes` as of the last render — what the setup's `then` and the fill's retry call. */
  const landYesLater = useLatest(landYes);

  /** *I'm in* — after the setup, when nothing is saved. */
  const sayYes = () => {
    if (busy || held) return;
    if (fill.setUpFirst(() => landYesLater.current())) return;
    landYes();
  };
  const sayNo = () => answer.mutate({ proposalId, said: 'no' }, { onSuccess: () => router.back() });

  // The read's clock — running while a time to pay is ahead, so *until …* leaves the money row by
  // itself; otherwise standing at the read, since nothing else here runs out.
  const at = useReadClock(details.readAt, receivedAt, detailsCanRunOut(details));
  const seats = courtSeatCount(sport);
  const { top, bottom } = rowsOf(details, seats / 2);
  const topCard = topCardOf(details);

  // What the card's foot draws — one of these, by the read's `actions`.
  const answering = actions.includes('YES') || actions.includes('NO');
  const withdrawing = actions.includes('WITHDRAW');
  const leaving = actions.includes('LEAVE');
  const confirming = actions.includes('CONFIRM_PAYMENT') ? details.yourPayment : undefined;

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top']} {...behindOverlay(reading !== undefined)}>
        <ScreenHeader
          compact
          onBack={() => router.back()}
          backLabel={COPY.game.back}
          lead={<OthersFaces people={peopleOn(details)} />}
          title={othersTitle(details) || COPY.game.onlyYou}
          subline={sportWords(sport, kind)}
        />
        <ScrollView
          contentContainerStyle={[s.body, { paddingBottom: reach + theme.size.gutter }]}
          testID="game-details"
        >
          {/* The top card, the kind's own: a competitive game's full forecast and what is at
              stake (#839), or a For-fun game's Social vibe card with its grid (#840). */}
          {topCard === undefined ? null : topCard.kind === 'vibe' ? (
            <SocialVibeCard grid={topCard.grid} />
          ) : (
            <ForecastBlock
              forecast={topCard.forecast}
              split={topCard.forecast.split}
              {...(topCard.atStake === undefined ? {} : { stake: topCard.atStake })}
              labels={barLabels([top, bottom])}
              names={forecastSides([top, bottom])}
              sentence={COUNTED_GAME_SENTENCE}
            />
          )}

          <View style={s.game} testID="game-details-card">
            <GameGround />
            <View accessible accessibilityRole="header">
              <CardTag
                label={detailsStatus(details.status, details.inCount, details.seats)}
                tone="grey"
                dot={PROPOSAL_STATUS_INK[details.status]}
              />
            </View>

            <GameTiles
              top={top}
              bottom={bottom}
              singles={seats === 2}
              completes={completesTheGame(details)}
              onPerson={setReading}
              // The forecast's split row says who partners whom; the Social vibe card does not,
              // nor does nothing at all — so there the vs line is spoken instead, said once.
              speaksSides={topCard?.kind !== 'forecast'}
            />

            <Facts details={details} at={at} />

            {/* Held while offline, and sent when the connection returns. */}
            {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

            {/* The card's foot: what the reader may do, right under the facts it answers. */}
            {answering || withdrawing || leaving || confirming ? (
              <View style={s.foot}>
                {answering ? (
                  // Side by side: Not this time on the left at its words' width, the yes the rest.
                  <View style={s.answers}>
                    {actions.includes('NO') ? (
                      <Button
                        label={COPY.no}
                        variant="secondary"
                        size="lg"
                        busy={answer.isPending && answer.variables?.said === 'no'}
                        disabled={busy && answer.variables?.said !== 'no'}
                        onPress={sayNo}
                        style={actions.includes('YES') ? s.beside : s.rest}
                      />
                    ) : null}
                    {actions.includes('YES') ? (
                      <Button
                        label={yesButtonLabel(chargesAtOnce(yesOn), shareWords(details))}
                        size="lg"
                        busy={booking || (answer.isPending && answer.variables?.said === 'yes')}
                        busyLabel={booking ? FILL_COPY.undo.booking : undefined}
                        disabled={held || (busy && !booking && answer.variables?.said !== 'yes')}
                        onPress={sayYes}
                        style={s.rest}
                      />
                    ) : null}
                  </View>
                ) : null}

                {withdrawing ? (
                  <Button
                    label={COPY.game.withdraw}
                    variant="secondary"
                    size="lg"
                    busy={withdraw.isPending}
                    disabled={busy && !withdraw.isPending}
                    onPress={() => withdraw.mutate(proposalId)}
                  />
                ) : null}

                {leaving ? (
                  <LeaveTheGame leaving={LEAVING_WHILE_WAITING} act={leaveWaiting} />
                ) : null}

                {confirming ? (
                  <Button
                    label={
                      FILL_COPY.confirm.title[
                        paymentWindowAt(confirming.confirmBy, confirming.timeTo, at)
                      ]
                    }
                    size="lg"
                    onPress={() => fill.confirm(confirming, yesOn)}
                  />
                ) : null}
              </View>
            ) : null}
          </View>

          {/* Who is free means something once somebody else is In to be free with. */}
          {details.inCount < 2 ? null : (
            <View style={s.grid}>
              <GameGround />
              <OverlapGrid overlap={details.overlap} today={weekdayAt(at)} />
            </View>
          )}
        </ScrollView>
      </SafeAreaView>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
          groupId={groupId}
        />
      )}
    </>
  );
}

/** WHERE · DAY · TIME · YOUR SHARE, on the stage's accent line (details 8). */
function Facts({ details, at }: { readonly details: ProposalDetails; readonly at: number }) {
  const card = { ...details, club: details.where };
  const day = gameDayOf(details.startsAt, at);
  const time = timeWords(details.startsAt);
  const when = day === undefined ? undefined : detailsDay(day, details.startsAt);
  const shareLines = detailsShareWords(
    details.status,
    card,
    weekdayAt(details.deadline),
    paymentDueOf(details, at),
  );
  const facts: readonly FactWords[] = [
    {
      label: COPY.game.where,
      value: clubName(card),
      ...(details.where.distanceKm === undefined
        ? {}
        : { aside: formatDistanceKm(details.where.distanceKm) }),
    },
    ...(when === undefined ? [] : [{ label: COPY.game.day, ...when }]),
    { label: COPY.game.time, value: time.from, aside: time.until },
    {
      label: COPY.game.share,
      value: shareWords(details),
      ...shareLines,
    },
  ];
  return <GameFacts facts={facts} accent={PROPOSAL_STATUS_INK[details.status]} />;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
  game: {
    borderRadius: theme.radius.cardDark,
    overflow: 'hidden',
    padding: theme.space.md,
    gap: theme.space.md,
  },
  grid: { borderRadius: theme.radius.cardDark, overflow: 'hidden', padding: theme.space.md },
  foot: { gap: theme.space.sm },
  answers: { flexDirection: 'row', gap: theme.space.sm },
  /**
   * *Not this time* at its words' width, and the yes takes the rest — either alone takes the row.
   * Both shrink, by their widths, where large type would make the two overflow: React Native's
   * `flexShrink` is 0 by default, which would squeeze the yes alone.
   */
  beside: { flexShrink: 1 },
  rest: { flexGrow: 1, flexShrink: 1 },
});
