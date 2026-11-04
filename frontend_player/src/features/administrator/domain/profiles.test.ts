/** What the switcher lists, for each shape of account, and which row is ticked. */

import { isWorn, profileOptions, switcherShown } from './profiles';

const OGRODY = { clubId: 'c0000000-0000-4000-8000-000000000033', clubName: 'Ogrody 33' };
const BONARKA = { clubId: 'c0000000-0000-4000-8000-000000000044', clubName: 'Bonarka Arena' };

describe('the profiles an account can switch between', () => {
  it('lists Player first, then one per club in the server’s order', () => {
    expect(
      profileOptions({
        nickname: 'Tomek Kowal',
        profiles: { actsAsPlayer: true, administers: [BONARKA, OGRODY] },
      }),
    ).toEqual([
      { kind: 'player', name: 'Tomek Kowal' },
      { kind: 'administrator', ...BONARKA },
      { kind: 'administrator', ...OGRODY },
    ]);
  });

  it('lists no Player for an account that does not play', () => {
    expect(
      profileOptions({
        nickname: 'Marta Nowak',
        profiles: { actsAsPlayer: false, administers: [OGRODY] },
      }),
    ).toEqual([{ kind: 'administrator', ...OGRODY }]);
  });

  it.each([
    ['only plays', { actsAsPlayer: true, administers: [] }, false],
    ['runs one club and does not play', { actsAsPlayer: false, administers: [OGRODY] }, false],
    ['plays and runs a club', { actsAsPlayer: true, administers: [OGRODY] }, true],
    ['runs two clubs', { actsAsPlayer: false, administers: [OGRODY, BONARKA] }, true],
  ])('draws the switcher for an account that %s: %p', (_, held, shown) => {
    const options = profileOptions({ nickname: 'Ada', profiles: { ...held } });
    expect(switcherShown(options)).toBe(shown);
  });

  it('ticks the profile worn, and only that one', () => {
    const [player, ogrody, bonarka] = profileOptions({
      nickname: 'Tomek Kowal',
      profiles: { actsAsPlayer: true, administers: [OGRODY, BONARKA] },
    });
    const worn = { kind: 'administrator', clubId: OGRODY.clubId } as const;

    expect([player, ogrody, bonarka].map((option) => option && isWorn(option, worn))).toEqual([
      false,
      true,
      false,
    ]);
  });
});
