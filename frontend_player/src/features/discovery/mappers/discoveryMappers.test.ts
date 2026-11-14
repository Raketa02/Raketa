import type { components } from '@/generated/schema';

import { toJoiner, toJoinerPage, toSameLevelPage, toSameLevelPlayer } from './discoveryMappers';

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
      people: [expect.objectContaining({ playerId: 'p-bartek' })],
      next: 'c-2',
      sports: ['padel', 'badminton'],
    });
  });

  it('has no cursor on the last page', () => {
    expect(toJoinerPage({ players: [], next: null, sports: [] })).not.toHaveProperty('next');
  });
});

const comparison = (
  sport: Wire['Sport'],
  over: Partial<Wire['SameLevelSportSchema']> = {},
): Wire['SameLevelSportSchema'] => ({
  sport,
  your_level: 2.71,
  their_level: 2.69,
  percent_even: 91,
  level_gap: -0.02,
  your_band: { name: 'Established', lower: 2.65, upper: 3.85 },
  ...over,
});

const ZOFIA: Wire['SameLevelPlayerSchema'] = {
  player_id: 'p-zofia',
  nickname: 'zofia.b',
  photo_id: 'f-2',
  photo_url: 'https://photos.example/zofia.jpg',
  shown: comparison('PADEL'),
  sports: [
    comparison('PADEL'),
    comparison('SQUASH', { your_level: 2.3, their_level: 2.55, percent_even: 51, level_gap: 0.25 }),
  ],
  relation: 'FRIEND',
};

describe('toSameLevelPlayer (#802)', () => {
  it('reads the face, the nickname, the card’s sport, every shared sport in order, and the relation', () => {
    expect(toSameLevelPlayer(ZOFIA)).toEqual({
      playerId: 'p-zofia',
      nickname: 'zofia.b',
      photoUrl: 'https://photos.example/zofia.jpg',
      shown: {
        sport: 'padel',
        yourLevel: 2.71,
        theirLevel: 2.69,
        percentEven: 91,
        levelGap: -0.02,
        yourBand: 'Established',
      },
      sports: [
        expect.objectContaining({ sport: 'padel', percentEven: 91 }),
        expect.objectContaining({ sport: 'squash', percentEven: 51, levelGap: 0.25 }),
      ],
      relation: 'FRIEND',
    });
  });

  it('draws the poster with no photo', () => {
    expect(toSameLevelPlayer({ ...ZOFIA, photo_id: null, photo_url: null })).not.toHaveProperty(
      'photoUrl',
    );
  });

  it('leaves out a shared sport this build cannot name, and the card when it is the card’s own', () => {
    const unknown = 'PICKLEBALL' as Wire['Sport'];
    expect(
      toSameLevelPlayer({ ...ZOFIA, sports: [comparison('PADEL'), comparison(unknown)] })?.sports,
    ).toEqual([expect.objectContaining({ sport: 'padel' })]);
    expect(toSameLevelPlayer({ ...ZOFIA, shown: comparison(unknown) })).toBeUndefined();
  });
});

describe('toSameLevelPage (#802)', () => {
  it('reads the page, its cursor and the pill’s sports', () => {
    expect(toSameLevelPage({ players: [ZOFIA], next: 'c-2', sports: ['PADEL', 'SQUASH'] })).toEqual(
      {
        people: [expect.objectContaining({ playerId: 'p-zofia' })],
        next: 'c-2',
        sports: ['padel', 'squash'],
      },
    );
  });

  it('has no cursor on the last page', () => {
    expect(toSameLevelPage({ players: [], next: null, sports: [] })).not.toHaveProperty('next');
  });
});
