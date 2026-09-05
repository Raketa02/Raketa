/**
 * The table, and the one rule read off it.
 *
 * Small, and worth having: `tabForPathname` is what lights the bar's active column on every
 * screen in the app, and the case it exists for — Play staying lit three screens deep — is
 * the case a whole-path comparison passes on today and fails on the day the builder lands.
 */

import { TAB_BAR_TABS } from '@/shared/ui';

import { PLAY_STACK, SHELL_TAB_ROOT, tabForPathname } from './shellTabs';

describe('the five routes', () => {
  it('names one for every tab the bar draws, and no others', () => {
    expect(Object.keys(SHELL_TAB_ROOT).sort()).toEqual(TAB_BAR_TABS.map((tab) => tab.key).sort());
  });

  it('opens the app at the shell root rather than at a second spelling of Now', () => {
    expect(SHELL_TAB_ROOT.now).toBe('/');
  });

  it('enters Play with Now underneath it, which is where back goes', () => {
    expect(PLAY_STACK).toEqual(['/', '/play']);
  });
});

describe('which tab a route is inside', () => {
  it.each(Object.entries(SHELL_TAB_ROOT))('reads %s back off its own route', (tab, route) => {
    expect(tabForPathname(route)).toBe(tab);
  });

  it('keeps Play lit on every screen inside Play', () => {
    // None of these exist yet; they are the deck, the builder and the pool, and the day
    // they land is the day a whole-path comparison would go dark on arrival.
    expect(tabForPathname('/play/deck')).toBe('play');
    expect(tabForPathname('/play/four')).toBe('play');
    expect(tabForPathname('/play/pickpool')).toBe('play');
  });

  /**
   * The Now tab's root is `/`, so a screen pushed over it cannot share its segment the way the
   * builder shares Play's — it is a sibling at the top level. Falling through to the default
   * would give the right answer for the wrong reason, and the day a second tab grows depth the
   * two would be indistinguishable.
   */
  it('keeps Now lit on a game, which is inside it without being under it', () => {
    expect(tabForPathname('/games/8f14e45f-ceea-467a-9dd1-4bd9c39d4a58')).toBe('now');
  });

  it('answers the root for a path the shell does not own', () => {
    // Nothing outside `(tabs)` draws a bar at all, so this is the answer to a question
    // that is never asked rather than a claim that /sign-in is the Now tab.
    expect(tabForPathname('/sign-in')).toBe('now');
  });
});
