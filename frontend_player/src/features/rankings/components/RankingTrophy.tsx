/**
 * **The trophy on Home** — a dark pill in the header's far-right corner, right of the bell since
 * [#816](https://github.com/Rakieta02/Rakieta/issues/816) (ADR-0205 §2; home refactor 1), where it
 * stood left of it (rankings 1; the screens §1; the mechanics §8;
 * [#775](https://github.com/Rakieta02/Rakieta/issues/775)): the drawn trophy and the reader's place,
 * *🏆 #7*, mono.
 *
 * **The place is the remembered view's** (#777; the mechanics §8) in the sport of the reader's latest
 * result, read off Home's one read (`proposals`' `useHomeRanking`): General's, or Friends' once the
 * reader last looked at Friends — the view the page itself opens on (`useRankingView`), so the number
 * is always the place on the page it opens.
 *
 * **No number, and still a button**, when there is no place in that view — not enough results, off
 * the list, never played, or in Friends no friend listed — and while Home or the phone is being read:
 * a number appearing is the badge's own move, and the pill is the way to the page whatever it says.
 * **Home holds the number back while it shimmers** (#871; `showsPlace`): the trophy is drawn for real
 * from the start, and its place comes with the rest of your things — or, past the ceiling, as it
 * lands — named only once drawn.
 *
 * **A tap opens Rankings on the trophy's sport and view**, pushed over Home (the shell keeps the Home
 * column lit): the sport in the address, the view the one the page reads off the phone. With no result
 * anywhere the page picks its own sport — the deck's last, or padel.
 *
 * The trophy is drawn — the character is never used (§30's preamble) — on `night`, the dark card's
 * fill, in white; a pill on paper, so it is the chip's shape (Part 16, 2026-11-08).
 */

import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { useHomeRanking } from '@/features/proposals/types';
import { theme } from '@/shared/ui';

import { placeIn } from '../domain/ranking';
import { useRankingView } from '../hooks/useRankingView';

import { rankingsRoute } from './rankingsRoutes';
import { RANKINGS_COPY, trophyLabel, trophyPlace } from './rankingsCopy';

/** The cup's own 24-unit box: a bowl on a stem and a foot, and the two handles stroked. */
const SPACE = 24;
const CUP =
  'M7 3h10v5a5 5 0 0 1-3.5 4.77V16H16a1 1 0 0 1 1 1v3H7v-3a1 1 0 0 1 1-1h2.5v-3.23A5 5 0 0 1 7 8z';
const HANDLES = 'M7 5H4.5v1.5A3 3 0 0 0 7 9.5M17 5h2.5v1.5A3 3 0 0 1 17 9.5';
const HANDLE_WEIGHT = 1.8;

export interface RankingTrophyProps {
  /** Whether its place may be drawn — Home's to say while it shimmers (#871). Drawn unless said. */
  readonly showsPlace?: boolean;
}

export function RankingTrophy({ showsPlace = true }: RankingTrophyProps) {
  const router = useRouter();
  const ranking = useHomeRanking();
  const { view } = useRankingView();
  // Home's read and the phone's both in, or no place to show — and no words for one.
  const known =
    !showsPlace || ranking == null || view === undefined ? undefined : { ranking, view };
  const place = known === undefined ? undefined : placeIn(known.view, known.ranking);
  const figure = trophyPlace(place);

  return (
    <Pressable
      testID="ranking-trophy"
      accessibilityRole="button"
      accessibilityLabel={
        known === undefined
          ? RANKINGS_COPY.trophy
          : trophyLabel(known.ranking.sport, place, known.view)
      }
      accessibilityHint={RANKINGS_COPY.trophyHint}
      onPress={() => router.push(rankingsRoute(ranking?.sport))}
      hitSlop={theme.hit.trophy}
      style={({ pressed }) => [s.pill, pressed ? s.pressed : undefined]}
    >
      <Svg
        width={theme.size.rankings.trophy}
        height={theme.size.rankings.trophy}
        viewBox={`0 0 ${SPACE} ${SPACE}`}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Path d={CUP} fill={theme.color.surface} />
        <Path
          d={HANDLES}
          fill="none"
          stroke={theme.color.surface}
          strokeWidth={HANDLE_WEIGHT}
          strokeLinecap="round"
        />
      </Svg>
      {figure === undefined ? null : <Text style={s.place}>{figure}</Text>}
    </Pressable>
  );
}

const s = StyleSheet.create({
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xs,
    height: theme.size.rankings.trophyPill,
    // With no place the pill is the trophy alone: 44 wide, so the target is 44 x 44 with `hit.trophy`.
    minWidth: theme.size.minTouch,
    justifyContent: 'center',
    paddingHorizontal: theme.space.md,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.night,
  },
  pressed: { opacity: 0.7 },
  place: { ...theme.num.s, ...theme.tabular, color: theme.color.surface },
});
