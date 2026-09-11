/**
 * **The bubble in a game card's footer** — the second of the card's two doors, and the only one
 * that goes somewhere else ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * *Open the chat* is **one act with one spelling** across this map
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7), so the name comes
 * from `features/conversations` rather than being written again here — the challenge screen, the
 * game screen and this footer all say it, and one constant is what makes *the same words* true by
 * construction.
 *
 * ## The first icon-only button in the app
 *
 * Every other control in this system carries its word on its face. This one carries a glyph and
 * its word is spoken: the card is a dark shell with one wide door that says the next thing to do,
 * and a second worded button beside it would be two sentences competing on one row of a card
 * whose slots have already spent the width. The mock draws a bubble in a dark square, and the
 * design wins — with the name on the control, always, which is Part 13's *never colour alone*
 * read as *never a glyph alone*. Design-system 6.14 is its section.
 *
 * ## The bubble is Feather `message-circle` and never the character
 *
 * 10.2 settled this shape for the bolt — *"the ⚡ is `zap` and never the character"* — and the
 * argument is the font rather than the glyph: Archivo does not ship a speech bubble, and a bare
 * `<Text>` of one requests whatever the platform substitutes, which on both of them is a colour
 * emoji that a `color` style has nothing to apply to. ADR-0135 fixed Feather as the app's one
 * family, so the bubble is `message-circle` from it, hidden from assistive tech because the
 * control carries the name. It borrows `size.tabIcon` for the glyph rather than adding a size step
 * for one control, which is 15.3's rule and the same borrowing 7.10's fit pill already made.
 *
 * ## Its shape is the on-dark button's, at the wide door's height and the touch minimum's width
 *
 * `Button` has no slot for a glyph and giving it one is a design-system change this ticket does
 * not make (`challengeDetailPresentation.ts` recorded the same refusal for the bolt). So this is
 * **6.1 `on-dark`'s own fill** — `onDarkFill` over `night`, `onDarkFillPressed` under the finger,
 * `radius.btn` — at `btnLg`'s height beside the `lg` door, so the two read as one row. **Its width
 * is the touch minimum**: 6.5's instruction is to keep the visual small and grow the target, but
 * horizontal `hitSlop` here is bounded by the door beside it, so the width is spent instead of the
 * slop, and `hit.btn` supplies the vertical half exactly as it does for every button.
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet } from 'react-native';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { theme } from '@/shared/ui';

export interface ChatDoorProps {
  readonly onPress: () => void;
}

export function ChatDoor({ onPress }: ChatDoorProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={OPEN_THE_CHAT}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.door, pressed ? s.pressed : undefined]}
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
