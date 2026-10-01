/**
 * The table, and the one rule read off it.
 *
 * Small, and worth having: `tabForPathname` is what lights the bar's active column on every
 * screen in the app, and the case it exists for — Play staying lit three screens deep — is
 * the case a whole-path comparison passes on today and fails on the day the builder lands.
 */

import { TAB_BAR_TABS } from '@/shared/ui';

import { PLAY_STACK, SHELL_TAB_ROOT, barStandsDown, tabForPathname } from './shellTabs';

describe('the five routes', () => {
  it('names one for every tab the bar draws, and no others', () => {
    expect(Object.keys(SHELL_TAB_ROOT).sort()).toEqual(TAB_BAR_TABS.map((tab) => tab.key).sort());
  });

  it('opens the app at the shell root rather than at a second spelling of Home', () => {
    expect(SHELL_TAB_ROOT.home).toBe('/');
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
    // The builder and the pool, and any depth Play grows next: a whole-path comparison would
    // go dark on the second screen.
    expect(tabForPathname('/play/builder')).toBe('play');
    expect(tabForPathname('/play/pool')).toBe('play');
    expect(tabForPathname('/play/anything-next')).toBe('play');
  });

  /**
   * The deck left Play for a tab of its own
   * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
   * §1): `/players` is Players' root, and nothing under `/play/…` is the deck any more.
   */
  it('reads Players off its root, and never off a route under Play', () => {
    expect(tabForPathname('/players')).toBe('players');
    expect(SHELL_TAB_ROOT.players).toBe('/players');
    expect(Object.values(SHELL_TAB_ROOT)).not.toContain('/around');
  });

  /**
   * The Home tab's root is `/`, so a screen pushed over it cannot share its segment the way the
   * builder shares Play's — it is a sibling at the top level. Falling through to the default
   * would give the right answer for the wrong reason, and the day a second tab grows depth the
   * two would be indistinguishable.
   */
  it('keeps Home lit on a game, which is inside it without being under it', () => {
    expect(tabForPathname('/games/8f14e45f-ceea-467a-9dd1-4bd9c39d4a58')).toBe('home');
  });

  it('keeps Home lit on a booked game, its chat and its result (#556)', () => {
    const booking = '/booking/3f2b8c1e-0000-4000-8000-0000000000b1';
    expect(tabForPathname(booking)).toBe('home');
    expect(tabForPathname(`${booking}/chat`)).toBe('home');
    expect(tabForPathname(`${booking}/result`)).toBe('home');
  });

  it('answers the root for a path the shell does not own', () => {
    // Nothing outside `(tabs)` draws a bar at all, so this is the answer to a question
    // that is never asked rather than a claim that /sign-in is the Home tab.
    expect(tabForPathname('/sign-in')).toBe('home');
  });
});

/**
 * **Three routes stand the bar down, and each is named in full** — the third a booked game's room
 * (#556), the same room reached from its details over Home. The conversation is the screen
 * whose composer replaces the bar ([#400](https://github.com/Raketa02/Raketa/issues/400)), and
 * the yes screen under a challenge is the one the bar would be a way out of that the record
 * says it does not have ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2). The inbox they are pushed over, the challenge screen, the builder under it and the game
 * screen behind the room's own *Details* door all keep theirs — so a `/chats/*` match would be
 * four screens too wide, and a prefix match would take the bar off the game screen at
 * `…/details` and the builder at `…/fill`.
 */
describe('where the bar stands down', () => {
  const ROOM = '/chats/conversation/eeeeeeee-0000-4000-8000-000000000005';
  const YES = '/chats/challenge/aaaaaaaa-0000-4000-8000-000000000001/yes';

  it('is inside a conversation, and its column stays lit while it does', () => {
    expect(barStandsDown(ROOM)).toBe(true);
    expect(tabForPathname(ROOM)).toBe('chats');
  });

  it('is on the yes screen under a challenge, and its column stays lit there too', () => {
    expect(barStandsDown(YES)).toBe(true);
    expect(tabForPathname(YES)).toBe('chats');
  });

  it.each([
    ['the Chats inbox the room is pushed over', '/chats'],
    ['the challenge screen', '/chats/challenge/aaaaaaaa-0000-4000-8000-000000000001'],
    ['the builder under a challenge', '/chats/challenge/aaaaaaaa-0000-4000-8000-000000000001/fill'],
    ['the game screen behind the room’s own Details door', `${ROOM}/details`],
    ['a game over Home', '/games/8f14e45f-ceea-467a-9dd1-4bd9c39d4a58'],
    ['the shell root', '/'],
    ['a path the shell does not own', '/sign-in'],
  ])('is not %s', (_, pathname) => {
    expect(barStandsDown(pathname)).toBe(false);
  });

  /** The third ([#556](https://github.com/Raketa02/Raketa/issues/556)): a booked game's room. */
  it('is inside a booked game’s room, and Home stays lit while it does', () => {
    const chat = '/booking/3f2b8c1e-0000-4000-8000-0000000000b1/chat';
    expect(barStandsDown(chat)).toBe(true);
    expect(tabForPathname(chat)).toBe('home');
  });

  it.each([
    ['a booked game’s details', '/booking/3f2b8c1e-0000-4000-8000-0000000000b1'],
    ['a booked game’s result', '/booking/3f2b8c1e-0000-4000-8000-0000000000b1/result'],
    ['a room with no booking', '/booking//chat'],
    [
      'anything under a booked game’s room',
      '/booking/3f2b8c1e-0000-4000-8000-0000000000b1/chat/more',
    ],
  ])('is not %s', (_, pathname) => {
    expect(barStandsDown(pathname)).toBe(false);
  });

  it('is not a conversation with no id, which is not a route at all', () => {
    expect(barStandsDown('/chats/conversation')).toBe(false);
    expect(barStandsDown('/chats/challenge//yes')).toBe(false);
  });

  it('is not anything else hung under a challenge, nor anything under the yes screen', () => {
    expect(barStandsDown('/chats/challenge/aaaaaaaa-0000-4000-8000-000000000001/no')).toBe(false);
    expect(barStandsDown(`${YES}/more`)).toBe(false);
  });
});
