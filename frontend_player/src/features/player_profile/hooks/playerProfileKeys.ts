/**
 * Every query key this feature uses, in one factory.
 *
 * Inline string keys are how two call sites end up caching the same read under two keys —
 * and how a mutation invalidates one of them.
 */

import type { Sport } from '@/shared/vocabulary/sport';

export const playerProfileKeys = {
  all: ['player-profile'] as const,
  /**
   * The tag vocabulary and its bounds, under **one** key.
   *
   * They arrive in one response because they are needed by the same part of onboarding at
   * the same moment, and splitting the key would turn one round trip into two while
   * pretending they can disagree.
   */
  options: () => [...playerProfileKeys.all, 'options'] as const,
  /**
   * Every fact `GET /players/me/profile` carries: the week, the declarations, and what You
   * draws beside them.
   *
   * **One key for all of them**, because they arrive in one response and are changed by the
   * same acts — the week write and the declaration write each change one of them, and a key
   * per fact would mean cache entries a single response has to be split across.
   *
   * It is on the **ordinary defaults** and refetches: it is not a ranked list that would reorder
   * under a player's finger, so it moves while you look at it like any other read.
   */
  surface: () => [...playerProfileKeys.all, 'surface'] as const,
  /**
   * The signed address of one of the player's own photographs — what a tile on the You tab
   * draws a held photo from. Its own entry per id, so a row of three is three reads that
   * each say their own standing, and a re-arrangement re-reads nothing.
   */
  photo: (photoId: string) => [...playerProfileKeys.all, 'photo', photoId] as const,
  /**
   * The cards each kind deals the player now in one sport, across their groups — what You ›
   * *What kind of game* counts a change in (ADR-0201 §6). One entry per sport, because a row is
   * opened one sport at a time and a change of intent is made in one.
   */
  deckCounts: (sport: Sport) => [...playerProfileKeys.all, 'deck-counts', sport] as const,
  /** No declared row open — a key nothing is ever read under, so no sport's count is borrowed. */
  deckCountsNone: () => [...playerProfileKeys.all, 'deck-counts', 'none'] as const,
};

/**
 * **The one queue every write of the Location area joins** — `PUT /players/me/location` from the
 * cold start and from *Where you play*'s two controls (#733). A mutation `scope` runs its writes
 * one after another, so a pick and a reading pressed in quick succession reach the server in the
 * order they were pressed, and the area held is the one the screen last drew.
 */
export const LOCATION_WRITES = { id: 'player-profile:location' } as const;
