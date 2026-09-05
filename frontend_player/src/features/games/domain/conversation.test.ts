/**
 * **The one rule that says what a player may do about a result**, and it is derived from the
 * record rather than asked for.
 *
 * The wire has one route for three acts on purpose — *"a client that named which would be a
 * client that could name it wrongly, and a mislabelled correction is a proposal nobody may
 * make"* — so what this decides is not *which act to send* but **what to draw**: a correction
 * and a counter are the same request and a completely different screen, and a player who spent
 * their side's one turn fixing a typo is the failure the ticket names first.
 */

import type { Game, StandingProposal } from './game';
import { actsOffered, resultConversation } from './conversation';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const OPPONENT = 'opp-111111-4444-8888-00000003';

const PROPOSAL: StandingProposal = {
  side: 'A',
  proposedBy: ME,
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 6, b: 2 },
    ],
  },
  answerBy: '2026-09-06T20:12:00Z',
  settlesAt: '2026-09-06T02:12:00Z',
};

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: 'game-1111-4444-8888-00000000001',
    challengeId: 'ask-11111-4444-8888-000000001',
    sport: 'padel',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    seats: [
      { side: 'A', playerId: ME },
      { side: 'A', playerId: PARTNER },
      { side: 'B', playerId: OPPONENT },
      { side: 'B', playerId: 'opp2-1111-4444-8888-00000004' },
    ],
    plannedAt: '2026-09-01T18:00:00Z',
    entryClosesAt: '2026-09-09T18:00:00Z',
    readAt: '2026-09-05T09:00:00Z',
    ...over,
  };
}

describe('before anybody has said it happened', () => {
  it('offers the entry, and says when saying so stops being possible', () => {
    const conversation = resultConversation(game(), ME);

    expect(conversation).toEqual({ kind: 'awaiting-entry', entryClosesAt: '2026-09-09T18:00:00Z' });
    expect(actsOffered(conversation)).toEqual(['enter']);
  });

  it('offers it to anybody who held a seat, which is all four of them', () => {
    expect(actsOffered(resultConversation(game(), OPPONENT))).toEqual(['enter']);
  });

  it('offers nothing once the window has closed — the game is a ghost and stays one', () => {
    const conversation = resultConversation(game({ standing: 'NEVER_PLAYED' }), ME);

    expect(conversation).toEqual({ kind: 'never-played' });
    expect(actsOffered(conversation)).toEqual([]);
  });
});

describe('one score on the table', () => {
  const played = {
    standing: 'AWAITING_ANSWER',
    playedAt: '2026-09-04T20:12:00Z',
    entryClosesAt: undefined,
    standingProposal: PROPOSAL,
  } as const;

  it('is a correction to the side that put it there, and never a second turn', () => {
    const conversation = resultConversation(game(played), ME);

    expect(conversation).toEqual({ kind: 'ours-stands', proposal: PROPOSAL });
    expect(actsOffered(conversation)).toEqual(['correct']);
  });

  /**
   * ADR-0137 §4's one narrowing, read from the client: *"the correction is the side's and not
   * its author's"*, so a player who disagrees with their own partner has a way to say so and
   * neither side gets two turns.
   */
  it('is a correction to the partner too, because the score is the side’s', () => {
    expect(actsOffered(resultConversation(game(played), PARTNER))).toEqual(['correct']);
  });

  it('is an agreement or a disagreement across the net, and the agreement leads', () => {
    const conversation = resultConversation(game(played), OPPONENT);

    expect(conversation).toEqual({ kind: 'theirs-stands', proposal: PROPOSAL });
    expect(actsOffered(conversation)).toEqual(['accept', 'counter']);
  });
});

describe('two scores on the table', () => {
  /**
   * `standing_proposal` is `null` in two cases that mean opposite things — nothing entered, or
   * **both sides have spoken** — and the client reads which off the standing rather than off
   * the absence, which is exactly what the schema's own docblock instructs.
   */
  it('is read off the standing and never off the missing proposal', () => {
    const conversation = resultConversation(
      game({ standing: 'AWAITING_ANSWER', playedAt: '2026-09-04T20:12:00Z' }),
      ME,
    );

    expect(conversation).toEqual({ kind: 'both-stand' });
  });

  /**
   * **Nothing is offered, and the module note is why**: the wire returns neither score in this
   * state, and a control asking somebody to agree with a score the screen cannot show them is
   * the one thing worse than not offering it.
   */
  it('offers nothing, because there is nothing on screen to agree with', () => {
    expect(actsOffered({ kind: 'both-stand' })).toEqual([]);
  });
});

describe('the ends', () => {
  it('confirms with the agreed score and what it says about you', () => {
    const conversation = resultConversation(
      game({
        standing: 'CONFIRMED',
        playedAt: '2026-09-04T20:12:00Z',
        score: PROPOSAL.score,
        outcome: 'WIN',
      }),
      ME,
    );

    expect(conversation).toEqual({ kind: 'confirmed', score: PROPOSAL.score, outcome: 'WIN' });
    expect(actsOffered(conversation)).toEqual([]);
  });

  it('leaves an unscored game alone — a settled result is final, and so is no result', () => {
    const conversation = resultConversation(
      game({ standing: 'UNSCORED', playedAt: '2026-09-04T20:12:00Z' }),
      ME,
    );

    expect(conversation).toEqual({ kind: 'unscored' });
    expect(actsOffered(conversation)).toEqual([]);
  });
});

describe('somebody who was not on this court', () => {
  /**
   * Unreachable through the list, which serves your games and nobody else's — and a state the
   * screen has to hold anyway, because a link is not a list. It is the client half of
   * `you_were_not_on_this_court`, and it names the same two cases the server refuses to tell
   * apart.
   */
  it('has no side, so there is no conversation and nothing to offer', () => {
    const conversation = resultConversation(game(), 'stranger-1-4444-8888-00000005');

    expect(conversation).toEqual({ kind: 'not-yours' });
    expect(actsOffered(conversation)).toEqual([]);
  });
});

describe('a standing this build is too old to read', () => {
  /**
   * A standing *is* the whole line, so it draws the out-of-date sentence rather than being
   * dropped — `the-words.md` §3's named gap, exactly as a challenge's standing does. What it
   * must never do is offer an act: acting on a game whose state we cannot name is how a
   * correction becomes a second proposal.
   */
  it('has a conversation with no acts in it', () => {
    const conversation = resultConversation(game({ standing: undefined }), ME);

    expect(conversation).toEqual({ kind: 'unreadable' });
    expect(actsOffered(conversation)).toEqual([]);
  });
});
