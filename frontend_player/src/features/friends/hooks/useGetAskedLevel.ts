/**
 * **The coral button on a friend's ask for a level** — *Get your padel level*, or *Carry on*
 * ([#765](https://github.com/Raketa02/Raketa/issues/765); the friends screens §6.4).
 *
 * **It is the *level asked* notice's act** — `onboarding`'s `useAddASport` from Home: the sport's
 * questionnaire started, its unfinished run handed back if there is one, a pass of that one sport
 * begun, so every way out lands on Home. One for the whole row, so a second card pressed while the
 * first starts does nothing, and `starting` says which card is.
 *
 * **A start that fails is told to the caller** (`onFailed`), whose words it is — the notice's own
 * toast. **`sport_already_rated` is also the state moving**: the level was got since Home was read,
 * so the card has gone on the server, and Home and the bell are read again.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { FROM_HOME, useAddASport } from '@/features/onboarding/types';
import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { rereadHomeAndBell, type Reread } from './useFriendWrites';

/** The level was got since the card was drawn — onboarding's start refuses a second rating. */
const ALREADY_RATED = 'sport_already_rated';

export interface GetAskedLevel {
  readonly get: (sport: Sport, onFailed: (error: AppError) => void) => void;
  /** The sport whose start is in flight, so its card alone says so. */
  readonly starting: Sport | undefined;
}

/** @param rereadBell the bell's re-read, handed in — the bell is `notifications`'. */
export function useGetAskedLevel(rereadBell: Reread): GetAskedLevel {
  const client = useQueryClient();
  const { rate, starting } = useAddASport(FROM_HOME);
  const get = useCallback(
    (sport: Sport, onFailed: (error: AppError) => void) =>
      rate(sport, {
        onError: (error) => {
          onFailed(error);
          if (error.code === ALREADY_RATED) void rereadHomeAndBell(client, rereadBell);
        },
      }),
    [client, rate, rereadBell],
  );
  return { get, starting };
}
