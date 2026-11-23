/**
 * **A group's Fill in tab** — the rescues the reader is offered, and nothing else
 * ([#557](https://github.com/Raketa02/Raketa/issues/557), split by
 * [#847](https://github.com/Raketa02/Raketa/issues/847); the screens A3, A3.1; split mock 1; mock 12;
 * the mechanics §10).
 *
 * ```
 * ┏ Padel · Saturday 16:00 ━━━━━━━━━━━━━━━━━━━━━━┓   coral
 * ┃ Ogrody 33 · fills by Fri 16:00               ┃
 * ┃ [KT] [AK] [KW] [?]               [ Pay 27 zł ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **Its read is its own**: `GET /pools/{id}/fill-in` for the page's sport (#545) — only rescues,
 * booked games that lost a player, which the reader fits and is free for — soonest first, each
 * leaving at its deadline (`useSeatsToFill`, on the read's clock). While nothing is drawn yet, the
 * muted spinner; a read held offline says it resumes, and one refused says why with the retry. None
 * of it touches You’re in, the tab beside it, which reads the reader's own live yeses.
 *
 * **No heading** — the tab's name does that job — **and no *+ Post a game***, which floats over You’re
 * in, where the game it makes appears (split override 1). **Empty, it is one line, always** — *No
 * seats to fill right now* — and never the group's starting card, which tells you to post from a tab
 * that no longer has the button (split Q3b).
 *
 * A row's upper block opens the rescue's details from outside (A4.3). A held poster opens that
 * player's record, as a sibling of the rows so they are hidden from a listener while the sheet is
 * up.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckPerson } from '../domain/deck';
import { useSeatsToFill } from '../hooks/useFillIn';

import { FILL_IN_COPY } from './fillInCopy';
import { HeldRead, isHeld } from './HeldRead';
import { rescueRoute } from './proposalRoutes';
import { SeatToFillRow } from './SeatToFillRow';

const COPY = FILL_IN_COPY;

export interface FillInBoardProps {
  readonly groupId: string;
  readonly sport: Sport;
}

export function FillInBoard({ groupId, sport }: FillInBoardProps) {
  const { read, now, seats } = useSeatsToFill(groupId, sport);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  if (seats === undefined) {
    return isHeld(read) ? (
      <HeldRead read={read} />
    ) : (
      <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
    );
  }
  if (seats.length === 0) return <Text style={s.empty}>{COPY.noSeats}</Text>;

  return (
    <>
      <View style={s.rows} {...behindOverlay(reading !== undefined)}>
        {seats.map((row) => (
          <SeatToFillRow
            key={row.bookingId}
            row={row}
            groupId={groupId}
            now={now}
            onOpen={() => router.push(rescueRoute(groupId, row.bookingId))}
            onHold={setReading}
          />
        ))}
      </View>

      {reading === undefined ? null : (
        <PlayerRecordSheet
          visible
          onClose={() => setReading(undefined)}
          subject={{ kind: 'player', playerId: reading.playerId }}
          sport={sport}
          groupId={groupId}
        />
      )}
    </>
  );
}

const s = StyleSheet.create({
  rows: { gap: theme.space.sm },
  // 10.1's empty state: one line of `tiny` in `muted`.
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
