/**
 * **Add friends** — the sheet **+ Add friends** opens ([#754](https://github.com/Raketa02/Raketa/issues/754),
 * PRD #743 stories 39–41; the friends screens §5; friends 4).
 *
 * ```
 * Add friends                                 (×)
 * FROM YOUR GROUPS
 * ┌───────────────────────────────────────────┐
 * │ [Oo] Ogrody open play                   › │
 * │      8 members · 2 to add                 │
 * │ [Kc] Kazimierz crew                     › │
 * │      10 members · nobody to add           │
 * └───────────────────────────────────────────┘
 * ┌───────────────────────────────────────────┐
 * │ Not on Rakieta yet?                       │
 * │ [rakieta.app/f/tk4m9q2z          ] [Copy] │
 * │ [New link]                                │
 * └───────────────────────────────────────────┘
 * ```
 *
 * ## From your groups
 *
 * **Each of your groups, newest joined first** (the server's order): its tile, its name, and *8
 * members · 2 to add* — the server's count of members you could still ask: not you, not a friend,
 * nobody with an open request either way, nobody you blocked. **A tap opens that group's Members**,
 * where the pills ask; the sheet closes first, so *back* from Members is the page.
 *
 * **The groups are read when the sheet opens**, not with the page: a page opened to accept somebody
 * asks for nothing it does not draw. Every friends write re-reads them (`friendKeys`), so a request
 * asked on Members is off the count when the sheet next opens.
 *
 * ## The tile and the door are handed in
 *
 * The tile is the group's monogram, whose letters the server cuts once (ADR-0183 §5) and the
 * player's Groups list holds, and Members is a `groups` route; `groups` draws this feature's pills,
 * so the other way round would be a dependency both ways. The shell hands both in (`GroupDoors`). No
 * navigation hook is used inside the sheet either way: a sheet's content keeps the root's contexts
 * only (architecture Part 13).
 *
 * ## The link card under it
 *
 * The sheet's body is a column of sections, and the groups are the first. **The link card —
 * *Not on Rakieta yet?*, the link, *Copy*, *New link* — is the second** (`FriendLinkCard`, #756),
 * read when the sheet opens as the groups are; nothing about the groups' section assumes it is
 * alone.
 */

import Feather from '@expo/vector-icons/Feather';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { BottomSheet, Card, theme } from '@/shared/ui';

import type { GroupToAddFrom } from '../domain/friendList';
import { useGroupsToAddFrom } from '../hooks/useFriendLists';

import { FriendLinkCard } from './FriendLinkCard';
import { FRIENDS_COPY, groupCountsLine, groupRowLabel } from './friendsCopy';
import { ListReading } from './ListReading';

const COPY = FRIENDS_COPY.sheet;

/**
 * **The sheet's way into a group** — what `groups` owns and the shell hands in: the group's tile,
 * by id, and the push to its Members.
 */
export interface GroupDoors {
  readonly tile: (groupId: string) => ReactNode;
  readonly open: (groupId: string) => void;
}

export interface AddFriendsSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  readonly groups: GroupDoors;
}

export function AddFriendsSheet({ visible, onClose, groups }: AddFriendsSheetProps) {
  return (
    <BottomSheet visible={visible} onClose={onClose} title={COPY.title} closeLabel={COPY.close}>
      <View style={s.sections}>
        <FromYourGroups
          reading={visible}
          groups={groups}
          onOpen={(groupId) => {
            onClose();
            groups.open(groupId);
          }}
        />
        <FriendLinkCard reading={visible} />
      </View>
    </BottomSheet>
  );
}

function FromYourGroups({
  reading,
  groups,
  onOpen,
}: {
  readonly reading: boolean;
  readonly groups: GroupDoors;
  readonly onOpen: (groupId: string) => void;
}) {
  const read = useGroupsToAddFrom({ enabled: reading });
  const list = read.data;

  return (
    <View style={s.section}>
      <Text style={s.eyebrow} accessibilityRole="header">
        {COPY.fromYourGroups}
      </Text>
      {list === undefined ? (
        <ListReading read={read} reading={COPY.reading} />
      ) : list.length === 0 ? (
        <Text style={s.quiet}>{COPY.none}</Text>
      ) : (
        <Card style={s.rows}>
          {list.map((group, at) => (
            <GroupRow
              key={group.groupId}
              group={group}
              tile={groups.tile(group.groupId)}
              divided={at > 0}
              onPress={() => onOpen(group.groupId)}
            />
          ))}
        </Card>
      )}
    </View>
  );
}

function GroupRow({
  group,
  tile,
  divided,
  onPress,
}: {
  readonly group: GroupToAddFrom;
  readonly tile: ReactNode;
  readonly divided: boolean;
  readonly onPress: () => void;
}) {
  return (
    <Pressable
      testID={`add-from-${group.groupId}`}
      accessibilityRole="button"
      accessibilityLabel={groupRowLabel(group.name, group.memberCount, group.toAdd)}
      accessibilityHint={COPY.openMembers}
      onPress={onPress}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      {tile}
      <View style={s.words}>
        <Text style={s.name} numberOfLines={1}>
          {group.name}
        </Text>
        <Text style={s.counts}>{groupCountsLine(group.memberCount, group.toAdd)}</Text>
      </View>
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
  // 9 between stacked cards: the groups, and the link card under them.
  sections: { gap: theme.space.sm },
  section: { gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  rows: { paddingVertical: theme.space.xxs },
  // `DoorRow`'s row: `space.sm` above and below, past 6.5's minimum with the 38pt tile.
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
  },
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  // Words, not a figure: friends 4 draws the counts in the sans, as a DoorRow's live line.
  counts: { ...theme.type.tiny, color: theme.color.muted },
});
