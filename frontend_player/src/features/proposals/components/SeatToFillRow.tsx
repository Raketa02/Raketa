/**
 * **A *Seats to fill* row** — a booked game that lost a player, offered to the reader
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3.1; mock 12; the mechanics
 * §10.1).
 *
 * ```
 * ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   coral, 1.5pt
 * ┃ Padel · Saturday 16:00                    ┃   the title — and the door to the details
 * ┃ Ogrody 33 · fills by Fri 16:00            ┃   the club, and how long, bold
 * ┃ [KT] [AK] [KW] [?]         [ I'm in · 27 zł ] ┃  the paid posters, the open seats, the join
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ```
 *
 * **The upper block opens the rescue's details** — the booked game seen from outside (A4.3) — and
 * ***I'm in · 27 zł*** takes the seat (`TakeTheSeat`): ten seconds behind *Undo*, the charge, *It's
 * a game!*, and the game in Home; a lost race says *Someone just took it*. The subtitle is the read's:
 * *fills by Fri 16:00* for a seat that opened before the cut-off, *offered until the start* for one
 * that opened after it. **At its deadline the row leaves** (`standingSeats`) — at the cut-off a
 * game still short is called off (§12.3), at the start it is under way — so A3.1's *switches by
 * itself* is a row going, never a row rewording itself: the next read is the server's.
 *
 * **Coral** — a rescue is the group's one emergency, the rescue ribbon's own meaning (§1.2, Part 16).
 */

import { formatZloty } from '@/shared/formatting/ratingFormat';

import type { DeckPerson } from '../domain/deck';
import { yesOnRow, type SeatToFill } from '../domain/fillIn';
import { gameDayOf } from '../domain/when';

import { clubName } from './deckPresentation';
import { rowTitle, seatRowLabel, seatWhen } from './fillInPresentation';
import { FillInRow } from './FillInRow';
import { FillInSquares } from './FillInSquares';
import { TakeTheSeat } from './TakeTheSeat';

export interface SeatToFillRowProps {
  readonly row: SeatToFill;
  readonly groupId: string;
  /** The read's clock. */
  readonly now: number;
  readonly onOpen: () => void;
  readonly onHold: (person: DeckPerson) => void;
}

export function SeatToFillRow({ row, groupId, now, onOpen, onHold }: SeatToFillRowProps) {
  const day = gameDayOf(row.startsAt, now);
  return (
    <FillInRow
      frame="rescue"
      label={seatRowLabel(row, day)}
      title={rowTitle(row, day)}
      club={clubName(row)}
      when={seatWhen(row)}
      onOpen={onOpen}
      testID={`seat-to-fill-${row.bookingId}`}
    >
      <FillInSquares people={row.players} open={row.openSeats} question onHold={onHold} />
      <TakeTheSeat
        seat={yesOnRow(row)}
        dealtIn={{ groupId, sport: row.sport, kind: row.kind }}
        share={formatZloty(row.shareGrosze)}
        heldUntilTheCutOff={row.fillsByTheCutOff}
        size="md"
      />
    </FillInRow>
  );
}
