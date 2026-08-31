/**
 * The `volt` variant, which is the one button that does not have the shape of the other four.
 *
 * `primary`, `dark`, `secondary` and `settled` are all *fill, white-or-ink label, a second
 * fill under the finger*. Volt breaks the pattern twice, and #219 B1 argues both: its label
 * is `ink` because white on volt is unreadable and `ink` on it is 13.96:1, and its press is
 * `opacity: .7` because volt is already the brightest value in the palette and has no darker
 * companion — inventing a seventh hex to satisfy *the variant's pressed fill* would be adding
 * a colour to describe a press.
 *
 * **Deliberately scoped to that variant.** The other four are the same three lines each with
 * different tokens, and a sweep asserting a lookup table against itself cannot fail. These
 * two rules can: both are one plausible-looking token away, and neither is visible in a diff
 * as anything but a colour.
 */

import { render, screen } from '@testing-library/react-native';
import { Pressable, StyleSheet, Text, type TextStyle, type ViewStyle } from 'react-native';

import { Button } from './Button';
import { theme } from './theme';

/** The button as React Native would draw it — see `Chip.test.tsx` for why the callback. */
function drawn(pressed: boolean): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getByType(Pressable).props.style({ pressed }));
}

function label(): TextStyle {
  return StyleSheet.flatten(screen.UNSAFE_getByType(Text).props.style);
}

describe('the volt button (6.1)', () => {
  it('fills with volt and labels in ink, never in white', () => {
    render(<Button label="Even it out" variant="volt" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.volt);
    expect(label().color).toBe(theme.color.ink);
    expect(label().color).not.toBe(theme.color.surface);
  });

  it('dims under the finger rather than taking a second fill', () => {
    render(<Button label="Even it out" variant="volt" onPress={jest.fn()} />);

    expect(drawn(false).opacity).toBeUndefined();
    expect(drawn(true).opacity).toBe(0.7);
    expect(drawn(true).backgroundColor).toBe(theme.color.volt);
  });
});
