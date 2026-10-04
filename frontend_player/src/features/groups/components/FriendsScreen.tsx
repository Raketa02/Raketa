/**
 * **Friends** — who the player could put on the court they are building, for one sport of one
 * group (play 54–55; PRD #500 story 70).
 *
 * **There is no friends feature**, and PRD #500 overrides play 49–56 by name: this screen always
 * shows its empty card — *Nobody you know here yet*, who would show up here, and the link's two
 * doors, because the only way anybody shows up is by joining with it. No list, no tags. The
 * eyebrow counts the court the player came from, *PADEL · 0 OF 3 PICKED*: everyone but the reader.
 *
 * The group is the page's read, already in the cache; a failure to read it is the page's own
 * block, with the page's words.
 */

import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { courtSeatCount, ScreenHeader, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { useGroup } from '../hooks/useGroups';

import { GROUPS_COPY } from './groupsCopy';
import { friendsLine, friendsPicked } from './groupsPresentation';
import { LinkCard } from './LinkCard';
import { ReadFailure } from './ReadFailure';

const COPY = GROUPS_COPY.friends;

export function FriendsScreen({
  groupId,
  sport,
}: {
  readonly groupId: string;
  readonly sport: Sport;
}) {
  const read = useGroup(groupId);
  const group = read.data;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader
        onBack={() => router.back()}
        backLabel={COPY.back}
        eyebrow={friendsPicked(sport, 0, courtSeatCount(sport) - 1)}
        title={COPY.title}
      />

      <View style={s.body}>
        {group !== undefined ? (
          <LinkCard group={group} headline={COPY.nobody} line={friendsLine(group.name)} />
        ) : read.error !== null ? (
          <ReadFailure
            error={read.error}
            message={codeMessage(GROUPS_COPY.group.refused, read.error)}
            onRetry={() => void read.refetch()}
          />
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { paddingHorizontal: theme.size.gutter, gap: theme.space.sm },
});
