/**
 * **Blocked players** — everyone the reader blocked, each with **Unblock**, pushed over the You tab
 * from its ACCOUNT group ([#587](https://github.com/Raketa02/Raketa/issues/587), PRD #571 stories
 * 19–21; [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
 * §3).
 *
 * **The way back from a mistake when the record is out of reach**: a block hides nobody, so their
 * record is usually a face away — but not always, and a control nobody can undo is a control people
 * are afraid to use.
 *
 * **The list is the server's, in its order** — newest first — and only the reader's own blocks: each
 * row is the face (their photograph, or their generated poster), the whole name, and *Unblock*,
 * spoken with the name, since a column of *Unblock*s says nothing about whose. **An unblock takes
 * the row away at once**: the answer is certain, nothing comes back with it, and the list is read
 * again to agree. Empty is said plainly — *You haven't blocked anyone.* — so it is never taken for
 * a failure, and a failure is the recovery sentence with *Try again*, never an empty list.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Card, Note, PlayerPhoto, theme } from '@/shared/ui';

import type { BlockedPlayer } from '../domain/blockedPlayer';
import { useBlockedPlayers } from '../hooks/useBlockedPlayers';
import { useUnblock } from '../hooks/useBlockWrites';

import { BLOCKS_COPY, unblockRowLabel } from './blocksCopy';
import { WriteNote } from './WriteNote';

const COPY = BLOCKS_COPY.blockedPlayers;

/** 7.19's people-list face — Members' and *Want to join*'s, spelled beside its callers as they do. */
const ROW_FACE = 38;

export function BlockedPlayersScreen() {
  const router = useRouter();
  const read = useBlockedPlayers();
  const blocked = read.data;

  return (
    <ShellScreen eyebrow={YOU_COPY.groups.account} title={COPY.title} onBack={router.back}>
      {blocked === undefined ? (
        <Reading read={read} />
      ) : blocked.length === 0 ? (
        <Text style={s.quiet}>{COPY.empty}</Text>
      ) : (
        <Card style={s.rows}>
          {blocked.map((player, at) => (
            <BlockedRow key={player.playerId} player={player} divided={at > 0} />
          ))}
        </Card>
      )}
    </ShellScreen>
  );
}

/** The list on its way: offline, refused, or being read. */
function Reading({ read }: { readonly read: ReturnType<typeof useBlockedPlayers> }) {
  if (read.fetchStatus === 'paused') {
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  }
  if (read.error === null || read.isFetching) return <Text style={s.quiet}>{COPY.loading}</Text>;
  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {recoveryMessage(read.error)}
      </Note>
      <Button
        label={COPY.readAgain}
        variant="secondary"
        size="sm"
        onPress={() => void read.refetch()}
        style={s.again}
      />
    </View>
  );
}

function BlockedRow({
  player,
  divided,
}: {
  readonly player: BlockedPlayer;
  readonly divided: boolean;
}) {
  const unblocking = useUnblock(player.playerId);

  return (
    <View testID={`blocked-${player.playerId}`} style={[s.entry, divided ? s.divided : undefined]}>
      <View style={s.row}>
        <PlayerPhoto
          playerId={player.playerId}
          {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
          box={{ kind: 'face', size: ROW_FACE }}
        />
        <Text style={s.name} numberOfLines={1}>
          {player.name}
        </Text>
        <Button
          label={COPY.unblock}
          variant="secondary"
          size="sm"
          busy={unblocking.isPending}
          busyLabel={BLOCKS_COPY.unblocking}
          // Whose, said: a column of *Unblock*s names nobody. The busy word speaks for itself.
          {...(unblocking.isPending ? {} : { accessibilityLabel: unblockRowLabel(player.name) })}
          onPress={() => unblocking.mutate()}
        />
      </View>
      <WriteNote write={unblocking} />
    </View>
  );
}

const s = StyleSheet.create({
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  failure: { gap: theme.space.sm },
  again: { alignSelf: 'flex-start' },
  // The rows carry their own padding, so the card's is a step smaller (the You tab's groups').
  rows: { paddingVertical: theme.space.xxs },
  entry: { gap: theme.space.xs, paddingVertical: theme.space.sm },
  // 5.5: the fold from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flex: 1 },
});
