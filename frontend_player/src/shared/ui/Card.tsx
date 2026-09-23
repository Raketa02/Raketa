/**
 * The card, per design-system 5.1 — the workhorse surface.
 *
 * Cards never cast a shadow: depth on paper comes from the surface change and the 1pt
 * `line` border. The three shadows in the system are for things that genuinely float.
 *
 * `PressableCard` is the same object with a press state. Pressed is `coral` because
 * coral is the *action* colour; a card that is *selected* takes `ink`, for the same
 * reason a selected chip is ink-filled (6.2) — selection is a state, not an action.
 *
 * **`marked` is the third border, and it is the only one that is not about this control.**
 * Pressed and selected are both things the reader has done to the card; a marked card carries a
 * standing fact about **whoever is drawn on it**, in `voltStroke`
 * ([#310](https://github.com/Raketa02/Raketa/issues/310)). That is why it announces nothing —
 * `accessibilityState` says what a control is, and this is not one of those — and why the press
 * state still wins over it: a finger on a marked card must read as a press, or the one border
 * the reader can act on is the one they cannot see.
 */

import {
  Pressable,
  StyleSheet,
  View,
  type AccessibilityActionEvent,
  type AccessibilityActionInfo,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { forwardRef, type ReactNode } from 'react';

import { theme } from './theme';

export interface CardProps {
  readonly children: ReactNode;
  /**
   * 5.1's pressed border, drawn on a card whose **control is inside it** rather than around it.
   *
   * Now's game card is the one such surface: it carries two actions — the body, which is the
   * whole statement, and the ✉ beside it, which goes somewhere else — so it cannot be a
   * `PressableCard` without swallowing the second into the first's one accessibility element
   * ([#367](https://github.com/Raketa02/Raketa/issues/367)). What it still owes the player is the
   * press *state*, and that is this: the same coral outline `PressableCard` draws, from the same
   * table, so a second surface cannot draw a different one.
   */
  readonly pressed?: boolean;
  readonly style?: StyleProp<ViewStyle>;
}

export function Card({ children, pressed = false, style }: CardProps) {
  return <View style={[s.card, pressed ? s.pressed : undefined, style]}>{children}</View>;
}

export interface PressableCardProps extends CardProps {
  readonly onPress: () => void;
  /** Drawn with the selected border and announced as selected. */
  readonly selected?: boolean;
  /**
   * A standing fact about the card's **subject**, drawn as a `voltStroke` border — never a state
   * of this control, and never the only carrier of the fact.
   *
   * [Part 13](../../../docs/design-system.md#part-13--accessibility): colour is never the only
   * cue, so a caller drawing this border also draws the word. Nothing is announced from here —
   * see the module note.
   */
  readonly marked?: boolean;
  readonly disabled?: boolean;
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
  /**
   * Acts on the card that are not the press — offered in a screen reader's actions rotor.
   *
   * A card in a list is one element and one door, and a second act on it that a sighted player
   * reaches by a **gesture** — a swipe, which assistive technology consumes before the card
   * sees it — has to be reachable by a listener some other way (`the-words.md` §20.12, *never
   * the only path*). This is that way: each action is named, and `onAccessibilityAction` says
   * which one was taken. Absent on every card that is only a door.
   */
  readonly accessibilityActions?: readonly AccessibilityActionInfo[];
  readonly onAccessibilityAction?: (event: AccessibilityActionEvent) => void;
}

/**
 * The ref is forwarded for the same reason `CloseControl`'s is: a card can be the control
 * an overlay returns focus to when it closes — see `BottomSheet`. Nothing else needs it,
 * and nothing about the drawing changes.
 */
export const PressableCard = forwardRef<View, PressableCardProps>(function PressableCard(
  {
    children,
    style,
    onPress,
    selected = false,
    marked = false,
    disabled = false,
    accessibilityLabel,
    accessibilityHint,
    accessibilityActions,
    onAccessibilityAction,
  },
  ref,
) {
  return (
    <Pressable
      ref={ref}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityActions={accessibilityActions}
      onAccessibilityAction={onAccessibilityAction}
      // Selection reaches a screen reader as state. The border is the sighted half of
      // the same fact — never the only half, which is why callers also carry a word.
      accessibilityState={{ selected, disabled }}
      disabled={disabled}
      onPress={onPress}
      // The order is the three borders ranked by how much the reader is doing. `marked` is a
      // standing fact about somebody and goes first; `selected` is a choice the reader has made
      // and outranks it; `pressed` is the finger that is on the card right now and outranks
      // both, or the one border they can cause is the one they cannot see. A caller's own
      // `style` still wins over all three, which is the shape this component already had.
      style={({ pressed }) => [
        s.card,
        marked ? s.marked : undefined,
        selected ? s.selected : undefined,
        pressed && !disabled ? s.pressed : undefined,
        style,
      ]}
    >
      {children}
    </Pressable>
  );
});

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    padding: theme.space.md,
  },
  selected: { borderColor: theme.color.ink },
  pressed: { borderColor: theme.color.coral },
  // The width is `line`'s 1pt and not the designs' 2: at 3.07 against the border it replaces
  // the change is legible at one point, and a second point would move every child of the card
  // by one — a border is drawn inside the box in React Native, so widening it is a re-layout
  // that only the marked cards in a list would take.
  marked: { borderColor: theme.color.voltStroke },
});
