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
  rereadDiscovery,
  useNewInRaketaLine,
  useSameLevelLine,
  useSameVibeLine,
} from '@/features/discovery/types';
import {
  GROUPS_COPY,
  HomeLevelCard,
  rereadHomeGroups,
  useHottestGroupsLine,
  useInNoGroup,
} from '@/features/groups/types';
import { NoticeBell } from '@/features/notifications/types';
import { HomeRail, YourGamesSkeleton, rereadHome } from '@/features/proposals/types';
import { RankingTrophy, rereadTopTen, useTopTenLine } from '@/features/rankings/types';
import {
  FoldingLine,
  FoldingLines,
  Reveal,
  SkeletonGround,
  theme,
  useRevealParts,
  type FoldingLineParts,
} from '@/shared/ui';

import {
  FOR_YOU_LINES,
  forYouShown,
  lineToStartOn,
  type ForYouLine,
  type LinesShown,
} from '../domain/forYou';
import { FOR_YOU, YOUR_THINGS, useHomeParts } from '../hooks/useHomeParts';
import { useOpenLine } from '../hooks/useOpenLine';

import { ForYouSkeleton } from './ForYouSkeleton';

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
 * **A member of a group rated in nothing is asked for a level first** (`groups`' `HomeLevelCard`,
 * [#731](https://github.com/Raketa02/Raketa/issues/731), ADR-0200 §7): *Get your level — your
 * groups can't deal you games until you have one.*, at the top, since until she has one nothing
 * under it can happen. It draws nothing for anybody else.
 *
 * **What waits on the reader is behind the envelope** (ADR-0205 §1): **Needs your answer**, the sheet
 * the header's envelope opens (`NeedsYourAnswer`) — TO CONFIRM and FRIENDS GAME, `proposals`'
 * ([#817](https://github.com/Raketa02/Raketa/issues/817)), then FRIEND REQUESTS and ASKED FOR A
 * LEVEL, `friends`' ([#816](https://github.com/Raketa02/Raketa/issues/816)). They were Home's rows
 * above Your games from #555, #759, #753 and #765, and the ask no longer stands in place of *Get your
 * level*, which is drawn whether or not someone asked. **The bar's Home badge still counts every
 * payment to confirm** (`needing_you`): the tab still pulls the player in when money waits, and the
 * envelope on the tab is where it is answered.
 *
 * **The header reads envelope, bell, trophy** (ADR-0205 §2; home refactor 1): the envelope only while
 * something waits for an answer; `notifications`' bell; and `rankings`' `RankingTrophy`
 * ([#775](https://github.com/Raketa02/Raketa/issues/775)), the reader's General place and the way to
 * Rankings, in the far-right corner. The slot is right-aligned, so without the envelope the bell and
 * the trophy stand where they were.
 *
 * **FOR YOU stands below *Your games*** ([#820](https://github.com/Raketa02/Raketa/issues/820);
 * ADR-0205 §5; home refactor 3–13): the five rows ADR-0204 put there, folded into five quiet lines —
 * **Groups heating up** (`groups`'), **Players at your level**, **New in Raketa** and **Players with
 * your vibe** (`discovery`'s), and **Top 10** (`rankings`') — each feature handing its title, what it
 * unfolds and its footer, and `undefined` while its read is out, empty or failed. **Which line is
 * open is the shell's** (`useOpenLine`): one at a time, closed at the start, kept across tab switches
 * while Home lives, and Groups heating up open by itself for **a reader in no group**, whose *Your
 * games* reads *Join a group to get games — see Groups heating up, just below.* where *Play finds you
 * one.* stood (§31.1). **Every line reads when Home opens**, open or not, so a closed line still
 * knows whether to show; the pull re-reads them all with Home's own. With all five hidden, FOR YOU is
 * hidden too. **Four lines carry a count** ([#822](https://github.com/Raketa02/Raketa/issues/822),
 * ADR-0205 §6) — how many there are to explore, on each line's own read — which the shell hands the
 * line as it hands the title; Top 10 has none.
 *
 * **A friend act anywhere moves a person on the people lines** — an answer in Needs your answer, the
 * record a face opens — because their reads list people (`LISTS_PEOPLE`) and every friend write
 * reaches those; the shell hands them nothing for that. **A pick on Top 10's pill re-reads that line
 * alone**; the pull re-reads it with the rest (`rereadTopTen`).
 *
 * **It shimmers until it is built, then reveals together** ([#871](https://github.com/Raketa02/Raketa/issues/871);
 * PRD #867; the loading shimmer log §6): **two parts, top-down** (`useHomeParts`) — *your things*
 * (the header's numbers, the level card and *Your games*) and FOR YOU whole. While a part's reads are
 * out its skeleton stands in its place — *Your games*' heading and one card (`proposals`'
 * `YourGamesSkeleton`), FOR YOU's heading and four closed lines (`ForYouSkeleton`) — on one ground,
 * so one band crosses both, and **no level card and no envelope**, which are often absent. Once every
 * part has finished, everything comes in on one cross-fade; **from 2.5 s after Home mounts** (the
 * ceiling, `useRevealParts`) it stops waiting for the slowest: the finished parts from the top, never
 * FOR YOU before your things, and each part in turn as it finishes. **The header is drawn for real
 * from the start** — the title, the bell and the trophy — and **its numbers wait for your things**:
 * the envelope, the trophy's place and the bell's badge come with them, or, past the ceiling, as each
 * lands, in a right-aligned slot that pushes nothing down. A skeleton is drawn only if something is
 * unread at the first draw, so a Home whose reads are all cached is simply drawn; and it shows **once
 * per mount** — never on a return to Home, a pull or a background re-read, since a part shown stays
 * shown and Home stays mounted.
 *
 * **Memoised, because it is kept** (`TAB_STACK`): Home stays mounted under every tab, and the route
 * that draws it is drawn again on every move the navigator makes — so without `memo` every press of
 * every tab re-rendered every row, card and poster on Home, nothing having changed, and a device
 * spent most of a second on it. It takes no props; what it reads, it reads for itself — the parts'
 * flags off the cache, so it draws again only as one of them turns.
 */
export const HomeScreen = memo(function HomeScreen() {
  const client = useQueryClient();
  const inNoGroup = useInNoGroup();
  const { shown, pastCeiling } = useRevealParts(useHomeParts());
  const yourThings = shown >= YOUR_THINGS;
  const forYou = shown >= FOR_YOU;
  // The header's numbers come with your things — or, past the ceiling, each as it lands.
  const numbers = yourThings || pastCeiling;
  return (
    <ShellScreen
      title={HOME_COPY.title}
      watchesOnScreen
      startsOverWhen={whenHomeStartsOver}
      right={
        <View style={s.headerRight}>
          <NeedsYourAnswer showsEnvelope={numbers} />
          <NoticeBell showsCount={numbers} />
          <RankingTrophy showsPlace={numbers} />
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
      {/* One ground for both parts, so one band crosses them both. */}
      <SkeletonGround style={s.parts} testID="home-parts">
        <Reveal
          testID="home-your-things"
          sizedBy="skeleton"
          finished={yourThings}
          landed={yourThings}
          skeleton={<YourGamesSkeleton />}
        >
          <View style={s.part}>
            <HomeLevelCard />
            <HomeRail
              empty={
                inNoGroup
                  ? { ...HOME_COPY.empty, act: GROUPS_COPY.hottest.groupless }
                  : HOME_COPY.empty
              }
            />
          </View>
        </Reveal>
        <Reveal
          testID="home-for-you"
          sizedBy="skeleton"
          finished={forYou}
          landed={forYou}
          skeleton={<ForYouSkeleton />}
        >
          <ForYou inNoGroup={inNoGroup} />
        </Reveal>
      </SkeletonGround>
    </ShellScreen>
  );
});

/**
 * **FOR YOU** — the five lines, each its feature's, in ADR-0205 §5's order; the eyebrow over them
 * while any is shown.
 */
function ForYou({ inNoGroup }: { readonly inNoGroup: boolean }) {
  const lines: Readonly<Record<ForYouLine, FoldingLineParts | undefined>> = {
    hottestGroups: useHottestGroupsLine(),
    sameLevel: useSameLevelLine(),
    newInRaketa: useNewInRaketaLine(),
    sameVibe: useSameVibeLine(),
    topTen: useTopTenLine(),
  };
  const shown: LinesShown = {
    hottestGroups: lines.hottestGroups !== undefined,
    sameLevel: lines.sameLevel !== undefined,
    newInRaketa: lines.newInRaketa !== undefined,
    sameVibe: lines.sameVibe !== undefined,
    topTen: lines.topTen !== undefined,
  };
  const { open, folding, pressed, press } = useOpenLine(shown, lineToStartOn({ inNoGroup }));

  if (!forYouShown(shown)) return null;
  return (
    <FoldingLines heading={HOME_COPY.forYou} folding={folding} testID="for-you">
      {FOR_YOU_LINES.map((key) => {
        const line = lines[key];
        return line === undefined ? null : (
          <FoldingLine
            key={key}
            title={line.title}
            count={line.count}
            open={open === key}
            onHeader={() => press(key)}
            footer={line.footer}
            reveals={pressed}
            testID={line.testID}
          >
            {line.content}
          </FoldingLine>
        );
      })}
    </FoldingLines>
  );
}

const s = StyleSheet.create({
  // The envelope and the bell, each in its own 44pt target, then the trophy's pill in the corner.
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  // The page's column, kept through the ground and each part: `sm` between what it stacks.
  parts: { gap: theme.space.sm },
  part: { gap: theme.space.sm },
});
