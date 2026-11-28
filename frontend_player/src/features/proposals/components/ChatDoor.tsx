/**
 * **The bubble in a Home card's footer** — the card's second door, straight into the game's room
 * (Q100; [#619](https://github.com/Rakieta02/Rakieta/issues/619)). It is Classic play's bubble
 * (`plans`' `ChatDoor`, #413), removed with that loop in #576 and drawn again here on the same
 * shape, design system 6.14.
 *
 * *Open the chat* is **one act with one spelling** — the details' *Chat* says it too — so the name
 * comes from `features/conversations` (`OPEN_THE_CHAT`) rather than being written again here.
 *
 * ## The app's icon-only button
 *
 * Every other control in this system carries its word on its face. This one carries a glyph and
 * its word is spoken: the card is a dark shell with one wide door, *Open game*, and a second worded
 * button beside it would be two sentences competing on one row. The mock draws a bubble in a dark
 * square, and the design wins — with the name on the control, always, which is Part 13's *never
 * colour alone* read as *never a glyph alone*.
 *
 * **The bubble is Feather `message-circle` and never the character**: Archivo ships no speech
 * bubble, and a bare glyph requests whatever the platform substitutes, a colour emoji a `color`
 * style has nothing to apply to (10.2's argument for the bolt; ADR-0135). It is hidden from
 * assistive tech because the control carries the name, and borrows `size.tabIcon` rather than
 * adding a size step for one control (15.3).
 *
 * ## Its shape is the on-dark button's, at the wide door's height and the touch minimum's width
 *
 * `Button` has no slot for a glyph, and giving it one is a design-system change. So this is **6.1
 * `on-dark`'s own fill** — `onDarkFill` over `night`, `onDarkFillPressed` under the finger,
 * `radius.btn` — at `btnLg`'s height beside the `lg` door, so the two read as one row. **Its width
 * is the touch minimum**: horizontal `hitSlop` here is bounded by the door beside it, so the width
 * is spent instead of the slop, and `hit.btn` supplies the vertical half as it does for every
 * button.
 *
 * **No count and no lit state yet**: both come with the unread count owed to the details' *Chat ·
 * n* (F-HOME-21.1), and the bubble then shows the same number.
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet } from 'react-native';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { theme } from '@/shared/ui';

export interface ChatDoorProps {
  readonly onPress: () => void;
  readonly testID?: string;
}

export function ChatDoor({ onPress, testID }: ChatDoorProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={OPEN_THE_CHAT}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.door, pressed ? s.pressed : undefined]}
      {...(testID === undefined ? {} : { testID })}
    >
      <Feather
        name="message-circle"
        size={theme.size.tabIcon}
        color={theme.color.surface}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  door: {
    minWidth: theme.size.minTouch,
    minHeight: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.onDarkFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1 `on-dark`'s pressed fill, because that is the shape this control borrows.
  pressed: { backgroundColor: theme.color.onDarkFillPressed },
});
