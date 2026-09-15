/**
 * The vibration motor, behind a port. **The only module that imports `expo-haptics`.**
 *
 * The first haptic in the app arrived with the yes screen
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2): one soft success buzz as the word lands. It is the fourth port and not a line in a
 * component, on the three others' argument: a native module has no JS implementation
 * underneath it, so a screen that imports one is a screen no suite can put in front of — and
 * *exactly one buzz, and none under reduced motion* is a rule worth a test that can count.
 *
 * **Two verbs, because there are two haptics.** A port grows a verb when a surface needs one
 * and the record allows it; a menu of every feedback the OS offers would be an invitation to
 * buzz on things nobody decided should buzz. The second arrived with the deck's drag
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §3): one light tick as the finger first crosses the threshold, so a thumb knows the release
 * will commit without looking at the stamp — off under reduced motion, with the motion.
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
  /** One light tick — the OS's own *impact: light* — as a drag crosses its threshold. */
  readonly light: () => void;
}

export const deviceHaptics: HapticsPort = {
  success() {
    // Fire and forget: the promise resolves when the motor has been told, and nothing waits
    // on that. A refusal is swallowed for the reason the module note gives.
    void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
  },
  light() {
    void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => undefined);
  },
};
