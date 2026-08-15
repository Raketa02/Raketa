/**
 * The position rules, with no renderer, no cache and no network.
 *
 * These are the arithmetic of "where am I in this run", and they are worth pinning apart
 * from the screen because the interesting cases are the ones a screen makes hard to
 * reach: a transcript that got shorter, a run that has stopped asking, a step that has
 * not arrived yet.
 */

import type { AnsweredQuestion, AssessmentStep, Question } from './Assessment';
import {
  answeredQuestions,
  outstandingPosition,
  questionAt,
  standingPosition,
} from './questionNavigation';

function question(id: string): Question {
  return {
    id,
    category: 'Match execution',
    tier: 'standard',
    situation: `The situation for ${id}`,
    text: `The question ${id} asks`,
    qualifier: 'A normal match against players at your level',
    options: [
      { id: 'rarely', text: 'Rarely' },
      { id: 'usually', text: 'Usually' },
    ],
  };
}

function answered(id: string, optionId: string): AnsweredQuestion {
  return { question: question(id), optionId };
}

function step(overrides: Partial<AssessmentStep> = {}): AssessmentStep {
  return {
    assessmentId: '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6',
    status: 'in_progress',
    questionsAsked: overrides.transcript?.length ?? 0,
    transcript: [],
    question: question('q-outstanding'),
    result: undefined,
    ...overrides,
  };
}

const THREE_ANSWERS = [
  answered('q-1', 'rarely'),
  answered('q-2', 'usually'),
  answered('q-3', 'rarely'),
];

describe('where the run is waiting', () => {
  it('puts the outstanding question one past the last answer', () => {
    expect(outstandingPosition(step({ transcript: THREE_ANSWERS }))).toBe(4);
  });

  it('starts at one on a run with nothing answered', () => {
    expect(outstandingPosition(step())).toBe(1);
    // Nothing has arrived yet, and a screen still has to say where it is. One is the only
    // answer that is not a guess about a run it has not read.
    expect(outstandingPosition(undefined)).toBe(1);
  });

  it('is still a position on a questionnaire that has stopped', () => {
    // Every question drawn has been answered and none is outstanding. The player standing
    // at the end stands one past the last answer — the position with no question at it.
    const stopped = step({ transcript: THREE_ANSWERS, question: undefined });

    expect(outstandingPosition(stopped)).toBe(4);
    expect(questionAt(stopped, 4)).toBeUndefined();
  });
});

describe('where the player is standing', () => {
  const run = step({ transcript: THREE_ANSWERS });

  it('follows the end of the run until the player moves', () => {
    // Not a position: it is the absence of one, which is what keeps a player on the
    // question their last answer produced rather than pinned behind it.
    expect(standingPosition(run, undefined)).toBe(4);
  });

  it('stands where they walked to', () => {
    expect(standingPosition(run, 2)).toBe(2);
    expect(standingPosition(run, 1)).toBe(1);
  });

  it('never stands past the end of the run', () => {
    // The case a revision creates: standing on question eight of a run that has just
    // become three answers long. Being pulled to the end is the only reading that leaves
    // the player looking at something that exists.
    expect(standingPosition(step({ transcript: [answered('q-1', 'rarely')] }), 8)).toBe(2);
    expect(standingPosition(run, 4)).toBe(4);
  });

  it('never stands before the first question', () => {
    expect(standingPosition(run, 0)).toBe(1);
    expect(standingPosition(run, -3)).toBe(1);
  });
});

describe('what is drawn at a position', () => {
  const run = step({ transcript: THREE_ANSWERS });

  it('gives an answered question with the option that was chosen', () => {
    expect(questionAt(run, 2)).toEqual({
      position: 2,
      question: question('q-2'),
      answer: 'usually',
    });
  });

  it('gives the outstanding question with no answer against it', () => {
    const outstanding = questionAt(run, 4);

    expect(outstanding?.question.id).toBe('q-outstanding');
    // The distinction the screen renders: an answer to show, or an answer to give.
    expect(outstanding?.answer).toBeUndefined();
  });

  it('has nothing at a position the run does not reach', () => {
    expect(questionAt(run, 5)).toBeUndefined();
    expect(questionAt(run, 0)).toBeUndefined();
  });

  it('has nothing at all while the step is still loading', () => {
    expect(questionAt(undefined, 1)).toBeUndefined();
  });
});

describe('every question already answered', () => {
  it('lists them in the order they were asked, with the option chosen against each', () => {
    const listed = answeredQuestions(step({ transcript: THREE_ANSWERS }));

    // The review's whole content, and the positions it opens the questionnaire at.
    expect(listed.map((entry) => [entry.position, entry.question.id, entry.answer])).toEqual([
      [1, 'q-1', 'rarely'],
      [2, 'q-2', 'usually'],
      [3, 'q-3', 'rarely'],
    ]);
  });

  it('leaves out the question still being asked, which has no answer to review', () => {
    const listed = answeredQuestions(step({ transcript: THREE_ANSWERS }));

    expect(listed.map((entry) => entry.question.id)).not.toContain('q-outstanding');
  });

  it('numbers positions the way the questionnaire moves by them', () => {
    // Not an index. A player opening the second entry has to land on `Question 2`, and an
    // off-by-one here sends them to change the answer beside the one they meant.
    const [first] = answeredQuestions(step({ transcript: THREE_ANSWERS }));

    expect(first?.position).toBe(1);
  });

  it('is empty on a stopped run that answered nothing, and on one still loading', () => {
    // Neither is a list with something missing from it: the first genuinely has no
    // answers, and the second has no run yet.
    expect(answeredQuestions(step({ question: undefined }))).toEqual([]);
    expect(answeredQuestions(undefined)).toEqual([]);
  });

  it('lists the answers of a run that has stopped, which is the case the review exists for', () => {
    // Neither a question nor a result, and every answer still the player's to change.
    const stopped = step({ transcript: THREE_ANSWERS, question: undefined });

    expect(answeredQuestions(stopped)).toHaveLength(3);
  });
});
