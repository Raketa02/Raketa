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

import { Platform } from 'react-native';

/** Pass to `KeyboardAvoidingView`'s `behavior`. `undefined` is correct on Android. */
export const KEYBOARD_AVOIDANCE = Platform.OS === 'ios' ? ('padding' as const) : undefined;
