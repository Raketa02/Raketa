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
 * Play drew `Match me · 3` here and no longer does — a number **in the label** reads as part of
 * the view's name.
 *
 * ## The badge — a count only you can clear, over the segment's corner
 *
 * A number that means *something here is yours to attend to* is the Chats badge's job, and `badge`
 * draws it: `CornerBadge`, the same `coralInk` pill with a white tabular digit at the segment's own
 * size, overlapping the segment's top-right corner so it belongs to that view rather than sitting
 * beside it (a group page's Games, Fill in and You’re in). On Fill in and You’re in it counts what
 * is **new since the player last looked** (#849, ADR-0208), and the page draws none on the segment
 * selected, since what that view shows is seen while it is shown; what a count means is the caller's.
 * Out of the layout, so a count arriving moves nothing. **It announces nothing**: the caller puts
 * the count in the option's `accessibilityLabel`, as the tab bar puts it on the column's, and a
 * badge that spoke too would be one number read twice.
 *
 * ## The door — a view that isn't yours yet
 *
 * The Games switch draws both kinds always, and the kind the player's intent doesn't want is a
 * **door** (`door`; [ADR-0201](../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §2): its press opens a way to change the intent rather than the view, and it reads *not yours
 * yet*. **Dimmed, never disabled** — the label at `size.segDoorOpacity` and nothing else: the same
 * box, the same slop, no `disabled` in its state, and its press reported like any other. A door
 * that read as shut is one nobody opens. The words carry the state as well (the caller's door has
 * no number), so the dim is never the whole fact.
 *
 * ## An option that owns a menu — a tab with a second layer
 *
 * A group page's **Friends** tab holds the kind of the game being built, in **the tab's menu**
 * (`TabMenu`, 9.5; PRD [#859](https://github.com/Raketa02/Raketa/issues/859), #861 — Games' from
 * #862), where a row of *Competitive | For fun* under the tabs once stood. Such an option carries
 * `menu`. **While it is selected and its menu is offered** — the page's rule, not this control's —
 * it draws a Feather chevron at its right edge, pointing down while the menu is shut and turning up
 * while it is open, and says `expanded`. Anywhere else it is an ordinary option: no chevron, no
 * `expanded`, a label and its badge. **The control still reports every press**, the selected
 * option's too: the page decides that a press there opens or shuts the menu.
 *
 * **It widens by the chevron's room, and the others share the rest** (`size.segMenu`): its box's
 * flex basis is the room where every other's is nought, so its label keeps the same share of the
 * track as every other option's and the chevron is added beside it, never squeezed out of it. **The
 * widths move by a layout transition** on each option's box — one change of size, and Reanimated
 * moves the frames; never a width animated frame by frame (`CLAUDE.md`'s Reanimated rule). So in a
 * control where any option owns a menu, **every option is a box** that is laid out in the track and
 * carries the raised surface, with the press inside it; a control with none is drawn as it always
 * was. The chevron turns on the same beat (`motion.tabMenu`), and under reduced motion nothing moves.
 */

import Feather from '@expo/vector-icons/Feather';
import { useEffect } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type LayoutRectangle,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import Animated, {
  Easing,
  LinearTransition,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { CornerBadge } from './CornerBadge';
import { useReducedMotion } from './overlay';
import { theme } from './theme';

const EASE = Easing.bezierFn(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** The widths moving as one layout change — see the module note. */
const WIDEN = LinearTransition.duration(theme.motion.tabMenu).easing(EASE);

/** The room the chevron takes beside the label: its gap, itself, and its inset from the edge. */
const CHEVRON_ROOM = theme.size.segMenu.gap + theme.size.segMenu.chevron + theme.size.segMenu.inset;

/** Pointing down while the menu is shut, turned over while it is open. */
const TURN = 180;

/**
 * **The menu an option owns** — see the module note. Present on the option that has one, whether or
 * not it is offered now, so the control's drawing is the same while the page decides.
 */
export interface SegmentMenu {
  /** Whether the page offers the menu now. Selected and offered, the option draws its chevron. */
  readonly offered: boolean;
  /** Whether the menu is open: the chevron turned up, and `expanded`. */
  readonly open: boolean;
  /** Where the option stands in the track, each time it is laid out — what its menu hangs from. */
  readonly onFrame?: (frame: LayoutRectangle) => void;
}

export interface SegmentOption<K extends string> {
  readonly key: K;
  /** What the segment says. Composed by the caller — see the module note. */
  readonly label: string;
  /** Defaults to `label`. Set it where the visible words are cryptic out of context. */
  readonly accessibilityLabel?: string;
  /**
   * The caller's count for this view — what is new on it, on a group page — drawn over the
   * segment's corner: see the module note. Absent, or 0, draws nothing. The caller says the count in
   * `accessibilityLabel`.
   */
  readonly badge?: number;
  /**
   * **A door** — a view that isn't the player's yet, whose press opens a way to make it theirs
   * rather than the view: its label dimmed, nothing else changed — see the module note.
   */
  readonly door?: boolean;
  /** **This option owns a menu** — a chevron while selected and offered: see the module note. */
  readonly menu?: SegmentMenu;
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
  /**
   * **The tab's own view switch**, drawn as play mocks 1 and 3 draw Play's *Groups | Explore*
   * ([#512](https://github.com/Raketa02/Raketa/issues/512), 6.3 as amended in Part 16): a taller
   * control whose raised segment is **`ink` with a `surface` label** rather than `surface` with an
   * `ink` one. It switches the whole tab rather than a pane inside a screen, and the mocks set it
   * apart for that — the same lightness step read from the dark side, as `onDark` reads it. The
   * track is `paper2`, the recess the popover close and the situation header already use, and the
   * label is `btn`'s 12 / 700. **No shadow under the thumb**, although the mocks draw one: a
   * segment does not float (4.3). `selected` still carries the state.
   */
  readonly prominent?: boolean;
}

export function Segment<K extends string>({
  options,
  selected,
  onSelect,
  style,
  onDark = false,
  prominent = false,
}: SegmentProps<K>) {
  const reduced = useReducedMotion();
  // One option with a menu makes every option a box, so all the widths move together.
  const boxed = options.some((option) => option.menu !== undefined);

  return (
    <View
      style={[
        s.track,
        onDark ? s.trackOnDark : undefined,
        prominent ? s.trackProminent : undefined,
        style,
      ]}
    >
      {options.map((option) => {
        const on = option.key === selected;
        const label = (
          <Text
            style={[
              s.label,
              prominent ? s.labelProminent : undefined,
              onDark && !on ? s.labelOnDark : undefined,
              on ? (prominent ? s.labelSelectedProminent : s.labelSelected) : undefined,
              option.door === true ? s.labelDoor : undefined,
            ]}
            numberOfLines={1}
          >
            {option.label}
          </Text>
        );
        const badge =
          option.badge === undefined || option.badge <= 0 ? null : (
            <CornerBadge count={option.badge} />
          );

        if (boxed) {
          const menu = option.menu;
          // The chevron, and the room for it, only while selected and offered.
          const chevron = on && menu?.offered === true;
          return (
            <Animated.View
              key={option.key}
              testID={`segment-${option.key}`}
              layout={reduced ? undefined : WIDEN}
              onLayout={
                menu?.onFrame === undefined
                  ? undefined
                  : ({ nativeEvent }) => menu.onFrame?.(nativeEvent.layout)
              }
              style={[
                s.box,
                chevron ? s.boxWidened : undefined,
                on ? (prominent ? s.selectedProminent : s.selected) : undefined,
              ]}
            >
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={option.accessibilityLabel ?? option.label}
                accessibilityState={
                  chevron ? { selected: on, expanded: menu.open } : { selected: on }
                }
                onPress={() => onSelect(option.key)}
                // 6.5's slop, as the unboxed segment's below.
                hitSlop={theme.hit.seg}
                // The press dims what the box holds; the raised surface is the box's, and stays.
                style={({ pressed }) => [
                  s.boxPress,
                  prominent ? s.segmentProminent : undefined,
                  chevron ? s.pressWidened : undefined,
                  pressed ? s.pressed : undefined,
                ]}
              >
                {label}
                {chevron ? (
                  <SegmentChevron
                    open={menu.open}
                    reduced={reduced}
                    tint={prominent ? theme.color.surface : theme.color.ink}
                    testID={`segment-chevron-${option.key}`}
                  />
                ) : null}
                {badge}
              </Pressable>
            </Animated.View>
          );
        }

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
              prominent ? s.segmentProminent : undefined,
              on ? (prominent ? s.selectedProminent : s.selected) : undefined,
              pressed ? s.pressed : undefined,
            ]}
          >
            {label}
            {badge}
          </Pressable>
        );
      })}
    </View>
  );
}

/**
 * The selected option's chevron — down while its menu is shut, turned over while it is open, on the
 * menu's beat; at once under reduced motion. A mark: the option's `expanded` says the same.
 */
function SegmentChevron({
  open,
  reduced,
  tint,
  testID,
}: {
  readonly open: boolean;
  readonly reduced: boolean;
  readonly tint: string;
  readonly testID: string;
}) {
  const turned = useSharedValue(open ? 1 : 0);
  useEffect(() => {
    const to = open ? 1 : 0;
    // The app has already asked the OS (`reduced`), so Reanimated is told not to ask again.
    turned.value = reduced
      ? to
      : withTiming(to, {
          duration: theme.motion.tabMenu,
          easing: EASE,
          reduceMotion: ReduceMotion.Never,
        });
  }, [open, reduced, turned]);
  const turn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${TURN * turned.value}deg` }],
  }));

  return (
    <Animated.View
      testID={testID}
      style={[s.chevron, turn]}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Feather name="chevron-down" size={theme.size.segMenu.chevron} color={tint} />
    </Animated.View>
  );
}

const s = StyleSheet.create({
  track: {
    flexDirection: 'row',
    gap: theme.space.xxs,
    padding: theme.space.xxs,
    borderRadius: theme.radius.seg,
    backgroundColor: theme.color.line2,
    // A segment's badge stands above the track's top edge too; Android would clip it.
    overflow: 'visible',
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
    // Android clips a child drawn outside its parent, and the badge overhangs the corner.
    overflow: 'visible',
  },
  trackOnDark: { backgroundColor: theme.color.onDarkTag },
  selected: { backgroundColor: theme.color.surface },
  pressed: { opacity: 0.7 },
  label: { ...theme.type.seg, color: theme.color.muted },
  labelOnDark: { color: theme.color.onDarkTiny },
  labelSelected: { color: theme.color.ink },
  labelDoor: { opacity: theme.size.segDoorOpacity },
  trackProminent: { backgroundColor: theme.color.paper2 },
  // `btn`'s height — the thumb is a control the size of a button, which is what the mock draws.
  segmentProminent: { minHeight: theme.size.btn },
  selectedProminent: { backgroundColor: theme.color.ink },
  labelProminent: { ...theme.type.btn },
  labelSelectedProminent: { color: theme.color.surface },
  // An option as a box, where any option owns a menu: the segment's share and shape, laid out in
  // the track, with the press inside it — see the module note.
  box: {
    flexGrow: 1,
    flexShrink: 1,
    flexBasis: 0,
    borderRadius: theme.radius.segThumb,
    overflow: 'visible',
  },
  // The chevron's room, on top of the share every option has.
  boxWidened: { flexBasis: CHEVRON_ROOM },
  boxPress: {
    flexGrow: 1,
    minHeight: theme.size.seg,
    paddingVertical: theme.space.xs,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
  // The label keeps the share; the chevron stands in the room beside it.
  pressWidened: { paddingRight: CHEVRON_ROOM },
  chevron: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: theme.size.segMenu.inset,
    justifyContent: 'center',
  },
});
