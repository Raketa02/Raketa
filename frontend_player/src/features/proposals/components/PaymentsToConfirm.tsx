/**
 * ***TO CONFIRM*** — You › Payments' way back to a seat whose share was refused
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the mechanics §12.2; #541's `GET
 * /players/me/payments-to-confirm`).
 *
 * The player whose own yes filled a game is shown the confirmation the moment their share is
 * refused. **Everybody else's share is refused while they are elsewhere** — somebody else's yes
 * filled the game — and *Confirm your payment to keep your seat* reaches them by email and, once
 * built, a notice (#559); this section is where the app keeps it until they do. A row is the game,
 * as a live yes is drawn — *Padel · Saturday 15:00* over the club, the share — and **Confirm** opens
 * the fill's confirmation on that payment. It is hidden when empty and while the first read is on
 * its way; a read that failed says so under the section's name.
 *
 * The proposals feature's section — the read is the Proposals context's, and the confirmation is
 * the fill's — placed above *LIVE YESES* by the route file, as *LIVE YESES* is.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { Button, Card, Note, theme } from '@/shared/ui';

import type { PaymentToConfirm } from '../domain/fill';
import { gameDayOf } from '../domain/when';
import { useFill } from '../hooks/useFill';
import { usePaymentsToConfirm } from '../hooks/useLiveYeses';

import { clubName, LINE_JOIN, shareWords } from './deckPresentation';
import { FILL_COPY } from './fillCopy';
import { toConfirmLabel } from './fillPresentation';
import { liveYesTitle } from './liveYesesPresentation';
import { ReadFailed } from './ReadFailed';

const WORDS = FILL_COPY.toConfirm;

export function PaymentsToConfirm() {
  const read = usePaymentsToConfirm();
  const fill = useFill();
  const list = read.data;

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
      seatChargeId: payment.seatChargeId,
      dealtIn: { groupId: payment.groupId, sport: payment.sport, kind: payment.kind },
    });

  return (
    <View style={s.section}>
      <View
        accessible
        accessibilityRole="header"
        accessibilityLabel={`${WORDS.title}, ${WORDS.line}`}
      >
        <Text style={s.head}>{WORDS.title}</Text>
        <Text style={s.line}>{WORDS.line}</Text>
      </View>
      <Card style={s.rows}>
        {list.map((payment, at) => {
          const day = gameDayOf(payment.startsAt, readAt);
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
              </View>
              <Button
                label={WORDS.action}
                accessibilityLabel={toConfirmLabel(payment, day)}
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
