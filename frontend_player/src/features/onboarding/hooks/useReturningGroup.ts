/**
 * **The group a running pass returns to** — its id, or nothing for a pass begun anywhere else
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §5).
 *
 * The last *Your rating* of a pass begun on a group says *Back to {group name}*, and the name is
 * TanStack Query's, in the groups feature — which imports this one at runtime, so this one
 * cannot import it back. So the result **route** asks for both: this id, and the group's name by it, and hands
 * the name to the screen. The pass keeps the identifier only (`domain/onboardingPass`).
 */

import { returnOf } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

/** Read off `returnOf`, the rule the gate lands by, so the name and the landing are one group's. */
export function useReturningGroup(): string | undefined {
  return useOnboardingPass((state) => {
    const back = state.pass === undefined ? undefined : returnOf(state.pass);
    return back?.kind === 'group' ? back.groupId : undefined;
  });
}
