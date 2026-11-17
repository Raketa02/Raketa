/**
 * The screens the shell composes under a tab's own words — **one of them here**, and none of
 * them a placeholder.
 *
 * Named components rather than one taking a `tab` prop: a route file's whole job is to say
 * which screen a path is, and `<HomeScreen />` says it where `<TabScreen tab="home" />` makes
 * the route file hold the answer as data. Play and You are the shell's too, in files of their
 * own because neither is thin.
 */

import { useQueryClient } from '@tanstack/react-query';
import { memo } from 'react';
import { StyleSheet, View } from 'react-native';

import {
  NewInRaketaRow,
  SameLevelRow,
  SameVibeRow,
  rereadDiscovery,
} from '@/features/discovery/types';
import {
  GROUPS_COPY,
  HomeLevelCard,
  HottestGroupsRow,
  rereadHomeGroups,
  useInNoGroup,
} from '@/features/groups/types';
import { NoticeBell, rereadNotices } from '@/features/notifications/types';
import {
  FriendsGamesRow,
  HomeRail,
  PaymentsToConfirm,
  rereadHome,
} from '@/features/proposals/types';
import { RankingTrophy, TopTenRow, rereadTopTen } from '@/features/rankings/types';
import { theme } from '@/shared/ui';

import { whenHomeStartsOver } from './homeStart';
import { NeedsYourAnswer } from './NeedsYourAnswer';
import { ShellScreen } from './ShellScreen';
import { HOME_COPY } from './shellCopy';

/**
 * **Home — the landing, after onboarding** ([#367](https://github.com/Raketa02/Raketa/issues/367)).
 * It was **Now** until [#550](https://github.com/Raketa02/Raketa/issues/550) renamed the tab whole
 * — key, label, copy and this component — with the route staying `/`.
 *
 * **Booked games only** ([#576](https://github.com/Raketa02/Raketa/issues/576)): the player's
 * booked games and the ones waiting for a club, on `features/proposals`' rail. The tab keeps the
 * shape it has always had — it owns its own words and nothing that is drawn under them — so the
 * empty sentences are handed down and the heading over the rail is the rail's.
 *
 * **It still never says nothing is happening.** The line says what the tab **is** and the one under
 * it names the act, which is true whether or not a game is on screen.
 *
 * **A payment to confirm is above the rail** — proposals' *TO CONFIRM*, which draws nothing while
 * there is none: the bar's Home badge counts every payment the player has to confirm, and a count
 * with nothing on the tab to answer it would be a dead end.
 *
 * **A member of a group rated in nothing is asked for a level first** (`groups`' `HomeLevelCard`,
 * [#731](https://github.com/Raketa02/Raketa/issues/731), ADR-0200 §7): *Get your level — your
 * groups can't deal you games until you have one.*, at the top, since until she has one nothing
 * under it can happen. It draws nothing for anybody else.
 *
 * **FRIENDS GAME sits at the very top** (`proposals`' row, [#759](https://github.com/Raketa02/Raketa/issues/759);
 * the friends screens §6; Q13: *Friends game → Friend requests → Your games*), drawn only while an
 * invitation waits on the reader — above *TO CONFIRM* too: an invitation runs out in hours, and the
 * mechanics put it at the very top. Answering one re-reads the bell, handed in as for requests.
 *
 * **FRIEND REQUESTS and ASKED FOR A LEVEL are behind the envelope** ([#816](https://github.com/Raketa02/Raketa/issues/816),
 * ADR-0205 §1): `friends`' sections in **Needs your answer**, the sheet the header's envelope opens
 * (`NeedsYourAnswer`). They were Home's rows above Your games from #753 and #765, and the ask no longer
 * stands in place of *Get your level*, which is drawn whether or not someone asked.
 *
 * **The header reads envelope, bell, trophy** (ADR-0205 §2; home refactor 1): the envelope only while
 * something waits for an answer; `notifications`' bell; and `rankings`' `RankingTrophy`
 * ([#775](https://github.com/Raketa02/Raketa/issues/775)), the reader's General place and the way to
 * Rankings, in the far-right corner. The slot is right-aligned, so without the envelope the bell and
 * the trophy stand where they were.
 *
 * **The five Home rows stand below *Your games*** (ADR-0204; the Home rows screens §1), each reading on
 * its own so a slow or failed one holds up nothing — **HOTTEST GROUPS** first (`groups`' row,
 * [#800](https://github.com/Raketa02/Raketa/issues/800)). The pull re-reads them with Home's own.
 * **A reader in no group** reads *Join a group to get games — the hottest ones are just below.* where
 * *Play finds you one.* stood (§31.1): the line points at the row under it, and whether the reader is
 * in a group is `groups`' answer, its words `groups`' too.
 *
 * **NEW IN RAKETA follows it** (`discovery`'s row, [#801](https://github.com/Raketa02/Raketa/issues/801)),
 * the third of the five: Same competitive level (#802) will stand between them. The pull re-reads it
 * with the rest. **A friend act anywhere moves a person on it** — an answer on FRIEND REQUESTS, the
 * record a face opens — because its reads list people (`LISTS_PEOPLE`) and every friend write reaches
 * those; the shell hands it nothing for that.
 *
 * **TOP 10 is the last** (`rankings`' row, [#805](https://github.com/Raketa02/Raketa/issues/805)), after
 * Same vibe: General's first ten in one sport, with its own sport pill and *Rankings ›*. A pick there
 * re-reads that row alone; the pull re-reads it with the rest (`rereadTopTen`).
 *
 * **Memoised, because it is kept** (`TAB_STACK`): Home stays mounted under every tab, and the route
 * that draws it is drawn again on every move the navigator makes — so without `memo` every press of
 * every tab re-rendered every row, card and poster on Home, nothing having changed, and a device
 * spent most of a second on it. It takes no props; what it reads, it reads for itself.
 */
export const HomeScreen = memo(function HomeScreen() {
  const client = useQueryClient();
  const inNoGroup = useInNoGroup();
  return (
    <ShellScreen
      title={HOME_COPY.title}
      watchesOnScreen
      startsOverWhen={whenHomeStartsOver}
      right={
        <View style={s.headerRight}>
          <NeedsYourAnswer />
          <NoticeBell />
          <RankingTrophy />
        </View>
      }
      onRefresh={() =>
        Promise.all([
          rereadHome(client),
          rereadHomeGroups(client),
          rereadDiscovery(client),
          rereadTopTen(client),
        ])
      }
    >
      <HomeLevelCard />
      <FriendsGamesRow onAnswered={() => rereadNotices(client)} />
      <PaymentsToConfirm />
      <HomeRail
        empty={
          inNoGroup ? { ...HOME_COPY.empty, act: GROUPS_COPY.hottest.groupless } : HOME_COPY.empty
        }
      />
      <HottestGroupsRow />
      <SameLevelRow />
      <NewInRaketaRow />
      <SameVibeRow />
      <TopTenRow />
    </ShellScreen>
  );
});

const s = StyleSheet.create({
  // The envelope and the bell, each in its own 44pt target, then the trophy's pill in the corner.
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
});
