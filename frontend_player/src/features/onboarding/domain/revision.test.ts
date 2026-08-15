/**
 * What a change means and what it costs, with no renderer, no cache and no network.
 *
 * The two rules here are the ones a screen must never restate: the cost a player is told
 * before the change happens, and the tap that means nothing at all. Both are cheap to get
 * subtly wrong — off by one in the count, or a confirmation shown for re-selecting the
 * answer already recorded — and neither is visible in the request that follows.
 */

import type { AnsweredQuestion, AssessmentStep, Question } from './Assessment';
import { proposeRevision } from './revision';

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

const RUN = step({ transcript: THREE_ANSWERS });

describe('proposing a change', () => {
  it('names the question it changes and the option it changes to', () => {
    expect(proposeRevision(RUN, 2, 'rarely')).toEqual({
      questionId: 'q-2',
      optionId: 'rarely',
      discards: 1,
    });
  });

  it('counts the answers after it, and never the one being changed', () => {
    // Three answers. Changing the first discards the two behind it; the first is replaced,
    // not discarded, which is the off-by-one this exists to pin.
    expect(proposeRevision(RUN, 1, 'usually')?.discards).toBe(2);
    expect(proposeRevision(RUN, 2, 'rarely')?.discards).toBe(1);
  });

  it('costs no other answers on the most recent one', () => {
    // A real case, not a degenerate one: nothing else is lost, and it is still a change,
    // because the engine is asked what to do with the transcript this produces.
    expect(proposeRevision(RUN, 3, 'usually')?.discards).toBe(0);
  });
});

describe('what is not a change at all', () => {
  it('is re-selecting the option already recorded', () => {
    // Changing your mind and changing it back. The server records nothing for it, so a
    // client that offered a confirmation here would announce a cost nobody pays.
    expect(proposeRevision(RUN, 2, 'usually')).toBeUndefined();
  });

  it('is a position the run holds no answer at', () => {
    // The outstanding question is answered rather than revised, and there is nothing at
    // all past it — the position a player stands on when the questionnaire has stopped.
    expect(proposeRevision(RUN, 4, 'rarely')).toBeUndefined();
    expect(proposeRevision(RUN, 9, 'rarely')).toBeUndefined();
    expect(proposeRevision(RUN, 0, 'rarely')).toBeUndefined();
  });

  it('is anything at all before the run has arrived', () => {
    expect(proposeRevision(undefined, 1, 'rarely')).toBeUndefined();
  });
});
