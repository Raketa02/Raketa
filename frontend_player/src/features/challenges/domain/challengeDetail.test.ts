/**
 * The fold the challenge screen is keyed on — **six standings, two sides, and the seat that
 * decides whether there is anything to press.**
 *
 * What is asserted here is the set of claims a build session could quietly undo: that a card
 * block is drawn while the arrangement is being decided and at no other time, that the two
 * answers are offered only where the act they name can actually happen, and that a standing
 * this build cannot read offers nothing at all.
 */

import type { ChallengeDetail, DetailSeat, SeatCard } from './challengeDetail';
import {
  acceptedPlayers,
  asTheRowSays,
  challengeArm,
  readerIsInTheRoom,
  redrawnFrom,
  seatsAwaiting,
} from './challengeDetail';
import { STANDINGS, type Standing } from './standing';

const ME = 'me';
const BEA = 'bea';
const CYRYL = 'cyryl';
const DIETER = 'dieter';

/** A card's contents are nothing to this fold — what it decides is whether one is drawn. */
const A_CARD = {} as SeatCard;

function detail(
  standing: Standing | undefined,
  seats: readonly DetailSeat[],
  organiserId = ME,
): ChallengeDetail {
  return {
    challengeId: 'c1',
    organiserId,
    ...(standing === undefined ? {} : { standing }),
    sport: 'padel',
    openedAt: '2026-09-05T09:00:00Z',
    readAt: '2026-09-05T12:00:00Z',
    seats,
  };
}

describe('the two answers', () => {
  /** The whole point of the screen: an invitee with a seat nobody has answered for. */
  it('offers them to an invitee whose own seat is still waiting', () => {
    const arm = challengeArm(
      detail(
        'AWAITING_ANSWERS',
        [
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: ME, answerBy: '2026-09-07T09:00:00Z', card: A_CARD },
        ],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('answer');
    expect(arm.kind === 'answer' ? arm.answerBy : undefined).toBe('2026-09-07T09:00:00Z');
  });

  /**
   * **A doubles four where one invitee has already accepted is still `AWAITING_ANSWERS`.**
   * Their act is spent: `POST /accept` answers `seat_already_answered`, so a button naming it
   * would name a state the act cannot produce.
   */
  it('withholds them from an invitee who has already answered', () => {
    const arm = challengeArm(
      detail(
        'AWAITING_ANSWERS',
        [
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: ME, answer: 'ACCEPTED' },
          { playerId: CYRYL },
          { playerId: DIETER },
        ],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('arranging');
  });

  /** The organiser's seat is accepted from birth, so there was never an answer to give. */
  it('withholds them from the organiser', () => {
    const arm = challengeArm(
      detail('AWAITING_ANSWERS', [{ playerId: ME, answer: 'ACCEPTED' }, { playerId: BEA }]),
      ME,
    );

    expect(arm.kind).toBe('arranging');
  });

  /** A link to somebody else's challenge is a 404 on the wire; this is the same answer. */
  it('withholds them from a reader who holds no seat at all', () => {
    const arm = challengeArm(
      detail('AWAITING_ANSWERS', [{ playerId: BEA, answer: 'ACCEPTED' }, { playerId: CYRYL }], BEA),
      ME,
    );

    expect(arm.kind).toBe('arranging');
  });
});

describe('the card block', () => {
  /**
   * ADR-0143 §8, stated on the two standings that draw one so a standing added later is
   * silent by default.
   */
  it('is drawn while the arrangement is being decided and in no other standing', () => {
    const drawing = STANDINGS.filter((standing) => {
      const arm = challengeArm(
        detail(standing, [{ playerId: BEA, answer: 'ACCEPTED' }, { playerId: ME }], BEA),
        ME,
      );
      return arm.kind === 'answer' || arm.kind === 'arranging' || arm.kind === 'filling';
    });

    expect(drawing).toEqual(['AWAITING_ANSWERS', 'LINE_UP_INCOMPLETE']);
  });

  /**
   * *That person is a stranger to you once more the moment they leave*, and the reader who
   * left is owed the sentence rather than a court full of cards.
   */
  it('is not drawn for a reader who declined inside a challenge that still stands', () => {
    const arm = challengeArm(
      detail(
        'LINE_UP_INCOMPLETE',
        [
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: CYRYL, answer: 'ACCEPTED' },
          { playerId: ME, answer: 'DECLINED' },
          {},
        ],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('stated');
  });

  /**
   * **The same, one standing up** — #392. `standing_of` holds `AWAITING_ANSWERS` while *any*
   * seat is awaiting, so a reader who has answered sits in it with nothing left to answer; and
   * the card block is what a reader answers *against*, so there is nothing for it to do. Both
   * live standings ask one question of the reader's own seat.
   */
  it('is not drawn for a reader who has left while somebody else still has not answered', () => {
    for (const mine of ['DECLINED', 'LAPSED'] as const) {
      const arm = challengeArm(
        detail(
          'AWAITING_ANSWERS',
          [
            { playerId: BEA, answer: 'ACCEPTED' },
            { playerId: CYRYL },
            { playerId: ME, answer: mine },
          ],
          BEA,
        ),
        ME,
      );

      expect(arm.kind).toBe('stated');
    }
  });

  /**
   * The one case the two arguments for this rule disagree about, and the precedent settles it:
   * an accepted reader is still on the court and the pair has not released, so they keep the
   * card — exactly as they do in `LINE_UP_INCOMPLETE`.
   */
  it('is still drawn for a reader who accepted and is still in it', () => {
    const arm = challengeArm(
      detail(
        'AWAITING_ANSWERS',
        [
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: CYRYL },
          { playerId: ME, answer: 'ACCEPTED' },
        ],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('arranging');
  });

  it('is drawn for a member who is still in one', () => {
    const arm = challengeArm(
      detail(
        'LINE_UP_INCOMPLETE',
        [
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: ME, answer: 'ACCEPTED', card: A_CARD },
          { playerId: CYRYL, answer: 'DECLINED' },
          {},
        ],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('filling');
  });
});

/**
 * **Grow · talk · leave**, and nobody ends it
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §1, [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4): any live member may complete the line-up, and a court somebody has joined is nobody's to
 * end for the others — the organiser leaves it like anybody else, and it ends by itself when one
 * is left.
 */
describe('a half-built court', () => {
  const HALF_BUILT: readonly DetailSeat[] = [
    { playerId: BEA, answer: 'ACCEPTED' },
    { playerId: ME, answer: 'ACCEPTED', card: A_CARD },
    { playerId: CYRYL, answer: 'DECLINED' },
    {},
  ];

  it('lets any live member fill it, and offers the organiser no end', () => {
    const invitee = challengeArm(detail('LINE_UP_INCOMPLETE', HALF_BUILT, BEA), ME);
    const organiser = challengeArm(detail('LINE_UP_INCOMPLETE', HALF_BUILT, ME), ME);

    expect(invitee).toEqual({ kind: 'filling', facts: expect.anything() });
    expect(organiser).toEqual({ kind: 'filling', facts: expect.anything() });
  });

  /**
   * A departed seat is still a seat, so the row stays — and what they get is the sentence and
   * nothing to press. Not even the fill: they are not a live member. (**The pair rule does not
   * hold them**; it released them when they left — [#393](https://github.com/Raketa02/Raketa/issues/393).)
   */
  it('offers the reader who has left nothing to press', () => {
    const arm = challengeArm(
      detail(
        'LINE_UP_INCOMPLETE',
        [{ playerId: BEA, answer: 'ACCEPTED' }, { playerId: ME, answer: 'LAPSED' }, {}, {}],
        BEA,
      ),
      ME,
    );

    expect(arm.kind).toBe('stated');
  });

  /**
   * **Who the fill may never take out** — read here because the fill's own answer cannot say
   * it: the people who accepted come back as ordinary candidate rows, and an ordinary row says
   * nothing about a challenge.
   */
  it('names who has already said yes, without the reader and in seat order', () => {
    expect(acceptedPlayers(detail('LINE_UP_INCOMPLETE', HALF_BUILT, BEA), ME)).toEqual([BEA]);
  });

  it('names nobody on a court where only the reader has accepted', () => {
    const alone: readonly DetailSeat[] = [{ playerId: ME, answer: 'ACCEPTED' }, {}];

    expect(acceptedPlayers(detail('LINE_UP_INCOMPLETE', alone, ME), ME)).toEqual([]);
  });
});

describe('the way out before the court is whole', () => {
  /**
   * **Leaving is the Chats row's swipe alone** (ADR-0175 §4), so the arm asks nothing about it;
   * what it asks is the removal's question, `mayRemove` — the organiser's, exactly while nobody
   * besides them holds an accepted seat (ADR-0165 §4).
   */
  it('offers nobody a leave, and the removal to no invitee', () => {
    const waiting: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', card: A_CARD },
      { playerId: CYRYL, answerBy: '2026-09-07T09:00:00Z' },
      {},
    ];

    const invitee = challengeArm(detail('AWAITING_ANSWERS', waiting, BEA), ME);
    const organiser = challengeArm(detail('AWAITING_ANSWERS', waiting, ME), ME);

    expect(invitee).toEqual({ kind: 'arranging', facts: expect.anything(), mayRemove: false });
    expect(organiser).toEqual({ kind: 'arranging', facts: expect.anything(), mayRemove: false });
  });

  /**
   * **A court of one is the organiser's to remove.** The organiser alone, with everybody still
   * deciding or already out, is on no court with anybody — their exit there is *Remove the
   * challenge* (ADR-0165 §4, [#428](https://github.com/Raketa02/Raketa/issues/428)).
   */
  it('offers the removal to an organiser nobody has joined yet', () => {
    const arm = challengeArm(
      detail('AWAITING_ANSWERS', [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, answerBy: '2026-09-07T09:00:00Z' },
      ]),
      ME,
    );

    expect(arm).toEqual({ kind: 'arranging', facts: expect.anything(), mayRemove: true });
  });

  it('offers the removal to an organiser whose every invitee has already given the seat up', () => {
    const arm = challengeArm(
      detail('AWAITING_ANSWERS', [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, answer: 'DECLINED' },
        { playerId: CYRYL, answerBy: '2026-09-07T09:00:00Z' },
        {},
      ]),
      ME,
    );

    expect(arm).toEqual({ kind: 'arranging', facts: expect.anything(), mayRemove: true });
  });
});

describe('the room, and whether the reader is in it', () => {
  const PAIR: readonly DetailSeat[] = [
    { playerId: BEA, answer: 'ACCEPTED' },
    { playerId: ME, answer: undefined, answerBy: '2026-09-06T12:00:00Z' },
  ];

  /** Nobody is in a room they have not said yes to: an unanswered invitee is not a member. */
  it('is not, while the reader has an answer to give', () => {
    expect(readerIsInTheRoom(challengeArm(detail('AWAITING_ANSWERS', PAIR, BEA), ME))).toBe(false);
  });

  it('is, on an accepted seat waiting on the others, and for the organiser waiting', () => {
    const waiting: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: undefined },
      { playerId: ME, answer: 'ACCEPTED' },
      {},
    ];

    expect(readerIsInTheRoom(challengeArm(detail('AWAITING_ANSWERS', waiting, BEA), ME))).toBe(
      true,
    );
    expect(readerIsInTheRoom(challengeArm(detail('AWAITING_ANSWERS', waiting, BEA), BEA))).toBe(
      true,
    );
  });

  it('is, for a live member of a half-built court, and on a court that is on', () => {
    const half: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED' },
      {},
      {},
    ];
    const on: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED' },
    ];

    expect(readerIsInTheRoom(challengeArm(detail('LINE_UP_INCOMPLETE', half, BEA), ME))).toBe(true);
    expect(readerIsInTheRoom(challengeArm(detail('ON', on, BEA), ME))).toBe(true);
  });

  /**
   * A reader who left is outside whatever room the others keep, and a list that still holds
   * it is a beat behind the reply — this is the reading that keeps a door off that beat.
   */
  it('is not, for a reader who left, nor once the episode has ended', () => {
    const left: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'DECLINED' },
      {},
      {},
    ];
    const ended: readonly DetailSeat[] = [
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'DECLINED' },
    ];

    expect(readerIsInTheRoom(challengeArm(detail('LINE_UP_INCOMPLETE', left, BEA), ME))).toBe(
      false,
    );
    expect(readerIsInTheRoom(challengeArm(detail('AWAITING_ANSWERS', left, BEA), ME))).toBe(false);
    expect(readerIsInTheRoom(challengeArm(detail('DECLINED', ended, BEA), ME))).toBe(false);
    expect(readerIsInTheRoom(challengeArm(detail('WITHDRAWN', ended, BEA), ME))).toBe(false);
    expect(readerIsInTheRoom(challengeArm(detail('CALLED_OFF', ended, BEA), ME))).toBe(false);
    expect(readerIsInTheRoom(challengeArm(detail(undefined, ended, BEA), ME))).toBe(false);
  });
});

/**
 * **The ended court** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7): a `CALLED_OFF` court and a `DECLINED` one a departure ended are drawn as the row's
 * sentence over every seat and what each person did — *You · in*, *left*, *said no*, *called it
 * off* — and offer nothing. Every other ending, and a court everybody merely declined, is the
 * sentence alone as before.
 */
describe('the ended court', () => {
  const named = (playerId: string, name: string, answer?: DetailSeat['answer']): DetailSeat => ({
    playerId,
    name,
    ...(answer === undefined ? {} : { answer }),
  });

  it('lists every seat and what each did, on a game called off by the last departure', () => {
    const court = {
      ...detail('CALLED_OFF', [
        named(ME, 'me.p', 'ACCEPTED'),
        named(BEA, 'bea.k', 'LEFT'),
        named(CYRYL, 'cyryl.w', 'LEFT'),
        named(DIETER, 'dieter.s', 'LEFT'),
      ]),
      endedBy: DIETER,
      gameId: 'g1',
    };

    expect(challengeArm(court, ME)).toEqual({
      kind: 'ended',
      facts: expect.objectContaining({ standing: 'CALLED_OFF', byADeparture: true }),
      court: [
        { playerId: ME, who: { kind: 'you' }, did: 'in' },
        { playerId: BEA, who: { kind: 'player', name: 'bea.k' }, did: 'left' },
        { playerId: CYRYL, who: { kind: 'player', name: 'cyryl.w' }, did: 'left' },
        { playerId: DIETER, who: { kind: 'player', name: 'dieter.s' }, did: 'left' },
      ],
    });
  });

  /**
   * **Every word is the seat's own** (ADR-0175 §1, §2): nobody's seat says *called it off* any
   * more, a seat still deciding when the court closed reads *asked*, and the hour's court —
   * nobody named — reads the same seats the same way.
   */
  it('reads each seat’s own word, a seat still deciding as asked, and never a presser', () => {
    const court = {
      ...detail('CALLED_OFF', [
        named(ME, 'me.p', 'ACCEPTED'),
        named(BEA, 'bea.k', 'LEFT'),
        { playerId: CYRYL, name: 'cyryl.w' },
        named(DIETER, 'dieter.s', 'LEFT'),
      ]),
      endedBy: BEA,
      gameId: 'g1',
    };

    const arm = challengeArm(court, ME);
    expect(arm.kind === 'ended' ? arm.court.map((seat) => seat.did) : []).toEqual([
      'in',
      'left',
      'asked',
      'left',
    ]);
    expect(arm.kind === 'ended' ? arm.court[0] : undefined).toEqual({
      playerId: ME,
      who: { kind: 'you' },
      did: 'in',
    });

    const { endedBy: _nobody, ...theHours } = court;
    const byTheHour = challengeArm(theHours, ME);
    expect(byTheHour.kind === 'ended' ? byTheHour.court.map((seat) => seat.did) : []).toEqual([
      'in',
      'left',
      'asked',
      'left',
    ]);
  });

  it('is drawn for a court that never became a game and ended on a departure, with a no and a lapse said', () => {
    const court = {
      ...detail('DECLINED', [
        named(ME, 'me.p', 'ACCEPTED'),
        named(BEA, 'bea.k', 'LEFT'),
        named(CYRYL, 'cyryl.w', 'DECLINED'),
        named(DIETER, 'dieter.s', 'LAPSED'),
      ]),
      endedBy: BEA,
    };

    const arm = challengeArm(court, ME);
    expect(arm.kind).toBe('ended');
    expect(arm.kind === 'ended' ? arm.court.map((seat) => seat.did) : []).toEqual([
      'in',
      'left',
      'said-no',
      'ran-out',
    ]);
  });

  /** An empty seat did nothing and is nobody: a court lists people. */
  it('lists occupied seats only', () => {
    const court = {
      ...detail('DECLINED', [named(ME, 'me.p', 'ACCEPTED'), named(BEA, 'bea.k', 'LEFT'), {}, {}]),
      endedBy: BEA,
    };

    const arm = challengeArm(court, ME);
    expect(arm.kind === 'ended' ? arm.court.map((seat) => seat.playerId) : []).toEqual([ME, BEA]);
  });

  it('is not drawn for a court everybody declined, a lapse or a withdrawal, which stay the sentence alone', () => {
    const declined = {
      ...detail('DECLINED', [named(ME, 'me.p', 'ACCEPTED'), named(BEA, 'bea.k', 'DECLINED')]),
      endedBy: BEA,
    };
    const lapsed = {
      ...detail('LAPSED', [named(ME, 'me.p', 'ACCEPTED'), named(BEA, 'bea.k', 'LAPSED')]),
      endedBy: BEA,
    };
    const withdrawn = {
      ...detail('WITHDRAWN', [named(ME, 'me.p', 'ACCEPTED'), named(BEA, 'bea.k')]),
      endedBy: ME,
    };

    expect(challengeArm(declined, ME).kind).toBe('stated');
    expect(challengeArm(lapsed, ME).kind).toBe('stated');
    expect(challengeArm(withdrawn, ME).kind).toBe('stated');
  });

  /**
   * The detail read carries no `ended_by` and no `game_id`; the row the list holds does. Merged
   * onto the detail before the fold, and a row that has not landed changes nothing.
   */
  it('reads who ended it and the game off the row the list holds', () => {
    const court = detail('CALLED_OFF', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'LEFT'),
    ]);
    const row = { ...court, endedBy: BEA, gameId: 'g1', endedAt: '2026-09-05T11:00:00Z' };

    expect(asTheRowSays(court, row)).toMatchObject({ endedBy: BEA, gameId: 'g1' });
    expect(asTheRowSays(court, row)).not.toHaveProperty('endedAt');
    expect(asTheRowSays(court, undefined)).toBe(court);
  });
});

describe('a standing this build cannot read', () => {
  /**
   * §3's named gap: the code *is* the whole sentence, and acting on a challenge whose standing
   * we cannot name is how an answer lands on a state nobody drew.
   */
  it('offers nothing and states nothing', () => {
    expect(challengeArm(detail(undefined, [{ playerId: ME }], BEA), ME)).toEqual({
      kind: 'unreadable',
    });
  });
});

describe('the seats the organiser is waiting on', () => {
  /**
   * §14's second sentence is per seat, so the list is per seat — and an empty seat has no
   * deadline because nobody was asked.
   */
  it('lists occupied seats that have not answered and have a deadline', () => {
    const waiting = seatsAwaiting(
      detail('AWAITING_ANSWERS', [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, name: 'bea.k', answerBy: '2026-09-07T09:00:00Z' },
        {
          playerId: CYRYL,
          name: 'cyryl.w',
          answer: 'DECLINED',
          answerBy: '2026-09-07T09:00:00Z',
        },
        {},
      ]),
    );

    expect(waiting).toEqual([
      { player: { kind: 'player', name: 'bea.k' }, answerBy: '2026-09-07T09:00:00Z' },
    ]);
  });
});

describe('the reply is the redraw', () => {
  const HELD = detail(
    'AWAITING_ANSWERS',
    [
      { playerId: BEA, answer: 'ACCEPTED', card: A_CARD },
      { playerId: ME, answerBy: '2026-09-07T09:00:00Z' },
    ],
    BEA,
  );

  /**
   * ADR-0143 §8: *a doubles accept that leaves the challenge in `LINE_UP_INCOMPLETE` keeps the
   * card block the client already holds — nothing about accepting changes who those people are.*
   * The reply carries no cards, so a merge that took the reply whole would blank the screen.
   */
  it('keeps the cards the screen holds, because the reply carries none', () => {
    const redrawn = redrawnFrom(HELD, {
      standing: 'LINE_UP_INCOMPLETE',
      seats: [
        { playerId: BEA, answer: 'ACCEPTED' },
        { playerId: ME, answer: 'ACCEPTED' },
      ],
    });

    expect(redrawn.standing).toBe('LINE_UP_INCOMPLETE');
    expect(redrawn.seats[0]?.card).toBe(A_CARD);
    expect(redrawn.seats[1]?.answer).toBe('ACCEPTED');
  });

  /**
   * The pair releases the moment somebody leaves, one level down as well as at the top: holding
   * their card because the reply had none either way would keep a stranger on screen.
   */
  it('drops the card of a seat that has left', () => {
    const redrawn = redrawnFrom(HELD, {
      standing: 'LINE_UP_INCOMPLETE',
      seats: [
        { playerId: BEA, answer: 'DECLINED' },
        { playerId: ME, answer: 'ACCEPTED' },
      ],
    });

    expect(redrawn.seats[0]?.card).toBeUndefined();
  });

  /**
   * **The one mistake this merge could make that nothing downstream could detect.** A card is a
   * statement about a person, so position joins the seats and the occupant is checked anyway.
   */
  it('never carries a card onto a seat somebody else now holds', () => {
    const redrawn = redrawnFrom(HELD, {
      standing: 'AWAITING_ANSWERS',
      seats: [{ playerId: CYRYL }, { playerId: ME, answer: 'ACCEPTED' }],
    });

    expect(redrawn.seats[0]?.card).toBeUndefined();
  });

  /**
   * A standing this build cannot read has to **clear** the one on screen: the previous sentence
   * left standing over a challenge that has moved is the screen saying something false.
   */
  it('clears a standing it can no longer name rather than leaving the old sentence up', () => {
    const redrawn = redrawnFrom(HELD, { seats: [{ playerId: BEA }, { playerId: ME }] });

    expect(redrawn.standing).toBeUndefined();
    expect(challengeArm(redrawn, ME)).toEqual({ kind: 'unreadable' });
  });
});
