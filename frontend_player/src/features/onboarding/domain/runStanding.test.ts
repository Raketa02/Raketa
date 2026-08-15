import type { AssessmentResult } from './AssessmentResult';
import type { AssessmentStep } from './Assessment';
import { runStanding } from './runStanding';

const QUESTION = {
  id: 'q-played',
  category: 'Recent activity',
  tier: undefined,
  situation: 'Before anything else',
  text: 'Have you played padel before?',
  qualifier: 'Any level counts',
  options: [{ id: 'never', text: 'Never played' }],
};

const RESULT = {
  level: 2.71,
  uncertainty: 0.62,
  confidence: 28,
  confidenceCeiling: 30,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questionsAsked: 2,
  engineVersion: 'racketskill-v3',
  calibrationPriority: 'high',
  confidenceReason: undefined,
  contributions: [],
  wideners: [],
} satisfies AssessmentResult;

function step(over: Partial<AssessmentStep> = {}): AssessmentStep {
  return {
    assessmentId: 'a-1',
    status: 'in_progress',
    questionsAsked: 0,
    transcript: [],
    question: QUESTION,
    result: undefined,
    ...over,
  };
}

it('is asking while a question is outstanding', () => {
  expect(runStanding(step())).toBe('asking');
});

it('is stopped when the run is in progress with neither a question nor a result', () => {
  // The moment #59 made real: the engine has heard enough, and nothing has been rated.
  // Read as *finished* — which is what "no question left" meant before the stop existed —
  // this shows a player a result screen with no result on it.
  expect(runStanding(step({ question: undefined, questionsAsked: 4 }))).toBe('stopped');
});

it('is rated once the run is completed', () => {
  expect(runStanding(step({ status: 'completed', question: undefined, result: RESULT }))).toBe(
    'rated',
  );
});

it('is ended when the run was abandoned, which also has neither', () => {
  // The other run with nothing left to show, and it demands the opposite screen: no
  // rating exists and none is coming.
  expect(runStanding(step({ status: 'abandoned', question: undefined }))).toBe('ended');
});

it('reads a status this build has never heard of as the questionnaire it still is', () => {
  // `toStatus` maps an unknown status to `in_progress` for this reason: the question is
  // what says whether there is something to answer, and a word this build does not know
  // is not grounds for throwing a player out of a run.
  expect(runStanding(step({ status: 'in_progress' as AssessmentStep['status'] }))).toBe('asking');
});

it('says nothing at all about a run that has not loaded', () => {
  // Not a state to route on. A screen that read absence as "stopped" would bounce a
  // player to the review for as long as the first read was in flight.
  expect(runStanding(undefined)).toBeUndefined();
});
