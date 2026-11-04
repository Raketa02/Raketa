import {
  parseFriendsRouteParams,
  parseGroupPlace,
  parseGroupRouteParams,
  parseJoinRouteParams,
} from './groupRouteParams';

describe('a group page’s route param', () => {
  it('reads a group id', () => {
    expect(parseGroupRouteParams({ groupId: 'a0000000-0000-4000-8000-000000000002' })).toEqual({
      groupId: 'a0000000-0000-4000-8000-000000000002',
    });
  });

  it.each([{ groupId: 'not-a-group' }, { groupId: ['a', 'b'] }, {}, undefined])(
    'refuses %p',
    (params) => {
      expect(parseGroupRouteParams(params)).toBeUndefined();
    },
  );
});

/**
 * **A group's deck opened by a notice** (#559; the screens A9): the sport, the kind and the card to
 * put on top ride with the group's id. All three, or the page opens as the page always does — a
 * group id is enough to open on, and an arrival this build cannot read is no reason to refuse it.
 */
describe('a group page opened at a card', () => {
  const GROUP = 'a0000000-0000-4000-8000-000000000002';
  const CARD = 'b0000000-0000-4000-8000-000000000003';

  it('reads the sport, the kind and the card beside the group', () => {
    expect(
      parseGroupRouteParams({ groupId: GROUP, sport: 'padel', kind: 'forFun', card: CARD }),
    ).toEqual({ groupId: GROUP, arrival: { sport: 'padel', kind: 'forFun', card: CARD } });
  });

  it.each([
    { sport: 'padel', kind: 'forFun' },
    { sport: 'pickleball', kind: 'forFun', card: CARD },
    { sport: 'padel', kind: 'FOR_FUN', card: CARD },
    { sport: 'padel', kind: 'forFun', card: 'not-a-card' },
  ])('opens the page as it always does for %p', (arrival) => {
    expect(parseGroupRouteParams({ groupId: GROUP, ...arrival })).toEqual({ groupId: GROUP });
  });
});

/**
 * **A group's page returned to by a rating pass** (#729, ADR-0200 §5): the tab the pass began on,
 * and the sport it rated last. The tab alone, or the page opens as it always does.
 */
describe('a group page a rating pass returns to', () => {
  const GROUP = 'a0000000-0000-4000-8000-000000000002';

  it('reads the tab and the sport beside the group', () => {
    expect(parseGroupRouteParams({ groupId: GROUP, tab: 'fillIn', sport: 'tennis' })).toEqual({
      groupId: GROUP,
      returning: { tab: 'fillIn', sport: 'tennis' },
    });
  });

  it('reads the tab with no sport, for a pass that rated nothing', () => {
    expect(parseGroupRouteParams({ groupId: GROUP, tab: 'friends' })).toEqual({
      groupId: GROUP,
      returning: { tab: 'friends' },
    });
  });

  it.each([
    { tab: 'info' },
    { tab: 'FILL_IN', sport: 'padel' },
    { tab: 'games', sport: 'pickleball' },
    { sport: 'padel' },
  ])('opens the page as it always does for %p', (returning) => {
    expect(parseGroupRouteParams({ groupId: GROUP, ...returning })).toEqual({ groupId: GROUP });
  });
});

/**
 * **The sports picker, opened from a group's tab** (#729, for #730's door): which group, and which
 * tab, so the pass it begins returns there.
 */
describe('a rating pass begun on a group’s tab', () => {
  const GROUP = 'a0000000-0000-4000-8000-000000000002';

  it('reads the group and the tab', () => {
    expect(parseGroupPlace({ groupId: GROUP, tab: 'games' })).toEqual({
      groupId: GROUP,
      tab: 'games',
    });
  });

  it.each([
    { groupId: GROUP },
    { groupId: GROUP, tab: 'members' },
    { groupId: 'not-a-group', tab: 'games' },
    {},
    undefined,
  ])('is no group for %p', (params) => {
    expect(parseGroupPlace(params)).toBeUndefined();
  });
});

describe('the Friends screen’s route params', () => {
  const GROUP = 'a0000000-0000-4000-8000-000000000002';

  it('reads a group id and the sport being built', () => {
    expect(parseFriendsRouteParams({ groupId: GROUP, sport: 'tennis' })).toEqual({
      groupId: GROUP,
      sport: 'tennis',
    });
  });

  it.each([
    { groupId: GROUP },
    { groupId: GROUP, sport: 'pickleball' },
    { groupId: GROUP, sport: 'PADEL' },
    { groupId: 'not-a-group', sport: 'padel' },
    undefined,
  ])('refuses %p', (params) => {
    expect(parseFriendsRouteParams(params)).toBeUndefined();
  });
});

/**
 * **Join a group's, opened by a group link** (#520): the code the link carried, which the screen
 * fills its field with. A code is eight letters and digits; which eight is the server's to say.
 */
describe('Join a group’s route param', () => {
  it('reads a code, in the lower case every code is minted in', () => {
    expect(parseJoinRouteParams({ code: 'K7PQ2MXA' })).toEqual({ code: 'k7pq2mxa' });
  });

  it.each([
    { code: 'k7pq' },
    { code: 'k7pq2mxa9' },
    { code: 'k7pq-2mx' },
    { code: ['k7pq2mxa', 'zzzzzzzz'] },
    {},
    undefined,
  ])('refuses %p', (params) => {
    expect(parseJoinRouteParams(params)).toBeUndefined();
  });
});
