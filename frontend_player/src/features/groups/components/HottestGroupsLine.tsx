/**
 * **Groups heating up** — the first of FOR YOU's five lines, just below *Your games*
 * ([#820](https://github.com/Rakieta02/Rakieta/issues/820); ADR-0205 §5; was HOTTEST GROUPS,
 * [#800](https://github.com/Rakieta02/Rakieta/issues/800), ADR-0204 §3; the Home rows screens §3; the
 * mechanics §5; home rows 1, 21; home refactor 5).
 *
 * Open, up to six cards on the row frame's rail (`HomeRowRail`), **peeking** and settling on their
 * edges, in the read's order — HOTTEST, then GROWING, then untagged — and ***All groups ›*** at the
 * foot, to the Groups heating up page ([#823](https://github.com/Rakieta02/Rakieta/issues/823); ADR-0205
 * §7; home refactor 5), pushed over Home. **Hidden** while the read holds nothing, is in flight, or
 * failed (the screens §1: a line that fails is left out, and the rest of Home stands).
 *
 * **Its count is how many groups there are to look through** ([#822](https://github.com/Rakieta02/Rakieta/issues/822);
 * ADR-0205 §6): every group with 3 or more players, the reader's own included — the read's `total`,
 * drawn *99+* past 99 — never how many cards the rail holds. It moves with the read: a return after
 * thirty seconds, foregrounding, the pull, and the re-read every join, ask and withdraw asks for.
 *
 * **A card's taps are the page's too** (`useHottestTaps`): the card opens the group sheet, and the
 * chip joins, asks, opens the withdraw sheet or the group's page — each write drawn at once on the line
 * and the page alike.
 */

import { router } from 'expo-router';
import { memo } from 'react';

import { FoldingLineFooter, HomeRowRail, type FoldingLineParts } from '@/shared/ui';

import type { HottestGroup } from '../domain/group';
import { useHottestGroups } from '../hooks/useHottestGroups';

import { HOTTEST_GROUPS_ROUTE } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { HottestGroupCard } from './HottestGroupCard';
import { useHottestTaps } from './HottestGroupTaps';

const HOT = GROUPS_COPY.hottest;

/**
 * **The Groups heating up line, as the shell draws it** — `undefined` while it is hidden. Read whether
 * it is open or not, so the read runs when Home opens.
 */
export function useHottestGroupsLine(): FoldingLineParts | undefined {
  const row = useHottestGroups().data;
  if (row === undefined || row.groups.length === 0) return undefined;
  return {
    title: HOT.line,
    count: row.total,
    testID: 'hottest-groups',
    content: <HottestGroups groups={row.groups} />,
    footer: (
      <FoldingLineFooter
        link={{
          words: HOT.allGroups,
          label: HOT.allGroupsLabel,
          onPress: () => router.push(HOTTEST_GROUPS_ROUTE),
        }}
      />
    ),
  };
}

/** Memoised: the shell draws every line from one component, so a re-read of another line must not
 * draw this one's cards again. */
const HottestGroups = memo(function HottestGroups({
  groups,
}: {
  readonly groups: readonly HottestGroup[];
}) {
  const taps = useHottestTaps(groups);

  return (
    <>
      <HomeRowRail cards={groups}>
        {(group, width) => (
          <HottestGroupCard
            key={group.id}
            group={group}
            width={width}
            layout="row"
            onOpen={() => taps.openSheet(group.id)}
            onChip={(action) => taps.chip(group, action)}
          />
        )}
      </HomeRowRail>
      {taps.sheet}
    </>
  );
});
