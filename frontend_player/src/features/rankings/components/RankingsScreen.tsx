/**
 * **Rankings** — a ranking per sport, sorted by the level
 * ([#775](https://github.com/Rakieta02/Rakieta/issues/775); [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
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
 * the podium with the first three rows, then the list on one white card, with the floating
 * *You · 212th* (#776, `RankingList`); *Nobody ranked in badminton yet* where nobody is listed.
 * **General** is read in pages of 50 (`useGeneral`); **Friends** whole (`useFriendsTable`), and where
 * no friend is listed its card is the page — *Just you so far*, or *None of your friends is ranked…*,
 * with **Add friends**, which opens `friends`' own Add friends sheet: your groups, and your link.
 * Both views hand the page one shape (`RankingRead`), so it is drawn once.
 *
 * **The page opens on** the sport it was asked for — the trophy's, or the one a pass returns to —
 * else the deck's last, else padel (`useRankingsSport`), and on the view the phone remembers.
 *
 * **Until the page has something to draw, it shimmers below the header** (#870, PRD #867;
 * `RankingsSkeleton`): while the view or the sport is still unknown, a shape in the switch's place and
 * the view's skeleton under it; then the real switch, and the view's skeleton until its read finishes
 * — a card-sized block, three podium steps and rows on one white card. **Only for a sport and view
 * with nothing cached**: one read in the last few minutes opens at once, read again quietly behind
 * it. The content is drawn underneath and comes in on one cross-fade (`Reveal`), and once in it never
 * goes back to the skeleton — a pull keeps the page and spins the pull's own spinner. One
 * `SkeletonGround` under the header, so one band crosses the switch's place and the view's.
 *
 * **A pull reads the page again** — every page drawn, the main read with them: places move whenever a
 * result settles anywhere in Rakieta. A refused read says why with *Try again*, and a read waiting for
 * a connection says so, each in the skeleton's place; a read refused once and asked again is still on
 * its way, so the skeleton stays through Query's retries rather than a blank page, and *Try again* or
 * the connection back stands it again until the page is in. **Another sport is another page**, read
 * from its top. The sport and the view are reads too, under a reveal of their own, so a page that
 * comes cached fades in from the skeleton that stood while they were unknown.
 *
 * **Any face, row or podium step opens the full record**, a stranger's too; the reader's own opens
 * their own (§6). **Everybody is listed** (ADR-0204 §2, [#799](https://github.com/Rakieta02/Rakieta/issues/799)),
 * a player the reader blocked or who blocked them included, at their true place: a tap on them opens
 * the record sheet, which reads *This record isn't available* — the server's one refusal, the sheet's
 * own drawing of it. **The page draws no switch but General | Friends**: *Show me in General* and its
 * hidden card are gone. **A request asked from it is the ranking's** (#779), in the page's sport, so the
 * other person's Home reads *Found you in the padel ranking*; *Add friend* is offered where the record
 * says a request may be sent. Whose record is up is this screen's state — route-local, as Members holds it — and
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
  Reveal,
  ScreenHeader,
  Segment,
  SkeletonGround,
  SportPillFrame,
  behindOverlay,
  theme,
  TopSafeArea,
  useTabBarReach,
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
import { RankingSwitchSkeleton, RankingsSkeleton } from './RankingsSkeleton';

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
  // The page ends at the bar's reach, as a pinned screen does, and its rows do not pass under the bar
  // (#881): whether the reader's row is on screen — the jump button — and where a jump centres it are
  // the list's own measure of its frame, and FlatList takes no inset.
  const reach = useTabBarReach();
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
        <TopSafeArea style={[s.screen, { paddingBottom: reach }]}>
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
            {/* One ground under the header, so one band crosses the switch's place and the view's. */}
            <SkeletonGround style={s.below}>
              {/* The view and the sport are reads too: until both are known, the switch's place and
                  the view's shimmer, and a view already cached comes in on the fade. One not read
                  yet hands over to its own skeleton, the same shapes on the same band. */}
              <Reveal
                finished={page !== undefined}
                landed={page !== undefined}
                style={s.below}
                skeleton={
                  <>
                    <RankingSwitchSkeleton />
                    <RankingsSkeleton />
                  </>
                }
              >
                {page === undefined ? null : (
                  <>
                    <Segment
                      options={viewOptions()}
                      selected={page.view}
                      onSelect={choose}
                      style={s.switch}
                    />
                    {page.view === 'GENERAL' ? (
                      <GeneralView key={page.sport} {...page} />
                    ) : (
                      <FriendsView key={page.sport} {...page} />
                    )}
                  </>
                )}
              </Reveal>
            </SkeletonGround>
          </SportPillFrame>
        </TopSafeArea>
      </View>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading.subject}
          sport={reading.sport}
          // A request asked here is the ranking's, in the page's sport (#779).
          rankingSport={reading.sport}
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
  // The page's one read has finished — landed, refused after its retries, or held for a connection —
  // so what it drew, its failure or the offline note takes the skeleton's place. A read refused once
  // and asked again is still on its way: the skeleton stays, rather than a blank page — and so it
  // stands again when Try again or the connection back sets the read out with still nothing drawn.
  const finished = ranking !== undefined || read.error !== null || read.paused;

  return (
    <Reveal
      finished={finished}
      landed={ranking !== undefined}
      skeleton={<RankingsSkeleton />}
      style={s.page}
    >
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
    </Reveal>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  screen: { flex: 1, backgroundColor: theme.color.paper },
  below: { flex: 1 },
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
