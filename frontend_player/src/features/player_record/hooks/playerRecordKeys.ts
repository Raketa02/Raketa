/**
 * This feature's query-key factory, and the one **override of the global defaults** beside it.
 *
 * ## The sport is in the key, because it changes the answer
 *
 * `?sport=` selects which sport the skill card is drawn for — the one asked for where they are
 * rated in it, and otherwise the one they have played most. Two arrivals at one person from two
 * sports are two different sheets, and a key that dropped the sport would draw a padel card
 * over a squash arrival for as long as the entry lived.
 *
 * **Admission is not in the key and cannot be**: whether a record opens at all is decided in
 * the partitions the platform already showed this person in, which is not something a client
 * sends and therefore not something it could key on.
 *
 * ## Your own record has a key of its own
 *
 * `/players/me/record` is a different route with a different gate, and the account's own id is
 * not what it is addressed by. Keying it under the subject's id would make the two routes one
 * cache entry the day a player opened their own face from a court they were seated on.
 *
 * ## Nothing here background-refetches, and nothing retries unasked
 *
 * Play's two postures, applied to a sheet that opens over Play. A record is **fetched on the
 * tap** and read once: a refetch on focus would move a Player Score under the reader while
 * they were looking at it, and the automatic retry would put the *Try again* they can see
 * roughly thirty-one seconds away. `staleTime` matches the search read-back's for the reason
 * that read has it — so the sheet and the card underneath it cannot disagree about the same
 * person inside one session.
 *
 * **`gcTime` is deliberately the app's own five minutes**, unlike the ranked list's. Nothing
 * holds a reference to a record after its sheet closes: a search record outlives the screens
 * that read it because a line-up is bound to its id, and a record is bound to nothing.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { RecordSubject } from '../domain/playerRecord';

export const PLAYER_RECORD_QUERY_OPTIONS = {
  /** Superseded by closing the sheet and opening it again, and by nothing else. */
  staleTime: Infinity,
  /** A figure must not move under the reader while they are reading it. */
  refetchOnWindowFocus: false,
  /** A retry the player cannot see is a retry they cannot reach. */
  retry: false,
} as const;

export const playerRecordKeys = {
  all: ['player-record'] as const,
  /**
   * One person's record, as read from one sport.
   *
   * `me` is a segment rather than an id, so the ungated route and the parameterised one can
   * never share an entry — see the note above.
   */
  detail: (subject: RecordSubject, sport: Sport | undefined) =>
    [
      ...playerRecordKeys.all,
      subject.kind === 'me' ? 'me' : subject.playerId,
      sport ?? 'their-most-played',
    ] as const,
};
