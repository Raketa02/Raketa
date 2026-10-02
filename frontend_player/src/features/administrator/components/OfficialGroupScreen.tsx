/**
 * **An official group's page** — the Administrator's own view of it (club 11, 18, 19; PRD #500
 * stories 126–130; [#516](https://github.com/Raketa02/Raketa/issues/516)).
 *
 * Headed *OGRODY 33 · OFFICIAL* over the group's name, with a back arrow to the Groups tab. Top to
 * bottom:
 *
 * - **The link card** (`ShareLinkCard`) — the link, **Share link** and **Copy link**: the
 *   Administrator's one job, one tap.
 * - **Want to join · N**, club 20's card (`OfficialRequests`), only while somebody is waiting.
 * - **The players card** (`PlayersCard`) — the stacked faces, *N players* and the ring of how much
 *   of the group has arrived; a tap opens **Members** (#529).
 *
 * **There is no way to delete or leave the group**: running an official group is not membership,
 * and only the club moves it (ADR-0183 §7–§8). Its settings are the You tab's
 * ([#517](https://github.com/Raketa02/Raketa/issues/517)).
 *
 * Nothing is drawn under the header while the first read is on its way; a failed read says why, in
 * this page's words where it can name the failure — `group_not_found` for every group that is not
 * theirs — and offers the retry only where one can help.
 */

import { router } from 'expo-router';
import { ScrollView, StyleSheet } from 'react-native';

import { ReadFailure } from '@/features/groups/types';
import { codeMessage } from '@/shared/errors';
import { ScreenHeader, theme, TopSafeArea } from '@/shared/ui';

import { useAreaClubName } from '../hooks/useAreaAccess';
import { useOfficialGroup } from '../hooks/useOfficialGroups';

import { ADMINISTRATOR_COPY } from './administratorCopy';
import { officialEyebrow } from './administratorPresentation';
import { OfficialRequests } from './OfficialRequests';
import { PlayersCard } from './PlayersCard';
import { ShareLinkCard } from './ShareLinkCard';

export interface OfficialGroupScreenProps {
  readonly clubId: string;
  readonly groupId: string;
}

export function OfficialGroupScreen({ clubId, groupId }: OfficialGroupScreenProps) {
  const COPY = ADMINISTRATOR_COPY.group;
  const clubName = useAreaClubName(clubId);
  const read = useOfficialGroup(clubId, groupId);
  const group = read.data;

  return (
    <TopSafeArea style={s.screen}>
      <ScreenHeader
        eyebrow={officialEyebrow(clubName)}
        {...(group === undefined ? {} : { title: group.name })}
        onBack={() => router.back()}
        backLabel={COPY.back}
      />

      <ScrollView contentContainerStyle={s.content}>
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
            <PlayersCard clubId={clubId} group={group} />
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
    paddingBottom: theme.space.lg,
    gap: theme.space.sm,
  },
});
