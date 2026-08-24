/**
 * Leave the standby queue on one match.
 *
 * A thin pass-through, and `ADR-0009`'s escape hatch covers exactly that: there is
 * no rule to hold here, because **nothing can refuse** (`ADR-0087`) and a standby
 * place confers nothing to weigh. What comes back is Now's update, which for this
 * act is the *gone* form — and it is mapped through the same `toNowUpdate` a seat
 * write and a departure run through, so the two forms are told apart by the wire's
 * own discriminator here as everywhere else.
 *
 * The response carries **only** the update (`StandbyWriteResponse`), so there is
 * nothing else to map: no `applied`, because nothing can refuse, and no regions,
 * because removing a card is not the same as recomposing the two she owns.
 */

import { leaveStandby as deleteStandbyPlace } from '../api/standbyApi';
import type { NowUpdate } from '../domain/ComposedScreen';
import { toNowUpdate } from '../mappers/nowMappers';

export interface LeaveStandbyOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

export function leaveStandby({ matchId, signal }: LeaveStandbyOptions): Promise<NowUpdate> {
  return deleteStandbyPlace({ matchId, signal }).then((wire) => toNowUpdate(wire.update));
}
