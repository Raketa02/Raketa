/**
 * **LIVE YESES · n** — You › Payments' section: every yes on a game still filling, across groups,
 * each with what it would charge ([#554](https://github.com/Rakieta02/Rakieta/issues/554); the
 * screens A7.3; mock 48).
 *
 * ```
 * LIVE YESES · 3
 * ┌─────────────────────────────────────────┐
 * │ Padel · Saturday 15:00            28 zł │   the share in grey mono
 * │ Bonarka Arena                           │
 * ├─────────────────────────────────────────┤
 * │ …                                       │
 * └─────────────────────────────────────────┘
 * ```
 *
 * **Hidden when empty** (A7.3) — and while the first read is on its way, so the section never
 * flashes in and out. A read that failed says so under the head with the retry, and one held
 * offline says it resumes, since a missing list would read as *nothing live*.
 *
 * **A row opens the game's details** — the deck's own screen, under Play, for the group, sport and
 * kind the yes was said in. The count is every yes across sports, and there is no cap on it
 * (removed 2026-10-05).
 *
 * The rows are the deck's words for a game (`liveYesesPresentation`): *Saturday* as the court block
 * says it, against the instant the list was read.
 */

import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { offlineMessage } from '@/shared/errors';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { useOnReturn } from '@/shared/lib/platform';
import { Card, Note, theme } from '@/shared/ui';

import type { LiveYes } from '../domain/liveYes';
import { gameDayOf } from '../domain/when';
import { useLiveYeses } from '../hooks/useLiveYeses';

import {
  LIVE_YES_HINT,
  LIVE_YESES_TITLE,
  liveYesLabel,
  liveYesPlace,
  liveYesTitle,
  liveYesesHeader,
} from './liveYesesPresentation';
import { gameRoute } from './proposalRoutes';
import { ReadFailed } from './ReadFailed';

export function LiveYeses() {
  const router = useRouter();
  const read = useLiveYeses();
  // A game can fill by somebody else's yes, which no action of this player's would re-read: coming
  // back to the list is when it is read again.
  useOnReturn(() => void read.refetch());
  const list = read.data;

  if (list === undefined) {
    const offline = read.fetchStatus === 'paused';
    if (!offline && (read.error === null || read.isFetching)) return null;
    return (
      <View style={s.section}>
        <Text accessibilityRole="header" style={s.head}>
          {LIVE_YESES_TITLE}
        </Text>
        {offline || read.error === null ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : (
          <ReadFailed error={read.error} onRetry={() => void read.refetch()} />
        )}
      </View>
    );
  }

  if (list.yeses.length === 0) return null;

  const readAt = read.dataUpdatedAt;
  const header = liveYesesHeader(list.yeses.length);

  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.head}>
        {header}
      </Text>
      <Card style={s.rows}>
        {list.yeses.map((yes, at) => (
          <LiveYesRow
            key={yes.proposalId}
            yes={yes}
            readAt={readAt}
            divided={at > 0}
            onPress={() => router.push(gameRoute(yes.groupId, yes.proposalId, yes.sport, yes.kind))}
          />
        ))}
      </Card>
    </View>
  );
}

function LiveYesRow({
  yes,
  readAt,
  divided,
  onPress,
}: {
  readonly yes: LiveYes;
  readonly readAt: number;
  readonly divided: boolean;
  readonly onPress: () => void;
}) {
  const day = gameDayOf(yes.startsAt, readAt);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={liveYesLabel(yes, day)}
      accessibilityHint={LIVE_YES_HINT}
      onPress={onPress}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <View style={s.words}>
        <Text style={s.title}>{liveYesTitle(yes, day)}</Text>
        <Text style={s.club}>{liveYesPlace(yes)}</Text>
      </View>
      <Text style={s.share}>{formatZloty(yes.shareGrosze)}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // A section apart from the method above it, as the You tab's groups are from each other.
  section: { gap: theme.space.xs, paddingTop: theme.space.xs },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  // The rows carry their own padding, so the card's is a step smaller (the You tab's groups').
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    // `space.sm` above and below two lines of words is over 6.5's minimum by geometry.
    paddingVertical: theme.space.sm,
  },
  // 5.5: the fold is drawn from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  pressed: { opacity: 0.7 },
  words: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  club: { ...theme.type.tiny, color: theme.color.muted },
  share: { ...theme.num.s, ...theme.tabular, color: theme.color.muted },
});
