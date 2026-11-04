/**
 * The rules a dealt card is drawn by — which row is on top, what the ribbon and the court block
 * say, when a yes says Pay, how long the card has, and what an answer does to the deck.
 */

import {
  chargesAtOnce,
  completesIt,
  countdownOf,
  courtTagOf,
  foldOf,
  inAcrossVersions,
  refusalOutcome,
  rescueGoneOf,
  resolveKind,
  ribbonOf,
  rowsOf,
  standingCards,
  weekCapOf,
  withOnTop,
  withoutCard,
  type DeckCard,
  type DeckPerson,
  type DeckRow,
  type GroupDeck,
} from './deck';

const HOUR = 3_600_000;
const READ_AT = Date.parse('2026-09-30T10:00:00Z');

function person(name: string, extra: Partial<DeckPerson> = {}): DeckPerson {
  return { playerId: `id-${name}`, isYou: false, name, level: 2.7, isIn: false, ...extra };
}

const YOU = person('You', { isYou: true });

function card(extra: Partial<DeckCard> = {}): DeckCard {
  return {
    proposalId: 'p-1',
    type: 'PICKED_FOR_YOU',
    kind: 'competitive',
    startsAt: '2026-10-03T14:00:00Z',
    club: { id: 'club-1', name: 'Ogrody 33' },
    shareGrosze: 2700,
    deadline: '2026-10-02T14:00:00Z',
    inCount: 0,
    versionCount: 1,
    openSeatsAfterYourYes: 3,
    court: 'COURT_AVAILABLE',
    noFreeCancellation: false,
    sides: { yours: [YOU, person('Zofia')], theirs: [person('Ania'), person('Ewa')] },
    forecast: { pct: 87, provisional: false },
    overlap: { grade: 'GOOD', cells: [], game: { day: 6, range: 'AFTERNOON' } },
    ...extra,
  };
}

/** A row as names, `·` for an empty seat — the shape the mocks are read in. */
const names = (row: DeckRow) =>
  row.seats.map((seat) => (seat.kind === 'empty' ? '·' : (seat.person.name ?? '?')));

describe('which segment the deck is read for', () => {
  it('is the one chosen, while the intent shows it', () => {
    expect(
      resolveKind('forFun', [
        { kind: 'competitive', count: 5 },
        { kind: 'forFun', count: 1 },
      ]),
    ).toBe('forFun');
  });

  it('is the only segment the intent shows, whatever was chosen', () => {
    expect(resolveKind('competitive', [{ kind: 'forFun', count: 2 }])).toBe('forFun');
  });

  it('stands as chosen while there is nothing to correct it against', () => {
    expect(resolveKind('forFun', undefined)).toBe('forFun');
    expect(resolveKind('forFun', [])).toBe('forFun');
  });
});

describe('the rows', () => {
  it('draws your side on top while nobody is In (mock 6)', () => {
    const { top, bottom } = rowsOf(card(), 2);

    expect(top.yours).toBe(true);
    expect(names(top)).toEqual(['You', 'Zofia']);
    expect(names(bottom)).toEqual(['Ania', 'Ewa']);
  });

  it('draws the side with more people In on top (mocks 3, 4, 7)', () => {
    const { top, bottom } = rowsOf(
      card({
        sides: {
          yours: [YOU, person('Ania', { isIn: true })],
          theirs: [person('Karol', { isIn: true }), person('Zofia', { isIn: true })],
        },
      }),
      2,
    );

    expect(top.yours).toBe(false);
    expect(names(top)).toEqual(['Karol', 'Zofia']);
    // In before you, in a row: *Ania + You*.
    expect(names(bottom)).toEqual(['Ania', 'You']);
  });

  it('keeps your side on top when it has the momentum (mock 5)', () => {
    const { top } = rowsOf(
      card({ sides: { yours: [YOU, person('Karol', { isIn: true })], theirs: [person('Ewa')] } }),
      2,
    );

    expect(top.yours).toBe(true);
    expect(names(top)).toEqual(['Karol', 'You']);
  });

  it('puts you before a partner who has not answered (mock 4)', () => {
    const { bottom } = rowsOf(
      card({
        sides: {
          yours: [person('Ewa'), YOU],
          theirs: [person('Kuba', { isIn: true }), person('Ania', { isIn: true })],
        },
      }),
      2,
    );

    expect(names(bottom)).toEqual(['You', 'Ewa']);
  });

  it('draws the seat a short side leaves as empty, after the people', () => {
    const { top, bottom } = rowsOf(card({ sides: { yours: [YOU], theirs: [person('Ania')] } }), 2);

    expect(names(top)).toEqual(['You', '·']);
    expect(names(bottom)).toEqual(['Ania', '·']);
  });

  it('draws singles one to a side', () => {
    const { top, bottom } = rowsOf(card({ sides: { yours: [YOU], theirs: [person('Kuba')] } }), 1);

    expect(names(top)).toEqual(['You']);
    expect(names(bottom)).toEqual(['Kuba']);
  });
});

describe('the ribbon', () => {
  it('says a pick, a challenge by name, the group’s challenge and a rescue', () => {
    expect(ribbonOf(card())).toEqual({ kind: 'pickedForYou' });
    expect(
      ribbonOf(card({ type: 'CHALLENGE', challenger: { playerId: 'k', name: 'kuba.w' } })),
    ).toEqual({ kind: 'challenge', by: 'kuba.w' });
    expect(ribbonOf(card({ type: 'CHALLENGE' }))).toEqual({ kind: 'challenge' });
    expect(ribbonOf(card({ type: 'CHALLENGE', challenger: { playerId: 'k' } }))).toEqual({
      kind: 'challenge',
    });
    expect(ribbonOf(card({ type: 'SEAT_OPEN' }))).toEqual({ kind: 'seatOpen' });
  });
});

describe('the court block and the stamp', () => {
  it('tags a free vote, a yes that fills, and a rescue', () => {
    expect(courtTagOf(card())).toBe('available');
    expect(courtTagOf(card({ court: 'BOOK_IT_NOW' }))).toBe('bookItNow');
    expect(courtTagOf(card({ type: 'SEAT_OPEN', court: 'BOOKED' }))).toBe('booked');
  });

  it('charges at once — and so says Pay — on Book it now and a rescue, never on a vote (Q124)', () => {
    expect(chargesAtOnce(card())).toBe(false);
    expect(chargesAtOnce(card({ court: 'BOOK_IT_NOW' }))).toBe(true);
    expect(chargesAtOnce(card({ type: 'SEAT_OPEN', court: 'BOOKED' }))).toBe(true);
  });

  it('says you complete it when your yes leaves no seat open, and not once it is given', () => {
    expect(completesIt(card({ openSeatsAfterYourYes: 0 }))).toBe(true);
    expect(completesIt(card({ openSeatsAfterYourYes: 1 }))).toBe(false);
    const youIn = card({
      openSeatsAfterYourYes: 0,
      sides: { yours: [{ ...YOU, isIn: true }], theirs: [] },
    });
    expect(completesIt(youIn)).toBe(false);
  });

  it('counts the whole game’s yeses only on a game dealt in versions', () => {
    expect(inAcrossVersions(card({ versionCount: 1, inCount: 2 }))).toBeUndefined();
    expect(inAcrossVersions(card({ versionCount: 3, inCount: 4 }))).toBe(4);
  });
});

describe('the countdown', () => {
  const at = (hoursLeft: number) => new Date(READ_AT + hoursLeft * HOUR).toISOString();

  it('draws nothing a day or more away', () => {
    expect(countdownOf(at(24), READ_AT)).toEqual({ kind: 'far' });
    expect(countdownOf(at(48), READ_AT)).toEqual({ kind: 'far' });
  });

  it('counts hours and minutes under a day, floored', () => {
    expect(countdownOf(at(21), READ_AT)).toEqual({ kind: 'hours', hours: 21, minutes: 0 });
    expect(countdownOf(at(23 + 59.9 / 60), READ_AT)).toEqual({
      kind: 'hours',
      hours: 23,
      minutes: 59,
    });
  });

  it('counts minutes under an hour', () => {
    expect(countdownOf(at(0.75), READ_AT)).toEqual({ kind: 'minutes', minutes: 45 });
  });

  it('is over at the deadline, and the card leaves', () => {
    expect(countdownOf(at(0), READ_AT)).toEqual({ kind: 'over' });
    expect(
      standingCards(
        [
          card({ proposalId: 'gone', deadline: at(-1) }),
          card({ proposalId: 'on', deadline: at(2) }),
        ],
        READ_AT,
      ).map((dealt) => dealt.proposalId),
    ).toEqual(['on']);
  });
});

describe('the forecast’s fold', () => {
  it('is your side’s mean Level minus theirs', () => {
    const fold = foldOf(
      card({
        sides: {
          yours: [person('You', { isYou: true, level: 3.1 }), person('Zofia', { level: 2.5 })],
          theirs: [person('Ania', { level: 2.6 }), person('Ewa', { level: 2.6 })],
        },
      }),
    );
    expect(fold).toBeCloseTo(0.2);
  });

  it('reads a short side as its present member', () => {
    expect(
      foldOf(
        card({
          sides: {
            yours: [person('You', { isYou: true, level: 3 })],
            theirs: [person('Ania', { level: 2.5 }), person('Ewa', { level: 2.5 })],
          },
        }),
      ),
    ).toBeCloseTo(0.5);
  });

  it('is nothing where somebody is unrated or a side is empty', () => {
    expect(
      foldOf(card({ sides: { yours: [YOU], theirs: [person('Ania', { level: undefined })] } })),
    ).toBeUndefined();
    expect(foldOf(card({ sides: { yours: [YOU], theirs: [] } }))).toBeUndefined();
  });
});

describe('the weekly cap', () => {
  const THIS = '2026-09-28';
  const NEXT = '2026-10-05';

  it('says which of the deck’s two weeks are full', () => {
    expect(weekCapOf([], THIS, NEXT)).toBeUndefined();
    expect(weekCapOf([{ startsOn: THIS, booked: 2 }], THIS, NEXT)).toEqual({
      weeks: 'this',
      booked: 2,
    });
    expect(weekCapOf([{ startsOn: NEXT, booked: 3 }], THIS, NEXT)).toEqual({
      weeks: 'next',
      booked: 3,
    });
    expect(
      weekCapOf(
        [
          { startsOn: THIS, booked: 2 },
          { startsOn: NEXT, booked: 2 },
        ],
        THIS,
        NEXT,
      ),
    ).toEqual({ weeks: 'both', booked: 2 });
  });

  it('says nothing of a week outside the fortnight', () => {
    expect(weekCapOf([{ startsOn: '2026-10-12', booked: 2 }], THIS, NEXT)).toBeUndefined();
  });
});

describe('answering', () => {
  const deck: GroupDeck = {
    segments: [
      { kind: 'competitive', count: 2 },
      { kind: 'forFun', count: 1 },
    ],
    gamesBadge: 1,
    gamesPerWeek: 2,
    cappedWeeks: [],
    cards: [card({ proposalId: 'a', inCount: 1 }), card({ proposalId: 'b' })],
  };

  it('drops an answered card, with its segment’s count and the badge following it', () => {
    const after = withoutCard(deck, 'a');

    expect(after.cards.map((dealt) => dealt.proposalId)).toEqual(['b']);
    expect(after.segments).toEqual([
      { kind: 'competitive', count: 1 },
      { kind: 'forFun', count: 1 },
    ]);
    expect(after.gamesBadge).toBe(0);
  });

  it('leaves the badge where nobody else was In', () => {
    expect(withoutCard(deck, 'b').gamesBadge).toBe(1);
  });

  it('changes nothing for a card that is not on the deck', () => {
    expect(withoutCard(deck, 'z')).toBe(deck);
  });

  it('returns the card on a refusal whose reason can go, and lets it go with the game', () => {
    expect(refusalOutcome('payment_method_required')).toBe('returns');
    expect(refusalOutcome('block_state_unavailable')).toBe('returns');
    expect(refusalOutcome(undefined)).toBe('returns');
    expect(refusalOutcome('something_new')).toBe('returns');
    expect(refusalOutcome('proposal_is_over')).toBe('gone');
    expect(refusalOutcome('proposal_is_full')).toBe('gone');
    expect(refusalOutcome('proposal_already_answered')).toBe('gone');
    expect(refusalOutcome('no_longer_fits')).toBe('gone');
    expect(refusalOutcome('proposal_not_found')).toBe('gone');
  });

  it('lets a rescue go once its seat is taken, off, started or not offered (#545)', () => {
    for (const code of [
      'seat_just_taken',
      'booking_is_called_off',
      'game_has_started',
      'rescue_not_offered',
      'booking_not_found',
    ]) {
      expect(refusalOutcome(code)).toBe('gone');
    }
    expect(refusalOutcome('payment_to_confirm')).toBe('returns');
  });
});

describe('the card a notice opened the deck for (#559; the screens A9)', () => {
  const first = card({ proposalId: 'p-1' });
  const second = card({ proposalId: 'p-2' });
  const third = card({ proposalId: 'p-3' });

  it('is drawn on top, and the rest keep the order they were dealt in', () => {
    expect(withOnTop([first, second, third], 'p-3').map((one) => one.proposalId)).toEqual([
      'p-3',
      'p-1',
      'p-2',
    ]);
  });

  it('changes nothing once it is no longer dealt — answered, filled, or gone', () => {
    expect(withOnTop([first, second], 'p-9')).toEqual([first, second]);
  });

  it('changes nothing when no notice opened the deck', () => {
    expect(withOnTop([first, second], undefined)).toEqual([first, second]);
  });
});

describe('why a rescue went, as the join says it (the bug report’s P1 on the rescue swipe)', () => {
  it('names each refusal the sheet says, and leaves the rest to the toast', () => {
    expect(rescueGoneOf('seat_just_taken')).toEqual({ reason: 'SEAT_TAKEN' });
    expect(rescueGoneOf('booking_not_found')).toEqual({ reason: 'BOOKING_GONE' });
    expect(rescueGoneOf('game_has_started')).toEqual({ reason: 'GAME_STARTED' });
    expect(rescueGoneOf('rescue_not_offered')).toEqual({ reason: 'NOT_OFFERED' });
    expect(rescueGoneOf('payment_to_confirm')).toBeUndefined();
    expect(rescueGoneOf(undefined)).toBeUndefined();
  });

  it('tells the club’s cancel, with its reason, from a game short at the cut-off', () => {
    expect(
      rescueGoneOf('booking_is_called_off', {
        reason: 'CANCELLED_BY_THE_CLUB',
        club_cancel_reason: 'REPAIR',
      }),
    ).toEqual({ reason: 'CANCELLED_BY_THE_CLUB', clubCancelReason: 'REPAIR' });
    expect(rescueGoneOf('booking_is_called_off', { reason: 'SHORT_AT_THE_CUT_OFF' })).toEqual({
      reason: 'SHORT_AT_THE_CUT_OFF',
    });
  });

  it('reads the details and never trusts them: what this build cannot name is plain *called off*', () => {
    expect(rescueGoneOf('booking_is_called_off')).toEqual({ reason: 'CALLED_OFF' });
    expect(rescueGoneOf('booking_is_called_off', { reason: 'SOMETHING_NEW' })).toEqual({
      reason: 'CALLED_OFF',
    });
    expect(rescueGoneOf('booking_is_called_off', { reason: 3 })).toEqual({ reason: 'CALLED_OFF' });
    // A club's reason it cannot name is no reason, and a reason never rides on a cut-off.
    expect(
      rescueGoneOf('booking_is_called_off', {
        reason: 'CANCELLED_BY_THE_CLUB',
        club_cancel_reason: 'HAIL',
      }),
    ).toEqual({ reason: 'CANCELLED_BY_THE_CLUB' });
    expect(
      rescueGoneOf('booking_is_called_off', {
        reason: 'SHORT_AT_THE_CUT_OFF',
        club_cancel_reason: 'WEATHER',
      }),
    ).toEqual({ reason: 'SHORT_AT_THE_CUT_OFF' });
  });
});
