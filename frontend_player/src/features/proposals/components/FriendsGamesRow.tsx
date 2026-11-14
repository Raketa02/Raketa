/**
 * **FRIENDS GAME · n** — Home's row of friends game invitations, at the very top
 * ([#759](https://github.com/Raketa02/Raketa/issues/759); the friends screens §6.1; friends 12;
 * Q13; the mechanics §9).
 *
 * ```
 * FRIENDS GAME · 1
 * ┌───────────────────────────────────────────────┐
 * │ tomek.k's game                      ⏱ 1 h 35 │   the clock: the deck ribbon's, coral under an hour
 * │   [TK]✓    [ZB]✓    [AK]     [EW]             │   ✓ on those In, faded on those still to answer
 * │  tomek.k  zofia.b  ania.k    You              │
 * │ Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive
 * │ tomek.k paid the court                        │   Whole court only
 * │ ┌─ Not this time ─┐ ┌─ Accept and pay 25 zł ─┐ │   Whole court: Accept
 * └───────────────────────────────────────────────┘
 * ```
 *
 * ## Only while an invitation waits
 *
 * **The row and its title are there only while they hold a card** (the screens §6): nothing while
 * Home's read is in flight, refused or holds none. The read is Home's (`friends_games`), the soonest
 * to end first, and nothing re-sorts it. A card whose time runs out while it is on screen leaves at
 * that instant (`invitationWaits`, on the read's clock), as the server would no longer list it.
 *
 * ## A horizontal row
 *
 * One card takes the content width; two or more are 7.7's peeking rail — the friend requests row's
 * own geometry, so the two rows under one another read as one kind of thing: both are Home's row
 * frame (`HomeRow`, #798).
 *
 * ## Each card answers itself
 *
 * - **Accept** — *Split*: their share held until the cut-off, with them present. Nothing saved opens
 *   the payment setup first (the fill's); a bank that wants them present, or a decline, opens the
 *   confirmation (`ConfirmPaymentSheet`, the deck's), which is the accept again once confirmed.
 *   *Whole court*: nothing held. In, the card moves to Your games — and the last seat taken is
 *   ***It's a game!***, as for any game (`useFill().celebrate`).
 * - **Not this time** — the card leaves.
 * - **A full week, a game at that hour** — the sentence on the card, which stays. **An invitation
 *   that ended, a game off or under way** — a toast, and Home read again: the card leaves.
 *
 * Either answer re-reads the bell (`onAnswered`, `notifications`', handed in by the shell): the
 * invitation's row there is the server's to take off.
 *
 * **The border is `ink`, not mock 12's coral** — §1.2's coral list is closed, and a card waiting on
 * the reader is the friend requests row's ink (5.1's selected border); the clock under an hour is
 * `coralInk`, coral text on paper (Part 16, 2026-11-07).
 */

import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { usePaymentSetupNeeded } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';
import { showToast } from '@/shared/store/toast.store';
import { Button, Card, HomeRow, HomeRowRail, Note, Tick, theme } from '@/shared/ui';

import type { YourPayment } from '../domain/fill';
import {
  acceptPaymentOf,
  answerRefusalOf,
  invitationFaces,
  invitationWaits,
  type FriendsGameInvitation,
  type InvitationFace,
} from '../domain/friendsGame';
import { useFill } from '../hooks/useFill';
import {
  useAcceptFriendsGame,
  useConfirmFriendsPayment,
  useDeclineFriendsGame,
} from '../hooks/useFriendsGameWrites';
import { useHomeFriendsGames, useReadClock } from '../hooks/useHome';

import { ConfirmPaymentSheet } from './ConfirmPaymentSheet';
import { FILL_COPY } from './fillCopy';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import {
  acceptLabel,
  acceptSpoken,
  answerRefusal,
  faceName,
  facesSpoken,
  friendsGamesHeading,
  gameOf,
  invitationClock,
  invitationLine,
  notThisTimeSpoken,
  paidTheCourt,
} from './friendsGamePresentation';
import { YesTile } from './YesTile';

const COPY = FRIENDS_GAME_COPY.invitation;

export interface FriendsGamesRowProps {
  /**
   * **An invitation was answered** — the bell's re-read, handed in by the shell: answering on Home
   * clears the invitation from the bell (the mechanics §9), and the bell is `notifications`'.
   */
  readonly onAnswered: () => Promise<unknown>;
}

export function FriendsGamesRow({ onAnswered }: FriendsGamesRowProps) {
  const { invitations, readAt, receivedAt } = useHomeFriendsGames();
  // The clocks tick while an invitation waits: *1 h 35* counts down, and a card leaves at its end.
  const now = useReadClock(readAt, receivedAt, (invitations?.length ?? 0) > 0);

  const waiting = (invitations ?? []).filter((one) => invitationWaits(one.friendsGame, now));
  if (waiting.length === 0) return null;

  return (
    <HomeRow heading={friendsGamesHeading(waiting.length)} testID="friends-games">
      <HomeRowRail cards={waiting}>
        {(invitation, width) => (
          <InvitationCard
            key={invitation.bookingId}
            invitation={invitation}
            now={now}
            width={width}
            onAnswered={onAnswered}
          />
        )}
      </HomeRowRail>
    </HomeRow>
  );
}

function InvitationCard({
  invitation,
  now,
  width,
  onAnswered,
}: {
  readonly invitation: FriendsGameInvitation;
  readonly now: number;
  readonly width: number;
  readonly onAnswered: () => Promise<unknown>;
}) {
  const fill = useFill();
  const setUpNeeded = usePaymentSetupNeeded();
  const accept = useAcceptFriendsGame();
  const decline = useDeclineFriendsGame();
  const confirmPayment = useConfirmFriendsPayment();
  const [failure, setFailure] = useState<string>();
  const [confirming, setConfirming] = useState<YourPayment | null>(null);

  const { bookingId, friendsGame: game, startsAt } = invitation;
  const sender = game.senderNickname;
  const split = game.payMode === 'SPLIT_THE_COST';
  const clock = invitationClock(game.yourInvitationUntil, now);
  const faces = invitationFaces(invitation, now);
  const accepting = accept.isPending || confirmPayment.isPending;
  const busy = accepting || decline.isPending;
  const label = acceptLabel(game, invitation.shareGrosze);

  /** In: *It's a game!* on the last seat, else the card moves to Your games. */
  const landed = (whole: boolean) => {
    void onAnswered();
    if (whole) fill.celebrate(bookingId, invitation.sides);
    else showToast({ message: COPY.accepted, tone: 'ok' });
  };

  /** Refused: on the card, or — the invitation gone — a toast and Home read again. */
  const refused = (error: AppError, again: () => void) => {
    switch (answerRefusalOf(error.code)) {
      case 'setUp':
        fill.setUpThen(again);
        return;
      case 'gone':
        // Home is read again by the write itself, and the card leaves with it.
        showToast({ message: answerRefusal(error, startsAt), tone: 'bad' });
        return;
      case 'say':
        setFailure(answerRefusal(error, startsAt));
        return;
    }
  };

  const sendAccept = () => {
    setFailure(undefined);
    accept.mutate(bookingId, {
      onSuccess: (answer) => {
        if (answer.accepted) {
          landed(answer.whole);
          return;
        }
        const payment = answer.yourPayment;
        if (payment === undefined) return;
        switch (acceptPaymentOf(payment)) {
          case 'confirm':
            setConfirming(payment);
            return;
          case 'setUp':
            fill.setUpThen(sendAccept);
            return;
          case 'termsAgain':
            showToast({ message: FILL_COPY.termsAgain, tone: 'bad' });
            return;
        }
      },
      onError: (error) => refused(error, sendAccept),
    });
  };

  const onAccept = () => {
    if (busy) return;
    // *Split* holds their share: nothing saved, the setup first (the screens §6.1).
    if (split && setUpNeeded === true) {
      fill.setUpThen(sendAccept);
      return;
    }
    sendAccept();
  };

  const onDecline = () => {
    if (busy) return;
    setFailure(undefined);
    decline.mutate(bookingId, {
      onSuccess: () => void onAnswered(),
      onError: (error) => refused(error, onDecline),
    });
  };

  return (
    <Card style={[s.card, { width }]}>
      <View
        style={s.top}
        accessible
        accessibilityRole="header"
        accessibilityLabel={[gameOf(sender), clock?.spoken]
          .filter((part) => part !== undefined)
          .join(', ')}
        testID={`friends-game-${bookingId}`}
      >
        <Text style={s.title} numberOfLines={1}>
          {gameOf(sender)}
        </Text>
        {clock === undefined ? null : (
          <View style={s.clock} testID="friends-game-clock">
            <Feather
              name="clock"
              size={theme.size.infoGlyph}
              color={clock.urgent ? theme.color.coralInk : theme.color.muted}
            />
            <Text style={[s.clockWords, clock.urgent ? s.urgent : undefined]}>{clock.words}</Text>
          </View>
        )}
      </View>

      <View style={s.faces} accessible accessibilityLabel={facesSpoken(faces)}>
        {faces.map((face) => (
          <Face key={face.person.playerId} face={face} />
        ))}
      </View>

      <Text style={s.line}>{invitationLine(invitation, now)}</Text>

      {split ? null : <Text style={s.paid}>{paidTheCourt(sender)}</Text>}

      {failure === undefined ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {failure}
        </Note>
      )}

      <View style={s.buttons}>
        <Button
          label={COPY.notThisTime}
          accessibilityLabel={notThisTimeSpoken(sender)}
          variant="secondary"
          size="lg"
          disabled={busy && !decline.isPending}
          busy={decline.isPending}
          onPress={onDecline}
          style={s.notThisTime}
        />
        <Button
          label={label}
          accessibilityLabel={acceptSpoken(label, sender)}
          size="lg"
          disabled={busy && !accepting}
          busy={accepting}
          busyLabel={COPY.accepting}
          onPress={onAccept}
          style={s.accept}
        />
      </View>

      {confirming === null ? null : (
        <ConfirmPaymentSheet
          key={confirming.seatChargeId}
          seatChargeId={confirming.seatChargeId}
          {...(confirming.confirmBy === undefined ? {} : { confirmBy: confirming.confirmBy })}
          {...(confirming.timeTo === undefined ? {} : { timeTo: confirming.timeTo })}
          seat="yours"
          onClose={() => setConfirming(null)}
          refusal={(error) => answerRefusal(error, startsAt)}
          yesAgain={async () => {
            await confirmPayment.mutateAsync(confirming.seatChargeId);
            // Confirmed is the accept made: asked again, it says whether the game is whole now.
            const again = await accept.mutateAsync(bookingId);
            setConfirming(null);
            if (again.accepted) landed(again.whole);
          }}
        />
      )}
    </Card>
  );
}

/** One face — the yes screen's tile, ✓ when In, faded while still to answer, the name under it. */
function Face({ face }: { readonly face: InvitationFace }) {
  const { person } = face;
  const size = theme.size.yesTile.doubles;
  return (
    <View style={[s.face, face.faded ? s.faded : undefined]} testID={`face-${person.playerId}`}>
      <View>
        <YesTile
          seat={{
            kind: 'person',
            playerId: person.playerId,
            ...(person.name === undefined ? {} : { name: person.name }),
            ...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl }),
          }}
          size={size}
        />
        {face.isIn ? (
          <View style={s.in} testID={`face-in-${person.playerId}`}>
            <Tick />
          </View>
        ) : null}
      </View>
      <Text style={s.name} numberOfLines={1}>
        {faceName(person)}
      </Text>
    </View>
  );
}

/** The ✓ disc at the face's corner — 6.9's remove square's size, the seat-clear badge's own. */
const IN_MARK = theme.size.photoTile.remove;

const s = StyleSheet.create({
  // A card waiting on the reader: 5.1's selected border, as the friend requests row's.
  card: { borderColor: theme.color.ink, gap: theme.space.md },
  top: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  title: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  clock: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs, marginLeft: 'auto' },
  clockWords: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  // Coral text on paper is `coralInk` (§1.2), as Today's column head is.
  urgent: { color: theme.color.coralInk },
  faces: { flexDirection: 'row', justifyContent: 'center', gap: theme.space.md },
  face: { alignItems: 'center', gap: theme.space.xxs, maxWidth: theme.size.yesTile.doubles },
  faded: { opacity: 0.4 },
  in: {
    position: 'absolute',
    right: -IN_MARK / 4,
    bottom: -IN_MARK / 4,
    width: IN_MARK,
    height: IN_MARK,
    borderRadius: IN_MARK / 2,
    // White never sits on `mint` (Rule C): the tick is drawn on `mintInk`.
    backgroundColor: theme.color.mintInk,
    alignItems: 'center',
    justifyContent: 'center',
  },
  name: { ...theme.type.tiny, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.ink, textAlign: 'center' },
  paid: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  buttons: { flexDirection: 'row', gap: theme.space.sm },
  notThisTime: { flex: 1 },
  accept: { flex: 2 },
});
