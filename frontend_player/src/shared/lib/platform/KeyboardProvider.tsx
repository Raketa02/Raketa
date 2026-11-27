/**
 * How a tree reaches the soft keyboard without knowing which one it is — `ShareProvider`'s shape,
 * for its reasons: the default is the real device, so nothing in the app wires this up, and what the
 * provider is for is a test wrapping the tree in a keyboard it raises and drops (#882).
 */

import {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from 'react';

import { deviceKeyboard, windowResizesForKeyboard, type KeyboardPort } from './keyboard';

const KeyboardContext = createContext<KeyboardPort>(deviceKeyboard);

export interface KeyboardProviderProps {
  readonly port: KeyboardPort;
  readonly children: ReactNode;
}

export function KeyboardProvider({ port, children }: KeyboardProviderProps) {
  return <KeyboardContext.Provider value={port}>{children}</KeyboardContext.Provider>;
}

/**
 * **Whether the keyboard has shrunk the window** — up, on a phone whose window shrinks for it:
 * Android. Never on an iPhone, where the keyboard is drawn over the window and covers whatever
 * stands at its foot (ADR-0210 §9).
 *
 * A shell stands its tab bar down while it is true: the bar floats at the window's foot, so on a
 * window shrunk for the keyboard it would ride up above the keyboard and over the field being typed
 * into. Followed, so its reader redraws as the keyboard comes and goes — and only then: on an iPhone
 * the answer never moves, so nothing redraws there at all.
 */
export function useKeyboardShrinksTheWindow(): boolean {
  const keyboard = useContext(KeyboardContext);
  const shrinks = useCallback(() => windowResizesForKeyboard() && keyboard.isUp(), [keyboard]);
  return useSyncExternalStore(keyboard.follow, shrinks, shrinks);
}
