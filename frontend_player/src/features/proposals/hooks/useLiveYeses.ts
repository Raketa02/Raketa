/**
 * **The player's live yeses** — `GET /players/me/live-yeses`, behind You › Payments' *LIVE YESES*
 * and a game's details opened from one of them (#554).
 *
 * The app's defaults, for the deck's reason: thirty seconds fresh, read again on focus. A yes and a
 * withdraw mark it stale wherever they are said (`useAnswerCard`, `useWithdrawYes`), so a player
 * back from the deck finds the list as they left it; a game filling or lapsing is the server's and
 * arrives with the next read.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PaymentToConfirm } from '../domain/fill';
import type { LiveYeses } from '../domain/liveYes';
import { readLiveYeses, readPaymentsToConfirm } from '../use-cases/liveYeses';

import { proposalKeys } from './proposalKeys';

/** `enabled` false asks nothing — for a screen that needs the list only when its own read failed it. */
export function useLiveYeses({ enabled = true }: { readonly enabled?: boolean } = {}) {
  return useQuery<LiveYeses, AppError>({
    queryKey: proposalKeys.liveYeses(),
    queryFn: ({ signal }) => readLiveYeses({ signal }),
    enabled,
  });
}

/**
 * **The reader's refused shares, waiting for them** (#555) — You › Payments' *TO CONFIRM*, the way
 * back to a seat for a player whose share was refused when somebody else's yes filled the game. The
 * app's defaults; the fill re-reads it whenever a yes or a confirmation could have moved it.
 */
export function usePaymentsToConfirm() {
  return useQuery<readonly PaymentToConfirm[], AppError>({
    queryKey: proposalKeys.paymentsToConfirm(),
    queryFn: ({ signal }) => readPaymentsToConfirm({ signal }),
  });
}
