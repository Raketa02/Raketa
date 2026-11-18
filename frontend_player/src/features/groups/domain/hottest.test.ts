import type { HottestGroup } from './group';
import {
  CARD_FACES,
  SHEET_FACES,
  cardFaces,
  isJoinTap,
  sheetButton,
  sheetFaces,
  withRelation,
} from './hottest';

const face = (n: number) => ({ playerId: `p${n}`, name: `player.${n}` });

function group(overrides: Partial<HottestGroup> = {}): HottestGroup {
  return {
    id: 'g-ogrody',
    kind: 'OFFICIAL',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colourKey: 2 },
    sports: ['padel', 'tennis'],
    memberCount: 11,
    joinPolicy: 'PEOPLE_I_APPROVE',
    runBy: 'Ogrody 33',
    club: { id: 'c-ogrody', name: 'Ogrody 33' },
    gamesThisWeek: 14,
    newThisMonth: 3,
    tag: 'HOTTEST',
    faces: [1, 2, 3, 4, 5, 6].map(face),
    friendsCount: 7,
    relation: 'NONE',
    isAdministrator: false,
    ...overrides,
  };
}

describe('a tap that writes', () => {
  it('is Join or Ask to join, never Asked, You’re in or Open group', () => {
    expect(isJoinTap('join')).toBe(true);
    expect(isJoinTap('ask')).toBe(true);
    expect(isJoinTap('requested')).toBe(false);
    expect(isJoinTap('in')).toBe(false);
    expect(isJoinTap('open')).toBe(false);
  });
});

describe('the group sheet’s one button', () => {
  it('opens the group for a member, and is the chip’s word for everybody else', () => {
    expect(sheetButton(group({ relation: 'MEMBER' }))).toBe('open');
    expect(sheetButton(group({ relation: 'REQUESTED' }))).toBe('requested');
    expect(sheetButton(group({ joinPolicy: 'ANYONE' }))).toBe('join');
    expect(sheetButton(group())).toBe('ask');
  });

  // The mechanics §5.7: an Administrator who runs an official group joins it directly.
  it('is Join for the Administrator who runs it, whatever its policy', () => {
    expect(sheetButton(group({ isAdministrator: true }))).toBe('join');
  });
});

describe('the faces', () => {
  it('draws the first four on the card and the six on the sheet, in the order served', () => {
    expect(cardFaces(group()).map((person) => person.playerId)).toEqual(['p1', 'p2', 'p3', 'p4']);
    expect(sheetFaces(group())).toHaveLength(SHEET_FACES);
    expect(CARD_FACES).toBe(4);
  });

  it('draws the faces a small group has', () => {
    const three = group({ faces: [1, 2].map(face), memberCount: 3 });
    expect(cardFaces(three)).toHaveLength(2);
    expect(sheetFaces(three)).toHaveLength(2);
  });
});

describe('a write’s relation, on the card it came from', () => {
  it('turns the one card and leaves the rest', () => {
    const kazimierz = group({ id: 'g-kazimierz', relation: 'MEMBER' });
    const row = [group(), kazimierz];

    const asked = withRelation(row, 'g-ogrody', 'REQUESTED');

    expect(asked[0]?.relation).toBe('REQUESTED');
    expect(asked[1]).toBe(kazimierz);
  });
});
