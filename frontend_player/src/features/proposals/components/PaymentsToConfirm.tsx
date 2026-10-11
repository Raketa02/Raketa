/**
 * ***TO CONFIRM*** — the way back to a seat whose share was refused, on Home above the rail and on
 * You › Payments ([#555](https://github.com/Raketa02/Raketa/issues/555); the mechanics §12.2; the
 * screens A7.3; #541's `GET /players/me/payments-to-confirm`).
 *
 * The player whose own yes filled a game is shown the confirmation the moment their share is
 * refused. **Everybody else's share is refused while they are elsewhere** — somebody else's yes
 * filled the game, or its club said yes — and *Confirm your payment by 14:40 to keep your seat*
 * reaches them by email and a notice; this section is where the app keeps it until they do. A row is
 * the game, as a live yes is drawn — *Padel · Saturday 15:00* over the club, the share — and under
 * them **their time to pay** while it runs, *Confirm your payment by 14:40* in amber (Q109; the
 * words Home's card says beside it), or, once it ran out, that the seat is open to others until they
 * confirm. **Before the club's cut-off it is their time to fix the card** (#643; Q113): *Fix your
 * card by 14:40*, with a line that nothing is paid now, and the button **Fix** — a card refused at
 * the fill, at its club's yes, at the holding time of a game booked already (#639), or on a rescue
 * (#640). **Confirm** opens the fill's confirmation on that payment, naming the same time and
 * window. It is hidden when empty and while the first read is on its way; a read that failed says
 * so under the section's name.
 *
 * The time is written as Home writes it — the hour alone on the day of the read — and leaves the
 * row at the deadline on this phone's clock, the read naming no instant of its own; the server takes
 * it off the row too, and the notice that says so re-reads the list (`rereadHome`).
 *
 * The proposals feature's section — the read is the Proposals context's, and the confirmation is
 * the fill's — placed above *LIVE YESES* by the route file, as *LIVE YESES* is.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { Button, Card, Note, theme } from '@/shared/ui';

import { confirmationOf, type PaymentToConfirm } from '../domain/fill';
import { deadlineAhead, paymentWindowAt } from '../domain/home';
import { gameDayOf } from '../domain/when';
import { useFill } from '../hooks/useFill';
import { useReadClock } from '../hooks/useHome';
import { usePaymentsToConfirm } from '../hooks/useLiveYeses';

import { clubName, LINE_JOIN, shareWords } from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { toConfirmLabel, toConfirmRowLine } from './fillPresentation';
import { liveYesTitle } from './liveYesesPresentation';
import { ReadFailed } from './ReadFailed';

const WORDS = FILL_COPY.toConfirm;

export function PaymentsToConfirm() {
  const read = usePaymentsToConfirm();
  const fill = useFill();
  const list = read.data;
  // The read names no instant of its own, so the time leaves a row on this phone's clock, ticking
  // while one is there to pass — as Home's line leaves at the deadline.
  const now = useReadClock(
    undefined,
    read.dataUpdatedAt,
    list?.some((payment) => payment.confirmBy !== undefined) ?? false,
  );

  if (list === undefined) {
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
          <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
        )}
      </View>
    );
  }

  if (list.length === 0) return null;

  const readAt = read.dataUpdatedAt;
  const confirm = (payment: PaymentToConfirm) =>
    fill.confirm({
      dealtIn: { groupId: payment.groupId, sport: payment.sport, kind: payment.kind },
      ...confirmationOf(payment),
    });

  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.head}>
        {WORDS.title}
      </Text>
      <Card style={s.rows}>
        {list.map((payment, at) => {
          const day = gameDayOf(payment.startsAt, readAt);
          const by = deadlineAhead(payment.confirmBy, now);
          // Once the time is gone the row reads as the server's next read will: no window named.
          const paymentWindow = paymentWindowAt(payment.confirmBy, payment.timeTo, now);
          return (
            <View
              key={payment.seatChargeId}
              style={[s.row, at > 0 ? s.divided : undefined]}
              testID={`to-confirm-${payment.seatChargeId}`}
            >
              <View style={s.words}>
                <Text style={s.title}>{liveYesTitle(payment, day)}</Text>
                <Text
                  style={s.club}
                >{`${clubName(payment)}${LINE_JOIN}${shareWords(payment)}`}</Text>
                <Text style={by === undefined ? s.line : s.timeToPay}>
                  {toConfirmRowLine(by === undefined ? undefined : { by, window: paymentWindow })}
                </Text>
                {paymentWindow === 'FIX_THE_CARD' ? (
                  <Text style={s.line}>{WORDS.nothingPaidNow}</Text>
                ) : null}
              </View>
              <Button
                label={WORDS.action[paymentWindow]}
                accessibilityLabel={toConfirmLabel(payment, day, paymentWindow)}
                size="sm"
                onPress={() => confirm(payment)}
              />
            </View>
          );
        })}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  // LIVE YESES' section, for the same kind of list.
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  line: { ...theme.type.tiny, color: theme.color.muted },
  // Amber, the colour of *watch this — not yet wrong*: the seat is theirs until then (Q109).
  timeToPay: { ...theme.type.tiny, color: theme.color.amber },
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
  },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  words: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  club: { ...theme.type.tiny, color: theme.color.muted },
});
