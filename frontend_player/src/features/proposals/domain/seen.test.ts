import {
  GAMES_SEEN,
  afterALook,
  gamesSeen,
  sameSeen,
  seenEntry,
  seenFrom,
  unseenCount,
} from './seen';

const GROUP = 'a0000000-0000-4000-8000-000000000005';
const OTHER_GROUP = 'a0000000-0000-4000-8000-000000000099';

describe('a tab’s badge (ADR-0208 §1)', () => {
  it('is the ids the tab counts now, minus the ids seen', () => {
    expect(unseenCount(['a', 'b', 'c'], ['b'])).toBe(2);
  });

  it('is every id the tab counts while nothing has been seen — the first run', () => {
    expect(unseenCount(['a', 'b'], [])).toBe(2);
  });

  it('is 0 once everything it counts has been seen, and with nothing to count', () => {
    expect(unseenCount(['a', 'b'], ['b', 'a'])).toBe(0);
    expect(unseenCount([], ['a'])).toBe(0);
  });

  it('never counts a seen id that has stopped being counted', () => {
    expect(unseenCount(['c'], ['a', 'b'])).toBe(1);
  });

  it('counts an id once, however often it is listed', () => {
    expect(unseenCount(['a', 'a'], [])).toBe(1);
  });
});

describe('what a look leaves seen (ADR-0208 §2)', () => {
  it('is what was seen and what is on screen, among the ids still counted', () => {
    expect(afterALook(['a'], ['b'], ['a', 'b', 'c'])).toEqual(['a', 'b']);
  });

  it('drops an id the tab no longer counts — a game gone takes its id with it', () => {
    expect(afterALook(['gone', 'a'], ['a'], ['a'])).toEqual(['a']);
  });

  it('keeps nothing on screen that the tab does not count', () => {
    expect(afterALook([], ['a', 'elsewhere'], ['a'])).toEqual(['a']);
  });

  it('is never bigger than what the tab counts', () => {
    const seen = afterALook(['x', 'y', 'z'], ['a', 'b'], ['a']);

    expect(seen).toEqual(['a']);
  });

  it('is in the tab’s own order, each id once', () => {
    expect(afterALook(['c', 'a'], ['a', 'b'], ['a', 'b', 'c'])).toEqual(['a', 'b', 'c']);
  });

  it('is empty once the tab counts nothing', () => {
    expect(afterALook(['a', 'b'], [], [])).toEqual([]);
  });
});

describe('whether a look changed anything', () => {
  it('is no change for the same ids in any order', () => {
    expect(sameSeen(['a', 'b'], ['b', 'a'])).toBe(true);
    expect(sameSeen([], [])).toBe(true);
  });

  it('is a change for an id more or less', () => {
    expect(sameSeen(['a'], ['a', 'b'])).toBe(false);
    expect(sameSeen(['a', 'b'], ['a'])).toBe(false);
    expect(sameSeen(['a'], ['b'])).toBe(false);
  });
});

describe('where a tab’s seen ids are kept', () => {
  it('is one entry per group, sport and tab', () => {
    const entries = [
      seenEntry(GROUP, 'padel', 'fillIn'),
      seenEntry(GROUP, 'padel', 'youreIn'),
      // Games' is per kind (#850): each kind's list is cut back by its own kind's read alone.
      seenEntry(GROUP, 'padel', gamesSeen('competitive')),
      seenEntry(GROUP, 'padel', gamesSeen('forFun')),
      seenEntry(GROUP, 'tennis', 'fillIn'),
      seenEntry(OTHER_GROUP, 'padel', 'fillIn'),
    ];

    expect(new Set(entries).size).toBe(entries.length);
    expect(seenEntry(GROUP, 'padel', 'fillIn')).toBe(seenEntry(GROUP, 'padel', 'fillIn'));
  });

  it('counts the Games badge against both kinds’ lists', () => {
    expect(GAMES_SEEN).toEqual([gamesSeen('competitive'), gamesSeen('forFun')]);
  });
});

describe('what the phone kept (ADR-0208 §4)', () => {
  it('is the ids it saved', () => {
    expect(seenFrom(JSON.stringify(['a', 'b']))).toEqual(['a', 'b']);
  });

  it('is nothing seen when nothing was saved', () => {
    expect(seenFrom(undefined)).toEqual([]);
  });

  it('is nothing seen when what was saved cannot be read', () => {
    expect(seenFrom('[not json')).toEqual([]);
  });

  it('is nothing seen when what was saved is not a list of ids — a stale value', () => {
    expect(seenFrom(JSON.stringify({ ids: ['a'] }))).toEqual([]);
    expect(seenFrom(JSON.stringify(['a', 7]))).toEqual([]);
    expect(seenFrom(JSON.stringify('a'))).toEqual([]);
    expect(seenFrom('null')).toEqual([]);
  });
});
