/**
 * How a screen reaches the clipboard without knowing which one it is — `HapticsProvider`'s
 * shape, for its reasons: the default is the real device, so nothing in the app wires this up,
 * and what the provider is for is a test wrapping the tree in a clipboard holding what it chose.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceClipboard, type ClipboardPort } from './clipboard';

const ClipboardContext = createContext<ClipboardPort>(deviceClipboard);

export interface ClipboardProviderProps {
  readonly port: ClipboardPort;
  readonly children: ReactNode;
}

export function ClipboardProvider({ port, children }: ClipboardProviderProps) {
  return <ClipboardContext.Provider value={port}>{children}</ClipboardContext.Provider>;
}

/** The clipboard this tree is running against. The device's, unless a test said otherwise. */
export function useClipboard(): ClipboardPort {
  return useContext(ClipboardContext);
}
