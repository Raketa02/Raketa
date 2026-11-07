/**
 * **The friends card** — a fixed line-up's card under a group's Friends court: the deck's card
 * without its tiles ([#757](https://github.com/Raketa02/Raketa/issues/757); the friends screens
 * §7.2; friends 8, 9).
 *
 * ```
 * ┌───────────────────────────────────────────┐
 * │ ──── YOU + EWA  VS  MAGDA + ANIA ────     │  the sides, the court's own (README note 3)
 * │                  87%                      │  the server's figure, its colour the bar's tone
 * │               Very even                   │
 * │ [ You + Ewa         │  Magda + Ania ]     │  your side on the left (Q70)
 * │              Slim overlap                 │  OverlapGrid — the deck's
 * │  M  T  W  T  F  S  S …                    │
 * │ ┌ Court available          25 zł each ┐  │  CourtBlock, *Book it now*'s bed: sending books it
 * │ │ Saturday 10:00 · Wisła Park · Court 3 │  │
 * │ └ Ogrody 33 is full at 10:00           ┘  │  another club's court only
 * │ [       Send game and pay 25 zł        ]  │  → the send sheet (#759)
 * │ [        Pick a different court        ]  │  → Find a court
 * └───────────────────────────────────────────┘
 * ```
 *
 * **Every part is the deck card's own** — the ground (`GameGround`), the *vs* line, the forecast's
 * figure and bar, the overlap grid and the court block — laid out as friends 9 draws them: the
 * figure over its word, the bar the card's width. No ribbon (nothing counts down), no tiles (the
 * court above draws the faces), and **no shadow**: the deck card floats on its stage, this one sits
 * in the page's column, and cards never cast one (4.3). **Send game and pay 25 zł** (volt, friends 8)
 * opens the send sheet (`SendGame`, #759); sent, the court goes back to empty (`onSent`).
 *
 * ## Every state has its drawing
 *
 * - **Read** — the card; or, with no court in the next 14 days, that one line and nothing to pick.
 * - **On its way** — the card's frame with a quiet line and nothing to press (the screens §7.2,
 *   designed, no mock): a swap, a court or a kind asks again, and the card that answered the last
 *   question is never drawn for the new one.
 * - **Refused** — the line-up's own sentence in the card's place, naming nobody (the mechanics
 *   §7.5). **A court picked that is no longer for sale** (`court_hour_not_for_sale`) is handed back
 *   (`onCourtGone`) and the card asks again for one it proposes.
 * - **Failed otherwise, or offline** — why, with *Try again*, never an empty frame.
 * - **A send refused for its court** (#759) — `court_just_taken` reads the card again, and the
 *   court's sentence stands above it until the next court, kind or send.
 *
 * **The people are the composer's**: the card is read by id, and every face on it is a friend the
 * picker drew (`CardPerson`) — so this feature imports nothing of `friends`.
 */

import { useEffect, useState, type ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { BalanceBar, Button, Note, courtSeatCount, theme } from '@/shared/ui';
import { balanceTone, balanceWord } from '@/shared/vocabulary/balancePresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import { foldOf, rowsOf } from '../domain/deck';
import {
  isCourtGone,
  refusalOf,
  sidesOn,
  type CardPerson,
  type FriendsCard as Card,
  type FriendsCardAsk,
  type FriendsCourt,
  type FriendsCourtPick,
} from '../domain/friendsCard';
import { gameDayOf, weekdayAt } from '../domain/when';
import { useFriendsCard } from '../hooks/useFriendsCard';

import { CourtBlock } from './CourtBlock';
import { barLabels, forecastSpoken, vsLine } from './deckPresentation';
import { FindACourtSheet } from './FindACourtSheet';
import { FRIENDS_CARD_COPY } from './friendsCardCopy';
import { courtShare, fullAtLine, refusalLine } from './friendsCardPresentation';
import { FORECAST_FIGURE } from './GameCard';
import { GameGround } from './GameGround';
import { OverlapGrid } from './OverlapGrid';
import { ReadFailed } from './ReadFailed';
import { SendGame } from './SendGame';

const COPY = FRIENDS_CARD_COPY;

export interface FriendsCardProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** The line-up as the court holds it — every seat filled. */
  readonly ask: FriendsCardAsk;
  /** The friends seated: their whole nicknames and Levels in the sport, as the picker read them. */
  readonly people: readonly CardPerson[];
  /** The reader — *You* on the card and in *Find a court*'s busy lines. */
  readonly readerId: string | undefined;
  readonly yourLevel: number | undefined;
  /** A row picked in *Find a court*: the composer holds it, and the card asks again for it. */
  readonly onPickCourt: (court: FriendsCourtPick) => void;
  /** The court picked is no longer for sale: the composer lets it go, and the card proposes one. */
  readonly onCourtGone: () => void;
  /** **Sent** (#759): the court booked, the game in Your games — the composer empties the court. */
  readonly onSent: () => void;
}

export function FriendsCard({
  groupId,
  sport,
  ask,
  people,
  readerId,
  yourLevel,
  onPickCourt,
  onCourtGone,
  onSent,
}: FriendsCardProps) {
  const read = useFriendsCard(groupId, sport, ask);
  const [finding, setFinding] = useState(false);
  // A send refused for its court says so above the card read again — for as long as the line-up
  // asks what it asked then: a swap, a kind or a court is a new question, and the line goes.
  const asking = askKey(ask);
  const [said, setSaid] = useState<{ readonly line: string; readonly for: string }>();
  const courtLine = said?.for === asking ? said.line : undefined;
  const code = read.error?.code;
  const gone = isCourtGone(code) && ask.court !== undefined;

  useEffect(() => {
    if (gone) onCourtGone();
  }, [gone, onCourtGone]);

  const card = read.data;
  const seats = courtSeatCount(sport);

  if (card === undefined) {
    if (read.fetchStatus === 'paused') {
      return <Note variant="amber">{offlineMessage('resumes')}</Note>;
    }
    const refusal = refusalOf(code);
    if (refusal !== undefined) {
      return (
        <Note variant="amber" accessibilityRole="alert">
          {refusalLine(refusal, sport, seats)}
        </Note>
      );
    }
    if (read.error !== null && !read.isFetching && !gone) {
      return <ReadFailed error={read.error} onRetry={() => void read.refetch()} />;
    }
    return <Building />;
  }

  if (card.court === undefined || card.overlap === undefined) {
    return <Note>{COPY.noCourt}</Note>;
  }

  return (
    <>
      {courtLine === undefined ? null : (
        <Note variant="amber" accessibilityRole="alert">
          {courtLine}
        </Note>
      )}
      <ReadCard
        card={card}
        court={card.court}
        overlap={card.overlap}
        people={people}
        yourLevel={yourLevel}
        seatsPerSide={seats / 2}
        readAt={read.dataUpdatedAt}
        onFind={() => setFinding(true)}
        send={
          <SendGame
            // A new line-up or court is a new send: nothing booked under the last one carries over.
            key={`${asking}|${card.court.courtId}|${card.court.startsAt}`}
            groupId={groupId}
            sport={sport}
            ask={ask}
            court={card.court}
            cutOff={card.cutOff}
            onSent={onSent}
            onReread={(line) => {
              setSaid(line === undefined ? undefined : { line, for: asking });
              void read.refetch();
            }}
            onCourtGone={(line) => {
              if (ask.court === undefined) {
                setSaid({ line, for: asking });
                void read.refetch();
                return;
              }
              // The court picked is let go, and the card asks for one it proposes.
              setSaid({ line, for: askKey({ ...ask, court: undefined }) });
              onCourtGone();
            }}
          />
        }
      />
      <FindACourtSheet
        visible={finding}
        onClose={() => setFinding(false)}
        groupId={groupId}
        sport={sport}
        friendIds={ask.friendIds}
        people={people}
        readerId={readerId}
        shown={card.court}
        onPick={(court) => {
          setFinding(false);
          onPickCourt({ courtId: court.courtId, startsAt: court.startsAt });
        }}
      />
    </>
  );
}

/** A line-up's question as one value — what the court's line is said for. */
function askKey(ask: FriendsCardAsk): string {
  return JSON.stringify([ask.kind, ask.friendIds, ask.partnerId, ask.court]);
}

/** The card's frame while it is read — a quiet line, nothing to press. */
function Building() {
  return (
    <View style={s.card} testID="friends-card-building">
      <GameGround />
      <View style={s.building} accessible accessibilityLabel={COPY.building}>
        <ActivityIndicator color={theme.color.onDarkTiny} />
        <Text style={s.quiet}>{COPY.building}</Text>
      </View>
    </View>
  );
}

function ReadCard({
  card,
  court,
  overlap,
  people,
  yourLevel,
  seatsPerSide,
  readAt,
  onFind,
  send,
}: {
  readonly card: Card;
  readonly court: FriendsCourt;
  readonly overlap: NonNullable<Card['overlap']>;
  readonly people: readonly CardPerson[];
  readonly yourLevel: number | undefined;
  readonly seatsPerSide: number;
  readonly readAt: number;
  readonly onFind: () => void;
  /** *Send game and pay 25 zł* and its sheet (#759). */
  readonly send: ReactNode;
}) {
  const sides = { sides: sidesOn(card, people, yourLevel) };
  const { top, bottom } = rowsOf(sides, seatsPerSide);
  const labels = barLabels([top, bottom]);
  const marker = fullAtLine(court, card.homeClub);

  return (
    <View style={s.card} testID="friends-card">
      <GameGround />
      <View style={s.body}>
        {/* The sides as a line. Decorative to a listener: the forecast's name says them. */}
        <View
          style={s.vs}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        >
          <View style={s.rule} />
          <Text style={s.vsWords} numberOfLines={1}>
            {vsLine(top, bottom)}
          </Text>
          <View style={s.rule} />
        </View>

        {card.forecast === undefined ? null : (
          <Forecast pct={card.forecast.pct} fold={foldOf(sides) ?? 0} labels={labels} />
        )}

        <OverlapGrid overlap={overlap} today={weekdayAt(readAt)} />

        <CourtBlock
          tag="bookItNow"
          day={gameDayOf(court.startsAt, readAt)}
          card={{ ...court, noFreeCancellation: false }}
          label={COPY.courtAvailable}
          share={courtShare(court)}
          {...(marker === undefined ? {} : { marker })}
        />

        {send}

        <Button
          label={COPY.pickACourt}
          accessibilityHint={COPY.pickACourtHint}
          variant="onDark"
          size="lg"
          onPress={onFind}
        />
      </View>
    </View>
  );
}

/**
 * *87%* over *Very even*, and the bar the card's width under them — friends 9's layout of the deck
 * card's forecast. One element, named by the word, the figure and the sides.
 */
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
  const spoken = forecastSpoken(pct, labels);
  return (
    <View
      style={s.forecast}
      accessible
      accessibilityRole="image"
      accessibilityLabel={spoken}
      testID="friends-card-forecast"
    >
      <Text style={[s.figure, { color: FORECAST_FIGURE[tone] }]}>{formatPercent(pct)}</Text>
      <Text style={s.word}>{balanceWord(pct)}</Text>
      <View
        style={s.bar}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <BalanceBar
          advantage={fold}
          tone={tone}
          size="md"
          variant="onDark"
          labels={labels}
          accessibilityLabel={spoken}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: theme.radius.deckCard, overflow: 'hidden', alignSelf: 'stretch' },
  body: { padding: theme.space.md, gap: theme.space.md },
  building: {
    padding: theme.space.xl,
    alignItems: 'center',
    gap: theme.space.sm,
  },
  quiet: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
  vs: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  rule: { flex: 1, height: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  vsWords: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    flexShrink: 1,
  },
  forecast: { alignItems: 'center', gap: theme.space.xs },
  figure: { ...theme.num.xl, ...theme.tabular },
  word: { ...theme.type.h2, color: theme.color.surface },
  bar: { alignSelf: 'stretch', marginTop: theme.space.xs },
});
