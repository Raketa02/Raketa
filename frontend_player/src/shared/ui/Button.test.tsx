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
 *
 * Beside it, the two things `on-dark` and `gloss` add that are **not** a table lookup: that a
 * glossed button draws a second line and keeps announcing **one** name, and that the second
 * line takes 5.2's repaint rather than the label's own white. A gloss read out after the name
 * the caller gave would say the same thing twice, and a `tiny` at full white on `night` is the
 * repaint quietly not happening — neither shows up in a diff as anything but a style array.
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

/**
 * **`arranging` is volt's shape a second time**, and the same two rules are the ones a diff would
 * not show: `ink` and never white on it (7,05:1 against 2,48:1), and a press that dims rather
 * than a darker companion invented for it ([#429](https://github.com/Raketa02/Raketa/issues/429)
 * F1: the Now card's *Fill the seat* is drawn in the stage dot's own colour).
 */
describe('the arranging button (6.1)', () => {
  it('fills with the arranging colour and labels in ink, never in white', () => {
    render(<Button label="Fill the seat" variant="arranging" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.arranging);
    expect(label().color).toBe(theme.color.ink);
    expect(label().color).not.toBe(theme.color.surface);
  });

  it('dims under the finger rather than taking a second fill', () => {
    render(<Button label="Fill the seat" variant="arranging" onPress={jest.fn()} />);

    expect(drawn(false).opacity).toBeUndefined();
    expect(drawn(true).opacity).toBe(0.7);
    expect(drawn(true).backgroundColor).toBe(theme.color.arranging);
  });
});

describe('the on-dark button (6.1)', () => {
  it('takes the two tokens the theme names the on-dark button', () => {
    render(<Button label="Competitive" variant="onDark" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.onDarkFill);
    expect(drawn(true).backgroundColor).toBe(theme.color.onDarkFillPressed);
    expect(label().color).toBe(theme.color.surface);
  });
});

describe('the gloss', () => {
  const GLOSS = 'You are here for an even, serious game.';

  it('draws a second line under the label, in 5.2’s repaint and not the label’s white', () => {
    render(<Button label="Competitive" gloss={GLOSS} variant="onDark" onPress={jest.fn()} />);

    const lines = screen.UNSAFE_getAllByType(Text);
    expect(lines).toHaveLength(2);
    expect(screen.getByText(GLOSS)).toBeTruthy();

    const gloss = StyleSheet.flatten(lines[1]?.props.style as TextStyle);
    expect(gloss.color).toBe(theme.color.onDarkTiny);
    expect(gloss.color).not.toBe(theme.color.surface);
    // The hierarchy is the type role rather than a second opacity nobody has computed.
    expect(gloss.fontSize).toBe(theme.type.tiny.fontSize);
  });

  /** One element, one action, one name — and the gloss is the sighted half of that name. */
  it('is not read out beside the name the caller gave', () => {
    render(
      <Button
        label="Competitive"
        gloss={GLOSS}
        variant="onDark"
        accessibilityLabel="Competitive, your usual at Padel"
        onPress={jest.fn()}
      />,
    );

    expect(screen.getByLabelText('Competitive, your usual at Padel')).toBeTruthy();
    expect(screen.queryByLabelText(GLOSS)).toBeNull();
  });

  /** Two lines of different lengths centred on their own widths read as a caption, not a row. */
  it('reads from the start, where a one-line button stays centred', () => {
    render(<Button label="Competitive" gloss={GLOSS} variant="onDark" onPress={jest.fn()} />);
    expect(drawn(false).alignItems).toBe('stretch');

    screen.unmount();

    render(<Button label="Competitive" variant="onDark" onPress={jest.fn()} />);
    expect(drawn(false).alignItems).toBe('center');
  });
});

/**
 * **The pill is the chip's alone, and this is the one exception** — the yes screen's two doors
 * ([ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2, Part 16 2026-09-14). A shape option on the one primitive rather than a second one, so
 * the pill differs from every other button by its corner and by nothing else.
 */
describe('the pill shape (6.1, amended)', () => {
  it('is 4.2’s 10pt corner unless asked for, and the chip’s pill when it is', () => {
    render(<Button label="Later" variant="onDark" onPress={jest.fn()} />);
    expect(drawn(false).borderRadius).toBe(theme.radius.btn);

    screen.unmount();

    render(<Button label="Later" variant="onDark" shape="pill" onPress={jest.fn()} />);
    expect(drawn(false).borderRadius).toBe(theme.radius.pill);
  });

  it('changes the corner and nothing else about the variant', () => {
    render(<Button label="Open the chat" variant="volt" shape="pill" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.volt);
    expect(label().color).toBe(theme.color.ink);
    expect(drawn(true).opacity).toBe(0.7);
  });
});
