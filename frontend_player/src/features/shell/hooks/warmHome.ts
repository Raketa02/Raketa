/**
 * **Home's reads, set out while the splash plays** ([#874](https://github.com/Raketa02/Raketa/issues/874);
 * PRD #867; [ADR-0209](../../../../../docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md)
 * §2, amended 2026-11-24; the loading shimmer log §7, Q18) — so that on a normal connection a cold
 * open fades onto a Home that is already whole, with no shimmer.
 *
 * **A step of the launch, started and never awaited** — the root layout starts it right after session
 * restore, as it starts the install referrer's read, and the splash waits on nothing it does: the fade
 * rule (§3) is unchanged, and *ready* still never means the data has arrived. **It is the shell's**
 * because Home is: each feature that feeds Home offers its Home read's prefetch, under the very
 * definitions its hooks observe — keys, functions and options, Top 10's chain included — and this
 * composes them, so Home finds every read fresh under the app's thirty-second `staleTime` when it
 * mounts and asks for nothing twice.
 *
 * | Read | Whose | For |
 * | --- | --- | --- |
 * | `GET /home` | `proposals` | *Your games*, the envelope, the trophy's place, the bar's badge |
 * | `GET /ratings` | `onboarding` | the level card, and Top 10's opening sport |
 * | `GET /groups`, `GET /hottest-groups` | `groups` | the groupless line and the level card; Groups heating up |
 * | `GET /same-level`, `/new-in-rakieta`, `/same-vibe` | `discovery` | FOR YOU's three people lines |
 * | `GET /players/me/notices` | `notifications` | the bell's number |
 * | `GET /top-10` | `rankings` | Top 10 — once the trophy's sport, else the deck's, is known |
 *
 * **Only for an account the entry gate will send to the tabs** — never for one headed for the naming,
 * the profile steps, a club's area or *Start playing*, by the gate's own rule over the account
 * (`onboarding`'s `entryDestinationAtLaunch`) — and **never on a phone that already knows it is
 * offline**, by the launch check's rule (`auth`'s `phoneKnowsItIsOffline`, ADR-0209 §4). **Launch
 * only**: after a sign-in Home mounts the moment the session opens, and a warm-up would gain nothing.
 *
 * **Why it is safe where mounting under the motion was not**: reads create no views. Their answers are
 * parsed on the JavaScript thread while the ball moves on the UI thread, and a cache write no screen
 * watches commits nothing. The A32's cold-start trace is its acceptance (the phone walk, #877).
 *
 * The photographs behind the faces, the booking rooms the chat button asks after and the phone's own
 * lists of games opened and removed are not warmed: none holds up a part of Home's reveal
 * (`useHomeParts`), and the phone's lists are read in milliseconds.
 */

import type { QueryClient } from '@tanstack/react-query';

import { phoneKnowsItIsOffline } from '@/features/auth/types';
import { prefetchPeopleLines } from '@/features/discovery/types';
import { prefetchHomeGroups } from '@/features/groups/types';
import { prefetchNotices } from '@/features/notifications/types';
import { entryDestinationAtLaunch, prefetchSkillRatings } from '@/features/onboarding/types';
import { prefetchHome } from '@/features/proposals/types';
import { prefetchTopTen } from '@/features/rankings/types';
import type { Reachability } from '@/shared/lib/platform';

/**
 * Resolves once every read it set out has settled — which a launch never waits for. It never
 * rejects: a read that fails is left in the cache for Home to say so, as Home's own would be.
 */
export async function warmHome(
  client: QueryClient,
  readReachability: () => Promise<Reachability>,
): Promise<void> {
  if (await phoneKnowsItIsOffline(readReachability)) return;
  if ((await entryDestinationAtLaunch(client))?.kind !== 'app') return;
  await Promise.all([
    prefetchHome(client),
    prefetchSkillRatings(client),
    prefetchHomeGroups(client),
    prefetchPeopleLines(client),
    prefetchNotices(client),
    prefetchTopTen(client),
  ]);
}
