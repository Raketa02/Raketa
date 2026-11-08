/**
 * **The app moving between the foreground, `inactive` and the background**, as a test can move it.
 *
 * `AppState` is a native module, and the RN jest preset fakes `addEventListener` with a mock that
 * records nothing anybody can replay. This stands in for the platform's half, as `hardwareBack.ts`
 * does for the back button: it keeps what the app subscribed to `change` and calls it with the
 * state a test names — `background`, `inactive` (iOS's app switcher, a call banner, Face ID behind
 * the keychain's autofill) or `active`.
 *
 * **The preset's mock is put back by hand.** It is already a `jest.fn`, so `spyOn` hands that same
 * mock back rather than wrapping it, and `mockRestore` would leave it answering `undefined` — and
 * the next `subscription.remove()` would throw. `stopWatchingAppState` gives it back a subscription
 * that removes nothing, which is what the preset's own answers.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { AppState, type AppStateStatus, type NativeEventSubscription } from 'react-native';

type Listener = (state: AppStateStatus) => void;

let listeners: Listener[] = [];

/** Start recording what the app subscribes. Call it **before** rendering. */
export function watchAppState(): void {
  listeners = [];
  jest
    .spyOn(AppState, 'addEventListener')
    .mockImplementation((event: string, listener: Listener): NativeEventSubscription => {
      if (event === 'change') listeners.push(listener);
      return {
        remove: () => {
          listeners = listeners.filter((one) => one !== listener);
        },
      };
    });
}

/** Forget everything subscribed, and give the preset's mock its own answer back. */
export function stopWatchingAppState(): void {
  listeners = [];
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: () => undefined }));
}

/** The OS moving the app — every `change` subscriber hears it, in the order they subscribed. */
export function moveAppTo(state: AppStateStatus): void {
  for (const listener of [...listeners]) listener(state);
}
