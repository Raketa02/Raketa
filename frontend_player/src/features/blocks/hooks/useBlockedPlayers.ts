/**
 * **Blocked players** — the You tab's row reads it for its count line, and the screen behind the
 * row for its list. One key, so a press on the screen is on the row the moment the player goes
 * back. The global defaults suit it: a list only this player changes, re-read by every block and
 * unblock rather than on a clock.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { BlockedPlayer } from '../domain/blockedPlayer';
import { readBlockedPlayers } from '../use-cases/blocks';

import { blockKeys } from './blockKeys';

export function useBlockedPlayers() {
  return useQuery<readonly BlockedPlayer[], AppError>({
    queryKey: blockKeys.list(),
    queryFn: ({ signal }) => readBlockedPlayers({ signal }),
  });
}
