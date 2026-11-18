import type { Wire } from '@/test-support/transport';

import {
  toClubCard,
  toEditedGroup,
  toGroup,
  toGroupMembers,
  toHomeClubSearch,
  toHottestGroups,
  toJoinRequests,
  toJoinSearch,
  toMyGroups,
} from './groupMappers';

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_nickname: 'Coach Andrzej',
  administrator_nickname: null,
  is_administrator: false,
  relation: 'REQUESTED',
};

const OGRODY: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000003',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distance_km: 2.4,
  sports: ['TENNIS', 'PADEL'],
  groups: [O3_CLUB],
};

describe('a club as a search answers it', () => {
  it('keeps the club, its distance and its groups with what each is to the reader', () => {
    expect(toClubCard(OGRODY)).toEqual({
      id: OGRODY.id,
      name: 'Ogrody 33',
      district: 'Grzegórzki',
      distanceKm: 2.4,
      sports: ['tennis', 'padel'],
      groups: [
        {
          id: O3_CLUB.id,
          kind: 'PLAYER',
          name: 'Ogrody 33 Club',
          monogram: { letters: 'O3', colourKey: 2 },
          sports: ['padel', 'tennis'],
          memberCount: 11,
          joinPolicy: 'PEOPLE_I_APPROVE',
          ownerName: 'Coach Andrzej',
          administratorName: null,
          isAdministrator: false,
          relation: 'REQUESTED',
        },
      ],
    });
  });

  // #519: an official group is answered for by its Administrator, and its runner joins directly.
  it('keeps an official group’s kind, who runs it, and whether the reader does', () => {
    const official: Wire['GroupAtClubSchema'] = {
      ...O3_CLUB,
      kind: 'OFFICIAL',
      owner_nickname: null,
      administrator_nickname: 'Marta Wójcik',
      is_administrator: true,
    };

    expect(toClubCard({ ...OGRODY, groups: [official] }).groups[0]).toMatchObject({
      kind: 'OFFICIAL',
      ownerName: null,
      administratorName: 'Marta Wójcik',
      isAdministrator: true,
    });
  });

  it('keeps no distance for a reader with no Location area', () => {
    expect(toClubCard({ ...OGRODY, distance_km: null }).distanceKm).toBeNull();
  });

  // A dot with no sport behind it is a colour claiming something.
  it('drops a sport this build cannot name', () => {
    const served = {
      ...OGRODY,
      sports: ['TENNIS', 'PICKLEBALL'],
    } as unknown as Wire['ClubCardSchema'];

    expect(toClubCard(served).sports).toEqual(['tennis']);
  });
});

describe('the two searches', () => {
  it('reads home-club search as text, carrying the text it answered', () => {
    expect(toHomeClubSearch('ogr', { clubs: [OGRODY], next_page: 2 })).toMatchObject({
      text: 'ogr',
      nextPage: 2,
      readAs: 'TEXT',
    });
  });

  it('keeps what join search read the text as', () => {
    const link = 'https://raketa.app/join/ZZZZZZZZ';

    expect(toJoinSearch(link, { clubs: [], next_page: null, read_as: 'LINK' })).toEqual({
      text: link,
      clubs: [],
      nextPage: null,
      readAs: 'LINK',
    });
  });
});

describe('the reader’s groups and a group’s page', () => {
  it('keeps the letters as typed, never re-cased', () => {
    const [group] = toMyGroups({
      groups: [
        {
          id: 'b0000000-0000-4000-8000-000000000001',
          kind: 'PLAYER',
          name: 'my raketa group',
          monogram: { letters: 'mr', colour: 5 },
          sports: [],
          member_count: 1,
          home_club: { id: OGRODY.id, name: 'Ogrody 33' },
        },
      ],
    });

    expect(group?.monogram).toEqual({ letters: 'mr', colourKey: 5 });
  });

  it('reads the page’s count, home club, link and ownership', () => {
    expect(
      toGroup({
        id: 'b0000000-0000-4000-8000-000000000001',
        kind: 'PLAYER',
        name: 'My raketa group',
        monogram: { letters: 'Mr', colour: 3 },
        sports: ['PADEL'],
        member_count: 1,
        home_club: { id: OGRODY.id, name: 'Ogrody 33' },
        link: 'https://raketa.app/join/ABCDEFGH',
        join_policy: 'ANYONE',
        is_owner: true,
        rated_by_sport: [],
        member_faces: [],
        administrator_nickname: null,
        is_administrator: false,
      }),
    ).toMatchObject({
      kind: 'PLAYER',
      memberCount: 1,
      homeClub: { name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      isOwner: true,
    });
  });

  it('carries no declared sports for a player group, which plays what its members are rated in', () => {
    expect(toGroup(PAGE)).not.toHaveProperty('declaredSports');
  });

  // #519: the filter narrows to them, and a reader rated in none is shown what to add.
  // An older build after a sport is added: nothing it could name to add, so the page reads the
  // group as it reads a player group rather than drawing nothing under the tabs.
  it('carries no declared sports when this build can name none of them', () => {
    const official = {
      ...PAGE,
      kind: 'OFFICIAL',
      is_owner: false,
      declared_sports: ['PICKLEBALL'],
    } as unknown as Wire['GroupResponse'];

    expect(toGroup(official)).not.toHaveProperty('declaredSports');
  });

  it('reads an official group’s declared sports, dropping one this build cannot name', () => {
    const official = {
      ...PAGE,
      kind: 'OFFICIAL',
      is_owner: false,
      declared_sports: ['PADEL', 'PICKLEBALL', 'SQUASH'],
    } as unknown as Wire['GroupResponse'];

    expect(toGroup(official)).toMatchObject({
      kind: 'OFFICIAL',
      declaredSports: ['padel', 'squash'],
    });
  });

  // #529: Members names who runs an official group, where its list does not.
  it('reads who runs an official group, and whether the reader does', () => {
    const official: Wire['GroupResponse'] = {
      ...PAGE,
      kind: 'OFFICIAL',
      is_owner: false,
      administrator_nickname: 'Marta Wójcik',
      is_administrator: true,
    };

    expect(toGroup(official)).toMatchObject({
      administratorName: 'Marta Wójcik',
      isAdministrator: true,
    });
    expect(toGroup(PAGE)).toMatchObject({ administratorName: null, isAdministrator: false });
  });

  it('reads each sport’s count and its first faces, in joining order', () => {
    const page: Wire['GroupResponse'] = {
      id: 'b0000000-0000-4000-8000-000000000001',
      kind: 'PLAYER',
      name: 'My raketa group',
      monogram: { letters: 'Mr', colour: 3 },
      sports: ['PADEL'],
      member_count: 3,
      home_club: { id: OGRODY.id, name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      join_policy: 'ANYONE',
      is_owner: true,
      administrator_nickname: null,
      is_administrator: false,
      rated_by_sport: [
        {
          sport: 'PADEL',
          rated_count: 2,
          first_rated: [
            {
              player_id: 'p1',
              nickname: 'Tomek Kowal',
              photo_id: 'f1',
              photo_url: 'https://photos.test/f1',
            },
            { player_id: 'p2', nickname: null },
          ],
        },
        { sport: 'TENNIS', rated_count: 0, first_rated: [] },
      ],
      member_faces: [],
    };

    expect(toGroup(page).ratedBySport).toEqual([
      {
        sport: 'padel',
        ratedCount: 2,
        firstRated: [
          { playerId: 'p1', name: 'Tomek Kowal', photoUrl: 'https://photos.test/f1' },
          // No photograph and no name: the seat is still theirs, drawn as the poster.
          { playerId: 'p2', name: null },
        ],
      },
      { sport: 'tennis', ratedCount: 0, firstRated: [] },
    ]);
  });

  // A roster with no sport behind it is a count claiming something.
  it('drops a roster for a sport this build cannot name', () => {
    const page = {
      id: 'b0000000-0000-4000-8000-000000000001',
      kind: 'PLAYER',
      name: 'My raketa group',
      monogram: { letters: 'Mr', colour: 3 },
      sports: [],
      member_count: 1,
      home_club: { id: OGRODY.id, name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      join_policy: 'ANYONE',
      is_owner: true,
      rated_by_sport: [{ sport: 'PICKLEBALL', rated_count: 1, first_rated: [] }],
      member_faces: [],
    } as unknown as Wire['GroupResponse'];

    expect(toGroup(page).ratedBySport).toEqual([]);
  });
});

const PAGE: Wire['GroupResponse'] = {
  id: 'b0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 8,
  home_club: { id: OGRODY.id, name: 'Centrum Ruchu' },
  link: 'https://raketa.app/join/ABCDEFGH',
  join_policy: 'PEOPLE_I_APPROVE',
  is_owner: true,
  administrator_nickname: null,
  is_administrator: false,
  rated_by_sport: [],
  member_faces: [
    {
      player_id: 'p1',
      nickname: 'Karol Tomczak',
      photo_id: 'f1',
      photo_url: 'https://photos.test/f1',
    },
    { player_id: 'p2', nickname: null },
  ],
};

describe('Info’s members row', () => {
  it('reads the faces in the order served, the photograph only where there is one', () => {
    expect(toGroup(PAGE).memberFaces).toEqual([
      { playerId: 'p1', name: 'Karol Tomczak', photoUrl: 'https://photos.test/f1' },
      { playerId: 'p2', name: null },
    ]);
  });
});

describe('Members, for one sport', () => {
  it('reads each row’s face, Level, points, band, ownership, relation and when they joined, in the order served', () => {
    expect(
      toGroupMembers({
        sport: 'PADEL',
        members: [
          {
            player_id: 'p0',
            nickname: 'Tomek Kowal',
            level: 2.71,
            player_score: 92,
            reliability_band: 'VERY_HIGH',
            is_owner: false,
            is_administrator: false,
            joined_at: '2026-09-20T10:00:00Z',
            relation: 'NONE',
          },
          {
            player_id: 'p1',
            nickname: 'Karol Tomczak',
            photo_id: 'f1',
            photo_url: 'https://photos.test/f1',
            level: 2.75,
            player_score: 75,
            reliability_band: 'HIGH',
            is_owner: true,
            is_administrator: false,
            joined_at: '2026-09-01T10:00:00Z',
            relation: 'ASKED_YOU',
          },
        ],
      }),
    ).toEqual([
      {
        playerId: 'p0',
        name: 'Tomek Kowal',
        level: 2.71,
        playerScore: 92,
        reliabilityBand: 'VERY_HIGH',
        isOwner: false,
        isAdministrator: false,
        relation: 'NONE',
      },
      {
        playerId: 'p1',
        name: 'Karol Tomczak',
        photoUrl: 'https://photos.test/f1',
        level: 2.75,
        playerScore: 75,
        reliabilityBand: 'HIGH',
        isOwner: true,
        isAdministrator: false,
        relation: 'ASKED_YOU',
      },
    ]);
  });

  /**
   * **A band this build cannot name keeps the points and drops the word** (#660): the tag draws
   * the figure on the neutral tint rather than a tone this phone guessed from it.
   */
  it('drops a band it cannot name, and keeps the points', () => {
    const [ewa] = toGroupMembers({
      sport: 'TENNIS',
      members: [
        {
          player_id: 'p2',
          nickname: 'Ewa Mazur',
          level: 2.6,
          player_score: 61,
          reliability_band: 'SHAKY' as Wire['ReliabilityBand'],
          is_owner: false,
          is_administrator: false,
          joined_at: '2026-09-10T10:00:00Z',
          relation: 'NONE',
        },
      ],
    });

    expect(ewa).toMatchObject({ playerScore: 61 });
    expect(ewa).not.toHaveProperty('reliabilityBand');
  });

  it('reads an official group’s Administrator who joined as a player', () => {
    const [marta] = toGroupMembers({
      sport: 'PADEL',
      members: [
        {
          player_id: 'p3',
          nickname: 'Marta Wójcik',
          level: 2.6,
          player_score: 100,
          reliability_band: 'VERY_HIGH',
          is_owner: false,
          is_administrator: true,
          joined_at: '2026-09-01T10:00:00Z',
          relation: 'NONE',
        },
      ],
    });

    expect(marta).toMatchObject({ isOwner: false, isAdministrator: true });
  });
});

describe('the Join requests waiting', () => {
  it('reads who asked, in the order they asked, with every sport they are rated in', () => {
    expect(
      toJoinRequests({
        requests: [
          {
            player_id: 'p3',
            nickname: 'Michał Rogalski',
            levels: [
              { sport: 'PADEL', level: 2.44 },
              { sport: 'TENNIS', level: 2.6 },
            ],
          },
          { player_id: 'p4', nickname: null, levels: [] },
        ],
      }),
    ).toEqual([
      {
        playerId: 'p3',
        name: 'Michał Rogalski',
        levels: [
          { sport: 'padel', level: 2.44 },
          { sport: 'tennis', level: 2.6 },
        ],
      },
      { playerId: 'p4', name: null, levels: [] },
    ]);
  });

  it('drops a Level for a sport this build cannot name', () => {
    const served = {
      requests: [
        {
          player_id: 'p3',
          name: 'Michał Rogalski',
          levels: [
            { sport: 'PICKLEBALL', level: 3 },
            { sport: 'PADEL', level: 2.44 },
          ],
        },
      ],
    } as unknown as Wire['JoinRequestsResponse'];

    expect(toJoinRequests(served)[0]?.levels).toEqual([{ sport: 'padel', level: 2.44 }]);
  });
});

describe('an edit’s answer', () => {
  it('reads the group as the save left it and who the switch to Anyone let in', () => {
    const edited = toEditedGroup({
      group: { ...PAGE, name: 'Kazimierz padel', join_policy: 'ANYONE' },
      admitted: [{ player_id: 'p3', nickname: 'Michał Rogalski' }],
    });

    expect(edited.group).toMatchObject({ name: 'Kazimierz padel', joinPolicy: 'ANYONE' });
    expect(edited.admitted).toEqual([{ playerId: 'p3', name: 'Michał Rogalski' }]);
  });
});

describe('Home’s Hottest groups', () => {
  const OGRODY_HOT: Wire['HottestGroupSchema'] = {
    id: 'a0000000-0000-4000-8000-000000000800',
    kind: 'OFFICIAL',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colour: 2 },
    sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
    member_count: 11,
    join_policy: 'PEOPLE_I_APPROVE',
    run_by: 'Ogrody 33',
    club: { id: 'c0000000-0000-4000-8000-000000000800', name: 'Ogrody 33' },
    games_this_week: 14,
    new_this_month: 3,
    heat_share: 1,
    tag: 'HOTTEST',
    faces: [
      {
        player_id: 'p0000000-0000-4000-8000-000000000801',
        nickname: 'kuba.w',
        photo_url: 'https://photos.test/kuba',
      },
      { player_id: 'p0000000-0000-4000-8000-000000000802', nickname: null },
    ],
    friends_count: 7,
    relation: 'NONE',
    is_administrator: false,
  };

  it('keeps every figure the card and its sheet draw, in the order served', () => {
    expect(toHottestGroups({ groups: [OGRODY_HOT], total: 1 })).toEqual([
      {
        id: OGRODY_HOT.id,
        kind: 'OFFICIAL',
        name: 'Ogrody 33 Club',
        monogram: { letters: 'O3', colourKey: 2 },
        sports: ['padel', 'tennis', 'squash', 'badminton'],
        memberCount: 11,
        joinPolicy: 'PEOPLE_I_APPROVE',
        runBy: 'Ogrody 33',
        club: { id: OGRODY_HOT.club.id, name: 'Ogrody 33' },
        gamesThisWeek: 14,
        newThisMonth: 3,
        tag: 'HOTTEST',
        faces: [
          {
            playerId: 'p0000000-0000-4000-8000-000000000801',
            name: 'kuba.w',
            photoUrl: 'https://photos.test/kuba',
          },
          { playerId: 'p0000000-0000-4000-8000-000000000802', name: null },
        ],
        friendsCount: 7,
        relation: 'NONE',
        isAdministrator: false,
      },
    ]);
  });

  it('carries no tag as none, and an Owner who can no longer be named as nobody', () => {
    const [kazimierz] = toHottestGroups({
      groups: [{ ...OGRODY_HOT, kind: 'PLAYER', tag: null, run_by: null }],
      total: 1,
    });
    expect(kazimierz?.tag).toBeNull();
    expect(kazimierz?.runBy).toBeNull();
  });
});
