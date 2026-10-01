/**
 * **A card on the Groups list** (play 1, 38) — the tile, the name on one line and ending in an
 * ellipsis (story 6), the sport dots and *N members*, the Home club, and a chevron. The whole card
 * is the door to the group's page, so it is one element named by all of it.
 *
 * **An official group's name carries the official mark** (`OfficialMark`), as it does on a club
 * card's rows and on the group's own header — sized off the card's `h2`, centred on the name's
 * line, a `space.xxs` after its last letter. The mark has no words, so the card's name says
 * *official*.
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { PressableCard, theme } from '@/shared/ui';

import type { MyGroup } from '../domain/group';

import { groupRoute } from './groupRoutes';
import { GroupMonogram } from './GroupMonogram';
import { groupCardLabel, membersLine } from './groupsPresentation';
import { OfficialMark } from './OfficialMark';
import { SportDots } from './SportDots';

export function GroupCard({ group }: { readonly group: MyGroup }) {
  return (
    <PressableCard
      accessibilityLabel={groupCardLabel(group)}
      onPress={() => router.push(groupRoute(group.id))}
      style={s.card}
    >
      <GroupMonogram monogram={group.monogram} size="card" />

      <View style={s.words}>
        <View style={s.nameRow}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          {group.kind === 'OFFICIAL' ? <OfficialMark fontSize={theme.type.h2.fontSize} /> : null}
        </View>
        <View style={s.meta}>
          <SportDots sports={group.sports} />
          <Text style={s.count} numberOfLines={1}>
            {membersLine(group.memberCount)}
          </Text>
        </View>
        <Text style={s.club} numberOfLines={1}>
          {group.homeClub.name}
        </Text>
      </View>

      <Feather
        name="chevron-right"
        size={theme.size.tabIcon}
        color={theme.color.muted}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </PressableCard>
  );
}

const s = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  words: { flex: 1, gap: theme.space.xxs },
  // The mark sits on the name's line, centred on it, a `space.xxs` after its last letter.
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  name: { ...theme.type.h2, color: theme.color.ink, flexShrink: 1 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  count: { ...theme.type.tiny, color: theme.color.muted },
  club: { ...theme.type.rlLabel, color: theme.color.ink },
});
