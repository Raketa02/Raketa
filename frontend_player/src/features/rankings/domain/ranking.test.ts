/**
 * **The Rankings page's own rules**, with no renderer — which sports the pill offers and in what
 * order, which sport the page opens on, and when there is a podium
 * ([#775](https://github.com/Raketa02/Raketa/issues/775); the rankings mechanics §9, the screens
 * §2, §5.1).
 */

import {
  belowTheCard,
  joinPages,
  jumpPlace,
  openingSport,
  pillSports,
  placeIn,
  podiumOf,
  rankingViewFrom,
  type RankedRow,
} from './ranking';

describe('the sports the pill offers', () => {
  // PRD #766 call 9: all four, the reader's rated ones first, then the rest — each part in the app's
  // sport order.
  it('lists the rated sports first, then the rest, each in the app’s order', () => {
    expect(pillSports(['squash', 'padel'])).toEqual(['padel', 'squash', 'tennis', 'badminton']);
  });

  it('offers all four to a reader rated in nothing', () => {
    expect(pillSports([])).toEqual(['padel', 'tennis', 'squash', 'badminton']);
  });
});

describe('the sport the page opens on', () => {
  it('is the sport it was asked for — the trophy’s, or a pass’s way back — whatever else is known', () => {
    expect(openingSport('tennis', { trophy: 'squash', deck: 'padel' })).toBe('tennis');
    expect(openingSport('tennis', { trophy: undefined, deck: undefined })).toBe('tennis');
  });

  it('is the trophy’s sport when none was asked — a tap made before Home had answered', () => {
    expect(openingSport(undefined, { trophy: 'squash', deck: 'padel' })).toBe('squash');
  });

  it('waits for Home while none was asked, rather than opening on the deck and then moving', () => {
    expect(openingSport(undefined, { trophy: undefined, deck: 'padel' })).toBeUndefined();
  });

  it('is the sport the deck last showed when the trophy names none — no result anywhere', () => {
    expect(openingSport(undefined, { trophy: null, deck: 'squash' })).toBe('squash');
  });

  it('is padel when the deck shows no sport — no level anywhere', () => {
    expect(openingSport(undefined, { trophy: null, deck: null })).toBe('padel');
  });

  it('is not known yet while the deck’s sport is being read', () => {
    expect(openingSport(undefined, { trophy: null, deck: undefined })).toBeUndefined();
  });
});

function row(place: number): RankedRow {
  return {
    place,
    playerId: `p-${place}`,
    nickname: `player.${place}`,
    form: [],
    chip: { kind: 'SAME' },
    level: 3 - place / 10,
    isYou: false,
  };
}

describe('the podium', () => {
  // The screens §5.1: first in the middle, second on the left, third on the right — each step its
  // true place, so a hidden second reads 1, 3 and 4.
  it('stands the first three rows the reader sees on their steps', () => {
    const [first, third, fourth] = [row(1), row(3), row(4)];

    expect(podiumOf([first, third, fourth])).toEqual({
      first,
      second: third,
      third: fourth,
    });
  });

  it('is none with fewer than three rows', () => {
    expect(podiumOf([row(1), row(2)])).toBeUndefined();
    expect(podiumOf([])).toBeUndefined();
  });
});

describe('General’s pages, joined', () => {
  // #776: General loads in pages of 50, each read after (or before) the last row's key as the order
  // stands at that read — so a row that dropped past the cursor between two reads comes back on the
  // next page. The list draws it once, where it already stands.
  it('lays the pages end to end, best first', () => {
    expect(joinPages([{ rows: [row(1), row(2)] }, { rows: [row(3), row(5)] }])).toEqual([
      row(1),
      row(2),
      row(3),
      row(5),
    ]);
  });

  it('draws a row that came back on a later page once, where it already stands', () => {
    const moved = { ...row(2), place: 4 };

    expect(joinPages([{ rows: [row(1), row(2)] }, { rows: [row(3), moved] }])).toEqual([
      row(1),
      row(2),
      row(3),
    ]);
  });

  // Around the reader the window's first page is in the middle: a page read above it later is laid
  // in before it, and a row that climbed past the cursor stays where it already stood.
  it('keeps a row where the window first drew it, however many pages were laid in above', () => {
    const climbed = { ...row(6), place: 3 };
    const above = { rows: [row(2), climbed] };
    const first = { rows: [row(5), row(6), row(7)] };

    expect(joinPages([above, first], 1)).toEqual([row(2), row(5), row(6), row(7)]);
  });

  it('is nothing with no page', () => {
    expect(joinPages([])).toEqual([]);
  });
});

describe('the place the jump button names', () => {
  // The screens §5.3: *You · 212th* — not shown when the reader isn't listed, nor, in General,
  // hidden.
  const placed = { place: 212, of: 480, level: 2.71 } as const;

  it('is the reader’s place when they are listed', () => {
    expect(jumpPlace({ state: 'LISTED', ...placed, gapLine: { kind: 'between' } })).toBe(212);
  });

  it('is none when the reader is hidden from General', () => {
    expect(jumpPlace({ state: 'HIDDEN', ...placed })).toBeUndefined();
  });

  it('is none when the reader is not listed, or no card could be read', () => {
    expect(jumpPlace({ state: 'NEEDS_RESULTS', results: 2, resultsToEnter: 5 })).toBeUndefined();
    expect(jumpPlace({ state: 'NO_LEVEL', resultsToEnter: 5 })).toBeUndefined();
    expect(jumpPlace({ state: 'OFF_THE_LIST' })).toBeUndefined();
    expect(jumpPlace(undefined)).toBeUndefined();
  });
});

describe('the view the phone remembers (#777)', () => {
  // The screens §3: General the first time, and whatever was last looked at after that.
  it('is the view saved', () => {
    expect(rankingViewFrom('GENERAL')).toBe('GENERAL');
    expect(rankingViewFrom('FRIENDS')).toBe('FRIENDS');
  });

  it('is General with nothing saved, or a value this build has never heard of', () => {
    expect(rankingViewFrom(undefined)).toBe('GENERAL');
    expect(rankingViewFrom('CITY')).toBe('GENERAL');
    expect(rankingViewFrom('friends')).toBe('GENERAL');
  });
});

describe('the place Home’s trophy shows (#777)', () => {
  // The mechanics §8: the trophy's sport, in the view the reader last looked at.
  it('is the place in the remembered view', () => {
    expect(placeIn('GENERAL', { generalPlace: 7, friendsPlace: 4 })).toBe(7);
    expect(placeIn('FRIENDS', { generalPlace: 7, friendsPlace: 4 })).toBe(4);
  });

  it('is none where the reader has no place in that view — never the other view’s', () => {
    expect(placeIn('FRIENDS', { generalPlace: 7 })).toBeUndefined();
    expect(placeIn('GENERAL', { friendsPlace: 4 })).toBeUndefined();
  });
});

describe('what stands below the card (#777)', () => {
  const placed = { place: 4, of: 9, level: 2.71 } as const;
  const listed = { state: 'LISTED', ...placed, gapLine: { kind: 'top' } } as const;

  it('is the table while anybody is listed', () => {
    expect(belowTheCard({ card: listed, listed: 9 })).toBe('table');
    // The reader's own not-listed card stands above the friends' table (Q7).
    expect(
      belowTheCard({ card: { state: 'NEEDS_RESULTS', results: 0, resultsToEnter: 1 }, listed: 3 }),
    ).toBe('table');
    expect(belowTheCard({ card: undefined, listed: 9 })).toBe('table');
  });

  it('is Nobody ranked where nobody is listed in the sport', () => {
    expect(belowTheCard({ card: { state: 'NO_LEVEL', resultsToEnter: 5 }, listed: 0 })).toBe(
      'nobodyRanked',
    );
  });

  // The screens §4.6: with no friend listed the card is the page, whatever is counted.
  it('is nothing when the Friends card is the page — just you, or none of your friends', () => {
    expect(belowTheCard({ card: { state: 'JUST_YOU' }, listed: 1 })).toBe('nothing');
    expect(belowTheCard({ card: { state: 'NO_FRIEND_LISTED' }, listed: 0 })).toBe('nothing');
  });
});
