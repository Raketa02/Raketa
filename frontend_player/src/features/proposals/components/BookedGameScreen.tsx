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
 * │ ▎PAID   28 zł                               │   the money row's words always under
 * │ ▎       Paid · 27,18 zł back if you leave   │   the figure (`moneyRow`)
 * │ ▎       by Sat 10:00                        │
 * └─────────────────────────────────────────────┘
 * [ We played ]                                     the result, once the hour has come
 * BALANCE FORECAST …                                the Game's own forecast (details 9)
 * SHOW AT THE DESK  [QR]  K7M2QX                    on the game's day
 * ```
 *
 * **One read, `GET /bookings/{id}`, and nothing re-derived.** The status, the sides, the share and
 * whether it was paid, the cut-off, the club's deadline, whether the forecast is drawn, the
 * check-in code and what leaving costs are the server's (#542, #544, #614); what is decided here is
 * how they are drawn, and the clock the money row's *back if you leave by* and *answers by* run on
 * is the read's (`useReadClock`).
 *
 * ## Three readers, one screen (A4)
 *
 * - **A player in the game** — the card, the result, the forecast, the desk, and ***Leave the game***
 *   with the line saying what it costs now (`LeaveTheGame`, #557; details 10), drawn while the read
 *   says there is a button: not once the hour has come, nor on a game that is over.
 * - **A game waiting for the club** (A4.2, #543) — the same, *Waiting for the club* in amber, no
 *   court and no Chat, and *Bonarka answers by 20:45* under the share until that passes (Q98);
 *   *Leave the game* there withdraws the yes, nobody having paid.
 * - **A full game gone back to filling** (Q106, #629) — *Seat open* in amber, no court and no Chat,
 *   the share nobody pays over *1 seat open · Kazimierz Padel is asked again when it's full · nobody
 *   paid*; its way out is a game still filling's, ***Withdraw***, free and never on the record, as
 *   on a *You're In* row — no sheet in front of it, and back to Home, which no longer holds it.
 * - **A rescue seen from outside** (A4.3, #545) — opened from a *Seat open* card or a *Seats to fill*
 *   row, by a member the open seat is offered to: the players *paid*, the reader in the dashed seat
 *   that opened (*You complete it* on the last one, *You?* while more are open), the court, the share
 *   and how long the seat is offered, and a volt ***I'm in · 27 zł*** (`TakeTheSeat`) — no Chat, no
 *   Leave. Taking the seat leaves this screen for the group under *It's a game!*; a seat that has
 *   gone meanwhile says so in one sentence (`offer`).
 *
 * ## The chat is reached from here — and from Home's bubble
 *
 * **Chat** in the top bar opens the game's room (the mechanics §14.3) — found by the room join
 * keyed by the booking (`useBookingRoom`, #577), drawn while the join finds the room and the
 * status can have one (`chatIsOpen`) — the room's own life closes it as today, after the result as
 * well (§14.3). The room is pushed over this screen, so its back chevron returns here. The bubble
 * on the game's Home card is the room's other door (Q100, #619): it pushes the room straight over
 * Home, with no details under it, so Back from there is Home. **Chat · 2's
 * count, and its volt lit only when something is unread, are owed**: no read carries an unread
 * count, so the door is drawn volt, as the mock draws it, with no number (Part 16).
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
import { useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useCurrentUser } from '@/features/auth/types';
import { OPEN_THE_CHAT, useBookingRoom } from '@/features/conversations/types';
import { GameForecast } from '@/features/games/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import { behindOverlay, Button, courtSeatCount, ScreenHeader, theme } from '@/shared/ui';

import { peopleOn, rowsOf, type DeckPerson } from '../domain/deck';
import { yesOnRescue } from '../domain/fill';
import {
  chatIsOpen,
  completesTheRescue,
  isFillingAgain,
  lineCanRunOut,
  resultActOf,
  type BookedGame,
} from '../domain/home';
import { gameDayOf } from '../domain/when';
import { bookingReadState, useBooking, useOpenedGames, useReadClock } from '../hooks/useHome';
import { useLeaveBooking, useWithdrawFillingAgain } from '../hooks/useLeaveBooking';

import { CardTag } from './CardTag';
import { BookingAbsent } from './BookingAbsent';
import { CheckInCard } from './CheckInCard';
import { clubName, detailsDay, othersTitle, refusalMessage } from './deckPresentation';
import { GameFacts, type FactWords } from './GameFacts';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { HOME_GAME_COPY } from './homeCopy';
import { LeaveTheGame } from './LeaveTheGame';
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
import { PROPOSALS_COPY } from './proposalsCopy';
import { TakeTheSeat } from './TakeTheSeat';

const COPY = HOME_GAME_COPY.details;

export interface BookedGameScreenProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
  /**
   * Opened as a seat offered — from a *Seat open* card or a *Seats to fill* row, under the group
   * (#557). A booking the read no longer gives this reader is then a seat gone, said so.
   */
  readonly offer?: boolean;
}

export function BookedGameScreen({ bookingId, offer = false }: BookedGameScreenProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;
  const { open } = useOpenedGames();

  // Drawn here, so no longer *new* on Home (the mechanics §11.4) — a game the reader is in only:
  // a rescue seen from outside is nobody's Home yet.
  const drawn = game?.rescue === undefined ? game?.bookingId : undefined;
  useEffect(() => {
    if (drawn !== undefined) open(drawn);
  }, [drawn, open]);

  if (game === undefined) {
    // Not this player's game — or one in a sport this build cannot name — is the one sentence.
    return (
      <BookingAbsent
        read={bookingReadState(read)}
        gone={offer ? COPY.seatGone : COPY.gone}
        waiting={COPY.reading}
        edges={['top']}
      />
    );
  }

  return <Booked game={game} receivedAt={read.dataUpdatedAt} />;
}

function Booked({ game, receivedAt }: { readonly game: BookedGame; readonly receivedAt: number }) {
  const me = useCurrentUser().data?.id;
  const room = useBookingRoom(game.bookingId);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);
  const leave = useLeaveBooking(game.bookingId);
  const withdraw = useWithdrawFillingAgain(game.groupId, game.bookingId);

  // A seat taken from here leaves for the group — but only while this is still the screen on top:
  // the ten seconds can outlive it, and *back* from wherever the player went would be a stray.
  const here = useRef(true);
  useEffect(
    () => () => {
      here.current = false;
    },
    [],
  );

  // The money row's *back if you leave by* leaves by itself at the cut-off, *answers by* at the
  // club's deadline.
  const now = useReadClock(game.readAt, receivedAt, lineCanRunOut(game));

  const { rescue } = game;
  const ink = STATUS_INK[game.status];
  const seats = courtSeatCount(game.sport);
  const { top, bottom } = rowsOf(game, seats / 2);
  const day = gameDayOf(game.startsAt, now);
  const when = day === undefined ? undefined : detailsDay(day, game.startsAt);
  const time = bookedTime(game.startsAt, game.endsAt);
  const where = whereAside(game, game.where.distanceKm);
  const share = formatZloty(game.money.shareGrosze);
  const facts: readonly FactWords[] = [
    {
      label: COPY.where,
      value: clubName({ club: game.where }),
      ...(where === undefined ? {} : { aside: where }),
    },
    ...(when === undefined ? [] : [{ label: COPY.day, ...when }]),
    { label: COPY.time, value: time.from, aside: time.until },
    moneyRow(game, now),
  ];

  // Neither Chat nor Leave for a rescue seen from outside (A4.3): the reader is not in the game.
  const chat = rescue === undefined && chatIsOpen(game) ? room.conversationId : undefined;
  const act = resultActOf(game);

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
              // The last seat open: your yes completes it, as the card says (A2.3).
              completes={completesTheRescue(game)}
              fill={false}
              onPerson={setReading}
              {...(rescue === undefined ? {} : { rescue: { share } })}
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

          {game.showsForecast && me !== undefined && game.gameId !== undefined ? (
            <GameForecast gameId={game.gameId} playerId={me} />
          ) : null}

          {game.checkIn === undefined ? null : <CheckInCard checkIn={game.checkIn} />}

          {rescue === undefined ? null : (
            <TakeTheSeat
              seat={yesOnRescue({
                bookingId: game.bookingId,
                club: game.where,
                sides: game.sides,
              })}
              dealtIn={{ groupId: game.groupId, sport: game.sport, kind: game.kind }}
              share={share}
              size="lg"
              leave={() => {
                if (here.current) router.back();
              }}
            />
          )}

          {rescue !== undefined || game.leaving === undefined ? null : (
            <LeaveTheGame leaving={game.leaving} act={leave} afterLeaving={() => router.back()} />
          )}

          {rescue !== undefined || !isFillingAgain(game) ? null : (
            <Button
              label={PROPOSALS_COPY.game.withdraw}
              variant="secondary"
              size="lg"
              busy={withdraw.isPending}
              onPress={() =>
                withdraw.mutate(undefined, {
                  onSuccess: () => {
                    if (here.current) router.back();
                  },
                  onError: (error) => showToast({ message: refusalMessage(error), tone: 'bad' }),
                })
              }
            />
          )}
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
