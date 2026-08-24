/**
 * The wire boundary: what the mapper keeps, what it resolves, and what it drops.
 *
 * Every fixture below is typed from the generated schema, so a contract change
 * fails `pnpm typecheck` here rather than failing an assertion somewhere confusing.
 */

import {
  clubCard,
  door,
  emptyNow,
  fit,
  fitReason,
  matchCard,
  personCard,
  seatWrite,
  shelf,
} from '@/test-support/now';
import type { Wire } from '@/test-support/transport';

import type { Block, Shelf } from '../domain/ComposedScreen';

import { toComposedScreen, toNowUpdate, toSeatAnswer } from './nowMappers';

/**
 * The mapper, asked for a chip.
 *
 * Every case but the door's is indifferent to which — the sport rides on the
 * request and comes back only to word the one block that carries none — so it
 * defaults to the chip the screen opens on.
 */
function compose(wire: Wire['NowResponse'], sport: Wire['SportFilter'] = 'all') {
  return toComposedScreen(wire, sport);
}

/** The block at this position, refusing anything that is not a shelf. */
function shelfAt(blocks: readonly Block[], index: number): Shelf {
  const block = nth(blocks, index);
  if (block.kind !== 'shelf') throw new Error(`block ${index} is a ${block.kind}, not a shelf`);
  return block;
}

/**
 * Index into a list, refusing an absent element rather than asserting one away.
 *
 * `noUncheckedIndexedAccess` is on, and a `!` here would be the one place in the
 * suite where a shape is claimed rather than checked — which is the shape of the
 * bug these tests exist to find.
 */
function nth<T>(list: readonly T[], index: number): T {
  const item = list[index];
  if (item === undefined) throw new Error(`no element at ${index} of ${list.length}`);
  return item;
}

describe('the three regions', () => {
  it('are present and empty for a player with nothing', () => {
    const screen = compose(emptyNow());

    expect(screen.offers.cards).toEqual([]);
    expect(screen.yourMatches.cards).toEqual([]);
    expect(screen.shelves.blocks).toEqual([]);
    expect(screen.debt).toBeUndefined();
  });

  it('keep the server’s order rather than sorting anything', () => {
    const screen = compose({
      ...emptyNow(),
      your_matches: {
        stamp: 1,
        cards: [
          matchCard({ matchId: 'second' }),
          matchCard({ matchId: 'first' }),
          matchCard({ matchId: 'third' }),
        ],
      },
    });

    expect(screen.yourMatches.cards.map((card) => card.matchId)).toEqual([
      'second',
      'first',
      'third',
    ]);
  });
});

describe('a match card', () => {
  it('carries both moments, and neither when the server sent neither', () => {
    const withClock = nth(
      compose({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            matchCard({
              matchId: 'm-1',
              clock: '2026-08-23T19:00:00Z',
              seatClaimExpiresAt: '2026-08-23T12:05:00Z',
            }),
          ],
        },
      }).offers.cards,
      0,
    );

    expect(withClock.clock).toBe('2026-08-23T19:00:00Z');
    expect(withClock.claimExpiresAt).toBe('2026-08-23T12:05:00Z');

    const bare = nth(
      compose({
        ...emptyNow(),
        offers: { stamp: 1, cards: [matchCard({ matchId: 'm-2' })] },
      }).offers.cards,
      0,
    );

    // `null` on the wire becomes absent here — one spelling of *nothing*, so no
    // reader has to know both.
    expect(bare.clock).toBeUndefined();
    expect(bare.claimExpiresAt).toBeUndefined();
  });

  it('resolves the situation to a sentence, with the spine’s own facts in it', () => {
    const card = nth(
      compose({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            matchCard({ matchId: 'm-1', situation: 'cancelledClub', clubName: 'Sunset Padel' }),
          ],
        },
      }).offers.cards,
      0,
    );

    expect(card.status?.line).toBe('Cancelled by Sunset Padel — everybody refunded.');
    expect(card.status?.tag).toBe('Cancelled');
    expect(card.status?.tone).toBe('ended');
  });

  it('formats the amount once, through the repo’s shared table', () => {
    const card = nth(
      compose({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [matchCard({ matchId: 'm-1', situation: 'confirmed', amount: 12000 })],
        },
      }).offers.cards,
      0,
    );

    expect(card.status?.line).toContain('120,00 zł');
    expect(card.price).toEqual({ amount: 12000, currency: 'PLN' });
  });

  it('leaves the sentence absent for a situation this build has never heard of', () => {
    // The one case a typecheck can never reach: an installed phone meeting a
    // thirty-seventh name. The card keeps its spine and loses exactly the thing that
    // is actually missing.
    const card = nth(
      compose({
        ...emptyNow(),
        offers: {
          stamp: 1,
          cards: [
            {
              ...matchCard({ matchId: 'm-1' }),
              situation: {
                situation: 'seatTransferred' as Wire['Situation'],
                facts: {
                  counts: { seats: 4, paid: 2, held: 0, turned_up: null },
                  court_total: { amount: 15200, currency: 'PLN' },
                  hold: null,
                  cause: null,
                },
              },
            },
          ],
        },
      }).offers.cards,
      0,
    );

    expect(card.situation).toBe('seatTransferred');
    expect(card.status).toBeUndefined();
    expect(card.where.clubName).toBe('Sunset Padel');
    expect(card.price.amount).toBe(3800);
  });

  it('keeps the club’s zone, its roof and its distance on the spine', () => {
    const card = nth(
      compose({
        ...emptyNow(),
        offers: { stamp: 1, cards: [matchCard({ matchId: 'm-1' })] },
      }).offers.cards,
      0,
    );

    expect(card.where.zone).toBe('Europe/Warsaw');
    expect(card.where.cover).toBe('indoor');
    expect(card.where.distanceKm).toBe(2.4);
  });

  it('carries the score exactly as it arrived, and flips nothing', () => {
    // The server put the viewer's side first and `first` is hers. A flip here would
    // be a second answer to *whose 6 was that*, which is the failure naming both
    // sides exists to prevent (`ADR-0060`).
    const card = nth(
      compose({
        ...emptyNow(),
        your_matches: {
          stamp: 1,
          cards: [
            matchCard({
              matchId: 'm-1',
              situation: 'completed',
              facts: {
                score: {
                  sides: [{ players: ['Ada', 'Kuba'] }, { players: ['Marta', 'Ola'] }],
                  sets: [
                    { first: 6, second: 4 },
                    { first: 3, second: 6 },
                  ],
                },
              },
            }),
          ],
        },
      }).yourMatches.cards,
      0,
    );

    expect(card.score?.sides.map((side) => side.players)).toEqual([
      ['Ada', 'Kuba'],
      ['Marta', 'Ola'],
    ]);
    expect(card.score?.sets).toEqual([
      { first: 6, second: 4 },
      { first: 3, second: 6 },
    ]);
  });

  it('has no score on a card the server sent none for', () => {
    // Which is thirty-four of the thirty-six: a score is on a card exactly when the
    // match has one to print, and never inferred from the situation.
    const card = nth(
      compose({
        ...emptyNow(),
        your_matches: { stamp: 1, cards: [matchCard({ matchId: 'm-1', situation: 'ready' })] },
      }).yourMatches.cards,
      0,
    );

    expect(card.score).toBeUndefined();
  });
});

describe('a shelf', () => {
  it('takes its words from its code, because no title crosses the wire', () => {
    const blocks = compose({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [shelf('bestFit', []), shelf('fullWorthWaiting', [], 'undeclaredPreferences')],
      },
    }).shelves.blocks;

    expect(shelfAt(blocks, 0).title).toBe('Best fit for you');
    expect(shelfAt(blocks, 0).caption).toBeUndefined();
    expect(shelfAt(blocks, 1).title).toBe('Full, but worth waiting for');
    expect(shelfAt(blocks, 1).caption).toBe(
      'Ordered on what we know — some of your preferences for this sport are not set.',
    );
  });

  it('has no title for a code this build has never heard of', () => {
    const blocks = compose({
      ...emptyNow(),
      shelves: {
        stamp: 1,
        shelves: [shelf('mostBooked' as Wire['ShelfCode'], [])],
      },
    }).shelves.blocks;

    expect(shelfAt(blocks, 0).code).toBe('mostBooked');
    expect(shelfAt(blocks, 0).title).toBeUndefined();
  });

  it('holds all three card types, discriminated', () => {
    const cards = shelfAt(
      compose({
        ...emptyNow(),
        shelves: {
          stamp: 1,
          shelves: [
            shelf('newPlayers', [
              matchCard({ matchId: 'm-1' }),
              personCard('p-1', 'ada'),
              clubCard('c-1', 'Kraków Padel'),
            ]),
          ],
        },
      }).shelves.blocks,
      0,
    ).cards;

    expect(cards.map((card) => card.kind)).toEqual(['match', 'person', 'club']);
  });
});

describe('the door', () => {
  /**
   * `ADR-0084`. The door is a **block in the list, in order** — the position the
   * ranked shelves would occupy, with the two light shelves beneath it.
   */
  const unratedSquash = (code: Wire['DoorCode'] = 'noRunYet'): Wire['NowResponse'] => ({
    ...emptyNow(),
    shelves: {
      stamp: 1,
      shelves: [door(code), shelf('newPlayers', []), shelf('newClubs', [])],
    },
  });

  it('keeps its position in the list rather than being lifted out of it', () => {
    const blocks = compose(unratedSquash(), 'SQUASH').shelves.blocks;

    expect(blocks.map((block) => block.kind)).toEqual(['door', 'shelf', 'shelf']);
    expect(shelfAt(blocks, 1).code).toBe('newPlayers');
    expect(shelfAt(blocks, 2).code).toBe('newClubs');
  });

  it('is worded with the chip the request carried, because the block carries none', () => {
    const blocks = compose(unratedSquash(), 'SQUASH').shelves.blocks;
    const first = nth(blocks, 0);

    expect(first.kind).toBe('door');
    expect(first.kind === 'door' ? first.copy?.line : undefined).toContain('Squash');
    expect(first.kind === 'door' ? first.copy?.action : undefined).toBe(
      'Take the Squash questions',
    );
  });

  it('says something different for a run already parked, and goes to the same place', () => {
    // Two sentences, one behaviour: the client never learns the difference, because
    // `POST /assessments` is idempotent per player and sport.
    const parked = nth(compose(unratedSquash('runParked'), 'SQUASH').shelves.blocks, 0);

    expect(parked.kind === 'door' ? parked.copy?.line : undefined).toBe(
      'Your Squash questions are waiting where you left them.',
    );
    expect(parked.kind === 'door' ? parked.copy?.action : undefined).toBe(
      'Pick up where you left off',
    );
  });

  it('has no copy for a code this build has never heard of', () => {
    // The same answer as *draw nothing for it*: a door whose sentence is blank and
    // whose button says nothing is worse than the row being missing.
    const blocks = compose(
      {
        ...emptyNow(),
        shelves: { stamp: 1, shelves: [door('reRate' as Wire['DoorCode'])] },
      },
      'SQUASH',
    ).shelves.blocks;
    const first = nth(blocks, 0);

    expect(first.kind).toBe('door');
    expect(first.kind === 'door' ? first.code : undefined).toBe('reRate');
    expect(first.kind === 'door' ? first.copy : 'not a door').toBeUndefined();
  });

  it('is absent from a screen the server sent no door on', () => {
    // The negative half of the rule, and the one that matters: a rated sport with an
    // empty city looks identical from here, and must not grow a door.
    const blocks = compose({
      ...emptyNow(),
      shelves: { stamp: 1, shelves: [shelf('newClubs', [])] },
    }).shelves.blocks;

    expect(blocks.map((block) => block.kind)).toEqual(['shelf']);
  });
});

describe('the one fact about the viewer', () => {
  it('carries the amount and the boolean, and never derives one from the other', () => {
    const screen = compose({
      ...emptyNow(),
      debt: { owed: { amount: 3000, currency: 'PLN' }, blocked: true },
    });

    expect(screen.debt).toEqual({ owed: { amount: 3000, currency: 'PLN' }, blocked: true });
  });

  it('keeps a debt the server says blocks nothing', () => {
    // Concluding *she owes, therefore create is dead* would be a rule, and the phone
    // holds none.
    const screen = compose({
      ...emptyNow(),
      debt: { owed: { amount: 3000, currency: 'PLN' }, blocked: false },
    });

    expect(screen.debt?.blocked).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// The fit badge
// ---------------------------------------------------------------------------

describe('the fit badge', () => {
  /** One shelf, one card, and the badge the server put on it. */
  function badgeOn(card: Wire['MatchCardResponse']) {
    const shelved = shelfAt(
      compose({ ...emptyNow(), shelves: { stamp: 1, shelves: [shelf('bestFit', [card])] } }).shelves
        .blocks,
      0,
    );
    const first = nth(shelved.cards, 0);
    if (first.kind !== 'match') throw new Error(`a ${first.kind} card carries no badge`);
    return first;
  }

  it('clamps the score at both ends, where the wire does not', () => {
    // The engine's measured range is 8 to 100 and the pill's is 20 to 99, so both
    // ends are reachable rather than defensive. The clamp is applied here so the
    // true score never enters the app at all.
    expect(badgeOn(matchCard({ matchId: 'm-1', fit: fit({ score: 8 }) })).fit?.score).toBe(20);
    expect(badgeOn(matchCard({ matchId: 'm-1', fit: fit({ score: 100 }) })).fit?.score).toBe(99);
    expect(badgeOn(matchCard({ matchId: 'm-1', fit: fit({ score: 74 }) })).fit?.score).toBe(74);
  });

  it('carries the warning as a boolean and no number beside it', () => {
    const badge = badgeOn(matchCard({ matchId: 'm-1', fit: fit({ score: 74, unsure: true }) })).fit;

    expect(badge?.unsure).toBe(true);
    // Coverage is never a number the player sees, so there is nowhere to put one.
    expect(Object.keys(badge ?? {}).sort()).toEqual(['reasons', 'score', 'unsure']);
  });

  it('resolves each reason to this app’s own sentence', () => {
    const badge = badgeOn(
      matchCard({
        matchId: 'm-1',
        fit: fit({
          score: 91,
          reasons: [
            fitReason('skill_overlap', {
              code: 'skill_overlap',
              level: 2.7,
              target: 2.9,
              band_half_width: 0.55,
              side: 'even',
            }),
            fitReason('travel', { code: 'travel', minutes: 14, radius: null }),
          ],
        }),
      }),
    ).fit;

    expect(badge?.reasons).toEqual([
      'Your level overlaps the level this match is aimed at.',
      'It is close to you.',
    ]);
  });

  it('takes at most three, so a fourth grows a card here rather than on a phone', () => {
    const one = fitReason('travel', { code: 'travel', minutes: 14, radius: null });
    const badge = badgeOn(
      matchCard({ matchId: 'm-1', fit: fit({ score: 91, reasons: [one, one, one, one] }) }),
    ).fit;

    expect(badge?.reasons).toHaveLength(3);
  });

  it('drops a term this build has never heard of rather than drawing it blank', () => {
    // The same answer an unknown situation gets: lose the thing that is missing, not
    // the card. A blank bullet is a defect where two reasons instead of three is not.
    const badge = badgeOn(
      matchCard({
        matchId: 'm-1',
        fit: fit({
          score: 91,
          reasons: [
            fitReason('coverage' as Wire['TermCode'], {
              code: 'travel',
              minutes: 14,
              radius: null,
            }),
            fitReason('travel', { code: 'travel', minutes: 14, radius: null }),
          ],
        }),
      }),
    ).fit;

    expect(badge?.reasons).toEqual(['It is close to you.']);
  });

  it('is absent on a card the server did not score', () => {
    // Every card in the strip, and every card on a screen that degraded. It is not
    // how an unrated viewer is answered — she gets a door where the shelves would be.
    expect(badgeOn(matchCard({ matchId: 'm-1' })).fit).toBeUndefined();
  });
});

describe('emphasis', () => {
  function cardsOf(cards: Wire['MatchCardResponse'][]) {
    const shelved = shelfAt(
      compose({ ...emptyNow(), shelves: { stamp: 1, shelves: [shelf('bestFit', cards)] } }).shelves
        .blocks,
      0,
    );
    return shelved.cards.map((card) => (card.kind === 'match' ? card.emphasis : 'not a match'));
  }

  it('is the wire’s flag, carried across untouched', () => {
    expect(
      cardsOf([
        matchCard({ matchId: 'm-1', fit: fit({ score: 94 }), emphasis: true }),
        matchCard({ matchId: 'm-2', fit: fit({ score: 93 }) }),
      ]),
    ).toEqual([true, false]);
  });

  it('is never concluded from the score', () => {
    // `ADR-0037`: 4,3 % of realistic scores reach 90 and a list selects for the
    // maximum, so a client comparing against 90 would light up the top of most
    // screens. Two cards clear it here and neither is flagged.
    expect(
      cardsOf([
        matchCard({ matchId: 'm-1', fit: fit({ score: 99 }) }),
        matchCard({ matchId: 'm-2', fit: fit({ score: 95 }) }),
      ]),
    ).toEqual([false, false]);
  });

  it('is false on a card with no badge at all', () => {
    expect(cardsOf([matchCard({ matchId: 'm-1' })])).toEqual([false]);
  });
});

describe('an action’s update', () => {
  it('maps the changed card through the same expression a compose does', () => {
    // A card arriving from an action and the same card arriving from a compose
    // cannot be rendered by two different expressions, or one screen says two
    // things about one match. Asserted as *the same card*, against a compose of
    // the identical wire object, rather than against a copy of the expected
    // rendering — which would agree with itself.
    const wire = matchCard({ matchId: 'm-1', situation: 'confirmed' });
    const update = toNowUpdate({ update_type: 'card', card: wire });
    const composed = nth(
      compose({ ...emptyNow(), your_matches: { stamp: 1, cards: [wire] } }).yourMatches.cards,
      0,
    );

    if (update.kind !== 'card') throw new Error('the card form was asked for');
    expect(update.card).toEqual(composed);
  });

  it('maps the gone form to the match it names and no card', () => {
    // `ADR-0087`'s form, and the reason the union exists: there is no card to
    // map, and an emptied one would be a blank the renderer has to interpret.
    const update = toNowUpdate({ update_type: 'gone', match_id: 'm-1' });

    expect(update).toEqual({ kind: 'gone', matchId: 'm-1' });
  });
});

describe('what taking a seat answered', () => {
  /**
   * A card carrying **every** spine field the write can move.
   *
   * A refusal's whole answer is this one card, so a mapper that mangled a field on
   * the way through would be the corrected card being wrong — and a fixture with
   * `act: null` and no claim cannot see it, because dropping either is then the
   * identity. It is the same trap the fit-badge suite hit with `unsure`.
   */
  const card = matchCard({
    matchId: 'm-1',
    situation: 'confirmed',
    clock: '2026-08-24T18:00:00Z',
    act: 'takeSeat',
    mayDepart: true,
  });

  it('reads what the tap did off the wire and never off the card', () => {
    // `claimed` is the server's statement about the **command**, and the client's
    // one self-written sentence hangs off it. The two cases below carry the
    // *identical* card — one with a seat claim on it, one without — so a mapper
    // deriving *was I refused* from the card would answer the same for both.
    const claim = matchCard({
      matchId: 'm-1',
      situation: 'confirmed',
      seatClaimExpiresAt: '2026-08-24T18:05:00Z',
    });

    expect(toSeatAnswer(seatWrite({ claimed: false, update: claim })).claimed).toBe(false);
    expect(toSeatAnswer(seatWrite({ claimed: true, update: card })).claimed).toBe(true);
  });

  it('maps the card through the same expression a compose does', () => {
    const answer = toSeatAnswer(seatWrite({ claimed: false, update: card }));
    const composed = nth(
      compose({ ...emptyNow(), your_matches: { stamp: 1, cards: [card] } }).yourMatches.cards,
      0,
    );

    if (answer.update.kind !== 'card') throw new Error('the card form was asked for');
    expect(answer.update.card).toEqual(composed);
  });

  it('carries both regions when the tap applied, mapped like any other card', () => {
    const answer = toSeatAnswer(
      seatWrite({ claimed: true, update: card, offers: [], yourMatches: [card] }),
    );
    const composed = nth(
      compose({ ...emptyNow(), your_matches: { stamp: 1, cards: [card] } }).yourMatches.cards,
      0,
    );

    expect(answer.regions?.offers.cards).toEqual([]);
    expect(answer.regions?.yourMatches.cards).toEqual([composed]);
  });

  it('carries no regions at all on a refusal', () => {
    // A tap that did not apply moved nothing, so the screen keeps the regions it
    // has and the corrected card is put back where it already sat.
    expect(toSeatAnswer(seatWrite({ claimed: false, update: card })).regions).toBeUndefined();
  });

  it('treats half an answer as none', () => {
    // The server sends both or neither. Half of one is not a region to write: the
    // direction this may fail in is a card in the wrong region, never a region
    // that has gone blank under her thumb.
    const half = { ...seatWrite({ claimed: true, update: card, offers: [] }), your_matches: null };

    expect(toSeatAnswer(half).regions).toBeUndefined();
    // And the other half missing answers the same way, so neither field is the
    // one that decides it.
    expect(
      toSeatAnswer({ ...seatWrite({ claimed: true, update: card, yourMatches: [] }), offers: null })
        .regions,
    ).toBeUndefined();
  });
});
