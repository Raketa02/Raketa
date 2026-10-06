/**
 * **The selection**, which is what a swap is — and the arithmetic that is not here.
 *
 * `ForecastResponse` carries all three pairings of a four, so the builder never computes a
 * forecast: it decides *which* of three it is looking at, and the number comes with it. These
 * assertions are about that decision going the right way, and about the one case that is easy
 * to get backwards — trading the two opponents is the **same game**, so its number must not
 * move.
 */

import { theme } from '@/shared/ui/theme';

import { seatPlaces } from '@/shared/vocabulary/seatPlace';

import {
  arrangementFor,
  courtSeating,
  courtWithYou,
  currentArrangement,
  evenestArrangement,
  firstEmptySeat,
  partnerOf,
  seatedIds,
  seatingOf,
  seatingToDraw,
  seatsFilled,
  shortfallBySeat,
  swapSeats,
  theirSideSeated,
  toBuildSeat,
  type Arrangement,
  type SeatedCourt,
  type Seating,
} from './forecast';

const ME = 'me-0000-4000-8000-000000000000';
const B = 'bbbbbbbb-0000-4000-8000-000000000001';
const C = 'cccccccc-0000-4000-8000-000000000002';
const D = 'dddddddd-0000-4000-8000-000000000003';

/**
 * One way round a padel four. **You are always on `A`**, which is the wire's own rule — *"there
 * is no arrangement in which the searcher crosses the net, because* which side am I on *is not
 * a question a builder asks"* — so the three fixtures differ only in who is beside you.
 */
function arrangement(
  partner: string,
  opponents: readonly [string, string],
  facts: { pairingId: number; pct: number; isCurrent?: boolean; isEvenest?: boolean },
): Arrangement {
  return {
    pairingId: facts.pairingId,
    isCurrent: facts.isCurrent ?? false,
    isEvenest: facts.isEvenest ?? false,
    seats: [
      { seatIndex: 0, relationship: 'SELF', playerId: ME },
      { seatIndex: 1, relationship: 'PARTNER', playerId: partner },
      { seatIndex: 2, relationship: 'OPPONENT', playerId: opponents[0] },
      { seatIndex: 3, relationship: 'OPPONENT', playerId: opponents[1] },
    ],
    forecast: { pct: facts.pct, sigmaGroup: 0.4, provisional: false, assumption: null },
    // The evidence behind the figure, served rather than derived — and derived here from the
    // fixture's own `pct` so the four numbers stay one computation the way the engine's are.
    split: {
      yourSide: 3.2,
      theirSide: 3.2 - (100 - facts.pct) / 100,
      gap: (100 - facts.pct) / 100,
    },
  };
}

const WITH_B = arrangement(B, [C, D], { pairingId: 1, pct: 78, isCurrent: true });
const WITH_C = arrangement(C, [B, D], { pairingId: 2, pct: 91, isEvenest: true });
const WITH_D = arrangement(D, [B, C], { pairingId: 3, pct: 64 });

const THREE = [WITH_B, WITH_C, WITH_D];

describe('reading one arrangement', () => {
  it('reads a seating in seat order, with SELF as you', () => {
    expect(seatingOf(WITH_B)).toEqual([
      { kind: 'you' },
      { kind: 'player', playerId: B },
      { kind: 'player', playerId: C },
      { kind: 'player', playerId: D },
    ]);
  });

  /**
   * Which seat is yours is `Relationship.SELF`'s answer and never an index's — **no route
   * serves a searcher their own player id**, so a seating derived from position would be the
   * one fact on this court nothing could check.
   */
  it('reads the seating off relationships rather than off the order the sides arrived in', () => {
    const shuffled: Arrangement = { ...WITH_B, seats: [...WITH_B.seats].reverse() };

    expect(seatingOf(shuffled)).toEqual(seatingOf(WITH_B));
  });

  it('reads an open seat as empty rather than as somebody', () => {
    const partial: Arrangement = {
      ...WITH_B,
      seats: [
        { seatIndex: 0, relationship: 'SELF', playerId: ME },
        { seatIndex: 1, relationship: 'PARTNER', playerId: B },
        { seatIndex: 2, relationship: 'OPPONENT' },
        { seatIndex: 3, relationship: 'OPPONENT' },
      ],
    };

    expect(seatsFilled(seatingOf(partial))).toBe(2);
    expect(seatedIds(seatingOf(partial))).toEqual([B]);
  });
});

describe('which one is drawn', () => {
  it('is the one the answer marks current', () => {
    expect(currentArrangement(THREE)).toBe(WITH_B);
  });

  /**
   * A response with no `is_current` is a build reading a document it does not know. Drawing the
   * first is the only answer that is both defined and stable — and drawing nothing would take
   * the number off a court the player is looking at.
   */
  it('falls back to the first rather than to nothing', () => {
    expect(currentArrangement([WITH_C, WITH_D])).toBe(WITH_C);
    expect(currentArrangement([])).toBeUndefined();
  });

  it('finds the evenest, which is what *Even it out* selects', () => {
    expect(evenestArrangement(THREE)).toBe(WITH_C);
  });
});

describe('a swap is a selection', () => {
  const seated = seatingOf(WITH_B);

  it('trades two seats without anybody leaving the court', () => {
    const swapped = swapSeats(seated, 1, 2);

    expect(seatedIds(swapped)).toEqual([C, B, D]);
    expect(seatsFilled(swapped)).toBe(4);
  });

  /**
   * **The case that is easy to get backwards.** Two opponents standing the other way round is
   * the same pairing, the same game and the same forecast — so the selection must not move, and
   * a screen that re-asked the server for it would spend a round trip on a swap that has none.
   */
  it('keeps the same arrangement when the two opponents trade, because it is the same game', () => {
    expect(arrangementFor(THREE, swapSeats(seated, 2, 3))).toBe(WITH_B);
  });

  it('selects another arrangement when somebody crosses the net', () => {
    expect(arrangementFor(THREE, swapSeats(seated, 1, 2))).toBe(WITH_C);
  });

  /**
   * **And a side follows you.** Swap mode is *change sides, never seats*, so you can end up in
   * the far half — at which point that half is yours, whoever is in it is your partner, and the
   * forecast is that pairing's.
   */
  it('follows you across the net, and reads your new neighbour as your partner', () => {
    const crossed = swapSeats(seated, 0, 2);

    expect(partnerOf(crossed)).toEqual({ kind: 'player', playerId: D });
    expect(arrangementFor(THREE, crossed)).toBe(WITH_D);
  });

  it('leaves the seating alone when an index it could not produce is passed', () => {
    expect(swapSeats(seated, 0, 9)).toBe(seated);
  });
});

describe('the courts that decide nothing', () => {
  /** Singles has one way round, so the seating cannot select and the current one stands. */
  it('keeps the one arrangement a singles court has', () => {
    const singles: Arrangement = {
      pairingId: 1,
      isCurrent: true,
      isEvenest: true,
      seats: [
        { seatIndex: 0, relationship: 'SELF', playerId: ME },
        { seatIndex: 1, relationship: 'OPPONENT', playerId: B },
      ],
      forecast: { pct: 80, sigmaGroup: 0.3, provisional: false, assumption: null },
      // Singles: two player strengths and the difference between them.
      split: { yourSide: 3.2, theirSide: 3.0, gap: 0.2 },
    };

    const seating = seatingOf(singles);
    expect(partnerOf(seating)).toBeUndefined();
    expect(arrangementFor([singles], swapSeats(seating, 0, 1))).toBe(singles);
  });

  /** A partner seat still open cannot pick between three, so the current one stands. */
  it('keeps the current one while the partner seat is empty', () => {
    const seating: Seating = [
      { kind: 'you' },
      { kind: 'empty' },
      { kind: 'player', playerId: C },
      { kind: 'empty' },
    ];

    expect(arrangementFor(THREE, seating)).toBe(WITH_B);
  });
});

describe('the court a line-up answer seated', () => {
  const court: SeatedCourt = {
    seats: [
      { seatIndex: 0, relationship: 'SELF', playerId: ME, unfilled: null },
      { seatIndex: 1, relationship: 'PARTNER', playerId: B, unfilled: null },
      { seatIndex: 2, relationship: 'OPPONENT', unfilled: 'POOL_EXHAUSTED' },
      { seatIndex: 3, relationship: 'OPPONENT', unfilled: 'POOL_EXHAUSTED' },
    ],
    arrangements: [],
    groupReason: null,
    dock: null,
  };

  it('reads the membership the fill seated, in seat order', () => {
    expect(seatedIds(courtSeating(court))).toEqual([B]);
    expect(seatsFilled(courtSeating(court))).toBe(2);
  });

  /**
   * The shortfall is keyed by index because **an empty seat cannot be swapped**: `tapSeat`
   * answers `OPEN_POOL` for one in both modes, so a hole never moves and an index is a stable
   * name for it.
   */
  it('states the shortfall per seat, and says nothing about a seat that is taken', () => {
    const shortfall = shortfallBySeat(court);

    expect(shortfall.get(2)).toBe('POOL_EXHAUSTED');
    expect(shortfall.get(3)).toBe('POOL_EXHAUSTED');
    expect(shortfall.has(0)).toBe(false);
    expect(shortfall.has(1)).toBe(false);
  });
});

/**
 * **The seating to draw**, and the fallback under it — the derivation that lets a builder need
 * no separate empty state and write nothing down when an answer lands.
 */
describe('the seating a court opens on', () => {
  it('is the current arrangement, once there is one', () => {
    expect(seatingToDraw(THREE, { seats: 4, members: [B, C, D] })).toEqual(seatingOf(WITH_B));
  });

  /**
   * Before there is an answer — an empty court, and the beat while a forecast is in flight —
   * it is **you, and the people you have added, in the order you added them**. Seat 0 is yours
   * because the engine's own roster puts it there.
   */
  it('is you and whoever has been added, before any answer', () => {
    expect(seatingToDraw([], { seats: 4, members: [C] })).toEqual([
      { kind: 'you' },
      { kind: 'player', playerId: C },
      { kind: 'empty' },
      { kind: 'empty' },
    ]);
  });

  it('seats you on a court nobody has been added to at all', () => {
    expect(seatingToDraw([], { seats: 2, members: [] })).toEqual([
      { kind: 'you' },
      { kind: 'empty' },
    ]);
    expect(seatsFilled(seatingToDraw([], { seats: 2, members: [] }))).toBe(1);
  });

  /**
   * It reads the member order rather than assuming `is_current`, which is the same thing on
   * every real answer — a fill seats out of the arrangement it drew, and a forecast marks the
   * order it was sent — and is the honest reading where they could differ.
   */
  it('draws the arrangement the members it holds imply', () => {
    expect(seatingToDraw(THREE, { seats: 4, members: [D, B, C] })).toEqual(seatingOf(WITH_D));
  });
});

describe('the court a send carries', () => {
  /**
   * The two rules that look like formatting and are not: **the organiser holds a seat like
   * anybody else** — a court without them is refused with `organiser_holds_a_seat` — and **an
   * empty seat is a seat**, because dropping it would renumber every seat behind it and the
   * side each one is on is read off the position.
   */
  it('puts you in your own seat and keeps every hole in its place', () => {
    const half: Seating = [
      { kind: 'you' },
      { kind: 'player', playerId: B },
      { kind: 'empty' },
      { kind: 'player', playerId: D },
    ];

    expect(courtWithYou(half, ME)).toEqual([ME, B, undefined, D]);
  });

  /** Swap mode is *change sides, never seats*, so your own seat is wherever you are standing. */
  it('follows you across the net rather than assuming seat 0', () => {
    const crossed: Seating = [{ kind: 'player', playerId: B }, { kind: 'you' }];

    expect(courtWithYou(crossed, ME)).toEqual([B, ME]);
  });
});

describe('where a *pick somebody* control lands', () => {
  it('is the first hole, whichever seat that is', () => {
    // Nobody added: the hole beside you.
    expect(firstEmptySeat(seatingToDraw([], { seats: 4, members: [] }))).toBe(1);
    // One added: the first hole is past them.
    expect(firstEmptySeat(seatingToDraw([], { seats: 4, members: [C] }))).toBe(2);
  });

  /** A full court answers seat 0, which is the only index that is always a seat. */
  it('answers a seat rather than nothing on a full court', () => {
    expect(firstEmptySeat(seatingOf(WITH_B))).toBe(0);
  });
});

/**
 * **A hand-seated player has accepted nothing**, and this is the one place that `false` is
 * written: opening the builder from an accepted challenge is out of scope, so the lock the
 * truth table keeps an arm for has no producer yet.
 */
describe('the rules view of a seat', () => {
  it('never claims an acceptance nothing can produce', () => {
    expect(seatingOf(WITH_B).map(toBuildSeat)).toEqual([
      { kind: 'you' },
      { kind: 'player', accepted: false },
      { kind: 'player', accepted: false },
      { kind: 'player', accepted: false },
    ]);
  });

  /** And it is what `seatPlaces` reads, which is how a side follows you across the net. */
  it('is what a side is read off', () => {
    const crossed = swapSeats(seatingOf(WITH_B), 0, 2);

    expect(seatPlaces(crossed.map(toBuildSeat))).toEqual([
      'THEIR_SIDE',
      'THEIR_SIDE',
      'YOUR_SIDE',
      'YOUR_PARTNER',
    ]);
  });
});

/**
 * **Is there anybody across the net** — the one fact the pool header's reading is gated on.
 *
 * The engine serves a forecast the moment one person is added, and reaches it by assuming an
 * empty seat matches the player opposite (`EMPTY_SEAT_MATCHES_ITS_PARTNER`). With nobody on
 * the far half that assumption mirrors your own side, so the figure is the assumption talking
 * rather than a reading — which is why the header says what would make one appear instead
 * ([#297](https://github.com/Raketa02/Raketa/issues/297)).
 */
describe('whether their side has anybody on it', () => {
  it('is false while everybody added is standing beside you', () => {
    const yoursOnly: Seating = [
      { kind: 'you' },
      { kind: 'player', playerId: B },
      { kind: 'empty' },
      { kind: 'empty' },
    ];

    expect(theirSideSeated(yoursOnly)).toBe(false);
  });

  it('is true from the first player across the net, before the court is full', () => {
    const three: Seating = [
      { kind: 'you' },
      { kind: 'player', playerId: B },
      { kind: 'player', playerId: C },
      { kind: 'empty' },
    ];

    expect(theirSideSeated(three)).toBe(true);
    expect(theirSideSeated(seatingOf(WITH_B))).toBe(true);
  });

  it('is false on a court nobody has been added to', () => {
    expect(theirSideSeated([{ kind: 'you' }, { kind: 'empty' }])).toBe(false);
  });

  it('answers a singles court, where the second seat is the opponent', () => {
    expect(theirSideSeated([{ kind: 'you' }, { kind: 'player', playerId: B }])).toBe(true);
  });

  /**
   * A side **follows you**, so *their* half is whichever one you are not standing in at the
   * moment you are asked — never the back half of the list.
   */
  it('follows you across the net rather than trusting seat order', () => {
    // [C, B, you, D]: with you at index 2, seats 0 and 1 are theirs and D at 3 is your partner.
    const crossed = swapSeats(seatingOf(WITH_B), 0, 2);

    expect(seatPlaces(crossed.map(toBuildSeat))).toEqual([
      'THEIR_SIDE',
      'THEIR_SIDE',
      'YOUR_SIDE',
      'YOUR_PARTNER',
    ]);
    expect(theirSideSeated(crossed)).toBe(true);
  });

  /**
   * The two seatings that actually falsify an index rule. *Seats 2 and 3 are theirs* answers
   * both of these wrongly, and the case above right — which is why that one is not the
   * evidence, whatever its shape suggests.
   */
  it('is not the back half of the list, which is what an index rule would read', () => {
    // You crossed and nobody followed: the only occupied seats are yours, in the far half.
    expect(
      theirSideSeated([{ kind: 'empty' }, { kind: 'empty' }, { kind: 'you' }, seatedAt(D)]),
    ).toBe(false);

    // Singles, crossed: the back seat is you, and the front one is the opponent.
    expect(theirSideSeated([seatedAt(B), { kind: 'you' }])).toBe(true);
  });

  /**
   * H-25 at this seam. Squash has no net and draws **both** seats on the near half of the
   * picture, so a rule that read the far side off a `y` coordinate would answer *nobody
   * opposite* on a court that has an opponent standing on it.
   */
  it('answers squash, whose two seats are drawn on the same half (H-25)', () => {
    const [near, far] = theme.size.court.seats.squash;
    const half = theme.size.court.space.height / 2;

    expect(near?.[1]).toBeGreaterThan(half);
    expect(far?.[1]).toBeGreaterThanOrEqual(half);
    expect(theirSideSeated([{ kind: 'you' }, seatedAt(B)])).toBe(true);
  });
});

/** A seated player, as a `Seating` holds one. */
function seatedAt(playerId: string): Seating[number] {
  return { kind: 'player', playerId };
}
