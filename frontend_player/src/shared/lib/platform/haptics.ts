/**
 * The vibration motor, behind a port. **The only module that imports `expo-haptics`.**
 *
 * The first haptic in the app arrived with the yes screen
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2): one soft success buzz as the word lands. It is the fourth port and not a line in a
 * component, on the three others' argument: a native module has no JS implementation
 * underneath it, so a screen that imports one is a screen no suite can put in front of — and
 * *exactly one buzz, and none under reduced motion* is a rule worth a test that can count.
 *
 * **One verb, because there is one haptic.** A port grows a verb when a surface needs one and
 * the record allows it; a menu of every feedback the OS offers would be an invitation to buzz
 * on things nobody decided should buzz.
 *
 * **It never rejects.** A phone with no motor, a platform that refuses, a call from a
 * background app: the buzz did not happen, and nothing a screen does next depends on whether
 * it did. The fake in `src/test-support/platform.ts` keeps the same promise.
 */

import * as Haptics from 'expo-haptics';

/**
 * What the app may ask of the motor.
 *
 * Screens depend on this interface; `deviceHaptics` is the one implementation that talks to
 * the OS, and a test substitutes `fakeHaptics()` from `src/test-support/platform.ts`.
 */
export interface HapticsPort {
  /** One soft success buzz — the OS's own *notification: success* pattern. */
  readonly success: () => void;
}

export const deviceHaptics: HapticsPort = {
  success() {
    // Fire and forget: the promise resolves when the motor has been told, and nothing waits
    // on that. A refusal is swallowed for the reason the module note gives.
    void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
  },
};
