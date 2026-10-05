/**
 * ***Confirm your payment*** — a share refused when its game filled, confirmed on the same payment
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4; the mechanics §12.2;
 * #541).
 *
 * ```
 * Confirm your payment                      ✕
 * 32 zł to Bonarka Arena
 * Padel · Saturday · 16:00
 * Your bank wants to check this payment once before the club can take it.
 * [ Confirm with your bank ]
 * ```
 *
 * **Two refusals wait for the player, and each has its one way through.** The bank wanting them
 * present is the bank's check over the card on file; a decline is another card, typed into the
 * provider's fields here and paying this share only — the saved method is You › Payments'. Either
 * way it is **the same payment**: the club's, on the club's account, confirmed on the phone and
 * then said to the server, which asks the provider whether it is held now and takes that as the
 * yes again — never the phone's word.
 *
 * What comes back is a yes's answer, and the fill's host reads it: the game booked on it is *It's a
 * game!*; held again with another seat still in the way, the sheet closes and says so; refused at
 * the provider once more, the sheet stays for another try. **A refusal is said in the sheet** —
 * the bank's (closed, declined, unreachable) and the server's (not confirmed yet, the seat taken,
 * the game over) — so the player is never left guessing which half said no.
 *
 * The share is read when the sheet opens, without its secret; the secret is asked of the server
 * again for the press and handed straight to the provider (`useConfirmOnPhone`).
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { confirmsWith, useConfirmOnPhone, useSeatCharge } from '@/features/payments/types';
import { codeMessage, offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { usePayments } from '@/shared/lib/platform';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import { FILL_COPY } from './fillCopy';
import { chargeGameLine, chargeLine } from './fillPresentation';

const WORDS = FILL_COPY.confirm;

export interface ConfirmPaymentSheetProps {
  readonly seatChargeId: string;
  /** Closed: the seat stays open until the player confirms, or somebody else takes it. */
  readonly onClose: () => void;
  /** The yes again, once the provider says the payment is confirmed. Rejects with the refusal. */
  readonly yesAgain: () => Promise<unknown>;
}

export function ConfirmPaymentSheet({ seatChargeId, onClose, yesAgain }: ConfirmPaymentSheetProps) {
  return (
    <BottomSheet visible onClose={onClose} title={WORDS.title} closeLabel={WORDS.close}>
      <Confirmation seatChargeId={seatChargeId} yesAgain={yesAgain} />
    </BottomSheet>
  );
}

function Confirmation({
  seatChargeId,
  yesAgain,
}: Pick<ConfirmPaymentSheetProps, 'seatChargeId' | 'yesAgain'>) {
  const read = useSeatCharge(seatChargeId);
  const confirmOnPhone = useConfirmOnPhone();
  const { CardFields } = usePayments();
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [cardComplete, setCardComplete] = useState(false);

  const charge = read.data;

  if (charge === undefined) {
    if (read.fetchStatus === 'paused')
      return <Note variant="amber">{offlineMessage('resumes')}</Note>;
    // Read, and dropped: a sport this build cannot name.
    if (read.isSuccess) return <Note>{WORDS.unreadable}</Note>;
    if (read.error !== null && !read.isFetching) {
      return (
        <View style={s.body}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(read.error)}
          </Note>
          <Button
            label={WORDS.readAgain}
            variant="secondary"
            size="sm"
            onPress={() => void read.refetch()}
            style={s.action}
          />
        </View>
      );
    }
    return <Text style={s.line}>{WORDS.reading}</Text>;
  }

  const typed = confirmsWith(charge) === 'typed';

  const confirm = async () => {
    if (busy) return;
    setBusy(true);
    setFailure(null);
    try {
      const phone = await confirmOnPhone(seatChargeId, confirmsWith(charge));
      if (phone === 'cancelled' || phone === 'declined' || phone === 'failed') {
        setFailure(WORDS.phone[phone]);
        return;
      }
      // Confirmed — or no longer waiting for the player, which only the server can settle.
      await yesAgain();
    } catch (error) {
      setFailure(codeMessage(WORDS.refused, error as AppError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={s.body}>
      <View accessible>
        <Text style={s.amount}>{chargeLine(charge.amountGrosze, charge.club.name)}</Text>
        <Text style={s.game}>
          {chargeGameLine(charge.sport, charge.startsAt, read.dataUpdatedAt)}
        </Text>
      </View>
      <Text style={s.line}>{typed ? WORDS.declinedLine : WORDS.checkLine}</Text>
      {typed ? (
        <CardFields
          onChange={(entry) => setCardComplete(entry.complete)}
          placeholders={WORDS.cardFields.placeholders}
          accessibilityLabel={WORDS.cardFields.label}
        />
      ) : null}
      {failure === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {failure}
        </Note>
      )}
      <Button
        label={typed ? WORDS.payWithCard : WORDS.check}
        size="lg"
        busy={busy}
        busyLabel={WORDS.confirming}
        disabled={typed && !cardComplete}
        onPress={() => void confirm()}
      />
    </View>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.md },
  amount: { ...theme.type.cardTitle, color: theme.color.ink },
  game: { ...theme.type.tiny, color: theme.color.muted },
  line: { ...theme.type.rlLabel, color: theme.color.muted },
  action: { alignSelf: 'flex-start' },
});
