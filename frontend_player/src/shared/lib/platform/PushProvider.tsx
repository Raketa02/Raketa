/**
 * How a screen reaches the phone's push notifications without knowing which phone it is —
 * `PaymentsProvider`'s shape, for its reasons: the default is the real device, so nothing in the
 * app wires this up, and what the provider is for is a test wrapping the tree in a phone whose
 * permission, token and pushes the suite decides.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { devicePush, type PushPort } from './push';

const PushContext = createContext<PushPort>(devicePush);

export interface PushProviderProps {
  readonly port: PushPort;
  readonly children: ReactNode;
}

export function PushProvider({ port, children }: PushProviderProps) {
  return <PushContext.Provider value={port}>{children}</PushContext.Provider>;
}

/** The push notifications this tree runs against. The device's, unless a test said otherwise. */
export function usePush(): PushPort {
  return useContext(PushContext);
}
