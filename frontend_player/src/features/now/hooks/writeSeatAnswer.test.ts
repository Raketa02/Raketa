/**
 * Where the two halves of a seat answer land.
 *
 * The half a rendered test cannot reach, and the reason this file exists: a player
 * switches chips, so several composed screens sit in the cache at once and **only
 * one of them is on display**. The card belongs on all of them and the two regions
 * belong on exactly one — the chip the write went out under, which is the chip
 * they were composed under. A screen test would pass either way, because it can
 * only see the one screen it is standing on.
 */

import { QueryClient } from '@tanstack/react-query';

import type { ComposedScreen, MatchCard, SeatAnswer } from '../domain/ComposedScreen';

import { nowKeys } from './nowKeys';
import { writeSeatAnswer } from './writeSeatAnswer';

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
    situation: 'seatOpened',
    status: undefined,
    departure: undefined,
    score: undefined,
    act: undefined,
    mayDepart: false,
    fit: undefined,
    emphasis: false,
    ...overrides,
  };
}

/** A screen with the offer on it and nothing in the strip — where a race starts. */
function screenOffering(matchId: string): ComposedScreen {
  return {
    offers: { cards: [card(matchId)] },
    yourMatches: { cards: [] },
    shelves: { blocks: [] },
    debt: undefined,
  };
}

const HERS = card('m-1', { claimExpiresAt: '2026-08-24T18:05:00Z', situation: 'confirmed' });

/** What the server answers a tap that applied: the card, and both regions whole. */
const TAKEN: SeatAnswer = {
  claimed: true,
  update: { kind: 'card', card: HERS },
  regions: { offers: { cards: [] }, yourMatches: { cards: [HERS] } },
};

/** What it answers a tap that did not: the corrected card, and no region at all. */
const REFUSED: SeatAnswer = {
  claimed: false,
  update: { kind: 'card', card: card('m-1', { situation: 'full' }) },
  regions: undefined,
};

let client: QueryClient;

beforeEach(() => {
  client = new QueryClient();
});

afterEach(() => {
  client.clear();
});

describe('a tap that applied', () => {
  it('writes the two regions to the chip it was sent under, and to no other', () => {
    client.setQueryData(nowKeys.screen('all'), screenOffering('m-1'));
    client.setQueryData(nowKeys.screen('PADEL'), screenOffering('m-1'));

    writeSeatAnswer(client, TAKEN, 'all');

    const composed = client.getQueryData<ComposedScreen>(nowKeys.screen('all'));
    const padel = client.getQueryData<ComposedScreen>(nowKeys.screen('PADEL'));

    expect(composed?.offers.cards).toEqual([]);
    expect(composed?.yourMatches.cards.map((c) => c.matchId)).toEqual(['m-1']);
    // The padel screen's regions are its own — composed under a different filter,
    // so writing `all`'s over them would replace her filtered screen.
    expect(padel?.offers.cards.map((c) => c.matchId)).toEqual(['m-1']);
    expect(padel?.yourMatches.cards).toEqual([]);
  });

  it('still corrects the card on every other chip’s screen', () => {
    // The card is a card whatever chip is held. Left uncorrected, the padel screen
    // would go on offering a seat that is already hers until the next ask.
    client.setQueryData(nowKeys.screen('PADEL'), screenOffering('m-1'));

    writeSeatAnswer(client, TAKEN, 'all');

    const padel = client.getQueryData<ComposedScreen>(nowKeys.screen('PADEL'));
    expect(padel?.offers.cards[0]?.claimExpiresAt).toBe('2026-08-24T18:05:00Z');
  });

  it('never touches the shelves', () => {
    // `ADR-0032`: dropping a joined match out of *Best fit* would re-order a shelf
    // under her thumb. The shelf copy is corrected by the one card instead.
    const shelved: ComposedScreen = {
      ...screenOffering('m-1'),
      shelves: {
        blocks: [
          { kind: 'shelf', code: 'bestFit', title: 'x', caption: undefined, cards: [card('m-1')] },
        ],
      },
    };
    client.setQueryData(nowKeys.screen('all'), shelved);

    writeSeatAnswer(client, TAKEN, 'all');

    const held = client.getQueryData<ComposedScreen>(nowKeys.screen('all'));
    expect(held?.shelves).toBe(shelved.shelves);
  });

  it('never touches the debt line', () => {
    // A seat claim moves no money: what she owes changes when a payment does, and
    // the next of the four asks is what collects it. Dropping it here would take
    // the one line on Now that tells her why creating a match is unavailable.
    const owing: ComposedScreen = {
      ...screenOffering('m-1'),
      debt: { owed: { amount: 2400, currency: 'PLN' }, blocked: true },
    };
    client.setQueryData(nowKeys.screen('all'), owing);

    writeSeatAnswer(client, TAKEN, 'all');

    expect(client.getQueryData<ComposedScreen>(nowKeys.screen('all'))?.debt).toEqual(owing.debt);
  });

  it('creates nothing for a chip that has never been composed', () => {
    writeSeatAnswer(client, TAKEN, 'all');

    expect(client.getQueryCache().getAll()).toHaveLength(0);
  });

  it('does not mark anything stale', () => {
    client.setQueryData(nowKeys.screen('all'), screenOffering('m-1'));

    writeSeatAnswer(client, TAKEN, 'all');

    expect(client.getQueryState(nowKeys.screen('all'))?.isInvalidated).toBe(false);
  });
});

describe('a tap that did not apply', () => {
  it('leaves both regions exactly as they were', () => {
    // A refusal moved nothing, and the corrected card staying where it sat is what
    // lets the screen write its own line over it rather than watching it vanish.
    const before = screenOffering('m-1');
    client.setQueryData(nowKeys.screen('all'), before);

    writeSeatAnswer(client, REFUSED, 'all');

    const held = client.getQueryData<ComposedScreen>(nowKeys.screen('all'));
    expect(held?.offers.cards.map((c) => c.matchId)).toEqual(['m-1']);
    expect(held?.offers.cards[0]?.situation).toBe('full');
    expect(held?.yourMatches.cards).toEqual([]);
  });
});
