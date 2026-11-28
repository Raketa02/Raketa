/**
 * ***Confirm your payment*** — a share refused when its game filled, confirmed on the same payment
 * ([#555](https://github.com/Rakieta02/Rakieta/issues/555); the screens A2.4; the mechanics §12.2;
 * #541) — ***Fix your card*** before the club's cut-off (#643; Q113).
 *
 * ```
 * Confirm your payment                      ✕
 * 32 zł to Bonarka Arena
 * Padel · Saturday · 16:00
 * ▎Confirm your payment by 14:40 to keep your seat     — while their time to pay runs (Q109)
 * Your bank wants to check this payment once before the club can take it.
 * [ Confirm with your bank ]
 * ```
 *
 * **Which window it is, is the server's** (`timeTo`, #638): before the cut-off nothing is being
 * taken, so the player is never asked to pay — the sheet is *Fix your card*, its note *Fix your card
 * by 14:40 to keep your seat*, a line that nothing is paid now (fixing it only places the hold
 * again), and a decline is fixed with another card (*Use this card*). After it, the words above.
 * With no window named — a time run out, an older server — the words say *confirm*, never *pay*: a
 * seat taken back before the cut-off is held, not paid.
 * **On a rescue** (#640) the seat is kept for the player to take, not yet theirs: *Fix your card by
 * 14:40 to take the seat — it's kept for you until then*.
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
 *
 * **Their time to pay is named while it runs** (#625, #626; Q109) — an amber note, *Confirm your
 * payment by 14:40 to keep your seat*, the notice's and the email's words, written as Home writes the
 * time. The payment's own read does not carry it (it is the Payments context's, and the time is the
 * game's), so whoever opens the sheet hands it in, with its window: the yes's answer, a *TO CONFIRM*
 * row, a game's details. Once it ran out there is no time to name, and no note.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  confirmsWith,
  useCardFieldsReady,
  useConfirmOnPhone,
  useSeatCharge,
} from '@/features/payments/types';
import { codeMessage, offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { usePayments } from '@/shared/lib/platform';
import { BottomSheet, Button, Note, theme } from '@/shared/ui';

import { deadlineAhead, paymentWindowAt, type SeatAtStake } from '../domain/home';
import type { TimeTo } from '../domain/vocabulary';

import { FILL_COPY } from './fillCopy';
import { chargeGameLine, chargeLine, confirmNote } from './fillPresentation';

const WORDS = FILL_COPY.confirm;

export interface ConfirmPaymentSheetProps {
  readonly seatChargeId: string;
  /** **Their time to pay**, while it runs (Q109). */
  readonly confirmBy?: string;
  /** What it is for (Q113) — to fix the card, before the cut-off; to pay, after it. */
  readonly timeTo?: TimeTo;
  /** Their own seat, or a rescue's, kept for them to take (#640). */
  readonly seat: SeatAtStake;
  /** Closed: the seat stays open until the player confirms, or somebody else takes it. */
  readonly onClose: () => void;
  /** The yes again, once the provider says the payment is confirmed. Rejects with the refusal. */
  readonly yesAgain: () => Promise<unknown>;
  /**
   * **The words for a refusal of what the confirmation carries**, where it is not a yes — a friends
   * game's send or *Accept* (#759): a full week, a game at that hour. Nothing, and the sheet's own.
   */
  readonly refusal?: (error: AppError) => string | undefined;
  /** What the close says aloud — *the seat stays open* unless what is confirmed is no seat yet. */
  readonly closeLabel?: string;
}

export function ConfirmPaymentSheet({
  onClose,
  closeLabel = WORDS.close,
  ...confirmation
}: ConfirmPaymentSheetProps) {
  // One instant for the title and the note: the time, and its window, as of the opening.
  const [openedAt] = useState(Date.now);
  const paymentWindow = paymentWindowAt(confirmation.confirmBy, confirmation.timeTo, openedAt);
  return (
    // A declined card is typed again here: a tap on the sheet keeps the keyboard (`BottomSheet`'s note).
    <BottomSheet
      visible
      onClose={onClose}
      title={WORDS.title[paymentWindow]}
      closeLabel={closeLabel}
      keepsKeyboardOnTap
    >
      <Confirmation {...confirmation} openedAt={openedAt} />
    </BottomSheet>
  );
}

function Confirmation({
  seatChargeId,
  confirmBy,
  timeTo,
  seat,
  openedAt,
  yesAgain,
  refusal,
}: Omit<ConfirmPaymentSheetProps, 'onClose' | 'closeLabel'> & { readonly openedAt: number }) {
  const read = useSeatCharge(seatChargeId);
  const confirmOnPhone = useConfirmOnPhone();
  const { CardFields } = usePayments();
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [cardComplete, setCardComplete] = useState(false);

  const charge = read.data;
  // The card fields are drawn only once Stripe is started with this payment's key — see the hook.
  const fields = useCardFieldsReady(
    seatChargeId,
    charge !== undefined && confirmsWith(charge) === 'typed',
  );

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
  // Named only while it is ahead: a row read before the time ran out still hands it in.
  const by = deadlineAhead(confirmBy, openedAt);
  const paymentWindow = paymentWindowAt(confirmBy, timeTo, openedAt);

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
      const refused = error as AppError;
      setFailure(refusal?.(refused) ?? codeMessage(WORDS.refused, refused));
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
      {by === undefined ? null : (
        <Note variant="amber">{confirmNote({ by, window: paymentWindow }, seat)}</Note>
      )}
      {paymentWindow === 'FIX_THE_CARD' ? (
        <Text style={s.line}>{WORDS.onlyPlacedAgain}</Text>
      ) : null}
      <Text style={s.line}>{(typed ? WORDS.declinedLine : WORDS.checkLine)[paymentWindow]}</Text>
      {typed && fields === 'ready' ? (
        <CardFields
          onChange={(entry) => setCardComplete(entry.complete)}
          placeholders={WORDS.cardFields.placeholders}
          accessibilityLabel={WORDS.cardFields.label}
        />
      ) : null}
      {typed && fields === 'reading' ? <Text style={s.line}>{WORDS.reading}</Text> : null}
      {typed && fields === 'failed' ? (
        <Note variant="coral" accessibilityRole="alert">
          {WORDS.providerNotStarted}
        </Note>
      ) : null}
      {failure === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {failure}
        </Note>
      )}
      <Button
        label={typed ? WORDS.withThisCard[paymentWindow] : WORDS.check}
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
