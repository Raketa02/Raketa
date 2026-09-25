import type { SearchedClub, GroupAtClub } from '../domain/group';

import {
  approverLine,
  clubLine,
  groupRowMeta,
  membersAtClub,
  membersLine,
} from './groupsPresentation';

const OGRODY: SearchedClub = {
  id: 'club-ogrody',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distanceKm: 2.4,
  sports: ['tennis', 'padel'],
  groups: [],
};

function group(overrides: Partial<GroupAtClub> = {}): GroupAtClub {
  return {
    id: 'group-club',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colourKey: 2 },
    sports: ['padel', 'tennis'],
    memberCount: 11,
    joinPolicy: 'PEOPLE_I_APPROVE',
    ownerName: 'Coach Andrzej',
    relation: 'NONE',
    ...overrides,
  };
}

describe('the approver line', () => {
  it('says anyone can join an Anyone group', () => {
    expect(approverLine(group({ joinPolicy: 'ANYONE' }))).toBe('anyone can join');
  });

  // ADR-0171 §4: the whole Name, never a first name cut from it.
  it('names the Owner whole on a People I approve group', () => {
    expect(approverLine(group({ ownerName: 'Karol Nowak' }))).toBe('Karol Nowak approves joins');
  });

  it('says the owner approves when the Owner can no longer be named', () => {
    expect(approverLine(group({ ownerName: null }))).toBe('the owner approves joins');
  });
});

describe('a group row’s second line', () => {
  it('is the count and who approves', () => {
    expect(groupRowMeta(group())).toBe('11 members · Coach Andrzej approves joins');
  });

  it('counts one member in the singular', () => {
    expect(groupRowMeta(group({ memberCount: 1, joinPolicy: 'ANYONE' }))).toBe(
      '1 member · anyone can join',
    );
  });
});

describe('the members line', () => {
  it('counts members', () => {
    expect(membersLine(8)).toBe('8 members');
    expect(membersLine(1)).toBe('1 member');
  });

  it('names the home club after the count on the group page', () => {
    expect(membersAtClub(1, 'Bonarka Arena')).toBe('1 member · Bonarka Arena');
    expect(membersAtClub(12, 'Ogrody 33')).toBe('12 members · Ogrody 33');
  });
});

describe('a club’s line', () => {
  it('is the district, the distance and the sports', () => {
    expect(clubLine(OGRODY, { distance: true })).toBe('Grzegórzki · 2,4 km · Tennis, Padel');
  });

  // Story 28: nothing pretends to know where a player with no Location area is.
  it('leaves the distance out when the reader’s location is unknown', () => {
    expect(clubLine({ ...OGRODY, distanceKm: null }, { distance: true })).toBe(
      'Grzegórzki · Tennis, Padel',
    );
  });

  // Home-club search rows draw no distance (#512), whatever the server knows.
  it('leaves the distance out where the row does not draw one', () => {
    expect(clubLine(OGRODY, { distance: false })).toBe('Grzegórzki · Tennis, Padel');
  });
});
