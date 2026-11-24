import type { GroupPerson, SportRoster } from './group';
import {
  faceIn,
  filterSports,
  gamesCard,
  homeAsksForALevel,
  levelCardReadsFinished,
  needsALevel,
  openingSport,
  rosterFor,
  sportsToAdd,
  sportsToOffer,
} from './groupPage';

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

  // Story 56: an official group plays what it declares.
  it('lists only the rated sports an official group plays', () => {
    expect(
      filterSports(['badminton', 'tennis', 'padel'], ['squash', 'padel', 'badminton']),
    ).toEqual(['padel', 'badminton']);
  });

  it('lists nothing for a reader rated in none of an official group’s sports', () => {
    expect(filterSports(['tennis'], ['padel'])).toEqual([]);
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

  // #559: a notice about a padel card opens the group on padel, whatever was picked last.
  it('is the sport a notice opened the page in, while the filter lists it', () => {
    expect(openingSport(['padel', 'tennis'], 'tennis', undefined, 'padel')).toBe('padel');
  });

  it('is the one picked as ever when the notice’s sport is not on the filter', () => {
    expect(openingSport(['padel', 'tennis'], 'tennis', undefined, 'squash')).toBe('tennis');
    expect(openingSport(['padel', 'tennis'], 'tennis', ['tennis'], 'padel')).toBe('tennis');
  });

  it('is a sport an official group plays, whatever was picked elsewhere', () => {
    expect(openingSport(['padel', 'tennis'], 'tennis', ['padel'])).toBe('padel');
    expect(openingSport(['padel', 'tennis', 'squash'], 'squash', ['squash', 'padel'])).toBe(
      'squash',
    );
  });

  it('is none for a reader rated in none of an official group’s sports', () => {
    expect(openingSport(['tennis'], 'tennis', ['padel'])).toBeUndefined();
  });
});

describe('the sports a reader must add to see an official group', () => {
  // Story 57.
  it('are every sport it plays, for a reader rated in none of them', () => {
    expect(sportsToAdd(['tennis'], ['squash', 'padel'])).toEqual(['padel', 'squash']);
  });

  it('are none once the reader is rated in one of them', () => {
    expect(sportsToAdd(['tennis', 'squash'], ['squash', 'padel'])).toEqual([]);
  });

  it('are none for a player group, which plays whatever its members are rated in', () => {
    expect(sportsToAdd([], undefined)).toEqual([]);
    expect(sportsToAdd(['tennis'], undefined)).toEqual([]);
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

/**
 * **The door where play begins** (ADR-0200 §2, #730): a player group plays whatever its members are
 * rated in, so a reader rated in nothing has no sport for any tab — and meets the door instead. An
 * official group keeps its own card (`sportsToAdd`), so its reader never does.
 */
describe('who meets the door instead of a player group’s tabs', () => {
  it('is a reader rated in nothing, in a player group', () => {
    expect(needsALevel([], undefined)).toBe(true);
  });

  it('is nobody rated in any sport, whatever the group plays', () => {
    expect(needsALevel(['tennis'], undefined)).toBe(false);
  });

  it('is never an official group’s reader, who has its own card', () => {
    expect(needsALevel([], ['padel'])).toBe(false);
    expect(needsALevel(['tennis'], ['padel'])).toBe(false);
  });
});

// #731, ADR-0200 §4: *+ Another sport* at the end of the chip.
describe('the sports *+ Another sport* offers', () => {
  it('is every sport a player group’s reader is unrated in, in the registry’s order', () => {
    expect(sportsToOffer(['tennis'], undefined)).toEqual(['padel', 'squash', 'badminton']);
  });

  it('is only an official group’s own sports the reader is unrated in', () => {
    expect(sportsToOffer(['padel'], ['tennis', 'padel', 'badminton'])).toEqual([
      'tennis',
      'badminton',
    ]);
  });

  it('is nothing once the reader is rated in everything there is to offer', () => {
    expect(sportsToOffer(['padel', 'tennis', 'squash', 'badminton'], undefined)).toEqual([]);
    expect(sportsToOffer(['padel', 'tennis'], ['padel', 'tennis'])).toEqual([]);
  });

  // The chip is drawn only once there is a rating to list; before it, the door or the card asks.
  it('is nothing while there is no chip to end — the door or the group’s card asks instead', () => {
    expect(sportsToOffer([], undefined)).toEqual([]);
    expect(sportsToOffer(['squash'], ['padel', 'tennis'])).toEqual([]);
  });
});

// #731, ADR-0200 §7: *Get your level — your groups can't deal you games until you have one.*
describe('who Home asks for a level', () => {
  // Whether a friend asked is no part of it (#816, ADR-0205 §4, Q13): the ask waits in Needs your
  // answer, and is never drawn in the card's place.
  it('is a member of a group who holds no rating', () => {
    expect(homeAsksForALevel(1, [])).toBe(true);
    expect(homeAsksForALevel(3, [])).toBe(true);
  });

  it('is nobody in no group — there is nothing a level would unlock yet', () => {
    expect(homeAsksForALevel(0, [])).toBe(false);
  });

  it('is nobody holding any rating, whatever the groups play', () => {
    expect(homeAsksForALevel(2, ['squash'])).toBe(false);
  });
});

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

// #871: what Home's reveal waits on for the card.
describe('whether the level card’s reads have finished', () => {
  const T = true;
  const F = false;

  it.each<[string, boolean, boolean | undefined, boolean, boolean]>([
    ['the ratings still out', F, undefined, T, F],
    ['a rated reader, whatever the groups do', T, F, F, T],
    [
      'the ratings holding nothing — refused, held or retrying: no card, nothing more',
      T,
      undefined,
      F,
      T,
    ],
    ['a reader rated in nothing, the groups still out', T, T, F, F],
    ['a reader rated in nothing, the groups in', T, T, T, T],
  ])('%s', (_case, ratingsFinished, ratedInNothing, groupsFinished, finished) => {
    expect(levelCardReadsFinished({ ratingsFinished, ratedInNothing, groupsFinished })).toBe(
      finished,
    );
  });
});
