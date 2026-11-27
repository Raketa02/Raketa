/**
 * **How a screen gets out of the keyboard's way**, in one place — and **whether the keyboard is up**.
 *
 * `KeyboardAvoidingView` needs a different `behavior` on each platform and has no sensible
 * cross-platform default: iOS wants `padding`, and Android already resizes the window itself, so
 * passing anything there fights the OS and double-counts the inset.
 *
 * It is here rather than written out at each call site because
 * [`.claude/rules/native-platform.md`](../../../../.claude/rules/native-platform.md) says so —
 * *"concentrate platform differences behind adapters, not `if (Platform.OS === 'ios')` scattered
 * through features"* — and the composer is the third caller, which is this repo's own signal to
 * promote. It is a **value** rather than a component: what differs between the two platforms is
 * one prop, and a wrapper would be a second component around a first one that already exists.
 *
 * **It is the only importer of React Native's `Keyboard`** — the one fenced name out of that module
 * beside `Share` — and so **the app's only listener for the keyboard's show and hide** (ADR-0210 §9,
 * [#882](https://github.com/Raketa02/Raketa/issues/882)). The reading is a port, `KeyboardPort`, for
 * the share sheet's reason: the keyboard is the OS's, a suite cannot bring one up, and a shell that
 * stands its bar down while it is up is a shell no suite could see do it. `fakeKeyboard()` in
 * `src/test-support/platform.ts` raises and drops it, and a tree reaches the port through
 * `KeyboardProvider`.
 */

import { Keyboard, Platform } from 'react-native';

import { releaseCardFocus } from './payments';

/** Pass to `KeyboardAvoidingView`'s `behavior`. `undefined` is correct on Android. */
export const KEYBOARD_AVOIDANCE = Platform.OS === 'ios' ? ('padding' as const) : undefined;

/**
 * Whether the window shrinks for the keyboard and grows back when it goes — Android's way. On iOS
 * the keyboard is drawn over the window and a scroll takes it as an inset. Read at the call, not at
 * import, so a suite can ask it as either phone.
 */
export function windowResizesForKeyboard(): boolean {
  return Platform.OS === 'android';
}

/**
 * **Hide the keyboard without sending a native blur to Stripe's card field.** Every sheet closes
 * through this, and a sheet holding the card field is where the crash came from: `Keyboard.dismiss()`
 * blurs whatever React Native records as focused, and on iOS, under the New Architecture, a blur
 * sent to the card field traps when its view is the legacy interop one (#552). So the card field's
 * focus record is released first, and the dismissal then finds nothing of the card's to blur.
 */
export function dismissKeyboard(): void {
  releaseCardFocus();
  Keyboard.dismiss();
}

/**
 * **What the app may ask of the soft keyboard: whether it is up, and to be told when that changes.**
 * The two halves of `useSyncExternalStore`.
 *
 * Screens depend on this interface; `deviceKeyboard` is the one implementation that listens to the
 * OS, and a test substitutes `fakeKeyboard()` from `src/test-support/platform.ts`.
 */
export interface KeyboardPort {
  /**
   * Whether the soft keyboard is up now, **taking room at the window's foot** — docked. A floating
   * or split keyboard is drawn over the window and takes none, so it is not up in this sense.
   */
  readonly isUp: () => boolean;
  /** Be told each time it comes up or goes down. Answers the way to stop being told. */
  readonly follow: (onChange: () => void) => () => void;
}

export const deviceKeyboard: KeyboardPort = {
  // Android reports a floating or split keyboard shown with no height (the review's catch, #882):
  // nothing shrinks for it, so it is read as not up, and no bar goes for it.
  isUp: () => Keyboard.isVisible() && (Keyboard.metrics()?.height ?? 0) > 0,
  follow: (onChange) => {
    // The *did* events, because Android sends no *will* ones. React Native keeps its own record of
    // the keyboard with listeners it adds as the module loads — before any of these — so by the
    // time `onChange` runs, `isVisible` already says the new state (`keyboard.test.ts`).
    const shown = Keyboard.addListener('keyboardDidShow', onChange);
    const hidden = Keyboard.addListener('keyboardDidHide', onChange);
    return () => {
      shown.remove();
      hidden.remove();
    };
  },
};
