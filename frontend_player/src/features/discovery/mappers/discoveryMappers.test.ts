import type { components } from '@/generated/schema';

import { toJoiner, toJoinerPage } from './discoveryMappers';

type Wire = components['schemas'];

const BARTEK: Wire['NewInRaketaPlayerSchema'] = {
  player_id: 'p-bartek',
  nickname: 'bartek.l',
  photo_id: 'f-1',
  photo_url: 'https://photos.example/bartek.jpg',
  joined_at: '2026-11-12T10:00:00Z',
  days_since_joined: 2,
  sports: [
    { sport: 'PADEL', level: 2.35 },
    { sport: 'BADMINTON', level: 2.1 },
  ],
  relation: 'NONE',
};

describe('toJoiner', () => {
  it('reads the face, the nickname, the days, every sport with its level, and the relation', () => {
    expect(toJoiner(BARTEK)).toEqual({
      playerId: 'p-bartek',
      nickname: 'bartek.l',
      photoUrl: 'https://photos.example/bartek.jpg',
      daysSinceJoined: 2,
      sports: [
        { sport: 'padel', level: 2.35 },
        { sport: 'badminton', level: 2.1 },
      ],
      relation: 'NONE',
    });
  });

  it('draws the poster with no photo, and no sport lines with no level', () => {
    const ola = toJoiner({ ...BARTEK, photo_id: null, photo_url: null, sports: [] });
    expect(ola).not.toHaveProperty('photoUrl');
    expect(ola.sports).toEqual([]);
  });

  it('leaves out a sport this build cannot name, and keeps the rest', () => {
    const sports = toJoiner({
      ...BARTEK,
      sports: [
        { sport: 'CURLING' as Wire['Sport'], level: 3 },
        { sport: 'TENNIS', level: 2.6 },
      ],
    }).sports;
    expect(sports).toEqual([{ sport: 'tennis', level: 2.6 }]);
  });
});

describe('toJoinerPage', () => {
  it('reads the page, its cursor and the pill’s sports', () => {
    expect(
      toJoinerPage({ players: [BARTEK], next: 'c-2', sports: ['PADEL', 'BADMINTON'] }),
    ).toEqual({
      joiners: [expect.objectContaining({ playerId: 'p-bartek' })],
      next: 'c-2',
      sports: ['padel', 'badminton'],
    });
  });

  it('has no cursor on the last page', () => {
    expect(toJoinerPage({ players: [], next: null, sports: [] })).not.toHaveProperty('next');
  });
});
