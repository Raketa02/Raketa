/**
 * **Top 10** — the last of FOR YOU's five lines ([#820](https://github.com/Raketa02/Raketa/issues/820),
 * [#821](https://github.com/Raketa02/Raketa/issues/821); ADR-0205 §5; was the TOP 10 row,
 * [#805](https://github.com/Raketa02/Raketa/issues/805), ADR-0204; the Home rows screens §7, the
 * mechanics §10; the words §31.1, §31.11; home rows 25–27, home refactor 12, 13).
 *
 * Places 1 to 10 of General in one sport. Open, the line holds the cards (`TopTenCard`) on a
 * `numbered` rail — the row ending at the last ranked player, one or two included — or *Nobody ranked
 * in squash yet* for a sport with nobody in it, and **its footer** holds the sport switcher at the
 * left — *Padel ›*, the deck's pill opening rightwards (`RowSportPill`) — and *Open the rankings ›* at
 * the right, where the row's heading held the pill and *Rankings ›* (#821). **Hidden** while
 * nobody is ranked in any sport, and while its read is out or failed: a line that fails is left out,
 * and the rest of Home stands (the screens §1). The closed line is its title alone.
 *
 * **It opens on the trophy's sport**, the deck's last, or padel, which the server falls through from;
 * **a pick asks for that sport exactly** and re-reads this line alone (`useTopTen`). The pick is held
 * by the line, not by what it unfolds, so it outlives a close while Home is up. The pill offers all
 * four, as the Rankings page's does.
 *
 * **A card opens the record**, on the line's sport and **from the ranking**: a request asked there is
 * the ranking's (the mechanics §12). The reader's own card opens their own. **Across a block the
 * record reads *This record isn't available*** — the sheet's own drawing of the server's one refusal;
 * nothing here knows about blocks, and everybody is on the line at their true place (ADR-0204 §2).
 *
 * **Open the rankings › opens the Rankings page on the line's sport, in General** (the mechanics
 * §10.4, a call): the list Top 10 is the top of. The page then remembers General, as any look at it does.
 */

import { router } from 'expo-router';
import { memo, useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import {
  FoldingLineFooter,
  HomeRowRail,
  RowSportPill,
  theme,
  type FoldingLineParts,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { TopTenPlayer } from '../domain/topTen';
import { useRankingView } from '../hooks/useRankingView';
import { useTopTen, type TopTenRead } from '../hooks/useTopTen';

import {
  TOP_TEN_COPY,
  TOP_TEN_PILL_WORDS,
  nobodyRankedLine,
  topTenRankingsLabel,
} from './rankingsCopy';
import { rankingsRoute } from './rankingsRoutes';
import { TopTenCard } from './TopTenCard';
import { numeralWidth } from './TopTenNumeral';

/**
 * **The Top 10 line, as the shell draws it** — `undefined` while it is hidden. Read whether it is
 * open or not, so the read runs when Home opens and the pick is held while Home is up.
 */
export function useTopTenLine(): FoldingLineParts | undefined {
  const top = useTopTen();
  const { face } = top;
  if (face.kind === 'hidden') return undefined;
  return {
    title: TOP_TEN_COPY.line,
    testID: 'top-ten',
    content: (
      <TopTen sport={face.sport} players={face.kind === 'cards' ? face.players : undefined} />
    ),
    footer: <TopTenFooter top={top} sport={top.sport ?? face.sport} />,
  };
}

/** **Whose record is up**, and the sport of the line it was opened from. */
interface RecordOpen {
  readonly subject: RecordSubject;
  readonly sport: Sport;
}

/**
 * The line's cards, or *Nobody ranked in squash yet* — memoised, with the read's own players handed in
 * rather than a face made afresh each render: the shell draws every line from one component, so a
 * re-read of another line must not draw these cards again.
 */
const TopTen = memo(function TopTen({
  sport,
  players,
}: {
  readonly sport: Sport;
  /** Nobody ranked in the sport when none. */
  readonly players: readonly TopTenPlayer[] | undefined;
}) {
  const [reading, setReading] = useState<RecordOpen>();
  const open = (player: TopTenPlayer) =>
    setReading({
      subject: { kind: player.isYou ? 'me' : 'player', playerId: player.playerId },
      sport,
    });

  return (
    <>
      {players === undefined ? (
        <Text style={s.nobody}>{nobodyRankedLine(sport)}</Text>
      ) : (
        <HomeRowRail cards={players} geometry="numbered" itemWidth={TOP_TEN_ITEM}>
          {(player, width) => (
            <TopTenCard
              key={player.playerId}
              player={player}
              width={width}
              onOpen={() => open(player)}
            />
          )}
        </HomeRowRail>
      )}
      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={reading.subject}
          sport={reading.sport}
          // A request asked here is the ranking's, in the line's sport (the mechanics §12).
          rankingSport={reading.sport}
        />
      )}
    </>
  );
});

/** The switcher at the open line's foot, on the left, and *Open the rankings ›* on the right. */
function TopTenFooter({ top, sport }: { readonly top: TopTenRead; readonly sport: Sport }) {
  const { choose } = useRankingView();
  return (
    <RowSportPill
      sports={top.sports}
      sport={top.sport}
      onPick={top.pick}
      words={TOP_TEN_PILL_WORDS}
    >
      {(pill, over) => (
        <FoldingLineFooter
          {...(pill === undefined ? {} : { control: pill })}
          {...(over === undefined ? {} : { over })}
          link={{
            words: TOP_TEN_COPY.rankings,
            label: topTenRankingsLabel(sport),
            onPress: () => {
              choose('GENERAL');
              router.push(rankingsRoute(sport));
            },
          }}
        />
      )}
    </RowSportPill>
  );
}

/**
 * **An item's width on the rail** — the numeral beside the card, less the card's overlap of it. Places
 * 1 to 9 stand alike, so the rail snaps on their edges; *10*'s wider figure only lengthens the end.
 */
const TOP_TEN_ITEM = (cardWidth: number) => numeralWidth(1) + cardWidth - theme.size.topTen.overlap;

const s = StyleSheet.create({
  // The Rankings page's own line for an empty sport (§30.7), in the rail's place.
  nobody: { ...theme.type.rlLabel, color: theme.color.muted },
});
