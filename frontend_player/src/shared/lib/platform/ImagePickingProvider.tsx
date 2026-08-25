/**
 * How a screen reaches the photo library without knowing which one it is.
 *
 * The port is an interface with two implementations — `deviceImagePicking`, which talks to
 * the OS, and `fakeImagePicking()` in `src/test-support/platform.ts`, which a test drives.
 * Something has to choose between them, and a screen importing `deviceImagePicking`
 * directly would be a screen no test can put in front of a refused permission.
 *
 * **The default is the real device**, so nothing in the app has to wire this up: the root
 * layout composes providers for state that has to be created, and a port that already
 * exists is not that. What the provider is for is the other direction — a test wrapping
 * the tree in a library it decides the contents of.
 *
 * A context rather than a module-level setter, which is what `configureHttp` is: that one
 * exists to break a genuine import cycle between the client and the auth subsystem, and
 * there is no cycle here. A React value read by React components belongs in React, where
 * two tests in one file cannot leak a port into each other.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { deviceImagePicking, type ImagePickingPort } from './imagePicking';

const ImagePickingContext = createContext<ImagePickingPort>(deviceImagePicking);

export interface ImagePickingProviderProps {
  readonly port: ImagePickingPort;
  readonly children: ReactNode;
}

export function ImagePickingProvider({ port, children }: ImagePickingProviderProps) {
  return <ImagePickingContext.Provider value={port}>{children}</ImagePickingContext.Provider>;
}

/** The photo library this tree is running against. The device's, unless a test said otherwise. */
export function useImagePicking(): ImagePickingPort {
  return useContext(ImagePickingContext);
}
