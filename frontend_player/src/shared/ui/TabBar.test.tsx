/**
 * The bar, asserted through what a player, a finger and a screen reader can each observe.
 *
 * Five tabs with names and states are ordinary queries, and the first two suites stay there.
 * **The rest are the declared exception the ring and the navigator already declare**: the
 * ring, the disc, the shadow and the pressed fills are drawings with no accessible name, and
 * they are exactly the rules this bar loses silently — a ring that changed the bar's height
 * would move the four columns that did not change, a disc that took `coral` instead of
 * `coralInk` would be a 3.89:1 white mark, and a bolt drawn as `⚡` would render in whatever
 * colour the platform's emoji font feels like.
 */

import Feather from '@expo/vector-icons/Feather';
import { fireEvent, render, screen } from '@testing-library/react-native';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { SafeAreaProvider, type Metrics } from 'react-native-safe-area-context';

import { TabBar, TAB_BAR_TABS, type TabBarKey } from './TabBar';
import { theme } from './theme';

/**
 * A notched phone. The bottom inset is the bar's own — a CTA above it applies none, and an
 * inset applied twice is 34pt of nothing.
 */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 320, height: 693 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

function renderBar(active: TabBarKey, onPress = jest.fn(), challengesWaiting?: number) {
  return render(
    <SafeAreaProvider initialMetrics={METRICS}>
      <TabBar active={active} onPress={onPress} challengesWaiting={challengesWaiting} />
    </SafeAreaProvider>,
  );
}

/** Every drawn View's resolved style, in tree order. */
function drawn(): ViewStyle[] {
  return screen.UNSAFE_queryAllByType(View).map((node) => StyleSheet.flatten(node.props.style));
}

/**
 * The active ring, if it is there at all.
 *
 * Found by its stroke rather than by *the one absolutely-positioned thing*, which it stopped
 * being when the badge arrived: both are out of the layout, and for the same reason.
 */
function ring(): ViewStyle | undefined {
  return drawn().find(
    (style) => style.position === 'absolute' && style.borderColor === theme.color.coral,
  );
}

/** The Chats badge, if the bar was handed a count. */
function badge(): ViewStyle | undefined {
  return drawn().find(
    (style) => style.position === 'absolute' && style.backgroundColor === theme.color.coralInk,
  );
}

function disc(): ViewStyle {
  const found = drawn().find((style) => style.borderRadius === theme.radius.fab);
  if (!found) throw new Error('the bar drew no disc');
  return found;
}

/**
 * The Play column as React Native would draw it under a finger.
 *
 * `Pressable` resolves its function child before the host View ever sees it, so the pressed
 * drawing is reachable only by calling it — the same reason the chip's suite reaches for its
 * style callback rather than firing an event at the host.
 */
function pressedPlayColumn(): ViewStyle[] {
  const column = screen.UNSAFE_getAllByType(Pressable)[2];
  const children = column.props.children as (state: { pressed: boolean }) => ReactNode;
  const under = render(<>{children({ pressed: true })}</>);
  return under.UNSAFE_queryAllByType(View).map((n) => StyleSheet.flatten(n.props.style));
}

/** A flank column's style callback, at rest or under a finger. */
function flankColumn(index: number, pressed: boolean): ViewStyle {
  return StyleSheet.flatten(screen.UNSAFE_getAllByType(Pressable)[index].props.style({ pressed }));
}

describe('what the bar offers', () => {
  it('is five tabs, named, in the order the map fixed', () => {
    renderBar('now');

    expect(screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel)).toEqual([
      'Now',
      'Players',
      'Play',
      'Chats',
      'You',
    ]);
  });

  it('reports which one was pressed', () => {
    const onPress = jest.fn();
    renderBar('now', onPress);

    fireEvent.press(screen.getByRole('tab', { name: 'Chats' }));

    expect(onPress).toHaveBeenCalledWith('chats');
  });

  it('reports a press on the tab that is already active — it decides nothing itself', () => {
    // ⚡Play always opens Find a game, whichever Play screen was last used, so a bar that
    // swallowed the press of the active tab would take that rule away from the shell.
    const onPress = jest.fn();
    renderBar('play', onPress);

    fireEvent.press(screen.getByRole('tab', { name: 'Play' }));

    expect(onPress).toHaveBeenCalledWith('play');
  });
});

describe('what the bar announces', () => {
  it('announces the active tab as selected', () => {
    renderBar('players');

    expect(screen.getByRole('tab', { name: 'Players', selected: true })).toBeTruthy();
  });

  it('announces the other four as not selected, rather than as silence', () => {
    renderBar('players');

    for (const name of ['Now', 'Play', 'Chats', 'You']) {
      expect(screen.getByRole('tab', { name, selected: false })).toBeTruthy();
    }
  });

  it('hides every glyph from the reader — the visible label already names the tab', () => {
    renderBar('now');

    for (const glyph of screen.UNSAFE_queryAllByType(Feather)) {
      expect(glyph.props.accessibilityElementsHidden).toBe(true);
      expect(glyph.props.importantForAccessibility).toBe('no');
    }
  });

  it('carries no badge — nothing on the bar is a count', () => {
    // The one counter this product has belongs to the segmented control inside Play: it is
    // not sport-filtered while the deck it labels is, and an unfiltered number on permanent
    // chrome would be a claim nobody can act on from here.
    renderBar('play');

    for (const text of screen.UNSAFE_queryAllByType(Text)) {
      expect(String(text.props.children)).not.toMatch(/\d/);
    }
  });
});

describe('the family', () => {
  it('draws every tab from Feather, and every name is one Feather ships', () => {
    // Typed against `glyphMap` at compile time and asserted here too, because a cast is all
    // it takes for a name that does not exist to become a blank column nobody notices at 16pt.
    for (const { glyph } of TAB_BAR_TABS) {
      expect(Feather.glyphMap).toHaveProperty(glyph);
    }
  });

  it('draws the bolt as a Feather glyph and never as U+26A1', () => {
    renderBar('play');

    // `⚡` carries `Emoji_Presentation=Yes`, so a `<Text>⚡</Text>` asks for colour emoji and
    // the `color` prop below has nothing to apply to. This is the assertion that the disc's
    // mark is the app's to colour.
    for (const text of screen.UNSAFE_queryAllByType(Text)) {
      expect(String(text.props.children)).not.toContain('⚡');
    }

    const bolt = screen.UNSAFE_queryAllByType(Feather).find((g) => g.props.name === 'zap');
    expect(bolt?.props.color).toBe(theme.color.surface);
    expect(bolt?.props.size).toBe(theme.size.tabBar.bolt);
  });

  it('carries selection in tone alone — the same glyph in both states', () => {
    renderBar('now');
    const resting = screen.UNSAFE_queryAllByType(Feather).map((g) => g.props.name);
    const tones = screen.UNSAFE_queryAllByType(Feather).map((g) => g.props.color);

    expect(resting).toEqual(TAB_BAR_TABS.map((t) => t.glyph));
    // Now is `ink` against four `muted`, and the bolt stays white on its own fill.
    expect(tones[0]).toBe(theme.color.ink);
    expect(tones[1]).toBe(theme.color.muted);
  });
});

describe('the disc, and the ring that says you are in Play', () => {
  it('is 6.1 `primary` in a squircle, and floats on the fifth shadow', () => {
    renderBar('now');

    expect(disc()).toMatchObject({
      width: theme.size.fab,
      height: theme.size.fab,
      borderRadius: theme.radius.fab,
      backgroundColor: theme.color.coralInk,
      shadowColor: theme.color.coral,
      shadowOpacity: theme.shadow.fab.shadowOpacity,
    });
  });

  it('brightens to `coral` under a finger, exactly as the primary button does', () => {
    renderBar('now');

    const pressed = pressedPlayColumn().find((s) => s.borderRadius === theme.radius.fab);

    expect(pressed?.backgroundColor).toBe(theme.color.coral);
  });

  it('grows a 2pt coral ring, 2pt clear of the disc, when Play is active', () => {
    renderBar('play');

    const { ringGap, ringStroke } = theme.size.tabBar;
    expect(ring()).toMatchObject({
      width: theme.size.fab + 2 * (ringGap + ringStroke),
      height: theme.size.fab + 2 * (ringGap + ringStroke),
      borderRadius: theme.radius.fab + ringGap + ringStroke,
      borderWidth: ringStroke,
      borderColor: theme.color.coral,
    });
  });

  it('draws no ring on any other tab', () => {
    renderBar('chats');

    expect(ring()).toBeUndefined();
  });

  it('does not change the bar between the two states — the ring is out of the layout', () => {
    // A bar that grew 8pt on arriving in Play would move the four things that did not change
    // in order to announce the one that did. Everything the layout can see is identical; the
    // ring is the only difference, and it is absolute.
    renderBar('chats');
    const elsewhere = drawn().filter((s) => s.position !== 'absolute');

    renderBar('play');
    const inPlay = drawn().filter((s) => s.position !== 'absolute');

    expect(inPlay).toEqual(elsewhere);
  });
});

describe('the geometry a finger meets', () => {
  it('gives the bar 10.2 paddings and the bottom inset', () => {
    renderBar('now');

    // The bar is the outermost drawn View: the columns are inside it.
    const [bar] = drawn();
    expect(bar).toMatchObject({
      paddingTop: theme.space.xs,
      paddingBottom: theme.space.md + METRICS.insets.bottom,
    });
  });

  it('dims a flank column under a finger, and never the Play column', () => {
    renderBar('now');

    // 6.6's answer for a surface with no second fill — and the disc has one, so dimming it
    // as well would be two channels for one press.
    expect(flankColumn(0, true).opacity).toBe(0.7);
    expect(flankColumn(0, false).opacity).toBeUndefined();
    expect(flankColumn(2, true).opacity).toBeUndefined();
  });

  it('reaches the touch minimum by its own geometry, with no hit-slop to arrange', () => {
    // The Play column is the tallest: the disc, the grid's smallest step, and one line of
    // `tag`. Every column stretches to it, and 45 clears 44.
    const column = theme.size.fab + theme.space.xxs + theme.type.tag.lineHeight;

    expect(column).toBeGreaterThanOrEqual(theme.size.minTouch);
  });
});

describe('Dynamic Type', () => {
  it('is the one thing that may grow the bar, and it is bounded', () => {
    // The bar's height is fixed against STATE — the ring is out of the layout — and not
    // against the OS text size, which Part 13 forbids freezing. At the cap one line of `tag`
    // goes 12 → 20,4pt, and that is the whole of the growth this surface allows.
    const grown = theme.type.tag.lineHeight * theme.size.tabBar.labelMaxScale;

    expect(grown).toBeGreaterThan(theme.type.tag.lineHeight);
    expect(grown - theme.type.tag.lineHeight).toBeLessThan(theme.size.minTouch / 4);
  });

  it('scales every label, bounded, and freezes none of them', () => {
    renderBar('now');

    const labels = screen.UNSAFE_queryAllByType(Text).filter((t) => t.props.numberOfLines === 1);

    expect(labels).toHaveLength(TAB_BAR_TABS.length);
    for (const label of labels) {
      // Part 13 permits `allowFontScaling={false}` only inside the level bar, so the cap is
      // the only mechanism this surface has — and it is derived, in `tabBarLabelCap.test.ts`.
      expect(label.props.allowFontScaling).toBeUndefined();
      expect(label.props.maxFontSizeMultiplier).toBe(theme.size.tabBar.labelMaxScale);
    }
  });

  it('draws the label as `tag` — a name, not a tracked eyebrow', () => {
    renderBar('now');

    const label = screen.getByText('Players');
    expect(StyleSheet.flatten(label.props.style)).toMatchObject({
      fontFamily: theme.type.tag.fontFamily,
      fontSize: theme.type.tag.fontSize,
    });
  });
});

/**
 * The badge is a **change to the label at least as much as to the drawing**, so both halves are
 * asserted — and the three states that draw nothing are asserted to draw nothing, because a
 * count that flickered onto permanent chrome would say something is waiting when nothing is.
 */
describe('the Chats badge', () => {
  it('draws nothing at all when the bar is handed no count', () => {
    renderBar('now');

    expect(badge()).toBeUndefined();
    expect(screen.getByLabelText('Chats')).toBeTruthy();
  });

  it('draws a coralInk mark on Chats, and speaks the count in that column’s own name', () => {
    renderBar('now', jest.fn(), 3);

    expect(badge()).toMatchObject({
      position: 'absolute',
      backgroundColor: theme.color.coralInk,
      height: theme.size.tabBar.badge,
      minWidth: theme.size.tabBar.badge,
      borderRadius: theme.radius.pill,
    });
    expect(screen.getByLabelText('Chats, 3 challenges waiting')).toBeTruthy();
  });

  it('hardcodes no plural', () => {
    renderBar('now', jest.fn(), 1);

    expect(screen.getByLabelText('Chats, 1 challenge waiting')).toBeTruthy();
  });

  it('prints the digit in white, which is 5.89 on that fill and not 3.89 on coral', () => {
    renderBar('now', jest.fn(), 2);

    // Queried through the tree rather than by text: the mark is hidden from the accessibility
    // tree on purpose — the count is on the column's own name — so it is not a text node a
    // reader can reach, which is exactly the assertion the suite next door makes.
    const mark = screen.UNSAFE_getAllByType(Text).find((node) => node.props.children === 2);

    expect(StyleSheet.flatten(mark?.props.style).color).toBe(theme.color.surface);
  });

  it('badges no other column, whatever it is handed', () => {
    renderBar('now', jest.fn(), 4);

    for (const tab of TAB_BAR_TABS) {
      if (tab.key === 'chats') continue;
      expect(screen.getByLabelText(tab.label)).toBeTruthy();
    }
  });

  it('leaves the bar’s height alone, because the mark is out of the layout', () => {
    renderBar('now', jest.fn(), 9);

    expect(badge()?.position).toBe('absolute');
  });
});
