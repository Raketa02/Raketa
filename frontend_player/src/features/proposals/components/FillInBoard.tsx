/**
 * **A group's Fill in tab** — *Seats to fill*, the rescues the reader is offered, then *You're In*,
 * their own yeses on games still filling ([#557](https://github.com/Raketa02/Raketa/issues/557);
 * the screens A3; mocks 11–13; the mechanics §10).
 *
 * ```
 * SEATS TO FILL · 1
 * ┏ Padel · Saturday 16:00 ━━━━━━━━━━━━━━━━━━━━━━┓   coral
 * ┃ Ogrody 33 · fills by Fri 16:00               ┃
 * ┃ [KT] [AK] [KW] [?]               [ Pay 27 zł ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * YOU'RE IN · 1
 * ┏ Padel · Saturday 15:00 ━━━━━━━━━━━━━━━━━━━━━━┓   mint
 * ┃ Bonarka Arena · book by Sat 13:00            ┃
 * ┃ [TK] [  ] [  ] [  ]              [ Withdraw ] ┃
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **Two reads.** *Seats to fill* is `GET /pools/{id}/fill-in` for the page's sport (#545): only
 * rescues — booked games that lost a player, which the reader fits and is free for — soonest first,
 * each leaving at its deadline (`standingSeats`, on the read's clock); the tab's badge is its count.
 * *You're In* is the reader's live yeses in this group and sport (`yesesIn`) — picks, challenges and
 * posts, never a rescue, which goes straight to Home — each row reading its own game's details for
 * the squares. **Sections only when they have rows** (A3); with neither, the tab is the group's
 * starting card the page hands in (`empty`), as the Games tab's is.
 *
 * A row's upper block opens its game: a rescue's details from outside (A4.3), a yes's game still
 * filling (A4.2). A held poster opens that player's record, as a sibling of the board so the board
 * is hidden from a listener while the sheet is up. The floating *+ Post a game* is the page's.
 *
 * **Each read is its own section's**: while either is on its way and nothing is drawn yet, the muted
 * spinner — the starting card only once both have said there is nothing; a read held offline says it
 * resumes, and one refused says why with the retry, in its section's place, without hiding the
 * other's rows.
 */

import { router } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { PlayerRecordSheet } from '@/features/player_record/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { behindOverlay, Note, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckPerson } from '../domain/deck';
import { standingSeats, yesesIn } from '../domain/fillIn';
import { useFillIn } from '../hooks/useFillIn';
import { useReadClock } from '../hooks/useHome';
import { useLiveYeses } from '../hooks/useLiveYeses';

import { FILL_IN_COPY } from './fillInCopy';
import { seatsToFillHeader, youreInHeader } from './fillInPresentation';
import { gameRoute, rescueRoute } from './proposalRoutes';
import { ReadFailed } from './ReadFailed';
import { SeatToFillRow } from './SeatToFillRow';
import { YoureInRow } from './YoureInRow';

export interface FillInBoardProps {
  readonly groupId: string;
  readonly sport: Sport;
  /** What the tab draws with no rows in either section — the group's starting card. */
  readonly empty: ReactNode;
}

export function FillInBoard({ groupId, sport, empty }: FillInBoardProps) {
  const read = useFillIn(groupId, sport);
  const live = useLiveYeses();
  const [reading, setReading] = useState<DeckPerson | undefined>(undefined);

  const board = read.data;
  // The read's clock, running while a row is offered, so a row leaves at its deadline by itself.
  const now = useReadClock(board?.readAt, read.dataUpdatedAt, (board?.seatsToFill.length ?? 0) > 0);

  const seats = board === undefined ? [] : standingSeats(board.seatsToFill, now);
  const yeses = live.data === undefined ? [] : yesesIn(live.data.yeses, groupId, sport);
  // A read with nothing to show yet is held offline or failed, or is still on its way.
  const seatsHeld = board === undefined && (read.fetchStatus === 'paused' || read.error !== null);
  const yesesHeld =
    live.data === undefined && (live.fetchStatus === 'paused' || live.error !== null);
  const pending = (board === undefined && !seatsHeld) || (live.data === undefined && !yesesHeld);

  if (seats.length === 0 && yeses.length === 0 && !seatsHeld && !yesesHeld) {
    // The starting card only once both reads have said there is nothing — never as a first frame.
    return pending ? (
      <ActivityIndicator accessibilityLabel={FILL_IN_COPY.reading} color={theme.color.muted} />
    ) : (
      <>{empty}</>
    );
  }

  return (
    <>
      <View style={s.board} {...behindOverlay(reading !== undefined)}>
        {seats.length === 0 ? null : (
          <View style={s.section}>
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
        )}
        {seatsHeld ? <Held read={read} /> : null}
        {yeses.length === 0 ? null : (
          <View style={s.section}>
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
        )}
        {yesesHeld ? <Held read={live} /> : null}
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

/**
 * **A read the tab could not draw** — held while offline, which resumes, or refused, with why and the
 * retry. Each section's own, so one read failing never hides the other's rows.
 */
function Held({
  read,
}: {
  readonly read: {
    readonly fetchStatus: string;
    readonly error: AppError | null;
    readonly refetch: () => unknown;
  };
}) {
  if (read.error === null || read.fetchStatus === 'paused') {
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  }
  return <ReadFailed error={read.error} onRetry={() => void read.refetch()} />;
}

const s = StyleSheet.create({
  // Room under the last row for the floating *+ Post a game*, which sits over the page's corner.
  board: { gap: theme.space.lg, paddingBottom: theme.size.btnLg + theme.space.lg },
  section: { gap: theme.space.sm },
  head: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
});
