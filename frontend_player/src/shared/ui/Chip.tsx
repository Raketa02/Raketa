/**
 * The chip, per design-system 6.2 — the filter pill, and the only true pill in the app.
 *
 * **Specified since the document was locked and built only now** (Part 16, 2026-08-25).
 * The app shipped the tag first, which is deliberately never pressable, so the rule *a
 * pressable pill is a chip* had nothing to point at until the social tags step wanted
 * nineteen of them.
 *
 * **Selected is ink-filled, not coral.** Coral is the action colour and a selected filter
 * is a state — the same argument `PressableCard` makes for the selected card (5.1).
 *
 * **Selection is not carried by colour.** The fill inverts — `ink` on `surface` becomes
 * `surface` on `ink`, a 17,50:1 *luminance* change rather than a change of hue — and
 * `accessibilityState.selected` carries the same fact for whoever sees neither. That
 * pairing is what Part 13's *never colour alone* asks for here, and Part 16 re-read it
 * against the rule at the moment the chip came into use.
 *
 * **It holds no selection of its own.** `selected` is the caller's, and every press is
 * reported — including a press on a chip that is already selected. Only whoever counts
 * the selection can enforce a floor or a ceiling on it, and a chip that swallowed that
 * press would take away removing a tag as well as adding one.
 *
 * 6.2's **small chip is not built**: nothing needs one, and its 10pt label is a size Part
 * 3.3 carries no role for. It arrives with the first screen that wants it, together with
 * the type role — theme and document in one commit (Part 15.3).
 *
 * **`busy` is 6.1's shape on 6.2's pill, and it arrived with the plan card**
 * ([Part 16](../../../docs/design-system.md#part-16--amendments-after-locking), 2026-09-09,
 * [#366](https://github.com/Raketa02/Raketa/issues/366)). A slot chip takes a mutation, *pending,
 * never optimistic* is that map's rule for everything that reaches another person, and a chip that
 * looked pressable while its write was going out would take a second press this app would send.
 * It blocks the press, announces `busy` and dims — the same three things 6.1's button does — and
 * **it swaps the label the way that button does too**, which is what keeps it distinguishable from
 * the greyed-out `disabled` beside it: the two mean opposite things and 6.1's own answer to
 * telling them apart is the word, not a second opacity. The word is the caller's, because a chip's
 * label is a value rather than a verb and only the surface knows what it is about to become.
 *
 * **And it moves with 6.1's busy** ([Part 16](../../../docs/design-system.md#part-16--amendments-after-locking),
 * 2026-11-21; [`decisions.md`](../../../../docs/specs/busy-indicator/decisions.md) §3.6): the pill
 * is drawn whole, not dimmed, and React Native's `ActivityIndicator` turns before the busy word in
 * the label's ink — so *on its way* and *you may not* are two drawings at last, and the dim is the
 * disabled chip's alone. The sport's dot and the count **step aside** while it turns: both describe
 * the value the busy word has replaced, and a sport dot beside *Starting…* would be a dot without
 * its name. Hidden from a listener, and turning under reduced motion, for the button's reasons.
 *
 * **The disabled chip arrived late and only where a chip is genuinely refused**
 * ([Part 16](../../../docs/design-system.md#part-16--amendments-after-locking), 2026-09-09,
 * [#365](https://github.com/Raketa02/Raketa/issues/365)). It is not the tag picker's answer to a
 * ninth tag — that step refuses out loud rather than by greying the other nineteen, and 6.2's
 * original sentence about it stands. What it is for is a control the **account** may not use: a
 * held account cannot post, and a quick chip that looked pressable and did nothing would be
 * exactly the dead end 6.1 forbids. It is `opacity: .4` and not pressable, 6.1's own disabled
 * row rather than a second value, and it may only be drawn where a note above the row has
 * already said why — which is the condition the amendment attaches to it.
 */

import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';

import { theme } from './theme';

export interface ChipProps {
  readonly label: string;
  /**
   * A 6pt square in a sport's identity colour, before the label — **6.4's dot, on 6.2's
   * pill**, and the same square rather than a second one.
   *
   * It is **decoration and nothing else**, hidden from assistive technology, because the
   * label beside it always says the same thing. That is the condition 2.3 attaches to every
   * surface drawing a sport hue, and it is what keeps a fifth sport a decision about colour
   * rather than a screen that stops being readable.
   */
  readonly dot?: string;
  /**
   * **A count after the label** — *Padel 10*, the members rated in a sport on *Post a game*'s chips
   * ([#558](https://github.com/Raketa02/Raketa/issues/558), mock 16; Part 16 2026-10-02). Mono, as
   * every count is (1.4), and quieter than the word: `muted`, `onDarkTiny` once selected. Drawn and
   * not spoken — the caller says it in `accessibilityLabel`, where it can say what it counts.
   */
  readonly count?: number;
  /** Fires on every press, selected or not. The chip reports; the caller decides. */
  readonly onPress: () => void;
  /**
   * Drawn at `opacity: .4`, not pressable, and announced as disabled.
   *
   * **Only where the act itself is refused**, and only under a note that has already said so:
   * greying a control is this system's word for *you may not*, and a screen that greys without
   * explaining is the dead end 6.1 and #324 both refuse. It is never *busy* — {@link busy} is —
   * and never a ceiling on a selection, which is refused in words.
   */
  readonly disabled?: boolean;
  /**
   * A press is on its way. Blocks the press, announces `busy`, swaps the label and turns a spinner
   * before it, at the pill's full strength.
   *
   * **A busy chip is not a disabled one**, which is 6.1's sentence: the disabled one dims and the
   * busy one spins. {@link busyLabel} is still required in practice — a chip's label is a value,
   * and a spinner beside *Saturday* does not say what Saturday is becoming.
   */
  readonly busy?: boolean;
  /**
   * The chip on the app's third dark surface — the Radar pane's sport chips, under the toggle
   * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   * §7). 5.2's repaint, as the tag's `onDark` is: the unselected pill is `onDarkTag` with an
   * `onDarkHair` edge and a white label, and the selected one inverts to `surface` with `ink` — the same
   * lightness step the paper chip takes from `surface` to `ink`, read from the other side.
   * `selected` carries the state either way, and the dot is the sport's on both.
   */
  readonly onDark?: boolean;
  /** What the chip reads while it is busy. Defaults to the label, which is rarely what is meant. */
  readonly busyLabel?: string;
  /** Drawn ink-filled and announced as selected. Owned by the caller. */
  readonly selected?: boolean;
  /** Defaults to `label`. Set it when the word alone is cryptic out of context. */
  readonly accessibilityLabel?: string;
  readonly accessibilityHint?: string;
  readonly style?: StyleProp<ViewStyle>;
}

export function Chip({
  label,
  onPress,
  dot,
  selected = false,
  disabled = false,
  busy = false,
  busyLabel,
  accessibilityLabel,
  accessibilityHint,
  style,
  onDark = false,
  count,
}: ChipProps) {
  const blocked = disabled || busy;
  // The accessible name follows what is drawn, exactly as 6.1's does: a chip reading "Saving…"
  // while it announces "Saturday" hands two different apps to two different players. A caller
  // that names the chip itself owns both halves and is left alone.
  const shown = busy ? (busyLabel ?? label) : label;
  // The label's ink, as `s.label` and its two repaints draw it: white where the pill is dark —
  // the selected paper chip, the unselected on-dark one — and `ink` on the two light pills.
  const ink = selected !== onDark ? theme.color.surface : theme.color.ink;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? shown}
      accessibilityHint={accessibilityHint}
      // Always present, never omitted when false: a chip that announced nothing while
      // unselected would leave "not chosen" indistinguishable from "not a choice".
      accessibilityState={{ selected, disabled: blocked, busy }}
      disabled={blocked}
      onPress={onPress}
      // 27 + 9 + 9 = 45. The visual stays small and the target grows (6.5); the 3pt of
      // horizontal slop is what a 6pt gap between neighbours allows.
      hitSlop={theme.hit.chip}
      // Touch has no hover, so the pressed appearance is declared rather than inherited
      // (6.6). Immediate, not animated — the prototype's 120ms is a mouse transition.
      style={({ pressed }) => [
        s.chip,
        onDark ? s.chipOnDark : undefined,
        selected ? (onDark ? s.selectedOnDark : s.selected) : undefined,
        pressed && !blocked ? s.pressed : undefined,
        disabled && !busy ? s.disabled : undefined,
        style,
      ]}
    >
      {busy ? (
        <ActivityIndicator
          size="small"
          color={ink}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />
      ) : null}
      {busy || dot === undefined ? null : (
        <View
          style={[s.dot, { backgroundColor: dot }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      )}
      <Text
        style={[
          s.label,
          onDark && !selected ? s.labelOnDark : undefined,
          selected && !onDark ? s.labelSelected : undefined,
        ]}
      >
        {shown}
      </Text>
      {busy || count === undefined ? null : (
        <Text style={[s.count, selected ? s.countSelected : undefined]}>{count}</Text>
      )}
    </Pressable>
  );
}

const s = StyleSheet.create({
  chip: {
    // `minHeight` and a vertical pad, never a fixed 27: at large OS text sizes the label
    // has to grow the pill rather than be clipped by it, and the label is the choice
    // itself here — the tag truncates because a status must not reflow a row, which is
    // not the same obligation. `radius.pill` holds at whatever height that lands on.
    minHeight: theme.size.chip,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xxs,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.space.xs,
    // `alignSelf`, so a chip in a row is its own width rather than the row's.
    alignSelf: 'flex-start',
  },
  selected: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  // 5.2's repaint: the on-dark tag's bed under the on-dark hairline, and the selection inverts
  // to `surface` with `ink` — the paper chip's own step, read from the dark side.
  chipOnDark: { backgroundColor: theme.color.onDarkTag, borderColor: theme.color.onDarkHair },
  selectedOnDark: { backgroundColor: theme.color.surface, borderColor: theme.color.surface },
  // Square, and the tag's own square: 6.4 already specified one sport dot and there is no
  // second shape for the same fact. It is drawn on both fills unchanged — a sport's hue is
  // an identity rather than a state, so it does not invert with the pill under it.
  dot: { width: theme.size.sportDot, height: theme.size.sportDot },
  pressed: { opacity: 0.7 },
  // 6.1's disabled row, not a second value — and *you may not*'s alone: a busy chip spins instead.
  disabled: { opacity: 0.4 },
  label: { ...theme.type.chip, color: theme.color.ink },
  labelOnDark: { color: theme.color.surface },
  // `surface` is the app's one white; there is no separate `white` token, deliberately.
  labelSelected: { color: theme.color.surface },
  count: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  countSelected: { color: theme.color.onDarkTiny },
});
