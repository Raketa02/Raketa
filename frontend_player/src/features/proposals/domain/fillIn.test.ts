import type { DeckPerson } from './deck';
import type { LiveYes } from './liveYes';
import {
  mayWithdraw,
  squaresOfYes,
  standingSeats,
  yesOnRow,
  yesesIn,
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

describe('yesesIn — You’re In (§10.2)', () => {
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

describe('squaresOfYes — a You’re In row’s squares (A3.2)', () => {
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

describe('mayWithdraw — Withdraw on a You’re In row', () => {
  it('is offered only once the details say so — never while a payment is awaited, nor before the read', () => {
    expect(mayWithdraw({ actions: ['WITHDRAW'] })).toBe(true);
    expect(mayWithdraw({ actions: ['LEAVE'] })).toBe(false);
    expect(mayWithdraw(undefined)).toBe(false);
  });
});
