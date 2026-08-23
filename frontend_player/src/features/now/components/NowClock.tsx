/**
 * The one clock every countdown on the screen reads.
 *
 * A context rather than a prop threaded through three region components: the value
 * changes every second while a seat claim is running, and a prop would re-render
 * the whole screen at that cadence to move one figure. The provider's own children
 * are handed to it as an element, so a tick re-renders the provider and the
 * countdowns that consume it — nothing else.
 *
 * **It is the only clock, and a card cannot make another.** `ADR-0088` records
 * *"one screen-wide timer, not one per card"* as the version that otherwise gets
 * built by accident; the timer lives in `hooks/useRepaintClock.ts` and no component
 * in this feature arms one, which `nowDiscipline.test.ts` walks for.
 *
 * Absent outside a provider, and that absence draws nothing rather than reaching
 * for the device's clock. A countdown with no clock behind it would be a second
 * reading of *now* in a second place, which is exactly what having one context is
 * for.
 */

import { createContext, useContext, type ReactNode } from 'react';

import type { ComposedScreen } from '../domain/ComposedScreen';
import { useRepaintClock } from '../hooks/useRepaintClock';

const NowClockContext = createContext<number | undefined>(undefined);

export interface NowClockProviderProps {
  readonly screen: ComposedScreen | undefined;
  readonly children: ReactNode;
}

export function NowClockProvider({ screen, children }: NowClockProviderProps) {
  const now = useRepaintClock(screen);

  return <NowClockContext.Provider value={now}>{children}</NowClockContext.Provider>;
}

/** The instant a countdown subtracts from, or `undefined` outside a provider. */
export function useNowClock(): number | undefined {
  return useContext(NowClockContext);
}
