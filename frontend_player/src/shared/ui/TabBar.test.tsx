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
import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { BlurView } from 'expo-blur';
import type { ReactElement } from 'react';
import { getAnimatedStyle } from 'react-native-reanimated';
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
import { ReducedMotionProvider } from './overlay';
import { MARKER_SLIDE } from './tabMarkerMotion';
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
  return render(onPhone(<TabBar active={active} onPress={jest.fn()} {...props} />, metrics));
}

/** A bar on a phone — its insets, and whether the phone asks for reduced motion. */
function onPhone(bar: ReactElement, metrics: Metrics = NOTCHED, reduced = false) {
  return (
    <SafeAreaProvider initialMetrics={metrics}>
      <ReducedMotionProvider value={reduced}>{bar}</ReducedMotionProvider>
    </SafeAreaProvider>
  );
}

/** The style a view is drawn at now — an animated one's as its last frame left it. */
function drawn(node: ReactTestInstance): ViewStyle & TextStyle {
  return node.props.jestAnimatedStyle === undefined
    ? flat(node.props.style)
    : flat(getAnimatedStyle(node));
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

/** The selection marker's drawing, as its last frame left it. */
const marker = () => drawn(screen.getByTestId(TAB_BAR_MARKER_TEST_ID));

/** One of the marker's transform steps — its translation, or its scale either way. */
function markerStep(step: 'translateX' | 'scaleX' | 'scaleY'): number | undefined {
  const steps = marker().transform as Record<string, number>[] | undefined;
  return steps?.find((each) => each[step] !== undefined)?.[step];
}

/** Where the marker's left edge stands inside the dock's hairline — its offset. */
function markerLeft(): number {
  const style = marker();
  return (typeof style.left === 'number' ? style.left : 0) + (markerStep('translateX') ?? 0);
}

/** The marker's centre, in columns of a dock this many wide — 0.5 is the first column's middle. */
const markerCentre = (count: number) =>
  (markerLeft() + Number(marker().width) / 2) / columnOf(count);

/** The marker's shape — its width and height as shares of its rest. */
const markerShape = () => ({ wide: markerStep('scaleX') ?? 1, tall: markerStep('scaleY') ?? 1 });

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

/** Every Ionicons glyph the bar drew, in order — two to a column, its idle and its selected. */
const glyphs = () => screen.UNSAFE_queryAllByType(Ionicons);

/** How much of a node shows: the opacity of the animated layer it is drawn in. */
function shownOf(node: ReactTestInstance): number {
  for (let at: ReactTestInstance | null = node; at !== null; at = at.parent) {
    if (at.props.jestAnimatedStyle !== undefined) return Number(drawn(at).opacity);
  }
  throw new Error('drawn in no animated layer');
}

/** One of a column's two layers, as drawn now: its glyph, its icon's and label's colours, and how much it shows. */
interface Layer {
  readonly glyph: string;
  readonly icon: string;
  readonly label: string;
  readonly shown: number;
}

/**
 * **A column's two layers, idle and selected**, by the column's name — each icon with its label,
 * which fade together.
 */
function layersOf(name: string): { readonly idle: Layer; readonly lit: Layer } {
  const icons = column(name).findAllByType(Ionicons);
  const words = column(name)
    .findAllByType(Text)
    .filter((text: ReactTestInstance) => text.props.numberOfLines === 1);
  expect(icons).toHaveLength(2);
  expect(words).toHaveLength(2);
  const layer = (at: 0 | 1): Layer => {
    const shown = shownOf(icons[at]!);
    expect(shownOf(words[at]!)).toBeCloseTo(shown, 10);
    return {
      glyph: icons[at]!.props.name,
      icon: icons[at]!.props.color,
      label: flat(words[at]!.props.style).color as string,
      shown,
    };
  };
  return { idle: layer(0), lit: layer(1) };
}

/** **What a column draws at rest** — the one of its layers that shows whole, the other not at all. */
function drawnFor(name: string): Layer {
  const { idle, lit } = layersOf(name);
  expect([idle.shown, lit.shown].sort()).toEqual([0, 1]);
  return lit.shown === 1 ? lit : idle;
}

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

    // Two to a column: the idle layer's and the selected layer's.
    expect(glyphs()).toHaveLength(6);
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
    const names = ['Home', 'Play', 'You'];
    renderBar('home');

    expect(names.map((name) => drawnFor(name).glyph)).toEqual(['home', 'flash', 'person-outline']);

    screen.unmount();
    renderBar('you');

    expect(names.map((name) => drawnFor(name).glyph)).toEqual(['home-outline', 'flash', 'person']);
  });

  it('draws each column’s outline under its filled glyph, ready to cross-fade', () => {
    renderBar('home');

    TAB_BAR_TABS.forEach(({ label, glyph }) => {
      const { idle, lit } = layersOf(label);
      expect([idle.glyph, lit.glyph]).toEqual([glyph.idle, glyph.lit]);
    });
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
    const { idle, lit } = layersOf('Play');
    expect([idle.glyph, lit.glyph]).toEqual(['flash', 'flash']);
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
      expect(drawnFor(name)).toMatchObject({
        icon: theme.color.tabIdle,
        label: theme.color.tabIdle,
      });
    }
    // `ink` at .62 — an alpha ink, which darkens with the ground under the glass.
    expect(alphaOf(theme.color.tabIdle)).toBe(0.62);
  });

  it('draws the lit tab’s icon in `coral` and its label in `coralInk`', () => {
    renderBar('play');

    expect(drawnFor('Play')).toMatchObject({
      icon: theme.color.coral,
      label: theme.color.coralInk,
    });
  });

  it('colours one tab for selected, and only the one the bar was told is lit', () => {
    renderBar('you');

    const lit = ['Home', 'Play', 'You'].filter(
      (name) => drawnFor(name).label === theme.color.coralInk,
    );
    expect(lit).toEqual(['You']);
  });

  it('keeps each column’s selected layer over its idle one, so only opacity has to move', () => {
    renderBar('you');

    for (const name of ['Home', 'Play', 'You']) {
      const { idle, lit } = layersOf(name);
      expect([idle.icon, idle.label]).toEqual([theme.color.tabIdle, theme.color.tabIdle]);
      expect([lit.icon, lit.label]).toEqual([theme.color.coral, theme.color.coralInk]);
    }
  });

  it('names each tab once — the selected label is a drawing a reader never reaches', () => {
    renderBar('home');

    for (const name of ['Home', 'Play', 'You']) {
      expect(screen.getAllByText(name)).toHaveLength(1);
      expect(screen.getAllByText(name, { includeHiddenElements: true })).toHaveLength(2);
    }
  });
});

/**
 * **The selection marker** (ADR-0210 §4): an opaque `coralSoft` capsule, 75 × 42, fully rounded,
 * centred in the lit column under its icon and label — placed there on the dock's first draw, at
 * rest and unstretched. How it travels is the next suite.
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

  it('is drawn at rest, unstretched, on the dock’s first draw', () => {
    renderBar('you');

    expect(markerShape()).toEqual({ wide: 1, tall: 1 });
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
 * **The marker travels** (ADR-0210 §8, #884): when the lit tab changes it slides there on the
 * 460 ms spring, stretching as it goes, and the new tab colours in from 140 ms into the slide while
 * the tab left goes idle at once. Read off each animated layer as its last frame drew it, on the
 * fake clock, timed from the change. **What the UI thread does lands on the next frame**, as on a
 * phone: the trip is worked out there, so the tab left goes idle with the slide's first frame.
 */
describe('the marker travels', () => {
  const FRAME = 16;
  const { colourIn, colourInAfter } = theme.motion.tabMarker;

  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  const advance = (ms: number) => act(() => jest.advanceTimersByTime(ms));

  /** The player's bar, drawn and handed a new lit tab — the shell's press, landing or notice alike. */
  function drawBar(active: TabBarKey, reduced = false) {
    const bar = (lit: TabBarKey, props: Partial<TabBarProps> = {}) =>
      onPhone(<TabBar active={lit} onPress={jest.fn()} {...props} />, NOTCHED, reduced);
    const view = render(bar(active));
    return {
      light: (lit: TabBarKey, props: Partial<TabBarProps> = {}) => view.rerender(bar(lit, props)),
    };
  }

  it('slides from the tab left to the lit one: between them mid-slide, at rest under it once settled', () => {
    const { light } = drawBar('home');

    light('you');
    advance(60);

    const midway = markerCentre(3);
    expect(midway).toBeGreaterThan(0.5);
    expect(midway).toBeLessThan(2.5);
    expect(markerColumn(3)).toBeUndefined();

    advance(MARKER_SLIDE);

    expect(markerColumn(3)).toBe(2);
    expect(markerShape()).toEqual({ wide: 1, tall: 1 });
  });

  it('stretches like a bubble on the way — wide and flat as it speeds up, narrow and tall as it brakes', () => {
    const { light } = drawBar('home');

    light('you');
    // Near its fastest, a third of the way.
    advance(48);
    const fast = markerShape();
    expect(fast.wide).toBeGreaterThan(1.25);
    expect(fast.tall).toBeLessThan(0.88);

    // Braking hard, near 70% of the way.
    advance(48);
    const braking = markerShape();
    expect(braking.wide).toBeLessThan(0.96);
    expect(braking.tall).toBeGreaterThan(1.04);
  });

  it('moves nothing but its transform — the travel a translate, the stretch a scale', () => {
    const { light } = drawBar('home');
    const before = marker();

    light('you');
    advance(48);
    const during = marker();

    const moved = Object.keys({ ...before, ...during }).filter(
      (key) =>
        JSON.stringify(before[key as keyof typeof before]) !==
        JSON.stringify(during[key as keyof typeof during]),
    );
    expect(moved).toEqual(['transform']);
  });

  it('colours the new tab in from 140 ms into the slide, whole by 440, and leaves the old tab idle at once', () => {
    const { light } = drawBar('home');

    light('you');
    advance(FRAME);

    expect(layersOf('Home').lit.shown).toBe(0);
    expect(layersOf('Home').idle.shown).toBe(1);
    expect(layersOf('You').lit.shown).toBe(0);

    advance(colourInAfter - 1 - FRAME);
    expect(layersOf('You').lit.shown).toBe(0);

    advance(colourIn / 2);
    const halfway = layersOf('You');
    expect(halfway.lit.shown).toBeGreaterThan(0.5);
    expect(halfway.lit.shown).toBeLessThan(1);
    // The idle layer stays whole under the selected one until that is whole: two layers each half
    // there would let the ground show through the word.
    expect(halfway.idle.shown).toBe(1);

    // 440 into the slide, and the frame that draws it.
    advance(colourIn / 2 + 1 + FRAME);
    expect(layersOf('You').lit.shown).toBe(1);
    expect(layersOf('You').idle.shown).toBe(0);
  });

  it('turns from where it is when a third tab is pressed mid-flight, and rests under that one', () => {
    const { light } = drawBar('home');

    light('you');
    advance(60);
    const turnedAt = markerCentre(3);

    light('play');
    advance(FRAME);
    // It carries on from where it was turned, still going the way it was — no jump, back or ahead.
    expect(markerCentre(3)).toBeGreaterThan(turnedAt);
    expect(markerCentre(3) - turnedAt).toBeLessThan(0.35);

    advance(MARKER_SLIDE);
    expect(markerColumn(3)).toBe(1);
    expect(markerShape()).toEqual({ wide: 1, tall: 1 });
    expect(drawnFor('Play').label).toBe(theme.color.coralInk);
    expect(drawnFor('You').label).toBe(theme.color.tabIdle);
  });

  it('never moves on a press of the lit tab — the bar is handed the same tab', () => {
    const { light } = drawBar('play');
    const before = marker();

    light('play');
    advance(60);

    expect(marker()).toEqual(before);
    expect(drawnFor('Play').label).toBe(theme.color.coralInk);
  });

  it('keeps its place and its colours through a re-render after it settles', () => {
    // An animated view redrawn by its parent is drawn with its first pose under jest, so the
    // marker and the layers are held out of the dock's re-renders — a count arriving is one.
    const { light } = drawBar('home');
    light('you');
    advance(MARKER_SLIDE + FRAME);

    light('you', { gamesNeedingYou: 3 });

    expect(markerColumn(3)).toBe(2);
    expect(drawnFor('You').label).toBe(theme.color.coralInk);
    expect(drawnFor('Home, 3 games waiting on you').label).toBe(theme.color.tabIdle);
  });

  it('is placed under the new tab under Reduce motion, and the colours switch with it', () => {
    const { light } = drawBar('home', true);

    light('you');
    // The next frame draws it: nothing between.
    advance(FRAME);

    expect(markerColumn(3)).toBe(2);
    expect(markerShape()).toEqual({ wide: 1, tall: 1 });
    expect(drawnFor('You').label).toBe(theme.color.coralInk);
    expect(drawnFor('Home').label).toBe(theme.color.tabIdle);
  });

  it('is placed the moment Reduce motion is turned on, though it was mid-slide', () => {
    let reduced = false;
    const bar = (lit: TabBarKey) =>
      onPhone(<TabBar active={lit} onPress={jest.fn()} />, NOTCHED, reduced);
    const view = render(bar('home'));
    view.rerender(bar('you'));
    advance(48);
    expect(markerColumn(3)).toBeUndefined();

    reduced = true;
    view.rerender(bar('you'));
    advance(FRAME);

    expect(markerColumn(3)).toBe(2);
    expect(markerShape()).toEqual({ wide: 1, tall: 1 });
    expect(drawnFor('You').label).toBe(theme.color.coralInk);
  });

  it('travels the same way on the Administrator’s two-column dock', () => {
    const bar = (lit: 'groups' | 'you') =>
      onPhone(<AdministratorTabBar active={lit} onPress={jest.fn()} />);
    const view = render(bar('groups'));

    view.rerender(bar('you'));
    advance(48);

    expect(markerColumn(2)).toBeUndefined();
    expect(markerShape().wide).toBeGreaterThan(1.1);

    advance(MARKER_SLIDE);
    expect(markerColumn(2)).toBe(1);
    expect(drawnFor('You').label).toBe(theme.color.coralInk);
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
    const order = home.findAll(
      (node: ReactTestInstance) => node.type === Ionicons || node.props.figure === 2,
    );
    // Both of the icon's layers, then the badge over them.
    expect(
      order.map((node: ReactTestInstance) => (node.type === Ionicons ? 'icon' : 'badge')),
    ).toEqual(['icon', 'icon', 'badge']);
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

    // Two to a column, idle and selected, and both bounded alike — the cross-fade never reflows.
    expect(labels).toHaveLength(2 * TAB_BAR_TABS.length);
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
    expect(['Groups', 'You'].map((name) => drawnFor(name).glyph)).toEqual([
      'people',
      'person-outline',
    ]);
    expect(markerColumn(2)).toBe(0);

    screen.unmount();
    renderArea('you');
    expect(['Groups', 'You'].map((name) => drawnFor(name).glyph)).toEqual([
      'people-outline',
      'person',
    ]);
    expect(markerColumn(2)).toBe(1);
  });
});
