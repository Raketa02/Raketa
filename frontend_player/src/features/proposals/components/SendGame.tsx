/**
 * ***Send game and pay 25 zł*** — the friends card's order, and the send sheet it opens
 * ([#759](https://github.com/Raketa02/Raketa/issues/759); the friends screens §8, designed, no mock;
 * the mechanics §8; the words §29.7).
 *
 * ```
 * How to pay                                       ✕
 * ┌ Split the cost                        25 zł ┐   chosen first: the ink border
 * └─────────────────────────────────────────────┘
 * ┌ Pay the whole court                  100 zł ┐
 * └─────────────────────────────────────────────┘
 * We hold 100 zł on your card until Fri 10:00. You pay 25 zł,   Split only: the maximum, right
 * plus 25 zł for any seat still empty then.                     above the order
 * [            Send game and pay 25 zł            ]
 * ```
 *
 * **The button is the order** (call 8): its words name the payment, and with *Split* the most it
 * can come to stands right above it. **Sending books the court at once** (#751): the court claimed,
 * then the sender's share and a cover for every other seat held, all or nothing, with them present.
 *
 * ## Every answer has its place
 *
 * - **Booked** — the sheet closes, the toast says where the game is, and the court goes back to
 *   empty (`onSent`): the game is in Your games now.
 * - **Nothing saved** — the payment setup opens first (the fill's, as before a first yes), and the
 *   send goes once a method is saved; the server saying so (`payment_method_required`) opens it too.
 * - **A payment the bank wants confirmed, or declined** — nothing was booked: each is confirmed in
 *   the app, one after another (`ConfirmPaymentSheet`, the deck's own), then the send goes again
 *   under the booking it answered, which takes the holds confirmed. **The terms again** is a toast
 *   naming You › Payments, as the deck's.
 * - **The court went** (`court_just_taken`), **or somebody seated no longer may be** — the sheet
 *   closes and the card is read again (`onReread`), the court's sentence above it; **the hour no
 *   longer for sale** — the card proposes another (`onCourtGone`).
 * - **Two games already waiting, the sender's own hour or week** — the sentence in the sheet, the
 *   order still there; said in a toast when the sheet is already closed (a send again after a
 *   confirmation).
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { usePaymentSetupNeeded } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { showToast } from '@/shared/store/toast.store';
import { BottomSheet, Button, Note, PressableCard, courtSeatCount, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { YourPayment } from '../domain/fill';
import type { FriendsCardAsk, FriendsCourt } from '../domain/friendsCard';
import { courtPrice, sendCharge, sendPaymentsOf, sendRefusalOf } from '../domain/friendsGame';
import type { PayMode } from '../domain/vocabulary';
import { useFill } from '../hooks/useFill';
import { useConfirmFriendsPayment, useSendFriendsGame } from '../hooks/useFriendsGameWrites';

import { ConfirmPaymentSheet } from './ConfirmPaymentSheet';
import { FILL_COPY } from './fillCopy';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { coverLine, payModeTitle, sendLabel, sendRefusal } from './friendsGamePresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = FRIENDS_GAME_COPY.send;

const PAY_MODES: readonly PayMode[] = ['SPLIT_THE_COST', 'WHOLE_COURT'];

export interface SendGameProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** The line-up as the card was read for it. */
  readonly ask: FriendsCardAsk;
  /** The court the card names — what the send books. */
  readonly court: FriendsCourt;
  /** The club's cut-off for its hour — *until Fri 10:00*. */
  readonly cutOff: string | undefined;
  /** Booked: the court goes back to empty. */
  readonly onSent: () => void;
  /** The card is read again, with the line to say above it, if any. */
  readonly onReread: (line?: string) => void;
  /** The hour is no longer for sale: the card proposes another, with the line to say. */
  readonly onCourtGone: (line: string) => void;
}

/** The payments a refused send named, confirmed one after another, and the booking to send under. */
interface Confirming {
  readonly bookingId: string;
  readonly payments: readonly YourPayment[];
  readonly at: number;
}

export function SendGame({
  groupId,
  sport,
  ask,
  court,
  cutOff,
  onSent,
  onReread,
  onCourtGone,
}: SendGameProps) {
  const fill = useFill();
  const setUpNeeded = usePaymentSetupNeeded();
  const send = useSendFriendsGame(groupId);
  const confirmPayment = useConfirmFriendsPayment();

  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<PayMode>('SPLIT_THE_COST');
  const [refusal, setRefusal] = useState<string>();
  const [confirming, setConfirming] = useState<Confirming | null>(null);

  const seats = courtSeatCount(sport);
  const share = court.shareGrosze;
  const price = courtPrice(share, seats);

  /** A sentence in the sheet while it is open, else a toast: the player is told either way. */
  const say = (line: string, sheetOpen: boolean) => {
    if (sheetOpen) setRefusal(line);
    else showToast({ message: line, tone: 'bad' });
  };

  const go = (payMode: PayMode, bookingId: string | undefined, sheetOpen: boolean) => {
    setRefusal(undefined);
    send.mutate(
      {
        sport,
        ask,
        court: { courtId: court.courtId, startsAt: court.startsAt },
        payMode,
        ...(bookingId === undefined ? {} : { bookingId }),
      },
      {
        onSuccess: (sent) => {
          if (sent.booked) {
            setOpen(false);
            showToast({ message: COPY.sent, tone: 'ok' });
            onSent();
            return;
          }
          const next = sendPaymentsOf(sent.yourPayments);
          switch (next.kind) {
            case 'setUp':
              setOpen(false);
              fill.setUpThen(() => go(payMode, sent.bookingId, false));
              return;
            case 'termsAgain':
              setOpen(false);
              showToast({ message: FILL_COPY.termsAgain, tone: 'bad' });
              return;
            case 'confirm':
              setOpen(false);
              setConfirming({ bookingId: sent.bookingId, payments: next.payments, at: 0 });
              return;
            case 'sendAgain':
              say(PROPOSALS_COPY.refused.block_state_unavailable, sheetOpen);
              return;
          }
        },
        onError: (error) => {
          switch (sendRefusalOf(error.code)) {
            case 'setUp':
              setOpen(false);
              fill.setUpThen(() => go(payMode, bookingId, false));
              return;
            case 'reread':
              setOpen(false);
              onReread(
                error.code === 'court_just_taken'
                  ? PROPOSALS_COPY.refused.court_just_taken
                  : undefined,
              );
              return;
            case 'courtGone':
              setOpen(false);
              onCourtGone(COPY.refused.courtGone);
              return;
            case 'say':
              say(sendRefusal(error, court.startsAt), sheetOpen);
              return;
          }
        },
      },
    );
  };

  const order = () => {
    if (send.isPending) return;
    // Nothing saved: the setup first, and the send once a method is (the screens §8).
    if (setUpNeeded === true) {
      setOpen(false);
      fill.setUpThen(() => go(mode, undefined, false));
      return;
    }
    go(mode, undefined, true);
  };

  const payment = confirming === null ? undefined : confirming.payments[confirming.at];

  return (
    <>
      <Button
        label={sendLabel(share)}
        variant="volt"
        size="lg"
        onPress={() => {
          setMode('SPLIT_THE_COST');
          setRefusal(undefined);
          setOpen(true);
        }}
      />

      <BottomSheet
        visible={open}
        onClose={() => setOpen(false)}
        title={COPY.title}
        closeLabel={COPY.close}
      >
        <View style={s.body} testID="send-sheet">
          <View style={s.choices} accessibilityRole="radiogroup">
            {PAY_MODES.map((one) => {
              const charge = formatZloty(sendCharge(one, share, seats));
              return (
                <PressableCard
                  key={one}
                  selected={mode === one}
                  onPress={() => {
                    setMode(one);
                    setRefusal(undefined);
                  }}
                  accessibilityLabel={`${payModeTitle(one)}, ${charge}`}
                  style={s.choice}
                >
                  <Text style={s.choiceTitle}>{payModeTitle(one)}</Text>
                  <Text style={s.charge}>{charge}</Text>
                </PressableCard>
              );
            })}
          </View>

          {mode === 'SPLIT_THE_COST' ? (
            <Text style={s.cover}>
              {coverLine({ priceGrosze: price, shareGrosze: share, cutOff, singles: seats === 2 })}
            </Text>
          ) : null}

          {refusal === undefined ? null : (
            <Note variant="coral" accessibilityRole="alert">
              {refusal}
            </Note>
          )}

          <Button
            label={sendLabel(sendCharge(mode, share, seats))}
            size="lg"
            busy={send.isPending}
            busyLabel={COPY.sending}
            onPress={order}
          />
        </View>
      </BottomSheet>

      {confirming === null || payment === undefined ? null : (
        <ConfirmPaymentSheet
          key={payment.seatChargeId}
          seatChargeId={payment.seatChargeId}
          {...(payment.confirmBy === undefined ? {} : { confirmBy: payment.confirmBy })}
          {...(payment.timeTo === undefined ? {} : { timeTo: payment.timeTo })}
          seat="yours"
          closeLabel={COPY.close}
          onClose={() => setConfirming(null)}
          refusal={(error: AppError) => sendRefusal(error, court.startsAt)}
          yesAgain={async () => {
            await confirmPayment.mutateAsync(payment.seatChargeId);
            const at = confirming.at + 1;
            if (at < confirming.payments.length) {
              setConfirming({ ...confirming, at });
              return;
            }
            // Every payment confirmed: the send again, under the booking it answered.
            setConfirming(null);
            go(mode, confirming.bookingId, false);
          }}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  choices: { gap: theme.space.sm },
  choice: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  choiceTitle: { ...theme.type.cardTitle, color: theme.color.ink },
  charge: { ...theme.num.m, ...theme.tabular, color: theme.color.ink },
  cover: { ...theme.type.rlLabel, color: theme.color.ink },
});
