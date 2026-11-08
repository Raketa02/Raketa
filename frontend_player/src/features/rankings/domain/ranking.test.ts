/**
 * **The Rankings page's own rules**, with no renderer — which sports the pill offers and in what
 * order, which sport the page opens on, and when there is a podium
 * ([#775](https://github.com/Raketa02/Raketa/issues/775); the rankings mechanics §9, the screens
 * §2, §5.1).
 */

import { openingSport, pillSports, podiumOf, type RankedRow } from './ranking';

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
