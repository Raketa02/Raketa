/**
 * **What a level got changes on Home** ([#765](https://github.com/Rakieta02/Rakieta/issues/765); the
 * friends mechanics §5.1) — its sport's ASKED FOR A LEVEL card dropped and Home read again
 * (`proposals`' `rereadHomeAfterALevel`), and the bell, whose *level asked* row went with the card
 * (`notifications`' `rereadNotices`).
 *
 * The entry gate runs it as a rating pass ends (`onboarding`'s `useEndOnboardingPass`), before the
 * shell is drawn, so the card is already gone on the way back from *Your rating*. The shell's because
 * it composes Home and the bell, and the gate stays a route file that hands a callback on.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { rereadNotices } from '@/features/notifications/types';
import { rereadHomeAfterALevel } from '@/features/proposals/types';
import type { Sport } from '@/shared/vocabulary/sport';

export function useRereadAfterALevel(): (sports: readonly Sport[]) => void {
  const client = useQueryClient();
  return useCallback(
    (sports: readonly Sport[]) =>
      void Promise.all([rereadHomeAfterALevel(client, sports), rereadNotices(client)]),
    [client],
  );
}
