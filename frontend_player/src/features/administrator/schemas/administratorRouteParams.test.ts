import { parseClubRouteParams, parseOfficialGroupRouteParams } from './administratorRouteParams';

const CLUB = 'c0000000-0000-4000-8000-000000000033';
const GROUP = 'a0000000-0000-4000-8000-000000000001';

describe('the administrator area’s route param', () => {
  it('reads a club id', () => {
    expect(parseClubRouteParams({ clubId: CLUB })).toEqual({ clubId: CLUB });
  });

  it.each([{ clubId: 'ogrody-33' }, { clubId: [CLUB, CLUB] }, {}, undefined])(
    'refuses %p',
    (params) => {
      expect(parseClubRouteParams(params)).toBeUndefined();
    },
  );
});

describe('an official group’s route params', () => {
  it('reads the club and the group', () => {
    expect(parseOfficialGroupRouteParams({ clubId: CLUB, groupId: GROUP })).toEqual({
      clubId: CLUB,
      groupId: GROUP,
    });
  });

  it.each([{ clubId: CLUB }, { groupId: GROUP }, { clubId: CLUB, groupId: '../../users/me' }])(
    'refuses %p',
    (params) => {
      expect(parseOfficialGroupRouteParams(params)).toBeUndefined();
    },
  );
});
