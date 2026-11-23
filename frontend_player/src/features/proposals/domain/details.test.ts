import type { DeckPerson } from './deck';
import {
  completesTheGame,
  courtOfDetails,
  detailsCanRunOut,
  paymentDueOf,
  topCardOf,
  yesOnDetails,
  type ProposalDetails,
} from './details';

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
  it('carries the id, the card’s type, the court and the sides', () => {
    const shown = details({ inCount: 3 });
    expect(yesOnDetails(shown)).toEqual({
      proposalId: 'p-1',
      type: 'PICKED_FOR_YOU',
      court: 'BOOK_IT_NOW',
      sides: shown.sides,
    });
  });
});

/** Tuesday 6 October, 14:10 in Warsaw — the read; the time to pay runs to 14:40 (#625). */
const READ = Date.parse('2026-10-06T12:10:00Z');
const TWENTY_TO_THREE = '2026-10-06T12:40:00Z';
const yours = {
  seatChargeId: 's-1',
  refusal: 'AUTHENTICATION_REQUIRED',
  confirmBy: TWENTY_TO_THREE,
} as const;

describe('paymentDueOf — the times to pay the money row names (Q111)', () => {
  it('is the payment the game waits for, and the reader’s own, while each is ahead', () => {
    const waiting = details({
      status: 'WAITING_FOR_A_PAYMENT',
      paymentDueBy: TWENTY_TO_THREE,
      yourPayment: yours,
    });
    expect(paymentDueOf(waiting, READ)).toEqual({
      dueBy: { at: TWENTY_TO_THREE, today: true },
      yours: { by: { at: TWENTY_TO_THREE, today: true }, window: 'UNNAMED' },
    });
    expect(paymentDueOf(waiting, Date.parse(TWENTY_TO_THREE))).toEqual({});
  });

  it('says what the reader’s own time is for, while it runs — to fix the card (#638; Q113)', () => {
    const fixing = details({
      status: 'WAITING_FOR_A_PAYMENT',
      yourPayment: { ...yours, timeTo: 'FIX_THE_CARD' },
    });
    expect(paymentDueOf(fixing, READ)).toEqual({
      yours: { by: { at: TWENTY_TO_THREE, today: true }, window: 'FIX_THE_CARD' },
    });
    expect(paymentDueOf(fixing, Date.parse(TWENTY_TO_THREE))).toEqual({});
  });

  it('is nothing where no time is given — a refused share whose time ran out included', () => {
    expect(paymentDueOf(details(), READ)).toEqual({});
    expect(
      paymentDueOf(
        details({ yourPayment: { seatChargeId: 's-1', refusal: 'AUTHENTICATION_REQUIRED' } }),
        READ,
      ),
    ).toEqual({});
  });
});

describe('detailsCanRunOut — a deadline the money row names that leaves by itself', () => {
  it('runs while a time to pay, or the reader’s own time, is there to pass', () => {
    expect(detailsCanRunOut(details())).toBe(false);
    expect(detailsCanRunOut(details({ paymentDueBy: TWENTY_TO_THREE }))).toBe(true);
    expect(detailsCanRunOut(details({ yourPayment: yours }))).toBe(true);
  });
});

describe('topCardOf — the competitive details open on the full forecast (#839, ADR-0207 §6)', () => {
  const forecast = {
    pct: 73,
    provisional: false,
    split: { yourSide: 2.65, theirSide: 2.74, gap: -0.09 },
  };
  const atStake = { winDelta: 0.08, lossDelta: -0.07 };

  it('is the forecast and both stakes on a competitive game', () => {
    expect(topCardOf(details({ forecast, atStake }))).toEqual({
      kind: 'forecast',
      forecast,
      atStake,
    });
  });

  it('is the forecast alone where the read sends no stakes', () => {
    expect(topCardOf(details({ forecast }))).toEqual({ kind: 'forecast', forecast });
  });

  it('is nothing where the read could not forecast the game — stakes or not', () => {
    expect(topCardOf(details())).toBeUndefined();
    expect(topCardOf(details({ atStake }))).toBeUndefined();
  });

  it('is never the forecast on For fun, even when the read sends one', () => {
    expect(topCardOf(details({ kind: 'forFun', forecast, atStake }))).toBeUndefined();
  });

  it('is never the Social vibe on a competitive game, even when the read sends one', () => {
    const vibe = { pct: 67, rows: [{ tag: 'PLAYS_TO_WIN' as const, carriedBy: ['me'] }] };
    expect(topCardOf(details({ forecast, vibe }))).toEqual({ kind: 'forecast', forecast });
    expect(topCardOf(details({ vibe }))).toBeUndefined();
  });
});

describe('topCardOf — For fun opens on the Social vibe card (#840, ADR-0207 §6)', () => {
  /** Mock 7's table: you and Kuba against Magda and Filip, who are both In. */
  const table = {
    sides: {
      yours: [person('me', { isYou: true, name: 'ola.k' }), person('kuba', { name: 'kuba.w' })],
      theirs: [
        person('magda', { name: 'magda.p', isIn: true, photoUrl: 'https://photo.test/magda' }),
        person('filip', { name: 'filip.n', isIn: true }),
      ],
    },
    inCount: 2,
  };

  function forFun(vibe: ProposalDetails['vibe'], extra: Partial<ProposalDetails> = {}) {
    return topCardOf(details({ kind: 'forFun', ...table, ...(vibe ? { vibe } : {}), ...extra }));
  }

  it('is the card, with the read’s own number', () => {
    const card = forFun({ pct: 67, rows: [] });
    expect(card?.kind).toBe('vibe');
    expect(card?.kind === 'vibe' ? card.grid.pct : undefined).toBe(67);
  });

  /**
   * Mock 7 over mocks 5 and 6: you first, then the others **as the tiles stand** — Magda and Filip
   * are In, so their row is the top one, and Kuba, your partner, comes after them.
   */
  it('heads its columns with you, then the others in the tiles’ order', () => {
    const card = forFun({ pct: 67, rows: [] });
    const columns = card?.kind === 'vibe' ? card.grid.columns : [];
    expect(columns.map((column) => column.playerId)).toEqual(['me', 'magda', 'filip', 'kuba']);
    expect(columns[0]).toEqual({ playerId: 'me', isYou: true, name: 'ola.k' });
    expect(columns[1]).toEqual({
      playerId: 'magda',
      isYou: false,
      name: 'magda.p',
      photoUrl: 'https://photo.test/magda',
    });
  });

  it('follows the tiles on a tie: your partner, then the other side', () => {
    const card = forFun({ pct: 67, rows: [] }, { sides: details().sides });
    const columns = card?.kind === 'vibe' ? card.grid.columns : [];
    // `details()`' own sides: Zofia (In) beside you, Ania (In) and Ewa across — one In a side, a
    // tie, so yours is the top row.
    expect(columns.map((column) => column.playerId)).toEqual(['me', 'zofia', 'ania', 'ewa']);
  });

  it('draws two columns on a singles court', () => {
    const card = forFun(
      { pct: 50, rows: [{ tag: 'STAYS_FOR_A_DRINK', carriedBy: ['me', 'ania'] }] },
      {
        seats: 2,
        sides: { yours: [person('me', { isYou: true })], theirs: [person('ania')] },
      },
    );
    const grid = card?.kind === 'vibe' ? card.grid : undefined;
    expect(grid?.columns.map((column) => column.playerId)).toEqual(['me', 'ania']);
    expect(grid?.rows).toEqual([{ tag: 'STAYS_FOR_A_DRINK', dots: [true, true], shared: true }]);
  });

  /**
   * A dot under every carrier, in the columns' order — whatever order the read named them in. A row
   * somebody else carries is shared; a row only you carry is not.
   */
  it('puts a dot under each carrier, and marks a row shared when anybody else carries it', () => {
    const card = forFun({
      pct: 67,
      rows: [
        { tag: 'STAYS_FOR_A_DRINK', carriedBy: ['me', 'kuba'] },
        { tag: 'GENEROUS_ON_LINE_CALLS', carriedBy: ['me', 'magda'] },
        { tag: 'HERE_TO_IMPROVE', carriedBy: ['me', 'kuba', 'filip'] },
        { tag: 'HERE_FOR_A_REGULAR_GAME', carriedBy: ['me'] },
      ],
    });
    expect(card?.kind === 'vibe' ? card.grid.rows : []).toEqual([
      { tag: 'STAYS_FOR_A_DRINK', dots: [true, false, false, true], shared: true },
      { tag: 'GENEROUS_ON_LINE_CALLS', dots: [true, true, false, false], shared: true },
      { tag: 'HERE_TO_IMPROVE', dots: [true, false, true, true], shared: true },
      { tag: 'HERE_FOR_A_REGULAR_GAME', dots: [true, false, false, false], shared: false },
    ]);
  });

  /** The rows are the read's — the reader's tags in the vocabulary's order — and never resorted. */
  it('keeps the read’s rows in the read’s order, 💘 among them', () => {
    const card = forFun({
      pct: 40,
      rows: [
        { tag: 'PLAYS_TO_WIN', carriedBy: ['me'] },
        { tag: 'OPEN_TO_MEET_SOMEONE', carriedBy: ['me', 'filip'] },
        { tag: 'NEW_IN_TOWN', carriedBy: ['me'] },
      ],
    });
    expect(card?.kind === 'vibe' ? card.grid.rows.map((row) => row.tag) : []).toEqual([
      'PLAYS_TO_WIN',
      'OPEN_TO_MEET_SOMEONE',
      'NEW_IN_TOWN',
    ]);
  });

  /** A carrier the read names who stands on no tile has no column to put a dot in. */
  it('shares a row only through a carrier it can draw', () => {
    const card = forFun({
      pct: 30,
      rows: [{ tag: 'SHARES_A_LIFT', carriedBy: ['me', 'somebody-gone'] }],
    });
    expect(card?.kind === 'vibe' ? card.grid.rows : []).toEqual([
      { tag: 'SHARES_A_LIFT', dots: [true, false, false, false], shared: false },
    ]);
  });

  /** A seat still open is nobody: the table is everyone named, and the read's table is the same. */
  it('draws no column for a seat still open', () => {
    const card = forFun(
      { pct: 50, rows: [] },
      {
        inCount: 2,
        sides: {
          yours: [person('me', { isYou: true, isIn: true })],
          theirs: [person('magda', { isIn: true })],
        },
      },
    );
    expect(card?.kind === 'vibe' ? card.grid.columns.map((column) => column.playerId) : []).toEqual(
      ['me', 'magda'],
    );
  });

  /** The read sends none where fewer than two are named, or nobody holds a tag that counts. */
  it('is nothing where the read sends no vibe', () => {
    expect(forFun(undefined)).toBeUndefined();
  });
});
