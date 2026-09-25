import { parseGroupRouteParams } from './groupRouteParams';

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
