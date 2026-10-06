/**
 * The screens the shell composes under a tab's own words — **one of them here**, and none of
 * them a placeholder.
 *
 * Named components rather than one taking a `tab` prop: a route file's whole job is to say
 * which screen a path is, and `<HomeScreen />` says it where `<TabScreen tab="home" />` makes
 * the route file hold the answer as data. Play and You are the shell's too, in files of their
 * own because neither is thin.
 */

import { NoticeBell } from '@/features/notifications/types';
import { HomeRail, PaymentsToConfirm } from '@/features/proposals/types';

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
 */
export function HomeScreen() {
  return (
    <ShellScreen title={HOME_COPY.title} right={<NoticeBell />}>
      <PaymentsToConfirm />
      <HomeRail empty={HOME_COPY.empty} />
    </ShellScreen>
  );
}
