/**
 * The one thing about the sheet that no other suite can see: **its body scrolls, so the
 * 88 % cap bounds it rather than cutting it off.**
 *
 * Asserted against the drawing, which is the declared exception `ConfidenceRing.test.tsx`
 * makes and for the same reason. Every control inside a sheet is *rendered* whatever the
 * content height — a query finds them all, and `promptSheet.test.tsx` presses them happily —
 * so a screen-level suite cannot tell a sheet whose last button is on the screen from one
 * whose last button is below the bottom edge of it. That is exactly how the answer controls
 * on `SH.saveav` went missing under a grid that had grown by 32pt: nothing failed, and the
 * buttons were not there.
 *
 * Two facts carry it, and both are structural: the children are inside a `ScrollView`, and
 * that `ScrollView` **shrinks**. Without the second the cap applies one level up, where there
 * is nothing to scroll — which is the version of this that looks right in a diff.
 */

import { render, screen, within } from '@testing-library/react-native';
import { ScrollView, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { BottomSheet } from './BottomSheet';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

function open(children: React.ReactNode) {
  render(
    <BottomSheet visible onClose={() => undefined} title="Keep these times?" closeLabel="Close">
      {children}
    </BottomSheet>,
  );
}

const body = () => screen.UNSAFE_getByType(ScrollView);

describe('a sheet taller than the screen', () => {
  it('scrolls its children rather than pushing the last of them off the bottom', () => {
    open(
      <View>
        <Text>A very tall grid</Text>
      </View>,
    );

    expect(screen.getByText('A very tall grid')).toBeTruthy();
    // `flexShrink` is the whole assertion: a ScrollView that cannot shrink takes its
    // content's full height, and the overflow moves up to the sheet, which does not scroll.
    expect(flatten(body().props.style)?.flexShrink).toBe(1);
  });

  it('keeps the grab, the title and the close control out of the scroll', () => {
    // The head is what a player reaches for to dismiss, and a title that scrolled away
    // would take the close control with it.
    open(<Text>Body</Text>);

    expect(within(body()).getByText('Body')).toBeTruthy();
    expect(within(body()).queryByRole('header')).toBeNull();
    // ...and the heading is on the sheet itself, not merely absent everywhere.
    expect(screen.getByRole('header')).toBeTruthy();
  });

  it('carries the sheet’s bottom padding on the scrolled content, not under it', () => {
    // Padding below the scroll is padding the last control never gets: at full scroll it
    // would sit against the edge of the screen.
    open(<Text>Body</Text>);

    expect(flatten(body().props.contentContainerStyle)?.paddingBottom).toBe(theme.space.xxl);
    expect(flatten(screen.UNSAFE_getByType(ScrollView).props.style)?.paddingBottom).toBeUndefined();
  });
});
