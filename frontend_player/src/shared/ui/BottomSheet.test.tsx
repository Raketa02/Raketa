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

import { fireEvent, render, screen, within } from '@testing-library/react-native';
import {
  Keyboard,
  KeyboardAvoidingView,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type ViewStyle,
} from 'react-native';

import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform/keyboard';

import { BottomSheet, SHEET_LIST } from './BottomSheet';
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

describe('a sheet whose body is a list that scrolls itself', () => {
  it('draws no scroll around it, and hands it the cap’s shrink and the bottom padding', () => {
    render(
      <BottomSheet visible onClose={() => {}} title="Find a court" closeLabel="Close" scrollsItself>
        <Text>A long list</Text>
      </BottomSheet>,
    );

    expect(screen.getByText('A long list')).toBeTruthy();
    expect(screen.UNSAFE_queryByType(ScrollView)).toBeNull();
    expect(flatten(SHEET_LIST.style)?.flexShrink).toBe(1);
    expect(flatten(SHEET_LIST.contentContainerStyle)?.paddingBottom).toBe(theme.space.xxl);
  });
});

describe('a sheet with a field in it', () => {
  it('lifts above the keyboard on iOS, and is left to the window on Android', () => {
    open(<Text>Card</Text>);

    expect(screen.UNSAFE_getByType(KeyboardAvoidingView).props.behavior).toBe(KEYBOARD_AVOIDANCE);
  });

  it('dismisses the keyboard before it closes, so no field keeps focus into a closing window', () => {
    const order: string[] = [];
    jest.spyOn(Keyboard, 'dismiss').mockImplementation(() => order.push('dismiss'));
    render(
      <BottomSheet
        visible
        onClose={() => order.push('close')}
        title="Keep these times?"
        closeLabel="Close the sheet"
      >
        <Text>Card</Text>
      </BottomSheet>,
    );

    fireEvent.press(screen.getByRole('button', { name: 'Close the sheet' }));

    expect(order).toEqual(['dismiss', 'close']);
    jest.restoreAllMocks();
  });
});

describe('a sheet with the card field in it', () => {
  it('lets a tap outside a field take the keyboard, by default', () => {
    open(<Text>Keep these times?</Text>);

    expect(body().props.keyboardShouldPersistTaps).toBe('handled');
  });

  it('keeps the keyboard on every tap when asked, so nothing blurs the card field natively', () => {
    render(
      <BottomSheet
        visible
        onClose={() => undefined}
        title="Before your first yes"
        closeLabel="Close"
        keepsKeyboardOnTap
      >
        <Text>Card details</Text>
      </BottomSheet>,
    );

    // `handled` blurs the focused field when a tap lands on the sheet's text or blank space — on
    // iOS a native blur of Stripe's card field closes the app.
    expect(body().props.keyboardShouldPersistTaps).toBe('always');
  });
});

describe('a sheet with an act on its title row', () => {
  // The group sheet's one button (#800, home rows 6): the title, the act, then the close.
  it('draws the act on the head, out of the scroll', () => {
    render(
      <BottomSheet
        visible
        onClose={() => undefined}
        title="Ogrody 33 Club"
        closeLabel="Close Ogrody 33 Club"
        action={<Text>Asked</Text>}
      >
        <Text>The group</Text>
      </BottomSheet>,
    );

    // On the sheet, and out of the scroll: it stays with the title it acts on.
    expect(within(screen.getByTestId('bottom-sheet')).getByText('Asked')).toBeTruthy();
    expect(within(body()).queryByText('Asked')).toBeNull();
  });
});
