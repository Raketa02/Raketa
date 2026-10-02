/**
 * **The administrator's Groups tab** (club 8, 9, 17; PRD #500 stories 122–124) — titled *Groups*,
 * with no eyebrow over it: the *OGRODY 33 · ADMINISTRATOR* club 17 draws there said only what the
 * bar under the screen already says (#529). The You tab keeps it, where it names whose profile it is.
 *
 * **+ New official group floats over the page's bottom corner**, in every state, as *+ Post a
 * game* does on a group's Fill in (#529): making a group never waits on the list, and the button
 * stays put however long the list grows. Under it the groups this Administrator runs at the club,
 * newest created first — or, before the first, one dark card saying what the job is (club 8, 9).
 * **Every state has its drawing**: nothing while the first read is on its way, and a failed read
 * says why and offers the retry, with the button still there to press.
 */

import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { Button, DarkCard, ScreenHeader, theme, TopSafeArea } from '@/shared/ui';

import { useAdministeredGroups } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { newOfficialGroupRoute } from './administratorRoutes';
import { OfficialGroupCard } from './OfficialGroupCard';

export function AdministratorGroupsScreen({ clubId }: { readonly clubId: string }) {
  const COPY = ADMINISTRATOR_COPY.groups;
  const read = useAdministeredGroups(clubId);
  const groups = read.data?.groups;

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader title={COPY.title} />

      <ScrollView contentContainerStyle={s.content}>
        {read.error !== null && groups === undefined ? (
          <ReadFailure error={read.error} onRetry={() => void read.refetch()} />
        ) : null}

        {groups !== undefined && groups.length === 0 ? (
          <DarkCard style={s.empty}>
            <Text accessibilityRole="header" style={s.emptyTitle}>
              {COPY.emptyTitle}
            </Text>
            <Text style={s.emptyLine}>{COPY.emptyLine}</Text>
          </DarkCard>
        ) : null}

        {groups?.map((group) => (
          <OfficialGroupCard key={group.id} clubId={clubId} group={group} />
        ))}
      </ScrollView>

      <View style={s.newGroup}>
        <Button
          label={COPY.newGroup}
          accessibilityLabel={COPY.newGroupLabel}
          size="lg"
          onPress={() => router.push(newOfficialGroupRoute(clubId))}
        />
      </View>
    </TopSafeArea>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    // The last card scrolls clear of the button floating over the corner, a gutter above it.
    paddingBottom: theme.size.btnLg + 2 * theme.size.gutter,
    gap: theme.space.sm,
  },
  // Over the page's bottom corner, at the gutter — Fill in's *+ Post a game* (play 46).
  newGroup: { position: 'absolute', right: theme.size.gutter, bottom: theme.size.gutter },
  empty: { alignItems: 'center', gap: theme.space.sm },
  // 3.3: `h2` titles a card — the dark card's headline, as the group page's link cards draw theirs.
  emptyTitle: { ...theme.type.h2, color: theme.color.surface, textAlign: 'center' },
  emptyLine: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
});
