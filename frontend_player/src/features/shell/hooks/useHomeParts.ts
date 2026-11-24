/**
 * **Home's two parts, top-down, and whether each has been read** ([#871](https://github.com/Raketa02/Raketa/issues/871);
 * PRD #867; the loading shimmer log §6, Q11, Q12) — what `HomeScreen` hands `shared/ui`'s
 * `useRevealParts`, which shows them together, or top-down from the ceiling.
 *
 * | Part | Draws | Waits for |
 * | --- | --- | --- |
 * | **1 — your things** | the header's numbers, the level card, *YOUR GAMES* | Home's own read; the ratings, and your groups where the level card needs them; in-no-group; the bell's notices |
 * | **2 — FOR YOU**, all its lines together | the heading and whichever lines have content | Groups heating up; the three people lines; Top 10, behind its opening sport |
 *
 * Each feature says whether its own reads have finished — landed, refused, held for a connection, or
 * failed once and retrying — off the cache, so Home draws again only as one of them turns. **Photo
 * bytes are never waited for**: no part asks after a face.
 */

import { useDiscoveryLinesFinished } from '@/features/discovery/types';
import {
  useHottestGroupsFinished,
  useInNoGroupFinished,
  useLevelCardFinished,
} from '@/features/groups/types';
import { useNoticesFinished } from '@/features/notifications/types';
import { useHomeReadFinished } from '@/features/proposals/types';
import { useTopTenFinished } from '@/features/rankings/types';

/** Part 1's place in the list — how many parts must be shown for it to be. */
export const YOUR_THINGS = 1;
/** Part 2's. */
export const FOR_YOU = 2;

export function useHomeParts(): readonly boolean[] {
  const home = useHomeReadFinished();
  const levelCard = useLevelCardFinished();
  const inNoGroup = useInNoGroupFinished();
  const notices = useNoticesFinished();
  const hottestGroups = useHottestGroupsFinished();
  const peopleLines = useDiscoveryLinesFinished();
  const topTen = useTopTenFinished();
  return [home && levelCard && inNoGroup && notices, hottestGroups && peopleLines && topTen];
}
