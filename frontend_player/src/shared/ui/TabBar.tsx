/**
 * The tab bar, per design-system 10.2 — five equal columns with ⚡Play raised at the centre.
 *
 * **The drawn object only.** It takes the active tab and a press handler and knows nothing
 * about routes, stacks or which screen is mounted; the shell that wires it is a separate
 * ticket, and the one navigation rule that ticket must not lose — `<Tabs>` remembers each
 * tab's stack by default, which fails *back goes where I came from* silently — is a fact
 * about the navigator, not about the bar.
 *
 * ## The inventory is fixed, and it lives here
 *
 * Five tabs, five Feather glyphs, one family
 * ([ADR-0135](../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)).
 * It is the design system's list rather than the shell's: the ADR's words are *"the family
 * is fixed and the inventory is these five … a sixth glyph on a sixth surface is a fresh
 * question that inherits the family and nothing else, never a licence to sprinkle."* A
 * caller that could pass its own tabs is a caller that could add a sixth without argument —
 * and it would silently invalidate `labelMaxScale`, which is derived from exactly these five
 * words in exactly this many columns.
 *
 * ## Feather, and selection in tone alone
 *
 * `ink` selected, `muted` resting — **3.25:1**, and a lightness difference rather than a hue
 * one, so it survives greyscale and a red-green deficiency. The glyph is the same glyph in
 * both states. Feather is a font with one weight and no filled counterparts, and that
 * limitation costs nothing here precisely because the tone channel is already sufficient: a
 * family with outline/filled pairs would put a second state channel on top of a working one,
 * which is the thing #227 already refused once in writing for the disc — *the ring carries
 * the state, not the shadow.*
 *
 * Every name is typed against Feather's own `glyphMap`, so a glyph absent from
 * `@expo/vector-icons@14.0.4` is a compile error rather than a blank column nobody notices
 * at 16pt.
 *
 * ## The bolt is a glyph, not a text character
 *
 * `U+26A1` carries `Emoji_Presentation=Yes`, so `<Text>⚡</Text>` requests *colour emoji* and
 * a `color` style has nothing to apply to — the one mark in the bar whose colour this app
 * would not control, on the disc whose whole argument is a **white** mark. Feather `zap` is a
 * font icon: `color` is a real prop, and white is white.
 *
 * ## The disc is 6.1 `primary` in a squircle
 *
 * Not a new colour treatment: `coralInk` fill, white mark, brightening to `coral` on press.
 * The prototype's white-on-`coral` was **3.89:1**, the exact pairing Rule C refuses outright.
 * Taking the button's variant means the press state arrives free and no colour is added.
 *
 * The active state is a 2pt `coral` ring set 2pt clear of the disc, and the gap is the bar's
 * own `surface`, so there is no collar to token and coral reads 3.89:1 on **both** edges of
 * the stroke — clearing 3:1 for a non-text indicator, which volt cleared on neither (1.25:1
 * against the bar, 2.86:1 against the disc; 2.2 as amended, measured rather than asserted).
 * **The ring is absolutely positioned**: a bar that grew 8pt on arriving in Play would move
 * the four things that did not change in order to announce the one that did.
 *
 * ## What is deliberately absent
 *
 * **No badge.** The one count this product has is *Match me · 3*, and it belongs to the
 * segmented control inside the Play screen ([6.3](../../../docs/design-system.md#63-segmented-control)).
 * It is **filtered by the sport on screen**, so that the number labels the deck it sits above
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)) — and the bar has no sport, so
 * promoting it here would put a number on permanent chrome that only means something beside a
 * control this bar does not draw, on a tab whose own rule is that it always opens somewhere
 * else.
 */

import Feather from '@expo/vector-icons/Feather';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from './theme';

/** A glyph name Feather actually ships. Not a `string`, and not behind a cast. */
type FeatherGlyph = keyof typeof Feather.glyphMap;

export type TabBarKey = 'now' | 'around' | 'play' | 'chats' | 'you';

export interface TabBarTab {
  readonly key: TabBarKey;
  readonly label: string;
  readonly glyph: FeatherGlyph;
}

/**
 * The five, in order. `home` and `map-pin` beat the calendar, the clock and `radar`: Now has
 * no plans, no bookings and no courts behind it, and a calendar glyph would announce a
 * scheduling surface nothing is building — `home` claims nothing that is not built, and
 * `map-pin` says *near here* and stops.
 *
 * `labelMaxScale` is derived from these exact words. Adding a sixth, or a longer one, is a
 * change to `tabBarLabelCap.test.ts`'s answer before it is a change to this list.
 */
export const TAB_BAR_TABS = [
  { key: 'now', label: 'Now', glyph: 'home' },
  { key: 'around', label: 'Around', glyph: 'map-pin' },
  { key: 'play', label: 'Play', glyph: 'zap' },
  { key: 'chats', label: 'Chats', glyph: 'message-circle' },
  { key: 'you', label: 'You', glyph: 'user' },
] as const satisfies readonly TabBarTab[];

/**
 * The bar's height at the default text size, **excluding** the bottom safe-area inset.
 *
 * Derived from the same tokens the stylesheet below lays the bar out from — the hairline, the
 * two paddings, the ⚡Play disc (which is the tallest thing in a column, not the 16pt icon
 * box) and the label — so it cannot drift from the bar it describes. It exists because
 * [9.2](../../../docs/design-system.md#92-toast) positions the toast *above the tab bar*, and
 * the alternative was the toast holding a copy of these five numbers.
 *
 * **The default size, and a floor rather than a promise.** `labelMaxScale` lets Dynamic Type
 * grow the labels, so a bar on a phone set large is taller than this; the toast clearing the
 * default is what 9.2 asks for, and a toast that measured the bar would be an overlay
 * depending on a screen having one.
 */
export const TAB_BAR_HEIGHT =
  1 +
  theme.space.xs +
  theme.size.fab +
  theme.space.xxs +
  theme.type.tag.lineHeight +
  theme.space.md;

export interface TabBarProps {
  /** Which of the five is showing. Play stays active for every screen inside Play. */
  readonly active: TabBarKey;
  readonly onPress: (key: TabBarKey) => void;
}

/** What every column is: one of the five, whether it is the one you are on, and the report. */
interface ColumnProps {
  readonly tab: TabBarTab;
  readonly selected: boolean;
  readonly onPress: (key: TabBarKey) => void;
}

export function TabBar({ active, onPress }: TabBarProps) {
  // The bar owns the bottom safe-area inset, and it owns it here rather than taking it as a
  // prop: a CTA sitting above the bar must not apply it too, and an inset applied twice is
  // 34pt of nothing on a notched device.
  const insets = useSafeAreaInsets();

  return (
    <View style={[s.bar, { paddingBottom: theme.space.md + insets.bottom }]}>
      {TAB_BAR_TABS.map((tab) =>
        tab.key === 'play' ? (
          <PlayTab key={tab.key} tab={tab} selected={active === tab.key} onPress={onPress} />
        ) : (
          <FlankTab key={tab.key} tab={tab} selected={active === tab.key} onPress={onPress} />
        ),
      )}
    </View>
  );
}

function FlankTab({ tab, selected, onPress }: ColumnProps) {
  const tone = selected ? theme.color.ink : theme.color.muted;

  return (
    <Column tab={tab} selected={selected} onPress={onPress} dimOnPress>
      <Glyph name={tab.glyph} size={theme.size.tabIcon} color={tone} />
      <Label text={tab.label} color={tone} />
    </Column>
  );
}

function PlayTab({ tab, selected, onPress }: ColumnProps) {
  // The ring is `size.fab` grown by the gap and the stroke on every side, and its radius is
  // `radius.fab` grown by the same — the arithmetic is here rather than in `theme.ts` so the
  // two numbers 10.2 states stay the two numbers `theme.ts` holds.
  const { ringGap, ringStroke } = theme.size.tabBar;
  const ringSize = theme.size.fab + 2 * (ringGap + ringStroke);
  const ringRadius = theme.radius.fab + ringGap + ringStroke;

  return (
    <Column tab={tab} selected={selected} onPress={onPress}>
      {({ pressed }) => (
        <>
          <View style={s.discBox}>
            {selected ? (
              <View
                style={[s.ring, { width: ringSize, height: ringSize, borderRadius: ringRadius }]}
              />
            ) : null}
            {/* The label's tone never changes on this column: the ring is the state, and a
                second channel is free to disagree with the first. */}
            <View style={[s.disc, pressed ? s.discPressed : null]}>
              <Glyph name={tab.glyph} size={theme.size.tabBar.bolt} color={theme.color.surface} />
            </View>
          </View>
          <Label text={tab.label} color={theme.color.ink} />
        </>
      )}
    </Column>
  );
}

/**
 * One of the five columns, and the whole of the touch target.
 *
 * The column reaches 44pt by its own geometry — the Play column is 30 + 3 + 12 = 45 inside
 * the bar's padding, and every column stretches to it — so there is no `hit` entry here.
 * That is the availability cell's situation rather than the chip's.
 */
function Column({
  tab,
  selected,
  onPress,
  dimOnPress = false,
  children,
}: ColumnProps & {
  /** 6.6's answer for a surface with no second fill. The disc has one, so it does not dim. */
  readonly dimOnPress?: boolean;
  readonly children: ReactNode | ((state: { pressed: boolean }) => ReactNode);
}) {
  return (
    <Pressable
      accessible
      accessibilityRole="tab"
      accessibilityLabel={tab.label}
      // The visible tone is the sighted half of this fact and never the whole of it.
      accessibilityState={{ selected }}
      onPress={() => onPress(tab.key)}
      style={({ pressed }) => [s.column, dimOnPress && pressed ? s.columnPressed : null]}
    >
      {children}
    </Pressable>
  );
}

/**
 * A mark, never a word. Hidden from the reader on every column: the visible label already
 * names the tab, and the bolt in particular is a private-use codepoint that a screen reader
 * would either spell or skip.
 */
function Glyph({ name, size, color }: { name: FeatherGlyph; size: number; color: string }) {
  return (
    <Feather
      name={name}
      size={size}
      color={color}
      accessibilityElementsHidden
      importantForAccessibility="no"
    />
  );
}

/**
 * `tag` — 9.5/700 and **flat**. A tab label is a *name*, and `eyebrow`, the other member of
 * the 9.5 pair, is tracked: 1.43pt per character spends 8.6pt of a 64pt column on air.
 *
 * Part 13 names this bar as the fixed-height exception **and** permits
 * `allowFontScaling={false}` only inside the level bar's drawn geometry, so a bounded
 * multiplier is the only mechanism left. It is derived rather than picked — see
 * `theme.size.tabBar.labelMaxScale`.
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

const s = StyleSheet.create({
  // 10.2 — equal columns, paddingTop 6, paddingBottom 12 + the bottom inset.
  bar: {
    flexDirection: 'row',
    backgroundColor: theme.color.surface,
    borderTopWidth: 1,
    // `line` BOUNDS a thing, and the bar is bounded against the screen above it.
    borderTopColor: theme.color.line,
    paddingTop: theme.space.xs,
  },
  column: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    // 10.2 sets the bar's paddings and the icon box and stops. The gap is the smallest step
    // on the 3pt grid rather than a fourth number invented beside it.
    gap: theme.space.xxs,
  },
  columnPressed: { opacity: 0.7 },

  discBox: {
    width: theme.size.fab,
    height: theme.size.fab,
    alignItems: 'center',
    justifyContent: 'center',
    // The ring is 4pt larger than this box on every side, which is the whole point — the box
    // is the LAYOUT and the ring is not in it. Declared rather than left to the default,
    // because Android is where a child drawn outside its parent gets clipped, and a clipped
    // ring is the active state disappearing on one platform with nothing to see in a test.
    overflow: 'visible',
  },
  // Absolute, and centred by the box rather than by an inset: entering Play must not change
  // the bar's height. The 4pt it takes above the disc comes out of the bar's own 6pt top
  // padding, leaving 2pt of clearance to the hairline.
  ring: {
    position: 'absolute',
    borderWidth: theme.size.tabBar.ringStroke,
    borderColor: theme.color.coral,
  },
  disc: {
    width: theme.size.fab,
    height: theme.size.fab,
    borderRadius: theme.radius.fab,
    alignItems: 'center',
    justifyContent: 'center',
    // 6.1 `primary`: the disc is that button in a squircle, so white on `coralInk` rather
    // than the prototype's white on `coral` at 3.89:1.
    backgroundColor: theme.color.coralInk,
    ...theme.shadow.fab,
  },
  discPressed: { backgroundColor: theme.color.coral },

  label: { ...theme.type.tag, textAlign: 'center' },
});
