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
 * Play's two postures, applied to a sheet that opens over Play. A refetch on focus would move a
 * Player Score under the reader while they were looking at it, and the automatic retry would
 * put the *Try again* they can see roughly thirty-one seconds away.
 *
 * ## …and nothing is cached between opens, because the gates are live
 *
 * This is the one place a record parts company with the ranked list beside it. A search record
 * is **immutable**: it is read back by id, `staleTime: Infinity` is honest about it, and the
 * gates that have moved since arrive as *withheld rows* on the read-back. A record is the
 * opposite — the four fail-closed gates are re-evaluated **on every open**, so a cached copy is
 * a copy the gates have stopped being applied to. A hold placed between two opens inside one
 * session would be answered by the entry the first open wrote, which is the one failure this
 * whole route's admission rule exists to prevent — and so would the reader's own block, which the
 * record now says (`blocked_by_you`).
 *
 * So `staleTime` and `gcTime` are both **nought**: every open is a cold read, and a sheet that
 * closes takes its answer with it. `the-player-record.md` §6.6 reaches the same place by a
 * different road — it keys on the citation *"so a key that dropped it would serve a cached
 * record after the entitlement that fetched it stopped applying"* — and no citation crosses on
 * the emitted contract, so there is nothing to key on and the cache itself is what goes. It
 * costs one request per deliberate tap, which is the latency budget that tap already has.
 *
 * The price is the sentence §6.6 wanted in exchange: the sheet and the card underneath it can
 * disagree about a Player Score inside one session. They **should** — a card is a recorded
 * answer frozen into a search and a record is current at the moment of opening, which is the
 * whole reason this is a route rather than a widened card.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { RecordSubject } from '../domain/playerRecord';

export const PLAYER_RECORD_QUERY_OPTIONS = {
  /** Every open is a cold read, because the gates it was refused or admitted by are live. */
  staleTime: 0,
  /** And a closed sheet takes its answer with it, so nothing stale is there to be drawn. */
  gcTime: 0,
  /** A figure must not move under the reader while they are reading it. */
  refetchOnWindowFocus: false,
  /** Nor when the connection comes back: the reader asked once, by tapping a face. */
  refetchOnReconnect: false,
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
  /**
   * **The reader's own face** — `useOwnFace`, the yes screen's one read of this feature.
   *
   * Its own entry rather than `detail({ kind: 'me' }, undefined)`, because the two are different
   * questions of one route: the sheet holds a whole record and is closed with it, and this holds
   * a URL and is read once per open of a screen the sheet is never on. Sharing the entry would
   * have one observer's `select` and `gcTime` deciding for the other.
   */
  ownFace: () => [...playerRecordKeys.all, 'me', 'face'] as const,
  /**
   * **Every read of your own record** — the sheet's entry from any sport and the face — as a
   * prefix, for the one write that moves what they say: the filter's switch (#662). The record is
   * never cached between opens, so what this reaches is the read on screen under the switch.
   */
  own: () => [...playerRecordKeys.all, 'me'] as const,
};
