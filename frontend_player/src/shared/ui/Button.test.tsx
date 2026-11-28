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
 *
 * And the two things `settled` does that the other fills do not (6.1, amended 2026-09-18): it
 * is drawn whole when it is shut, and its arrival fades the fill it came from — once, never on
 * the way back, and not at all under reduced motion.
 */

import Feather from '@expo/vector-icons/Feather';
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { Button } from './Button';
import { ReducedMotionProvider } from './overlay';
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
 * than a darker companion invented for it ([#429](https://github.com/Rakieta02/Rakieta/issues/429)
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

/**
 * **`waiting` is a request waiting on somebody else** — the group sheet's *Asked* (#800, home rows
 * 6): amber's soft bed and its ink, the warn tag's two colours, as a control. Amber on `amberSoft`
 * is 5,06:1, and it presses into `amberLine`, its own fold, rather than a hex invented for a press.
 */
describe('the waiting button (6.1)', () => {
  it('fills with amber’s soft bed and labels in amber', () => {
    render(<Button label="Asked" variant="waiting" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.amberSoft);
    expect(label().color).toBe(theme.color.amber);
  });

  it('presses into amber’s line', () => {
    render(<Button label="Asked" variant="waiting" onPress={jest.fn()} />);

    expect(drawn(true).backgroundColor).toBe(theme.color.amberLine);
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

/**
 * **The settled button is drawn whole when it is shut, and its arrival is the one motion**
 * (6.1, amended 2026-09-18). Both are claims a diff cannot show: the dim is one conditional
 * away from applying to every variant again, and the fade is a layer that would still mount
 * on first paint, or on the way back, or under reduced motion, without anybody noticing in
 * the style table.
 */
describe('the marks after the label (6.1, amended)', () => {
  it('draws a tick and a chevron after the words, in the label’s own ink, and speaks the words alone', () => {
    render(
      <Button label="Friend" variant="secondary" marks={['tick', 'chevron']} onPress={() => {}} />,
    );

    const marks = screen.UNSAFE_getAllByType(Feather);
    expect(marks.map((mark) => mark.props.name)).toEqual(['check', 'chevron-down']);
    for (const mark of marks) expect(mark.props.color).toBe(theme.color.ink);
    expect(screen.getByRole('button', { name: 'Friend' })).toBeTruthy();
  });

  it('draws none unless asked', () => {
    render(<Button label="Add friend" variant="dark" onPress={() => {}} />);
    expect(screen.UNSAFE_queryAllByType(Feather)).toHaveLength(0);
  });
});

/**
 * **A mark before the words, and the soft settled bed** (6.1, amended 2026-11-14, #801): a sheet's
 * worded friend button reads *+ Add friend* and *✓ Friends*, and Archivo ships no ✓ — so the plus
 * and the tick are drawn before the label and never spoken; *✓ Friends* is mint's soft bed with its
 * ink, as home rows 9 draws it.
 */
describe('the mark before the label and settledSoft (6.1, amended)', () => {
  it('draws a plus or a tick before the words, in the label’s own ink, and speaks the words alone', () => {
    render(<Button label="Friends" variant="settledSoft" lead="tick" onPress={() => {}} />);

    const [mark] = screen.UNSAFE_getAllByType(Feather);
    expect(mark?.props.name).toBe('check');
    expect(mark?.props.color).toBe(theme.color.mintInk);
    const button = screen.getByRole('button', { name: 'Friends' });
    expect(StyleSheet.flatten(button.props.style)).toMatchObject({
      backgroundColor: theme.color.mintSoft,
    });
  });

  it('draws the plus for Add friend', () => {
    render(<Button label="Add friend" variant="dark" lead="plus" onPress={() => {}} />);
    expect(screen.UNSAFE_getAllByType(Feather).map((mark) => mark.props.name)).toEqual(['plus']);
  });
});

/**
 * **A button that opens a screen is announced as a link** (6.1, amended 2026-11-08, #784): the
 * sign-in stage's *I have an invitation code* is 6.1 `secondary` in look and a link in what it
 * does — it opens a screen carrying what was typed — and a screen reader meets it among the
 * screen's links. The look is the variant's; only the role changes.
 */
describe('the role (6.1, amended)', () => {
  it('is a button unless the caller says the press opens a screen', () => {
    render(<Button label="Sign in" onPress={() => {}} />);
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeTruthy();
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('is a link when asked, drawn exactly as the variant is', () => {
    render(
      <Button
        label="I have an invitation code"
        variant="secondary"
        role="link"
        onPress={() => {}}
      />,
    );

    expect(screen.getByRole('link', { name: 'I have an invitation code' })).toBeTruthy();
    expect(screen.queryByRole('button')).toBeNull();
    expect(drawn(false).backgroundColor).toBe(theme.color.surface);
    expect(drawn(false).borderColor).toBe(theme.color.line);
    expect(drawn(true).backgroundColor).toBe(theme.color.line2);
  });
});

/**
 * **The coral dot before the label** (6.1 and 1.2, amended 2026-11-08, #784) — the product owner's
 * mark on the stage's invitation button, kept against 1.2's closed list. A drawn mark, never spoken.
 */
/** The sign-in stage's buttons are its boxes' height — 48, measured off mock 3 (6.1, amended). */
describe('the stage’s size (6.1, amended)', () => {
  it('stands as tall as the stage’s text boxes', () => {
    render(<Button label="Sign in" size="stage" onPress={() => {}} />);
    expect(drawn(false).minHeight).toBe(theme.size.stage.control);
  });
});

describe('the dot before the label (6.1, amended)', () => {
  it('draws a coral dot of the smallest mark’s size before the words, and speaks the words alone', () => {
    render(<Button label="I have an invitation code" variant="secondary" dot onPress={() => {}} />);

    const dot = screen.getByTestId('button-dot', { includeHiddenElements: true });
    const style = StyleSheet.flatten(dot.props.style as ViewStyle);
    expect(style.backgroundColor).toBe(theme.color.coral);
    expect(style.width).toBe(theme.size.sportDot);
    expect(screen.getByRole('button', { name: 'I have an invitation code' })).toBeTruthy();
  });

  it('draws none unless asked', () => {
    render(<Button label="Sign in" onPress={() => {}} />);
    expect(screen.queryByTestId('button-dot', { includeHiddenElements: true })).toBeNull();
  });
});

/**
 * **A busy button says it is working: a spinner before its word, at its full fill** (6.1, amended
 * 2026-11-21, `docs/specs/busy-indicator/decisions.md`). The 40% dim drawn over a word that did not
 * move read as a frozen screen, and it was disabled's dim besides — so busy and *you may not* were
 * one drawing told apart only by the word. Every claim here is one conditional away from undoing
 * itself: the dim back on busy, the spinner on a disabled button, a glyph of the idle state left
 * beside the busy word, or the spinner stopped for a reader who asked for less motion.
 */
describe('a busy button (6.1, amended)', () => {
  const spinner = () => screen.UNSAFE_queryByType(ActivityIndicator);

  it('draws a spinner before the busy word, in the label’s own ink', () => {
    render(<Button label="Sign in" busy busyLabel="Signing in…" onPress={jest.fn()} />);

    const drawnSpinner = screen.UNSAFE_getByType(ActivityIndicator);
    expect(drawnSpinner.props.color).toBe(theme.color.surface);
    expect(screen.getByText('Signing in…')).toBeTruthy();
    expect(screen.queryByText('Sign in')).toBeNull();
    // Before the word, in the one row the two share.
    expect(drawnSpinner.parent?.children[0]).toBe(drawnSpinner);

    screen.unmount();

    render(<Button label="Withdraw" variant="secondary" busy busyLabel="…" onPress={jest.fn()} />);
    expect(spinner()?.props.color).toBe(theme.color.ink);
  });

  it('keeps its full fill — the 40% dim is disabled’s alone', () => {
    render(<Button label="Sign in" busy busyLabel="Signing in…" onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.coralInk);
    expect(drawn(false).opacity).toBeUndefined();
    // And no pressed fill either: the press is blocked, so nothing answers the finger.
    expect(drawn(true).backgroundColor).toBe(theme.color.coralInk);

    screen.unmount();

    render(<Button label="Sign in" disabled onPress={jest.fn()} />);
    expect(drawn(false).opacity).toBe(0.4);
    expect(spinner()).toBeNull();
  });

  it('is busy rather than disabled when it is told both', () => {
    render(<Button label="Sign in" disabled busy busyLabel="Signing in…" onPress={jest.fn()} />);

    expect(drawn(false).opacity).toBeUndefined();
    expect(spinner()).not.toBeNull();
  });

  it('takes no press, and is named by its word with the spinner unspoken', () => {
    const pressed = jest.fn();
    render(<Button label="Sign in" busy busyLabel="Signing in…" onPress={pressed} />);

    const button = screen.getByRole('button', { name: 'Signing in…' });
    fireEvent.press(button);
    expect(pressed).not.toHaveBeenCalled();
    expect(button.props.accessibilityState).toMatchObject({ busy: true, disabled: true });
    expect(spinner()?.props.accessibilityElementsHidden).toBe(true);
    expect(spinner()?.props.importantForAccessibility).toBe('no-hide-descendants');
  });

  it('spins under reduced motion too — it is progress, not decoration', () => {
    render(
      <ReducedMotionProvider value>
        <Button label="Sign in" busy busyLabel="Signing in…" onPress={jest.fn()} />
      </ReducedMotionProvider>,
    );

    expect(spinner()).not.toBeNull();
    expect(spinner()?.props.animating).not.toBe(false);
  });

  it('draws no spinner while nothing is on its way', () => {
    render(<Button label="Sign in" onPress={jest.fn()} />);
    expect(spinner()).toBeNull();
  });

  it('spins beside its own label when it has no busy word', () => {
    render(<Button label="Withdraw" variant="secondary" busy onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Withdraw' })).toBeTruthy();
    expect(spinner()).not.toBeNull();
  });

  /** One glyph before the word, never two; and the marks describe the idle state, not the busy one. */
  it('takes the place of the glyph before the label and hides the marks after it', () => {
    render(
      <Button
        label="Add friend"
        variant="dark"
        lead="plus"
        busy
        busyLabel="Asking…"
        onPress={jest.fn()}
      />,
    );
    expect(screen.UNSAFE_queryAllByType(Feather)).toHaveLength(0);
    expect(spinner()).not.toBeNull();

    screen.unmount();

    render(
      <Button
        label="Friend"
        variant="secondary"
        marks={['tick', 'chevron']}
        busy
        busyLabel="Removing…"
        onPress={jest.fn()}
      />,
    );
    expect(screen.UNSAFE_queryAllByType(Feather)).toHaveLength(0);
    expect(screen.getByText('Removing…')).toBeTruthy();
  });

  it('keeps a glossed answer’s second line under the spinning first one', () => {
    render(
      <Button
        label="Competitive"
        gloss="You are here for an even, serious game."
        variant="onDark"
        busy
        onPress={jest.fn()}
      />,
    );

    expect(screen.getByText('You are here for an even, serious game.')).toBeTruthy();
    expect(spinner()?.props.color).toBe(theme.color.surface);
  });
});

describe('the settled button (6.1, amended)', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  /** The fill on its way out, or `undefined` once there is nothing fading. */
  function arrival(): ViewStyle | undefined {
    const layer = screen.queryByTestId('button-arrival');
    return layer === null ? undefined : (StyleSheet.flatten(layer.props.style) as ViewStyle);
  }

  function draw(variant: 'primary' | 'settled', reduced = false) {
    return (
      <ReducedMotionProvider value={reduced}>
        <Button label="Saved" variant={variant} disabled onPress={jest.fn()} />
      </ReducedMotionProvider>
    );
  }

  it('keeps its fill when shut, where every other variant dims to 40%', () => {
    render(<Button label="Saved" variant="settled" disabled onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.mintInk);
    expect(drawn(false).opacity).toBeUndefined();
    expect(screen.getByLabelText('Saved').props.accessibilityState?.disabled).toBe(true);

    screen.unmount();

    render(<Button label="Saved" variant="primary" disabled onPress={jest.fn()} />);
    expect(drawn(false).opacity).toBe(0.4);
  });

  it('fades the fill it arrived from over the mint, once, and then draws the mint alone', () => {
    const view = render(draw('primary'));
    expect(arrival()).toBeUndefined();

    view.rerender(draw('settled'));

    // The first frame of the new state: the mint underneath, the coral whole on top of it.
    expect(drawn(false).backgroundColor).toBe(theme.color.mintInk);
    expect(arrival()?.backgroundColor).toBe(theme.color.coralInk);
    expect(arrival()?.opacity).toBe(1);

    act(() => jest.advanceTimersByTime(theme.motion.fade / 2));
    const half = arrival()?.opacity;
    expect(half).toBeGreaterThan(0);
    expect(half).toBeLessThan(1);

    act(() => jest.advanceTimersByTime(theme.motion.fade));
    expect(arrival()).toBeUndefined();
    expect(drawn(false).backgroundColor).toBe(theme.color.mintInk);
  });

  it('simply is settled on first mount, and on the way back to an action', () => {
    const view = render(draw('settled'));
    expect(arrival()).toBeUndefined();

    view.rerender(draw('primary'));
    expect(arrival()).toBeUndefined();
    expect(drawn(false).backgroundColor).toBe(theme.color.coralInk);
  });

  it('simply is settled under reduced motion', () => {
    const view = render(draw('primary', true));
    view.rerender(draw('settled', true));

    expect(arrival()).toBeUndefined();
    expect(drawn(false).backgroundColor).toBe(theme.color.mintInk);
  });

  it('drops the fade the moment the button goes back to an action', () => {
    const view = render(draw('primary'));
    view.rerender(draw('settled'));
    expect(arrival()).toBeDefined();

    view.rerender(draw('primary'));
    expect(arrival()).toBeUndefined();

    // And the next arrival starts whole again rather than from wherever the last one stopped.
    view.rerender(draw('settled'));
    expect(arrival()?.opacity).toBe(1);
  });
});
