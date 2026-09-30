/**
 * **A game still filling, in detail** — what the card or its **i** opens (the screens A4.2, Q75;
 * details mocks 5–10 for the layout; [#553](https://github.com/Raketa02/Raketa/issues/553)).
 *
 * ```
 * ‹  [faces]  Karol Tomaszewski, Zofia Bielecka, Ania Kowalska
 *             Padel · filling
 * ┌ ● Filling · 1 of 4 in ─────────────────────┐   the dark card — the status, the tiles with IN,
 * │ [tile] [tile]  ── KAROL + YOU VS … ──       │   the vs line, and the court on an accent line:
 * │ [tile] [tile]                               │
 * │ ▎WHERE  Bonarka Arena                       │   the club, never a court number
 * │ ▎DAY    Saturday 3 Oct                      │
 * │ ▎TIME   16:00  until 17:00                  │
 * │ ▎YOUR SHARE  32 zł  if it fills · book by … │
 * └─────────────────────────────────────────────┘
 * BALANCE FORECAST  [ You + Zofia │ Ania + Ewa ]  87% Very even
 * ┌ Slim overlap … the grid ────────────────────┐
 * Your yes costs nothing until everybody is in. …
 * [ I'm in ]  [ Not this time ]     — or [ Withdraw ] once you are In
 * ```
 *
 * ## What it draws is the card the deck dealt
 *
 * There is no read of one proposal: the deck is the reader's view of every game dealt to them, and
 * the details are one card of it, found by id in the read for this group, sport and kind. **Once a
 * yes is said here the deck stops dealing the card** — a card you are In on is in *You're In*, not
 * the deck — so the screen keeps the card it last found for as long as it is open, with your tile
 * In and the game one yes further on (`withYourYes`), and *Withdraw* where the two answers were. A
 * withdraw puts the answers back. That memory is the screen's own and dies with it; nothing of the
 * read is copied anywhere a later screen could find it.
 *
 * **Withdraw follows *you are In*** (`youAreIn`) on the card as drawn, so it is there whenever the
 * reader's tile carries IN — after a yes here, or on a card the read ever deals with them In.
 *
 * ## A game you are already In on is drawn from your yes
 *
 * You › Payments' *LIVE YESES* open this screen too (#554), for games the deck **never** deals —
 * every one of them is a yes of yours. There is no read of one proposal yet (#542 serves it), so
 * when the deck has answered without the card the screen reads your live yeses and, finding the
 * game there, draws what the yes knows: the club as the title, *Filling*, WHERE · DAY · TIME · YOUR
 * SHARE, and *Withdraw*. No tiles, no forecast and no grid — who else is In is not on the yes, and
 * the screen draws nothing it cannot vouch for. A withdraw puts the answers back, and the deck,
 * read again, deals the game with everything on it. The yes found is kept while the screen is open,
 * as the card is.
 *
 * **A game this screen never found** — a link into a card the deck no longer deals and no yes of
 * yours names, a read that forgot it — says so in one sentence rather than drawing a game it cannot
 * vouch for. Before that is known the screen waits with the muted spinner, says the read resumes
 * while offline, and says why a read failed with the retry. An answer given offline is held and
 * sent on reconnect, and the amber note says so.
 *
 * ## Answers
 *
 * *I'm in* and *Not this time* are the deck's two answers, sent the same way and refused the same
 * way (`refusalMessage`, `refusalOutcome`): a refusal the player can mend is a toast and the
 * screen stays; a game that is over, full or no longer theirs is a toast and *back*, to a deck that
 * no longer holds it. *Not this time* is final, so it goes back too. Each button is busy while its
 * answer is in flight, and the other waits.
 *
 * **No Chat, no Leave**: a game still filling has neither (A4.2). *Waiting for the club* and its
 * *Leave the game* are the booked game's (#556, #557).
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { balanceLabel, balanceTone, balanceWord } from '@/features/play/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import {
  BALANCE_INK,
  BalanceBar,
  behindOverlay,
  Button,
  Card,
  courtSeatCount,
  Note,
  PlayerPhoto,
  ScreenHeader,
  theme,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';
import type { Weekday } from '@/shared/vocabulary/week';

import {
  completesIt,
  foldOf,
  peopleOn,
  refusalOutcome,
  rowsOf,
  withYourYes,
  youAreIn,
  type DeckCard,
  type DeckPerson,
} from '../domain/deck';
import type { LiveYes } from '../domain/liveYes';
import type { GameKind } from '../domain/vocabulary';
import { gameDayOf, weekdayAt, type GameDay } from '../domain/when';
import { useAnswerCard, useGroupDeck, useWithdrawYes } from '../hooks/useGroupDeck';
import { useLiveYeses } from '../hooks/useLiveYeses';

import {
  barLabels,
  clubName,
  detailsDay,
  detailsSubline,
  fillingStatus,
  othersTitle,
  refusalMessage,
  shareAside,
  shareWords,
  timeWords,
} from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';
import { CardTag } from './CardTag';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { OverlapGrid } from './OverlapGrid';
import { ReadFailed } from './ReadFailed';

const COPY = PROPOSALS_COPY;

/** How many of the other players' faces the header overlaps (details 7). */
const HEADER_FACES = 3;

export interface GameDetailsScreenProps {
  readonly groupId: string;
  readonly proposalId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
}

export function GameDetailsScreen({ groupId, proposalId, sport, kind }: GameDetailsScreenProps) {
  const { read } = useGroupDeck(groupId, sport, kind);
  const found = read.data?.cards.find((card) => card.proposalId === proposalId);

  // The card last found, kept while the screen is open — see the module note. Set during render
  // from the read, which is React's own shape for remembering what an earlier render saw.
  const [last, setLast] = useState<DeckCard | undefined>(found);
  if (found !== undefined && found !== last) setLast(found);
  const dealt = found ?? last;

  // Your own yes, for a game the deck does not deal because you are In on it — asked only once
  // the deck has answered without the card, and kept as the card is. See the module note.
  const yeses = useLiveYeses({ enabled: read.data !== undefined && dealt === undefined });
  const foundYes = yeses.data?.yeses.find((yes) => yes.proposalId === proposalId);
  const [lastYes, setLastYes] = useState<LiveYes | undefined>(foundYes);
  if (foundYes !== undefined && foundYes !== lastYes) setLastYes(foundYes);
  const yours = dealt === undefined ? (foundYes ?? lastYes) : undefined;

  /**
   * What you did here — a yes, or a yes taken back. The card as it stands after a yes is
   * `withYourYes`, because the deck stops dealing it; a withdraw is the read's again.
   */
  const [answered, setAnswered] = useState<'yes' | 'withdrawn' | undefined>(undefined);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  const refused = (error: AppError) => {
    showToast({ message: refusalMessage(error), tone: 'bad' });
    if (refusalOutcome(error.code) === 'gone') router.back();
  };
  const answer = useAnswerCard(groupId, refused);
  const withdraw = useWithdrawYes(groupId, refused);

  const readAt = read.dataUpdatedAt;
  const card =
    dealt === undefined
      ? undefined
      : answered === 'yes' && !youAreIn(dealt)
        ? withYourYes(dealt)
        : dealt;

  const busy = answer.isPending || withdraw.isPending;
  const paused = answer.isPaused || withdraw.isPaused;

  const sayYes = () =>
    answer.mutate({ proposalId, said: 'yes' }, { onSuccess: () => setAnswered('yes') });
  const sayNo = () => answer.mutate({ proposalId, said: 'no' }, { onSuccess: () => router.back() });
  const takeBack = () => withdraw.mutate(proposalId, { onSuccess: () => setAnswered('withdrawn') });

  /** *Withdraw* while you are In, the two answers otherwise — and the note while one is held. */
  const answers = (inNow: boolean) => (
    <>
      {/* Held while offline, and sent when the connection returns. */}
      {paused ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      {inNow ? (
        <Button
          label={COPY.game.withdraw}
          variant="secondary"
          size="lg"
          busy={withdraw.isPending}
          disabled={busy && !withdraw.isPending}
          onPress={takeBack}
        />
      ) : (
        <View style={s.answers}>
          <Button
            label={COPY.yes}
            size="lg"
            busy={answer.isPending && answer.variables?.said === 'yes'}
            disabled={busy && answer.variables?.said !== 'yes'}
            onPress={sayYes}
          />
          <Button
            label={COPY.no}
            variant="secondary"
            size="lg"
            busy={answer.isPending && answer.variables?.said === 'no'}
            disabled={busy && answer.variables?.said !== 'no'}
            onPress={sayNo}
          />
        </View>
      )}
    </>
  );

  if (card === undefined && yours !== undefined) {
    return (
      <SafeAreaView style={s.screen} edges={['top']}>
        <ScreenHeader
          compact
          onBack={() => router.back()}
          backLabel={COPY.game.back}
          title={clubName(yours)}
          subline={detailsSubline(sport)}
        />
        <ScrollView contentContainerStyle={s.body}>
          <View style={s.game}>
            <GameGround />
            <View accessible accessibilityRole="header">
              <CardTag label={COPY.game.filling} tone="grey" dot={theme.color.arranging} />
            </View>
            <Facts
              card={yours}
              day={gameDayOf(yours.startsAt, yeses.dataUpdatedAt)}
              deadlineDay={weekdayAt(yours.deadline)}
            />
          </View>

          <Text style={s.meaning}>{COPY.game.whatAYesMeans}</Text>

          {answers(answered !== 'withdrawn')}
        </ScrollView>
      </SafeAreaView>
    );
  }

  const header = (
    <ScreenHeader
      compact
      onBack={() => router.back()}
      backLabel={COPY.game.back}
      lead={card === undefined ? undefined : <Faces card={card} />}
      title={card === undefined ? undefined : othersTitle(card)}
      subline={card === undefined ? undefined : detailsSubline(sport)}
    />
  );

  if (card === undefined) {
    return (
      <SafeAreaView style={s.screen} edges={['top']}>
        {header}
        <View style={s.body}>
          {read.fetchStatus === 'paused' || yeses.fetchStatus === 'paused' ? (
            <Note variant="amber">{offlineMessage('resumes')}</Note>
          ) : read.isPending || yeses.fetchStatus === 'fetching' ? (
            <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
          ) : read.error !== null && read.data === undefined ? (
            <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
          ) : yeses.error !== null && yeses.data === undefined ? (
            <ReadFailed error={yeses.error} onRetry={() => void yeses.refetch()} />
          ) : (
            // Read, and neither among the cards nor your yeses: a game this screen cannot vouch for.
            <Note>{COPY.game.gone}</Note>
          )}
        </View>
      </SafeAreaView>
    );
  }

  const seats = courtSeatCount(sport);
  const { top, bottom } = rowsOf(card, seats / 2);
  const day = gameDayOf(card.startsAt, readAt);

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top']} {...behindOverlay(reading !== undefined)}>
        {header}
        <ScrollView contentContainerStyle={s.body}>
          <View style={s.game}>
            <GameGround />
            <View accessible accessibilityRole="header">
              <CardTag
                label={fillingStatus(card.inCount, seats)}
                tone="grey"
                // The stage still being arranged, the Now card's own dot for it.
                dot={theme.color.arranging}
              />
            </View>

            <GameTiles
              top={top}
              bottom={bottom}
              singles={seats === 2}
              completes={completesIt(card)}
              fill={false}
              onPerson={setReading}
            />

            <Facts card={card} day={day} deadlineDay={weekdayAt(card.deadline)} />
          </View>

          {card.forecast === undefined ? null : (
            <Forecast
              pct={card.forecast.pct}
              fold={foldOf(card) ?? 0}
              labels={barLabels([top, bottom])}
            />
          )}

          <View style={s.grid}>
            <GameGround />
            <OverlapGrid overlap={card.overlap} today={weekdayAt(readAt)} />
          </View>

          <Text style={s.meaning}>{COPY.game.whatAYesMeans}</Text>

          {answers(youAreIn(card))}
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

/** The other players' faces, overlapping, up to three (details 7). Decorative: the title names them. */
function Faces({ card }: { readonly card: DeckCard }) {
  const others = peopleOn(card)
    .filter((person) => !person.isYou)
    .slice(0, HEADER_FACES);
  return (
    <View
      style={s.faces}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {others.map((person, at) => (
        <View key={person.playerId} style={at > 0 ? s.overlap : undefined}>
          <PlayerPhoto
            playerId={person.playerId}
            {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
            box={{ kind: 'face', size: theme.size.groupPage.stackFace }}
          />
        </View>
      ))}
    </View>
  );
}

/** WHERE · DAY · TIME · YOUR SHARE, on an accent line (details 8), each one element to a listener. */
function Facts({
  card,
  day,
  deadlineDay,
}: {
  /** A dealt card, or your own yes on a game the deck no longer deals. */
  readonly card: Pick<DeckCard, 'club' | 'startsAt' | 'shareGrosze' | 'deadline'>;
  readonly day: GameDay | undefined;
  readonly deadlineDay: Weekday | undefined;
}) {
  const time = timeWords(card.startsAt);
  const when = day === undefined ? undefined : detailsDay(day, card.startsAt);
  const fact = (label: string, value: string, aside?: string) => (
    <View
      style={s.fact}
      accessible
      accessibilityLabel={[label, value, aside].filter((part) => part !== undefined).join(', ')}
    >
      <Text style={s.factLabel}>{label}</Text>
      <Text style={s.factLine}>
        <Text style={s.factValue}>{value}</Text>
        {aside === undefined ? null : <Text style={s.factAside}> {aside}</Text>}
      </Text>
    </View>
  );
  return (
    <View style={s.facts}>
      {fact(COPY.game.where, clubName(card))}
      {when === undefined ? null : fact(COPY.game.day, when.value, when.aside)}
      {fact(COPY.game.time, time.from, time.until)}
      {fact(COPY.game.share, shareWords(card), shareAside(card.deadline, deadlineDay))}
    </View>
  );
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
  facts: {
    borderLeftWidth: theme.size.gameCard.courtStroke,
    borderLeftColor: theme.color.arranging,
    paddingLeft: theme.space.md,
    gap: theme.space.sm,
  },
  fact: { gap: theme.space.xxs },
  factLabel: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
  },
  factLine: { ...theme.type.h1, color: theme.color.surface },
  factValue: { ...theme.type.h1, color: theme.color.surface },
  factAside: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  forecast: { gap: theme.space.sm },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  reading: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
  grid: { borderRadius: theme.radius.cardDark, overflow: 'hidden', padding: theme.space.md },
  meaning: { ...theme.type.tiny, color: theme.color.muted },
  answers: { gap: theme.space.sm },
  faces: { flexDirection: 'row' },
  overlap: { marginLeft: -theme.size.groupPage.stackOverlap },
});
