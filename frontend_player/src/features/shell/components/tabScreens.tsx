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

import { FriendRequestsRow } from '@/features/friends/types';
import { HomeLevelCard } from '@/features/groups/types';
import { NoticeBell, rereadNotices } from '@/features/notifications/types';
import { PlayerRecordSheet, PlayerScoreTag } from '@/features/player_record/types';
import { HomeRail, PaymentsToConfirm, rereadHome } from '@/features/proposals/types';

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
 * **FRIEND REQUESTS sits above Your games** (`friends`' row, [#753](https://github.com/Raketa02/Raketa/issues/753);
 * the friends screens §6; Q13), drawn only while a request waits. The shell hands it the two things
 * that are `player_record`'s — the reliability chip, and the record a face opens — so `friends` does
 * not import the feature that draws its record button; and the bell's re-read, since answering a
 * request takes its row off the bell.
 */
export function HomeScreen() {
  const client = useQueryClient();
  return (
    <ShellScreen
      title={HOME_COPY.title}
      right={<NoticeBell />}
      onRefresh={() => rereadHome(client)}
    >
      <HomeLevelCard />
      <PaymentsToConfirm />
      <HomeFriendRequests />
      <HomeRail empty={HOME_COPY.empty} />
    </ShellScreen>
  );
}

/** *FRIEND REQUESTS · n*, and the record a card's face opens. */
function HomeFriendRequests() {
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
