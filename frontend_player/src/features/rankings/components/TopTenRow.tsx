/**
 * **TOP 10** — the last of Home's five rows ([#805](https://github.com/Raketa02/Raketa/issues/805);
 * ADR-0204; the Home rows screens §7, the mechanics §10; the words §31.1, §31.11; home rows 2, 25–27).
 *
 * Places 1 to 10 of General in one sport, on Home's row frame (`HomeRow`, a `numbered` `HomeRowRail`):
 * *TOP 10*, the deck's sliding sport pill (`RowSportPill`) and *Rankings ›* on the heading's line, and
 * under it the cards (`TopTenCard`) — the row ending at the last ranked player, one or two included —
 * or *Nobody ranked in squash yet* for a sport with nobody in it. **Hidden with its heading** while
 * nobody is ranked in any sport, and while its read is out or failed: a row that fails is left out,
 * and the rest of Home stands (the screens §1).
 *
 * **It opens on the trophy's sport**, the deck's last, or padel, which the server falls through from;
 * **a pick asks for that sport exactly** and re-reads this row alone (`useTopTen`). The pill offers all
 * four, as the Rankings page's does.
 *
 * **A card opens the record**, on the row's sport and **from the ranking**: a request asked there reads
 * *Found you in the padel ranking* on the other person's Home (the mechanics §12). The reader's own
 * card opens their own. **Across a block the record reads *This record isn't available*** — the
 * sheet's own drawing of the server's one refusal; nothing here knows about blocks, and everybody is
 * on the row at their true place (ADR-0204 §2).
 *
 * **Rankings › opens the Rankings page on the row's sport, in General** (the mechanics §10.4, a call):
 * the list Top 10 is the top of. The page then remembers General, as any look at it does.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text } from 'react-native';

import { PlayerRecordSheet, type RecordSubject } from '@/features/player_record/types';
import { HomeRow, HomeRowRail, RowSportPill, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { TopTenPlayer } from '../domain/topTen';
import { useRankingView } from '../hooks/useRankingView';
import { useTopTen } from '../hooks/useTopTen';

import {
  TOP_TEN_COPY,
  TOP_TEN_PILL_WORDS,
  nobodyRankedLine,
  topTenRankingsLabel,
} from './rankingsCopy';
import { rankingsRoute } from './rankingsRoutes';
import { TopTenCard } from './TopTenCard';

/** **Whose record is up**, and the sport of the row it was opened from. */
interface RecordOpen {
  readonly subject: RecordSubject;
  readonly sport: Sport;
}

export function TopTenRow() {
  const top = useTopTen();
  const { choose } = useRankingView();
  const [reading, setReading] = useState<RecordOpen>();
  const { face } = top;
  if (face.kind === 'hidden') return null;

  // The pill's: the sport picked, while its read is out, else the one the row shows.
  const sport = top.sport ?? face.sport;
  const open = (player: TopTenPlayer) =>
    setReading({
      subject: { kind: player.isYou ? 'me' : 'player', playerId: player.playerId },
      sport: face.sport,
    });

  return (
    <RowSportPill
      sports={top.sports}
      sport={top.sport}
      onPick={top.pick}
      words={TOP_TEN_PILL_WORDS}
    >
      {(pill, over) => (
        <HomeRow
          heading={TOP_TEN_COPY.heading}
          control={pill}
          over={over}
          link={{
            words: TOP_TEN_COPY.rankings,
            label: topTenRankingsLabel(sport),
            onPress: () => {
              choose('GENERAL');
              router.push(rankingsRoute(sport));
            },
          }}
          testID="top-ten"
        >
          {face.kind === 'nobody' ? (
            <Text style={s.nobody}>{nobodyRankedLine(face.sport)}</Text>
          ) : (
            <HomeRowRail cards={face.players} geometry="numbered">
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
              // A request asked here is the ranking's, in the row's sport (the mechanics §12).
              rankingSport={reading.sport}
            />
          )}
        </HomeRow>
      )}
    </RowSportPill>
  );
}

const s = StyleSheet.create({
  // The Rankings page's own line for an empty sport (§30.7), in the rail's place under the heading.
  nobody: { ...theme.type.rlLabel, color: theme.color.muted },
});
