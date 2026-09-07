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
 *
 * **A withheld seat answers the same character and is not the same seat**, which is why
 * `named` travels beside the word: it holds a player the record can no longer describe, so it
 * has a face drawn from an id, a sentence of its own, and no name to put in one.
 */

import { playerName } from '@/shared/formatting/playerName';

import type { SeatOccupant } from '../accessibilityPresentation';

import type { CourtSeatOccupant } from './CourtSeat';

export interface SeatWho {
  /** What `seatLabel` and `clearSeatLabel` compose from — the level with it, where there is one. */
  readonly spoken: SeatOccupant;
  /** The name alone: drawn under the face, quoted in the badge's sentence and in a toast. */
  readonly name: string;
  /**
   * The Skill level drawn **under** the name, where the record still holds one.
   *
   * It travels beside the word rather than being read off the occupant a second time, for the
   * reason `name` does: a withheld row carries no card, so the handle and the figure are
   * absent together and one switch decides both.
   */
  readonly level?: number;
  /**
   * Whether that name is **somebody's** rather than the unknown's question mark.
   *
   * Two seats answer `?` and they are not the same seat: an empty one, which names nobody
   * because nobody is in it, and a **withheld** one, which holds a player whose row the record
   * no longer carries. Both draw the same character under the face and neither may be quoted
   * into a sentence — *Remove ? from their side* is a sentence about a punctuation mark — so
   * the two registers separate here rather than at each of the three call sites.
   */
  readonly named: boolean;
}

export function seatWho(occupant: CourtSeatOccupant): SeatWho {
  switch (occupant.kind) {
    case 'you':
      return { spoken: { kind: 'you' }, name: playerName({ kind: 'you' }), named: true };
    case 'player': {
      // The two facts a seat says about a person travel together and go together: a withheld
      // row carries no card, so there is neither a handle to draw nor a level to speak.
      if (occupant.nickname === undefined || occupant.level === undefined) {
        return {
          spoken: { kind: 'withheld' },
          name: playerName({ kind: 'unknown' }),
          named: false,
        };
      }
      const name = playerName({ kind: 'player', nickname: occupant.nickname });
      return {
        spoken: { kind: 'player', name, level: occupant.level },
        name,
        level: occupant.level,
        named: true,
      };
    }
    case 'empty':
      return {
        spoken: { kind: 'empty', unfilled: occupant.unfilled },
        name: playerName({ kind: 'unknown' }),
        named: false,
      };
  }
}
