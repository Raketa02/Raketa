/**
 * The wire boundary for the administrator's official groups — what crosses, in the app's
 * spelling, and what a build that cannot name a sport drops.
 */

import type { components } from '@/generated/schema';

import {
  toAdministeredGroups,
  toOfficialGroup,
  toSavedSettings,
  toSettingsRequest,
} from './administratorMappers';

type Schemas = components['schemas'];

const CLUB: Schemas['OfficialGroupClubSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000033',
  name: 'Ogrody 33',
  sports: ['PADEL', 'TENNIS'],
};

describe('the Groups tab’s read', () => {
  it('carries the club, and each card with who is waiting', () => {
    expect(
      toAdministeredGroups({
        club: CLUB,
        groups: [
          {
            id: 'a0000000-0000-4000-8000-000000000001',
            kind: 'OFFICIAL',
            name: 'Ogrody 33 Club',
            monogram: { letters: 'O3', colour: 1 },
            sports: ['PADEL', 'TENNIS'],
            member_count: 11,
            waiting_count: 1,
            home_club: { id: CLUB.id, name: CLUB.name },
          },
        ],
      }),
    ).toEqual({
      club: { id: CLUB.id, name: 'Ogrody 33', sports: ['padel', 'tennis'] },
      groups: [
        {
          id: 'a0000000-0000-4000-8000-000000000001',
          name: 'Ogrody 33 Club',
          monogram: { letters: 'O3', colourKey: 1 },
          sports: ['padel', 'tennis'],
          memberCount: 11,
          waitingCount: 1,
          homeClub: { id: CLUB.id, name: 'Ogrody 33' },
        },
      ],
    });
  });

  it('drops a sport this build cannot name', () => {
    const wire = {
      club: { ...CLUB, sports: ['PADEL', 'PICKLEBALL'] },
      groups: [],
    } as unknown as Schemas['AdministeredGroupsResponse'];

    expect(toAdministeredGroups(wire).club.sports).toEqual(['padel']);
  });
});

describe('an official group’s page', () => {
  const PAGE: Schemas['AdministeredGroupResponse'] = {
    id: 'a0000000-0000-4000-8000-000000000001',
    kind: 'OFFICIAL',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colour: 1 },
    sports: ['PADEL'],
    member_count: 2,
    home_club: CLUB,
    link: 'https://raketa.app/join/K7PQ2MXA',
    join_policy: 'PEOPLE_I_APPROVE',
    whatsapp_size: 48,
    players: [
      {
        player_id: 'p1',
        name: 'Ania Kowalczyk',
        photo_id: 'f1',
        photo_url: 'https://photos.test/f1',
        joined_at: '2026-09-07T18:00:00Z',
      },
      { player_id: 'p2', name: null, joined_at: '2026-08-31T10:00:00Z' },
    ],
    requests: [
      {
        player_id: 'p3',
        name: 'Michał Rogalski',
        levels: [
          { sport: 'PADEL', level: 2.44 },
          { sport: 'TENNIS', level: 2.6 },
        ],
      },
    ],
  };

  it('carries the link, the settings, the players and the requests', () => {
    expect(toOfficialGroup(PAGE)).toEqual({
      id: PAGE.id,
      name: 'Ogrody 33 Club',
      monogram: { letters: 'O3', colourKey: 1 },
      sports: ['padel'],
      memberCount: 2,
      homeClub: { id: CLUB.id, name: 'Ogrody 33', sports: ['padel', 'tennis'] },
      link: 'https://raketa.app/join/K7PQ2MXA',
      joinPolicy: 'PEOPLE_I_APPROVE',
      whatsAppSize: 48,
      players: [
        { playerId: 'p1', name: 'Ania Kowalczyk', photoUrl: 'https://photos.test/f1' },
        // No photograph, and nobody to name: the seat is kept, the poster stands in.
        { playerId: 'p2', name: null },
      ],
      requests: [
        {
          playerId: 'p3',
          name: 'Michał Rogalski',
          levels: [
            { sport: 'padel', level: 2.44 },
            { sport: 'tennis', level: 2.6 },
          ],
        },
      ],
    });
  });

  it('carries no photograph key where there is none', () => {
    expect(toOfficialGroup(PAGE).players[1]).not.toHaveProperty('photoUrl');
  });
});

describe('a settings save’s answer', () => {
  const GROUP: Schemas['AdministeredGroupResponse'] = {
    id: 'a0000000-0000-4000-8000-000000000001',
    kind: 'OFFICIAL',
    name: 'Ogrody 33 Club',
    monogram: { letters: 'O3', colour: 1 },
    sports: ['PADEL'],
    member_count: 4,
    home_club: CLUB,
    link: 'https://raketa.app/join/K7PQ2MXA',
    join_policy: 'ANYONE',
    whatsapp_size: 52,
    players: [],
    requests: [],
  };

  it('carries the group as saved, and who the switch let in, in the order they asked', () => {
    const saved = toSavedSettings({
      group: GROUP,
      admitted: [
        {
          player_id: 'p3',
          name: 'Michał Rogalski',
          photo_id: 'f3',
          photo_url: 'https://photos.test/f3',
        },
        { player_id: 'p7', name: null },
      ],
    });

    expect(saved.group).toEqual(toOfficialGroup(GROUP));
    expect(saved.admitted).toEqual([
      { playerId: 'p3', name: 'Michał Rogalski', photoUrl: 'https://photos.test/f3' },
      { playerId: 'p7', name: null },
    ]);
    expect(saved.admitted[1]).not.toHaveProperty('photoUrl');
  });
});

describe('the group to create, and its settings', () => {
  it('is the wire’s spelling of the four fields', () => {
    expect(
      toSettingsRequest({
        name: 'Ogrody 33 Club',
        joinPolicy: 'ANYONE',
        whatsAppSize: 48,
        sports: ['padel', 'squash'],
      }),
    ).toEqual({
      name: 'Ogrody 33 Club',
      join_policy: 'ANYONE',
      whatsapp_size: 48,
      sports: ['PADEL', 'SQUASH'],
    });
  });
});
