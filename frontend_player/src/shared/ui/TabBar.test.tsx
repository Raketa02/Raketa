/**
 * The bar, asserted through what a player, a finger and a screen reader can each observe — and,
 * past those, through its drawing.
 *
 * Tabs with names and states are ordinary queries, and the first two suites stay there. **The
 * rest are the declared exception**: the dock, its glass, the selection marker, the glyphs and the
 * pressed dim are drawings with no accessible name, and they are exactly the rules this bar loses
 * silently — a dock that grew with its label would move every screen's foot, a selected label in
 * `coral` would be 3.38:1 on the marker, and a glyph name Ionicons does not ship would be a blank
 * column nobody notices at 18pt (10.2, ADR-0210 §2, §4, §5, #883).
 */

import Ionicons from '@expo/vector-icons/Ionicons';
import { fireEvent, render, screen } from '@testing-library/react-native';
import { BlurView } from 'expo-blur';
import {
  Dimensions,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
import { SafeAreaProvider, type Metrics } from 'react-native-safe-area-context';

import {
  ADMINISTRATOR_TAB_BAR_TABS,
  AdministratorTabBar,
  TabBar,
  TAB_BAR_MARKER_TEST_ID,
  TAB_BAR_TABS,
  TAB_BAR_TEST_ID,
  type TabBarKey,
  type TabBarProps,
} from './TabBar';
import { theme } from './theme';

/** A notched phone: its bottom inset is larger than the dock's least lift, so the inset leads. */
const NOTCHED: Metrics = {
  frame: { x: 0, y: 0, width: 320, height: 693 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

/** An Android phone on SDK 52, which draws no edge to edge: no bottom inset at all. */
const NO_INSET: Metrics = {
  frame: { x: 0, y: 0, width: 320, height: 693 },
  insets: { top: 24, left: 0, right: 0, bottom: 0 },
};

const { tabBar } = theme.size;

/** A node as a query hands it back. */
type ReactTestInstance = ReturnType<typeof screen.getByTestId>;

/** The dock's hairline, which the columns and the marker are laid inside. */
const HAIRLINE = 1;

/** The bar as it ships — **Home · Play · You**. */
function renderBar(
  active: TabBarKey,
  props: Partial<Omit<TabBarProps, 'active'>> = {},
  metrics: Metrics = NOTCHED,
) {
  return render(
    <SafeAreaProvider initialMetrics={metrics}>
      <TabBar active={active} onPress={jest.fn()} {...props} />
    </SafeAreaProvider>,
  );
}

/** Every column the bar drew, by the name it speaks. */
function columns(): string[] {
  return screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel);
}

/** A column's `Pressable`, found by the name it speaks rather than by where it sits. */
function column(name: string) {
  const found = screen
    .UNSAFE_getAllByType(Pressable)
    .find((node) => node.props.accessibilityLabel === name);
  if (!found) throw new Error(`the bar drew no ${name} column`);
  return found;
}

/** A column's style callback, at rest or under a finger. */
function columnStyle(name: string, pressed: boolean): ViewStyle {
  return StyleSheet.flatten(column(name).props.style({ pressed }));
}

const flat = (style: unknown): ViewStyle & TextStyle =>
  StyleSheet.flatten(style as ViewStyle & TextStyle) ?? {};

/** The dock's own frame. */
const dock = () => flat(screen.getByTestId(TAB_BAR_TEST_ID).props.style);

/** The selection marker's drawing. */
const marker = () => flat(screen.getByTestId(TAB_BAR_MARKER_TEST_ID).props.style);

/** Where the marker's left edge stands inside the dock's hairline — its offset. */
function markerLeft(): number {
  const style = marker();
  const shift = (style.transform as { translateX?: number }[] | undefined)?.find(
    (step) => step.translateX !== undefined,
  )?.translateX;
  return (typeof style.left === 'number' ? style.left : 0) + (shift ?? 0);
}

/** A column's width as the dock lays it out: the window less both side insets and the hairlines. */
const columnOf = (count: number) =>
  (Dimensions.get('window').width - 2 * tabBar.sideInset - 2 * HAIRLINE) / count;

/** Which column the marker is centred in — `undefined` when it is centred in none. */
function markerColumn(count: number): number | undefined {
  const width = columnOf(count);
  const centre = markerLeft() + Number(marker().width) / 2;
  const at = Math.floor(centre / width);
  return Math.abs(centre - (at + 0.5) * width) < 0.01 ? at : undefined;
}

/** Every Ionicons glyph the bar drew, in order. */
const glyphs = () => screen.UNSAFE_queryAllByType(Ionicons);

/** A column's glyph, by the column's name. */
function glyphOf(name: string) {
  const found = column(name).findByType(Ionicons);
  return found.props as { name: string; color: string; size: number };
}

/** A column's label, by its text. */
const labelColour = (text: string) => flat(screen.getByText(text).props.style).color;

/** A translucent token's alpha — its last channel — without spelling the colour out here. */
const alphaOf = (token: string) => Number(token.split(',').pop()?.replace(')', ''));

/** Home's badge, if the bar was handed a count. */
function badge(): ViewStyle | undefined {
  return screen
    .UNSAFE_queryAllByType(View)
    .map((node) => flat(node.props.style))
    .find(
      (style) => style.position === 'absolute' && style.backgroundColor === theme.color.coralInk,
    );
}

/**
 * **Home · Play · You, and nothing else** — the old loop's Players and Chats columns went with
 * that loop ([#576](https://github.com/Raketa02/Raketa/issues/576)), and no switch brings them back.
 */
describe('what the bar offers', () => {
  it('is Home, Play and You, in that order', () => {
    renderBar('home');

    expect(columns()).toEqual(['Home', 'Play', 'You']);
  });

  it('reports which one was pressed', () => {
    const onPress = jest.fn();
    renderBar('home', { onPress });

    fireEvent.press(screen.getByRole('tab', { name: 'You' }));

    expect(onPress).toHaveBeenCalledWith('you');
  });

  it('reports Home by its own key', () => {
    const onPress = jest.fn();
    renderBar('you', { onPress });

    fireEvent.press(screen.getByRole('tab', { name: 'Home' }));

    expect(onPress).toHaveBeenCalledWith('home');
  });

  it('reports a press on the tab that is already active — it decides nothing itself', () => {
    // Play always opens its root, whichever Play screen was last used, so a bar that swallowed
    // the press of the active tab would take that rule away from the shell.
    const onPress = jest.fn();
    renderBar('play', { onPress });

    fireEvent.press(screen.getByRole('tab', { name: 'Play' }));

    expect(onPress).toHaveBeenCalledWith('play');
  });
});

describe('what the bar announces', () => {
  it('announces the active tab as selected', () => {
    renderBar('you');

    expect(screen.getByRole('tab', { name: 'You', selected: true })).toBeTruthy();
  });

  it('announces the other two as not selected, rather than as silence', () => {
    renderBar('you');

    for (const name of ['Home', 'Play']) {
      expect(screen.getByRole('tab', { name, selected: false })).toBeTruthy();
    }
  });

  it('hides every glyph from the reader — the visible label already names the tab', () => {
    renderBar('home');

    expect(glyphs()).toHaveLength(3);
    for (const glyph of glyphs()) {
      expect(glyph.props.accessibilityElementsHidden).toBe(true);
      expect(glyph.props.importantForAccessibility).toBe('no');
    }
  });

  it('draws no count when it is handed none', () => {
    renderBar('play');

    for (const text of screen.UNSAFE_queryAllByType(Text)) {
      expect(String(text.props.children)).not.toMatch(/\d/);
    }
  });
});

/**
 * **The dock** (10.2, ADR-0210 §2): 54 tall, 12 in from each side, lifted the larger of 12 and the
 * bottom inset, at `radius.dock`, bounded by a `line` hairline, and lifted off the page by
 * `shadow.dock`. The bottom inset is the lift's: the dock pads itself with nothing.
 */
describe('the dock', () => {
  it('floats 12 in from each side, 54 tall, its corners at 22, bounded by a hairline', () => {
    renderBar('home');

    expect(dock()).toMatchObject({
      position: 'absolute',
      left: tabBar.sideInset,
      right: tabBar.sideInset,
      height: tabBar.height,
      borderRadius: theme.radius.dock,
      borderWidth: HAIRLINE,
      borderColor: theme.color.line,
    });
    expect(tabBar).toMatchObject({ height: 54, sideInset: 12, lift: 12 });
    expect(theme.radius.dock).toBe(22);
  });

  it('rests on a notched phone’s safe-area line — the inset is larger than the least lift', () => {
    renderBar('home', {}, NOTCHED);

    expect(dock().bottom).toBe(NOTCHED.insets.bottom);
    expect(dock().paddingBottom).toBeUndefined();
  });

  it('stands 12 clear of the foot on a phone with no inset, as it does of either side', () => {
    renderBar('home', {}, NO_INSET);

    expect(dock().bottom).toBe(tabBar.lift);
  });

  it('is the same height in every state and with a count — nothing on it is in its layout', () => {
    renderBar('home');
    const atHome = dock();

    screen.unmount();
    renderBar('play', { gamesNeedingYou: 12 });

    expect(dock()).toEqual(atHome);
  });

  it('takes the deck card’s shadow, in the retired disc’s slot', () => {
    expect(theme.shadow.dock).toEqual(theme.shadow.deckCard);
    expect(theme.shadow).not.toHaveProperty('fab');
    expect(Object.keys(theme.shadow).filter((name) => name !== 'textOnMedia')).toHaveLength(7);
  });
});

/**
 * **The material** (ADR-0210 §2, §7 as amended by the A32 spike, #880): the iPhone draws
 * `color.glass` over `expo-blur` at the strength the spike recorded, and Android draws the glass
 * only if the theme's switch says so — today it doesn't, so its dock is opaque `surface`. Either
 * way a 1pt `surface` rim runs inside the hairline.
 */
describe('the material', () => {
  /** The fill that is the dock's ground — glass, or `surface` where no glass is drawn. */
  function ground(): string | undefined {
    const fills = screen
      .UNSAFE_queryAllByType(View)
      .map((node) => flat(node.props.style).backgroundColor)
      .filter((fill) => fill === theme.color.glass || fill === theme.color.surface);
    return fills[0] as string | undefined;
  }

  function rim(): ViewStyle | undefined {
    return screen
      .UNSAFE_queryAllByType(View)
      .map((node) => flat(node.props.style))
      .find((style) => style.borderColor === theme.color.surface);
  }

  /** What a case replaced — put back after it, pass or fail, since the config restores nothing. */
  const replaced: { restore: () => void }[] = [];
  const onPlatform = (os: 'ios' | 'android') =>
    replaced.push(jest.replaceProperty(Platform, 'OS', os));

  afterEach(() => {
    while (replaced.length > 0) replaced.pop()?.restore();
  });

  it('is glass on an iPhone: 88% white over a light blur at 100', () => {
    onPlatform('ios');
    renderBar('home');

    const [blur] = screen.UNSAFE_getAllByType(BlurView);
    expect(blur?.props).toMatchObject({ intensity: theme.glass.blur, tint: 'light' });
    expect(theme.glass.blur).toBe(100);
    expect(ground()).toBe(theme.color.glass);
    // 88% white: what holds idle words at 4.53:1 over Home's dark game card (ADR-0210 §2).
    expect(theme.color.glass).not.toBe(theme.color.surface);
    expect(alphaOf(theme.color.glass)).toBe(0.88);
  });

  it('shadows the iPhone’s glass outside the dock only, never from its pixels', () => {
    onPlatform('ios');
    renderBar('home');

    expect(dock().boxShadow).toEqual(theme.glass.shadow);
    expect(dock().shadowOpacity).toBeUndefined();
    expect(dock().elevation).toBeUndefined();
  });

  it('is opaque `surface` on Android while the switch is off, and draws no blur at all', () => {
    onPlatform('android');
    renderBar('home');

    expect(theme.glass.android).toBe(false);
    expect(screen.UNSAFE_queryAllByType(BlurView)).toHaveLength(0);
    expect(ground()).toBe(theme.color.surface);
    // The opaque dock casts `shadow.dock`; its `elevation` draws as it is there (the spike's T3).
    expect(dock()).toMatchObject(theme.shadow.dock);
    expect(dock().boxShadow).toBeUndefined();
  });

  it('draws Android’s glass when the switch is on, shadowed outside the dock only', () => {
    onPlatform('android');
    replaced.push(jest.replaceProperty(theme.glass as { android: boolean }, 'android', true));
    renderBar('home');

    const [blur] = screen.UNSAFE_getAllByType(BlurView);
    expect(blur?.props).toMatchObject({
      intensity: theme.glass.blur,
      experimentalBlurMethod: 'dimezisBlurView',
    });
    expect(ground()).toBe(theme.color.glass);
    // `elevation` would show through a translucent fill; `boxShadow` is drawn outside the box.
    expect(dock().elevation).toBeUndefined();
    expect(dock().boxShadow).toEqual(theme.glass.shadow);
  });

  it('runs a 1pt `surface` rim inside the hairline, its corner the dock’s less the hairline', () => {
    renderBar('home');

    expect(rim()).toMatchObject({
      position: 'absolute',
      borderWidth: HAIRLINE,
      borderColor: theme.color.surface,
      borderRadius: theme.radius.dock - HAIRLINE,
    });
  });
});

/**
 * **The glyphs** (ADR-0210 §5): Ionicons, one family on the bar, outlined while idle and filled
 * while lit — but Play's bolt, which is filled in both states, because it is the brand's mark.
 * Feather stays everywhere else.
 */
describe('the family', () => {
  it('draws every tab from Ionicons, and every name is one Ionicons ships', () => {
    // Typed against `glyphMap` at compile time and asserted here too, because a cast is all it
    // takes for a name that does not exist to become a blank column nobody notices at 18pt.
    for (const { glyph } of [...TAB_BAR_TABS, ...ADMINISTRATOR_TAB_BAR_TABS]) {
      expect(Ionicons.glyphMap).toHaveProperty(glyph.idle);
      expect(Ionicons.glyphMap).toHaveProperty(glyph.lit);
    }
  });

  it('outlines the idle tabs and fills the lit one, with the bolt filled always', () => {
    renderBar('home');

    expect(glyphs().map((glyph) => glyph.props.name)).toEqual(['home', 'flash', 'person-outline']);

    screen.unmount();
    renderBar('you');

    expect(glyphs().map((glyph) => glyph.props.name)).toEqual(['home-outline', 'flash', 'person']);
  });

  it('draws each glyph at 18', () => {
    renderBar('play');

    expect(tabBar.icon).toBe(18);
    for (const glyph of glyphs()) {
      expect(glyph.props.size).toBe(tabBar.icon);
    }
  });

  it('never draws the bolt as U+26A1', () => {
    renderBar('play');

    // `⚡` carries `Emoji_Presentation=Yes`, so a `<Text>⚡</Text>` asks for colour emoji and the
    // `color` prop has nothing to apply to.
    for (const text of screen.UNSAFE_queryAllByType(Text)) {
      expect(String(text.props.children)).not.toContain('⚡');
    }
    expect(glyphOf('Play').name).toBe('flash');
  });
});

/**
 * **Idle and selected** (ADR-0210 §4, §5): idle is `ink` at .62, icon and label; the lit tab's
 * icon is `coral`, a mark at 3.38:1 on the marker, and its label `coralInk`, words at 5.11:1.
 */
describe('the colours', () => {
  it('draws the idle tabs’ icons and labels in `tabIdle`', () => {
    renderBar('play');

    for (const name of ['Home', 'You']) {
      expect(glyphOf(name).color).toBe(theme.color.tabIdle);
      expect(labelColour(name)).toBe(theme.color.tabIdle);
    }
    // `ink` at .62 — an alpha ink, which darkens with the ground under the glass.
    expect(alphaOf(theme.color.tabIdle)).toBe(0.62);
  });

  it('draws the lit tab’s icon in `coral` and its label in `coralInk`', () => {
    renderBar('play');

    expect(glyphOf('Play').color).toBe(theme.color.coral);
    expect(labelColour('Play')).toBe(theme.color.coralInk);
  });

  it('colours one tab for selected, and only the one the bar was told is lit', () => {
    renderBar('you');

    const lit = ['Home', 'Play', 'You'].filter(
      (name) => labelColour(name) === theme.color.coralInk,
    );
    expect(lit).toEqual(['You']);
  });
});

/**
 * **The selection marker** (ADR-0210 §4): an opaque `coralSoft` capsule, 75 × 42, fully rounded,
 * centred in the lit column under its icon and label. It does not move yet (#884), so it simply
 * stands under whichever tab is lit.
 */
describe('the selection marker', () => {
  it('is an opaque `coralSoft` capsule, 75 × 42 and fully rounded', () => {
    renderBar('home');

    expect(marker()).toMatchObject({
      position: 'absolute',
      width: 75,
      height: 42,
      borderRadius: theme.radius.pill,
      backgroundColor: theme.color.coralSoft,
    });
    expect(marker().opacity).toBeUndefined();
  });

  it.each([
    ['home', 0],
    ['play', 1],
    ['you', 2],
  ] as const)('stands centred in the %s column', (active, at) => {
    renderBar(active);

    expect(markerColumn(3)).toBe(at);
  });

  it('is centred top to bottom inside the hairline', () => {
    renderBar('home');

    expect(marker().top).toBe((tabBar.height - 2 * HAIRLINE - tabBar.marker.height) / 2);
  });

  it('is under the newly lit tab the moment the lit tab changes', () => {
    const { rerender } = renderBar('home');

    rerender(
      <SafeAreaProvider initialMetrics={NOTCHED}>
        <TabBar active="you" onPress={jest.fn()} />
      </SafeAreaProvider>,
    );

    expect(markerColumn(3)).toBe(2);
  });

  it('says nothing to a reader and takes no touch — the column under it does both', () => {
    renderBar('home');

    const node = screen.getByTestId(TAB_BAR_MARKER_TEST_ID);
    expect(node.props.pointerEvents).toBe('none');
    // An empty drawing: no name, no role, no text, so nothing a reader could land on.
    expect(node.props.accessible).toBeUndefined();
    expect(node.props.accessibilityRole).toBeUndefined();
    expect(node.children).toHaveLength(0);
  });
});

/**
 * **Bottom to top: glass → marker → icons and labels → badge** (ADR-0210 §8). The marker is under
 * the words, so the stretch #884 gives it never deforms a glyph, and the badge is over everything.
 */
describe('the layers', () => {
  it('draws the glass, then the marker, then the columns', () => {
    renderBar('home', { gamesNeedingYou: 2 });

    // Every drawn node on the dock, in the order it is drawn — each over the ones before it.
    const drawnInOrder = screen
      .getByTestId(TAB_BAR_TEST_ID)
      .findAll((node: ReactTestInstance) => typeof node.type === 'string');
    const at = (find: (props: Record<string, unknown>) => boolean) =>
      drawnInOrder.findIndex((node: ReactTestInstance) => find(node.props));

    const ground: unknown[] = [theme.color.glass, theme.color.surface];
    const glass = at((props) => ground.includes(flat(props.style).backgroundColor));
    const markerAt = at((props) => props.testID === TAB_BAR_MARKER_TEST_ID);
    const firstColumn = at((props) => props.accessibilityRole === 'tab');

    expect(glass).toBeGreaterThanOrEqual(0);
    expect(glass).toBeLessThan(markerAt);
    expect(markerAt).toBeLessThan(firstColumn);
  });

  it('draws the badge over Home’s icon, after it in the column', () => {
    renderBar('home', { gamesNeedingYou: 2 });

    const home = column('Home, 2 games waiting on you');
    const drawn = home.findAll(
      (node: ReactTestInstance) => node.type === Ionicons || node.props.figure === 2,
    );
    expect(
      drawn.map((node: ReactTestInstance) => (node.type === Ionicons ? 'icon' : 'badge')),
    ).toEqual(['icon', 'badge']);
  });
});

describe('the press', () => {
  it('dims every column’s icon and label to 0.7 under a finger — Play’s too, now it has no disc', () => {
    renderBar('home');

    for (const name of ['Home', 'Play', 'You']) {
      expect(columnStyle(name, true).opacity).toBe(0.7);
      expect(columnStyle(name, false).opacity).toBeUndefined();
    }
  });

  it('leaves the marker alone — it is no part of any column', () => {
    renderBar('home');

    const node = screen.getByTestId(TAB_BAR_MARKER_TEST_ID);
    for (let at = node.parent; at !== null; at = at.parent) {
      expect(at.props.accessibilityRole).not.toBe('tab');
    }
  });

  it('reaches the touch minimum by its own geometry, with no hit-slop to arrange', () => {
    // A column is the dock's height inside its hairline, and a third of a 320 phone's dock.
    expect(tabBar.height - 2 * HAIRLINE).toBeGreaterThanOrEqual(theme.size.minTouch);
    expect((320 - 2 * tabBar.sideInset - 2 * HAIRLINE) / 3).toBeGreaterThanOrEqual(
      theme.size.minTouch,
    );
  });
});

describe('Dynamic Type', () => {
  it('scales every label, bounded, and freezes none of them', () => {
    renderBar('home');

    const labels = screen.UNSAFE_queryAllByType(Text).filter((t) => t.props.numberOfLines === 1);

    expect(labels).toHaveLength(TAB_BAR_TABS.length);
    for (const label of labels) {
      // Part 13 permits `allowFontScaling={false}` only inside the level bar, so the cap is the
      // only mechanism this surface has — and it is held inside the marker in
      // `tabBarLabelCap.test.ts`.
      expect(label.props.allowFontScaling).toBeUndefined();
      expect(label.props.maxFontSizeMultiplier).toBe(tabBar.labelMaxScale);
    }
  });

  it('draws the label as `tag` — a name, not a tracked eyebrow', () => {
    renderBar('home');

    expect(flat(screen.getByText('Home').props.style)).toMatchObject({
      fontFamily: theme.type.tag.fontFamily,
      fontSize: theme.type.tag.fontSize,
    });
  });

  it('puts the icon over its label with the grid’s smallest step between them', () => {
    renderBar('home');

    expect(columnStyle('Home', false)).toMatchObject({
      alignItems: 'center',
      justifyContent: 'center',
      gap: theme.space.xxs,
    });
  });
});

/**
 * **Home's badge counts the booked games that need you** — a seat open, a result to enter or
 * confirm, a no-show against you, a payment to confirm
 * ([the mechanics §3](../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 * The bar draws the number it is handed; which games need you is the caller's fold.
 *
 * A badge is a **change to the label at least as much as to the drawing**, so both halves are
 * asserted — and the states that draw nothing are asserted to draw nothing, because a count that
 * flickered onto permanent chrome would say something is waiting when nothing is.
 */
describe('the Home badge', () => {
  it('draws nothing at all when the bar is handed no count', () => {
    renderBar('you');

    expect(badge()).toBeUndefined();
    expect(screen.getByLabelText('Home')).toBeTruthy();
  });

  it('draws a coralInk mark on Home, and speaks the count in Home’s own name', () => {
    renderBar('you', { gamesNeedingYou: 2 });

    expect(badge()).toMatchObject({
      position: 'absolute',
      backgroundColor: theme.color.coralInk,
      height: tabBar.badge,
      minWidth: tabBar.badge,
      borderRadius: theme.radius.pill,
    });
    expect(screen.getByLabelText('Home, 2 games waiting on you')).toBeTruthy();
  });

  it('rises 4 above the 18pt icon box and sits 3 back over its right edge', () => {
    renderBar('you', { gamesNeedingYou: 2 });

    expect(badge()).toMatchObject({
      bottom: tabBar.icon - tabBar.badge + tabBar.badgeRise,
      left: tabBar.icon - theme.space.xxs,
    });
    expect(tabBar.badgeRise).toBe(4);
    expect(theme.space.xxs).toBe(3);
  });

  it('hardcodes no plural', () => {
    renderBar('you', { gamesNeedingYou: 1 });

    expect(screen.getByLabelText('Home, 1 game waiting on you')).toBeTruthy();
  });

  it('prints the digit in white, which is 5.89 on that fill and not 3.89 on coral', () => {
    renderBar('home', { gamesNeedingYou: 2 });

    // Queried through the tree rather than by text: the mark is hidden from the accessibility
    // tree on purpose — the count is on the column's own name — so it is not a text node a
    // reader can reach.
    const mark = screen.UNSAFE_getAllByType(Text).find((node) => node.props.children === 2);

    expect(flat(mark?.props.style).color).toBe(theme.color.surface);
  });

  it('badges no other column with it', () => {
    renderBar('home', { gamesNeedingYou: 4 });

    for (const name of ['Play', 'You']) {
      expect(screen.getByLabelText(name)).toBeTruthy();
    }
  });
});

/**
 * **The Administrator's bar is the same dock with two columns**, Groups · You (ADR-0210 §3, Q16):
 * the same geometry, material and marker, Groups in Ionicons `people`.
 */
describe('the Administrator’s bar', () => {
  function renderArea(active: 'groups' | 'you') {
    return render(
      <SafeAreaProvider initialMetrics={NOTCHED}>
        <AdministratorTabBar active={active} onPress={jest.fn()} />
      </SafeAreaProvider>,
    );
  }

  it('is Groups and You, with the lit one announced as selected', () => {
    renderArea('groups');

    expect(columns()).toEqual(['Groups', 'You']);
    expect(screen.getByRole('tab', { name: 'Groups', selected: true })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'You', selected: false })).toBeTruthy();
  });

  it('is the player’s dock — the same frame, lift and height', () => {
    renderBar('home');
    const players = dock();
    screen.unmount();

    renderArea('groups');

    expect(dock()).toEqual(players);
  });

  it('draws Groups as `people`, outlined while idle, and stands the marker under the lit one', () => {
    renderArea('groups');
    expect(glyphs().map((glyph) => glyph.props.name)).toEqual(['people', 'person-outline']);
    expect(markerColumn(2)).toBe(0);

    screen.unmount();
    renderArea('you');
    expect(glyphs().map((glyph) => glyph.props.name)).toEqual(['people-outline', 'person']);
    expect(markerColumn(2)).toBe(1);
  });
});
