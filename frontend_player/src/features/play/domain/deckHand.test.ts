/**
 * The one rule on this file somebody could get wrong: **a spent deal is not an empty pool**,
 * and an empty pool has two readings.
 *
 * Written against the split rather than against the arithmetic, because the arithmetic is a
 * filter and the split is the decision — get it wrong and a player who has answered ten cards
 * is told to widen their radius, which is the product sending them further away from people it
 * has already found for them.
 */

import type { Candidate, PoolDescription } from './candidate';

import { deckStanding, type DeckDeal } from './deckHand';

const POOL: PoolDescription = { radiusKmUsed: 12, playersInRange: 7, window: 'THIS_WEEK' };

function candidate(playerId: string): Candidate {
  return {
    playerId,
    fit: 78,
    card: {
      nickname: playerId,
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

function deal(playerIds: readonly string[], pool: PoolDescription = POOL): DeckDeal {
  return { candidates: playerIds.map(candidate), pool };
}

describe('the card in front of you', () => {
  it('is the first row nobody has answered', () => {
    expect(deckStanding(deal(['a', 'b', 'c']), ['a'])).toMatchObject({
      kind: 'card',
      candidate: { playerId: 'b' },
    });
  });

  /**
   * The order is the deck's variety — *"people who already said Let's play to you, then the
   * liveliest, then the rest"* — and nothing on this side sorts, so answering out of order is
   * not a case this rule has to invent an answer for.
   */
  it('keeps the dealt order rather than reordering what is left', () => {
    expect(deckStanding(deal(['a', 'b', 'c']), ['b'])).toMatchObject({
      kind: 'card',
      candidate: { playerId: 'a' },
    });
  });
});

describe('having no card is three different things', () => {
  it('is a spent deal when every card was answered — a request, never a screen', () => {
    expect(deckStanding(deal(['a', 'b']), ['a', 'b'])).toEqual({ kind: 'spent' });
  });

  it('is *you have seen everybody* when a fresh deal is empty and people are in range', () => {
    expect(deckStanding(deal([]), [])).toEqual({ kind: 'seen-everybody' });
  });

  it('is *nobody in range* only when the post-gate count is nought', () => {
    const thin = deal([], { ...POOL, playersInRange: 0 });

    expect(deckStanding(thin, [])).toEqual({ kind: 'nobody-in-range' });
  });

  /**
   * The failure this split exists to prevent: ten cards answered in a healthy pool must not
   * reach the state whose advice is *widen your radius*.
   */
  it('never reads a spent deal as a thin pool, whatever the count says', () => {
    const spent = deal(['a'], { ...POOL, playersInRange: 0 });

    expect(deckStanding(spent, ['a'])).toEqual({ kind: 'spent' });
  });
});
