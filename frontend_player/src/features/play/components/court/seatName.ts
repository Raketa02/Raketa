/**
 * What a court calls whoever is in a seat — **one word, through §15's one formatter.**
 *
 * [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §15: *"One
 * `playerName()`: the handle, whole, and `You` for yourself"*, and ADR-0107's rule that
 * inventing a familiar form is the product addressing somebody by a name they never gave it.
 *
 * It is one function because three things on this court say a person's name and **all three
 * say the same string**: the label drawn under a face, the clear badge's *Remove {name} from
 * {side}*, and the guard toast a refused tap raises. The difference between them is the box,
 * not the word — the 46pt seat truncates its copy and the two sentences do not — which is
 * exactly why *"a seat label may truncate visually; a sentence may not, and a spoken name
 * never does"* is a statement about components rather than about formatters.
 *
 * **The empty seat's word is a question mark**, which `playerName` already owns as its unknown
 * and which is deliberately not a word: the court states an empty seat with a dashed ring and
 * a plus, and a label reading *open* underneath would be the same fact printed twice at 9,5pt.
 */

import { playerName } from '@/shared/formatting/playerName';

import type { CourtSeatOccupant } from './CourtSeat';

export function seatName(occupant: CourtSeatOccupant): string {
  switch (occupant.kind) {
    case 'you':
      return playerName({ kind: 'you' });
    case 'player':
      return playerName({ kind: 'player', nickname: occupant.nickname });
    case 'empty':
      return playerName({ kind: 'unknown' });
  }
}
