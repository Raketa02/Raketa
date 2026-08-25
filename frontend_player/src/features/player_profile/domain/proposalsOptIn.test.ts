import { emptyDraft, recordAnswer } from './ProfileDraft';
import { mayFinish, optInStanding } from './proposalsOptIn';

const COPY = 'proposals-opt-in.v1';

describe('what an unanswered question is', () => {
  /**
   * The invariant this whole file exists for: *skipping is not consent*. An absent answer
   * is neither yes nor no, and the one thing it must never quietly become is `false` —
   * a recorded refusal and an unasked question are different facts about a person.
   */
  it('is neither yes nor no', () => {
    expect(optInStanding(undefined)).toEqual({ kind: 'unanswered' });
  });

  it('is what a draft holds the moment the part is entered', () => {
    expect(optInStanding(emptyDraft().proposalsOptIn)).toEqual({ kind: 'unanswered' });
  });

  it('does not open the finish', () => {
    expect(mayFinish(optInStanding(undefined))).toBe(false);
  });
});

describe('an answer that was given', () => {
  it('carries which one it was', () => {
    expect(optInStanding({ accepted: true, copyVersion: COPY })).toEqual({
      kind: 'answered',
      accepted: true,
    });
    expect(optInStanding({ accepted: false, copyVersion: COPY })).toEqual({
      kind: 'answered',
      accepted: false,
    });
  });

  /**
   * **No is a complete answer, not an abandoned setup.** A gate that only opened on yes
   * would be the product pressing for consent by withholding the rest of itself, which is
   * the failure the step's copy is written against.
   */
  it('opens the finish whichever one it was', () => {
    expect(mayFinish(optInStanding({ accepted: true, copyVersion: COPY }))).toBe(true);
    expect(mayFinish(optInStanding({ accepted: false, copyVersion: COPY }))).toBe(true);
  });
});

describe('changing the answer before finishing', () => {
  /**
   * The last one wins, and the copy version travels with it — consent gathered against one
   * sentence is not consent to a different one, so an answer is never held apart from the
   * words it was given against.
   */
  it('replaces the answer and the words it was given against, and disturbs nothing else', () => {
    const said = recordAnswer(emptyDraft(), {
      socialTagIds: ['PLAYS_TO_WIN'],
      proposalsOptIn: { accepted: true, copyVersion: COPY },
    });

    const changedMind = recordAnswer(said, {
      proposalsOptIn: { accepted: false, copyVersion: COPY },
    });

    expect(optInStanding(changedMind.proposalsOptIn)).toEqual({
      kind: 'answered',
      accepted: false,
    });
    expect(changedMind.socialTagIds).toEqual(['PLAYS_TO_WIN']);
  });
});
