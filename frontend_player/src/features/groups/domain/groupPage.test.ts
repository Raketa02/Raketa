import type { GroupPerson, SportRoster } from './group';
import { faceIn, filterSports, gamesCard, openingSport, rosterFor } from './groupPage';

describe('the sports a group page filters by', () => {
  it('lists the sports the reader is rated in, in the order padel › tennis › squash › badminton', () => {
    expect(filterSports(['badminton', 'tennis', 'padel'])).toEqual([
      'padel',
      'tennis',
      'badminton',
    ]);
  });

  it('lists a sport once, however it came', () => {
    expect(filterSports(['squash', 'squash'])).toEqual(['squash']);
  });

  it('lists nothing for a reader rated in nothing', () => {
    expect(filterSports([])).toEqual([]);
  });
});

describe('the sport a group page opens on', () => {
  it('is the sport last picked, while the reader is still rated in it', () => {
    expect(openingSport(['padel', 'tennis'], 'tennis')).toBe('tennis');
  });

  it('is the first rated sport when nothing was picked', () => {
    expect(openingSport(['tennis', 'badminton'], undefined)).toBe('tennis');
    expect(openingSport(['badminton', 'squash'], undefined)).toBe('squash');
  });

  // ADR-0188 §4: a sport the player is no longer rated in falls back to the default.
  it('is the first rated sport when the one picked is no longer rated', () => {
    expect(openingSport(['tennis', 'badminton'], 'padel')).toBe('tennis');
  });

  it('is the first rated sport when what was saved is not a sport', () => {
    expect(openingSport(['padel'], 'pickleball')).toBe('padel');
  });

  it('is none for a reader rated in nothing', () => {
    expect(openingSport([], 'padel')).toBeUndefined();
  });
});

function person(n: number): GroupPerson {
  return { playerId: `p${n}`, name: `Player ${n}` };
}

function roster(ratedCount: number, faces = ratedCount): SportRoster {
  return {
    sport: 'padel',
    ratedCount,
    firstRated: Array.from({ length: faces }, (_, n) => person(n + 1)),
  };
}

describe('the Games card', () => {
  it('is just you while you are the only one rated in the sport', () => {
    expect(gamesCard(roster(1), 4)).toEqual({
      kind: 'just-you',
      rated: 1,
      seats: 4,
      faces: [person(1)],
    });
  });

  it('counts the ones rated in the sport against the seats once others are in', () => {
    expect(gamesCard(roster(3), 4)).toEqual({
      kind: 'filling',
      rated: 3,
      seats: 4,
      faces: [person(1), person(2), person(3)],
    });
  });

  it('picks nothing once the seats could be filled', () => {
    expect(gamesCard(roster(2), 2).kind).toBe('nothing-picked');
    expect(gamesCard(roster(7, 4), 4)).toEqual({
      kind: 'nothing-picked',
      rated: 7,
      seats: 4,
      faces: [person(1), person(2), person(3), person(4)],
    });
  });

  // The backend serves at most as many faces as the sport seats; a court never draws more.
  it('never draws more faces than the court has seats', () => {
    expect(gamesCard(roster(9, 6), 4).faces).toHaveLength(4);
  });

  it('is just you, with nobody drawn, for a sport the group has no count for', () => {
    expect(gamesCard(undefined, 2)).toEqual({ kind: 'just-you', rated: 0, seats: 2, faces: [] });
  });
});

describe('a sport’s roster, and a face in it', () => {
  const padel = roster(2);
  const group = { ratedBySport: [padel, { ...roster(0), sport: 'tennis' as const }] };

  it('finds the sport’s roster, and none for a sport the group was not served', () => {
    expect(rosterFor(group, 'padel')).toBe(padel);
    expect(rosterFor(group, 'squash')).toBeUndefined();
  });

  it('finds somebody among the first rated, and nobody who joined after a court’s worth', () => {
    expect(faceIn(padel, 'p2')).toEqual(person(2));
    expect(faceIn(padel, 'p9')).toBeUndefined();
    expect(faceIn(undefined, 'p1')).toBeUndefined();
  });
});
