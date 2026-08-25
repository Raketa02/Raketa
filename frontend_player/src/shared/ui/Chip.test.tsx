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
import { Pressable, StyleSheet, type ViewStyle } from 'react-native';

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
