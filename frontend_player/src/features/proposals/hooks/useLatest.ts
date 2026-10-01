/**
 * **A value as of the last render, read later** — the one shape behind every handler a mutation
 * or a timer calls after the render that made it: a mutation's own callbacks outlive the call that
 * started it (TanStack drops a call's callbacks when it is called again), and the fill's timer and
 * sheets call back a screen's closure from a later render.
 *
 * Feature-local, by Part 1's third-caller rule: the deck's answers, the fill's writes and its
 * screens are this feature's three callers.
 */

import { useEffect, useRef } from 'react';

export function useLatest<T>(value: T): { readonly current: T } {
  const latest = useRef(value);
  useEffect(() => {
    latest.current = value;
  });
  return latest;
}
