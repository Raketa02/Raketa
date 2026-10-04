import type { SearchedClub, GroupAtClub } from '../domain/group';

import type { GamesCard } from '../domain/groupPage';

import {
  addSportHeadline,
  addSportLabel,
  addSportLine,
  approverLine,
  clubLine,
  exitSheetBody,
  infoPolicyLine,
  linkShown,
  memberLine,
  memberRowLabel,
  membersTitle,
  membersRowLabel,
  openRecordHint,
  requestLevels,
  requestTags,
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
    kind: 'PLAYER',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colourKey: 2 },
    sports: ['padel', 'tennis'],
    memberCount: 11,
    joinPolicy: 'PEOPLE_I_APPROVE',
    ownerName: 'Coach Andrzej',
    administratorName: null,
    isAdministrator: false,
    relation: 'NONE',
    ...overrides,
  };
}

function official(overrides: Partial<GroupAtClub> = {}): GroupAtClub {
  return group({
    kind: 'OFFICIAL',
    ownerName: null,
    administratorName: 'Marta Wójcik',
    ...overrides,
  });
}

describe('the approver line', () => {
  it('says anyone can join an Anyone group', () => {
    expect(approverLine(group({ joinPolicy: 'ANYONE' }))).toBe('anyone can join');
    expect(approverLine(official({ joinPolicy: 'ANYONE' }))).toBe('anyone can join');
  });

  // #529: who approves was too long for the row; that somebody does is what the reader needs.
  it('says a People I approve group needs approval, whoever answers', () => {
    expect(approverLine(group({ ownerName: 'Karol Nowak' }))).toBe('Needs approval');
    expect(approverLine(group({ ownerName: null }))).toBe('Needs approval');
    expect(approverLine(official())).toBe('Needs approval');
    expect(approverLine(official({ administratorName: null }))).toBe('Needs approval');
  });
});

describe('a group row’s second line', () => {
  it('is the count and whether it needs approval', () => {
    expect(groupRowMeta(group())).toBe('11 members · Needs approval');
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
    expect(clubLine(OGRODY)).toBe('Grzegórzki · 2,4 km · Tennis, Padel');
  });

  // Story 28: nothing pretends to know where a player with no Location area is.
  it('leaves the distance out when the reader’s location is unknown', () => {
    expect(clubLine({ ...OGRODY, distanceKm: null })).toBe('Grzegórzki · Tennis, Padel');
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
    const player = { kind: 'PLAYER' } as const;
    expect(infoPolicyLine({ ...player, joinPolicy: 'ANYONE', isOwner: true })).toBe(
      'anyone can join',
    );
    expect(infoPolicyLine({ ...player, joinPolicy: 'PEOPLE_I_APPROVE', isOwner: true })).toBe(
      'you approve joins',
    );
    expect(infoPolicyLine({ ...player, joinPolicy: 'PEOPLE_I_APPROVE', isOwner: false })).toBe(
      'the owner approves joins',
    );
  });

  // #519: an official group has no Owner, and its read names nobody.
  it('says the administrator approves on an official group', () => {
    expect(
      infoPolicyLine({ kind: 'OFFICIAL', joinPolicy: 'PEOPLE_I_APPROVE', isOwner: false }),
    ).toBe('the administrator approves joins');
    expect(infoPolicyLine({ kind: 'OFFICIAL', joinPolicy: 'ANYONE', isOwner: false })).toBe(
      'anyone can join',
    );
  });

  it('speaks the members row whole, the sports by name', () => {
    expect(
      membersRowLabel({
        kind: 'PLAYER',
        memberCount: 8,
        sports: ['padel', 'tennis'],
        joinPolicy: 'ANYONE',
        isOwner: false,
      }),
    ).toBe('8 members, plays Padel, Tennis, anyone can join');
    expect(
      membersRowLabel({
        kind: 'PLAYER',
        memberCount: 1,
        sports: [],
        joinPolicy: 'ANYONE',
        isOwner: true,
      }),
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

  // #529: four sports over two lines made the row untidy — two tags, and the rest counted.
  it('draws a request’s first two sports as short tags, in the order served, and counts the rest', () => {
    const four = [
      { sport: 'padel', level: 2.71 },
      { sport: 'tennis', level: 3.1 },
      { sport: 'squash', level: 2.3 },
      { sport: 'badminton', level: 2.05 },
    ] as const;

    const drawn = (levels: Parameters<typeof requestTags>[0]) => {
      const { shown, more } = requestTags(levels);
      return [
        ...shown.map((tag) => `${tag.sport}: ${tag.label}`),
        ...(more === undefined ? [] : [more]),
      ];
    };

    expect(drawn(four)).toEqual(['padel: Pad 2,71', 'tennis: Ten 3,10', '+2']);
    expect(drawn(four.slice(0, 3))).toEqual(['padel: Pad 2,71', 'tennis: Ten 3,10', '+1']);
    expect(drawn(four.slice(1, 3))).toEqual(['tennis: Ten 3,10', 'squash: Squ 2,30']);
    expect(drawn(four.slice(3))).toEqual(['badminton: Bad 2,05']);
  });

  it('says what leaving does — the handover for an Owner, and the way back in', () => {
    expect(exitSheetBody('leave', { isOwner: false, joinPolicy: 'ANYONE' })).toEqual([
      'You can join again any time with its link.',
    ]);
    expect(exitSheetBody('leave', { isOwner: true, joinPolicy: 'PEOPLE_I_APPROVE' })).toEqual([
      'It passes to whoever has been in it longest, with the requests waiting.',
      'To come back, you ask to join again.',
    ]);
    expect(exitSheetBody('delete', { isOwner: true, joinPolicy: 'ANYONE' })).toEqual([
      'Nobody else is in it. Its link stops working, and the group can’t be brought back.',
    ]);
  });
});

describe('Members', () => {
  it('titles the screen with how many play the sport here, and the word alone before it is known', () => {
    expect(membersTitle(8)).toBe('Members · 8');
    expect(membersTitle(undefined)).toBe('Members');
  });

  it('reads a row’s line as the sport and its Level — the score is the tag beside the name', () => {
    expect(memberLine('padel', { level: 2.71 })).toBe('Padel 2,71');
    expect(memberLine('tennis', { level: 3.1 })).toBe('Tennis 3,10');
  });

  it('speaks a row as it is drawn: who, the score tag, the admin tag, and the line', () => {
    expect(
      memberRowLabel('padel', {
        name: 'Karol Tomczak',
        level: 2.75,
        playerScore: 93,
        isOwner: true,
        isAdministrator: false,
        you: false,
      }),
    ).toBe('Karol Tomczak, score 93, admin, Padel 2,75');
    expect(
      memberRowLabel('padel', {
        name: 'Tomek Kowal',
        level: 2.71,
        isOwner: false,
        isAdministrator: false,
        you: true,
      }),
    ).toBe('You, Padel 2,71');
  });

  it('speaks an official group’s Administrator who joined as a player with the admin tag', () => {
    expect(
      memberRowLabel('padel', {
        name: 'Marta Wójcik',
        level: 2.6,
        isOwner: false,
        isAdministrator: true,
        you: false,
      }),
    ).toBe('Marta Wójcik, admin, Padel 2,60');
  });

  it('hints what a tap on a row opens — the name is already the row’s', () => {
    expect(openRecordHint({ you: false })).toBe('Opens their record');
    expect(openRecordHint({ you: true })).toBe('Opens your record');
  });
});

describe('an official group for a player rated in none of its sports', () => {
  // Story 57: the sports in lower case mid-line, as the page's other sentences write them.
  it('says what the group plays and what to add', () => {
    expect(addSportHeadline(['padel'])).toBe('This group plays padel');
    expect(addSportLine(['padel'])).toBe('Add padel to your Skill passport to see its games.');
  });

  it('names every sport it plays, and any one of them to add', () => {
    expect(addSportHeadline(['padel', 'squash'])).toBe('This group plays padel and squash');
    expect(addSportLine(['padel', 'squash'])).toBe(
      'Add padel or squash to your Skill passport to see its games.',
    );
    expect(addSportHeadline(['padel', 'tennis', 'badminton'])).toBe(
      'This group plays padel, tennis and badminton',
    );
    expect(addSportLine(['padel', 'tennis', 'badminton'])).toBe(
      'Add padel, tennis or badminton to your Skill passport to see its games.',
    );
  });

  it('names each sport’s button by what it adds', () => {
    expect(addSportLabel('padel')).toBe('Add Padel');
  });
});
