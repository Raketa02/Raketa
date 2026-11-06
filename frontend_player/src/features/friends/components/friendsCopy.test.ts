import { requestsHeading, wantsToBeYourFriend, whereLine } from './friendsCopy';

describe('the request card’s words (§29.2)', () => {
  it('names who asks, whole', () => {
    expect(wantsToBeYourFriend('ines.d')).toBe('ines.d wants to be your friend');
  });

  it('says where, the sport and the Level, before the chip', () => {
    expect(
      whereLine({
        byLink: false,
        group: { name: 'Kazimierz crew' },
        sportName: 'Padel',
        level: 3.4,
      }),
    ).toBe('With you in Kazimierz crew · Padel 3,40 ·');
  });

  it('reads Invited you to Raketa for a link’s request', () => {
    expect(whereLine({ byLink: true })).toBe('Invited you to Raketa');
  });

  it('says only what the wire named — a group they left, a sport they hold no Level in', () => {
    expect(whereLine({ byLink: false, sportName: 'Padel' })).toBe('Padel ·');
    expect(whereLine({ byLink: false, group: { name: 'Kazimierz crew' } })).toBe(
      'With you in Kazimierz crew ·',
    );
    expect(whereLine({ byLink: false })).toBe('');
  });

  it('counts the row’s title', () => {
    expect(requestsHeading(1)).toBe('Friend requests · 1');
  });
});
