/**
 * How a screen reaches the motor without knowing which one it is — `ImagePickingProvider`'s
 * shape, for its reasons: the default is the real device, so nothing in the app wires this
 * up, and what the provider is for is a test wrapping the tree in a motor it can count.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceHaptics, type HapticsPort } from './haptics';

const HapticsContext = createContext<HapticsPort>(deviceHaptics);

export interface HapticsProviderProps {
  readonly port: HapticsPort;
  readonly children: ReactNode;
}

export function HapticsProvider({ port, children }: HapticsProviderProps) {
  return <HapticsContext.Provider value={port}>{children}</HapticsContext.Provider>;
}

/** The motor this tree is running against. The device's, unless a test said otherwise. */
export function useHaptics(): HapticsPort {
  return useContext(HapticsContext);
}
