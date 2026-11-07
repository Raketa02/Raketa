import {
  cardAskOf,
  emptyLineUp,
  keptAsShown,
  openSeatsOf,
  pinned,
  seatPicks,
  seatedOf,
  shownSeats,
  swapSeats,
  takeOff,
  togglePick,
  withCourt,
  withoutCourt,
  withoutStrangers,
  type FriendsLineUp,
} from './friendsLineUp';

const EWA = 'ewa';
const MAGDA = 'magda';
const ANIA = 'ania';
const ZOFIA = 'zofia';
const COURT = { courtId: 'court-3', startsAt: '2026-11-14T09:00:00Z' };

/** Three seated, as Done leaves them — evenest, waiting on the card. */
function doneWith(picks: readonly string[]): FriendsLineUp {
  return seatPicks(emptyLineUp(3), picks);
}

describe('an empty line-up', () => {
  it('has the seats the sport puts beside the reader, every one open', () => {
    expect(emptyLineUp(3)).toEqual({ seats: [null, null, null], evenest: false });
    expect(openSeatsOf(emptyLineUp(1).seats)).toBe(1);
  });
});

describe('Done', () => {
  it('seats the picks in the order picked, and asks the card for the evenest sides', () => {
    expect(doneWith([EWA, MAGDA, ANIA])).toEqual({ seats: [EWA, MAGDA, ANIA], evenest: true });
  });

  it('keeps a friend already seated in their seat, and fills the empty ones with the rest', () => {
    const one = { seats: [null, EWA, null], evenest: false } as const;

    expect(seatPicks(one, [MAGDA, EWA]).seats).toEqual([MAGDA, EWA, null]);
  });

  it('takes off whoever was unpicked', () => {
    const three = { seats: [EWA, MAGDA, ANIA], evenest: false } as const;

    expect(seatPicks(three, [MAGDA, ZOFIA]).seats).toEqual([ZOFIA, MAGDA, null]);
  });

  it('keeps a court picked while the same friends are seated, and drops it once they change', () => {
    const picked: FriendsLineUp = { seats: [EWA, MAGDA, ANIA], evenest: false, court: COURT };

    expect(seatPicks(picked, [ANIA, EWA, MAGDA]).court).toEqual(COURT);
    expect(seatPicks(picked, [ANIA, EWA, ZOFIA]).court).toBeUndefined();
  });

  it('never seats more than the court holds', () => {
    expect(seatPicks(emptyLineUp(1), [EWA, MAGDA]).seats).toEqual([EWA]);
  });
});

describe('the seats the court draws', () => {
  it('are the card’s evenest sides once it is read — your partner first, then theirs', () => {
    const sides = { yours: ['me', ANIA], theirs: [MAGDA, EWA] };

    expect(shownSeats(doneWith([EWA, MAGDA, ANIA]), sides)).toEqual([ANIA, MAGDA, EWA]);
  });

  it('are the seats as picked while the card is read', () => {
    expect(shownSeats(doneWith([EWA, MAGDA, ANIA]), undefined)).toEqual([EWA, MAGDA, ANIA]);
  });

  it('are the seats as they stand once the player has moved somebody', () => {
    const moved = { seats: [MAGDA, EWA, ANIA], evenest: false } as const;
    const sides = { yours: ['me', ANIA], theirs: [MAGDA, EWA] };

    expect(shownSeats(moved, sides)).toEqual([MAGDA, EWA, ANIA]);
  });

  it('ignore a card read for somebody else', () => {
    const sides = { yours: ['me', ZOFIA], theirs: [MAGDA, EWA] };

    expect(shownSeats(doneWith([EWA, MAGDA, ANIA]), sides)).toEqual([EWA, MAGDA, ANIA]);
  });

  it('are a singles court’s one seat, whatever the card says', () => {
    expect(shownSeats(seatPicks(emptyLineUp(1), [EWA]), { yours: ['me'], theirs: [EWA] })).toEqual([
      EWA,
    ]);
  });
});

describe('a swap', () => {
  const shown = [ANIA, MAGDA, EWA] as const;

  it('trades two faces’ seats, and the sides stand as the player put them', () => {
    expect(swapSeats(doneWith([EWA, MAGDA, ANIA]), shown, MAGDA, ANIA)).toEqual({
      seats: [MAGDA, ANIA, EWA],
      evenest: false,
    });
  });

  it('keeps the court picked: the same four, standing differently', () => {
    const picked: FriendsLineUp = { seats: [...shown], evenest: false, court: COURT };

    expect(swapSeats(picked, shown, EWA, ANIA).court).toEqual(COURT);
  });

  it('moves nobody for a face that is not on the court', () => {
    expect(swapSeats(doneWith([EWA, MAGDA, ANIA]), shown, ZOFIA, ANIA).seats).toEqual(shown);
  });
});

describe('the ×', () => {
  it('empties that face’s seat, leaves the rest where they are drawn, and drops the court', () => {
    const picked: FriendsLineUp = { seats: [EWA, MAGDA, ANIA], evenest: true, court: COURT };

    expect(takeOff(picked, [ANIA, MAGDA, EWA], ANIA)).toEqual({
      seats: [null, MAGDA, EWA],
      evenest: false,
    });
  });
});

describe('pinning what is drawn', () => {
  it('keeps the sides the court shows when something else about the game changes', () => {
    expect(pinned(doneWith([EWA, MAGDA, ANIA]), [ANIA, MAGDA, EWA])).toEqual({
      seats: [ANIA, MAGDA, EWA],
      evenest: false,
    });
  });
});

describe('a friend who is no longer one', () => {
  it('leaves an empty seat, and the court picked for the four goes with them', () => {
    const picked: FriendsLineUp = { seats: [EWA, MAGDA, ANIA], evenest: true, court: COURT };

    expect(withoutStrangers(picked, new Set([EWA, ANIA]))).toEqual({
      seats: [EWA, null, ANIA],
      evenest: true,
    });
  });

  it('changes nothing while the friends are still being read, or all are still friends', () => {
    const lineUp = doneWith([EWA, MAGDA, ANIA]);

    expect(withoutStrangers(lineUp, undefined)).toBe(lineUp);
    expect(withoutStrangers(lineUp, new Set([EWA, MAGDA, ANIA, ZOFIA]))).toBe(lineUp);
  });
});

describe('what the card is asked', () => {
  it('is nothing while a seat is empty', () => {
    expect(cardAskOf({ seats: [EWA, null, ANIA], evenest: false })).toBeUndefined();
  });

  it('is the friends as seated, and no partner while the card is to choose the sides', () => {
    expect(cardAskOf(doneWith([EWA, MAGDA, ANIA]))).toEqual({ friendIds: [EWA, MAGDA, ANIA] });
  });

  it('names the partner beside the reader once the player has stood the sides', () => {
    expect(cardAskOf({ seats: [MAGDA, EWA, ANIA], evenest: false, court: COURT })).toEqual({
      friendIds: [MAGDA, EWA, ANIA],
      partnerId: MAGDA,
      court: COURT,
    });
  });

  it('never names a partner in singles', () => {
    expect(cardAskOf({ seats: [EWA], evenest: false })).toEqual({ friendIds: [EWA] });
  });
});

describe('who is seated', () => {
  it('is every face on the court, in seat order', () => {
    expect(seatedOf([EWA, null, ANIA])).toEqual([EWA, ANIA]);
    expect(openSeatsOf([EWA, null, ANIA])).toBe(1);
  });
});

describe('a pick in the picker', () => {
  it('ticks a friend, and unticks one already picked', () => {
    expect(togglePick([EWA], MAGDA, 3)).toEqual([EWA, MAGDA]);
    expect(togglePick([EWA, MAGDA], EWA, 3)).toEqual([MAGDA]);
  });

  it('ticks nobody more once the seats are full', () => {
    expect(togglePick([EWA], MAGDA, 1)).toEqual([EWA]);
  });
});

describe('a court picked in Find a court', () => {
  it('is put on the line-up, which keeps the sides the court shows', () => {
    expect(withCourt(doneWith([EWA, MAGDA, ANIA]), [ANIA, MAGDA, EWA], COURT)).toEqual({
      seats: [ANIA, MAGDA, EWA],
      evenest: false,
      court: COURT,
    });
  });

  it('is let go when it is no longer for sale, and the sides stay', () => {
    expect(withoutCourt({ seats: [ANIA, MAGDA, EWA], evenest: false, court: COURT })).toEqual({
      seats: [ANIA, MAGDA, EWA],
      evenest: false,
    });
  });
});

describe('another kind chosen', () => {
  it('keeps the sides the court shows once every seat is filled', () => {
    expect(keptAsShown(doneWith([EWA, MAGDA, ANIA]), [ANIA, MAGDA, EWA])).toEqual({
      seats: [ANIA, MAGDA, EWA],
      evenest: false,
    });
  });

  it('changes nothing while a seat is open, or once the sides are already the player’s', () => {
    const open = { seats: [EWA, null, ANIA], evenest: false } as const;
    const stood = { seats: [ANIA, MAGDA, EWA], evenest: false } as const;

    expect(keptAsShown(open, open.seats)).toBe(open);
    expect(keptAsShown(stood, stood.seats)).toBe(stood);
  });
});
