/**
 * **A game still filling, in detail** — what a card or its **i**, a *You're In* row and a live yes
 * open (the screens A4.2, Q75; details mocks 5–10 for the layout;
 * [#553](https://github.com/Raketa02/Raketa/issues/553), [#557](https://github.com/Raketa02/Raketa/issues/557)).
 *
 * ```
 * ‹  [faces]  Karol Tomaszewski, Zofia Bielecka, Ania Kowalska
 *             Padel · filling
 * ┌ ● Filling · 1 of 4 in ─────────────────────┐   the dark card — the status, the tiles with IN,
 * │ [tile] [tile]  ── KAROL + YOU VS … ──       │   the vs line, and the court on an accent line:
 * │ [tile] [tile]                               │
 * │ ▎WHERE  Bonarka Arena  3,1 km               │   the club and its distance, never a court number
 * │ ▎DAY    Saturday 3 Oct                      │
 * │ ▎TIME   16:00  until 17:00                  │
 * │ ▎YOUR SHARE  32 zł  if it fills · book by … │   — while the club decides, on a line under
 * └─────────────────────────────────────────────┘     the share: Bonarka answers by 20:45 · Nobody
 *                                                     pays until it confirms
 * BALANCE FORECAST  [ You + Zofia │ Ania + Ewa ]  87% Very even
 * ┌ Slim overlap … the grid ────────────────────┐
 * Your yes costs nothing until everybody is in. …
 * [ I'm in ]  [ Not this time ]     — or [ Withdraw ], [ Leave the game ], [ Confirm your payment ]
 * ```
 *
 * ## One read, and the server says what the reader may do
 *
 * **`GET /proposals/{id}`** (#542) is the whole of it: who is In, the sides and their forecast, the
 * club and its distance, the share and the book-by, the overlap, the status — *Filling · 2 of 4
 * in*, *Waiting for the club* in amber, booked, or how it ended unfilled — and **`actions`, what the
 * reader may do now**, in the screen's order. **One status it cannot word alone**: a game its club
 * turned down names one status for the club's no and its silence, so its booking — the same id —
 * is read for which (`clubsAnswer`, Q105): *Kazimierz Padel said no* or *… didn't answer in time*,
 * and *Called off* until that read says. Nothing about the game is kept by the screen: every
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
 *   saved opens the payment setup first; on the last seat it counts ten seconds behind *Undo* —
 *   *I'm in* busy meanwhile — and a yes that books the game leaves this screen under *It's a game!*.
 *   What the last seat does is the deck's own rule read off the seats and the In count
 *   (`courtOfDetails`), because the details carry no court state.
 * - **Withdraw** while the reader is In — free and silent.
 * - **Leave the game** in its place while an On request club decides (A4.2, #543): the sheet says
 *   nobody has paid and leaving withdraws the yes, and it is sent as the withdrawal, which calls off
 *   the request to the club (`LeaveTheGame`, the booked game's door).
 * - **Confirm your payment** while the reader's seat waits on a refused share (#541): the fill's
 *   confirmation, on the payment the read names.
 *
 * **No Chat, no court number**: a game still filling has neither (A4.2). A game the reader was never
 * dealt is `proposal_not_found`, said in one sentence; before the read lands the screen waits with
 * the muted spinner, says it resumes while offline, and says why a read failed with the retry. An
 * answer given offline is held and sent on reconnect, and the amber note says so.
 */

import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { formatDistanceKm, formatPercent } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import {
  BALANCE_INK,
  BalanceBar,
  behindOverlay,
  Button,
  Card,
  courtSeatCount,
  Note,
  ScreenHeader,
  theme,
} from '@/shared/ui';
import { balanceLabel, balanceTone, balanceWord } from '@/shared/vocabulary/balancePresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import { foldOf, peopleOn, refusalOutcome, rowsOf, type DeckPerson } from '../domain/deck';
import { completesTheGame, yesOnDetails, type ProposalDetails } from '../domain/details';
import { LEAVING_WHILE_WAITING, answerByAhead } from '../domain/home';
import type { GameKind } from '../domain/vocabulary';
import { gameDayOf, weekdayAt } from '../domain/when';
import { useFillYes } from '../hooks/useFillYes';
import { useAnswerCard, useWithdrawYes } from '../hooks/useGroupDeck';
import { useLatest } from '../hooks/useLatest';
import { useBooking, useReadClock } from '../hooks/useHome';
import { useLeaveWhileWaiting, useProposal } from '../hooks/useProposal';

import {
  barLabels,
  clubName,
  detailsDay,
  detailsShareWords,
  detailsStatus,
  detailsSubline,
  othersTitle,
  refusalMessage,
  shareWords,
  timeWords,
} from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { PROPOSAL_STATUS_INK, clubsAnswer } from './homePresentation';
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
  // The club's no and its silence are one status here, and two on the booking (Q105).
  const turnedDown = details.status === 'TURNED_DOWN';
  const booking = useBooking(proposalId, { enabled: turnedDown }).data ?? undefined;
  const answered = turnedDown && booking !== undefined ? clubsAnswer(booking) : undefined;

  /** This game's yes is counting down behind *Undo*. */
  const counting = fill.counting === proposalId;
  /** Another booking counts, and this yes would move money too — one window at a time. */
  const held = !counting && fill.held(yesOn);
  /** An answer is on its way here — this game's yes counting down among them. */
  const busy = answer.isPending || withdraw.isPending || counting;
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

  // The read's clock — running while the club's deadline is ahead, so *answers by …* leaves the
  // money row by itself; otherwise standing at the read, since nothing else here runs out.
  const at = useReadClock(details.readAt, receivedAt, details.answerBy !== undefined);
  const seats = courtSeatCount(sport);
  const { top, bottom } = rowsOf(details, seats / 2);

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top']} {...behindOverlay(reading !== undefined)}>
        <ScreenHeader
          compact
          onBack={() => router.back()}
          backLabel={COPY.game.back}
          lead={<OthersFaces people={peopleOn(details)} />}
          title={othersTitle(details)}
          subline={detailsSubline(sport, details.status)}
        />
        <ScrollView contentContainerStyle={s.body}>
          <View style={s.game}>
            <GameGround />
            <View accessible accessibilityRole="header">
              <CardTag
                label={answered ?? detailsStatus(details.status, details.inCount, details.seats)}
                tone="grey"
                dot={PROPOSAL_STATUS_INK[details.status]}
              />
            </View>

            <GameTiles
              top={top}
              bottom={bottom}
              singles={seats === 2}
              completes={completesTheGame(details)}
              fill={false}
              onPerson={setReading}
            />

            <Facts details={details} at={at} />
          </View>

          {details.forecast === undefined ? null : (
            <Forecast
              pct={details.forecast.pct}
              fold={foldOf(details) ?? 0}
              labels={barLabels([top, bottom])}
            />
          )}

          <View style={s.grid}>
            <GameGround />
            <OverlapGrid overlap={details.overlap} today={weekdayAt(at)} />
          </View>

          {details.status === 'FILLING' ? (
            <Text style={s.meaning}>{COPY.game.whatAYesMeans}</Text>
          ) : null}

          {/* Held while offline, and sent when the connection returns. */}
          {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

          {actions.includes('YES') || actions.includes('NO') ? (
            <View style={s.answers}>
              {actions.includes('YES') ? (
                <Button
                  label={COPY.yes}
                  size="lg"
                  busy={counting || (answer.isPending && answer.variables?.said === 'yes')}
                  busyLabel={counting ? FILL_COPY.undo.booking : undefined}
                  disabled={held || (busy && !counting && answer.variables?.said !== 'yes')}
                  onPress={sayYes}
                />
              ) : null}
              {actions.includes('NO') ? (
                <Button
                  label={COPY.no}
                  variant="secondary"
                  size="lg"
                  busy={answer.isPending && answer.variables?.said === 'no'}
                  disabled={busy && answer.variables?.said !== 'no'}
                  onPress={sayNo}
                />
              ) : null}
            </View>
          ) : null}

          {actions.includes('WITHDRAW') ? (
            <Button
              label={COPY.game.withdraw}
              variant="secondary"
              size="lg"
              busy={withdraw.isPending}
              disabled={busy && !withdraw.isPending}
              onPress={() => withdraw.mutate(proposalId)}
            />
          ) : null}

          {actions.includes('LEAVE') ? (
            <LeaveTheGame leaving={LEAVING_WHILE_WAITING} act={leaveWaiting} />
          ) : null}

          {actions.includes('CONFIRM_PAYMENT') && details.yourPayment !== undefined ? (
            <Button
              label={FILL_COPY.confirm.title}
              size="lg"
              onPress={() => {
                if (details.yourPayment !== undefined) {
                  fill.confirm(details.yourPayment.seatChargeId, yesOn);
                }
              }}
            />
          ) : null}
        </ScrollView>
      </SafeAreaView>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
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
    answerByAhead(details, at),
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

/** BALANCE FORECAST on paper — the bar, your side left, and the figure with its word (details 9). */
function Forecast({
  pct,
  fold,
  labels,
}: {
  readonly pct: number;
  readonly fold: number;
  readonly labels: readonly [string, string];
}) {
  const tone = balanceTone(pct);
  return (
    <Card style={s.forecast}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {COPY.game.forecast}
      </Text>
      <BalanceBar
        advantage={fold}
        tone={tone}
        size="md"
        labels={labels}
        accessibilityLabel={balanceLabel(pct)}
      />
      <View style={s.reading} accessible accessibilityLabel={balanceLabel(pct)}>
        <Text style={[s.figure, { color: BALANCE_INK[tone] }]}>{formatPercent(pct)}</Text>
        <Text style={s.word}>{balanceWord(pct)}</Text>
      </View>
    </Card>
  );
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
  forecast: { gap: theme.space.sm },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  reading: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
  grid: { borderRadius: theme.radius.cardDark, overflow: 'hidden', padding: theme.space.md },
  meaning: { ...theme.type.tiny, color: theme.color.muted },
  answers: { gap: theme.space.sm },
});
