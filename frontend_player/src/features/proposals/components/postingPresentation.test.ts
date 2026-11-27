/**
 * *Post a game*'s sentences — the grid's heads and cells, a cell's sheet, the pick and the guards
 * (#558). Read at Wednesday 30 September 2026, 10:00 in Warsaw.
 */

import { AppError } from '@/shared/errors';

import type { SeatToFill } from '../domain/fillIn';
import type { FreeCourt, PostingCell, PostStillFilling } from '../domain/posting';

import {
  cellCount,
  cellSpoken,
  courtHour,
  courtRowLine,
  courtRowSpoken,
  dayHead,
  dayHeadSpoken,
  eachWords,
  fitLine,
  fitSpoken,
  fitsFreeTag,
  happeningTitle,
  pickLine,
  postLine,
  postRefusal,
  postedToast,
  rangeHoursLines,
  rangeLabelSpoken,
  rangeOfDay,
  rescueLine,
  seatsTag,
  slotHeadline,
  sportChipSpoken,
  weekTitle,
} from './postingPresentation';

const READ_AT = Date.parse('2026-09-30T08:00:00Z');

function cell(extra: Partial<PostingCell> = {}): PostingCell {
  return {
    day: '2026-10-03',
    range: 'EVENING',
    fitsFree: 5,
    courtFree: true,
    fullGame: true,
    outsideYourHours: false,
    past: false,
    happening: false,
    ...extra,
  };
}

const COURT: FreeCourt = {
  club: { id: 'c-1', name: 'Ogrody 33' },
  homeClub: true,
  distanceKm: 2.4,
  startsAt: '2026-10-03T15:00:00Z',
  shareGrosze: 2700,
  bookBy: '2026-10-03T13:00:00Z',
  courts: 2,
  fitsFree: 4,
};

function refused(code: string, details?: Record<string, unknown>): AppError {
  return new AppError('conflict', 'business-conflict', 'refused', {
    code,
    status: 409,
    ...(details === undefined ? {} : { details }),
  });
}

describe('the controls', () => {
  it('says how many members are rated in a sport', () => {
    expect(sportChipSpoken('padel', 10)).toBe('Padel, 10 members rated');
    expect(sportChipSpoken('tennis', 1)).toBe('Tennis, 1 member rated');
  });

  it('names the two weeks', () => {
    expect(weekTitle(1)).toBe('This week');
    expect(weekTitle(2)).toBe('Next week');
  });
});

describe('the grid', () => {
  it('heads today’s column Today and the rest with the short weekday, each over its date', () => {
    expect(dayHead({ day: '2026-09-30', isToday: true })).toEqual({
      name: 'Today',
      date: '30 Sep',
    });
    expect(dayHead({ day: '2026-10-02', isToday: false })).toEqual({ name: 'Fri', date: '2 Oct' });
  });

  it('speaks a column’s head and a row’s label, and draws a row’s hours in two lines', () => {
    expect(dayHeadSpoken({ name: 'Sat', date: '3 Oct' })).toBe('Sat 3 Oct');
    expect(rangeLabelSpoken('MORNING')).toBe('Morning, 07:00 to 12:00');
    expect(rangeHoursLines('EVENING')).toEqual(['17:00–', '23:00']);
  });

  it('counts a cell up to five, then five-plus, and nothing when dead', () => {
    expect(cellCount(cell({ fitsFree: 3 }))).toBe('3');
    expect(cellCount(cell({ fitsFree: 5 }))).toBe('5');
    expect(cellCount(cell({ fitsFree: 8 }))).toBe('5+');
    expect(cellCount(cell({ fitsFree: 0 }))).toBeUndefined();
  });

  it('names a day’s range — this, tomorrow, the weekday, and the date a week out', () => {
    expect(rangeOfDay('2026-09-30', 'EVENING', READ_AT)).toBe('This evening');
    expect(rangeOfDay('2026-10-01', 'MORNING', READ_AT)).toBe('Tomorrow morning');
    expect(rangeOfDay('2026-10-03', 'EVENING', READ_AT)).toBe('Saturday evening');
    expect(rangeOfDay('2026-10-10', 'AFTERNOON', READ_AT)).toBe('Saturday 10 Oct · afternoon');
  });

  it('speaks a cell — its count, its look and every flag over it', () => {
    expect(cellSpoken(cell({ happening: true }), true, READ_AT)).toBe(
      'Saturday evening, 5 of your best fits free, a court free and a full game, a game already happening here, your pick',
    );
    expect(cellSpoken(cell({ fitsFree: 0, courtFree: false }), false, READ_AT)).toBe(
      'Saturday evening, nobody who fits is free',
    );
    expect(
      cellSpoken(cell({ fitsFree: 2, fullGame: false, outsideYourHours: true }), false, READ_AT),
    ).toBe(
      'Saturday evening, 2 of your best fits free, a court free, may not fill, outside your hours',
    );
    expect(
      cellSpoken(cell({ day: '2026-09-30', range: 'MORNING', past: true }), false, READ_AT),
    ).toContain('earlier today');
  });
});

describe('a cell’s sheet', () => {
  it('heads a full game with its count, a thin one with its warning, a dead one with nobody', () => {
    expect(slotHeadline(cell())).toEqual({ count: 5, words: '5 of your best fits free then' });
    expect(slotHeadline(cell({ fitsFree: 2, fullGame: false }))).toEqual({
      count: 2,
      words: 'only 2 fit · may not fill',
    });
    expect(slotHeadline(cell({ fitsFree: 0 }))).toEqual({
      words: 'Nobody who fits is free then',
    });
  });

  it('adds outside your hours to whichever headline it is', () => {
    expect(slotHeadline(cell({ outsideYourHours: true })).words).toBe(
      '5 of your best fits free then · outside your hours',
    );
    expect(slotHeadline(cell({ fitsFree: 0, outsideYourHours: true })).words).toBe(
      'Nobody who fits is free then · outside your hours',
    );
  });

  it('gives a courtless few the count, not the warning — it cannot be picked', () => {
    expect(slotHeadline(cell({ fitsFree: 2, fullGame: false, courtFree: false })).words).toBe(
      '2 of your best fits free then',
    );
  });

  it('lines a fit with their Level and forecast, and says them whole', () => {
    const fit = { playerId: 'p', name: 'karol.t', level: 2.75, forecast: { pct: 93 } };
    expect(fitLine(fit, 'competitive')).toEqual([{ text: '2,75' }, { text: '93' }]);
    expect(fitLine({ playerId: 'p', level: 2.75 }, 'competitive')).toEqual([{ text: '2,75' }]);
    expect(fitLine({ playerId: 'p' }, 'competitive')).toEqual([]);
    expect(fitSpoken(fit, 'competitive')).toBe('karol.t, level 2,75, a 93 % even game');
  });

  // #753 (Q68, applying since Q128): a fit who is the reader's own friend says so.
  it('says friend after the name of the reader’s own friend', () => {
    expect(
      fitSpoken({ playerId: 'p', name: 'karol.t', level: 2.75, friend: true }, 'competitive'),
    ).toBe('karol.t, friend, level 2,75');
  });

  // #842 (ADR-0207 §5): on a For-fun post the fit's number is the Social vibe of the two of you.
  describe('on a For-fun post', () => {
    const fit = (pct: number) => ({ playerId: 'p', name: 'zofia.b', level: 2.69, vibe: { pct } });

    it('lines a fit with their Level and the Social vibe as a %, in its band', () => {
      expect(fitLine(fit(83), 'forFun')).toEqual([{ text: '2,69' }, { text: '83%', vibe: 'volt' }]);
      expect(fitLine(fit(60), 'forFun')[1]).toEqual({ text: '60%', vibe: 'volt' });
      expect(fitLine(fit(36), 'forFun')[1]).toEqual({ text: '36%', vibe: 'dimVolt' });
      expect(fitLine(fit(14), 'forFun')[1]).toEqual({ text: '14%', vibe: 'grey' });
    });

    it('says the Social vibe and its word after the Level', () => {
      expect(fitSpoken(fit(83), 'forFun')).toBe(
        'zofia.b, level 2,69, Social vibe, 83 percent, Great vibe',
      );
      expect(fitSpoken({ ...fit(36), friend: true }, 'forFun')).toBe(
        'zofia.b, friend, level 2,69, Social vibe, 36 percent, Some common ground',
      );
    });

    it('draws and says no forecast, even one a read sent — and no vibe on a competitive post', () => {
      const both = { ...fit(83), forecast: { pct: 93 } };
      expect(fitLine(both, 'forFun')).toEqual([{ text: '2,69' }, { text: '83%', vibe: 'volt' }]);
      expect(fitSpoken(both, 'forFun')).not.toContain('even game');
      expect(fitLine(both, 'competitive')).toEqual([{ text: '2,69' }, { text: '93' }]);
      expect(fitSpoken(both, 'competitive')).not.toContain('Social vibe');
    });

    it('lines and says the figure the row would draw — whole, held to 0–100, banded as drawn', () => {
      expect(fitLine(fit(69.6), 'forFun')[1]).toEqual({ text: '70%', vibe: 'volt' });
      expect(fitSpoken(fit(69.6), 'forFun')).toContain('70 percent, Great vibe');
      expect(fitLine(fit(130), 'forFun')[1]).toEqual({ text: '100%', vibe: 'volt' });
    });

    it('lines the Level alone where neither of you holds a tag', () => {
      expect(fitLine({ playerId: 'p', level: 2.69 }, 'forFun')).toEqual([{ text: '2,69' }]);
      expect(fitSpoken({ playerId: 'p', name: 'zofia.b', level: 2.69 }, 'forFun')).toBe(
        'zofia.b, level 2,69',
      );
    });
  });

  it('lines a free court with its distance, share and book-by — its hour and count apart', () => {
    expect(courtHour(COURT)).toBe('17:00');
    expect(courtRowLine(COURT)).toBe('2,4 km · 27 zł if it fills · book by Sat 15:00');
    expect(courtRowLine({ ...COURT, distanceKm: undefined } as unknown as FreeCourt)).toBe(
      '27 zł if it fills · book by Sat 15:00',
    );
    expect(fitsFreeTag(COURT)).toBe('4 free');
    expect(eachWords(2700)).toBe('27 zł each');
    expect(courtRowSpoken(COURT, true)).toBe(
      '17:00, Ogrody 33, 2,4 km · 27 zł if it fills · book by Sat 15:00, 4 of your best fits free, 27 zł each, your pick',
    );
  });

  it('titles a game already happening as a Fill in row, and lines a rescue with its court', () => {
    const rescue = {
      sport: 'padel',
      kind: 'competitive',
      startsAt: '2026-10-04T18:00:00Z',
      club: { id: 'c', name: 'Centrum Ruchu' },
      courtName: 'Court 2',
      shareGrosze: 3000,
    } as SeatToFill;
    expect(happeningTitle(rescue, READ_AT)).toBe('Padel · Sunday 20:00');
    expect(rescueLine(rescue)).toBe('Centrum Ruchu · Court 2 · 30 zł each');
  });

  it('lines a post with its poster and no court — the group’s once they withdrew', () => {
    const post = {
      club: { id: 'c', name: 'Bonarka Arena' },
      shareGrosze: 3200,
      challenger: { playerId: 'k', name: 'kuba.w' },
    } as PostStillFilling;
    expect(postLine(post)).toBe('kuba.w · Bonarka Arena · 32 zł if it fills');
    expect(postLine({ ...post, challenger: undefined })).toBe(
      'The group · Bonarka Arena · 32 zł if it fills',
    );
    expect(seatsTag(2)).toBe('2 seats');
    expect(seatsTag(1)).toBe('1 seat');
  });
});

describe('the pick and the button', () => {
  it('says what the post will be — the hour alone until the slot’s read names the club and share', () => {
    const pick = { startsAt: '2026-10-03T15:00:00Z' };
    expect(pickLine(pick, COURT, READ_AT)).toBe(
      'Saturday 17:00 · Ogrody 33 · 27 zł each if it fills',
    );
    expect(pickLine(pick, undefined, READ_AT)).toBe('Saturday 17:00');
  });

  it('says each guard in the button’s order, with the cap and the week where the server names them', () => {
    expect(postRefusal(refused('payment_method_required'))).toMatch(/saved way to pay/);
    expect(postRefusal(refused('live_posts_exhausted', { cap: 2 }))).toMatch(/2 posts live/);
    expect(postRefusal(refused('games_per_week_booked', { week: '2026-10-05' }))).toBe(
      'Your games for the week from 5 Oct are already booked.',
    );
    expect(postRefusal(refused('you_play_then'))).toBe('You already have a game at that hour.');
    expect(postRefusal(refused('nobody_fits_then'))).toMatch(/None of your best fits/);
  });

  it('tells the poster how many best fits have it', () => {
    expect(postedToast({ proposalId: 'p', versions: 1, dealtTo: 5, openSeats: 3 })).toBe(
      'Posted — 5 of your best fits have it.',
    );
    expect(postedToast({ proposalId: 'p', versions: 1, dealtTo: 1, openSeats: 3 })).toBe(
      'Posted — 1 of your best fits has it.',
    );
  });
});
