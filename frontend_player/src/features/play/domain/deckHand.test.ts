/**
 * The rules on this file somebody could get wrong: **a spent deal is not an empty pool**, an
 * empty pool has two readings, **the cards behind are real people or nothing**, and *N left*
 * counts the pool rather than the hand.
 *
 * Written against the split rather than against the arithmetic, because the arithmetic is a
 * filter and the split is the decision — get it wrong and a player who has answered ten cards
 * is told to widen their radius, which is the product sending them further away from people it
 * has already found for them.
 */

import type { Candidate, PoolDescription } from './candidate';

import {
  CARDS_BEHIND,
  PREFETCH_AT,
  appendHand,
  cardKey,
  cardsLeft,
  deckStanding,
  oneFewerWaiting,
  unansweredIn,
  wantsTheNextHand,
  type AnsweredCard,
  type DeckDeal,
} from './deckHand';

const POOL: PoolDescription = {
  radiusKmUsed: 12,
  playersInRange: 7,
  window: 'THIS_WEEK',
  remaining: 5,
  wantToPlayYou: 0,
};

function candidate(playerId: string): Candidate {
  return {
    playerId,
    fit: 78,
    card: {
      name: playerId,
      areaCode: 'A+050612+0019938',
      socialTags: [],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    terms: [],
    concerns: [],
    livenessReasons: [],
    degradedTerms: [],
    modifiers: [],
  };
}

interface DealOver {
  readonly pool?: PoolDescription;
  /** The latest hand's size. Defaults to the whole list, which is one hand. */
  readonly latestHand?: number;
}

/** Answered on the one hand every fixture below deals, unless a test says otherwise. */
const done = (...playerIds: readonly string[]): readonly AnsweredCard[] =>
  playerIds.map((playerId) => ({ searchId: 'deal-1', playerId }));

function deal(playerIds: readonly string[], over: DealOver = {}): DeckDeal {
  return {
    cards: playerIds.map((playerId) => ({ candidate: candidate(playerId), searchId: 'deal-1' })),
    pool: over.pool ?? POOL,
    latestHand: over.latestHand ?? playerIds.length,
  };
}

describe('the card in front of you', () => {
  it('is the first row nobody has answered', () => {
    expect(deckStanding(deal(['a', 'b', 'c']), done('a'))).toMatchObject({
      kind: 'card',
      card: { candidate: { playerId: 'b' } },
    });
  });

  /**
   * The order is the deck's — the lifted band, then the rest — and nothing on this side sorts,
   * so answering out of order is not a case this rule has to invent an answer for.
   */
  it('keeps the dealt order rather than reordering what is left', () => {
    expect(deckStanding(deal(['a', 'b', 'c']), done('b'))).toMatchObject({
      kind: 'card',
      card: { candidate: { playerId: 'a' } },
    });
  });

  it('carries the deal each card came off, because that is the origin key its answer cites', () => {
    const held: DeckDeal = {
      cards: [
        { candidate: candidate('a'), searchId: 'deal-1' },
        { candidate: candidate('b'), searchId: 'deal-2' },
      ],
      pool: POOL,
      latestHand: 1,
    };

    expect(deckStanding(held, done('a'))).toMatchObject({
      kind: 'card',
      card: { searchId: 'deal-2' },
    });
  });
});

describe('an answer belongs to a card, not a person', () => {
  /**
   * The same player dealt again on a later hand — after a reset, or once the dealt memory has
   * lapsed — is a new card. An answer given on the first deal must not hide the second.
   */
  it('shows a person dealt again on a later hand, though they were answered on an earlier one', () => {
    const twice: DeckDeal = {
      cards: [
        { candidate: candidate('a'), searchId: 'deal-1' },
        { candidate: candidate('a'), searchId: 'deal-2' },
      ],
      pool: POOL,
      latestHand: 1,
    };

    expect(deckStanding(twice, done('a'))).toMatchObject({
      kind: 'card',
      card: { searchId: 'deal-2' },
    });
    expect(deckStanding(twice, [...done('a'), { searchId: 'deal-2', playerId: 'a' }])).toEqual({
      kind: 'spent',
    });
  });
});

describe('the cards behind', () => {
  /**
   * Two real people, offset and scaled back — never a placeholder. The stack says *there are
   * more*, and it may only say so about people who are actually there.
   */
  it('are the next two unanswered people, in order', () => {
    expect(deckStanding(deal(['a', 'b', 'c', 'd']), done())).toMatchObject({
      kind: 'card',
      behind: [{ candidate: { playerId: 'b' } }, { candidate: { playerId: 'c' } }],
    });
    expect(CARDS_BEHIND).toBe(2);
  });

  it('are one when one remains, and none when none does', () => {
    expect(deckStanding(deal(['a', 'b']), done())).toMatchObject({
      behind: [{ candidate: { playerId: 'b' } }],
    });
    expect(deckStanding(deal(['a']), done())).toMatchObject({ behind: [] });
  });

  it('skips the answered, exactly as the top card does', () => {
    expect(deckStanding(deal(['a', 'b', 'c', 'd']), done('b'))).toMatchObject({
      card: { candidate: { playerId: 'a' } },
      behind: [{ candidate: { playerId: 'c' } }, { candidate: { playerId: 'd' } }],
    });
  });
});

describe('having no card is three different things', () => {
  it('is a spent deal when every card was answered — a request, never a screen', () => {
    expect(deckStanding(deal(['a', 'b']), done('a', 'b'))).toEqual({ kind: 'spent' });
  });

  it('is *you have seen everybody* when a fresh deal is empty and people are in range', () => {
    expect(deckStanding(deal([]), done())).toEqual({ kind: 'seen-everybody' });
  });

  it('is *nobody in range* only when the post-gate count is nought', () => {
    const thin = deal([], { pool: { ...POOL, playersInRange: 0 } });

    expect(deckStanding(thin, done())).toEqual({ kind: 'nobody-in-range' });
  });

  /**
   * The failure this split exists to prevent: ten cards answered in a healthy pool must not
   * reach the state whose advice is *widen your radius*.
   */
  it('never reads a spent deal as a thin pool, whatever the count says', () => {
    const spent = deal(['a'], { pool: { ...POOL, playersInRange: 0 } });

    expect(deckStanding(spent, done('a'))).toEqual({ kind: 'spent' });
  });

  /**
   * The next hand is appended to the one being answered, so an empty *latest* hand under
   * unanswered cards is not yet an ending — and once they are answered it is one, with no
   * further deal: the pool has already said there is nobody.
   */
  it('is an ending once the cards above an empty latest hand are answered', () => {
    const appended = deal(['a', 'b'], { latestHand: 0 });

    expect(deckStanding(appended, done('a'))).toMatchObject({ kind: 'card' });
    expect(deckStanding(appended, done('a', 'b'))).toEqual({ kind: 'seen-everybody' });
  });
});

describe('N left', () => {
  /**
   * *"A counter that says 2 left and then produces ten more lies."* The number is the whole
   * pool — what the server says is beyond this hand, plus what is still unanswered in it — and
   * it counts down by one per answer.
   */
  it('is the pool beyond the hand plus the hand still unanswered', () => {
    const held = deal(['a', 'b', 'c']);

    expect(unansweredIn(held, done())).toBe(3);
    expect(cardsLeft(held, done())).toBe(8);
    expect(cardsLeft(held, done('a'))).toBe(7);
    expect(cardsLeft(held, done('a', 'b', 'c'))).toBe(5);
  });

  it('reads the pool as nought where a deal did not say', () => {
    const { remaining: _dropped, ...noCount } = POOL;

    expect(cardsLeft(deal(['a'], { pool: noCount }), done())).toBe(1);
  });
});

describe('asking for the next hand', () => {
  it('is wanted once two unanswered cards remain, and there are people beyond the hand', () => {
    const held = deal(['a', 'b', 'c']);

    expect(PREFETCH_AT).toBe(2);
    expect(wantsTheNextHand(held, done())).toBe(false);
    expect(wantsTheNextHand(held, done('a'))).toBe(true);
    expect(wantsTheNextHand(held, done('a', 'b'))).toBe(true);
  });

  it('is not wanted when the pool has nobody beyond the hand', () => {
    const last = deal(['a', 'b'], { pool: { ...POOL, remaining: 0 } });

    expect(wantsTheNextHand(last, done())).toBe(false);
    expect(wantsTheNextHand(last, done('a'))).toBe(false);
  });

  /**
   * A latest hand of nought under a pool that still claims people would otherwise be asked
   * for again on every render — and the server has already answered that question.
   */
  it('is not wanted after a hand that brought nobody', () => {
    expect(wantsTheNextHand(deal(['a', 'b'], { latestHand: 0 }), [])).toBe(false);
  });
});

describe('folding a hand onto the deal', () => {
  const hand = (searchId: string, ...playerIds: readonly string[]) => ({
    searchId,
    candidates: playerIds.map(candidate),
    pool: { ...POOL, remaining: 3 },
  });

  it('starts the deal where nothing is held, every card citing the hand it came off', () => {
    const held = appendHand(undefined, hand('deal-1', 'a', 'b'));

    expect(held.cards.map(cardKey)).toEqual(['deal-1:a', 'deal-1:b']);
    expect(held.latestHand).toBe(2);
    expect(held.pool.remaining).toBe(3);
  });

  it('keeps the cards already dealt in front, and takes the latest hand’s pool', () => {
    const held = appendHand(appendHand(undefined, hand('deal-1', 'a')), hand('deal-2', 'b', 'c'));

    expect(held.cards.map(cardKey)).toEqual(['deal-1:a', 'deal-2:b', 'deal-2:c']);
    expect(held.latestHand).toBe(2);
  });

  /** A person again on a new hand is a new card — after a reset, or once the memory has lapsed. */
  it('deals a person again on a new hand', () => {
    const held = appendHand(appendHand(undefined, hand('deal-1', 'a')), hand('deal-2', 'a'));

    expect(held.cards.map(cardKey)).toEqual(['deal-1:a', 'deal-2:a']);
    expect(held.latestHand).toBe(1);
  });

  /**
   * The same card twice — the same person on the same hand, which the route never does — would
   * hold a hand that can never be answered out, and the ask for the next one would never stop.
   */
  it('drops the same card twice, so a hand of nothing new is a hand of nought', () => {
    const held = appendHand(appendHand(undefined, hand('deal-1', 'a')), hand('deal-1', 'a'));

    expect(held.cards.map(cardKey)).toEqual(['deal-1:a']);
    expect(held.latestHand).toBe(0);
  });
});

describe('one fewer waiting', () => {
  const liker: Candidate = { ...candidate('a'), inclusionReason: 'INTEREST_LIFT' };
  const twoWaiting: DeckDeal = {
    cards: [
      { candidate: liker, searchId: 'deal-1' },
      { candidate: candidate('b'), searchId: 'deal-1' },
    ],
    pool: { ...POOL, wantToPlayYou: 2 },
    latestHand: 2,
  };

  it('drops the count by one on a liker’s card', () => {
    expect(
      oneFewerWaiting(twoWaiting, { searchId: 'deal-1', playerId: 'a' }).pool.wantToPlayYou,
    ).toBe(1);
  });

  /** A mutual on a stranger's card is somebody who said yes after the deal counted. */
  it('leaves the count alone on a stranger’s card, and on a card the deal does not hold', () => {
    expect(oneFewerWaiting(twoWaiting, { searchId: 'deal-1', playerId: 'b' })).toBe(twoWaiting);
    expect(oneFewerWaiting(twoWaiting, { searchId: 'deal-9', playerId: 'a' })).toBe(twoWaiting);
  });

  it('never goes below nought, and leaves a deal with no count alone', () => {
    const none = { ...twoWaiting, pool: { ...POOL, wantToPlayYou: 0 } };
    const { wantToPlayYou: _dropped, ...uncounted } = POOL;
    const unknown = { ...twoWaiting, pool: uncounted };

    expect(oneFewerWaiting(none, { searchId: 'deal-1', playerId: 'a' })).toBe(none);
    expect(oneFewerWaiting(unknown, { searchId: 'deal-1', playerId: 'a' })).toBe(unknown);
  });
});
