/**
 * **A player's live yeses, read** (#554) — a pass-through: which yeses are live, in what order, is
 * the server's projection (`ReadLiveYeses`, #539), and nothing about it is decided on the way in.
 */

import { getLiveYeses, getPaymentsToConfirm, type Cancellable } from '../api/proposalsApi';
import type { PaymentToConfirm } from '../domain/fill';
import type { LiveYeses } from '../domain/liveYes';
import { toPaymentsToConfirm } from '../mappers/fillMappers';
import { toLiveYeses } from '../mappers/liveYesMappers';

export async function readLiveYeses(options: Cancellable = {}): Promise<LiveYeses> {
  return toLiveYeses(await getLiveYeses(options));
}

/** The reader's refused shares still waiting for them (#555). */
export async function readPaymentsToConfirm(
  options: Cancellable = {},
): Promise<readonly PaymentToConfirm[]> {
  return toPaymentsToConfirm(await getPaymentsToConfirm(options));
}
