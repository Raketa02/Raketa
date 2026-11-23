/**
 * **A group's rescue board** — *Seats to fill*, the rescues the reader is offered
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3, A3.1; mocks 11, 12; the
 * mechanics §10).
 *
 * ```
 * SEATS TO FILL · 1
 * ┏ Padel · Saturday 16:00 ━━━━━━━━━━━━━━━━━━━━━━┓   coral
 * ┃ Ogrody 33 · fills by Fri 16:00               ┃
 * ┃ [KT] [AK] [KW] [?]               [ Pay 27 zł ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **Its read is its own**: `GET /pools/{id}/fill-in` for the page's sport (#545) — only rescues,
 * booked games that lost a player, which the reader fits and is free for — soonest first, each
 * leaving at its deadline (`useSeatsToFill`, on the read's clock). A read held offline says it
 * resumes, and one refused says why with the retry, in the board's place.
 *
 * A row's upper block opens the rescue's details from outside (A4.3). A held poster opens that
 * player's record, as a sibling of the rows so they are hidden from a listener while the sheet is
 * up.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckPerson } from '../domain/deck';
import { useSeatsToFill } from '../hooks/useFillIn';

import { seatsToFillHeader } from './fillInPresentation';
import { HeldRead, isHeld } from './HeldRead';
import { rescueRoute } from './proposalRoutes';
import { SeatToFillRow } from './SeatToFillRow';

export interface FillInBoardProps {
  readonly groupId: string;
  readonly sport: Sport;
}

export function FillInBoard({ groupId, sport }: FillInBoardProps) {
  const { read, now, seats } = useSeatsToFill(groupId, sport);
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  if (seats === undefined) return isHeld(read) ? <HeldRead read={read} /> : null;
  if (seats.length === 0) return null;

  return (
    <>
      <View style={s.section} {...behindOverlay(reading !== undefined)}>
        <Text accessibilityRole="header" style={s.head}>
          {seatsToFillHeader(seats.length)}
        </Text>
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
  section: { gap: theme.space.sm },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
});
