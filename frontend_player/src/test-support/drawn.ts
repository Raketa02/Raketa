/**
 * What a control is drawn with, read off the host element a query returns.
 *
 * **In `test-support/` because four suites read the same fact** — that a *Save* whose work is
 * done is drawn green (6.1 `settled`, amended 2026-09-18) — and a style flattened four ways is
 * four chances to read the wrong element. A `Pressable` hands its host `View` the style it
 * resolved for the unpressed state, so the fill a player sees at rest is one `flatten` away.
 *
 * Read beside the words, never instead of them: every suite that reads a fill here has already
 * found the element by its label, because the green is never the whole fact (Part 13).
 */

import { StyleSheet, type ViewStyle } from 'react-native';

/** A host element as any RNTL query returns it. */
interface Drawn {
  readonly props: { readonly style?: unknown };
}

/** The colour the element is filled with at rest, or `undefined` where it paints none. */
export function fillOf(element: Drawn): string | undefined {
  return StyleSheet.flatten(element.props.style as ViewStyle)?.backgroundColor as
    string | undefined;
}
