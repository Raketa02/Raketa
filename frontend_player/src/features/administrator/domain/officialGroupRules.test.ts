/**
 * What the administrator area works out on the phone, with no renderer and no network: how much of
 * the group has arrived, which faces the players card draws, and whether the settings changed.
 */

import type { OfficialGroupSettings } from './officialGroup';
import { playersStack, settingsUnchanged, whatsAppShare } from './officialGroupRules';

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
