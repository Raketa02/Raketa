import { Notice } from '@/ui/Notice';

import type { LinkState } from '../mappers';

/**
 * **What a link that can no longer set a password says**: that the password was just set here,
 * with what to do next, or what the link is now, one sentence per state. Nothing while it works.
 */
export function LinkOutcome({
  state,
  justSet,
  done,
  states,
}: {
  state: LinkState;
  /** The page was reached by setting the password on it. */
  justSet: boolean;
  /** What to do next, once the password is set here. */
  done: string;
  states: Readonly<Record<Exclude<LinkState, 'valid'>, string>>;
}) {
  if (state === 'valid') return null;
  if (justSet && state === 'used') return <Notice tone="success">{done}</Notice>;
  return <Notice tone="info">{states[state]}</Notice>;
}
