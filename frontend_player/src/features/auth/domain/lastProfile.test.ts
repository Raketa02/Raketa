/** The last profile, as the phone keeps it — written, read back, and anything else it might hold. */

import { profileChoiceFrom, savedProfile, type ProfileChoice } from './lastProfile';

const OGRODY = 'c0000000-0000-4000-8000-000000000033';

describe('the last profile on the phone', () => {
  it.each<ProfileChoice>([{ kind: 'player' }, { kind: 'administrator', clubId: OGRODY }])(
    'reads back %j as it was kept',
    (choice) => {
      expect(profileChoiceFrom(savedProfile(choice))).toEqual(choice);
    },
  );

  it('writes Player and a club as two short strings', () => {
    expect(savedProfile({ kind: 'player' })).toBe('player');
    expect(savedProfile({ kind: 'administrator', clubId: OGRODY })).toBe(`administrator:${OGRODY}`);
  });

  it.each([undefined, '', 'coach', 'administrator:', 'PLAYER'])(
    'reads %p as nothing chosen',
    (saved) => {
      expect(profileChoiceFrom(saved)).toBeUndefined();
    },
  );
});
