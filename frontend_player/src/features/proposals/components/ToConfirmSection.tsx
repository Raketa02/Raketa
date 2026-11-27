/**
 * **TO CONFIRM · n** — Needs your answer's first section: one tile per payment to confirm
 * ([#817](https://github.com/Raketa02/Raketa/issues/817), ADR-0205 §1; Q14, Q32). It was Home's one
 * card of stacked rows above the rail from [#555](https://github.com/Raketa02/Raketa/issues/555);
 * You › Payments keeps that card (`PaymentsToConfirm`).
 *
 * ```
 * TO CONFIRM · 2
 * ┌───────────────────────────────┐ ┌──────
 * │ Padel · Saturday 15:00        │ │ Padel
 * │ Bonarka Arena · 32 zł         │ │ Ogrod
 * │ Confirm your payment by 14:40 │ │ Fix y   ← amber while the time runs
 * │                               │ │ Nothi   ← *Nothing is paid now*, before the cut-off
 * │ ┌────────── Confirm ────────┐ │ │ ┌───
 * └───────────────────────────────┘ └──────
 * ```
 *
 * ## First, because a seat is held
 *
 * **A seat in a booked game is held for the player until their time runs out**, so it is the most
 * urgent thing that waits on them and comes first in the sheet (Q14, Q32). Home's tab badge still
 * counts it, and the notice and the email still carry the deadline.
 *
 * ## One tile per payment, on the peeking rail
 *
 * Each tile says what the row says (`toConfirmWords`, one reading for both): the game as a live yes
 * is drawn — *Padel · Saturday 15:00* — over the club and the share, then **their time to pay** while
 * it runs, *Confirm your payment by 14:40* in amber, or before the club's cut-off *Fix your card by
 * 14:40* with *Nothing is paid now* under it (Q109, Q113). **The time leaves the tile at the
 * deadline**, on this phone's clock, as it left the row: the seat is open to others then, and the tile
 * says it is theirs to take back while it is free — until the server's next read takes the payment
 * off. **Confirm** or **Fix** opens the fill's confirmation on that payment, naming the same time and
 * window, drawn over the sheet.
 *
 * 7.7's peeking rail at its standard 0.74 — the one wider card is the friend request's — **every tile
 * as tall as the tallest, its title held to two lines and its button at the foot**, so the buttons
 * sit level across the rail (Q3), as the sheet's other tiles do. A lone tile takes the content width.
 *
 * ## Only while a payment waits
 *
 * **The section and its title are there only while they hold a tile.** Nothing is drawn while the
 * read is in flight, refused or empty: the sheet says no failure of its own, and a failed read is
 * counted as nothing, so it draws no envelope by itself (ADR-0205 §3; decision log §3.6) — Home's
 * usual re-reads retry, and the notice and the email carry the deadline.
 *
 * ## Home's read, not their own
 *
 * **The rows are Home's `payments_to_confirm`** (#815, #819), the same rows as
 * `GET /players/me/payments-to-confirm` — which You › Payments keeps — and nothing re-sorts them.
 * The sheet's four sections come from the one read whose watermark the visit names, so what it
 * marks seen is exactly what was shown.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, HomeRow, HomeRowRail, theme } from '@/shared/ui';

import { confirmAskOf, type PaymentToConfirm } from '../domain/fill';
import { useFill } from '../hooks/useFill';
import { useHomePaymentsToConfirm, useReadClock } from '../hooks/useHome';

import { FILL_COPY } from './fillCopy';
import { toConfirmHeading, toConfirmWords } from './fillPresentation';

/** The most lines a tile's title takes, so its button sits level with the next tile's. */
const TITLE_LINES = 2;

export function ToConfirmSection() {
  const read = useHomePaymentsToConfirm();
  const fill = useFill();
  const list = read.data;
  // The time leaves a tile on this phone's clock, as it leaves the You › Payments row, ticking while
  // one is there to pass — as Home's line leaves at the deadline.
  const now = useReadClock(
    undefined,
    read.dataUpdatedAt,
    list?.some((payment) => payment.confirmBy !== undefined) ?? false,
  );

  if (list === undefined || list.length === 0) return null;

  return (
    <HomeRow heading={toConfirmHeading(list.length)} testID="to-confirm">
      <HomeRowRail cards={list}>
        {(payment, width) => (
          <ToConfirmTile
            key={payment.seatChargeId}
            payment={payment}
            readAt={read.dataUpdatedAt}
            now={now}
            width={width}
            onConfirm={() => fill.confirm(confirmAskOf(payment))}
          />
        )}
      </HomeRowRail>
    </HomeRow>
  );
}

interface ToConfirmTileProps {
  readonly payment: PaymentToConfirm;
  /** When the read landed — what *Saturday* is said against. */
  readonly readAt: number;
  readonly now: number;
  readonly width: number;
  readonly onConfirm: () => void;
}

function ToConfirmTile({ payment, readAt, now, width, onConfirm }: ToConfirmTileProps) {
  const words = toConfirmWords(payment, readAt, now);
  return (
    <Card style={[s.tile, { width }]}>
      <View style={s.body} testID={`to-confirm-${payment.seatChargeId}`}>
        <View style={s.words}>
          <Text style={s.title} numberOfLines={TITLE_LINES}>
            {words.title}
          </Text>
          <Text style={s.line}>{words.place}</Text>
          <Text style={words.running ? s.timeToPay : s.line}>{words.time}</Text>
          {words.nothingPaidNow ? (
            <Text style={s.line}>{FILL_COPY.toConfirm.nothingPaidNow}</Text>
          ) : null}
        </View>
        <Button
          label={words.action}
          accessibilityLabel={words.spoken}
          size="lg"
          onPress={onConfirm}
          style={s.button}
        />
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  // A tile waiting on the reader: 5.1's selected border, as the sheet's other tiles.
  tile: { borderColor: theme.color.ink },
  // The tile's whole height — the rail stands it as tall as the tallest — so the foot is its foot.
  body: { flex: 1, gap: theme.space.md },
  words: { gap: theme.space.xxs },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  // Amber, the colour of *watch this — not yet wrong*: the seat is theirs until then (Q109).
  timeToPay: { ...theme.type.tiny, color: theme.color.amber },
  // At the foot, so the buttons sit level across the rail (Q3).
  button: { marginTop: 'auto' },
});
