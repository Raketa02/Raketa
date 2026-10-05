import type { DeckPerson } from './deck';
import { completesTheGame, courtOfDetails, yesOnDetails, type ProposalDetails } from './details';

const person = (playerId: string, extra: Partial<DeckPerson> = {}): DeckPerson => ({
  playerId,
  isYou: false,
  isIn: false,
  ...extra,
});

function details(extra: Partial<ProposalDetails> = {}): ProposalDetails {
  return {
    proposalId: 'p-1',
    groupId: 'group-1',
    type: 'PICKED_FOR_YOU',
    kind: 'competitive',
    sport: 'padel',
    readAt: '2026-09-30T08:00:00Z',
    status: 'FILLING',
    actions: ['YES', 'NO'],
    inCount: 2,
    seats: 4,
    startsAt: '2026-10-03T14:00:00Z',
    where: { id: 'club-1', name: 'Bonarka Arena', distanceKm: 3.1 },
    shareGrosze: 3200,
    deadline: '2026-10-02T11:00:00Z',
    noFreeCancellation: false,
    clubConfirms: false,
    sides: {
      yours: [person('me', { isYou: true }), person('zofia', { isIn: true })],
      theirs: [person('ania', { isIn: true }), person('ewa')],
    },
    overlap: { grade: 'GOOD', cells: [], game: { day: 6, range: 'AFTERNOON' } },
    ...extra,
  };
}

describe('courtOfDetails — what a yes from the details does (the deck’s own rule)', () => {
  it('is a free vote while the game is short of more than your yes', () => {
    expect(courtOfDetails(details({ inCount: 2 }))).toBe('COURT_AVAILABLE');
  });

  it('books it now when your yes is the last seat', () => {
    expect(courtOfDetails(details({ inCount: 3 }))).toBe('BOOK_IT_NOW');
  });

  it('is nothing to book for a reader already In, whose yes is said', () => {
    const youIn = details({
      inCount: 3,
      sides: {
        yours: [person('me', { isYou: true, isIn: true }), person('zofia', { isIn: true })],
        theirs: [person('ania', { isIn: true })],
      },
    });
    expect(courtOfDetails(youIn)).toBe('COURT_AVAILABLE');
    expect(completesTheGame(youIn)).toBe(false);
  });
});

describe('completesTheGame — You complete it', () => {
  it('says so only when your yes would leave no seat open', () => {
    expect(completesTheGame(details({ inCount: 3 }))).toBe(true);
    expect(completesTheGame(details({ inCount: 2 }))).toBe(false);
  });
});

describe('yesOnDetails — what the fill holds for a yes said here', () => {
  it('carries the id, the card’s type, the court, the sides and the club', () => {
    const shown = details({ inCount: 3, clubConfirms: true });
    expect(yesOnDetails(shown)).toEqual({
      proposalId: 'p-1',
      type: 'PICKED_FOR_YOU',
      court: 'BOOK_IT_NOW',
      sides: shown.sides,
      club: { id: 'club-1', name: 'Bonarka Arena' },
    });
  });
});
