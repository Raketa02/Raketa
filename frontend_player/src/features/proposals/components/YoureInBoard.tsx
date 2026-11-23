/**
 * **A group's You’re in board** — the reader's own live yeses in this group and sport, on games
 * still filling ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3, A3.2;
 * mock 13; the mechanics §10.2).
 *
 * ```
 * YOU'RE IN · 1
 * ┏ Padel · Saturday 15:00 ━━━━━━━━━━━━━━━━━━━━━━┓   mint
 * ┃ Bonarka Arena · book by Sat 13:00            ┃
 * ┃ [TK] [  ] [  ] [  ]              [ Withdraw ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **Its read is its own**: the live yeses (`yesesIn`) — picks, challenges and posts, never a rescue,
 * which goes straight to Home — each row reading its own game's details for the squares. A read held
 * offline says it resumes, and one refused says why with the retry, in the board's place.
 *
 * A row's upper block opens its game still filling (A4.2). A held poster opens that player's record,
 * as a sibling of the rows so they are hidden from a listener while the sheet is up.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { behindOverlay, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckPerson } from '../domain/deck';
import { yesesIn } from '../domain/fillIn';
import { useLiveYeses } from '../hooks/useLiveYeses';

import { youreInHeader } from './fillInPresentation';
import { HeldRead, isHeld } from './HeldRead';
import { gameRoute } from './proposalRoutes';
import { YoureInRow } from './YoureInRow';

export interface YoureInBoardProps {
  readonly groupId: string;
  readonly sport: Sport;
}

export function YoureInBoard({ groupId, sport }: YoureInBoardProps) {
  const live = useLiveYeses();
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  if (live.data === undefined) return isHeld(live) ? <HeldRead read={live} /> : null;
  const yeses = yesesIn(live.data.yeses, groupId, sport);
  if (yeses.length === 0) return null;
  // The read's clock: the instant the list was received, as You › Payments reads its rows.
  const now = live.dataUpdatedAt;

  return (
    <>
      <View style={s.section} {...behindOverlay(reading !== undefined)}>
        <Text accessibilityRole="header" style={s.head}>
          {youreInHeader(yeses.length)}
        </Text>
        {yeses.map((yes) => (
          <YoureInRow
            key={yes.proposalId}
            yes={yes}
            now={now}
            onOpen={() => router.push(gameRoute(groupId, yes.proposalId, yes.sport, yes.kind))}
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
