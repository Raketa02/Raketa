/**
 * **A group's page — its header, for now** (play 40; #512). Back, the group's tile, its name and
 * *N members · Home club*, both lines ending in an ellipsis. The sport pill and the four tabs
 * under it are [#513](https://github.com/Raketa02/Raketa/issues/513)'s.
 *
 * Reached from a card on the Groups list, and **replacing** New group once a group is created, so
 * *back* from here is the list either way. A group created a moment ago is drawn at once — the
 * create's answer seeded its read — with *Group created* over it.
 *
 * **Every state has its drawing.** While the read is on its way the header has only its way back.
 * `group_not_found` is one sentence, because the server gives the same answer for *no such group*
 * and *not one of yours* and both have one remedy; any other failure says why and offers the retry.
 */

import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { codeMessage } from '@/shared/errors';
import { ScreenHeader, theme } from '@/shared/ui';

import { useGroup } from '../hooks/useGroups';

import { GroupMonogram } from './GroupMonogram';
import { GROUPS_COPY } from './groupsCopy';
import { ReadFailure } from './ReadFailure';
import { membersAtClub } from './groupsPresentation';

const COPY = GROUPS_COPY.group;

export function GroupScreen({ groupId }: { readonly groupId: string }) {
  const read = useGroup(groupId);
  const group = read.data;

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader
        compact
        onBack={() => router.back()}
        backLabel={COPY.back}
        lead={
          group === undefined ? undefined : (
            <GroupMonogram monogram={group.monogram} size="header" />
          )
        }
        title={group?.name}
        subline={
          group === undefined ? undefined : membersAtClub(group.memberCount, group.homeClub.name)
        }
      />

      {read.error !== null && group === undefined ? (
        <View style={s.body}>
          <ReadFailure
            error={read.error}
            message={codeMessage(COPY.refused, read.error)}
            onRetry={() => void read.refetch()}
          />
        </View>
      ) : null}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { paddingHorizontal: theme.size.gutter, gap: theme.space.sm },
});
