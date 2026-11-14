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
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import {
  NewInRaketaRow,
  SameLevelRow,
  SameVibeRow,
  rereadDiscovery,
} from '@/features/discovery/types';
import { FriendRequestsRow, LevelAsksRow } from '@/features/friends/types';
import {
  GROUPS_COPY,
  HomeLevelCard,
  HottestGroupsRow,
  rereadHomeGroups,
  useInNoGroup,
} from '@/features/groups/types';
import { NoticeBell, OPEN_NOTICE_WORDS, rereadNotices } from '@/features/notifications/types';
import { PlayerRecordSheet, PlayerScoreTag } from '@/features/player_record/types';
import {
  FriendsGamesRow,
  HomeRail,
  PaymentsToConfirm,
  rereadHome,
} from '@/features/proposals/types';
import { RankingTrophy } from '@/features/rankings/types';
import { theme } from '@/shared/ui';

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
 * **FRIEND REQUESTS sits above Your games** (`friends`' row, [#753](https://github.com/Raketa02/Raketa/issues/753);
 * the friends screens §6; Q13), drawn only while a request waits. The shell hands it the two things
 * that are `player_record`'s — the reliability chip, and the record a face opens — so `friends` does
 * not import the feature that draws its record button; and the bell's re-read, since answering a
 * request takes its row off the bell.
 *
 * **ASKED FOR A LEVEL sits under it** (`friends`' row, [#765](https://github.com/Raketa02/Raketa/issues/765);
 * the friends screens §6.4; Q129), drawn only while a friend's ask waits, handed the same record and
 * bell, and the *level asked* notice's toast for a start that fails. **For a player rated in nothing
 * it stands in place of *Get your level*** — `groups`' rule, which reads the same Home.
 *
 * **The trophy stands just left of the bell** (`rankings`' `RankingTrophy`, [#775](https://github.com/Raketa02/Raketa/issues/775);
 * the rankings screens §1; Q13): the reader's General place in the sport of their latest result, and
 * the way to Rankings — the bell keeps the corner.
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
 * record a face opens — because its reads list people (`LISTS_PEOPLE`) and every friend write re-reads
 * those; the shell hands it nothing for that.
 */
export function HomeScreen() {
  const client = useQueryClient();
  const inNoGroup = useInNoGroup();
  return (
    <ShellScreen
      title={HOME_COPY.title}
      right={
        <View style={s.headerRight}>
          <RankingTrophy />
          <NoticeBell />
        </View>
      }
      onRefresh={() =>
        Promise.all([rereadHome(client), rereadHomeGroups(client), rereadDiscovery(client)])
      }
    >
      <HomeLevelCard />
      <FriendsGamesRow onAnswered={() => rereadNotices(client)} />
      <PaymentsToConfirm />
      <HomeFriendRows />
      <HomeRail
        empty={
          inNoGroup ? { ...HOME_COPY.empty, act: GROUPS_COPY.hottest.groupless } : HOME_COPY.empty
        }
      />
      <HottestGroupsRow />
      <SameLevelRow />
      <NewInRaketaRow />
      <SameVibeRow />
    </ShellScreen>
  );
}

/** *FRIEND REQUESTS · n* and *ASKED FOR A LEVEL · n*, and the record a face on either opens. */
function HomeFriendRows() {
  const client = useQueryClient();
  const [reading, setReading] = useState<string>();
  return (
    <>
      <FriendRequestsRow
        scoreTag={(request) => (
          <PlayerScoreTag
            score={request.playerScore}
            {...(request.reliabilityBand === undefined ? {} : { band: request.reliabilityBand })}
          />
        )}
        onFace={setReading}
        onAnswered={() => rereadNotices(client)}
      />
      <LevelAsksRow
        onFace={setReading}
        onAnswered={() => rereadNotices(client)}
        unstarted={OPEN_NOTICE_WORDS.unstarted}
      />
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading }}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  // The trophy, then the bell in the corner: the bell's own 44pt target is its spacing on the right.
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
});
