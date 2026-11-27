/**
 * The table, and the one rule read off it.
 *
 * Small, and worth having: `tabForPathname` is what lights the bar's active column on every
 * screen in the app, and the case it exists for — Play staying lit three screens deep — is
 * the case a whole-path comparison passes on and fails the day Play grows a second screen.
 */

import { TAB_BAR_TABS } from '@/shared/ui';

import { PLAY_STACK, SHELL_TAB_ROOT, barStandsDown, tabForPathname } from './shellTabs';

describe('the three routes', () => {
  it('names one for every tab the bar draws, and no others', () => {
    expect(Object.keys(SHELL_TAB_ROOT).sort()).toEqual(TAB_BAR_TABS.map((tab) => tab.key).sort());
  });

  it('is Home, Play and You — the old loop’s Players and Chats are not routes of the shell', () => {
    expect(SHELL_TAB_ROOT).toEqual({ home: '/', play: '/play', you: '/you' });
  });

  it('enters Play with Home underneath it, which is where back goes', () => {
    expect(PLAY_STACK).toEqual(['/', '/play']);
  });
});

describe('which tab a route is inside', () => {
  it.each(Object.entries(SHELL_TAB_ROOT))('reads %s back off its own route', (tab, route) => {
    expect(tabForPathname(route)).toBe(tab);
  });

  it('keeps Play lit on every screen inside Play', () => {
    // A group's page and what is pushed over it, and any depth Play grows next: a whole-path
    // comparison would go dark on the second screen.
    expect(tabForPathname('/play/group/aaaaaaaa-0000-4000-8000-000000000001')).toBe('play');
    expect(tabForPathname('/play/new-group')).toBe('play');
    expect(tabForPathname('/play/anything-next')).toBe('play');
  });

  it('keeps You lit on every screen behind its rows', () => {
    expect(tabForPathname('/you/payments')).toBe('you');
  });

  /**
   * The Home tab's root is `/`, so a screen pushed over it cannot share its segment the way a
   * group's page shares Play's — it is a sibling at the top level, and named in the table.
   */
  it('keeps Home lit on a booked game, its chat and its result (#556)', () => {
    const booking = '/booking/3f2b8c1e-0000-4000-8000-0000000000b1';
    expect(tabForPathname(booking)).toBe('home');
    expect(tabForPathname(`${booking}/chat`)).toBe('home');
    expect(tabForPathname(`${booking}/result`)).toBe('home');
  });

  it('keeps Home lit on the recent notices behind its bell (#559), and the bar up', () => {
    expect(tabForPathname('/notices')).toBe('home');
    expect(barStandsDown('/notices')).toBe(false);
  });

  it('keeps Home lit on Rankings behind its trophy (#775, Q11), and the bar up', () => {
    expect(tabForPathname('/rankings')).toBe('home');
    expect(barStandsDown('/rankings')).toBe(false);
  });

  it('keeps Home lit on the people rows’ See all (#801, #802, #803), and the bar up', () => {
    for (const seeAll of ['/new-in-raketa', '/same-level', '/same-vibe']) {
      expect(tabForPathname(seeAll)).toBe('home');
      expect(barStandsDown(seeAll)).toBe(false);
    }
  });

  it('keeps Home lit on the Groups heating up page (#823), and the bar up', () => {
    expect(tabForPathname('/hottest-groups')).toBe('home');
    expect(barStandsDown('/hottest-groups')).toBe(false);
  });

  it('answers the root for a path the shell does not own', () => {
    // Nothing outside `(tabs)` draws a bar at all, so this is the answer to a question
    // that is never asked rather than a claim that /sign-in is the Home tab — and it is the
    // answer the old loop's removed routes get too.
    expect(tabForPathname('/sign-in')).toBe('home');
    expect(tabForPathname('/chats')).toBe('home');
    expect(tabForPathname('/players')).toBe('home');
  });
});

/**
 * **One route stands the bar down, and it is named in full** — a booked game's room (#556), the
 * screen whose composer replaces the bar ([#400](https://github.com/Raketa02/Raketa/issues/400)).
 * The details it is pushed over and the result beside it keep theirs, so a prefix match would be
 * two screens too wide.
 */
describe('where the bar stands down', () => {
  const BOOKING = '/booking/3f2b8c1e-0000-4000-8000-0000000000b1';

  it('is inside a booked game’s room, and Home stays lit while it does', () => {
    expect(barStandsDown(`${BOOKING}/chat`)).toBe(true);
    expect(tabForPathname(`${BOOKING}/chat`)).toBe('home');
  });

  it.each([
    ['a booked game’s details', BOOKING],
    ['a booked game’s result', `${BOOKING}/result`],
    ['a room with no booking', '/booking//chat'],
    ['anything under a booked game’s room', `${BOOKING}/chat/more`],
    ['the shell root', '/'],
    ['a path the shell does not own', '/sign-in'],
  ])('is not %s', (_, pathname) => {
    expect(barStandsDown(pathname)).toBe(false);
  });
});
