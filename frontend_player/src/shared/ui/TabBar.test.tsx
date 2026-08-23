/**
 * The tab bar's anatomy, and the tree it moves through.
 *
 * Two levels in one file, deliberately. The bar is a design primitive with no router in
 * it, so its five glyphs, its circle, its badge and its selected cue are assertable
 * without one — and the *mapping* from a tab key to a route is the only thing that is
 * not, because it lives in `(app)/(tabs)/_layout.tsx`. Splitting them would put a
 * two-case router suite in a file of its own with nothing else in it.
 *
 * **The glyphs are asserted by the character actually drawn.** Feather is a font: it
 * renders a `Text` in family `feather` whose child is the glyph's codepoint, so
 * `Feather.glyphMap` is what turns a name into the thing on screen. Asserting the name
 * would only assert the prop this file passes; asserting the codepoint asserts what a
 * player sees, and a swap to any other glyph in the family goes red.
 */

import { Feather } from '@expo/vector-icons';
import { fireEvent, render, screen } from '@testing-library/react-native';
import { act, fireEvent as routerPress, screen as routerScreen } from 'expo-router/testing-library';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { emptyNow, stubNow } from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import {
  TabBar,
  TAB_BADGE_ID,
  TAB_BAR_ID,
  TAB_CIRCLE_ID,
  tabIconId,
  tabId,
  type TabKey,
} from './TabBar';
import { theme } from './theme';

/** Every style a node was given, flattened — RN accepts arrays and nesting. */
function stylesOf(node: { readonly props: { readonly style?: unknown } }): Record<string, unknown> {
  const flatten = (style: unknown): Record<string, unknown> => {
    if (Array.isArray(style)) return Object.assign({}, ...style.map(flatten));
    return typeof style === 'object' && style !== null ? (style as Record<string, unknown>) : {};
  };
  return flatten(node.props.style);
}

/**
 * The character Feather draws for a glyph name.
 *
 * The map is typed `string | number` because the vendored icon sets are not all
 * codepoints; Feather's are, and a name that resolved to anything else would throw here
 * rather than quietly compare two empty strings.
 */
function glyphOf(name: keyof typeof Feather.glyphMap): string {
  const point = Feather.glyphMap[name];
  if (typeof point !== 'number') throw new Error(`Feather.${String(name)} is not a codepoint`);
  return String.fromCodePoint(point);
}

/**
 * Which edges the safe areas above a node claim.
 *
 * `SafeAreaView` is `RNCSafeAreaView` and spends the inset **natively**, so there is no
 * `paddingBottom` in the JS tree to read — under jest the observable fact is the
 * instruction it was given, which is exactly the thing an edit here changes: `additive`
 * claims the inset, `off` leaves it to somebody below.
 */
function safeAreaEdgesAbove(node: { parent: unknown }): Record<string, unknown>[] {
  const found: Record<string, unknown>[] = [];
  let walk = node.parent as {
    type?: unknown;
    props?: Record<string, unknown>;
    parent?: unknown;
  } | null;
  while (walk !== null && walk !== undefined) {
    const edges = walk.props?.edges;
    if (String(walk.type) === 'RNCSafeAreaView' && typeof edges === 'object' && edges !== null) {
      found.push(edges as Record<string, unknown>);
    }
    walk = (walk.parent ?? null) as typeof walk;
  }
  return found;
}

/** What the icon `Text` actually rendered. */
function drawn(node: { readonly props: { readonly children?: unknown } }): string {
  const children = node.props.children;
  return (
    (Array.isArray(children) ? children : [children]).filter((c) => typeof c === 'string')[0] ?? ''
  );
}

function draw(active: TabKey = 'now', badges?: Partial<Record<TabKey, number>>) {
  const onSelect = jest.fn();
  render(
    <SafeAreaProvider
      initialMetrics={{
        frame: { x: 0, y: 0, width: 390, height: 844 },
        insets: { top: 0, left: 0, right: 0, bottom: 0 },
      }}
    >
      <TabBar active={active} badges={badges} onSelect={onSelect} />
    </SafeAreaProvider>,
  );
  return onSelect;
}

const GLYPHS: readonly (readonly [TabKey, keyof typeof Feather.glyphMap])[] = [
  ['now', 'home'],
  ['find', 'search'],
  ['create', 'plus'],
  ['msg', 'inbox'],
  ['you', 'user'],
];

// ---------------------------------------------------------------------------
// One family, five glyphs, one box
// ---------------------------------------------------------------------------

describe('five glyphs from one outline family', () => {
  it('draws home · search · plus · inbox · user', () => {
    draw();

    for (const [key, glyph] of GLYPHS) {
      expect(drawn(screen.getByTestId(tabIconId(key)))).toBe(glyphOf(glyph));
    }
  });

  it('takes all five from Feather and none from a second family', () => {
    draw();

    for (const [key] of GLYPHS) {
      expect(stylesOf(screen.getByTestId(tabIconId(key))).fontFamily).toBe('feather');
    }
  });

  it('draws every one at the existing 16pt box', () => {
    // `size.tabIcon`, which the card's exit control also draws at — the app's one box for
    // a stock glyph rather than the tab bar's private measurement.
    draw();

    for (const [key] of GLYPHS) {
      expect(stylesOf(screen.getByTestId(tabIconId(key))).fontSize).toBe(theme.size.tabIcon);
    }
  });

  it('is five tabs and no more', () => {
    draw();

    expect(screen.getAllByRole('tab')).toHaveLength(GLYPHS.length);
  });

  it('clears the home indicator without giving up its own padding', () => {
    // 10.2's `paddingBottom = 12 + bottom safe-area inset`. The inset is *added*: a bar
    // that replaced the 12 with it would sit tight under the labels on a phone with a
    // home indicator, and flush against the screen edge on one without.
    render(
      <SafeAreaProvider
        initialMetrics={{
          frame: { x: 0, y: 0, width: 390, height: 844 },
          insets: { top: 47, left: 0, right: 0, bottom: 34 },
        }}
      >
        <TabBar active="now" onSelect={jest.fn()} />
      </SafeAreaProvider>,
    );

    expect(stylesOf(screen.getByTestId(TAB_BAR_ID)).paddingBottom).toBe(theme.space.md + 34);
  });
});

// ---------------------------------------------------------------------------
// The create control
// ---------------------------------------------------------------------------

describe('the create tab is a flat coral circle', () => {
  it('is a filled coral circle at the fab size', () => {
    draw();

    const style = stylesOf(screen.getByTestId(TAB_CIRCLE_ID));

    expect(style.width).toBe(theme.size.fab);
    expect(style.height).toBe(theme.size.fab);
    // A circle, not §B13's radius-10 square: half the size is what makes it one, and it
    // is where ADR-0082's stated 14 comes from.
    expect(style.borderRadius).toBe(theme.size.fab / 2);
    expect(style.backgroundColor).toBe(theme.color.coral);
  });

  it('keeps the plus white, where a numeral could not be', () => {
    // Rule C forbids white *text* on coral (3.89:1). A glyph is non-text content under
    // 1.4.11, whose threshold is 3:1 — so this passes and the badge below does not.
    draw();

    expect(stylesOf(screen.getByTestId(tabIconId('create'))).color).toBe(theme.color.surface);
  });

  it('is flat and level with the other four', () => {
    // ADR-0082 declines both §B13's `margin-bottom:-4px` and 10.2's *lifted 3 above the
    // row*: being twice the size and the only filled shape already says it is not a fifth
    // destination, and raising it would break the bar's top line to say it twice.
    draw();

    const style = stylesOf(screen.getByTestId(TAB_CIRCLE_ID));

    expect(style.marginBottom).toBeUndefined();
    expect(style.marginTop).toBeUndefined();
    expect(style.transform).toBeUndefined();
    expect(style.shadowOpacity).toBeUndefined();
    expect(style.elevation).toBeUndefined();
  });

  it('carries no visible label, and still announces where it goes', () => {
    draw();

    expect(screen.queryByText('Create')).toBeNull();
    expect(screen.getByLabelText('Create a match')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The badge
// ---------------------------------------------------------------------------

describe('the Inbox badge', () => {
  it('draws its numeral in ink, on coral', () => {
    // §B13 says white; white on coral is 3.89:1 and a numeral is read, so 1.4.3 applies
    // and `ink` is the one dark Rule C permits there.
    draw('now', { msg: 2 });

    // `includeHiddenElements`: the pill is hidden from assistive technology on purpose,
    // because the count is already in the tab's own label.
    const pill = screen.getByTestId(TAB_BADGE_ID, { includeHiddenElements: true });
    const numeral = screen.getByText('2', { includeHiddenElements: true });

    expect(stylesOf(numeral).color).toBe(theme.color.ink);
    expect(stylesOf(pill).backgroundColor).toBe(theme.color.coral);
  });

  it('is a pill that grows sideways rather than a fixed square', () => {
    draw('now', { msg: 12 });

    const pill = stylesOf(screen.getByTestId(TAB_BADGE_ID, { includeHiddenElements: true }));

    expect(screen.getByText('12', { includeHiddenElements: true })).toBeTruthy();
    expect(pill.minWidth).toBe(theme.size.tabBadge);
    expect(pill.height).toBe(theme.size.tabBadge);
    expect(pill.borderRadius).toBe(theme.size.tabBadge / 2);
  });

  it('puts the count in the tab’s own label, where a screen reader can reach it', () => {
    draw('now', { msg: 2 });

    expect(screen.getByLabelText('Inbox, 2 new')).toBeTruthy();
  });

  it('is absent when nothing counts anything', () => {
    draw();

    expect(screen.getByLabelText('Inbox')).toBeTruthy();
    expect(screen.queryByTestId(TAB_BADGE_ID, { includeHiddenElements: true })).toBeNull();
  });

  it('is absent at zero rather than drawn empty', () => {
    draw('now', { msg: 0 });

    expect(screen.getByLabelText('Inbox')).toBeTruthy();
    expect(screen.queryByTestId(TAB_BADGE_ID, { includeHiddenElements: true })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Selection
// ---------------------------------------------------------------------------

describe('selection is coral, and coral alone', () => {
  it('tints the selected tab coral and the rest muted', () => {
    draw('find');

    expect(stylesOf(screen.getByTestId(tabIconId('find'))).color).toBe(theme.color.coral);
    expect(stylesOf(screen.getByText('Find')).color).toBe(theme.color.coral);

    expect(stylesOf(screen.getByTestId(tabIconId('now'))).color).toBe(theme.color.muted);
    expect(stylesOf(screen.getByText('Now')).color).toBe(theme.color.muted);
  });

  it('changes nothing but the colour — the knowing 1.4.1 failure, asserted', () => {
    // Feather is a font: no filled counterpart, no stroke weight, no optical size. The
    // remedy ADR-0082 pre-costs is a 3pt coral dot under the selected label. Until that
    // ships, *nothing else may quietly start carrying selection either* — a second cue
    // added here without amending the ADR would make its recorded failure untrue in one
    // direction and its recorded remedy stale in the other.
    draw('now');
    const selectedIcon = stylesOf(screen.getByTestId(tabIconId('now')));
    const selectedLabel = stylesOf(screen.getByText('Now'));
    const selectedTab = stylesOf(screen.getByTestId(tabId('now')));
    const restingTab = stylesOf(screen.getByTestId(tabId('find')));

    screen.unmount();

    draw('find');
    const restingIcon = stylesOf(screen.getByTestId(tabIconId('now')));
    const restingLabel = stylesOf(screen.getByText('Now'));

    expect(without(selectedIcon, 'color')).toEqual(without(restingIcon, 'color'));
    expect(without(selectedLabel, 'color')).toEqual(without(restingLabel, 'color'));
    // The column itself is identical either way: no underline, no fill, no weight change.
    expect(selectedTab).toEqual(restingTab);
  });
});

function without(style: Record<string, unknown>, key: string): Record<string, unknown> {
  const { [key]: _dropped, ...rest } = style;
  return rest;
}

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

describe('every tab is announced with its state', () => {
  it('gives each tab a role, a label and a selected state', () => {
    draw('msg');

    const tabs = screen.getAllByRole('tab');
    expect(tabs.map((t) => t.props.accessibilityLabel)).toEqual([
      'Now',
      'Find',
      'Create a match',
      'Inbox',
      'You',
    ]);
    expect(tabs.map((t) => t.props.accessibilityState.selected)).toEqual([
      false,
      false,
      false,
      true,
      false,
    ]);
  });

  it('marks exactly one tab selected', () => {
    draw('you');

    const selected = screen
      .getAllByRole('tab')
      .filter((t) => t.props.accessibilityState.selected === true);

    expect(selected).toHaveLength(1);
  });

  it('names the bar itself as a tab list', () => {
    draw();

    expect(screen.getByTestId(TAB_BAR_ID).props.accessibilityRole).toBe('tablist');
  });
});

describe('pressing a tab', () => {
  it('hands back the key that was pressed', () => {
    const onSelect = draw();

    fireEvent.press(screen.getByTestId(tabId('find')));

    expect(onSelect).toHaveBeenCalledWith('find');
  });

  it('hands back create like any other tab', () => {
    // The circle is drawn differently and is not a different kind of control.
    const onSelect = draw();

    fireEvent.press(screen.getByTestId(tabId('create')));

    expect(onSelect).toHaveBeenCalledWith('create');
  });
});

// ---------------------------------------------------------------------------
// The tree — the one thing the primitive cannot answer
// ---------------------------------------------------------------------------

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

describe('the bar reaches the tabs', () => {
  let transport: Transport;

  beforeEach(async () => {
    transport = installTransport();
    resetSessionStatus();
    wireHttpCredentials(refreshTokens);
    await clearStoredTokens();
    queryClient.clear();
    focusManager.setFocused(true);
  });

  afterEach(() => {
    transport.restore();
    queryClient.clear();
    onlineManager.setOnline(true);
    focusManager.setFocused(undefined);
  });

  async function launchOnNow(insets?: {
    top: number;
    left: number;
    right: number;
    bottom: number;
  }) {
    stubGate(transport, { ratings: [RATING] });
    stubNow(transport, emptyNow());
    await launchSignedIn('/', insets);
    await routerScreen.findByTestId(TAB_BAR_ID);
  }

  const HOME_INDICATOR = { top: 47, left: 0, right: 0, bottom: 34 };

  it('is under Now, with Now selected', async () => {
    await launchOnNow();

    expect(routerScreen).toHavePathname('/');
    expect(routerScreen.getByLabelText('Now').props.accessibilityState.selected).toBe(true);
  });

  it('opens Find, and the selected tab moves with it', async () => {
    await launchOnNow();

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('find')));
    });

    expect(routerScreen).toHavePathname('/find');
    expect(routerScreen.getByLabelText('Find').props.accessibilityState.selected).toBe(true);
    expect(routerScreen.getByLabelText('Now').props.accessibilityState.selected).toBe(false);
  });

  it('is the only thing that spends the bottom inset', async () => {
    // `BottomTabView` hands its own `insets` to the bar and leaves the screens' inset
    // context alone, so a screen above the bar that also claims `bottom` claims the same
    // 34pt twice — a band of dead paper between its last control and the bar. The bar
    // spends it; every screen under `(tabs)` takes `edges={['top']}`.
    await launchOnNow(HOME_INDICATOR);

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('you')));
    });

    const bar = stylesOf(routerScreen.getByTestId(TAB_BAR_ID));
    expect(bar.paddingBottom).toBe(theme.space.md + HOME_INDICATOR.bottom);

    // Nothing between the account screen's last control and the bar claims it again.
    const claims = safeAreaEdgesAbove(routerScreen.getByText('Sign out'));
    expect(claims.length).toBeGreaterThan(0);
    for (const edges of claims) expect(edges.bottom).toBe('off');
  });

  it('reaches the account screen, which nothing else could', async () => {
    // It moved off `index` when Now became the home screen and has had no way in since.
    await launchOnNow();

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('you')));
    });

    expect(routerScreen).toHavePathname('/account');
    expect(routerScreen.getByText('Sign out')).toBeTruthy();
  });

  it('opens create and inbox rather than pressing into nothing', async () => {
    await launchOnNow();

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('create')));
    });
    expect(routerScreen).toHavePathname('/create');

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('msg')));
    });
    expect(routerScreen).toHavePathname('/inbox');
  });

  it('comes back to Now, on the screen it left', async () => {
    // A tab navigator and not five links: each tab keeps its own stack, so returning is
    // returning rather than a fresh compose.
    await launchOnNow();

    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('find')));
    });
    await act(async () => {
      routerPress.press(routerScreen.getByTestId(tabId('now')));
    });

    expect(routerScreen).toHavePathname('/');
    expect(routerScreen.getByText('Your matches')).toBeTruthy();
  });
});
