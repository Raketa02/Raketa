/**
 * **What the door where play begins offers** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §2, §5, [#730](https://github.com/Raketa02/Raketa/issues/730)) — with no renderer and no
 * network: the picker for a player with nothing left halfway, and the run itself, at the question
 * she is on, for one who left it.
 */

import type { AssessmentRun, AssessmentStep, Question } from './Assessment';
import { levelDoor } from './levelDoor';

const RUN: AssessmentRun = { assessmentId: '4d5e6f70-8192-4a3b-8c4d-5e6f70819730', sport: 'padel' };

const QUESTION: Question = {
  id: 'q-serve',
  category: 'Serve',
  tier: undefined,
  situation: 'A normal match',
  text: 'How often does your first serve land?',
  qualifier: 'Against players at your level',
  options: [{ id: 'often', text: 'Most of the time' }],
};

function step(overrides: Partial<AssessmentStep>): AssessmentStep {
  return {
    assessmentId: RUN.assessmentId,
    status: 'in_progress',
    questionsAsked: 4,
    transcript: [],
    question: QUESTION,
    result: undefined,
    ...overrides,
  };
}

describe('the door where play begins', () => {
  it('opens the picker for a player with no run left halfway', () => {
    expect(levelDoor(undefined, undefined)).toEqual({ kind: 'start' });
  });

  it('carries on a run left halfway, on the question she is on — four answered, so five', () => {
    expect(levelDoor(RUN, step({ questionsAsked: 4 }))).toEqual({
      kind: 'carry-on',
      run: RUN,
      question: 5,
    });
  });

  it('counts the first question of a run that was opened and never answered as question 1', () => {
    expect(levelDoor(RUN, step({ questionsAsked: 0 }))).toEqual({
      kind: 'carry-on',
      run: RUN,
      question: 1,
    });
  });

  it('carries on a run whose questions have stopped on the last one answered', () => {
    // Every answer is in and nothing is outstanding: the run is at its review, one press from a
    // rating, and still unfinished — so it is still carried on, never begun again.
    expect(levelDoor(RUN, step({ questionsAsked: 7, question: undefined }))).toEqual({
      kind: 'carry-on',
      run: RUN,
      question: 7,
    });
  });

  it('opens the picker when the run turns out to have ended since the list was read', () => {
    // The list of unfinished runs is one read and the run another: a run completed or abandoned
    // on another phone in between is nothing to carry on.
    expect(levelDoor(RUN, step({ status: 'completed', question: undefined }))).toEqual({
      kind: 'start',
    });
    expect(levelDoor(RUN, step({ status: 'abandoned', question: undefined }))).toEqual({
      kind: 'start',
    });
  });
});
