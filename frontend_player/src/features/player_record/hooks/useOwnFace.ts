/**
 * **The reader's own face** — their photograph off their own record, or nothing, for the one
 * surface that draws the reader as a tile rather than as a seat
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3, [#433](https://github.com/Raketa02/Raketa/issues/433)).
 *
 * ## Why a read at all
 *
 * Nothing carries a player's own photograph onto a court: a seat card is about the *other*
 * people, and every court in the app draws the reader's own seat as the poster. The yes screen
 * is the first surface where that is wrong — the mock's tile is *the person's photo when the
 * app has one, the reader's own included* — and the only route that serves the reader their own
 * photograph is the ungated `/players/me/record`, which is this feature's. So the read crosses
 * into `player_record` through its public surface, the sanctioned shape, and this hook is the
 * whole of what crosses: a URL or nothing, and whether the answer is in.
 *
 * ## One read per open, and the record's own posture
 *
 * The record says *cached for the session*, and this hook deliberately reads once **per open**
 * instead — `PLAYER_RECORD_QUERY_OPTIONS` whole, which is the feature's own answer to the same
 * read on the sheet. The reason is the link: `photo_url` is a signed address minted per response
 * and valid for **five minutes** (`PHOTO_URL_VALID_FOR_MINUTES`), so a URL held for a session
 * would be a dead link on the second yes screen of an evening — drawn as a blank tile, which is
 * worse than the poster. A cold read on each open costs one request on a tap a player makes a
 * few times a week, which is exactly the budget the sheet already spends per open; and with
 * `gcTime: 0` nothing stale is there to be drawn first, so no tile swaps mid-animation — the
 * one thing the record insists on.
 *
 * **The poster if it does not answer.** `retry: false` is part of those options, and it is
 * load-bearing here: the entrance waits for this read, and three retries with backoff would hold
 * the screen blank for seven seconds over a photograph the poster stands in for anyway. A
 * failure resolves to *no photograph*, and the screen does not distinguish the two.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PlayerRecord } from '../domain/playerRecord';
import { readPlayerRecord } from '../use-cases/readPlayerRecord';

import { PLAYER_RECORD_QUERY_OPTIONS, playerRecordKeys } from './playerRecordKeys';

export interface OwnFace {
  /** The signed link, or nothing — no photograph, or a read that did not answer. */
  readonly photoUrl: string | undefined;
  /** Whether the read is in, either way. A surface that waits for its faces waits on this. */
  readonly settled: boolean;
}

/**
 * @param playerId who the reader is — `RecordSubject`'s own shape, which carries the id on the
 *   `me` arm for the poster's sake; the route is addressed by the bearer token and never by it.
 *   `undefined` while the reader is not yet known, which is *not settled* rather than a read
 *   fired about nobody.
 */
export function useOwnFace(playerId: string | undefined): OwnFace {
  const { data, isPending } = useQuery<PlayerRecord, AppError, string | undefined>({
    queryKey: playerRecordKeys.ownFace(),
    queryFn: ({ signal }) =>
      readPlayerRecord({ subject: { kind: 'me', playerId: playerId ?? '' }, signal }),
    select: (record) => record.photoUrl,
    enabled: playerId !== undefined,
    ...PLAYER_RECORD_QUERY_OPTIONS,
  });

  return { photoUrl: data, settled: !isPending };
}
