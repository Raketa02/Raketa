import { joinedAgo } from '../domain/joiner';

import { joinedLine, nobodyNewPlays, sportLevelLine, tileLabel } from './discoveryCopy';

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
