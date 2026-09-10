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
import { acceptedPlayers, challengeArm, redrawnFrom, seatsAwaiting } from './challengeDetail';
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
 * **Grow · talk · end**, and the two permissions are different
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §1): any live member may complete the line-up, and only the organiser may end it.
 */
describe('a half-built court', () => {
  const HALF_BUILT: readonly DetailSeat[] = [
    { playerId: BEA, answer: 'ACCEPTED' },
    { playerId: ME, answer: 'ACCEPTED', card: A_CARD },
    { playerId: CYRYL, answer: 'DECLINED' },
    {},
  ];

  it('lets any live member fill it, and only the organiser end it', () => {
    const invitee = challengeArm(detail('LINE_UP_INCOMPLETE', HALF_BUILT, BEA), ME);
    const organiser = challengeArm(detail('LINE_UP_INCOMPLETE', HALF_BUILT, ME), ME);

    expect(invitee).toEqual({ kind: 'filling', facts: expect.anything(), mayEnd: false });
    expect(organiser).toEqual({ kind: 'filling', facts: expect.anything(), mayEnd: true });
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
        { playerId: BEA, nickname: 'bea.k', answerBy: '2026-09-07T09:00:00Z' },
        {
          playerId: CYRYL,
          nickname: 'cyryl.w',
          answer: 'DECLINED',
          answerBy: '2026-09-07T09:00:00Z',
        },
        {},
      ]),
    );

    expect(waiting).toEqual([
      { player: { kind: 'player', nickname: 'bea.k' }, answerBy: '2026-09-07T09:00:00Z' },
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
