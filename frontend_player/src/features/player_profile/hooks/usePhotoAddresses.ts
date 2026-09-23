/**
 * Where each of the profile's photographs can be drawn from — one signed address per held
 * photo, read together, for the row on the You tab
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The profile read carries the ids and the verdicts and deliberately not the addresses — a
 * signed address is minted per response and stops working, so serving three on a read most
 * callers make for the week would be three signatures nobody looks at. The tile has to draw
 * something, so the screen asks `GET /photos/{id}` for each, under its own key, and seeds the
 * workbench once every one is in: a row of three drawn one tile at a time would be a row
 * whose *first* changed under the finger as the addresses arrived out of order.
 *
 * **Read once per open, and gone with the screen** — `useOwnFace`'s choices for the same
 * class of value, a signed address minted per response: every open is a cold read, and a
 * closed screen takes its answers with it, so nothing keeps an address the route says is not
 * to be stored. Nothing refetches one in the background either — a tile already drawing a
 * picture has nothing to gain from a second link to it — and an address that expired while
 * the screen stayed open draws as a broken picture, which reopening the screen fixes.
 * `retry` is the app's default for a read. `signal` is Query's, passed through as every read
 * passes it.
 */

import { useQueries, type UseQueryOptions } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { UploadedPhoto } from '../domain/photoCollection';
import { readPhotoAddress } from '../use-cases/readPhotoAddress';

import { playerProfileKeys } from './playerProfileKeys';

export interface PhotoAddresses {
  /** Every held photo's address, by id — `undefined` until every one is in. */
  readonly addressOf: ((photoId: string) => string) | undefined;
  /** Whether any read is on its way. False for a profile holding no photos. */
  readonly isPending: boolean;
  /** The first read that failed, for the sentence and the retry. */
  readonly error: AppError | null;
  /** Ask again for whichever failed. */
  readonly refetch: () => void;
}

export function usePhotoAddresses(held: readonly UploadedPhoto[]): PhotoAddresses {
  return useQueries({
    queries: held.map((photo): UseQueryOptions<string, AppError> => ({
      queryKey: playerProfileKeys.photo(photo.photoId),
      queryFn: ({ signal }) => readPhotoAddress({ photoId: photo.photoId, signal }),
      staleTime: 0,
      gcTime: 0,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    })),
    combine: (results) => {
      const addresses = new Map<string, string>();
      held.forEach((photo, at) => {
        const address = results[at]?.data;
        if (address !== undefined) addresses.set(photo.photoId, address);
      });
      const failed = results.find((result) => result.error !== null);

      return {
        // A map that is missing one is a row that cannot be drawn whole, so it is nothing.
        addressOf:
          addresses.size === held.length
            ? (photoId: string) => addresses.get(photoId) ?? ''
            : undefined,
        isPending: results.some((result) => result.isPending),
        error: failed?.error ?? null,
        refetch: () => {
          for (const result of results) {
            if (result.error !== null) void result.refetch();
          }
        },
      };
    },
  });
}
