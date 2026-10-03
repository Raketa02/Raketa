/**
 * **The recent notices — the list behind the bell on Home** ([#559](https://github.com/Raketa02/Raketa/issues/559);
 * the screens A9; the mechanics §17.2).
 *
 * ```
 * ‹ Notifications                                   HOME
 * ┌ It's a game! · you paid 30 zł              14:05 ›┐   newest first; the words the push used
 * │ Padel · Sat 16:00 · Bonarka Arena                 │
 * │ Someone left your game                Yesterday ›│
 * └───────────────────────────────────────────────────┘
 * ```
 *
 * **No mock draws it** — A9 says *a list reached from a bell on Home* and nothing more — so it is
 * Payments' receipts drawn again: one card of rows, the title and a line, *when* at the trailing
 * edge in mono, and a chevron on every row that opens something. **A row opens the game the notice
 * is about** (`useOpenNotice`), pushed over this list so *back* returns to it; a notice about a game
 * this build cannot name is listed, words and all, and opens nothing.
 *
 * **Nothing is marked read**: the backend keeps no seen marker, so the list is the newest thirty and
 * the bell carries no count. A pull re-reads it; so does a push arriving while the app is open.
 */

import Feather from '@expo/vector-icons/Feather';
import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { HOME_COPY, ShellScreen } from '@/features/shell/types';
import { Card, theme } from '@/shared/ui';

import { givenWhen, type Notice } from '../domain/notice';
import { notificationKeys } from '../hooks/notificationKeys';
import { useRecentNotices } from '../hooks/useRecentNotices';

import {
  NOTIFICATIONS_COPY,
  NOTIFICATIONS_TITLE,
  givenLine,
  noticeRowSpoken,
} from './notificationsCopy';
import { ReadState } from './ReadState';
import { useOpenNotice } from '../hooks/useOpenNotice';

const COPY = NOTIFICATIONS_COPY;

export function NoticesScreen() {
  const router = useRouter();
  const client = useQueryClient();
  const read = useRecentNotices();
  const open = useOpenNotice();
  const notices = read.data;
  // *When* is read against the moment the list arrived, as the receipts' days are.
  const now = new Date(read.dataUpdatedAt).toISOString();

  return (
    <ShellScreen
      eyebrow={HOME_COPY.title}
      title={NOTIFICATIONS_TITLE}
      onBack={router.back}
      onRefresh={() => client.invalidateQueries({ queryKey: notificationKeys.notices() })}
    >
      {notices === undefined ? (
        <ReadState read={read} loading={COPY.list.loading} />
      ) : notices.length === 0 ? (
        <Text style={s.quiet}>{COPY.list.empty}</Text>
      ) : (
        <Card style={s.rows}>
          {notices.map((notice, index) => (
            <NoticeRow
              key={notice.id}
              notice={notice}
              now={now}
              divided={index > 0}
              onOpen={open}
            />
          ))}
        </Card>
      )}
    </ShellScreen>
  );
}

function NoticeRow({
  notice,
  now,
  divided,
  onOpen,
}: {
  readonly notice: Notice;
  readonly now: string;
  readonly divided: boolean;
  readonly onOpen: ReturnType<typeof useOpenNotice>;
}) {
  const when = givenWhen(notice.givenAt, now);
  const said = when === undefined ? undefined : givenLine(when);
  const label = noticeRowSpoken(notice.title, notice.body, said);
  const target = notice.target;

  const words = (
    <>
      <View style={s.words}>
        <Text style={s.title}>{notice.title}</Text>
        <Text style={s.line}>{notice.body}</Text>
      </View>
      {said === undefined ? null : <Text style={s.when}>{said}</Text>}
    </>
  );

  if (target === undefined) {
    return (
      <View accessible accessibilityLabel={label} style={[s.row, divided ? s.divided : undefined]}>
        {words}
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={() => onOpen(target)}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      {words}
      <Feather
        name="chevron-right"
        size={theme.size.tabIcon}
        color={theme.color.muted}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  // The rows carry their own padding, so the card's is a step smaller (the receipts').
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
  },
  // 5.5: the fold from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  // 6.6: the press state for a row whose whole surface is the control.
  pressed: { opacity: 0.7 },
  words: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  // A time is a number, and every number is mono (1.4).
  when: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
});
