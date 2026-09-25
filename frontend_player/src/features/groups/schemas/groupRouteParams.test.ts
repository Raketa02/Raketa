import { parseFriendsRouteParams, parseGroupRouteParams } from './groupRouteParams';

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
