/**
 * The tab bar, per design-system 10.2 — **Home · ⚡Play · You**, equal columns with ⚡Play raised
 * at the centre, and five with **Classic play**.
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
 * **The bar ships three of the five** — Home · ⚡Play · You — and draws the other two, Players
 * and Chats, only with **Classic play**
 * ([ADR-0189](../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6).
 * That is a switch and not a list: the caller says whether Classic play is on, and which columns
 * that means is decided here, so a caller still cannot pass tabs. The cap stays derived from the
 * five, because five is the narrowest the columns ever get — three are wider, and the words fit
 * them with room to spare.
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
 * ## Two badges, on Home and on Chats, and on no other column
 *
 * **The badge inventory is fixed at two, one per column, for the reason the glyph inventory is
 * fixed at five** ([#326](https://github.com/Raketa02/Raketa/issues/326)). Each counts things
 * only you can clear, which is what makes it an obligation a player can discharge rather than a
 * number that nags. **Home's** counts the games that need you — a result to enter or confirm, a
 * seat open in your game ([#550](https://github.com/Raketa02/Raketa/issues/550)). **Chats'**
 * counts unanswered challenges **addressed to you**, and it is Classic play's: it goes with its
 * column, whatever it is handed.
 *
 * **Each is a named prop and never a hook.** `shared/ui` importing a feature hook inverts the
 * dependency ([ADR-0009](../../../../docs/adr/0009-feature-first-clean-architecture-frontends.md))
 * and would give *"the drawn object only"* a network call. And they are `gamesNeedingYou` and
 * `challengesWaiting` rather than a generic `badges?: Partial<Record<TabBarKey, number>>`, which
 * is the glyph argument in a new costume: a caller that can badge any tab can badge You.
 *
 * **The argument that kept the bar bare survives as the test, and it still bites.** The count
 * this product already had was the player's own outstanding yeses, drawn as a **sentence** on
 * the deck's ending ([6.3](../../../docs/design-system.md#63-segmented-control)'s segment
 * carried it as *Match me · 3* until that was struck for reading as a count of waiting cards).
 * It is **filtered by the sport on screen**, so that the number labels the deck it is about
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)) — and the bar has no sport, so
 * promoting *that* here would still put a number on permanent chrome that only means something
 * beside a control this bar does not draw. A challenge addressed to you is filtered by nothing,
 * and Chats is where it opens: the absence is **amended, not overturned**.
 *
 * **Nothing is drawn unless there is a count.** `undefined` is zero, in flight and refused at
 * once, and they are deliberately not told apart — a spinner or a `?` on permanent chrome is
 * anxiety with no act behind it. **No cap**: the pair rule allows at most one open challenge per
 * organiser, so a double-digit badge means something genuinely unusual and `9+` would hide the
 * one case worth seeing.
 *
 * **The count is spoken on the column's own label.** `Column` is `accessible` with an explicit
 * name, so a `<Text>` dropped inside is swallowed rather than announced — the badge is a change
 * to the **label** at least as much as to the drawing, or it does not exist for half its
 * readers. Not `accessibilityValue`: a tab has no value, and the count is part of what the tab
 * *is* right now.
 */

import Feather from '@expo/vector-icons/Feather';
import { counted } from '@/shared/formatting/counted';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { theme } from './theme';

/** A glyph name Feather actually ships. Not a `string`, and not behind a cast. */
type FeatherGlyph = keyof typeof Feather.glyphMap;

export type TabBarKey = 'home' | 'players' | 'play' | 'chats' | 'you';

export interface TabBarTab<Key extends string = TabBarKey> {
  readonly key: Key;
  readonly label: string;
  readonly glyph: FeatherGlyph;
}

/**
 * The five, in order — every column the bar can draw. **The first is Home**, today's Now renamed
 * whole — key, label and screen, the route staying `/` ([#550](https://github.com/Raketa02/Raketa/issues/550)):
 * your games from the moment they fill. It always drew `home`, which beat the calendar and the
 * clock because it claims nothing that is not built, and now it is also the tab's name. **The
 * second column is Players and draws
 * `users`** — the deck lives there, one person at a time, and `user` is You's
 * ([ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1). It was Around, drawn with `map-pin` after `radar` was refused for a tab with no scan
 * behind it (ADR-0135); the family finding stands, and `radar` is still not drawn, because the
 * Radar is a pane inside Players and not a tab.
 *
 * `labelMaxScale` is derived from these exact words. Adding a sixth, or a longer one, is a
 * change to `tabBarLabelCap.test.ts`'s answer before it is a change to this list — and
 * *Players* is the longest of the five, which is what moved the cap when Around retired.
 */
export const TAB_BAR_TABS = [
  { key: 'home', label: 'Home', glyph: 'home' },
  { key: 'players', label: 'Players', glyph: 'users' },
  { key: 'play', label: 'Play', glyph: 'zap' },
  { key: 'chats', label: 'Chats', glyph: 'message-circle' },
  { key: 'you', label: 'You', glyph: 'user' },
] as const satisfies readonly TabBarTab[];

/**
 * **The two columns only Classic play draws** — the old loop's Players deck and Chats tab
 * ([ADR-0189](../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §6).
 * They come back together and where they were, so the bar is the five with these two left out.
 */
export const CLASSIC_PLAY_TABS: readonly TabBarKey[] = ['players', 'chats'];

/** The columns the bar draws: the five with Classic play, and without it Home · ⚡Play · You. */
function columnsOf(classicPlay: boolean): readonly TabBarTab[] {
  return classicPlay
    ? TAB_BAR_TABS
    : TAB_BAR_TABS.filter((tab) => !CLASSIC_PLAY_TABS.includes(tab.key));
}

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
  /**
   * Which of the five is showing. Play stays active for every screen inside Play. A column the
   * bar does not draw — Chats, reached from a Home card's chat door without Classic play — lights
   * nothing, rather than a neighbour the player is not on.
   */
  readonly active: TabBarKey;
  readonly onPress: (key: TabBarKey) => void;
  /**
   * **Whether Classic play is on** — Players and Chats drawn in their places. The caller reads the
   * flag; the bar decides which columns that means.
   */
  readonly classicPlay: boolean;
  /**
   * The games that need you — the badge on Home.
   *
   * Absent draws nothing, and absent covers zero, still loading and failed alike. The caller
   * folds those three together, so this prop is *a count to draw* rather than a number the bar
   * has to decide about.
   */
  readonly gamesNeedingYou?: number;
  /**
   * Unanswered challenges addressed to you — the badge on Chats, drawn only with Classic play.
   * Absent draws nothing, as Home's does.
   */
  readonly challengesWaiting?: number;
}

/** What every column is: one of the five, whether it is the one you are on, and the report. */
interface ColumnProps<Key extends string = TabBarKey> {
  readonly tab: TabBarTab<Key>;
  readonly selected: boolean;
  readonly onPress: (key: Key) => void;
}

/**
 * A count, drawn on the column's glyph and spoken in its name — `spoken` being the words that
 * follow the column's own label.
 *
 * It is **not** on `ColumnProps`, because ⚡Play has no badge and never will: the inventory is
 * fixed at two, and a prop the raised column inherits and ignores is the first step to a third.
 */
interface Badged {
  readonly badge?: { readonly count: number; readonly spoken: string };
}

export function TabBar({
  active,
  onPress,
  classicPlay,
  gamesNeedingYou,
  challengesWaiting,
}: TabBarProps) {
  // The bar owns the bottom safe-area inset, and it owns it here rather than taking it as a
  // prop: a CTA sitting above the bar must not apply it too, and an inset applied twice is
  // 34pt of nothing on a notched device.
  const insets = useSafeAreaInsets();

  // Each count is spoken through `counted()` like every other in the app, because a market with
  // real plural rules has to have one function to change rather than every sentence that counts
  // something. The words live here, beside the labels they follow: this is chrome copy over a
  // count the client derives ([#326](https://github.com/Raketa02/Raketa/issues/326) §9).
  const badges: Readonly<Partial<Record<TabBarKey, Badged['badge']>>> = {
    home:
      gamesNeedingYou === undefined
        ? undefined
        : {
            count: gamesNeedingYou,
            spoken: `${counted(gamesNeedingYou, 'game', 'games')} waiting on you`,
          },
    chats:
      challengesWaiting === undefined
        ? undefined
        : {
            count: challengesWaiting,
            spoken: `${counted(challengesWaiting, 'challenge', 'challenges')} waiting`,
          },
  };

  return (
    <View style={[s.bar, { paddingBottom: theme.space.md + insets.bottom }]}>
      {columnsOf(classicPlay).map((tab) =>
        tab.key === 'play' ? (
          <PlayTab key={tab.key} tab={tab} selected={active === tab.key} onPress={onPress} />
        ) : (
          <FlankTab
            key={tab.key}
            tab={tab}
            selected={active === tab.key}
            onPress={onPress}
            badge={badges[tab.key]}
          />
        ),
      )}
    </View>
  );
}

/**
 * **The administrator area's bar** — two columns, **Groups · You**, drawn in this bar's style
 * (club mock 17; [#516](https://github.com/Raketa02/Raketa/issues/516)).
 *
 * **A second fixed inventory, not a caller's list.** ADR-0135's argument stands whole: a bar that
 * took its tabs from a caller could grow a sixth without argument. The administrator's side of the
 * account is a second surface with its own two places, so it gets its own inventory here, beside
 * the five — the family inherited (Feather, one weight, selection in tone alone), nothing else.
 * `users` is *Groups*: the crowds the administrator runs. Players draws it on the player's bar, and
 * the two bars are never on screen together, so it names one thing wherever it is seen. `user` is
 * *You* on both.
 *
 * Two flank columns and no disc, so the bar is shorter than the player's by the disc's height; the
 * toast's clearance is the player's bar's, which clears this one too (9.2). No badge: *N waiting*
 * is on the group's card, where it can be answered.
 */
export type AdministratorTabBarKey = 'groups' | 'you';

export const ADMINISTRATOR_TAB_BAR_TABS = [
  { key: 'groups', label: 'Groups', glyph: 'users' },
  { key: 'you', label: 'You', glyph: 'user' },
] as const satisfies readonly TabBarTab<AdministratorTabBarKey>[];

export interface AdministratorTabBarProps {
  /** Which of the two is showing. Groups stays active for every screen inside Groups. */
  readonly active: AdministratorTabBarKey;
  readonly onPress: (key: AdministratorTabBarKey) => void;
}

export function AdministratorTabBar({ active, onPress }: AdministratorTabBarProps) {
  // The bottom inset is the bar's, as it is on the player's (10.1).
  const insets = useSafeAreaInsets();

  return (
    <View style={[s.bar, { paddingBottom: theme.space.md + insets.bottom }]}>
      {ADMINISTRATOR_TAB_BAR_TABS.map((tab) => (
        <FlankTab key={tab.key} tab={tab} selected={active === tab.key} onPress={onPress} />
      ))}
    </View>
  );
}

function FlankTab<Key extends string>({
  tab,
  selected,
  onPress,
  badge,
}: ColumnProps<Key> & Badged) {
  const tone = selected ? theme.color.ink : theme.color.muted;

  return (
    <Column tab={tab} selected={selected} onPress={onPress} badge={badge} dimOnPress>
      {/* The glyph gets a box of its own so the badge can be positioned against the icon
          rather than against the column: a column is 64pt wide and the mark it belongs to
          is 16. */}
      <View style={s.glyphBox}>
        <Glyph name={tab.glyph} size={theme.size.tabIcon} color={tone} />
        {badge === undefined ? null : <Badge count={badge.count} />}
      </View>
      <Label text={tab.label} color={tone} />
    </Column>
  );
}

/**
 * The count, as a mark — **`coralInk` filled with a white digit at 5,89**.
 *
 * White on `coral` is 3,89, the one pairing Rule C refuses outright and the exact correction
 * the ⚡Play disc three columns away already took. The digit is mono and tabular, so 1 -> 2 does
 * not reflow the column, and there is no cap.
 *
 * It is **out of the layout**, like the active ring and for the same reason: the bar's height
 * must not change because a challenge arrived. It rises `badgeRise` above the icon — the 4pt the
 * ring already spends out of the bar's 6pt top padding — and sits back over the glyph's right
 * edge by the smallest step on the grid, so it reads as attached to the mark rather than
 * floating beside it.
 *
 * **It announces nothing.** The count is on the column's own `accessibilityLabel`, because
 * `Column` is `accessible` and a `<Text>` inside it is swallowed — so a badge that announced
 * itself here would be either silent or a second reading of one number.
 */
function Badge({ count }: { readonly count: number }) {
  return (
    <View
      style={s.badge}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={s.badgeCount} maxFontSizeMultiplier={theme.size.tabBar.labelMaxScale}>
        {count}
      </Text>
    </View>
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
 * One of the columns, and the whole of the touch target.
 *
 * The column reaches 44pt by its own geometry — the Play column is 30 + 3 + 12 = 45 inside
 * the bar's padding, and every column stretches to it — so there is no `hit` entry here.
 * That is the availability cell's situation rather than the chip's.
 */
function Column<Key extends string>({
  tab,
  selected,
  onPress,
  badge,
  dimOnPress = false,
  children,
}: ColumnProps<Key> &
  Badged & {
    /** 6.6's answer for a surface with no second fill. The disc has one, so it does not dim. */
    readonly dimOnPress?: boolean;
    readonly children: ReactNode | ((state: { pressed: boolean }) => ReactNode);
  }) {
  return (
    <Pressable
      accessible
      accessibilityRole="tab"
      accessibilityLabel={badge === undefined ? tab.label : `${tab.label}, ${badge.spoken}`}
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

  // The icon's own box. `visible` for the disc's reason: Android clips a child drawn outside
  // its parent, and a clipped badge is a count disappearing on one platform.
  glyphBox: {
    width: theme.size.tabIcon,
    height: theme.size.tabIcon,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
  },
  badge: {
    position: 'absolute',
    // Up by the ring's own overhang, and back over the glyph's right edge by the smallest
    // step on the grid — so the badge belongs to the mark rather than sitting beside it.
    bottom: theme.size.tabIcon - theme.size.tabBar.badge + theme.size.tabBar.badgeRise,
    left: theme.size.tabIcon - theme.space.xxs,
    height: theme.size.tabBar.badge,
    minWidth: theme.size.tabBar.badge,
    paddingHorizontal: theme.space.xxs,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
    // 6.1 `primary`'s fill: white on `coralInk` is 5.89, where white on `coral` is 3.89.
    backgroundColor: theme.color.coralInk,
  },
  badgeCount: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.surface,
    // The role's own line height is 17 inside an 18pt box; centring is the box's job, and the
    // text box must not add its own leading on top of it.
    lineHeight: theme.size.tabBar.badge,
  },

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
