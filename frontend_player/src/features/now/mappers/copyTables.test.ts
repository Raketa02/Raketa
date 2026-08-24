/**
 * What the typecheck cannot say about the four copy tables.
 *
 * `ADR-0075` makes **completeness** a typecheck: a `Record` over the union
 * `openapi-typescript` emits fails to compile the moment the contract grows a
 * member without its sentence. Three things that mechanism cannot see are
 * asserted here instead.
 *
 * - **A count is a decision.** The `Record` forces a thirty-seventh row to be
 *   written; it cannot force anybody to notice that a thirty-seventh situation
 *   now exists. The lists below are the backend's own enumerations copied out,
 *   so growth stops here and somebody chooses.
 * - **A sentence is not a blank.** A row satisfying the `Record` with `''` type-
 *   checks perfectly and ships the exact defect the table exists to prevent.
 * - **The fallback path.** Every lookup is typed to take a `string`, because an
 *   installed phone meeting a thirty-seventh name is the one case a typecheck
 *   never reaches. Typing it as the union would make that branch unreachable.
 */

import {
  ACT_COPY,
  CAPTION_COPY,
  DOOR_COPY,
  FIT_BADGE_WITHHELD,
  FIT_REASON_COPY,
  FIT_UNSURE_WARNING,
  HOLD_REASON_COPY,
  SHELF_COPY,
  SITUATION_COPY,
  actCopy,
  captionCopy,
  doorCopy,
  findPreFilter,
  fitReasonSentence,
  holdReasonClause,
  shelfTitle,
  situationCopy,
} from '../types';
import type { FitReason, SituationContext, Tag, Tone } from '../types';

/**
 * A reason as it now crosses: a code **and** its typed fact payload.
 *
 * `Raketa02/Raketa#75` put the quantities beside the code, so the table's
 * entries take the whole reason rather than the code alone — which is the shape
 * they were already written in. Drawing them is `#88`'s; what this file needs is
 * a payload that satisfies the contract, and the travel term's is the smallest
 * one there is.
 */
const aReason = (code: string): FitReason =>
  ({ code, fact: { code: 'travel', minutes: 20, radius: null } }) as FitReason;

import type { ActCode, AssertTrue, CaptionCode, CardHoldReason, IsClosedUnion } from './codes';
import type { DoorCode, ShelfCode, Situation, SituationFacts, TermCode } from './codes';

/**
 * The five guards a `Record` cannot carry, in the one place they are read
 * together: each fails `pnpm typecheck` if its key stops being a closed union
 * and becomes a bare `string`, at which point every `Record` below silently
 * degrades into an index signature that never fires.
 */
export type SituationKeyIsClosed = AssertTrue<IsClosedUnion<Situation>>;
export type TermCodeKeyIsClosed = AssertTrue<IsClosedUnion<TermCode>>;
export type HoldReasonKeyIsClosed = AssertTrue<IsClosedUnion<CardHoldReason>>;
export type ActKeyIsClosed = AssertTrue<IsClosedUnion<ActCode>>;
export type ShelfKeyIsClosed = AssertTrue<IsClosedUnion<ShelfCode>>;
export type CaptionKeyIsClosed = AssertTrue<IsClosedUnion<CaptionCode>>;
export type DoorKeyIsClosed = AssertTrue<IsClosedUnion<DoorCode>>;

/** The kernel's ladder, in ladder order. Growth is a decision, not a diff. */
const SITUATIONS: readonly Situation[] = [
  'inventoryLost',
  'cancelledClub',
  'cancelledIncomplete',
  'cancelledCheckpoint',
  'playedNoShow',
  'playedShort',
  'completed',
  'playedNoScore',
  'confirmResult',
  'needsResult',
  'seatOffered',
  'seatOpened',
  'waitlisted',
  'privateOpen',
  'privateFull',
  'privatePartial',
  'privateReserved',
  'replacementTransfer',
  'rescueLate',
  'rescue',
  'replacement',
  'protectedBack',
  'formingBack',
  'ready',
  'confirmedOnFill',
  'confirmed',
  'full',
  'formingLateHeld',
  'clubHeld',
  'heldSoft',
  'heldReleased',
  'formingHeld',
  'formingLate',
  'forming',
  'heldStale',
  'heldExtended',
];

const TERM_CODES: readonly TermCode[] = [
  'skill_overlap',
  'predicted_balance',
  'time_fit',
  'match_viability',
  'group_reliability',
  'travel',
  'ladder_qualification',
  'price',
  'match_type',
  'familiarity',
];

const HOLD_REASONS: readonly CardHoldReason[] = ['committed', 'far', 'near', 'stale', 'extended'];

const ACTS: readonly ActCode[] = [
  'takeSeat',
  'finishPaying',
  'enterResult',
  'answerResult',
  'seeAlternatives',
  'gettingIn',
  'leaveStandby',
];

const SHELVES: readonly ShelfCode[] = [
  'bestFit',
  'sameLevel',
  'fullWorthWaiting',
  'recentlyViewed',
  'newPlayers',
  'newClubs',
];

const TONES: readonly Tone[] = ['good', 'watch', 'time', 'ended', 'idle'];

const TAGS: readonly Tag[] = [
  'Forming',
  'Court held',
  'Court released',
  'Court committed',
  'Court protected',
  'Full',
  'Confirmed',
  'Replacement pending',
  'Rescue active',
  'Ready to play',
  'Needs result',
  'Confirm the result',
  'Completed',
  'Played',
  'On standby',
  'Reserved',
  'Cancelled',
  'Seat offered',
  'Seat open',
];

/**
 * The two facts every card carries, so an override only says what it is about.
 *
 * `counts` and `court_total` are required on the wire — counting is by money
 * and every card counts — and a fixture that could leave them out would be
 * exercising a payload the server cannot compose.
 */
const FACTS: SituationFacts = {
  counts: { seats: 4, paid: 2, held: 0, turned_up: null },
  court_total: { amount: 15200, currency: 'PLN' },
  hold: null,
  cause: null,
};

const context = (over: Partial<SituationContext> = {}): SituationContext => ({
  facts: FACTS,
  clubName: 'Kortowo',
  price: '38,00 zł',
  ...over,
});

describe('the four copy tables are complete and pinned', () => {
  it.each([
    ['situations', SITUATION_COPY, SITUATIONS, 36],
    ['fit reasons', FIT_REASON_COPY, TERM_CODES, 10],
    ['hold reasons', HOLD_REASON_COPY, HOLD_REASONS, 5],
    ['acts', ACT_COPY, ACTS, 7],
    ['shelves', SHELF_COPY, SHELVES, 6],
  ] as const)('%s hold exactly the codes the contract names', (_name, table, codes, count) => {
    expect(codes).toHaveLength(count);
    expect(Object.keys(table).sort()).toEqual([...codes].sort());
  });

  it('holds exactly the two door codes, so a third is a decision', () => {
    const codes: readonly DoorCode[] = ['noRunYet', 'runParked'];

    expect(codes).toHaveLength(2);
    expect(Object.keys(DOOR_COPY).sort()).toEqual([...codes].sort());
  });

  it('words both doors for the chip, and offers a way in on each', () => {
    for (const code of ['noRunYet', 'runParked'] as const) {
      const copy = DOOR_COPY[code]({ sport: 'SQUASH' });

      expect(copy.line).toContain('Squash');
      expect(copy.action.trim().length).toBeGreaterThan(0);
    }
  });

  it('takes no noun from the one chip that is not a sport', () => {
    // `all` never produces a door — the server composes one only for a named chip —
    // so this is a word chosen for a sentence rather than a rule about when a door
    // appears. What it must never print is *"Take the All questions"*.
    expect(DOOR_COPY.noRunYet({ sport: 'all' }).action).not.toContain('All');
  });

  it('holds the one caption v1 composes', () => {
    const codes: readonly CaptionCode[] = ['undeclaredPreferences'];
    expect(Object.keys(CAPTION_COPY).sort()).toEqual([...codes].sort());
  });

  it('keeps a row for the shelf that ships dark, so its return is a server change', () => {
    // ADR-0085 reserves `recentlyViewed` on the wire and never composes it. The
    // reservation is only worth anything if the client already holds the row.
    expect(SHELF_COPY.recentlyViewed.title).not.toHaveLength(0);
  });
});

describe('every situation says something', () => {
  it.each(SITUATIONS)('%s renders a line, a known tag and a known tone', (situation) => {
    const copy = SITUATION_COPY[situation](context());

    expect(copy.line.trim().length).toBeGreaterThan(0);
    expect(TAGS).toContain(copy.tag);
    expect(TONES).toContain(copy.tone);
  });

  it('alerts on exactly the three that leave a player short inside the rescue window', () => {
    // ADR-0072: it stops only when a seat is actually being taken, which is why
    // `replacementTransfer` carries none though it wears the same tag.
    const alerting = SITUATIONS.filter((s) => SITUATION_COPY[s](context()).alert !== null);

    expect(alerting.sort()).toEqual(['replacement', 'rescue', 'rescueLate']);
  });

  it('says a payment will not change on every alert', () => {
    for (const situation of ['replacement', 'rescue', 'rescueLate'] as const) {
      expect(SITUATION_COPY[situation](context()).alert).toContain('Your payment will not change.');
    }
  });

  it('gives the lost court an ended tone rather than the prototype colourless dot', () => {
    // The prototype declared `bad`, its own tone map had no such key, and the
    // dot rendered with no colour at all. UI §G decides the retone.
    expect(SITUATION_COPY.inventoryLost(context()).tone).toBe('ended');
  });

  it('never claims a seat is reserved, under either of its two names', () => {
    // `ADR-0061` retired the exclusive offer **and its wording** together — the
    // one-hour hold, the cap of three, and *"a seat is being offered to you"* all
    // existed to make one-at-a-time safe, and none of them ships. So both offer
    // situations speak in the open-call voice, and the hard constraint — *a seat
    // that is gone must never be presented as an exceptional card* — is kept by
    // that wording rather than by a retraction nobody can send.
    const race = 'A seat just opened — first to take it.';

    expect(SITUATION_COPY.seatOpened(context()).line).toBe(race);
    expect(SITUATION_COPY.seatOffered(context()).line).toBe(race);
  });

  it('tells the two offer names apart by the tag, which is all that is left', () => {
    // The lines are now identical on purpose, so the **tag** is the only thing
    // carrying the difference between an open call and the exclusive offer the
    // kernel keeps a name for. A table where both halves agree is a table where one
    // of the two names means nothing.
    const offered = SITUATION_COPY.seatOffered(context());
    const opened = SITUATION_COPY.seatOpened(context());

    expect(offered.tag).not.toBe(opened.tag);
    expect(offered.line).toBe(opened.line);
    expect(offered.tone).toBe(opened.tone);
  });

  it('says nothing anywhere about a seat being held for somebody', () => {
    // The negative control the rewrite above needs: a table with one such
    // sentence in it is a table that can grow a second. Every line on this screen
    // is checked, because the claim is about the vocabulary and not about two rows.
    const reserving = /reserved for you|held for you|nobody else can|for the hour/i;

    for (const situation of SITUATIONS) {
      expect(SITUATION_COPY[situation](context()).line).not.toMatch(reserving);
    }

    expect(reserving.test('nobody else can take it for the hour')).toBe(true);
    expect(reserving.test('A seat just opened — first to take it.')).toBe(false);
  });

  it('reads the club and the price off the spine rather than restating them', () => {
    const copy = SITUATION_COPY.cancelledClub(context({ clubName: 'Hala Wisła' }));
    expect(copy.line).toContain('Hala Wisła');

    expect(SITUATION_COPY.confirmed(context({ price: '120,00 zł' })).line).toContain('120,00 zł');
  });

  it('composes the hold reason into the sentence rather than printing free text', () => {
    const near = SITUATION_COPY.heldSoft(
      context({ facts: { ...FACTS, hold: { reason: 'near' } } }),
    );
    const far = SITUATION_COPY.heldSoft(context({ facts: { ...FACTS, hold: { reason: 'far' } } }));

    expect(near.line).toContain('one seat short');
    expect(far.line).toContain('twelve hours');
    expect(near.line).not.toEqual(far.line);
  });

  it('still says the court is held when the hold reason is one it cannot name', () => {
    const unknown = SITUATION_COPY.heldSoft(
      context({ facts: { ...FACTS, hold: { reason: 'invented' as CardHoldReason } } }),
    );

    expect(unknown.line).toBe('Held for this match.');
    expect(unknown.tag).toBe('Court held');
  });
});

describe('a name this build has never heard of costs one sentence and nothing else', () => {
  it('returns nothing for an unknown situation', () => {
    expect(situationCopy('somethingTheLadderGrewLater', context())).toBeUndefined();
    expect(situationCopy('forming', context())?.tag).toBe('Forming');
  });

  it('returns nothing for an unknown act, so no button opens somewhere unresolvable', () => {
    expect(actCopy('transferSeat', { price: '38,00 zł' })).toBeUndefined();
    expect(actCopy('gettingIn', { price: '38,00 zł' })?.surface).toBe('gettingIn');
  });

  it('returns nothing for an unknown door code, so no blank ask is drawn', () => {
    expect(doorCopy('reRate', { sport: 'SQUASH' })).toBeUndefined();
    expect(doorCopy('runParked', { sport: 'SQUASH' })?.action).toBe('Pick up where you left off');
  });

  it('returns nothing for an unknown term, shelf, caption or hold reason', () => {
    expect(fitReasonSentence(aReason('coverage'))).toBeUndefined();
    expect(shelfTitle('somethingNew')).toBeUndefined();
    expect(findPreFilter('somethingNew', 'all')).toBeUndefined();
    expect(captionCopy('somethingNew')).toBeUndefined();
    expect(holdReasonClause(undefined)).toBeUndefined();
    expect(holdReasonClause(null)).toBeUndefined();
  });
});

describe('acts, shelves, fit reasons and captions', () => {
  it('puts the amount on the two acts that ask for money', () => {
    expect(ACT_COPY.takeSeat({ price: '38,00 zł' }).label).toBe('Take the seat · 38,00 zł');
    expect(ACT_COPY.finishPaying({ price: '38,00 zł' }).label).toContain('38,00 zł');
  });

  it('sends both result acts to the same surface and neither to a second one', () => {
    expect(ACT_COPY.enterResult({ price: '' }).surface).toBe('result');
    expect(ACT_COPY.answerResult({ price: '' }).surface).toBe('result');
  });

  it('resolves leaving standby to a write and not to a route', () => {
    // ADR-0087: one tap, no confirmation. A route would be a screen asking her
    // to confirm giving up a free-to-rejoin queue place.
    expect(ACT_COPY.leaveStandby({ price: '' }).surface).toBe('standbyWrite');
  });

  it('carries the sport into the pre-filter, since the shelf does not know it', () => {
    expect(findPreFilter('newClubs', 'SQUASH')).toEqual({
      seats: 'any',
      order: 'newest',
      kind: 'clubs',
      sport: 'SQUASH',
    });
  });

  it('retitles shelf one without changing what it is a door into', () => {
    expect(SHELF_COPY.bestFit.title).not.toBe(SHELF_COPY.sameLevel.title);
    expect(SHELF_COPY.sameLevel.claim.seats).toBe('open');
    expect(SHELF_COPY.fullWorthWaiting.claim.seats).toBe('full');
  });

  it.each(TERM_CODES)('%s reads as a reason a player could act on', (code) => {
    expect(fitReasonSentence(aReason(code))?.trim().length).toBeGreaterThan(0);
  });

  it('warns rather than printing a number when the estimate is unsure', () => {
    expect(FIT_UNSURE_WARNING).not.toMatch(/\d/);
    expect(FIT_BADGE_WITHHELD).not.toMatch(/\d/);
  });

  it('never puts a percentage on the caption', () => {
    expect(CAPTION_COPY.undeclaredPreferences).not.toMatch(/%|\d/);
  });
});
