/**
 * **A reset's link, wire to view.** The only file in this feature that imports a generated type
 * (ADR-0187 §6).
 */

import { toLinkState, type LinkState } from '@/features/set-password/mappers';
import type { components } from '@/generated/schema';

type WireReset = components['schemas']['ResetPageResponse'];

/** What the reset page reads off its link: **its state and nothing else** (ADR-0187 §5). */
export interface ResetLink {
  readonly state: LinkState;
}

export function toResetLink(wire: WireReset): ResetLink {
  return { state: toLinkState(wire.state) };
}
