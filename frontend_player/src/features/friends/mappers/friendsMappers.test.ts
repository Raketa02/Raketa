import {
  toAskRequest,
  toFriend,
  toFriendRequest,
  toGroupToAddFrom,
  toLevelAskRequest,
} from './friendsMappers';

describe('toAskRequest', () => {
  it('names the group and the sport the screen showed', () => {
    expect(toAskRequest('p-1', { from: 'MEMBERS', groupId: 'g-1', sport: 'padel' })).toEqual({
      player_id: 'p-1',
      made_from: 'MEMBERS',
      group_id: 'g-1',
      sport: 'PADEL',
    });
  });

  it('leaves both off where the screen showed neither', () => {
    expect(toAskRequest('p-1', { from: 'RECORD' })).toEqual({
      player_id: 'p-1',
      made_from: 'RECORD',
    });
  });
});

describe('toFriend', () => {
  it('reads the face, the whole nickname and every sport with its Level and band', () => {
    expect(
      toFriend({
        player_id: 'p-1',
        nickname: 'magda.p',
        photo_id: 'f-1',
        photo_url: 'https://cdn.test/magda.jpg',
        friends_since: '2026-10-01T10:00:00Z',
        level_asked_in: [],
        sports: [
          { sport: 'PADEL', level: 2.66, band: 'Established' },
          { sport: 'TENNIS', level: 3.1, band: 'Developing' },
        ],
      }),
    ).toEqual({
      playerId: 'p-1',
      nickname: 'magda.p',
      photoUrl: 'https://cdn.test/magda.jpg',
      sports: [
        { sport: 'padel', level: 2.66, band: 'Established' },
        { sport: 'tennis', level: 3.1, band: 'Developing' },
      ],
      askedIn: [],
    });
  });

  it('reads every sport you asked them to get a level in, leaving off one this build cannot name', () => {
    expect(
      toFriend({
        player_id: 'p-5',
        nickname: 'zofia.b',
        photo_id: null,
        photo_url: null,
        friends_since: '2026-10-01T10:00:00Z',
        level_asked_in: ['PADEL', 'CURLING' as 'PADEL'],
        sports: [],
      }).askedIn,
    ).toEqual(['padel']);
  });

  it('draws a poster for no photograph, and leaves off a sport this build cannot name', () => {
    expect(
      toFriend({
        player_id: 'p-2',
        nickname: 'ewa.m',
        photo_id: null,
        photo_url: null,
        friends_since: '2026-10-01T10:00:00Z',
        level_asked_in: [],
        sports: [{ sport: 'CURLING' as 'PADEL', level: 2, band: 'Established' }],
      }),
    ).toEqual({ playerId: 'p-2', nickname: 'ewa.m', sports: [], askedIn: [] });
  });
});

describe('toFriendRequest', () => {
  it('reads who, their face, and whether you set it aside', () => {
    expect(
      toFriendRequest({
        player_id: 'p-3',
        nickname: 'ines.d',
        photo_id: null,
        photo_url: null,
        asked_at: '2026-10-01T07:00:00Z',
        set_aside: true,
      }),
    ).toEqual({ playerId: 'p-3', nickname: 'ines.d', setAside: true });
  });
});

describe('toGroupToAddFrom', () => {
  it('reads the name and both counts', () => {
    expect(
      toGroupToAddFrom({ group_id: 'g-1', name: 'Ogrody open play', member_count: 8, to_add: 2 }),
    ).toEqual({ groupId: 'g-1', name: 'Ogrody open play', memberCount: 8, toAdd: 2 });
  });
});

describe('toLevelAskRequest', () => {
  it('names the picker’s sport and the group whose Friends tab it is on', () => {
    expect(toLevelAskRequest('padel', 'g-1')).toEqual({ sport: 'PADEL', group_id: 'g-1' });
  });
});
