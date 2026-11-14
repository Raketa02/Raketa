import { joinedAgo } from '../domain/joiner';

import {
  comparisonTitle,
  evenTag,
  gapLine,
  joinedLine,
  levelsLine,
  nobodyNewPlays,
  pairingLabel,
  sportLevelLine,
  sportsCount,
  tileLabel,
} from './discoveryCopy';

describe('the Joined ladder’s words (§31.7)', () => {
  it.each<[number, string]>([
    [0, 'Joined today'],
    [1, 'Joined yesterday'],
    [2, 'Joined 2 days ago'],
    [6, 'Joined 6 days ago'],
    [7, 'Joined last week'],
    [13, 'Joined last week'],
    [14, 'Joined 2 weeks ago'],
    [21, 'Joined 3 weeks ago'],
    [29, 'Joined 4 weeks ago'],
  ])('%i days: %s', (days, line) => {
    expect(joinedLine(joinedAgo(days))).toBe(line);
  });
});

describe('a tile’s words', () => {
  it('writes a sport with its level, the decimal comma', () => {
    expect(sportLevelLine('padel', 2.35)).toBe('Padel 2,35');
  });

  it('speaks the tile in the order drawn', () => {
    expect(
      tileLabel(
        {
          playerId: 'p-1',
          nickname: 'bartek.l',
          daysSinceJoined: 2,
          sports: [
            { sport: 'padel', level: 2.35 },
            { sport: 'badminton', level: 2.1 },
          ],
          relation: 'NONE',
        },
        'Joined 2 days ago',
      ),
    ).toBe('bartek.l, Padel 2,35, Badminton 2,10, Joined 2 days ago');
  });
});

it('says a sport that leaves nobody inside the sentence', () => {
  expect(nobodyNewPlays('squash')).toBe('Nobody new plays squash yet');
});

describe('Same competitive level’s words (§31.5, §31.6)', () => {
  const PADEL = {
    sport: 'padel',
    yourLevel: 2.71,
    theirLevel: 2.69,
    percentEven: 91,
    levelGap: -0.02,
    yourBand: 'Established',
  } as const;

  it('says the gap below, above, or the same level', () => {
    expect(gapLine({ kind: 'below', gap: 0.02 })).toBe('0,02 below you');
    expect(gapLine({ kind: 'above', gap: 0.09 })).toBe('0,09 above you');
    expect(gapLine({ kind: 'same' })).toBe('Same level');
  });

  it('counts the sports, titles the sheet and words a block', () => {
    expect(sportsCount(2)).toBe('2 sports');
    expect(comparisonTitle('zofia.b')).toBe('You vs zofia.b');
    expect(levelsLine(PADEL, 'zofia.b')).toBe('You 2,71 · zofia.b 2,69');
    expect(evenTag(91)).toBe('91% even');
  });

  it('speaks the pairing in the order drawn', () => {
    expect(pairingLabel(PADEL, 'zofia.b')).toBe(
      '91% even in padel, You 2,71, zofia.b 2,69, 0,02 below you',
    );
  });
});
