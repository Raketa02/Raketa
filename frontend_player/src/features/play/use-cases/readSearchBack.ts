/**
 * **Re-reading a search** — the pool's own act, and the one that makes a withheld seat real.
 *
 * `GET /searches/{id}` answers *"in the same shape the `POST` returned it"* and **never
 * recomputes**: the record is immutable and the gates are live
 * ([ADR-0104](../../../../../docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)).
 * What a re-read adds is therefore exactly one thing — a row the fail-closed gates no longer
 * admit, **stated as withheld**, keeping its place and carrying no person
 * ([ADR-0130](../../../../../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)).
 *
 * ## Why it is the pool's and not the builder's
 *
 * The builder reads the record and never fetches it: *"the search that minted it wrote it, and
 * `GET /searches/{id}` is not a substitute"*, because the read-back answers with the envelope
 * and the rows and **not the sport or the week**, which were the request's. Re-reading is the
 * pool's act *"with the origin already in hand"* (`hooks/useBuilder.ts`), and this function is
 * the whole of what that sentence means: the held record supplies everything the wire does not.
 *
 * ## It replaces the answer and keeps everything the answer never carried
 *
 * The entry under `searchKeys.detail(id)` is a `SearchRecord`, and two of its four parts have
 * no representation in a `ShortlistResponse`:
 *
 * - the **origin**, without which the builder loses the sport and the week it draws its court
 *   from — the failure this function exists to make impossible;
 * - the **court**, which only `POST /lineups` ever seats. A re-read of a line-up's own search
 *   answers as a shortlist, so rebuilding the record from the response alone would silently
 *   take away the seats, the arrangements and the four `UnfilledReason` statements one screen
 *   behind the player.
 *
 * So the held record is spread and only the two halves the wire actually re-states are
 * replaced. **The rows may come back shorter**, which is the point: `withheldSeats` is a set
 * difference against them, so a seated player the gates no longer admit becomes a marked seat —
 * and the court draws that as its own fourth spoken kind, a seat with a place and no facts,
 * stating the fact and never the cause.
 */

import { readSearch, type Cancellable } from '../api/playSearchApi';
import type { SearchRecord } from '../domain/lineup';
import { toRankedList } from '../mappers/candidateMappers';

/**
 * @param held whatever `searchKeys.detail(searchId)` holds — the origin, and the answer under
 *   it. It is an argument rather than a read, so the one caller states which record it is
 *   refreshing and this function has no cache to reach into.
 */
export async function readSearchBack(
  held: SearchRecord,
  { signal }: Cancellable = {},
): Promise<SearchRecord> {
  const response = await readSearch(held.searchId, { signal });
  const { envelope, candidates } = toRankedList(response);

  return { ...held, envelope, candidates };
}
