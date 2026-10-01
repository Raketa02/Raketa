/**
 * **A booked game you're in, in detail** — what Home's *Open game* and *It's a game!*'s *Open game*
 * open ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, details 5–10; the
 * mechanics §14.2, §15.1).
 *
 * ```
 * ‹  [faces]  Piotr Sowa, Inés Díaz, Bartek Lis              [ Chat ]   the top bar (details 7)
 *             Padel · booked
 * ┌ ● Booked ──────────────────────────────────┐   the game card (details 8): the status,
 * │ [You · 2,71 · paid]  [Piotr · 2,95 · paid] │   the tiles with *paid*, the vs line,
 * │ ── YOU + PIOTR VS INÉS + BARTEK ──          │
 * │ [Inés · 3,40 · paid] [Bartek · 2,35 · paid]│
 * │ ▎WHERE  Bonarka Arena  Court 2 · 3,1 km     │   and the court on the status's accent line
 * │ ▎DAY    Sunday  20 Sep                      │
 * │ ▎TIME   10:00  until 11:00                  │
 * │ ▎PAID   28 zł  your share · to the club …   │
 * └─────────────────────────────────────────────┘
 * [ We played ]                                     the result, once the hour has come
 * BALANCE FORECAST …                                the Game's own forecast (details 9)
 * SHOW AT THE DESK  [QR]  K7M2QX                    on the game's day
 * ```
 *
 * **One read, `GET /bookings/{id}`, and nothing re-derived.** The status, the sides, the share and
 * whether it was paid, the cut-off, whether the forecast is drawn and the check-in code are the
 * server's (#542); what is decided here is how they are drawn, and the clock the money row's
 * *free to leave until* runs on is the read's (`useReadClock`). *Leave the game* is #557's.
 *
 * ## The chat is reached from here, and only from here
 *
 * **Chat** in the top bar opens the game's room (the mechanics §14.3) — found by the room join
 * keyed by the game (`useGameRoom`), drawn while the join finds the room and the status can have
 * one (`chatIsOpen`) — the room's own life closes it as today, after the result as well (§14.3). The
 * room is pushed over this screen, so its back chevron returns here. **Chat · 2's count, and its volt lit only when something is unread, are
 * owed**: no read carries an unread count, so the door is drawn volt, as the mock draws it, with
 * no number (Part 16).
 *
 * ## The result is today's
 *
 * The result states are unchanged from today (§14.1), so once the hour has come the details offer
 * today's act — *We played*, or *Confirm the result* once a score is on the table — and it opens
 * today's game screen over these details, where the result is told and agreed.
 *
 * ## Opening it is what makes a game not *new*
 *
 * Home marks a game that filled since you last looked *new until opened* (§11.4): once a booked
 * game has been drawn here, this phone keeps it as opened (`useOpenedGames`).
 *
 * A booking nobody may see, or one this player has no seat on, is `booking_not_found` and says so
 * in one sentence; a read in flight is the muted spinner, offline says it resumes, and any other
 * failure says why with the retry.
 */

import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import { OPEN_THE_CHAT, useGameRoom } from '@/features/conversations/types';
import { GameForecast } from '@/features/games/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay, Button, courtSeatCount, ScreenHeader, theme } from '@/shared/ui';

import { peopleOn, rowsOf, type DeckPerson } from '../domain/deck';
import { chatIsOpen, resultActOf, type BookedGame } from '../domain/home';
import { gameDayOf } from '../domain/when';
import { bookingReadState, useBooking, useOpenedGames, useReadClock } from '../hooks/useHome';

import { CardTag } from './CardTag';
import { BookingAbsent } from './BookingAbsent';
import { CheckInCard } from './CheckInCard';
import { clubName, detailsDay, othersTitle } from './deckPresentation';
import { GameFacts, type FactWords } from './GameFacts';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { HOME_GAME_COPY } from './homeCopy';
import {
  STATUS_INK,
  bookedTime,
  moneyRow,
  statusSubline,
  statusWord,
  whereAside,
} from './homePresentation';
import { OthersFaces } from './OthersFaces';
import { bookedChatRoute, bookedResultRoute } from './proposalRoutes';

const COPY = HOME_GAME_COPY.details;

export interface BookedGameScreenProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
}

export function BookedGameScreen({ bookingId }: BookedGameScreenProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;
  const { open } = useOpenedGames();

  // Drawn here, so no longer *new* on Home (the mechanics §11.4).
  const drawn = game?.bookingId;
  useEffect(() => {
    if (drawn !== undefined) open(drawn);
  }, [drawn, open]);

  if (game === undefined) {
    // Not this player's game — or one in a sport this build cannot name — is the one sentence.
    return (
      <BookingAbsent
        read={bookingReadState(read)}
        gone={COPY.gone}
        waiting={COPY.reading}
        edges={['top']}
      />
    );
  }

  return <Booked game={game} receivedAt={read.dataUpdatedAt} />;
}

function Booked({ game, receivedAt }: { readonly game: BookedGame; readonly receivedAt: number }) {
  const me = useCurrentUser().data?.id;
  const room = useGameRoom(game.gameId);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  // The money row's *free to leave until* leaves by itself at the cut-off.
  const now = useReadClock(game.readAt, receivedAt, game.money.freeToLeaveUntil !== undefined);

  const ink = STATUS_INK[game.status];
  const seats = courtSeatCount(game.sport);
  const { top, bottom } = rowsOf(game, seats / 2);
  const day = gameDayOf(game.startsAt, now);
  const when = day === undefined ? undefined : detailsDay(day, game.startsAt);
  const time = bookedTime(game.startsAt, game.endsAt);
  const where = whereAside(game, game.where.distanceKm);
  const facts: readonly FactWords[] = [
    {
      label: COPY.where,
      value: clubName({ club: game.where }),
      ...(where === undefined ? {} : { aside: where }),
    },
    ...(when === undefined ? [] : [{ label: COPY.day, ...when }]),
    { label: COPY.time, value: time.from, aside: time.until },
    moneyRow(game, seats, now),
  ];

  const chat = chatIsOpen(game.status) ? room.conversationId : undefined;
  const act = resultActOf(game.status);

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top']} {...behindOverlay(reading !== undefined)}>
        <ScreenHeader
          compact
          onBack={() => router.back()}
          backLabel={COPY.back}
          lead={<OthersFaces people={peopleOn(game)} />}
          title={othersTitle(game)}
          subline={statusSubline(game.sport, game.status)}
          {...(chat === undefined
            ? {}
            : {
                right: (
                  <Button
                    label={COPY.chat}
                    accessibilityLabel={OPEN_THE_CHAT}
                    variant="volt"
                    size="sm"
                    onPress={() => router.push(bookedChatRoute(game.bookingId))}
                  />
                ),
              })}
        />
        <ScrollView contentContainerStyle={s.body}>
          <View style={s.game}>
            <GameGround />
            <View accessible accessibilityRole="header">
              <CardTag label={statusWord(game.status)} tone="grey" dot={ink} />
            </View>

            <GameTiles
              top={top}
              bottom={bottom}
              singles={seats === 2}
              completes={false}
              fill={false}
              onPerson={setReading}
            />

            <GameFacts facts={facts} accent={ink} />
          </View>

          {act === undefined ? null : (
            <Button
              label={COPY.resultAct[act]}
              size="lg"
              onPress={() => router.push(bookedResultRoute(game.bookingId))}
            />
          )}

          {game.showsForecast && me !== undefined ? (
            <GameForecast gameId={game.gameId} playerId={me} />
          ) : null}

          {game.checkIn === undefined ? null : <CheckInCard checkIn={game.checkIn} />}
        </ScrollView>
      </SafeAreaView>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={game.sport}
        />
      )}
    </>
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
});
