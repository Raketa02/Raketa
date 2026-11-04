import { lastControlLabel, rateNextLabel } from './resultPresentation';

describe('the last control on Your rating', () => {
  it('names the group a pass begun there goes back to', () => {
    expect(lastControlLabel({ kind: 'group' }, 'Padel at Kazimierz')).toBe(
      'Back to Padel at Kazimierz',
    );
  });

  it('still says where it goes while the group’s name is being read', () => {
    expect(lastControlLabel({ kind: 'group' }, undefined)).toBe('Back to the group');
  });

  it.each([{ kind: 'passport' }, { kind: 'closing' }, { kind: 'app' }] as const)(
    'is See your ratings for %p, whatever group is named',
    (destination) => {
      expect(lastControlLabel(destination, 'Padel at Kazimierz')).toBe('See your ratings');
    },
  );
});

describe('the next sport on Your rating', () => {
  it('names it', () => {
    expect(rateNextLabel('tennis')).toBe('Rate Tennis');
  });
});
