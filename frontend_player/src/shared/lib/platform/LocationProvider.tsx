/**
 * How a screen reaches the device's position without knowing whose it is.
 *
 * The twin of `ImagePickingProvider`, for the same reason and with the same defaults: the
 * port is an interface with two implementations — `deviceLocation`, which talks to the OS,
 * and `fakeLocation()` in `src/test-support/platform.ts`, which a test drives — and a
 * screen importing `deviceLocation` directly would be a screen no test can put in front of
 * a refused permission.
 *
 * **The default is the real device**, so nothing in the app has to wire this up. What the
 * provider is for is the other direction: a test deciding what the phone knows and what
 * the player answers.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceLocation, type LocationPort } from './location';

const LocationContext = createContext<LocationPort>(deviceLocation);

export interface LocationProviderProps {
  readonly port: LocationPort;
  readonly children: ReactNode;
}

export function LocationProvider({ port, children }: LocationProviderProps) {
  return <LocationContext.Provider value={port}>{children}</LocationContext.Provider>;
}

/** The device this tree is running against. The real one, unless a test said otherwise. */
export function useLocation(): LocationPort {
  return useContext(LocationContext);
}
