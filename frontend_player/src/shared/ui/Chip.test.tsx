/**
 * The chip, asserted through what a player and a screen reader can observe.
 *
 * Unlike the ring and the navigator, a chip is not a drawing with no name — it is a button
 * carrying a label and a state, so what a press reports and what the selection announces
 * are both reachable by role, and that is where the first two suites stay.
 *
 * **The third suite is the declared exception, and it is the same one the ring and the
 * navigator declare.** A finger meets the reachable area, the pressed dimming and the
 * ink fill; a query meets none of them. They are the three rules a chip is most likely to
 * lose silently — the visual is 27pt against a 44pt minimum, touch has no hover to fall
 * back on, and coral is one careless token away.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { ActivityIndicator, Pressable, StyleSheet, View, type ViewStyle } from 'react-native';

import { Chip } from './Chip';
import { theme } from './theme';

/**
 * The chip as React Native would draw it, at rest or under a finger.
 *
 * `Pressable` resolves its style callback before the host View ever sees it, so the
 * pressed appearance is reachable only from the callback — firing `pressIn` at the host
 * leaves the drawing untouched, which is exactly what would make this assertion pass
 * while proving nothing.
 */
function drawn(pressed: boolean): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getByType(Pressable).props.style({ pressed }));
}

describe('what a chip reports', () => {
  it('reports a press', () => {
    const onPress = jest.fn();
    render(<Chip label="After the match" onPress={onPress} />);

    fireEvent.press(screen.getByRole('button', { name: 'After the match' }));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('reports a press when it is already selected — it toggles nothing itself', () => {
    // Selection belongs to whoever counts it: at the tags step's ceiling of six a seventh
    // press has to arrive to be refused out loud, and a chip that swallowed the press of
    // a selected chip would take away removing one as well.
    const onPress = jest.fn();
    render(<Chip label="Doubles" selected onPress={onPress} />);

    fireEvent.press(screen.getByRole('button', { name: 'Doubles' }));

    expect(onPress).toHaveBeenCalledTimes(1);
  });
});

describe('what a chip announces', () => {
  it('announces the selected state, and not only the fill', () => {
    render(<Chip label="Competitive" selected onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Competitive', selected: true })).toBeTruthy();
  });

  it('announces unselected as a state rather than as silence', () => {
    // `selected: false` is not the same fact as no `selected` at all. The first announces
    // "not selected"; the second announces nothing, and leaves whoever cannot see the
    // fill unable to tell a chosen tag from an unchosen one.
    render(<Chip label="Competitive" onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Competitive', selected: false })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Competitive', selected: true })).toBeNull();
  });

  it('takes a name of its own when the label alone is cryptic out of context', () => {
    render(
      <Chip label="Social" accessibilityLabel="Social — why you are here" onPress={jest.fn()} />,
    );

    expect(screen.getByRole('button', { name: 'Social — why you are here' })).toBeTruthy();
  });
});

/**
 * **Busy is 6.1's busy, whole** — the label swapped, the press blocked, and since 2026-11-21 a
 * spinner before the word at the chip's full strength (6.1 and 6.2, amended;
 * `docs/specs/busy-indicator/decisions.md` §3.6). The dim is disabled's alone: the two mean
 * opposite things, and they are no longer one drawing.
 */
describe('a chip with a press on its way', () => {
  it('draws and announces the busy word rather than the value', () => {
    render(<Chip label="Saturday" busy busyLabel="Saving…" onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Saving…' })).toBeTruthy();
    expect(screen.queryByText('Saturday')).toBeNull();
  });

  it('takes no press, so one write cannot become two', () => {
    const pressed = jest.fn();
    render(<Chip label="Saturday" busy busyLabel="Saving…" onPress={pressed} />);

    fireEvent.press(screen.getByRole('button', { name: 'Saving…' }));

    expect(pressed).not.toHaveBeenCalled();
  });

  /** The spinner is the sighted half of the same fact, never the whole of it (Part 13). */
  it('is announced as busy, drawn whole rather than dimmed, and drops the pressed appearance', () => {
    render(<Chip label="Saturday" busy busyLabel="Saving…" onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Saving…' }).props.accessibilityState.busy).toBe(
      true,
    );
    expect(drawn(false).opacity).toBeUndefined();
    expect(drawn(true).opacity).toBeUndefined();

    screen.unmount();

    render(<Chip label="Saturday" disabled onPress={jest.fn()} />);
    expect(drawn(false).opacity).toBe(0.4);
  });

  it('turns a spinner before the busy word, in the label’s ink, unspoken', () => {
    render(<Chip label="Saturday" busy busyLabel="Saving…" onPress={jest.fn()} />);

    const spinner = screen.UNSAFE_getByType(ActivityIndicator);
    expect(spinner.props.color).toBe(theme.color.ink);
    expect(spinner.props.accessibilityElementsHidden).toBe(true);
    expect(spinner.parent?.children[0]).toBe(spinner);

    screen.unmount();

    render(<Chip label="Saturday" selected busy busyLabel="Saving…" onPress={jest.fn()} />);
    expect(screen.UNSAFE_getByType(ActivityIndicator).props.color).toBe(theme.color.surface);
  });

  /** The sport's dot and the count describe the value the busy word has replaced. */
  it('sets the dot and the count aside while the word is the busy one', () => {
    render(
      <Chip
        label="Padel"
        dot={theme.color.ink}
        count={10}
        busy
        busyLabel="Starting…"
        onPress={jest.fn()}
      />,
    );

    expect(screen.queryByText('10')).toBeNull();
    const sportDots = screen
      .UNSAFE_queryAllByType(View)
      .filter((node) => StyleSheet.flatten(node.props.style)?.width === theme.size.sportDot);
    expect(sportDots).toHaveLength(0);
  });

  it('draws no spinner on a chip with nothing on its way, nor on a refused one', () => {
    render(<Chip label="Saturday" onPress={jest.fn()} />);
    expect(screen.UNSAFE_queryByType(ActivityIndicator)).toBeNull();

    screen.unmount();

    render(<Chip label="Saturday" disabled onPress={jest.fn()} />);
    expect(screen.UNSAFE_queryByType(ActivityIndicator)).toBeNull();
  });

  it('leaves an ordinary chip saying nothing about being busy', () => {
    render(<Chip label="Saturday" onPress={jest.fn()} />);

    expect(screen.getByRole('button', { name: 'Saturday' }).props.accessibilityState.busy).toBe(
      false,
    );
  });
});

describe('what a finger meets', () => {
  it('reaches the 44pt minimum although the chip is drawn at 27', () => {
    render(<Chip label="Doubles" onPress={jest.fn()} />);

    // Both halves are read from what was rendered, never from the token the component was
    // meant to use: a target asserted out of `theme.size.chip` stays green when the chip
    // stops being 27 tall, which is the only way this one ever goes wrong.
    const height = Number(drawn(false).minHeight);
    const slop = screen.getByRole('button', { name: 'Doubles' }).props.hitSlop;

    expect(height).toBe(theme.size.chip);
    expect(height + slop.top + slop.bottom).toBeGreaterThanOrEqual(theme.size.minTouch);
  });

  it('dims under the finger, because there is no hover to fall back on', () => {
    render(<Chip label="Doubles" onPress={jest.fn()} />);

    expect(drawn(false).opacity).toBeUndefined();
    expect(drawn(true).opacity).toBe(0.7);
  });

  it('fills a selected chip with ink and never with the accent', () => {
    // Coral is the action colour and a selected filter is a state (6.2). The two are one
    // token apart, and swapping them is the kind of change that reads fine in a diff.
    render(<Chip label="Doubles" selected onPress={jest.fn()} />);

    expect(drawn(false).backgroundColor).toBe(theme.color.ink);
    expect(drawn(false).backgroundColor).not.toBe(theme.color.coral);
  });
});

/**
 * The sport dot — 6.4's square, on 6.2's pill.
 *
 * Asserted against the drawing for the reason the fill is: a decorative square has no role,
 * no name and no text, and *it is hidden from assistive technology* is a claim only its
 * props can carry. That half is the condition [2.3](../../../docs/design-system.md) attaches
 * to drawing a sport hue at all — the label beside it always says which sport — so a dot
 * that announced itself would be the same fact spoken twice.
 */
describe('the sport dot', () => {
  const dots = () =>
    screen
      .UNSAFE_queryAllByType(View)
      .filter((node) => StyleSheet.flatten(node.props.style)?.width === theme.size.sportDot);

  it('is not drawn at all unless a colour is given', () => {
    render(<Chip label="Padel" onPress={jest.fn()} />);

    expect(dots()).toHaveLength(0);
  });

  it('draws one square in the colour it was handed, and hides it from a reader', () => {
    render(<Chip label="Padel" dot={theme.sport.padel} onPress={jest.fn()} />);

    const [dot] = dots();
    expect(dots()).toHaveLength(1);
    expect(StyleSheet.flatten(dot?.props.style)).toEqual(
      expect.objectContaining({
        width: theme.size.sportDot,
        height: theme.size.sportDot,
        backgroundColor: theme.sport.padel,
      }),
    );
    expect(dot?.props.accessibilityElementsHidden).toBe(true);

    // And the name is still the label alone: the dot adds nothing to what is announced.
    expect(screen.getByRole('button', { name: 'Padel' })).toBeTruthy();
  });

  it('keeps its hue when the pill inverts — a sport is an identity, not a state', () => {
    render(<Chip label="Padel" dot={theme.sport.padel} selected onPress={jest.fn()} />);

    expect(StyleSheet.flatten(dots()[0]?.props.style)?.backgroundColor).toBe(theme.sport.padel);
    expect(drawn(false).backgroundColor).toBe(theme.color.ink);
  });
});
