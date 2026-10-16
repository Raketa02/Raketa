import { setDeviceZone } from '@/test-support/deviceZone';

import type { SeatToFill } from '../domain/fillIn';
import type { LiveYes } from '../domain/liveYes';

import {
  rowTitle,
  seatRowLabel,
  seatWhen,
  seatsToFillHeader,
  yesRowLabel,
  yesWhen,
  youreInHeader,
} from './fillInPresentation';

beforeAll(() => setDeviceZone('America/New_York'));

const row = (extra: Partial<SeatToFill> = {}): SeatToFill => ({
  bookingId: 'b-1',
  sport: 'padel',
  kind: 'competitive',
  // Saturday 3 October, 16:00 in Warsaw.
  startsAt: '2026-10-03T14:00:00Z',
  club: { id: 'club-1', name: 'Ogrody 33' },
  courtName: 'Court 6',
  shareGrosze: 2700,
  openSeats: 1,
  // Friday 2 October, 16:00 in Warsaw — the cut-off.
  deadline: '2026-10-02T14:00:00Z',
  fillsByTheCutOff: true,
  players: [],
  ...extra,
});

const yes = (extra: Partial<LiveYes> = {}): LiveYes => ({
  proposalId: 'p-1',
  groupId: 'group-1',
  sport: 'padel',
  kind: 'competitive',
  // Saturday 3 October, 15:00 in Warsaw.
  startsAt: '2026-10-03T13:00:00Z',
  club: { id: 'club-1', name: 'Bonarka Arena' },
  shareGrosze: 2800,
  // Saturday 3 October, 13:00 in Warsaw — the book-by.
  deadline: '2026-10-03T11:00:00Z',
  ...extra,
});

const SATURDAY = { kind: 'weekday', weekday: 6 } as const;

describe('the sections’ heads (mock 11)', () => {
  it('count their rows', () => {
    expect(seatsToFillHeader(1)).toBe('Seats to fill · 1');
    expect(youreInHeader(2)).toBe('You’re In · 2');
  });
});

describe('rowTitle — Padel · Saturday 16:00 (A3.1, A3.2)', () => {
  it('names the sport, the day as the court block does and the hour — and a friendly as one', () => {
    expect(rowTitle(row(), SATURDAY)).toBe('Padel · Saturday 16:00');
    expect(rowTitle(row({ kind: 'forFun' }), SATURDAY)).toBe('Padel · Saturday 16:00 · friendly');
    expect(rowTitle(row(), undefined)).toBe('Padel · 16:00');
  });
});

describe('seatWhen — how long a rescue is offered (A3.1)', () => {
  it('fills by the cut-off before it, and is offered until the start after it', () => {
    expect(seatWhen(row())).toBe('fills by Fri 16:00');
    expect(seatWhen(row({ fillsByTheCutOff: false }))).toBe('offered until the start');
  });
});

describe('yesWhen — a yes’s book-by (A3.2)', () => {
  it('is the book-by while the game fills', () => {
    expect(yesWhen(yes())).toBe('book by Sat 13:00');
  });
});

describe('the rows, spoken', () => {
  it('say the game, the club and its court, how long, and the seats open', () => {
    expect(seatRowLabel(row(), SATURDAY)).toBe(
      'Padel · Saturday 16:00, Ogrody 33, Court 6, fills by Fri 16:00, 1 seat open',
    );
    expect(seatRowLabel(row({ openSeats: 2 }), SATURDAY)).toBe(
      'Padel · Saturday 16:00, Ogrody 33, Court 6, fills by Fri 16:00, 2 seats open',
    );
  });

  it('say a yes’s game, its club and its book-by', () => {
    expect(yesRowLabel(yes(), SATURDAY)).toBe(
      'Padel · Saturday 15:00, Bonarka Arena, book by Sat 13:00',
    );
  });
});
