/**
 * **The administrator's Groups tab** (club 8, 9, 17; PRD #500 stories 122–124) — headed
 * *OGRODY 33 · ADMINISTRATOR / Groups*, club 17's header over club 8–9's (PRD #500 overrides 8–9's
 * person's name and switcher chip by name: the chip is the You tab's, #518).
 *
 * **+ New official group** first, in every state: making a group never waits on the list. Then the
 * groups this Administrator runs at the club, newest created first — or, before the first, one dark
 * card saying what the job is (club 8, 9). **Every state has its drawing**: nothing while the first
 * read is on its way, and a failed read says why and offers the retry, under the button that still
 * works.
 */

import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ReadFailure } from '@/features/groups/types';
import { Button, DarkCard, ScreenHeader, theme } from '@/shared/ui';

import { useAreaClubName } from '../hooks/useAreaAccess';
import { useAdministeredGroups } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { administratorEyebrow } from './administratorPresentation';
import { newOfficialGroupRoute } from './administratorRoutes';
import { OfficialGroupCard } from './OfficialGroupCard';

export function AdministratorGroupsScreen({ clubId }: { readonly clubId: string }) {
  const COPY = ADMINISTRATOR_COPY.groups;
  const clubName = useAreaClubName(clubId);
  const read = useAdministeredGroups(clubId);
  const groups = read.data?.groups;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader eyebrow={administratorEyebrow(clubName)} title={COPY.title} />

      <ScrollView contentContainerStyle={s.content}>
        <Button
          label={COPY.newGroup}
          accessibilityLabel={COPY.newGroupLabel}
          size="lg"
          onPress={() => router.push(newOfficialGroupRoute(clubId))}
        />

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
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
  empty: { alignItems: 'center', gap: theme.space.sm },
  // 3.3: `h2` titles a card — the dark card's headline, as the group page's link cards draw theirs.
  emptyTitle: { ...theme.type.h2, color: theme.color.surface, textAlign: 'center' },
  emptyLine: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
});
