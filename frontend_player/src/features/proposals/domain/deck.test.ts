/**
 * The rules a dealt card is drawn by — which row is on top, what the ribbon and the court block
 * say, when a yes says Pay, how long the card has, and what an answer does to the deck.
 */

import {
  chargesAtOnce,
  completesIt,
  countdownOf,
  courtTagOf,
  doorPanel,
  drawnTheSame,
  findingAfterTheDoor,
  findingAfterTheQuestion,
  foldOf,
  headlineOf,
  intentAnswering,
  inAcrossVersions,
  kindMenu,
  refusalOutcome,
  rescueGoneOf,
  resolveKind,
  ribbonOf,
  rowsOf,
  standingCards,
  switchSides,
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

describe('the switch’s two sides (ADR-0201 §2)', () => {
  it('draws the kind a one-kind intent does not show as a door, with no count', () => {
    expect(switchSides([{ kind: 'competitive', count: 7 }])).toEqual([
      { kind: 'competitive', door: false, count: 7 },
      { kind: 'forFun', door: true },
    ]);
    expect(switchSides([{ kind: 'forFun', count: 3 }])).toEqual([
      { kind: 'competitive', door: true },
      { kind: 'forFun', door: false, count: 3 },
    ]);
  });

  it('draws both live for Either suits me, Competitive first', () => {
    expect(
      switchSides([
        { kind: 'forFun', count: 1 },
        { kind: 'competitive', count: 5 },
      ]),
    ).toEqual([
      { kind: 'competitive', door: false, count: 5 },
      { kind: 'forFun', door: false, count: 1 },
    ]);
  });

  it('draws no switch while no intent is declared', () => {
    expect(switchSides([])).toEqual([]);
  });
});

describe('the Games tab’s menu, off the reads already held (#862)', () => {
  const ANIA = [{ kind: 'competitive', count: 7 }] as const;
  const ZOFIA = [
    { kind: 'competitive', count: 5 },
    { kind: 'forFun', count: 1 },
  ] as const;

  it('is drawn off the read of the kind chosen: both kinds, the deck’s kind ticked', () => {
    expect(kindMenu('competitive', ZOFIA, undefined)).toEqual({
      kind: 'competitive',
      ticked: 'competitive',
      sides: [
        { kind: 'competitive', door: false, count: 5 },
        { kind: 'forFun', door: false, count: 1 },
      ],
    });
  });

  it('keeps the door a door: dimmed, with no count, and never the tick', () => {
    expect(kindMenu('competitive', ANIA, undefined)).toEqual({
      kind: 'competitive',
      ticked: 'competitive',
      sides: [
        { kind: 'competitive', door: false, count: 7 },
        { kind: 'forFun', door: true },
      ],
    });
  });

  it('stands on the kind the intent shows when the one chosen is the door, as the deck does', () => {
    expect(kindMenu('forFun', ANIA, undefined)).toMatchObject({
      kind: 'competitive',
      ticked: 'competitive',
    });
  });

  it('is drawn off the other kind’s read while the one picked is read — or failed', () => {
    // Both reads carry the same pair of counts, so the menu stays while the deck reads.
    expect(kindMenu('forFun', undefined, ZOFIA)).toEqual({
      kind: 'forFun',
      ticked: 'forFun',
      sides: [
        { kind: 'competitive', door: false, count: 5 },
        { kind: 'forFun', door: false, count: 1 },
      ],
    });
  });

  it('ticks nothing while the deck stands on a kind the read held says is a door', () => {
    expect(kindMenu('forFun', undefined, ANIA)).toMatchObject({
      kind: 'forFun',
      ticked: undefined,
    });
  });

  it('is not there before a read of either kind has come back', () => {
    expect(kindMenu('competitive', undefined, undefined)).toBeUndefined();
  });

  it('is not there while the first-time question is up, whatever the other kind held', () => {
    expect(kindMenu('competitive', [], undefined)).toBeUndefined();
    expect(kindMenu('competitive', [], ZOFIA)).toBeUndefined();
    expect(kindMenu('competitive', undefined, [])).toBeUndefined();
  });
});

describe('the panel a door opens', () => {
  it('says the kind the player plays and their count of it in this group', () => {
    expect(doorPanel([{ kind: 'competitive', count: 7 }], 'forFun')).toEqual({
      yours: 'competitive',
      count: 7,
      tapped: 'forFun',
    });
  });

  it('opens on nothing but a door', () => {
    expect(doorPanel([{ kind: 'competitive', count: 7 }], 'competitive')).toBeUndefined();
    expect(
      doorPanel(
        [
          { kind: 'competitive', count: 7 },
          { kind: 'forFun', count: 0 },
        ],
        'forFun',
      ),
    ).toBeUndefined();
    expect(doorPanel([], 'forFun')).toBeUndefined();
  });

  it('answers Either suits me or the kind tapped, in the intent’s own words', () => {
    const panel = { yours: 'competitive', count: 7, tapped: 'forFun' } as const;

    expect(intentAnswering(panel, 'either')).toBe('NO_PREFERENCE');
    expect(intentAnswering(panel, 'tapped')).toBe('FOR_FUN');
    expect(intentAnswering({ ...panel, yours: 'forFun', tapped: 'competitive' }, 'tapped')).toBe(
      'COMPETITIVE',
    );
  });
});

describe('what finding names, and where it lands (A2.1 state 5)', () => {
  it('names the kind tapped on the door, whichever answer, and lands there', () => {
    expect(findingAfterTheDoor({ yours: 'competitive', count: 7, tapped: 'forFun' })).toEqual({
      landsOn: 'forFun',
      names: 'forFun',
    });
  });

  it('names the kind the first-time question was answered with, and lands there', () => {
    expect(findingAfterTheQuestion('FOR_FUN', 'competitive')).toEqual({
      landsOn: 'forFun',
      names: 'forFun',
    });
    expect(findingAfterTheQuestion('COMPETITIVE', 'forFun')).toEqual({
      landsOn: 'competitive',
      names: 'competitive',
    });
  });

  it('names no kind after Either suits me, and lands where the switch already stands', () => {
    expect(findingAfterTheQuestion('NO_PREFERENCE', 'forFun')).toEqual({ landsOn: 'forFun' });
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

describe('the number a card leads with (ADR-0207 §5, #838)', () => {
  it('is the forecast on a competitive card, and never a vibe', () => {
    expect(headlineOf(card())).toEqual({ kind: 'forecast', pct: 87 });
    expect(headlineOf(card({ vibe: { pct: 60 } }))).toEqual({ kind: 'forecast', pct: 87 });
  });

  it('is the Social vibe on a For-fun card, and never a forecast — even one sent', () => {
    expect(headlineOf(card({ kind: 'forFun', vibe: { pct: 82 } }))).toEqual({
      kind: 'vibe',
      pct: 82,
    });
    expect(headlineOf(card({ kind: 'forFun', forecast: undefined, vibe: { pct: 35 } }))).toEqual({
      kind: 'vibe',
      pct: 35,
    });
  });

  it('is nothing where the server sent its kind’s number none', () => {
    expect(headlineOf(card({ forecast: undefined, vibe: { pct: 60 } }))).toBeUndefined();
    expect(headlineOf(card({ kind: 'forFun' }))).toBeUndefined();
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
    // The cards with somebody In, across both kinds (#846): 'a' here, and 'f' on For fun.
    inCardIds: ['a', 'f'],
    dealtIds: ['a', 'b'],
    gamesPerWeek: 2,
    cappedWeeks: [],
    cards: [card({ proposalId: 'a', inCount: 1 }), card({ proposalId: 'b' })],
  };

  it('drops an answered card, with its segment’s count following it', () => {
    const after = withoutCard(deck, 'a');

    expect(after.cards.map((dealt) => dealt.proposalId)).toEqual(['b']);
    expect(after.segments).toEqual([
      { kind: 'competitive', count: 1 },
      { kind: 'forFun', count: 1 },
    ]);
  });

  // #850's review: a seen card is cut from the seen list only by the server's read, never by an
  // answer it may yet refuse.
  it('leaves the badge’s ids, and the dealt ids, to the server’s next read', () => {
    const after = withoutCard(deck, 'a');

    expect(after.inCardIds).toEqual(['a', 'f']);
    expect(after.dealtIds).toEqual(['a', 'b']);
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

describe('two reads of one card (the deck redraws only what changed)', () => {
  const photo = (n: string) => ({ photoId: 'ph-1', photoUrl: `https://store.test/ph-1?sig=${n}` });

  it('draw the same when every field is equal', () => {
    expect(drawnTheSame(card(), card())).toBe(true);
  });

  it('draw the same when only a photograph’s link was minted again', () => {
    const read = (n: string) =>
      card({ sides: { yours: [YOU, person('Zofia', photo(n))], theirs: [person('Ania')] } });
    expect(drawnTheSame(read('a'), read('b'))).toBe(true);
  });

  it('differ when the photograph itself changed', () => {
    const read = (photoId: string) =>
      card({
        sides: {
          yours: [YOU, person('Zofia', { photoId, photoUrl: `https://store.test/${photoId}` })],
          theirs: [person('Ania')],
        },
      });
    expect(drawnTheSame(read('ph-1'), read('ph-2'))).toBe(false);
  });

  it('differ when a link changed with no photograph to say it is the same one', () => {
    const read = (url: string) =>
      card({ sides: { yours: [YOU, person('Zofia', { photoUrl: url })], theirs: [] } });
    expect(drawnTheSame(read('https://p/a'), read('https://p/b'))).toBe(false);
  });

  it('differ when anything else moved — somebody In, the count, a field gone', () => {
    expect(drawnTheSame(card(), card({ inCount: 1 }))).toBe(false);
    expect(
      drawnTheSame(
        card(),
        card({
          sides: {
            yours: [YOU, person('Zofia', { isIn: true })],
            theirs: [person('Ania'), person('Ewa')],
          },
        }),
      ),
    ).toBe(false);
    const { forecast: _gone, ...withoutForecast } = card();
    expect(drawnTheSame(card(), withoutForecast)).toBe(false);
  });
});
