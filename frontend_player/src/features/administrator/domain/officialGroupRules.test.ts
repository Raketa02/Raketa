/**
 * The two things the administrator area works out on the phone, with no renderer and no network:
 * when a player joined, as the players list says it, and how much of the WhatsApp group has
 * arrived.
 */

import type { OfficialGroupSettings } from './officialGroup';
import { joinedWhen, playersStack, settingsUnchanged, whatsAppShare } from './officialGroupRules';

const READ_AT = Date.parse('2026-09-26T12:00:00Z');

describe('when a player joined', () => {
  it('is this week within seven days of the read', () => {
    expect(joinedWhen('2026-09-26T11:00:00Z', READ_AT)).toEqual({ kind: 'this-week' });
    expect(joinedWhen('2026-09-19T12:00:01Z', READ_AT)).toEqual({ kind: 'this-week' });
  });

  it('is the day, in the platform’s zone, from seven days on', () => {
    expect(joinedWhen('2026-09-19T12:00:00Z', READ_AT)).toEqual({ kind: 'day', day: '2026-09-19' });
    // 23:30 UTC on the 6th is already the 7th in Warsaw.
    expect(joinedWhen('2026-09-06T23:30:00Z', READ_AT)).toEqual({ kind: 'day', day: '2026-09-07' });
  });

  it('is this week for a moment the phone’s clock has not reached yet', () => {
    expect(joinedWhen('2026-09-27T09:00:00Z', READ_AT)).toEqual({ kind: 'this-week' });
  });

  it('says nothing for a value that is not an instant', () => {
    expect(joinedWhen('yesterday', READ_AT)).toBeUndefined();
  });
});

describe('the share of the WhatsApp group that has arrived', () => {
  it('is the players over the size, as a percentage', () => {
    expect(whatsAppShare(38, 48)).toBeCloseTo(79.17, 2);
    expect(whatsAppShare(0, 48)).toBe(0);
  });

  it('passes 100% when more have arrived than the group has, and says so', () => {
    expect(whatsAppShare(52, 48)).toBeCloseTo(108.33, 2);
  });
});

describe('the players card’s faces', () => {
  const players = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];

  it('draws the five newest, and counts everybody else in the group', () => {
    expect(playersStack(players, 11)).toEqual({ faces: ['a', 'b', 'c', 'd', 'e'], more: 6 });
  });

  it('counts from the group’s count, which a block does not change', () => {
    // Two players hidden from this reader by a block: drawn nowhere, counted all the same.
    expect(playersStack(['a', 'b'], 4)).toEqual({ faces: ['a', 'b'], more: 2 });
  });

  it('counts nobody more with no face drawn, where it would only repeat the count', () => {
    expect(playersStack([], 3)).toEqual({ faces: [], more: 0 });
    expect(playersStack([], 0)).toEqual({ faces: [], more: 0 });
  });
});

describe('whether the settings say what the group already says', () => {
  const GROUP = {
    name: 'Ogrody 33 Club',
    joinPolicy: 'PEOPLE_I_APPROVE',
    whatsAppSize: 48,
    sports: ['padel', 'tennis'],
  } as const;
  const AS_READ: OfficialGroupSettings = { ...GROUP, sports: ['padel', 'tennis'] };

  it('is so when all four are the group’s', () => {
    expect(settingsUnchanged(AS_READ, GROUP)).toBe(true);
  });

  it.each<[string, Partial<OfficialGroupSettings>]>([
    ['a new name', { name: 'Ogrody 33 Klub' }],
    ['a switch to Anyone', { joinPolicy: 'ANYONE' }],
    ['a new WhatsApp group size', { whatsAppSize: 52 }],
    ['a sport added', { sports: ['padel', 'tennis', 'squash'] }],
    ['a sport taken away', { sports: ['tennis'] }],
    ['another sport in place of one', { sports: ['padel', 'squash'] }],
  ])('is not so with %s', (_case, change) => {
    expect(settingsUnchanged({ ...AS_READ, ...change }, GROUP)).toBe(false);
  });
});
