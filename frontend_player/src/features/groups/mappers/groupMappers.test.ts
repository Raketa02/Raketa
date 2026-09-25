import type { Wire } from '@/test-support/transport';

import { toClubCard, toGroup, toHomeClubSearch, toJoinSearch, toMyGroups } from './groupMappers';

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000001',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_name: 'Coach Andrzej',
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
          name: 'Ogrody 33 Club',
          monogram: { letters: 'O3', colourKey: 2 },
          sports: ['padel', 'tennis'],
          memberCount: 11,
          joinPolicy: 'PEOPLE_I_APPROVE',
          ownerName: 'Coach Andrzej',
          relation: 'REQUESTED',
        },
      ],
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
        name: 'My raketa group',
        monogram: { letters: 'Mr', colour: 3 },
        sports: ['PADEL'],
        member_count: 1,
        home_club: { id: OGRODY.id, name: 'Ogrody 33' },
        link: 'https://raketa.app/join/ABCDEFGH',
        join_policy: 'ANYONE',
        is_owner: true,
        rated_by_sport: [],
      }),
    ).toMatchObject({
      memberCount: 1,
      homeClub: { name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      isOwner: true,
    });
  });

  it('reads each sport’s count and its first faces, in joining order', () => {
    const page: Wire['GroupResponse'] = {
      id: 'b0000000-0000-4000-8000-000000000001',
      name: 'My raketa group',
      monogram: { letters: 'Mr', colour: 3 },
      sports: ['PADEL'],
      member_count: 3,
      home_club: { id: OGRODY.id, name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      join_policy: 'ANYONE',
      is_owner: true,
      rated_by_sport: [
        {
          sport: 'PADEL',
          rated_count: 2,
          first_rated: [
            {
              player_id: 'p1',
              name: 'Tomek Kowal',
              photo_id: 'f1',
              photo_url: 'https://photos.test/f1',
            },
            { player_id: 'p2', name: null },
          ],
        },
        { sport: 'TENNIS', rated_count: 0, first_rated: [] },
      ],
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
      name: 'My raketa group',
      monogram: { letters: 'Mr', colour: 3 },
      sports: [],
      member_count: 1,
      home_club: { id: OGRODY.id, name: 'Ogrody 33' },
      link: 'https://raketa.app/join/ABCDEFGH',
      join_policy: 'ANYONE',
      is_owner: true,
      rated_by_sport: [{ sport: 'PICKLEBALL', rated_count: 1, first_rated: [] }],
    } as unknown as Wire['GroupResponse'];

    expect(toGroup(page).ratedBySport).toEqual([]);
  });
});
