/**
 * The segmented control, per design-system [6.3](../../../docs/design-system.md#63-segmented-control)
 * — an **inset track with a raised selection**, which is the chip's shape inverted.
 *
 * ```
 * track     background line2   radius 10   padding 3   gap 3
 * segment   flex 1  paddingVertical 6  radius 8  label 10.5 / 700  muted
 * selected  background surface   label ink
 * ```
 *
 * **Specified since the document was locked and built only now.** 6.3 closes with *"nothing
 * uses it today; it is specified so the first screen that needs one does not invent a second
 * shape"*, and Play's two ways through the tab were that screen: *Find a game* and *Match me*
 * were two views of one surface, which is precisely what 6.3 is for and what neither the chip
 * (a filter over what is on screen) nor the switch (a claim a player makes) is. That segment is
 * gone — the deck is the Players tab now — and the same control is that tab's whole header, the
 * *Deck | Radar* toggle (ADR-0169 §1), beside the mode segment Find a game still draws.
 *
 * ## What carries the state
 *
 * A `button` with `accessibilityState.selected`, exactly as the chip does — **not**
 * `switch` with `checked`. `the-play-components.md` §6.12 draws that line in writing: nothing
 * in Part 6 carries `checked` on a *mode*, and 6.3 *"picks one of several"*. `selected` is
 * always present rather than omitted when false, because a segment that announced nothing
 * while unselected leaves *not chosen* indistinguishable from *not a choice*.
 *
 * **The selection is not carried by colour.** The raised segment changes surface — `line2`
 * to `surface`, a lightness step rather than a hue — and its label goes `muted` to `ink`;
 * `selected` carries the same fact for whoever sees neither (Part 13, *never colour alone*).
 *
 * **It holds no selection of its own**, and every press is reported, including a press on the
 * segment already selected: only the caller knows whether re-entering a view is a no-op or an
 * arrival, and Play's *Find a game* was the second of those for as long as it was a segment.
 *
 * The label is a string the caller composes rather than a name plus a count slot: a label that
 * carries more than a name is copy, and copy lives with the feature that has something to say.
 * Play drew `Match me · 3` here and no longer does — a number in a segment reads as *how many
 * are waiting* — which is a decision this primitive neither made nor needs to know about, and
 * exactly why the slot was never built into it.
 */

import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';

import { theme } from './theme';

export interface SegmentOption<K extends string> {
  readonly key: K;
  /** What the segment says. Composed by the caller — see the module note. */
  readonly label: string;
  /** Defaults to `label`. Set it where the visible words are cryptic out of context. */
  readonly accessibilityLabel?: string;
}

export interface SegmentProps<K extends string> {
  readonly options: readonly SegmentOption<K>[];
  readonly selected: K;
  /** Fires on every press, selected or not. The control reports; the caller decides. */
  readonly onSelect: (key: K) => void;
  readonly style?: StyleProp<ViewStyle>;
  /**
   * The same control on the app's third dark surface — the Radar pane's header, where the
   * *Deck | Radar* toggle stands over the field's ground rather than over paper
   * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   * §7). 5.2's repaint read as a control, as `Button`'s `onDark` is: the track takes
   * `onDarkTag`, the unselected label the on-dark tiny grey, and the raised segment is still
   * `surface` with `ink` — mock 4 draws it so, and it is the same lightness step the paper
   * version takes, read from the other side. `selected` carries the state either way.
   */
  readonly onDark?: boolean;
}

export function Segment<K extends string>({
  options,
  selected,
  onSelect,
  style,
  onDark = false,
}: SegmentProps<K>) {
  return (
    <View style={[s.track, onDark ? s.trackOnDark : undefined, style]}>
      {options.map((option) => {
        const on = option.key === selected;

        return (
          <Pressable
            key={option.key}
            accessibilityRole="button"
            accessibilityLabel={option.accessibilityLabel ?? option.label}
            accessibilityState={{ selected: on }}
            onPress={() => onSelect(option.key)}
            // 25 + 9 + 9 = 43 of reachable height, and the track's own 3pt of padding makes
            // the rest: 6.5 lists the segment at exactly this slop, and horizontal slop is
            // refused because the neighbour is 3pt away (6.5's own bound).
            hitSlop={theme.hit.seg}
            // Touch has no hover, so the pressed appearance is declared (6.6). Opacity
            // rather than a second fill: the segment is one of the five surfaces 6.6 names.
            style={({ pressed }) => [
              s.segment,
              on ? s.selected : undefined,
              pressed ? s.pressed : undefined,
            ]}
          >
            <Text
              style={[
                s.label,
                onDark && !on ? s.labelOnDark : undefined,
                on ? s.labelSelected : undefined,
              ]}
              numberOfLines={1}
            >
              {option.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  track: {
    flexDirection: 'row',
    gap: theme.space.xxs,
    padding: theme.space.xxs,
    borderRadius: theme.radius.seg,
    backgroundColor: theme.color.line2,
  },
  segment: {
    flex: 1,
    // `minHeight` and a vertical pad, never a fixed 25: at large OS text sizes the label has
    // to grow the segment rather than be clipped by it — the chip's own argument, and the
    // label here is the name of a view rather than a status that may truncate.
    minHeight: theme.size.seg,
    paddingVertical: theme.space.xs,
    borderRadius: theme.radius.segThumb,
    alignItems: 'center',
    justifyContent: 'center',
  },
  trackOnDark: { backgroundColor: theme.color.onDarkTag },
  selected: { backgroundColor: theme.color.surface },
  pressed: { opacity: 0.7 },
  label: { ...theme.type.seg, color: theme.color.muted },
  labelOnDark: { color: theme.color.onDarkTiny },
  labelSelected: { color: theme.color.ink },
});
