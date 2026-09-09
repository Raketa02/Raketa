/**
 * *We are meeting here.*
 *
 * The value is **tidied here rather than at the box**, so the one thing sent is the one thing the
 * cap was measured against — the control and the write are two readers of `mayRecordPlace`, and
 * a component that sent the untidied string would be sending a value the check had approved of a
 * different shape of.
 *
 * **Nothing is truncated.** An over-long note is refused by `mayRecordPlace` before it is sent and
 * by the server if it ever gets past that: *a shortened note is one the person who typed it
 * believes they wrote whole, in front of the other people on the court.*
 */

import { putPlace } from '../api/plansApi';
import { tidyPlace, type Plan } from '../domain/slots';
import { toPlan } from '../mappers/planMappers';

export interface SetPlaceAsk {
  readonly gameId: string;
  /** As the player typed it. Tidied on the way out, never on the way back. */
  readonly written: string;
}

export function setPlace({ gameId, written }: SetPlaceAsk): Promise<Plan> {
  return putPlace(gameId, { place: tidyPlace(written) }).then(toPlan);
}
