import type { SearchedClub, GroupAtClub } from '../domain/group';

import type { GamesCard } from '../domain/groupPage';

import {
  approverLine,
  clubLine,
  exitSheetBody,
  infoPolicyLine,
  linkShown,
  memberLine,
  memberRowLabel,
  membersEyebrow,
  membersRowLabel,
  openRecordLabel,
  playSportCount,
  requestLevels,
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

describe('the Info tab', () => {
  it('shows the link without its scheme', () => {
    expect(linkShown('https://raketa.app/join/K7PQ2MXA')).toBe('raketa.app/join/K7PQ2MXA');
    expect(linkShown('http://localhost:3000/join/K7PQ2MXA')).toBe('localhost:3000/join/K7PQ2MXA');
  });

  it('says who answers a request, from where the reader stands', () => {
    expect(infoPolicyLine({ joinPolicy: 'ANYONE', isOwner: true })).toBe('anyone can join');
    expect(infoPolicyLine({ joinPolicy: 'PEOPLE_I_APPROVE', isOwner: true })).toBe(
      'you approve joins',
    );
    expect(infoPolicyLine({ joinPolicy: 'PEOPLE_I_APPROVE', isOwner: false })).toBe(
      'the owner approves joins',
    );
  });

  it('speaks the members row whole, the sports by name', () => {
    expect(
      membersRowLabel({
        memberCount: 8,
        sports: ['padel', 'tennis'],
        joinPolicy: 'ANYONE',
        isOwner: false,
      }),
    ).toBe('8 members, plays Padel, Tennis, anyone can join');
    expect(
      membersRowLabel({ memberCount: 1, sports: [], joinPolicy: 'ANYONE', isOwner: true }),
    ).toBe('1 member, anyone can join');
  });

  // Club 20: full sport names, each with its Level.
  it('lists every sport a person asking is rated in, with its Level', () => {
    expect(
      requestLevels([
        { sport: 'padel', level: 2.44 },
        { sport: 'tennis', level: 2.6 },
      ]),
    ).toBe('Padel 2,44 · Tennis 2,60');
  });

  it('says what leaving does — the handover for an Owner, and the way back in', () => {
    expect(exitSheetBody('leave', { isOwner: false, joinPolicy: 'ANYONE' })).toEqual([
      'You can join again any time with its link.',
    ]);
    expect(exitSheetBody('leave', { isOwner: true, joinPolicy: 'PEOPLE_I_APPROVE' })).toEqual([
      'It passes to whoever has been in it longest, with the requests waiting.',
      'To come back, you ask to join again with its link.',
    ]);
    expect(exitSheetBody('delete', { isOwner: true, joinPolicy: 'ANYONE' })).toEqual([
      'Nobody else is in it. Its link stops working, and the group can’t be brought back.',
    ]);
  });
});

describe('Members', () => {
  it('heads the page with the group’s name and its count', () => {
    expect(membersEyebrow({ name: 'Kazimierz crew', memberCount: 8 })).toBe('Kazimierz crew · 8');
  });

  it('heads the list with the sport and how many play it here', () => {
    expect(playSportCount('padel', 8)).toBe('Play Padel · 8');
  });

  it('reads a row’s Level and Player Score, and no score where there is none', () => {
    expect(memberLine('padel', { level: 2.71, playerScore: 92 })).toBe('Padel 2,71 · score 92');
    expect(memberLine('tennis', { level: 3.1 })).toBe('Tennis 3,10');
  });

  it('speaks a row as who, the admin tag, and the line', () => {
    expect(
      memberRowLabel('padel', {
        name: 'Karol Tomczak',
        level: 2.75,
        playerScore: 93,
        isOwner: true,
        you: false,
      }),
    ).toBe('Karol Tomczak, admin, Padel 2,75 · score 93');
    expect(
      memberRowLabel('padel', { name: 'Tomek Kowal', level: 2.71, isOwner: false, you: true }),
    ).toBe('You, Padel 2,71');
  });

  it('names the record a hold opens', () => {
    expect(openRecordLabel({ name: 'Zofia Bąk', you: false })).toBe('Open Zofia Bąk’s record');
    expect(openRecordLabel({ name: 'Tomek Kowal', you: true })).toBe('Open your record');
  });
});
