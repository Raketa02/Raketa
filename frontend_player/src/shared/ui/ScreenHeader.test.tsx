/**
 * The one **control** in 10.3's header, and the two things the amendment fixed about it.
 *
 * Both are asserted against the **drawing**, which is the declared exception: a chevron in
 * `muted` and one in `ink` are the same control to every query a screen can run, and a mark
 * centred by its 24pt line box and one centred by its own 19pt glyph are the same element at
 * two different heights. Neither difference is reachable any other way, and the design system
 * now states both.
 *
 * What the rest of the header does — which line survives, and which of them is announced — is
 * asserted where a player meets it, on the screens that draw one.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, type TextStyle } from 'react-native';

import { ScreenHeader } from './ScreenHeader';
import { theme } from './theme';

const noop = () => {};

/** The mark's own style, found by the glyph rather than by position in the tree. */
function chevron() {
  render(<ScreenHeader title="Your line-up" onBack={noop} />);
  return StyleSheet.flatten(screen.getByText('‹').props.style as TextStyle);
}

describe('the back chevron', () => {
  it('is ink, because it is the one thing in the header that is pressed', () => {
    // It was `muted` — the eyebrow's own colour — which left the control quieter than the
    // text beside it. Nothing else moved: same role, same weight, same target.
    expect(chevron()?.color).toBe(theme.color.ink);
    expect(chevron()?.fontSize).toBe(theme.type.h1.fontSize);
  });

  it('takes a line box the size of the mark, so the row centres the glyph and not a gap', () => {
    // Part 4's rule for a drawn figure, read against a drawn mark. h1's own 24pt line around a
    // 19pt chevron is 5pt of nothing that the header's `alignItems: 'center'` centres instead.
    expect(chevron()?.lineHeight).toBe(theme.type.h1.fontSize);
  });

  it('is drawn only where a screen says it has somewhere to go', () => {
    // 10.3's opt-in, which is the reason the header does not point at whatever the router
    // happened to be holding.
    render(<ScreenHeader title="Your line-up" />);

    expect(screen.queryByText('‹')).toBeNull();
  });
});

describe('what the header announces', () => {
  it('names the screen with its title and never with the eyebrow above it', () => {
    render(<ScreenHeader title="Pick players" eyebrow="Padel · doubles · for fun" />);

    expect(screen.getByRole('header', { name: 'Pick players' })).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'Padel · doubles · for fun' })).toBeNull();
  });

  it('names the back control by where it goes, where the screen says so', () => {
    render(<ScreenHeader title="Your court" onBack={noop} backLabel="Back to Find a game" />);

    expect(screen.getByLabelText('Back to Find a game')).toBeTruthy();
  });
});
