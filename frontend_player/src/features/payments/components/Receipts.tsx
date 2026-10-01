/**
 * **RECEIPTS** — You › Payments' last section, under the method and the live yeses
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A7.3; mock 49; the
 * mechanics §12.1).
 *
 * ```
 * RECEIPTS
 * ┌──────────────────────────────────────────┐
 * │ [✓]  Bonarka Arena                −28 zł │   a charge: ✓ on paper2, the amount in ink
 * │      Padel · Today · 16:00               │
 * │──────────────────────────────────────────│
 * │ [↩]  Ogrody 33                 +26,58 zł │   a refund: ↩ on mintSoft, the amount in mintInk
 * │      Padel · Saturday · 18:00            │
 * └──────────────────────────────────────────┘
 * Refunds: BLIK within hours · cards up to two weeks.
 * ```
 *
 * **The club is the title** — the seller, named on every receipt (§12.1) — and the game under it.
 * Newest first, as the server orders them. **Empty, the section says what will land here**, and the
 * refund-timing footer is drawn only under rows, where a refund can be waited for.
 *
 * Rows are not buttons: a receipt is a record, and the game it was for is reached from Home. A
 * read on its way draws nothing — a missing list must not read as *nothing yet* — and a read that
 * failed says why under the section's name, with the retry.
 *
 * **The mint is a refund's**, settled money coming back — the colour's own meaning (Part 1) — on its
 * soft fill with the ink beside it, Rule C's pair; a charge stays in ink on the row lead's paper.
 */

import Feather from '@expo/vector-icons/Feather';
import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Card, Note, theme } from '@/shared/ui';

import { receiptDayOf, type Receipt } from '../domain/receipts';
import { useReceipts } from '../hooks/useReceipts';

import { PAYMENTS_COPY } from './paymentsCopy';
import { receiptAmount, receiptClub, receiptLabel, receiptLine } from './receiptsPresentation';

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
  const refund = receipt.kind === 'REFUND';
  return (
    <View
      accessible
      accessibilityLabel={receiptLabel(receipt, day)}
      testID={`receipt-${receipt.seatChargeId}`}
      style={[s.row, divided ? s.divided : undefined]}
    >
      <View style={[s.mark, refund ? s.markRefund : undefined]}>
        <Feather
          name={refund ? 'corner-up-left' : 'check'}
          size={theme.size.rowLeadGlyph}
          color={refund ? theme.color.mintInk : theme.color.night2}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      </View>
      <View style={s.words}>
        <Text style={s.club}>{receiptClub(receipt)}</Text>
        <Text style={s.line}>{receiptLine(receipt, day)}</Text>
      </View>
      <Text style={[s.amount, refund ? s.amountRefund : undefined]}>{receiptAmount(receipt)}</Text>
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
  // The door row's lead square (5.5 as amended), its glyph a charge's ✓ or a refund's ↩.
  mark: {
    width: theme.size.rowLead,
    height: theme.size.rowLead,
    borderRadius: theme.radius.rowLead,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markRefund: { backgroundColor: theme.color.mintSoft },
  words: { flex: 1 },
  club: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  amount: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
  amountRefund: { color: theme.color.mintInk },
  footer: { ...theme.type.tiny, color: theme.color.muted },
});
