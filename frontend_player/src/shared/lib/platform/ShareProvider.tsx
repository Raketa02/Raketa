/**
 * How a screen reaches the share sheet without knowing which one it is — `ClipboardProvider`'s
 * shape, for its reasons: the default is the real device, so nothing in the app wires this up,
 * and what the provider is for is a test wrapping the tree in a sheet that records what it was
 * handed.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceShare, type SharePort } from './share';

const ShareContext = createContext<SharePort>(deviceShare);

export interface ShareProviderProps {
  readonly port: SharePort;
  readonly children: ReactNode;
}

export function ShareProvider({ port, children }: ShareProviderProps) {
  return <ShareContext.Provider value={port}>{children}</ShareContext.Provider>;
}

/** The share sheet this tree is running against. The device's, unless a test said otherwise. */
export function useShare(): SharePort {
  return useContext(ShareContext);
}
