/**
 * How a screen follows a room without knowing what a socket is.
 *
 * The third of the three port providers, for the same reason and with the same default as
 * `LocationProvider` and `ImagePickingProvider`: the port is an interface with two
 * implementations — `deviceLiveStream`, which opens Server-Sent Events, and `fakeLiveStream()` in
 * `src/test-support/platform.ts`, which a test drives — and a screen importing the real one
 * directly would be a screen no suite can put in front of a severed channel.
 *
 * **The default is the real channel**, so nothing in the app has to wire this up. What the
 * provider is for is the other direction: a test deciding what the channel is doing, which for
 * this port is every state worth drawing.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceLiveStream, type LiveStreamPort } from './liveStream';

const LiveStreamContext = createContext<LiveStreamPort>(deviceLiveStream);

export interface LiveStreamProviderProps {
  readonly port: LiveStreamPort;
  readonly children: ReactNode;
}

export function LiveStreamProvider({ port, children }: LiveStreamProviderProps) {
  return <LiveStreamContext.Provider value={port}>{children}</LiveStreamContext.Provider>;
}

/** The live channel this tree runs against. The real one, unless a test said otherwise. */
export function useLiveStream(): LiveStreamPort {
  return useContext(LiveStreamContext);
}
