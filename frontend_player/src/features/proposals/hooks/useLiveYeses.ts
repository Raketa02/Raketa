/**
 * **The player's live yeses** — `GET /players/me/live-yeses`, behind You › Payments' *LIVE YESES*
 * (#554) and a group's *You're In* (#557).
 *
 * The app's defaults, for the deck's reason: thirty seconds fresh, read again on focus. A yes and a
 * withdraw mark it stale wherever they are said (`useAnswerCard`, `useWithdrawYes`), so a player
 * back from the deck finds the list as they left it; a game filling or lapsing is the server's and
 * arrives with the next read.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PaymentToConfirm } from '../domain/fill';
import type { Home } from '../domain/home';
import type { LiveYeses } from '../domain/liveYes';
import { readLiveYeses, readPaymentsToConfirm } from '../use-cases/liveYeses';

import { proposalKeys } from './proposalKeys';

export function useLiveYeses() {
  return useQuery<LiveYeses, AppError>({
    queryKey: proposalKeys.liveYeses(),
    queryFn: ({ signal }) => readLiveYeses({ signal }),
  });
}

/**
 * **The reader's refused shares, waiting for them** (#555) — You › Payments' *TO CONFIRM*, the way
 * back to a seat for a player whose share was refused when somebody else's yes filled the game. The
 * app's defaults; the fill re-reads it whenever a yes or a confirmation could have moved it.
 *
 * **It starts from Home's read** (#819): Home serves the same rows (`payments_to_confirm`, #815)
 * and is read all session, so a screen that opens on a payment — a booked game's details, a
 * rescue's, You › Payments — draws what Home last read rather than a *Pay* that turns into
 * *Confirm* a moment later. Seeded at Home's read's own time, so the words are said against it and
 * the read runs again once that is stale, as any read does; a seed only where nothing is held.
 */
export function usePaymentsToConfirm() {
  const client = useQueryClient();
  return useQuery<readonly PaymentToConfirm[], AppError>({
    queryKey: proposalKeys.paymentsToConfirm(),
    queryFn: ({ signal }) => readPaymentsToConfirm({ signal }),
    initialData: () => client.getQueryData<Home>(proposalKeys.home())?.paymentsToConfirm,
    initialDataUpdatedAt: () => client.getQueryState(proposalKeys.home())?.dataUpdatedAt,
  });
}
