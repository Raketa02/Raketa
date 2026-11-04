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

  it('is the passport’s own for a pass begun there, whatever group is named', () => {
    // The Skill passport *is* your ratings.
    expect(lastControlLabel({ kind: 'passport' }, 'Padel at Kazimierz')).toBe('See your ratings');
  });

  it('goes back to Home for a pass begun there, whatever group is named', () => {
    // ADR-0200 §5 — and no summary any more: *Your starting ratings* went with #730.
    expect(lastControlLabel({ kind: 'home' }, 'Padel at Kazimierz')).toBe('Back to Home');
  });
});

describe('the next sport on Your rating', () => {
  it('names it', () => {
    expect(rateNextLabel('tennis')).toBe('Rate Tennis');
  });
});
