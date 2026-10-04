import { groupDetailsFrom } from './groupDetailsForm';

describe('what an Edit group form saves', () => {
  it('is the name and who can join', () => {
    expect(groupDetailsFrom({ name: 'Kazimierz padel', joinPolicy: 'ANYONE' })).toEqual({
      name: 'Kazimierz padel',
      joinPolicy: 'ANYONE',
    });
  });

  // The server trims before it counts; the form sends what it would keep.
  it('sends the name trimmed', () => {
    expect(groupDetailsFrom({ name: '  Kazimierz crew ', joinPolicy: 'ANYONE' })?.name).toBe(
      'Kazimierz crew',
    );
  });

  it('saves nothing for a name that is only spaces', () => {
    expect(groupDetailsFrom({ name: '   ', joinPolicy: 'ANYONE' })).toBeUndefined();
  });

  it('saves nothing for a name longer than 40 characters', () => {
    expect(groupDetailsFrom({ name: 'x'.repeat(41), joinPolicy: 'ANYONE' })).toBeUndefined();
    expect(groupDetailsFrom({ name: 'x'.repeat(40), joinPolicy: 'ANYONE' })).toBeDefined();
  });
});
