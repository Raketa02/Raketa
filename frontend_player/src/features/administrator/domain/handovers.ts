/**
 * **What the handover sheet tells next**
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
 * §2): one club at a time — the club of the oldest handover the account has not been told about —
 * with **every** group that club handed it, so a club that hands over three groups at once is one
 * sheet and not three. What this launch already closed is left out, because the server may still
 * list it until the write that says so has landed.
 */

import type { Handover } from '@/features/auth/types';

/** One group on the sheet, and the queue it came with. */
export interface HandedGroup {
  readonly groupId: string;
  readonly groupName: string;
  readonly waitingCount: number;
}

/** **One sheet**: a club, and the groups it handed this account. */
export interface HandoverNotice {
  readonly clubId: string;
  readonly clubName: string;
  readonly groups: readonly HandedGroup[];
}

export function nextHandoverNotice(
  handovers: readonly Handover[],
  closed: readonly string[],
): HandoverNotice | undefined {
  const untold = handovers.filter((handover) => !closed.includes(handover.groupId));
  const first = untold[0];
  if (first === undefined) return undefined;
  return {
    clubId: first.clubId,
    clubName: first.clubName,
    groups: untold
      .filter((handover) => handover.clubId === first.clubId)
      .map(({ groupId, groupName, waitingCount }) => ({ groupId, groupName, waitingCount })),
  };
}
