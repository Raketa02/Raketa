/**
 * The week, the radius and the declaration — the read Play's search screen is drawn from, and
 * the two writes that change it.
 *
 * **Ordinary defaults, deliberately.** Nothing in Play background-refetches a *ranked list*,
 * because foregrounding would reorder the pool under the player's finger; this is not one, and
 * `searchKeys.ts` puts *"the profile and the week grid behind the working copy"* among the
 * reads that should move. A radius widened in *You* on another device should be the radius the
 * next search runs at.
 *
 * **The two mutations write the response into the cache rather than invalidating it.** Each
 * route answers with the value **as the profile now holds it** — the radius after the range
 * and the step were re-checked — so a refetch would be a round trip for an answer already in
 * hand, and Part 7's *"don't immediately refetch what you were just handed"* is the rule. What
 * they must not do is write the number the client *sent*: a client that assumed its own value
 * landed would be re-deciding a bound the server owns.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';
import { changeSearchRadius } from '../use-cases/changeSearchRadius';
import { declarePlayIntent, type PlayIntentDeclaration } from '../use-cases/declarePlayIntent';
import { readProfileSurface } from '../use-cases/readProfileSurface';

import { playerProfileKeys } from './playerProfileKeys';

/** One declaration as the profile now holds it — the pair the write answers with. */
type Declared = { readonly sport: Sport; readonly intent: PlayIntent };

export function useProfileSurface() {
  return useQuery<PlayerProfileSurface, AppError>({
    queryKey: playerProfileKeys.surface(),
    queryFn: ({ signal }) => readProfileSurface({ signal }),
  });
}

/**
 * Widen or narrow the profile's own radius.
 *
 * `retry: false` is the app's mutation default and is right here for the ordinary reason: this
 * is a write, and a retry the player cannot see is a retry they cannot reach.
 */
export function useChangeSearchRadius() {
  const client = useQueryClient();

  return useMutation<number, AppError, number>({
    mutationFn: (radiusKm) => changeSearchRadius(radiusKm),
    onSuccess: (searchRadiusKm) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, searchRadiusKm },
      );
    },
  });
}

/**
 * Declare what kind of game this player wants in one sport.
 *
 * The pair written into the cache is **the route's answer**, not the request: a declaration
 * that landed is the profile holding it, and that is what the search screen's interstitial
 * reads to close itself. An answer naming a sport or an intent this build cannot read has
 * nothing honest to record, so the read is invalidated instead — the interstitial stays open
 * over a refetch rather than closing over a value nothing can draw.
 */
export function useDeclarePlayIntent() {
  const client = useQueryClient();

  return useMutation<Declared | undefined, AppError, PlayIntentDeclaration>({
    mutationFn: (declaration) => declarePlayIntent(declaration),
    onSuccess: (declared) => {
      if (declared === undefined) {
        void client.invalidateQueries({ queryKey: playerProfileKeys.surface() });
        return;
      }

      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined
          ? held
          : {
              ...held,
              playIntents: { ...held.playIntents, [declared.sport]: declared.intent },
            },
      );
    },
  });
}
