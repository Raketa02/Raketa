/**
 * The New official group form's one schema — *Create the group* is pressable exactly when this
 * answers a group (club 10, #516).
 */

import {
  newOfficialGroupFrom,
  whatsAppSizeFrom,
  type OfficialGroupForm,
} from './newOfficialGroupForm';

const OGRODY_SPORTS = ['padel', 'tennis', 'squash'] as const;

const FILLED: OfficialGroupForm = {
  name: 'Ogrody 33 Club',
  joinPolicy: 'PEOPLE_I_APPROVE',
  whatsAppSize: '48',
  sports: ['padel'],
};

describe('the WhatsApp group size', () => {
  it.each([
    ['2', 2],
    ['48', 48],
    ['1024', 1024],
    [' 48 ', 48],
  ])('reads %p as %p', (typed, size) => {
    expect(whatsAppSizeFrom(typed)).toBe(size);
  });

  it.each(['', '1', '1025', '4.5', '-3', '48 people', '1e2'])('is not %p', (typed) => {
    expect(whatsAppSizeFrom(typed)).toBeUndefined();
  });
});

describe('the group the form answers', () => {
  it('is the four fields, the name trimmed and the size a number', () => {
    expect(newOfficialGroupFrom({ ...FILLED, name: '  Ogrody 33 Club ' }, OGRODY_SPORTS)).toEqual({
      name: 'Ogrody 33 Club',
      joinPolicy: 'PEOPLE_I_APPROVE',
      whatsAppSize: 48,
      sports: ['padel'],
    });
  });

  it('puts the sports in the registry’s order, whatever order they were ticked in', () => {
    expect(
      newOfficialGroupFrom({ ...FILLED, sports: ['squash', 'padel'] }, OGRODY_SPORTS)?.sports,
    ).toEqual(['padel', 'squash']);
  });

  it.each<[string, Partial<OfficialGroupForm>]>([
    ['a blank name', { name: '   ' }],
    ['a name past 40 characters', { name: 'x'.repeat(41) }],
    ['no WhatsApp group size', { whatsAppSize: '' }],
    ['a size out of range', { whatsAppSize: '1' }],
    ['no sport', { sports: [] }],
    ['a sport the club does not offer', { sports: ['padel', 'badminton'] }],
  ])('is nothing with %s', (_case, change) => {
    expect(newOfficialGroupFrom({ ...FILLED, ...change }, OGRODY_SPORTS)).toBeUndefined();
  });
});
