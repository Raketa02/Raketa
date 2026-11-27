import type { SearchedClub } from '../domain/group';

import { newGroupFrom, type NewGroupForm } from './newGroupForm';

const BONARKA: SearchedClub = {
  id: 'c0000000-0000-4000-8000-000000000002',
  name: 'Bonarka Arena',
  district: 'Bonarka',
  distanceKm: 3.1,
  sports: ['padel', 'badminton'],
  groups: [],
};

function form(overrides: Partial<NewGroupForm> = {}): NewGroupForm {
  return { name: 'My rakieta group', homeClub: BONARKA, joinPolicy: 'ANYONE', ...overrides };
}

describe('the group a New group form creates', () => {
  it('is the name, the home club and who can join', () => {
    expect(newGroupFrom(form({ joinPolicy: 'PEOPLE_I_APPROVE' }))).toEqual({
      name: 'My rakieta group',
      homeClubId: BONARKA.id,
      joinPolicy: 'PEOPLE_I_APPROVE',
    });
  });

  // The server trims before it counts; the form sends what it would keep.
  it('sends the name trimmed', () => {
    expect(newGroupFrom(form({ name: '  Kazimierz crew ' }))?.name).toBe('Kazimierz crew');
  });

  it('is nothing without a home club — it is required', () => {
    expect(newGroupFrom(form({ homeClub: undefined }))).toBeUndefined();
  });

  it('is nothing without a name', () => {
    expect(newGroupFrom(form({ name: '' }))).toBeUndefined();
  });

  it('is nothing with a name that is only spaces', () => {
    expect(newGroupFrom(form({ name: '   ' }))).toBeUndefined();
  });

  it('is nothing with neither', () => {
    expect(newGroupFrom(form({ name: '', homeClub: undefined }))).toBeUndefined();
  });

  it('is nothing with a name past 40 characters', () => {
    expect(newGroupFrom(form({ name: 'x'.repeat(41) }))).toBeUndefined();
    expect(newGroupFrom(form({ name: 'x'.repeat(40) }))?.name).toHaveLength(40);
  });
});
