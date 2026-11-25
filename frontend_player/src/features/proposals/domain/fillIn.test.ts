import type { ReadStage } from '@/shared/lib/query-client';

import type { DeckPerson } from './deck';
import type { LiveYes } from './liveYes';
import {
  mayWithdraw,
  rescueIds,
  squaresOfYes,
  standingSeats,
  yesIds,
  yesOnRow,
  yesesIn,
  youreInEmpty,
  youreInRead,
  type SeatToFill,
} from './fillIn';

const CUT_OFF = '2026-10-02T14:00:00Z';

function row(extra: Partial<SeatToFill> = {}): SeatToFill {
  return {
    bookingId: 'b-1',
    sport: 'padel',
    kind: 'competitive',
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'club-1', name: 'Ogrody 33' },
    courtName: 'Court 6',
    shareGrosze: 2700,
    openSeats: 1,
    deadline: CUT_OFF,
    fillsByTheCutOff: true,
    players: [],
    ...extra,
  };
}

function yes(extra: Partial<LiveYes> = {}): LiveYes {
  return {
    proposalId: 'p-1',
    groupId: 'group-1',
    sport: 'padel',
    kind: 'competitive',
    startsAt: '2026-10-03T13:00:00Z',
    club: { id: 'club-1', name: 'Bonarka Arena' },
    shareGrosze: 2800,
    deadline: '2026-10-03T11:00:00Z',
    ...extra,
  };
}

describe('standingSeats — a row leaves at its deadline (§10.1)', () => {
  it('keeps a row until its deadline, and lets it go at it', () => {
    const rows = [row()];
    expect(standingSeats(rows, Date.parse(CUT_OFF) - 1)).toEqual(rows);
    expect(standingSeats(rows, Date.parse(CUT_OFF))).toEqual([]);
  });
});

describe('yesOnRow — what the fill holds for a row’s I’m in', () => {
  it('is the booking’s seat, a rescue that waits behind Undo, with no sides', () => {
    expect(yesOnRow(row())).toEqual({
      proposalId: 'b-1',
      type: 'SEAT_OPEN',
      court: 'BOOKED',
    });
  });
});

describe('yesesIn — You’re in (§10.2)', () => {
  it('is the live yeses of this group in this sport, in the list’s order', () => {
    const here = yes({ proposalId: 'p-1' });
    const later = yes({ proposalId: 'p-2' });
    const yeses = [
      here,
      yes({ proposalId: 'other-group', groupId: 'group-2' }),
      yes({ proposalId: 'tennis', sport: 'tennis' }),
      later,
    ];
    expect(yesesIn(yeses, 'group-1', 'padel')).toEqual([here, later]);
  });
});

// ADR-0208 §1: a row is known by its id, so a row that only changed keeps it.
describe('the ids the two tabs count (#849)', () => {
  it('is the booking of each rescue still standing, on Fill in', () => {
    const rows = [
      row({ bookingId: 'b-1' }),
      row({ bookingId: 'b-2', deadline: '2026-10-01T10:00:00Z' }),
    ];

    expect(rescueIds(standingSeats(rows, Date.parse('2026-10-01T12:00:00Z')))).toEqual(['b-1']);
  });

  it('is the proposal of each live yes in this group and sport, on You’re in', () => {
    const yeses = [yes({ proposalId: 'p-1' }), yes({ proposalId: 'p-2', groupId: 'group-2' })];

    expect(yesIds(yesesIn(yeses, 'group-1', 'padel'))).toEqual(['p-1']);
  });
});

describe('squaresOfYes — a You’re in row’s squares (A3.2)', () => {
  const person = (playerId: string, isIn: boolean): DeckPerson => ({
    playerId,
    isYou: playerId === 'me',
    isIn,
  });

  it('is everybody In, then a dashed square per seat still open', () => {
    const squares = squaresOfYes({
      seats: 4,
      inCount: 2,
      sides: {
        yours: [person('me', true), person('zofia', true)],
        theirs: [person('ania', false)],
      },
    });
    expect(squares.people.map((one) => one.playerId)).toEqual(['me', 'zofia']);
    expect(squares.open).toBe(2);
  });
});

describe('mayWithdraw — Withdraw on a You’re in row', () => {
  it('is offered only once the details say so — never while a payment is awaited, nor before the read', () => {
    expect(mayWithdraw({ actions: ['WITHDRAW'] })).toBe(true);
    expect(mayWithdraw({ actions: ['LEAVE'] })).toBe(false);
    expect(mayWithdraw(undefined)).toBe(false);
  });
});

describe('youreInEmpty — You’re in with no yes (#847, split Q3)', () => {
  it('is the starting card only once Fill in has said there is nothing too', () => {
    expect(youreInEmpty([], false)).toBe('startingCard');
  });

  it('is the one line while Fill in has a rescue', () => {
    expect(youreInEmpty([row()], false)).toBe('line');
  });

  it('is the one line while Fill in could not say — the card needs both reads', () => {
    expect(youreInEmpty(undefined, true)).toBe('line');
  });

  it('waits while Fill in’s read is on its way — never the card as a first frame', () => {
    expect(youreInEmpty(undefined, false)).toBe('waiting');
  });
});

// #875: when You’re in's first read has finished, for the group page's reveal.
describe('youreInRead — how far You’re in’s reads have come', () => {
  it.each<[string, ReadStage, number | undefined, ReadStage, ReadStage]>([
    ['the yeses on their way', 'reading', undefined, 'landed', 'reading'],
    ['the yeses refused, held or retrying', 'ended', undefined, 'landed', 'ended'],
    ['a yes here: its rows, whatever Fill in does', 'landed', 2, 'reading', 'landed'],
    ['no yes here, Fill in on its way: the card waits for it', 'landed', 0, 'reading', 'reading'],
    ['no yes here, Fill in read: the starting card or the line', 'landed', 0, 'landed', 'landed'],
    ['no yes here, Fill in refused, held or retrying', 'landed', 0, 'ended', 'ended'],
  ])('%s', (_case, yeses, here, rescues, stage) => {
    expect(youreInRead(yeses, here, rescues)).toBe(stage);
  });
});
