import type { ReadStage } from '@/shared/lib/query-client';

import type { GroupPerson, SportRoster } from './group';
import {
  bodyRead,
  deckSport,
  faceIn,
  filterSports,
  gamesCard,
  gamesRead,
  groupPageParts,
  groupReadStage,
  homeAsksForALevel,
  levelCardReadsFinished,
  needsALevel,
  openingSport,
  rosterFor,
  sportsToAdd,
  sportsToOffer,
  type GroupPageParts,
  type GroupPageReads,
  type GroupTab,
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

/** **The sport the deck last showed** — what Rankings and Top 10 open on past the trophy (#775, #874). */
describe('the sport the deck last showed', () => {
  it('is not known while the ratings or the phone are still being read', () => {
    expect(deckSport(undefined, 'tennis')).toBeUndefined();
    expect(deckSport(['tennis'], undefined)).toBeUndefined();
  });

  it('is the sport last picked while the reader is still rated in it', () => {
    expect(deckSport(['padel', 'tennis'], 'tennis')).toBe('tennis');
  });

  it('is the first rated sport when nothing was saved, or the saved one is no longer rated', () => {
    expect(deckSport(['tennis', 'padel'], null)).toBe('padel');
    expect(deckSport(['tennis'], 'squash')).toBe('tennis');
  });

  it('is none for a reader rated in nothing', () => {
    expect(deckSport([], 'padel')).toBeNull();
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

// #875: what the group page's reveal waits on — the header and the tab bar, then the tab's body.
describe('the group page’s two parts', () => {
  it.each<[string, GroupPageReads, GroupPageParts]>([
    [
      'the group on its way: nothing finished',
      { group: 'reading', sportAnswered: true, body: 'landed' },
      { finished: [false, false], landed: [false, false] },
    ],
    [
      'the group read, the sport still to be read off the phone: the body waits with the header',
      { group: 'landed', sportAnswered: false, body: 'landed' },
      { finished: [false, false], landed: [false, false] },
    ],
    [
      'the group and the sport in, the tab’s read on its way',
      { group: 'landed', sportAnswered: true, body: 'reading' },
      { finished: [true, false], landed: [true, false] },
    ],
    [
      'everything in',
      { group: 'landed', sportAnswered: true, body: 'landed' },
      { finished: [true, true], landed: [true, true] },
    ],
    [
      'the tab’s read refused, held for a connection or retrying: what it draws then is its own',
      { group: 'landed', sportAnswered: true, body: 'ended' },
      { finished: [true, true], landed: [true, false] },
    ],
    [
      'the group refused or held: the header’s way back, and the failure or the note for the body',
      { group: 'ended', sportAnswered: true, body: 'reading' },
      { finished: [true, true], landed: [false, false] },
    ],
    [
      'the group held, the sport still out: the body is the note, the header still waits',
      { group: 'ended', sportAnswered: false, body: 'reading' },
      { finished: [false, true], landed: [false, false] },
    ],
  ])('%s', (_case, reads, parts) => {
    expect(groupPageParts(reads)).toEqual(parts);
  });
});

describe('the group’s own read, as the page’s reveal reads it', () => {
  it.each<[string, { landed: boolean; refused: boolean; held: boolean }, ReadStage]>([
    [
      'on its way — or retrying after a failure: every part draws from it',
      { landed: false, refused: false, held: false },
      'reading',
    ],
    ['refused: the failure and its retry', { landed: false, refused: true, held: false }, 'ended'],
    [
      'held for a connection: the offline note',
      { landed: false, refused: false, held: true },
      'ended',
    ],
    ['landed, whatever a re-read does', { landed: true, refused: true, held: false }, 'landed'],
  ])('%s', (_case, read, stage) => {
    expect(groupReadStage(read)).toBe(stage);
  });
});

describe('what the body on screen waits on', () => {
  it.each<[string, GroupTab, boolean, ReadStage]>([
    ['Games, for its first deck read', 'games', true, 'reading'],
    ['Fill in, for its rescues', 'fillIn', true, 'ended'],
    ['You’re in, for its yeses', 'youreIn', true, 'landed'],
  ])('%s', (_case, tab, drawsTheTab, stage) => {
    expect(bodyRead(tab, drawsTheTab, stage)).toBe(stage);
  });

  it('waits on nothing for Friends, whose court reads its own', () => {
    expect(bodyRead('friends', true, 'reading')).toBe('landed');
  });

  it('waits on nothing in place of a tab — the add-a-sport card, the level door', () => {
    expect(bodyRead('games', false, 'reading')).toBe('landed');
  });
});

describe('Games’ first read, with something over the deck', () => {
  it.each<[string, ReadStage, boolean, ReadStage]>([
    ['the deck on its way, nothing over it', 'reading', false, 'reading'],
    [
      'the deck on its way, the door’s panel or finding over it: that is drawn',
      'reading',
      true,
      'ended',
    ],
    ['the deck read, whatever lies over it', 'landed', true, 'landed'],
    ['the deck refused, whatever lies over it', 'ended', true, 'ended'],
  ])('%s', (_case, deck, covered, stage) => {
    expect(gamesRead(deck, covered)).toBe(stage);
  });
});
