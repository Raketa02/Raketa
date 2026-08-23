/**
 * The one write another feature makes to this screen.
 *
 * What a rendered test cannot reach: **which** cached screens an action corrects.
 * A player switches chips, so several screens are in the cache at once and only
 * one of them is on display — and the one she is looking at is the one a shallow
 * implementation would happen to fix.
 */

import { QueryClient } from '@tanstack/react-query';

import type { ComposedScreen, MatchCard, NowUpdate } from '../domain/ComposedScreen';

import { nowKeys } from './nowKeys';
import { writeNowUpdate } from './writeNowUpdate';

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

function screenHolding(matchId: string): ComposedScreen {
  return {
    offers: { cards: [] },
    yourMatches: { cards: [card(matchId)] },
    shelves: { blocks: [] },
    debt: undefined,
  };
}

const LEFT: NowUpdate = { card: card('m-1', { mayDepart: false, departure: 'You left.' }) };

let client: QueryClient;

beforeEach(() => {
  client = new QueryClient();
});

afterEach(() => {
  client.clear();
});

describe('writing Now’s update', () => {
  it('corrects every sport’s screen, not the one she happens to be on', () => {
    // The sport is part of the key — one request per chip, never a filter over a
    // payload holding every sport — so a match she left is stale on `all` **and**
    // on its own sport's screen. Correcting whichever chip she was standing on
    // leaves the other to be discovered later as a card offering an act that is
    // gone.
    client.setQueryData(nowKeys.screen('all'), screenHolding('m-1'));
    client.setQueryData(nowKeys.screen('PADEL'), screenHolding('m-1'));

    writeNowUpdate(client, LEFT);

    for (const sport of ['all', 'PADEL'] as const) {
      const held = client.getQueryData<ComposedScreen>(nowKeys.screen(sport));
      expect(held?.yourMatches.cards[0]?.mayDepart).toBe(false);
    }
  });

  it('leaves a screen that was never holding the match alone', () => {
    client.setQueryData(nowKeys.screen('SQUASH'), screenHolding('m-2'));

    writeNowUpdate(client, LEFT);

    const held = client.getQueryData<ComposedScreen>(nowKeys.screen('SQUASH'));
    expect(held?.yourMatches.cards.map((c) => c.matchId)).toEqual(['m-2']);
  });

  it('creates nothing for a sport that has never been composed', () => {
    // A write that seeded a cache entry would put a screen on display with one
    // card and no regions around it, on the next switch to that chip.
    writeNowUpdate(client, LEFT);

    expect(client.getQueryData(nowKeys.screen('TENNIS'))).toBeUndefined();
    expect(client.getQueryCache().getAll()).toHaveLength(0);
  });

  it('does not mark anything stale', () => {
    // A departure changes more than one card — the counting moves for everybody in
    // the match — and none of that is in the update, deliberately. The next of the
    // four asks collects it. Invalidating here would turn every action into a
    // refetch on the next focus, which is the cost the update exists to avoid.
    client.setQueryData(nowKeys.screen('all'), screenHolding('m-1'));

    writeNowUpdate(client, LEFT);

    expect(client.getQueryState(nowKeys.screen('all'))?.isInvalidated).toBe(false);
  });
});
