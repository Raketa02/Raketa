import type { HottestGroup } from './group';
import {
  CARD_FACES,
  SHEET_FACES,
  cardFaces,
  isJoinTap,
  joinHottestPages,
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
    const row = { groups: [group(), kazimierz], total: 2 };

    const asked = withRelation(row, 'g-ogrody', 'REQUESTED');

    expect(asked.groups[0]?.relation).toBe('REQUESTED');
    expect(asked.groups[1]).toBe(kazimierz);
  });

  /** #822: the count moves with the line's read, never with a card's guess. */
  it('keeps the row’s total', () => {
    expect(withRelation({ groups: [group()], total: 38 }, 'g-ogrody', 'MEMBER').total).toBe(38);
  });

  /** #823: the page's cards move as the row's do, so the page and Home's line agree. */
  it('turns the one card on a page of Groups heating up, and keeps its cursor', () => {
    const page = { groups: [group(), group({ id: 'g-kazimierz' })], next: 'c-20' };

    const joined = withRelation(page, 'g-kazimierz', 'MEMBER');

    expect(joined.groups.map((each) => each.relation)).toEqual(['NONE', 'MEMBER']);
    expect(joined.next).toBe('c-20');
  });
});

describe('Groups heating up, page by page', () => {
  it('lists the pages in the order read', () => {
    const pages = [
      { groups: [group({ id: 'g-1' }), group({ id: 'g-2' })], next: 'c-2' },
      { groups: [group({ id: 'g-3' })] },
    ];

    expect(joinHottestPages(pages).map((each) => each.id)).toEqual(['g-1', 'g-2', 'g-3']);
  });

  /** The mechanics §5.10: heat is worked out on every read, so a group that cooled is read again. */
  it('draws a group a later page reads again only once, where it was first drawn', () => {
    const pages = [
      { groups: [group({ id: 'g-1' }), group({ id: 'g-2' })], next: 'c-2' },
      { groups: [group({ id: 'g-2', gamesThisWeek: 1 }), group({ id: 'g-3' })] },
    ];

    const listed = joinHottestPages(pages);

    expect(listed.map((each) => each.id)).toEqual(['g-1', 'g-2', 'g-3']);
    expect(listed[1]?.gamesThisWeek).toBe(14);
  });

  it('is empty before any page holds a group', () => {
    expect(joinHottestPages([{ groups: [] }])).toEqual([]);
  });
});
