/**
 * **FRIENDS GAME · n** — Needs your answer's section of friends game invitations, after TO CONFIRM
 * and before FRIEND REQUESTS ([#817](https://github.com/Rakieta02/Rakieta/issues/817), ADR-0205 §1;
 * home refactor 2). It was Home's row at the very top from
 * [#759](https://github.com/Rakieta02/Rakieta/issues/759) (the friends screens §6.1; friends 12; the
 * mechanics §9).
 *
 * ```
 * FRIENDS GAME · 2
 * ┌───────────────────────────────────────────────┐
 * │ tomek.k's game                      ⏱ 1 h 35 │   the clock: the deck ribbon's, coral under an hour
 * │   [TK]✓    [ZB]✓    [AK]     [EW]             │   ✓ on those In, faded on those still to answer
 * │  tomek.k  zofia.b  ania.k    You              │
 * │ Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive
 * │ tomek.k paid the court                        │   Whole court only
 * │ ┌─ Not this time ─┐ ┌─ Accept and pay 25 zł ─┐ │   Whole court: Accept
 * └───────────────────────────────────────────────┘
 *                      ━ ·                            the dots, from two
 * ```
 *
 * ## Only while an invitation waits
 *
 * **The section and its title are there only while they hold a card** (ADR-0205 §1): nothing while
 * Home's read is in flight, refused or holds none. The read is Home's (`friends_games`), the soonest
 * to end first, and nothing re-sorts it. A card whose time runs out while it is on screen leaves at
 * that instant (`useFriendsGamesWaiting`, on the read's clock), as the server would no longer list
 * it — and Needs your answer counts the same list, so it never opens on a section left empty.
 *
 * ## One big tile at a time
 *
 * **The paging rail** (Q9, Q46): every card the content width, snapping one at a time, as Your
 * games pages — and **its dots from two** (`dotsAlone`, 7.18 as amended): one invitation has nothing
 * to page to, and the heading counts it. **The card is as it was on Home** — title, clock, faces,
 * the when/where/sport line, a refusal said on it, **Not this time** and **Accept and pay 25 zł** or
 * **Accept** — mock 2's tile.
 *
 * ## Each card answers itself
 *
 * - **Accept** — *Split*: their share held until the cut-off, with them present. Nothing saved opens
 *   the payment setup first (the fill's); a bank that wants them present, or a decline, opens the
 *   confirmation (`ConfirmPaymentSheet`, the deck's), which is the accept again once confirmed.
 *   *Whole court*: nothing held. In, the card moves to Your games — and the last seat taken is
 *   ***It's a game!***, as for any game (`useFill().celebrate`). **All three are the fill's** — the
 *   confirmation too (`confirmOwn`, #817) — drawn inside the sheet that carries it (`FillInASheet`),
 *   so the sheet steps aside under them, and *It's a game!* closes it for good (the shell's). The
 *   confirmation was the card's own sheet until then, and the sheet could close beneath it when the
 *   confirmed accept took the invitation off Home's read.
 * - **Not this time** — the card leaves.
 * - **A full week, a game at that hour** — the sentence on the card, which stays. **An invitation
 *   that ended, a game off or under way** — a toast, and Home read again: the card leaves.
 *
 * Either answer re-reads the bell (`onAnswered`, `notifications`', handed in by the shell): the
 * invitation's row there is the server's to take off.
 *
 * **The border is `ink`, not mock 12's or mock 2's coral** — §1.2's coral list is closed, and a card
 * waiting on the reader is the friend request tile's ink (5.1's selected border); the clock under an
 * hour is `coralInk`, coral text on paper (Part 16, 2026-11-07).
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
  type FriendsGameInvitation,
  type InvitationFace,
} from '../domain/friendsGame';
import { useFill } from '../hooks/useFill';
import {
  useAcceptFriendsGame,
  useConfirmFriendsPayment,
  useDeclineFriendsGame,
} from '../hooks/useFriendsGameWrites';
import type { FriendsGamesWaiting } from '../hooks/useHome';

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

export interface FriendsGameSectionProps {
  /**
   * **The invitations still waiting, and the clock they wait on** — `useAnswersWaiting`'s, which the
   * sheet's owner reads all session to count them, handed back in: the envelope's count and the
   * section's tiles are one list on one clock, which has run since the launch rather than from this
   * section's mount.
   */
  readonly invitations: FriendsGamesWaiting;
  /**
   * **An invitation was answered** — the bell's re-read, handed in by the shell: answering clears
   * the invitation from the bell (the mechanics §9), and the bell is `notifications`'.
   */
  readonly onAnswered: () => Promise<unknown>;
}

export function FriendsGameSection({ invitations, onAnswered }: FriendsGameSectionProps) {
  // The clock ticks while an invitation waits: *1 h 35* counts down, and a card leaves at its end.
  const { waiting, now } = invitations;
  if (waiting === undefined || waiting.length === 0) return null;

  return (
    <HomeRow heading={friendsGamesHeading(waiting.length)} testID="friends-games">
      <HomeRowRail cards={waiting} geometry="paging" dotsAlone={false}>
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

  /**
   * **The bank's check, or a card declined** — the fill's confirmation, which is the accept again once
   * confirmed. The fill draws it, over Needs your answer, so the sheet steps aside under it rather
   * than closing beneath it when the confirmed accept takes the invitation off Home's read.
   */
  const confirmShare = (payment: YourPayment) =>
    fill.confirmOwn({
      seatChargeId: payment.seatChargeId,
      ...(payment.confirmBy === undefined ? {} : { confirmBy: payment.confirmBy }),
      ...(payment.timeTo === undefined ? {} : { timeTo: payment.timeTo }),
      refusal: (error) => answerRefusal(error, startsAt),
      yesAgain: async () => {
        await confirmPayment.mutateAsync(payment.seatChargeId);
        // Confirmed is the accept made: asked again, it says whether the game is whole now.
        const again = await accept.mutateAsync(bookingId);
        if (again.accepted) landed(again.whole);
      },
    });

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
            confirmShare(payment);
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
