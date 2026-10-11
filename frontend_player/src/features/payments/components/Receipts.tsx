/**
 * **RECEIPTS** — You › Payments' last section, under the method and the live yeses
 * ([#555](https://github.com/Raketa02/Raketa/issues/555), [#644](https://github.com/Raketa02/Raketa/issues/644);
 * the screens A7.3; mock 49; the mechanics §12.1, Q113).
 *
 * ```
 * RECEIPTS
 * ┌───────────────────────────────────────────┐
 * │ [✓]  Bonarka Arena          −40 zł · paid │   a share taken: ✓ on paper2, the amount in ink
 * │      Padel · Today · 16:00                │
 * │───────────────────────────────────────────│
 * │ [↩]  Ogrody 33       +38,24 zł · refunded │   a refund: ↩ on mintSoft, the amount in mintInk,
 * │      Padel · Saturday · 18:00             │   and exactly what was kept on the payment
 * │      1,76 zł kept on your payment         │
 * │───────────────────────────────────────────│
 * │ [○]  Bonarka Arena  40 zł held · released │   a hold let go: an open lock on paper2, all muted,
 * │      Padel · 20 Oct · 16:00               │   and the day it was let go
 * │      Released 28 Sep                      │
 * └───────────────────────────────────────────┘
 * Refunds can take up to two weeks to reach your card.
 * ```
 *
 * **The club is the title** — the seller, named on every receipt (§12.1) — and the game under it.
 * Newest first, as the server orders them. **Every movement of the money is a row** (Q113): a share
 * taken at the cut-off, a refund, and a hold let go untaken, so the hold the bank app showed is
 * explained — dated when it was let go, as the bank dates it. **The amount shares the club's line**,
 * where a row's third line — the fee kept, the day — would otherwise squeeze the game's under it.
 * **Empty, the section says what will land here**, and the refund-timing footer is drawn only under
 * rows, where a refund can be waited for.
 *
 * Rows are not buttons: a receipt is a record, and the game it was for is reached from Home. A
 * read on its way draws nothing — a missing list must not read as *nothing yet* — and a read that
 * failed says why under the section's name, with the retry.
 *
 * **The mint is a refund's**, settled money coming back — the colour's own meaning (Part 1) — on its
 * soft fill with the ink beside it, Rule C's pair; a share taken stays in ink on the row lead's
 * paper, and **a hold let go is muted**, nothing having moved.
 */

import Feather from '@expo/vector-icons/Feather';
import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Card, Note, theme, type DoorRowGlyph } from '@/shared/ui';

import { receiptDayOf, type Receipt, type ReceiptKind } from '../domain/receipts';
import { useReceipts } from '../hooks/useReceipts';

import { PAYMENTS_COPY } from './paymentsCopy';
import {
  receiptAmount,
  receiptClub,
  receiptLabel,
  receiptLine,
  receiptNote,
} from './receiptsPresentation';

const WORDS = PAYMENTS_COPY.receipts;

export function Receipts() {
  const read = useReceipts();
  const rows = read.data;

  if (rows === undefined) {
    const offline = read.fetchStatus === 'paused';
    if (!offline && (read.error === null || read.isFetching)) return null;
    return (
      <View style={s.section}>
        <Text accessibilityRole="header" style={s.head}>
          {WORDS.title}
        </Text>
        {offline || read.error === null ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : (
          <View style={s.failure}>
            <Note variant="coral" accessibilityRole="alert">
              {recoveryMessage(read.error)}
            </Note>
            <Button
              label={PAYMENTS_COPY.readAgain}
              variant="secondary"
              size="sm"
              onPress={() => void read.refetch()}
            />
          </View>
        )}
      </View>
    );
  }

  // The day words are read against the moment the list arrived, as the deck's are.
  const at = read.dataUpdatedAt;

  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.head}>
        {WORDS.title}
      </Text>
      {rows.length === 0 ? (
        <Text style={s.empty}>{WORDS.empty}</Text>
      ) : (
        <>
          <Card style={s.rows}>
            {rows.map((receipt, index) => (
              <ReceiptRow
                key={`${receipt.seatChargeId}-${receipt.kind}`}
                receipt={receipt}
                at={at}
                divided={index > 0}
              />
            ))}
          </Card>
          <Text style={s.footer}>{WORDS.footer}</Text>
        </>
      )}
    </View>
  );
}

/**
 * **How each kind of row is drawn** — the lead square's glyph on its fill, and the amount's ink: a
 * share taken in ink on paper, a refund in the mint, a hold let go muted under an open lock.
 */
const LOOK: Readonly<
  Record<
    ReceiptKind,
    {
      readonly glyph: DoorRowGlyph;
      readonly glyphInk: string;
      readonly lead: string;
      readonly amountInk: string;
    }
  >
> = {
  CHARGE: {
    glyph: 'check',
    glyphInk: theme.color.night2,
    lead: theme.color.paper2,
    amountInk: theme.color.ink,
  },
  REFUND: {
    glyph: 'corner-up-left',
    glyphInk: theme.color.mintInk,
    lead: theme.color.mintSoft,
    amountInk: theme.color.mintInk,
  },
  RELEASED: {
    glyph: 'unlock',
    glyphInk: theme.color.muted,
    lead: theme.color.paper2,
    amountInk: theme.color.muted,
  },
};

function ReceiptRow({
  receipt,
  at,
  divided,
}: {
  readonly receipt: Receipt;
  readonly at: number;
  readonly divided: boolean;
}) {
  const day = receiptDayOf(receipt.startsAt, at);
  const note = receiptNote(receipt);
  const look = LOOK[receipt.kind];
  return (
    <View
      accessible
      accessibilityLabel={receiptLabel(receipt, day)}
      testID={`receipt-${receipt.seatChargeId}`}
      style={[s.row, divided ? s.divided : undefined]}
    >
      <View style={[s.mark, { backgroundColor: look.lead }]}>
        <Feather
          name={look.glyph}
          size={theme.size.rowLeadGlyph}
          color={look.glyphInk}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      </View>
      <View style={s.words}>
        <View style={s.top}>
          <Text style={s.club}>{receiptClub(receipt)}</Text>
          <Text style={[s.amount, { color: look.amountInk }]}>{receiptAmount(receipt)}</Text>
        </View>
        <Text style={s.line}>{receiptLine(receipt, day)}</Text>
        {note === undefined ? null : <Text style={s.line}>{note}</Text>}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // A section apart from the one above it, as LIVE YESES is from the method.
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  failure: { gap: theme.space.sm },
  empty: { ...theme.type.rlLabel, color: theme.color.muted },
  // The rows carry their own padding, so the card's is a step smaller (LIVE YESES').
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.md,
    paddingVertical: theme.space.sm,
  },
  // 5.5: the fold is drawn from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  // The door row's lead square (5.5 as amended), filled and marked by its kind (`LOOK`).
  mark: {
    width: theme.size.rowLead,
    height: theme.size.rowLead,
    borderRadius: theme.radius.rowLead,
    alignItems: 'center',
    justifyContent: 'center',
  },
  words: { flex: 1 },
  // The club and the amount share the first line; a long name wraps beside the amount.
  top: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.md },
  club: { ...theme.type.cardTitle, color: theme.color.ink, flex: 1 },
  line: { ...theme.type.tiny, color: theme.color.muted },
  amount: { ...theme.num.s, ...theme.tabular },
  footer: { ...theme.type.tiny, color: theme.color.muted },
});
