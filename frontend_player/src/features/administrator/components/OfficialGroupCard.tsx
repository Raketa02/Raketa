/**
 * **A card on the administrator's Groups tab** (club 17) — the tile, the name on one line with the
 * amber *N waiting* beside it, the sport dots and *N members*, the home club, and a chevron. The
 * whole card is the door to the group's page, so it is one element named by all of it.
 *
 * `groups`' `GroupCard`, with the one thing only an Administrator is shown: **who is waiting**.
 * Amber is *reversible, not yet wrong* — a request is an answer not given yet — and the tag carries
 * the word, so the colour is never the only carrier. Nothing is drawn while nobody waits.
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { GroupMonogram, membersLine, SportDots } from '@/features/groups/types';
import { PressableCard, Tag, theme } from '@/shared/ui';

import type { AdministeredGroup } from '../domain/officialGroup';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { officialCardLabel, waitingTag } from './administratorPresentation';
import { officialGroupRoute } from './administratorRoutes';

export function OfficialGroupCard({
  clubId,
  group,
}: {
  readonly clubId: string;
  readonly group: AdministeredGroup;
}) {
  return (
    <PressableCard
      accessibilityLabel={officialCardLabel(group)}
      accessibilityHint={ADMINISTRATOR_COPY.groups.groupHint}
      onPress={() => router.push(officialGroupRoute(clubId, group.id))}
      style={s.card}
    >
      <GroupMonogram monogram={group.monogram} size="card" />

      <View style={s.words}>
        <View style={s.title}>
          <Text style={s.name} numberOfLines={1}>
            {group.name}
          </Text>
          {group.waitingCount > 0 ? (
            <Tag label={waitingTag(group.waitingCount)} variant="warn" />
          ) : null}
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
  title: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // The name gives way to the tag, never the other way: *N waiting* is the card's news.
  name: { ...theme.type.h2, color: theme.color.ink, flexShrink: 1 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  count: { ...theme.type.tiny, color: theme.color.muted },
  club: { ...theme.type.rlLabel, color: theme.color.ink },
});
