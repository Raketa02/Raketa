/**
 * **Rankings** — a ranking per sport, sorted by the level
 * ([#775](https://github.com/Raketa02/Raketa/issues/775); [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
 * the rankings screens §2–§5; rankings 2–11).
 *
 * **The header** (§2): ‹ back to Home, *Rankings* with *Competitive games only* under it, small and
 * grey, and on the right **the deck's own sport pill** (`SportPillFrame`, #774), offering all four
 * sports, the reader's rated ones first. Switching sport is a new read of the page.
 *
 * **Under it, *General | Friends*** (§3, #777): the view the phone remembers per account, General the
 * first time (`useRankingView`, which Home's trophy reads too). **Switching view is another page**,
 * read for that view: everything below the switch is the view's own.
 *
 * **Then the view** (§4, §5): the reader's place card — or the not-listed card in its place — then
 * the podium with three rows the reader sees, then the list on one white card, with the floating
 * *You · 212th* (#776, `RankingList`); *Nobody ranked in badminton yet* where nobody is listed.
 * **General** is read in pages of 50 (`useGeneral`); **Friends** whole (`useFriendsTable`), and where
 * no friend is listed its card is the page — *Just you so far*, or *None of your friends is ranked…*,
 * with **Add friends**, which opens `friends`' own Add friends sheet: your groups, and your link.
 * Both views hand the page one shape (`RankingRead`), so it is drawn once.
 *
 * **The page opens on** the sport it was asked for — the trophy's, or the one a pass returns to —
 * else the deck's last, else padel (`useRankingsSport`), and on the view the phone remembers. It draws
 * no switch until it knows the view, and nothing below it until it knows the sport too.
 *
 * **A pull reads the page again** — every page drawn, the main read with them: places move whenever a
 * result settles anywhere in Raketa. While the first read is out nothing is drawn under the header
 * but the pull; a refused read says why with *Try again*, and a read waiting for a connection says
 * so. **Another sport is another page**, read from its top.
 *
 * **Any face, row or podium step opens the full record**, a stranger's too; the reader's own opens
 * their own (§6). Whose record is up is this screen's state — route-local, as Members holds it — and
 * so is the Add friends sheet; both are drawn beside the screen's root, which is hidden from a
 * listener while either is up.
 *
 * **Pushed over Home, the Home column lit** (Q11): the shell lists `/rankings` inside Home's tab.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { RefreshControl, StyleSheet, Text, View } from 'react-native';

import { AddFriendsSheet } from '@/features/friends/types';
import { MyGroupMonogram, ReadFailure, groupMembersRoute } from '@/features/groups/types';
import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { offlineMessage } from '@/shared/errors';
import {
  Note,
  ScreenHeader,
  Segment,
  SportPillFrame,
  behindOverlay,
  theme,
  TopSafeArea,
  type SegmentOption,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { RANKING_VIEWS, belowTheCard, podiumOf, type RankedRow } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';
import type { RankingRead } from '../hooks/rankingRead';
import { useFriendsTable } from '../hooks/useFriendsTable';
import { useGeneral } from '../hooks/useGeneral';
import { useRankingsSport } from '../hooks/useRankingsSport';
import { useRankingView } from '../hooks/useRankingView';

import { PlaceCard } from './PlaceCard';
import { PodiumSteps } from './PodiumSteps';
import { RankingList } from './RankingList';
import { RANKINGS_COPY, RANKINGS_PILL_WORDS, VIEW_WORDS, nobodyRankedLine } from './rankingsCopy';

export interface RankingsScreenProps {
  /** The sport the page was opened on — the trophy's, or a pass's way back. Absent: the deck's, or padel. */
  readonly sport?: Sport;
}

/** §3: the switch's two views, General first. Built at the call — the barrels' cycle (`rankingsCopy`). */
function viewOptions(): readonly SegmentOption<RankingView>[] {
  return RANKING_VIEWS.map((view) => ({ key: view, label: VIEW_WORDS[view] }));
}

/** **Whose record is up**, and on which sport's page it was opened. */
interface RecordOpen {
  readonly subject: RecordSubject;
  readonly sport: Sport;
}

export function RankingsScreen({ sport: asked }: RankingsScreenProps) {
  const { sports, sport, pick } = useRankingsSport(asked);
  const { view, choose } = useRankingView();
  // The overlays are the screen's, drawn beside its root: `behindOverlay` hides what it holds.
  const [reading, setReading] = useState<RecordOpen>();
  const [adding, setAdding] = useState(false);

  const page =
    sport === undefined || view === undefined
      ? undefined
      : {
          sport,
          view,
          onOpen: (row: RankedRow) =>
            setReading({
              subject: { kind: row.isYou ? 'me' : 'player', playerId: row.playerId },
              sport,
            }),
          onAddFriends: () => setAdding(true),
        };

  return (
    <>
      <View style={s.root} {...behindOverlay(adding || reading !== undefined)}>
        <TopSafeArea style={s.screen}>
          <SportPillFrame
            sports={sports}
            sport={sport}
            onPick={pick}
            words={RANKINGS_PILL_WORDS}
            header={(pill) => (
              <ScreenHeader
                onBack={() => router.back()}
                backLabel={RANKINGS_COPY.back}
                title={RANKINGS_COPY.title}
                subline={RANKINGS_COPY.subline}
                right={pill}
              />
            )}
          >
            {view === undefined ? null : (
              <Segment options={viewOptions()} selected={view} onSelect={choose} style={s.switch} />
            )}
            {page === undefined ? null : page.view === 'GENERAL' ? (
              <GeneralView key={page.sport} {...page} />
            ) : (
              <FriendsView key={page.sport} {...page} />
            )}
          </SportPillFrame>
        </TopSafeArea>
      </View>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading.subject}
          sport={reading.sport}
        />
      )}

      {/* `friends`' own sheet: your groups — each opening its Members — and your friend link. */}
      <AddFriendsSheet
        visible={adding}
        onClose={() => setAdding(false)}
        groups={{
          tile: (groupId) => <MyGroupMonogram groupId={groupId} size="card" />,
          open: (groupId) => router.push(groupMembersRoute(groupId)),
        }}
      />
    </>
  );
}

/** **What a view's page is handed** — its sport and view, and the screen's two overlays to open. */
interface ViewPageProps {
  readonly sport: Sport;
  readonly view: RankingView;
  readonly onOpen: (row: RankedRow) => void;
  readonly onAddFriends: () => void;
}

/** General, for one sport: the list in pages — from the top, or around the reader after a jump. */
function GeneralView(props: ViewPageProps) {
  return <ViewPage {...props} read={useGeneral(props.sport)} />;
}

/** Friends, for one sport: the whole table, read at once. */
function FriendsView(props: ViewPageProps) {
  return <ViewPage {...props} read={useFriendsTable(props.sport)} />;
}

/**
 * **One view of one sport** — the card, then what stands below it (`belowTheCard`): the podium and the
 * list, *Nobody ranked in {sport} yet*, or nothing where the Friends card is the page.
 */
function ViewPage({
  sport,
  view,
  onOpen,
  onAddFriends,
  read,
}: ViewPageProps & { readonly read: RankingRead }) {
  const { ranking } = read;
  // A pull is the pull's own state, never the query's: a background refetch spins nothing, and a
  // pull spins until its read has landed, refused or not (ShellScreen's rule).
  const [pulling, setPulling] = useState(false);
  const pull = () => {
    if (pulling) return;
    setPulling(true);
    void read.reread().finally(() => setPulling(false));
  };

  const below = ranking === undefined ? undefined : belowTheCard(ranking);
  const podium = ranking === undefined ? undefined : podiumOf(ranking.podium);

  const top =
    ranking === undefined ? (
      read.error !== null ? (
        <ReadFailure error={read.error} onRetry={read.retry} />
      ) : read.paused ? (
        <Note variant="amber">{offlineMessage('resumes')}</Note>
      ) : null
    ) : (
      <>
        {ranking.card === undefined ? null : (
          <PlaceCard card={ranking.card} sport={sport} view={view} onAddFriends={onAddFriends} />
        )}
        {below === 'nobodyRanked' ? (
          <Text testID="nobody-ranked" style={s.nobody}>
            {nobodyRankedLine(sport)}
          </Text>
        ) : below === 'table' && podium !== undefined ? (
          <PodiumSteps podium={podium} onOpen={onOpen} />
        ) : null}
      </>
    );
  const shownRows = below === 'table' ? read.rows : [];

  return (
    <View style={s.page}>
      <RankingList
        window={read.window}
        rows={shownRows}
        header={
          <View style={s.header}>
            {read.atTheTop ? top : null}
            {read.earlierFailure === undefined ? null : (
              <ReadFailure error={read.earlierFailure.error} onRetry={read.earlierFailure.retry} />
            )}
          </View>
        }
        footer={
          read.laterFailure === undefined ? null : (
            <View style={s.footer}>
              <ReadFailure error={read.laterFailure.error} onRetry={read.laterFailure.retry} />
            </View>
          )
        }
        refreshControl={
          <RefreshControl
            refreshing={pulling}
            onRefresh={pull}
            tintColor={theme.color.muted}
            colors={[theme.color.muted]}
            progressBackgroundColor={theme.color.paper}
          />
        }
        onOpen={onOpen}
        onStartReached={read.loadEarlier}
        onEndReached={read.loadLater}
        jump={read.jump}
      />
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  screen: { flex: 1, backgroundColor: theme.color.paper },
  // §3: the switch under the header, at the gutter, `sm` above the card.
  switch: { marginHorizontal: theme.size.gutter, marginBottom: theme.space.sm },
  page: { flex: 1 },
  // The card, the podium — or what stands in their place — above the rows, `sm` apart and from them.
  header: { gap: theme.space.sm, paddingBottom: theme.space.sm },
  footer: { paddingTop: theme.space.sm },
  nobody: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    textAlign: 'center',
    paddingVertical: theme.space.xl,
  },
});
