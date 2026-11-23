/**
 * **A booked game you're in, in detail** — what Home's *Open game* and *It's a game!*'s *Open game*
 * open ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, details 5–10; the
 * mechanics §14.2).
 *
 * ```
 * ‹  [faces]  piotr.s, ines.d, bartek.l              [ Chat ]   the top bar (details 7)
 *             Padel                                    the sport and kind: the tag is the state
 * ┌ ● Booked ──────────────────────────────────┐   the game card (details 8): the status,
 * │ [You · 2,71 · paid]  [Piotr · 2,95 · paid] │   the tiles with *paid*, the vs line,
 * │ ── YOU + PIOTR VS INÉS + BARTEK ──          │
 * │ [Inés · 3,40 · paid] [Bartek · 2,35 · paid]│
 * │ ▎WHERE  Bonarka Arena  Court 2 · 3,1 km     │   and the court on the status's accent line
 * │ ▎DAY    Sunday  20 Sep                      │
 * │ ▎TIME   10:00  until 11:00                  │
 * │ ▎YOUR SHARE  28 zł                          │   the money row's words always under
 * │ ▎       Held on your card · taken Sat 10:00 │   the figure (`moneyRow`)
 * │ ▎       · free to leave until then          │
 * └─────────────────────────────────────────────┘
 * [ We played ]                                     the result, once the hour has come
 * BALANCE FORECAST …  /  SOCIAL VIBE …              the Game's own pairing, as its kind's card
 * ```
 *
 * **The pairing's card is the kind's** (#841, ADR-0207 §5): a competitive game draws the Balance
 * forecast and its stakes, as it always did; **a For-fun game draws the Social vibe card** its
 * details opened on before the last yes, where *A friendly — nothing moves.* stood — so a For-fun
 * game reads the same before and after it is booked, and at the court. It is `games`'
 * `GamePairingCard`, drawn on the same occasions as the forecast was (`showsForecast`); its columns
 * are the tiles' own people, in the tiles' order (`vibeColumnsOf`), and on For fun the vs line is
 * spoken, since the vibe card does not say who partners whom and the forecast's split row did.
 *
 * **Nothing to show at the desk** (ADR-0195): players walk straight to the court, so the details
 * carry no QR code and no check-in code, on the game's day or any other.
 *
 * **One read, `GET /bookings/{id}`, and nothing re-derived.** The status, the sides, the share and
 * whether it was paid, the cut-off, whether the forecast is drawn and what leaving costs are the
 * server's (#542, #544); what is decided here is how they are drawn, and the clock the money row's
 * *held from*, *taken* and *until* run on is the read's (`useReadClock`).
 *
 * **A friends game** (#759; the friends screens §9) adds its seats under the facts — *In*, *waiting ·
 * 21 h 00 left*, *can't make it*, *didn't answer*, *empty*, *Seat open* (`FriendsSeats`) — its pay
 * mode under the price (*Split* or *tomek.k paid the court*, `moneyRow`). **An empty seat** (#760)
 * offers ***Invite a friend*** to anyone In — the picker with one seat, pushed over these details —
 * and ***Open to {group}*** to the sender before the cut-off, behind its confirmation; the group's
 * name is the composer's (`groupName`), since `groups` reads this feature. **The sender's way out
 * before the cut-off is one door, *Leave or call it off*** (`SendersLeave`), whose sheet is two
 * ways: *Call it off for everyone* and *Leave · the others play on* — the only place a sender calls
 * it off (2026-11-07); after the cut-off, the ordinary late leave.
 *
 * ## Three readers, one screen (A4)
 *
 * - **A player in the game** — the card, the result, the forecast, and ***Leave the game***
 *   with the line saying what it costs now (`LeaveTheGame`, #557; details 10), drawn while the read
 *   says there is a button: not once the hour has come, nor on a game that is over.
 * - **A game waiting for one payment** (Q111, #630) — *Waiting for one payment* in amber, no court
 *   and no Chat, the share nobody pays yet over *Waiting for one payment · until 14:40 · Nobody pays
 *   until it's in*; *Leave the game* withdraws the yes, nobody having paid. **The payer** reads their
 *   own time there, *Confirm your payment by 14:40*, and ***Confirm your payment*** under the card —
 *   the payment their *TO CONFIRM* row holds for this game, opened on the fill's confirmation with
 *   the same time — so the details that name the time also offer the act. Before the club's cut-off
 *   it is their time to fix the card (Q113): *Fix your card by 14:40* and ***Fix your card***.
 * - **A booked game whose holding was refused** (#639; Q113) — still *Booked*, the others' cards
 *   unchanged; its player's money row reads *Fix your card by 14:40 to keep your seat*, and ***Fix
 *   your card*** under the card opens the same confirmation.
 * - **A full game gone back to filling** (Q106, #629) — *Seat open* in amber, no court and no Chat,
 *   the share nobody pays over *1 seat open · books when it's full · nobody paid*; its way out is a game still filling's, ***Withdraw***, free and never on the record, as
 *   on a *You’re in* row — no sheet in front of it, and back to Home, which no longer holds it.
 * - **A rescue seen from outside** (A4.3, #545) — opened from a *Seat open* card or a *Seats to fill*
 *   row, by a member the open seat is offered to: the players *paid*, the reader in the dashed seat
 *   that opened (*You complete it* on the last one, *You?* while more are open), the court, the share
 *   and how long the seat is offered, and a volt ***Pay 27 zł*** (`TakeTheSeat`, Q124) — no Chat, no
 *   Leave. Taking the seat leaves this screen for the group under *It's a game!*; a seat that has
 *   gone meanwhile says so in one sentence (`offer`). **A rescuer whose card was refused** (#640)
 *   reads their kept seat's time, *Fix your card by 14:40 to take the seat*, and while their *TO
 *   CONFIRM* row holds the payment, ***Fix your card*** (or ***Confirm your payment*** after the
 *   cut-off) stands where *Pay* stood: the join again is that confirmation.
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
 * today's game screen over these details, where the result is told and agreed. **In the first half
 * hour the door is *Who's here*** (#658): the same screen, where a player at the court says who
 * isn't here yet and an awaited player says they are; and while a late *I was there* waits on the
 * reader, *Say who was there*.
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
import { GamePairingCard, tapsAreOpen } from '@/features/games/types';
import { PlayerRecordSheet } from '@/features/player_record/types';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import { behindOverlay, Button, courtSeatCount, ScreenHeader, theme } from '@/shared/ui';

import { peopleOn, rowsOf, type DeckPerson } from '../domain/deck';
import { vibeColumnsOf } from '../domain/details';
import { confirmationOf, paymentToConfirmOn, yesOnRescue } from '../domain/fill';
import { seatsShown, twoWayLeaveIn } from '../domain/friendsGame';
import {
  chatIsOpen,
  completesTheRescue,
  cutOffAhead,
  isFillingAgain,
  leavingAt,
  lineCanRunOut,
  paymentWindowAt,
  resultActOf,
  shownStatus,
  type BookedGame,
} from '../domain/home';
import { gameDayOf } from '../domain/when';
import { useFill } from '../hooks/useFill';
import { bookingReadState, useBooking, useOpenedGames, useReadClock } from '../hooks/useHome';
import { useLeaveBooking, useWithdrawFillingAgain } from '../hooks/useLeaveBooking';
import { usePaymentsToConfirm } from '../hooks/useLiveYeses';

import { CardTag } from './CardTag';
import { BookingAbsent } from './BookingAbsent';
import { clubName, detailsDay, othersTitle, refusalMessage } from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { GameFacts, type FactWords } from './GameFacts';
import { GameGround } from './GameGround';
import { FriendsSeats } from './FriendsSeats';
import { GameTiles } from './GameTiles';
import { HOME_GAME_COPY } from './homeCopy';
import { LeaveTheGame } from './LeaveTheGame';
import {
  STATUS_INK,
  bookedTime,
  moneyRow,
  sportWords,
  statusWord,
  whereAside,
} from './homePresentation';
import { OthersFaces } from './OthersFaces';
import { bookedChatRoute, bookedResultRoute, seatInviteRoute } from './proposalRoutes';
import { PROPOSALS_COPY } from './proposalsCopy';
import { SendersLeave } from './SendersLeave';
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
  /**
   * The game's group, by name — *Open to Ogrody* on an empty seat (#760). `groups'` read, handed
   * in by the route; absent while it reads, or for a game with no seat to open (*the group*).
   */
  readonly groupName?: string;
}

export function BookedGameScreen({ bookingId, offer = false, groupName }: BookedGameScreenProps) {
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

  return <Booked game={game} receivedAt={read.dataUpdatedAt} groupName={groupName} />;
}

function Booked({
  game,
  receivedAt,
  groupName,
}: {
  readonly game: BookedGame;
  readonly receivedAt: number;
  readonly groupName: string | undefined;
}) {
  const me = useCurrentUser().data?.id;
  const room = useBookingRoom(game.bookingId);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);
  const leave = useLeaveBooking(game.bookingId);
  const withdraw = useWithdrawFillingAgain(game.groupId, game.bookingId);
  const fill = useFill();
  // A refused share of the reader's on this game, waiting for them (#625, #626).
  const toConfirm = paymentToConfirmOn(game.bookingId, usePaymentsToConfirm().data);

  // A seat taken from here leaves for the group — but only while this is still the screen on top:
  // the ten seconds can outlive it, and *back* from wherever the player went would be a stray.
  const here = useRef(true);
  useEffect(
    () => () => {
      here.current = false;
    },
    [],
  );

  // The money row turns to *Paid* by itself at the cut-off, *held from* to *held on your card* at a
  // checked share's holding time, and *until* leaves at a time to pay — and the door is *Who's
  // here* until the first half hour ends (#658), so it ticks through that too.
  const readAtTheCourt = game.status === 'NEEDS_RESULT' && tapsAreOpen(game.startsAt, game.readAt);
  const now = useReadClock(game.readAt, receivedAt, lineCanRunOut(game) || readAtTheCourt);
  const leaving = leavingAt(game, now);

  const { rescue } = game;
  const status = shownStatus(game);
  const ink = STATUS_INK[status];
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
  const act = resultActOf(game, { atTheCourt: tapsAreOpen(game.startsAt, now) });
  // A rescue's own seat — what Pay takes, and what a refused rescuer's confirmation is for.
  const seat = yesOnRescue({ bookingId: game.bookingId, sides: game.sides });
  const leaveHere = () => {
    if (here.current) router.back();
  };
  // A friends game's seats (#759), and whether its sender may still call it off — until the
  // cut-off, gone at that instant on the read's clock, as the server would refuse it.
  const seatsNow = seatsShown(game, now);
  const cutOff = cutOffAhead(game.money, now);
  const callsOff = game.friendsGame?.canCallOff === true && cutOff !== undefined;
  // The sender's leave before the cut-off is two ways (#760), worded in the pay mode, and the one
  // door to calling it off — the ordinary leave again at the cut-off on the read's clock.
  const twoWayLeave = callsOff ? twoWayLeaveIn(game, leaving?.kind) : undefined;

  return (
    <>
      <SafeAreaView style={s.screen} edges={['top']} {...behindOverlay(reading !== undefined)}>
        <ScreenHeader
          compact
          onBack={() => router.back()}
          backLabel={COPY.back}
          lead={<OthersFaces people={peopleOn(game)} />}
          title={othersTitle(game)}
          subline={sportWords(game.sport, game.kind)}
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
              <CardTag label={statusWord(status)} tone="grey" dot={ink} />
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
              // For fun draws no forecast, whose split row said the sides — so the line says them.
              speaksSides={game.kind === 'forFun'}
            />

            <GameFacts facts={facts} accent={ink} />

            <FriendsSeats
              seats={seatsNow}
              now={now}
              {...(rescue === undefined
                ? {
                    filling: {
                      bookingId: game.bookingId,
                      cutOff,
                      startsAt: game.startsAt,
                      group: groupName,
                      shareGrosze: game.money.shareGrosze,
                      onInvite: (seatOf: string) =>
                        router.push(seatInviteRoute(game.bookingId, seatOf)),
                    },
                  }
                : {})}
            />
          </View>

          {act === undefined ? null : (
            <Button
              label={COPY.resultAct[act]}
              size="lg"
              onPress={() => router.push(bookedResultRoute(game.bookingId))}
            />
          )}

          {toConfirm === undefined ? null : (
            <Button
              label={
                FILL_COPY.confirm.title[paymentWindowAt(toConfirm.confirmBy, toConfirm.timeTo, now)]
              }
              size="lg"
              onPress={() =>
                fill.confirm({
                  dealtIn: { groupId: game.groupId, sport: game.sport, kind: game.kind },
                  // From outside, the seat confirmed is the rescue's, taken by it (#640).
                  ...(rescue === undefined ? {} : { card: seat, leave: leaveHere }),
                  ...confirmationOf(toConfirm),
                })
              }
            />
          )}

          {game.showsForecast && me !== undefined && game.gameId !== undefined ? (
            <GamePairingCard
              gameId={game.gameId}
              playerId={me}
              columns={vibeColumnsOf({ top, bottom })}
            />
          ) : null}

          {rescue === undefined || toConfirm !== undefined ? null : (
            <TakeTheSeat
              seat={seat}
              dealtIn={{ groupId: game.groupId, sport: game.sport, kind: game.kind }}
              share={share}
              heldUntilTheCutOff={rescue.fillsByTheCutOff}
              size="lg"
              leave={leaveHere}
            />
          )}

          {rescue !== undefined || leaving === undefined ? null : twoWayLeave !== undefined ? (
            <SendersLeave
              bookingId={game.bookingId}
              payMode={twoWayLeave}
              club={game.where.name}
              cutOff={cutOff}
              shareGrosze={game.money.shareGrosze}
              leave={leave}
              afterLeaving={() => router.back()}
            />
          ) : (
            <LeaveTheGame leaving={leaving} act={leave} afterLeaving={() => router.back()} />
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
          groupId={game.groupId}
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
