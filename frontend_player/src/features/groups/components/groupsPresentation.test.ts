import type { SearchedClub, GroupAtClub } from '../domain/group';

import type { GamesCard } from '../domain/groupPage';

import {
  approverLine,
  clubLine,
  emptySeatLabel,
  friendsPicked,
  gamesHeadline,
  gamesLine,
  groupRowMeta,
  membersAtClub,
  membersLine,
  seatsFilledLabel,
  shareMessage,
  yourSeatLabel,
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

describe('the group page’s sentences', () => {
  const card = (kind: GamesCard['kind'], rated: number, seats: number): GamesCard => ({
    kind,
    rated,
    seats,
    faces: [],
  });

  it('heads the Games card by how far the seats are from filled', () => {
    expect(gamesHeadline(card('just-you', 1, 4))).toBe('Just you so far');
    expect(gamesHeadline(card('filling', 3, 4))).toBe('3 of 4');
    expect(gamesHeadline(card('nothing-picked', 5, 4))).toBe('Nothing picked right now');
  });

  it('says what the app waits for — the court’s seats, the sport in lower case and the club', () => {
    expect(gamesLine(card('filling', 2, 4), 'badminton', 'Bonarka Arena')).toBe(
      'The app picks games here once 4 who play badminton are in and a court at Bonarka Arena is free. Send the link — it all starts when they arrive.',
    );
  });

  it('says nothing about waiting for people once the seats could be filled', () => {
    expect(gamesLine(card('nothing-picked', 4, 4), 'padel', 'Bonarka Arena')).toBeUndefined();
  });

  it('names an empty seat by where it is, in play’s words', () => {
    expect(emptySeatLabel('YOUR_PARTNER')).toBe('Your side, your partner, empty');
    expect(emptySeatLabel('THEIR_SIDE')).toBe('Their side, empty');
  });

  it('speaks your seat with your Level, and without one when there is none', () => {
    expect(yourSeatLabel('YOUR_SIDE', 2.71)).toBe('Your side, you, level 2,71');
    expect(yourSeatLabel('YOUR_SIDE', undefined)).toBe('Your side, you');
  });

  it('counts a court’s filled seats in play’s summary sentence', () => {
    expect(seatsFilledLabel('tennis', 1, 2)).toBe('Tennis, 1 of 2 seats filled.');
  });

  it('counts the Friends screen’s picks against the seats left', () => {
    expect(friendsPicked('padel', 0, 3)).toBe('Padel · 0 of 3 picked');
  });

  it('shares the link inside one sentence naming the group', () => {
    expect(shareMessage('my raketa group', 'https://raketa.app/join/K7PQ2MXA')).toBe(
      'Join my raketa group on Raketa: https://raketa.app/join/K7PQ2MXA',
    );
  });
});
