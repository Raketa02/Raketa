/**
 * A changed card, put back where it was.
 *
 * Every assertion here is about something that must **not** happen. `ADR-0032`
 * keeps order on the server, and the one moment a client holds both a composed
 * screen and a freshly recomposed card is the moment it could quietly stop being
 * true — so what is tested is that the list is the same list, in the same order,
 * with one element swapped.
 */

import type { ComposedScreen, MatchCard, NowUpdate } from '../domain/ComposedScreen';

import { applyNowUpdate } from './applyNowUpdate';

function card(matchId: string, overrides: Partial<MatchCard> = {}): MatchCard {
  return {
    kind: 'match',
    matchId,
    clock: undefined,
    claimExpiresAt: undefined,
    where: {
      clubId: 'c-1',
      clubName: 'Sunset Padel',
      zone: 'Europe/Warsaw',
      cover: 'indoor',
      distanceKm: undefined,
    },
    price: { amount: 3800, currency: 'PLN' },
    situation: 'forming',
    status: undefined,
    departure: undefined,
    act: undefined,
    mayDepart: true,
    fit: undefined,
    emphasis: false,
    ...overrides,
  };
}

function screen(overrides: Partial<ComposedScreen> = {}): ComposedScreen {
  return {
    offers: { cards: [] },
    yourMatches: { cards: [] },
    shelves: { blocks: [] },
    debt: undefined,
    ...overrides,
  };
}

const LEFT: NowUpdate = {
  card: card('m-2', { mayDepart: false, departure: 'You left — nothing had been taken.' }),
};

describe('applying Now’s update', () => {
  it('replaces the card in place, and moves nothing', () => {
    const before = screen({
      yourMatches: { cards: [card('m-1'), card('m-2'), card('m-3')] },
    });

    const after = applyNowUpdate(before, LEFT);

    expect(after.yourMatches.cards.map((held) => held.matchId)).toEqual(['m-1', 'm-2', 'm-3']);
    expect(after.yourMatches.cards[1]?.mayDepart).toBe(false);
    expect(after.yourMatches.cards[1]?.departure).toBe('You left — nothing had been taken.');
  });

  it('reaches the offers region as well as the strip', () => {
    // Both are viewer-owned, and a card offered to her is as much hers to act on
    // as one she holds a seat in.
    const before = screen({ offers: { cards: [card('m-2')] } });

    expect(applyNowUpdate(before, LEFT).offers.cards[0]?.mayDepart).toBe(false);
  });

  it('never inserts a card the screen was not already holding', () => {
    // A departure from a match that is not on this sport's screen changes nothing
    // on it. Inserting the card would be the client deciding a card's *place*,
    // which is the one judgement the composition keeps.
    const before = screen({ yourMatches: { cards: [card('m-1')] } });

    const after = applyNowUpdate(before, LEFT);

    expect(after.yourMatches.cards.map((held) => held.matchId)).toEqual(['m-1']);
    expect(after.offers.cards).toEqual([]);
  });

  it('leaves the shelves alone, whatever they are holding', () => {
    // The shelves are never in an update at all. A ranked list rewritten from a
    // write is a match moving under the player's thumb.
    const shelf = {
      kind: 'shelf' as const,
      code: 'bestFit',
      title: 'Best fit for you',
      caption: undefined,
      cards: [card('m-2')],
    };
    const before = screen({ shelves: { blocks: [shelf] } });

    const after = applyNowUpdate(before, LEFT);

    expect(after.shelves).toBe(before.shelves);
    expect(after.shelves.blocks[0]).toBe(shelf);
  });

  it('hands back the same list when nothing matched', () => {
    // Identity, so a screen holding the match in neither region gives React
    // nothing to re-render.
    const cards = [card('m-1')];
    const before = screen({ yourMatches: { cards } });

    expect(applyNowUpdate(before, LEFT).yourMatches.cards).toBe(cards);
  });

  it('keeps the one fact about the viewer', () => {
    const before = screen({
      yourMatches: { cards: [card('m-2')] },
      debt: { owed: { amount: 1200, currency: 'PLN' }, blocked: true },
    });

    expect(applyNowUpdate(before, LEFT).debt).toEqual(before.debt);
  });
});
