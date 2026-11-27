/**
 * **An official group's page** — the Administrator's own view of it (club 11, 18, 19; PRD #500
 * stories 126–130; [#516](https://github.com/Raketa02/Raketa/issues/516)).
 *
 * Headed by the group's name alone, with a back arrow to the Groups tab — no eyebrow over it: club
 * 11's *OGRODY 33 · OFFICIAL* said what every group in this area is, at the club the area is already
 * for (#529, as the Groups tab's went). Top to bottom:
 *
 * - **The link card** (`ShareLinkCard`) — the link, **Share link** and **Copy link**: the
 *   Administrator's one job, one tap.
 * - **Want to join · N**, club 20's card (`OfficialRequests`), only while somebody is waiting.
 * - **The members card** (`MembersCard`) — the stacked faces, *N members* and the ring of how much
 *   of the group has arrived; a tap opens **Members** (#529).
 *
 * **There is no way to delete or leave the group**: running an official group is not membership,
 * and only the club moves it (ADR-0183 §7–§8). Its settings are the You tab's
 * ([#517](https://github.com/Raketa02/Raketa/issues/517)).
 *
 * **A pull reads the group again** (#529), as the Groups tab's does: somebody who asked or arrived
 * on another phone is on the page when the spinner stops, where they waited for a return to it.
 *
 * Nothing is drawn under the header while the first read is on its way; a failed read says why, in
 * this page's words where it can name the failure — `group_not_found` for every group that is not
 * theirs — and offers the retry only where one can help.
 */

import { router } from 'expo-router';
import { RefreshControl, ScrollView, StyleSheet } from 'react-native';

import { ReadFailure, usePull } from '@/features/groups/types';
import { codeMessage } from '@/shared/errors';
import { ScreenHeader, theme, TopSafeArea, useTabBarReach } from '@/shared/ui';

import { useOfficialGroup, useOfficialGroupReread } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { MembersCard } from './MembersCard';
import { OfficialRequests } from './OfficialRequests';
import { ShareLinkCard } from './ShareLinkCard';

export interface OfficialGroupScreenProps {
  readonly clubId: string;
  readonly groupId: string;
}

export function OfficialGroupScreen({ clubId, groupId }: OfficialGroupScreenProps) {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  const COPY = ADMINISTRATOR_COPY.group;
  const read = useOfficialGroup(clubId, groupId);
  const group = read.data;
  const { refreshing, pull } = usePull(useOfficialGroupReread(clubId, groupId));

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader
        {...(group === undefined ? {} : { title: group.name })}
        onBack={() => router.back()}
        backLabel={COPY.back}
      />

      <ScrollView
        testID="official-group-page"
        contentContainerStyle={[s.content, { paddingBottom: reach + theme.space.lg }]}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={pull}
            tintColor={theme.color.muted}
            colors={[theme.color.muted]}
            progressBackgroundColor={theme.color.paper}
          />
        }
      >
        {group === undefined && read.error !== null ? (
          <ReadFailure
            error={read.error}
            message={codeMessage(COPY.refused, read.error)}
            onRetry={() => void read.refetch()}
          />
        ) : null}

        {group === undefined ? null : (
          <>
            <ShareLinkCard group={group} />
            <OfficialRequests clubId={clubId} groupId={groupId} requests={group.requests} />
            <MembersCard clubId={clubId} group={group} />
          </>
        )}
      </ScrollView>
    </TopSafeArea>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
  },
});
