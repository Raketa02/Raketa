/**
 * **The ✉ in a game card's footer** — the second of the card's two actions, and the only one that
 * goes somewhere else.
 *
 * *Open the chat* is **one act with one spelling** across this map
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7), so the name comes
 * from `features/conversations` rather than being written again here — the challenge screen, the
 * game screen and this footer all say it, and one constant is what makes *the same words* true by
 * construction.
 *
 * ## The ✉ is Feather `mail` and never the character
 *
 * 10.2 settled this shape for the bolt — *"the ⚡ is `zap` and never the character"* — and the
 * argument is the font rather than the glyph: Archivo does not ship U+2709, and a bare `<Text>` of
 * it requests whatever the platform substitutes, which on both of them is a colour emoji that a
 * `color` style has nothing to apply to. ADR-0135 fixed Feather as the app's one family, so the
 * envelope is `mail` from it, hidden from assistive tech because the control carries the name.
 *
 * `Button` has no slot for a glyph and giving it one is a design-system change this ticket does
 * not make (`challengeDetailPresentation.ts` recorded the same refusal for the bolt). So this is
 * **6.1 `secondary`'s own shape** — `surface`, a 1pt `line` border, `radius.btn` — at `btnSm`'s
 * height beside the named door, with `line2` under the finger. It borrows `size.tabIcon` for the
 * glyph box rather than adding a size step for one control, which is 15.3's rule and the same
 * borrowing 7.10's fit pill already made.
 *
 * **Its width is the touch minimum rather than its height**: a 44pt square beside a 32pt door
 * would be the taller control, and 6.5's instruction is to keep the visual small and grow the
 * target — but horizontal `hitSlop` here is bounded by the door beside it, so the width is spent
 * instead of the slop.
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
        name="mail"
        size={theme.size.tabIcon}
        color={theme.color.ink}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  door: {
    minWidth: theme.size.minTouch,
    minHeight: theme.size.btnSm,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1 `secondary`'s pressed fill, because that is the shape this control borrows.
  pressed: { backgroundColor: theme.color.line2 },
});
