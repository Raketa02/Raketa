/**
 * **How a screen gets out of the keyboard's way**, in one place.
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
 */

import { Keyboard, Platform } from 'react-native';

import { releaseCardFocus } from './payments';

/** Pass to `KeyboardAvoidingView`'s `behavior`. `undefined` is correct on Android. */
export const KEYBOARD_AVOIDANCE = Platform.OS === 'ios' ? ('padding' as const) : undefined;

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
