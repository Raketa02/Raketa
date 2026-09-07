/**
 * The segmented control — the two things about it a screen cannot observe for itself.
 *
 * The words are the caller's and the routing is the caller's, so what is asserted here is the
 * **contract**: that the state is announced on every segment rather than only on the chosen
 * one, and that a press on the segment already selected is still reported. The second is not
 * a detail — Play's *Find a game* segment **re-enters the tab**, which is arriving rather
 * than doing nothing, and a control that swallowed that press would make the rule
 * unimplementable from outside.
 */

import { render, screen, userEvent } from '@testing-library/react-native';
import { StyleSheet, Text, type TextStyle, type ViewStyle } from 'react-native';

import { Segment } from './Segment';
import { theme } from './theme';

const OPTIONS = [
  { key: 'find', label: 'Find a game' },
  { key: 'match', label: 'Match me · 3' },
] as const;

function renderSegment(selected: 'find' | 'match', onSelect = jest.fn()) {
  render(<Segment options={OPTIONS} selected={selected} onSelect={onSelect} />);
  return onSelect;
}

const isSelected = (label: string) =>
  screen.getByLabelText(label).props.accessibilityState?.selected === true;

describe('what it announces', () => {
  it('states the selection on every segment, not only on the chosen one', () => {
    renderSegment('match');

    expect(isSelected('Match me · 3')).toBe(true);
    // Present and false, never absent: *not chosen* and *not a choice* are different facts.
    expect(screen.getByLabelText('Find a game').props.accessibilityState?.selected).toBe(false);
  });

  it('is a button carrying `selected`, and never a switch carrying `checked`', () => {
    renderSegment('find');

    const segment = screen.getByLabelText('Find a game');
    expect(segment.props.accessibilityRole).toBe('button');
    expect(segment.props.accessibilityState?.checked).toBeUndefined();
  });

  it('takes an accessible name of its own where the visible words are cryptic', () => {
    render(
      <Segment
        options={[
          { key: 'find', label: 'Find a game' },
          { key: 'match', label: 'Match me · 3', accessibilityLabel: 'Match me, 3 yeses waiting' },
        ]}
        selected="find"
        onSelect={() => undefined}
      />,
    );

    expect(screen.getByLabelText('Match me, 3 yeses waiting')).toBeTruthy();
  });
});

describe('what it reports', () => {
  it('reports a press on the segment that is already selected', async () => {
    const onSelect = renderSegment('find');

    await userEvent.press(screen.getByLabelText('Find a game'));

    expect(onSelect).toHaveBeenCalledWith('find');
  });

  it('reports the key rather than the label', async () => {
    const onSelect = renderSegment('find');

    await userEvent.press(screen.getByLabelText('Match me · 3'));

    expect(onSelect).toHaveBeenCalledWith('match');
  });
});

describe('the drawing', () => {
  /**
   * 6.3's inversion, and Part 13's *never colour alone* under it: the raised segment is a
   * **lightness** step on the surface and a matching one on the label, so the pairing that
   * carries the state is legible without hue — and `selected` states it besides.
   */
  it('raises the selected segment onto the surface and darkens its label', () => {
    renderSegment('match');

    expect(styleOf(screen.getByLabelText('Match me \u00b7 3'))).toMatchObject({
      backgroundColor: theme.color.surface,
    });
    expect(styleOf(screen.getByLabelText('Find a game')).backgroundColor).toBeUndefined();

    expect(labelStyle('Match me \u00b7 3')).toMatchObject({ color: theme.color.ink });
    expect(labelStyle('Find a game')).toMatchObject({ color: theme.color.muted });
  });

  it("reaches the touch minimum through 6.5's own slop", () => {
    renderSegment('find');

    expect(screen.getByLabelText('Find a game').props.hitSlop).toBe(theme.hit.seg);
  });
});

/** The style a `Pressable`'s style function produces with nothing pressed. */
function styleOf(node: { readonly props: { readonly style?: unknown } }): ViewStyle {
  const style = node.props.style;
  const resolved = typeof style === 'function' ? style({ pressed: false }) : style;
  return StyleSheet.flatten(resolved as ViewStyle);
}

/** The one `Text` inside a segment, flattened. */
function labelStyle(label: string): TextStyle {
  const [text] = screen.getByLabelText(label).findAllByType(Text);
  return StyleSheet.flatten(text?.props.style as TextStyle);
}
