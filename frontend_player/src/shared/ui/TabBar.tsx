/**
 * The tab bar, per design-system 10.2 — **the dock**: a rounded slab floating over the screen's
 * foot, **Home · Play · You** in three equal columns, and the selection marker under the lit one
 * ([ADR-0210](../../../../docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md),
 * [#883](https://github.com/Rakieta02/Rakieta/issues/883)).
 *
 * **The drawn object only.** It takes the active tab and a press handler and knows nothing
 * about routes, stacks or which screen is mounted; the shell that wires it is a separate
 * ticket, and the one navigation rule that ticket must not lose — `<Tabs>` remembers each
 * tab's stack by default, which fails *back goes where I came from* silently — is a fact
 * about the navigator, not about the bar.
 *
 * ## The inventory is fixed, and it lives here
 *
 * Three tabs, three Ionicons pairs, one family on the bar (ADR-0210 §5, which supersedes
 * [ADR-0135](../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md) for the
 * bar and keeps its argument): *"the family is fixed … a sixth glyph on a sixth surface is a fresh
 * question that inherits the family and nothing else, never a licence to sprinkle."* A caller that
 * could pass its own tabs is a caller that could add a fourth without argument — and it would
 * silently break `labelMaxScale` and the marker's fit, which are held against exactly these three
 * words in exactly this many columns.
 *
 * ## The dock, and the glass
 *
 * 54 tall, 12 in from each side, lifted the larger of 12 and the bottom inset, at `radius.dock`
 * (§2). **The bottom inset is the lift's**: the dock pads itself with nothing, so on a notched
 * iPhone it rests on the safe-area line and on an Android phone with no inset it stands 12 clear of
 * three edges. Its **reach**, the room it takes at the bottom, is the lift + 54; the shell says it
 * (`tabBarReach.ts`) and every screen ends there.
 *
 * **The material is the theme's switch** (`theme.glass`, §7): the iPhone draws `color.glass` over
 * `expo-blur` at the spike's strength, and Android draws the glass only where the switch says so —
 * today it doesn't, because the A32 measured the blur costing frames, so its dock is opaque
 * `surface`. Either way the dock is bounded by a 1pt `line` hairline, a 1pt `surface` rim runs
 * inside it, and the deck card's shadow lifts it: `shadow.dock` on the opaque dock, and the same
 * values as `boxShadow` (`glass.shadow`) on a dock that draws the glass. A translucent dock has no
 * opaque fill to work a shadow's outline from, so iOS's shadow props would be drawn from its pixels —
 * an off-screen pass whenever the page moves under the blur, which can stop the blur drawing — and
 * Android's `elevation` would show through it. `boxShadow` is drawn outside the box only.
 *
 * ## Selection is a marker, a shape and a tone
 *
 * The lit tab's icon fills in and turns `coral`, its label turns `coralInk`, and both sit on **the
 * selection marker**, an opaque `coralSoft` capsule (§4, §5). Idle tabs are outlines in `tabIdle`.
 * All three channels are drawn from one value, **the marker's trip**, which follows `active` from
 * the next frame, so they cannot disagree — the dock never shows two selected tabs. A channel
 * added here reads the trip too, never `selected`: `selected` is the column's spoken state, and it
 * turns at the press while the drawing turns with the slide. Play's bolt is filled in both states,
 * because it is the brand's mark, so on Play the marker and the colour carry it alone.
 *
 * **Layers, bottom to top: glass → marker → icons and labels → badge.** The marker is one layer
 * of the dock's own rather than a part of a column: it is what travels between columns, a press
 * dims the column and never the marker, and its stretch is a scale on a layer that holds no word
 * or glyph, so nothing is ever deformed and iOS has nothing to rasterise blurred. It stands at the
 * lit column's centre, worked out from the window's width as every other width in the app is — a
 * measured one would leave the first frame without a marker.
 *
 * ## The marker travels
 *
 * **When the lit tab changes, the marker slides to it** on `motion.tabMarker`'s 460 ms spring,
 * stretching like a bubble as it speeds up and recoiling as it brakes, and the new tab colours in
 * after it sets off (ADR-0210 §8, [#884](https://github.com/Rakieta02/Rakieta/issues/884)). The
 * numbers are `tabMarkerMotion.ts`'s, pure; here they run on the UI thread off **one clock** that
 * Reanimated moves from 0 to 460, so the travel, the stretch and the colour-in can never drift apart.
 * Per frame only `transform` and `opacity` move.
 *
 * - **It slides on every change of the lit tab after the dock's first draw** — a press, a landing,
 *   a notice, a group opened from Home, and back. The bar cannot tell them apart, and has no need
 *   to: the lit tab is the one value it is handed.
 * - **It never slides on the dock's first draw**, which is also every time the dock comes back
 *   after the chat or Android's keyboard: the shell draws it anew, and a new dock is placed. Nor on
 *   a press of the lit tab, which changes nothing it is handed.
 * - **A press mid-flight turns it from where it is, at the speed it has**: the new trip is worked
 *   out on the UI thread in the same step that restarts the clock, so no frame falls between the
 *   marker's place and the trip that starts from it.
 * - **The colour-in is a cross-fade** of two stacked layers per column, idle and selected, so only
 *   opacity moves: the new tab's selected layer comes in over 300 ms on `easeDecel`, 140 ms into
 *   the slide, over its idle layer, which stays whole under it until it is whole — and the tab left
 *   is idle at once.
 * - **Reduce motion places the marker** under the new tab, and the colours switch at once — also the
 *   moment it is turned on mid-slide.
 *
 * **The animated layers are memoised** and handed only shared values and fixed inventory, so a
 * re-render of the dock — a count arriving, a press — never redraws them with their first pose.
 *
 * Every name is typed against Ionicons' own `glyphMap`, so a glyph absent from
 * `@expo/vector-icons@14.0.4` is a compile error rather than a blank column nobody notices at
 * 18pt. **The bolt is a glyph, not a text character**: `U+26A1` carries
 * `Emoji_Presentation=Yes`, so `<Text>⚡</Text>` requests colour emoji and a `color` style has
 * nothing to apply to.
 *
 * ## One badge, on Home, and on no other column
 *
 * **The badge inventory is fixed at one, for the reason the glyph inventory is fixed at three**
 * ([#326](https://github.com/Rakieta02/Rakieta/issues/326)). It counts the booked games that need
 * you — a seat open, a result to enter or confirm, a no-show against you, a payment to confirm
 * ([#550](https://github.com/Rakieta02/Rakieta/issues/550), [#556](https://github.com/Rakieta02/Rakieta/issues/556))
 * — which is what makes it an obligation a player can discharge rather than a number that nags.
 * It is a `coralInk` fill, *a thing to attend to*, kept apart from the marker's `coralSoft`,
 * *where you are*, by fill.
 *
 * **It is a named prop and never a hook.** `shared/ui` importing a feature hook inverts the
 * dependency ([ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md))
 * and would give *"the drawn object only"* a network call. And it is `gamesNeedingYou` rather
 * than a generic `badges?: Partial<Record<TabBarKey, number>>`, which is the glyph argument in a
 * new costume: a caller that can badge any tab can badge You.
 *
 * **Nothing is drawn unless there is a count.** `undefined` is zero, in flight and refused at
 * once, and they are deliberately not told apart — a spinner or a `?` on permanent chrome is
 * anxiety with no act behind it. **No cap**: a double-digit badge means something genuinely
 * unusual, and `9+` would hide the one case worth seeing.
 *
 * **The count is spoken on the column's own label.** `Column` is `accessible` with an explicit
 * name, so a `<Text>` dropped inside is swallowed rather than announced — the badge is a change
 * to the **label** at least as much as to the drawing, or it does not exist for half its
 * readers. Not `accessibilityValue`: a tab has no value, and the count is part of what the tab
 * *is* right now.
 */

import Ionicons from '@expo/vector-icons/Ionicons';
import { BlurView } from 'expo-blur';
import { counted } from '@/shared/formatting/counted';
import { memo, useEffect, useRef } from 'react';
import { Platform, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Animated, {
  Easing,
  ReduceMotion,
  runOnUI,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CountBadge } from './CountBadge';
import { useReducedMotion } from './overlay';
import {
  colourInAt,
  MARKER_SLIDE,
  markerAt,
  markerPlacedAt,
  markerTravelling,
  type MarkerTrip,
} from './tabMarkerMotion';
import { theme } from './theme';

/** The marker's rest width, as a number a UI-thread worklet can hold without copying the theme. */
const MARKER_WIDTH = theme.size.tabBar.marker.width;

/** The colour-in's curve — the app's for a thing arriving. */
const EASE = Easing.bezierFn(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** A glyph name Ionicons actually ships. Not a `string`, and not behind a cast. */
type IoniconsGlyph = keyof typeof Ionicons.glyphMap;

export type TabBarKey = 'home' | 'play' | 'you';

export interface TabBarTab<Key extends string = TabBarKey> {
  readonly key: Key;
  readonly label: string;
  /** The outline drawn while the tab is idle, and the filled glyph drawn while it is lit. */
  readonly glyph: { readonly idle: IoniconsGlyph; readonly lit: IoniconsGlyph };
}

/**
 * The three, in order. **The first is Home**, today's Now renamed whole — key, label and screen,
 * the route staying `/` ([#550](https://github.com/Rakieta02/Rakieta/issues/550)): your games from
 * the moment they are booked. **Play's bolt is `flash` in both states** (ADR-0210 §5): the brand's
 * mark for a game being dealt, not a pictogram with an outline.
 *
 * `labelMaxScale` and the marker are held against these exact words. Adding a fourth, or a longer
 * one, is a change `tabBarLabelCap.test.ts` has to pass before it is a change to this list.
 */
export const TAB_BAR_TABS = [
  { key: 'home', label: 'Home', glyph: { idle: 'home-outline', lit: 'home' } },
  { key: 'play', label: 'Play', glyph: { idle: 'flash', lit: 'flash' } },
  { key: 'you', label: 'You', glyph: { idle: 'person-outline', lit: 'person' } },
] as const satisfies readonly TabBarTab[];

/** The dock's hairline, and the rim inside it — the 1pt every border in the app is. */
const HAIRLINE = 1;

/** **How far the dock stands off the phone's foot**: the larger of its least lift and the inset. */
function dockLift(bottomInset: number): number {
  return Math.max(theme.size.tabBar.lift, bottomInset);
}

/**
 * **The room the dock takes at the bottom of the phone while it is drawn** — its lift and its 54,
 * for either bar: the administrator's is the same dock with two columns. The shell says it
 * (`useSaysTabBarReach`); nothing else works it out.
 *
 * **A fixed figure, not a floor**: the dock is 54 at every text size, because the label's cap
 * holds it inside the marker (10.2). 66 on the A32, 88 on a notched iPhone.
 */
export function tabBarReachOver(bottomInset: number): number {
  return dockLift(bottomInset) + theme.size.tabBar.height;
}

/** The bar's own frame — what a suite reads to see where it stands. Both bars carry it. */
export const TAB_BAR_TEST_ID = 'tab-bar';

/** The selection marker's drawing — what a suite reads to see which tab it stands under. */
export const TAB_BAR_MARKER_TEST_ID = 'tab-bar-marker';

export interface TabBarProps {
  /** Which of the three is showing. Play stays active for every screen inside Play. */
  readonly active: TabBarKey;
  readonly onPress: (key: TabBarKey) => void;
  /**
   * The booked games that need you — the badge on Home.
   *
   * Absent draws nothing, and absent covers zero, still loading and failed alike. The caller
   * folds those three together, so this prop is *a count to draw* rather than a number the bar
   * has to decide about.
   */
  readonly gamesNeedingYou?: number;
}

/**
 * **What Home says after its own name** — the badge's half of the column's spoken label.
 *
 * **The words live here rather than in `the-words.md`**: that file is the deck for codes the
 * backend sends and the app writes words for, and these are chrome copy over a count the client
 * is handed ([#326](https://github.com/Rakieta02/Rakieta/issues/326) §9). They sit beside
 * `TAB_BAR_TABS`, which already owns the label they follow — and the counted phrase goes through
 * `counted()` like every other in the app, because a market with real plural rules has to have
 * one function to change rather than every sentence that counts something.
 */
const homeBadgeWords = (count: number) => `${counted(count, 'game', 'games')} waiting on you`;

/** What a column announces — its name, and the count when it is carrying one. */
function columnLabel(tab: TabBarTab<string>, waiting: number | undefined): string {
  return waiting === undefined ? tab.label : `${tab.label}, ${homeBadgeWords(waiting)}`;
}

export function TabBar({ active, onPress, gamesNeedingYou }: TabBarProps) {
  return (
    <Dock
      tabs={TAB_BAR_TABS}
      active={active}
      onPress={onPress}
      waiting={(key) => (key === 'home' ? gamesNeedingYou : undefined)}
    />
  );
}

/**
 * **The administrator area's bar** — two columns, **Groups · You**, the same dock with the same
 * marker (club mock 17; [#516](https://github.com/Rakieta02/Rakieta/issues/516); ADR-0210 §3, Q16).
 *
 * **A second fixed inventory, not a caller's list.** ADR-0135's argument stands whole: a bar that
 * took its tabs from a caller could grow a fourth without argument. The administrator's side of the
 * account is a second surface with its own two places, so it gets its own inventory here, beside
 * the three — the family inherited (Ionicons, outline idle and filled lit), nothing else.
 * `people` is *Groups*: the crowds the administrator runs. `person` is *You* on both.
 *
 * No badge: *N waiting* is on the group's card, where it can be answered.
 */
export type AdministratorTabBarKey = 'groups' | 'you';

export const ADMINISTRATOR_TAB_BAR_TABS = [
  { key: 'groups', label: 'Groups', glyph: { idle: 'people-outline', lit: 'people' } },
  { key: 'you', label: 'You', glyph: { idle: 'person-outline', lit: 'person' } },
] as const satisfies readonly TabBarTab<AdministratorTabBarKey>[];

export interface AdministratorTabBarProps {
  /** Which of the two is showing. Groups stays active for every screen inside Groups. */
  readonly active: AdministratorTabBarKey;
  readonly onPress: (key: AdministratorTabBarKey) => void;
}

export function AdministratorTabBar({ active, onPress }: AdministratorTabBarProps) {
  return <Dock tabs={ADMINISTRATOR_TAB_BAR_TABS} active={active} onPress={onPress} />;
}

/** **Whether this phone's dock draws the glass** — always on an iPhone, on Android at the switch. */
const drawsGlass = () => Platform.OS !== 'android' || theme.glass.android;

/**
 * **The dock both bars draw**: the material, the marker, and a column per tab. `waiting` is the
 * count a column carries — Home's alone, which the player's bar hands it.
 */
function Dock<Key extends string>({
  tabs,
  active,
  onPress,
  waiting,
}: {
  readonly tabs: readonly TabBarTab<Key>[];
  readonly active: Key;
  readonly onPress: (key: Key) => void;
  readonly waiting?: (key: Key) => number | undefined;
}) {
  const { bottom } = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const glass = drawsGlass();

  // The columns divide what is inside the hairline equally, so the lit one's centre is worked out
  // from the window rather than measured: a marker that waited on a layout would leave the dock's
  // first frame with none (ADR-0210 §8: never without its marker, not even for a frame).
  const column = (width - 2 * theme.size.tabBar.sideInset - 2 * HAIRLINE) / tabs.length;
  const lit = Math.max(
    0,
    tabs.findIndex((tab) => tab.key === active),
  );
  const { trip, clock } = useMarkerTravel(lit);
  const columnWidth = useSharedValue(column);
  useEffect(() => {
    columnWidth.value = column;
  }, [column, columnWidth]);

  return (
    <View
      testID={TAB_BAR_TEST_ID}
      style={[
        s.dock,
        { bottom: dockLift(bottom) },
        // A translucent dock gives neither platform's own shadow an opaque fill to draw from, and
        // `boxShadow` is drawn outside the box only (the A32 spike's T3).
        glass ? s.glassShadow : s.shadow,
      ]}
    >
      {/* The glass: clipped to the inner corner, the blur under the 88% white. */}
      <View pointerEvents="none" style={[s.material, glass ? null : s.opaque]}>
        {glass ? (
          <>
            <BlurView
              intensity={theme.glass.blur}
              tint="light"
              experimentalBlurMethod={Platform.OS === 'android' ? 'dimezisBlurView' : undefined}
              style={StyleSheet.absoluteFill}
            />
            <View style={s.glass} />
          </>
        ) : null}
      </View>
      <View pointerEvents="none" style={s.rim} />
      <Marker trip={trip} clock={clock} column={columnWidth} />
      {tabs.map((tab, index) => (
        <Column
          key={tab.key}
          tab={tab}
          index={index}
          selected={tab.key === active}
          onPress={onPress}
          waiting={waiting?.(tab.key)}
          trip={trip}
          clock={clock}
        />
      ))}
    </View>
  );
}

/** The marker's trip and the clock it runs on — what every animated layer of the dock reads. */
interface Travel {
  readonly trip: SharedValue<MarkerTrip>;
  readonly clock: SharedValue<number>;
}

/**
 * **The marker's travel to the lit column**: placed under it on the dock's first draw, and sent to
 * it on every change after — from where it is, on the UI thread — or placed under it at once under
 * Reduce motion. A press of the lit tab changes nothing here, so nothing moves.
 */
function useMarkerTravel(lit: number): Travel {
  const reduced = useReducedMotion();
  const trip = useSharedValue(markerPlacedAt(lit));
  // At its end: a placed marker is at rest, and its tab wholly coloured in.
  const clock = useSharedValue(MARKER_SLIDE);
  const drawnFor = useRef(lit);

  useEffect(() => {
    const changed = drawnFor.current !== lit;
    drawnFor.current = lit;
    // Placed under Reduce motion — and the moment it is turned on, even mid-slide.
    if (reduced) {
      trip.value = markerPlacedAt(lit);
      clock.value = MARKER_SLIDE;
      return;
    }
    if (changed) runOnUI(setOff)(trip, clock, lit);
  }, [lit, reduced, trip, clock]);

  return { trip, clock };
}

/**
 * **A new trip, set off on the UI thread**: worked out from the marker's place and speed at the
 * clock's reading, and the clock restarted, in one step — so no frame is drawn between the two.
 */
function setOff(trip: SharedValue<MarkerTrip>, clock: SharedValue<number>, to: number) {
  'worklet';
  trip.value = markerTravelling(trip.value, clock.value, to);
  clock.value = 0;
  // The app has decided Reduce motion itself (above), so the clock is never cut by the system's.
  clock.value = withTiming(MARKER_SLIDE, {
    duration: MARKER_SLIDE,
    easing: Easing.linear,
    reduceMotion: ReduceMotion.Never,
  });
}

/**
 * **The selection marker** — the dock's own layer, moved by `transform` alone: translated to where
 * its trip has it, and scaled about its centre by its stretch. Memoised on shared values, so a
 * re-render of the dock never redraws it with its first pose.
 */
const Marker = memo(function Marker({
  trip,
  clock,
  column,
}: Travel & { readonly column: SharedValue<number> }) {
  const drawn = useAnimatedStyle(() => {
    const pose = markerAt(trip.value, clock.value);
    return {
      // Translate first, so the scale is about the marker's own centre.
      transform: [
        {
          translateX: pose.at * column.value + (column.value - MARKER_WIDTH) / 2,
        },
        { scaleX: pose.wide },
        { scaleY: pose.tall },
      ],
    };
  });
  return (
    <Animated.View testID={TAB_BAR_MARKER_TEST_ID} pointerEvents="none" style={[s.marker, drawn]} />
  );
});

/**
 * **How much one of a column's two layers shows**: its selected layer coming in on `easeDecel` while
 * the trip is to it, over its idle layer, which stays whole under it until it is whole and only then
 * goes — two layers each half there would let the ground show through the word mid-fade. A column
 * the trip is not to is idle.
 */
function useLayerShown(index: number, layer: 'idle' | 'lit', { trip, clock }: Travel) {
  return useAnimatedStyle(() => {
    const lit = trip.value.to === index ? EASE(colourInAt(clock.value)) : 0;
    return { opacity: layer === 'lit' ? lit : lit < 1 ? 1 : 0 };
  });
}

/**
 * One of the columns, and the whole of the touch target.
 *
 * The column reaches 44pt by its own geometry — the dock's 52 inside its hairline, and a third of
 * the narrowest phone's dock across — so there is no `hit` entry here. Under a finger its icon,
 * label and badge dim to 0.7 (6.6's answer for a surface with no second fill); the marker is the
 * dock's, so it does not.
 *
 * **Its icon and its label are each two layers**, idle and selected, stacked and cross-faded by
 * the dock's clock — the selected one over the idle one — so the colour-in moves opacity and
 * nothing else. The badge stands over both.
 */
function Column<Key extends string>({
  tab,
  index,
  selected,
  onPress,
  waiting,
  trip,
  clock,
}: Travel & {
  readonly tab: TabBarTab<Key>;
  readonly index: number;
  readonly selected: boolean;
  readonly onPress: (key: Key) => void;
  readonly waiting: number | undefined;
}) {
  return (
    <Pressable
      accessible
      accessibilityRole="tab"
      accessibilityLabel={columnLabel(tab, waiting)}
      // The visible marker, shape and tone are the sighted half of this fact and never the whole.
      accessibilityState={{ selected }}
      onPress={() => onPress(tab.key)}
      style={({ pressed }) => [s.column, pressed ? s.columnPressed : null]}
    >
      {/* The glyph gets a box of its own so the badge can be positioned against the icon rather
          than against the column: a column is 98pt wide and the mark it belongs to is 18. */}
      <View style={s.glyphBox}>
        <GlyphLayers glyph={tab.glyph} index={index} trip={trip} clock={clock} />
        {/* 1.2's sixth coral entry: a count of things only the player can clear. */}
        {waiting === undefined ? null : (
          <CountBadge figure={waiting} tone="attend" over={theme.size.tabBar.icon} />
        )}
      </View>
      <LabelLayers text={tab.label} index={index} trip={trip} clock={clock} />
    </Pressable>
  );
}

/**
 * **A column's two glyphs**: the outline in `tabIdle`, and over it the filled one in `coral`. Each
 * fills the icon's box. Memoised on fixed inventory and shared values, like the marker.
 */
const GlyphLayers = memo(function GlyphLayers({
  glyph,
  index,
  trip,
  clock,
}: Travel & { readonly glyph: TabBarTab<string>['glyph']; readonly index: number }) {
  const idle = useLayerShown(index, 'idle', { trip, clock });
  const lit = useLayerShown(index, 'lit', { trip, clock });
  return (
    <>
      <Animated.View style={[s.glyphLayer, idle]}>
        <Glyph name={glyph.idle} color={theme.color.tabIdle} />
      </Animated.View>
      <Animated.View style={[s.glyphLayer, lit]}>
        <Glyph name={glyph.lit} color={theme.color.coral} />
      </Animated.View>
    </>
  );
});

/**
 * **A column's two labels**: in `tabIdle`, and over it in `coralInk`. The selected copy is a
 * drawing laid over the word, hidden from the reader — the column is named once, by its own label.
 */
const LabelLayers = memo(function LabelLayers({
  text,
  index,
  trip,
  clock,
}: Travel & { readonly text: string; readonly index: number }) {
  const idle = useLayerShown(index, 'idle', { trip, clock });
  const lit = useLayerShown(index, 'lit', { trip, clock });
  return (
    <View>
      <Animated.View style={idle}>
        <Label text={text} color={theme.color.tabIdle} />
      </Animated.View>
      <Animated.View
        style={[StyleSheet.absoluteFill, lit]}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Label text={text} color={theme.color.coralInk} />
      </Animated.View>
    </View>
  );
});

/**
 * A mark, never a word. Hidden from the reader on every column: the visible label already names
 * the tab, and the bolt in particular is a private-use codepoint that a screen reader would either
 * spell or skip.
 */
function Glyph({ name, color }: { name: IoniconsGlyph; color: string }) {
  return (
    <Ionicons
      name={name}
      size={theme.size.tabBar.icon}
      color={color}
      accessibilityElementsHidden
      importantForAccessibility="no"
    />
  );
}

/**
 * `tag` — 9.5/700 and **flat**. A tab label is a *name*, and `eyebrow`, the other member of
 * the 9.5 pair, is tracked: 1.43pt per character spent on air.
 *
 * Part 13 names this bar as the fixed-height exception **and** permits
 * `allowFontScaling={false}` only inside the level bar's drawn geometry, so a bounded
 * multiplier is the only mechanism left — see `theme.size.tabBar.labelMaxScale` for where its
 * number comes from, and what it now holds inside the marker.
 */
function Label({ text, color }: { text: string; color: string }) {
  return (
    <Text
      numberOfLines={1}
      maxFontSizeMultiplier={theme.size.tabBar.labelMaxScale}
      style={[s.label, { color }]}
    >
      {text}
    </Text>
  );
}

const { tabBar } = theme.size;

const s = StyleSheet.create({
  // 10.2 — **over the screen, at its foot** (10.1, ADR-0210 §3): the dock owns no layout, so every
  // screen inside the tabs draws to the bottom of the phone and ends at its reach instead.
  dock: {
    position: 'absolute',
    left: tabBar.sideInset,
    right: tabBar.sideInset,
    height: tabBar.height,
    flexDirection: 'row',
    borderRadius: theme.radius.dock,
    // `line` BOUNDS a thing, and the dock is a thing on the page.
    borderWidth: HAIRLINE,
    borderColor: theme.color.line,
  },
  shadow: theme.shadow.dock,
  glassShadow: { boxShadow: [...theme.glass.shadow] },

  // The dock's ground, inside the hairline and clipped to its inner corner — a blur drawn past
  // the corner would square it off.
  material: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: theme.radius.dock - HAIRLINE,
    overflow: 'hidden',
  },
  opaque: { backgroundColor: theme.color.surface },
  glass: { ...StyleSheet.absoluteFillObject, backgroundColor: theme.color.glass },
  // The glass's bright edge, a 1pt `surface` line inside the hairline. On the opaque dock it is
  // white on white, which is harmless.
  rim: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: theme.radius.dock - HAIRLINE,
    borderWidth: HAIRLINE,
    borderColor: theme.color.surface,
  },

  // Over the glass and under the words. Centred top to bottom inside the hairline; across, the
  // dock places it under the lit column.
  marker: {
    position: 'absolute',
    left: 0,
    top: (tabBar.height - 2 * HAIRLINE - tabBar.marker.height) / 2,
    width: tabBar.marker.width,
    height: tabBar.marker.height,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.coralSoft,
  },

  column: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    // The icon over its label, the smallest step on the 3pt grid between them.
    gap: theme.space.xxs,
  },
  columnPressed: { opacity: 0.7 },

  // The icon's own box. `visible` because Android clips a child drawn outside its parent, and a
  // clipped badge is a count disappearing on one platform.
  glyphBox: {
    width: tabBar.icon,
    height: tabBar.icon,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
  // One of the icon's two layers, filling its box with the glyph centred in it.
  glyphLayer: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },

  label: { ...theme.type.tag, textAlign: 'center' },
});
