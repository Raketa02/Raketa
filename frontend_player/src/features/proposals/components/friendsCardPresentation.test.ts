import type { FriendsCourt } from '../domain/friendsCard';

import {
  busyLine,
  courtDayHeading,
  courtRowSpoken,
  fullAtLine,
  refusalLine,
} from './friendsCardPresentation';

const PEOPLE = [
  { playerId: 'ewa', name: 'ewa.m' },
  { playerId: 'magda', name: 'magda.p' },
  { playerId: 'ania', name: 'ania.k' },
];
const ME = 'me';

describe('who is busy, on a row', () => {
  it('is everybody free when nobody is busy', () => {
    expect(busyLine([], ME, PEOPLE)).toBe('Everybody free');
  });

  it('names the friends busy, joined as a sentence joins them', () => {
    expect(busyLine(['ania'], ME, PEOPLE)).toBe('ania.k busy');
    expect(busyLine(['magda', 'ania'], ME, PEOPLE)).toBe('magda.p and ania.k busy');
    expect(busyLine(['ewa', 'magda', 'ania'], ME, PEOPLE)).toBe('ewa.m, magda.p and ania.k busy');
  });

  it('says you first, as you', () => {
    expect(busyLine([ME], ME, PEOPLE)).toBe('You’re busy');
    expect(busyLine([ME, 'ania'], ME, PEOPLE)).toBe('You and ania.k busy');
  });

  it('says somebody for a friend it cannot name', () => {
    expect(busyLine(['zofia'], ME, PEOPLE)).toBe('Somebody busy');
  });
});

describe('a day’s heading', () => {
  it('is today, tomorrow, the weekday, then the short weekday and its date', () => {
    expect(courtDayHeading({ kind: 'today' })).toBe('Today');
    expect(courtDayHeading({ kind: 'tomorrow' })).toBe('Tomorrow');
    expect(courtDayHeading({ kind: 'weekday', weekday: 6 })).toBe('Saturday');
    expect(courtDayHeading({ kind: 'dated', weekday: 6, day: '2026-09-26' })).toBe('Sat 26 Sep');
  });
});

describe('another club at the home club’s full hour', () => {
  const row: Pick<FriendsCourt, 'startsAt' | 'homeClubFull'> = {
    startsAt: '2026-11-07T09:00:00Z',
    homeClubFull: true,
  };

  it('says the home club is full then', () => {
    expect(fullAtLine(row, { id: 'ogrody', name: 'Ogrody 33' })).toBe('Ogrody 33 is full at 10:00');
  });

  it('says nothing for the home club’s own court', () => {
    expect(fullAtLine({ ...row, homeClubFull: false }, { id: 'ogrody', name: 'Ogrody 33' })).toBe(
      undefined,
    );
  });
});

describe('a row, spoken', () => {
  it('is the hour, the court, who is free, the share and the marker', () => {
    const row: FriendsCourt = {
      startsAt: '2026-11-07T09:00:00Z',
      club: { id: 'wisla', name: 'Wisła Park' },
      courtId: 'c3',
      courtName: 'Court 3',
      indoor: true,
      shareGrosze: 2500,
      homeClubFull: true,
      busy: ['ania'],
    };

    expect(courtRowSpoken(row, 'ania.k busy', 'Ogrody 33 is full at 10:00', true)).toBe(
      '10:00, Wisła Park · Court 3, ania.k busy, 25 zł each, Ogrody 33 is full at 10:00, picked',
    );
  });
});

describe('what the card says in its place', () => {
  it('says four can’t play together, or two in singles, naming nobody', () => {
    expect(refusalLine('cannot_play_together', 'padel', 4)).toBe(
      'These four can’t all play together. Swap someone.',
    );
    expect(refusalLine('cannot_play_together', 'tennis', 2)).toBe(
      'These two can’t play together. Swap someone.',
    );
  });

  it('says somebody has no level in the sport, or is no longer a friend', () => {
    expect(refusalLine('no_level', 'padel', 4)).toBe(
      'Somebody here has no padel level yet. Swap someone.',
    );
    expect(refusalLine('not_a_friend', 'padel', 4)).toBe(
      'Somebody here isn’t your friend any more. Seat someone else.',
    );
  });
});
