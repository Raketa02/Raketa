/**
 * The Android back button, as a test can press it.
 *
 * `BackHandler` is a native module with no JS implementation, and unlike `AppState` the RN
 * jest preset gives it no fake to drive — the three functions it exposes under jest are
 * `exitApp`, `addEventListener` and `removeEventListener`, and nothing calls any of them.
 * So this stands in for the **platform's** half: it records what the app subscribed and
 * replays a press through it in the order Android does.
 *
 * **The order is the whole of what makes this worth having.** Handlers run in *reverse*
 * registration order and the first one returning `true` ends the press — which is exactly
 * why a screen can answer before the navigator does. A helper that called them forwards, or
 * called all of them, would pass against an app whose screens never get a say.
 *
 * **What it cannot model is the fall-through**, and callers have to know it: when no handler
 * claims the press, Android hands it to the activity and the navigator pops. Nothing here
 * pops anything. So `pressHardwareBack()` answers **whether the app claimed it**, and a test
 * that cares about not leaving a flow asserts on that answer — the real pop is the platform's
 * and is not on this side of the boundary.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { BackHandler } from 'react-native';

/** RN's own signature: a handler may decline by returning anything but `true`. */
type BackPress = () => boolean | null | undefined;

let handlers: BackPress[] = [];
let spy: jest.SpyInstance | undefined;

/**
 * Start recording what the app subscribes. Call it **before** rendering.
 *
 * Returns nothing to hold: `stopWatchingHardwareBack` in an `afterEach` is what puts the real
 * module back, and a test that forgets leaves the spy on for the file rather than for the app.
 */
export function watchHardwareBack(): void {
  handlers = [];
  spy = jest
    .spyOn(BackHandler, 'addEventListener')
    .mockImplementation((event: 'hardwareBackPress', handler: BackPress) => {
      if (event === 'hardwareBackPress') handlers.push(handler);
      return {
        remove: () => {
          handlers = handlers.filter((one) => one !== handler);
        },
      };
    });
}

/** Put the real `BackHandler` back, and forget everything subscribed against the fake. */
export function stopWatchingHardwareBack(): void {
  spy?.mockRestore();
  spy = undefined;
  handlers = [];
}

/**
 * Press it.
 *
 * @returns `true` when some handler claimed the press — the app answered, and the platform
 *   would do nothing. `false` when every handler declined, which on a device is the pop this
 *   helper cannot perform.
 */
export function pressHardwareBack(): boolean {
  for (const handler of [...handlers].reverse()) {
    if (handler() === true) return true;
  }
  return false;
}
