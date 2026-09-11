/**
 * The one read this feature makes.
 *
 * **`enabled` is the sheet being open**, which is what makes the second round trip affordable
 * at all: a court of four draws four faces and fires nothing, and the request happens on the
 * tap that asks for it. A record is opened at most a few times a search and never twenty times
 * at once, which is precisely the distinction that refused a batch profile route for the
 * shortlist.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayerRecord, RecordSubject } from '../domain/playerRecord';
import { readPlayerRecord } from '../use-cases/readPlayerRecord';

import { PLAYER_RECORD_QUERY_OPTIONS, playerRecordKeys } from './playerRecordKeys';

export interface PlayerRecordAsk {
  readonly subject: RecordSubject;
  readonly sport?: Sport;
  /** The sheet being open. Nothing is prefetched, and nothing is read for a face nobody tapped. */
  readonly enabled: boolean;
}

export function usePlayerRecord({ subject, sport, enabled }: PlayerRecordAsk) {
  return useQuery<PlayerRecord, AppError>({
    queryKey: playerRecordKeys.detail(subject, sport),
    queryFn: ({ signal }) =>
      readPlayerRecord({ subject, ...(sport === undefined ? {} : { sport }), signal }),
    enabled,
    ...PLAYER_RECORD_QUERY_OPTIONS,
  });
}
