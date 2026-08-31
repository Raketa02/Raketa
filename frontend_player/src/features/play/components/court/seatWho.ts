/**
 * Who is in a seat, in the two registers a court says it in — **and one switch for both.**
 *
 * [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §15: *"One
 * `playerName()`: the handle, whole, and `You` for yourself"*, and ADR-0107's rule that
 * inventing a familiar form is the product addressing somebody by a name they never gave it.
 *
 * Three things on this court name a person and **all three say the same string**: the label
 * drawn under a face, the clear badge's *Remove {name} from {side}*, and the guard toast a
 * refused tap raises. That is why `name` comes back beside the spoken occupant rather than
 * from a second function walking the same three cases — the difference between the registers
 * is the **box**, not the word. The 46pt seat truncates its copy and the two sentences do not,
 * which is the whole of *"a seat label may truncate visually; a sentence may not, and a spoken
 * name never does"*: a statement about components, not about formatters.
 *
 * **The empty seat's word is a question mark**, which `playerName` already owns as its unknown
 * and which is deliberately not a word: the court states an empty seat with a dashed ring and
 * a plus, and a label reading *open* underneath would be the same fact printed twice at 9,5pt.
 */

import { playerName } from '@/shared/formatting/playerName';

import type { SeatOccupant } from '../accessibilityPresentation';

import type { CourtSeatOccupant } from './CourtSeat';

export interface SeatWho {
  /** What `seatLabel` and `clearSeatLabel` compose from — the level with it, where there is one. */
  readonly spoken: SeatOccupant;
  /** The name alone: drawn under the face, quoted in the badge's sentence and in a toast. */
  readonly name: string;
}

export function seatWho(occupant: CourtSeatOccupant): SeatWho {
  switch (occupant.kind) {
    case 'you':
      return { spoken: { kind: 'you' }, name: playerName({ kind: 'you' }) };
    case 'player': {
      const name = playerName({ kind: 'player', nickname: occupant.nickname });
      return { spoken: { kind: 'player', name, level: occupant.level }, name };
    }
    case 'empty':
      return {
        spoken: { kind: 'empty', unfilled: occupant.unfilled },
        name: playerName({ kind: 'unknown' }),
      };
  }
}
