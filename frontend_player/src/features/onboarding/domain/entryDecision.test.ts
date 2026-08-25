/**
 * The entry gate's rule, with no renderer and no network.
 *
 * These cases are the whole of "where does a player belong on launch", and each one is a
 * decision someone could plausibly get backwards.
 */

import type { AssessmentRun } from './Assessment';
import { entryDestination } from './entryDecision';
import type { SkillRating } from './SkillRating';
import type { Sport } from './Sport';

function rating(sport: Sport): SkillRating {
  return {
    sport,
    level: 2.71,
    uncertainty: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engineVersion: 'racketskill-v3',
    updatedAt: '2026-08-14T09:00:00Z',
  };
}

const RUN: AssessmentRun = {
  assessmentId: '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6',
  sport: 'tennis',
};

/** Nothing set aside — the ordinary launch, and the default for most of these. */
const NONE_DEFERRED: readonly string[] = [];

describe('where a player belongs on launch', () => {
  it('sends a player with no ratings to the welcome screen', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('sends a rated player into the app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'app' });
  });

  it('resumes an unfinished run', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });

  it('resumes an unfinished run even when the player is already rated elsewhere', () => {
    // The case the ordering exists for: rated at padel, half way through tennis. Reading
    // ratings first would drop them into the app with those tennis answers stranded, and
    // nothing would ever offer them the rest of the questionnaire.
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });
});

describe('a run the player asked to come back to later', () => {
  it('is not resumed, so leaving the questionnaire is actually leaving it', () => {
    // Without this the exit is not an exit: the run is genuinely still unfinished, so the
    // gate would route straight back to the question the player just left.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('lets a player rated elsewhere reach the app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'app' });
  });

  it('does not stand in for a different run', () => {
    // Deferral is about one run, not about onboarding. A tennis run set aside says
    // nothing about the squash run the player started afterwards.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: ['a-different-assessment'],
        hasPlayerProfile: true,
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });
});

describe('a player with a rating and no Player profile', () => {
  it('is sent to the social steps rather than into the app', () => {
    // The hole ADR-0090 closes. Rating padel, reaching the social steps and killing the
    // app used to leave a player *rated*, so the gate read one fact and dropped them into
    // the app past the second part — permanently, with no route back to it.
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: false,
      }),
    ).toEqual({ kind: 'social-steps' });
  });

  it('is still sent to welcome when nothing has been rated', () => {
    // Order matters, and this is the pair that fixes it. A player with no ratings has not
    // finished the first part, and the second part is only reachable after it — so *no
    // ratings* is answered before *no profile*, and the brand-new account goes to welcome
    // rather than into a part it has not earned.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: false,
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('still resumes an unfinished run first', () => {
    // An unfinished run outranks everything, and that did not change: answers already
    // given must never be stranded behind a screen asking about something else.
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        hasPlayerProfile: false,
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });

  it('reaches the social steps once that run is set aside', () => {
    // *Done for now* with a sport still to go is an ordinary outcome, and it must still
    // lead to a profile — the third user story in the spec. The deferral takes the run out
    // of the gate's way and the next branch is the one that answers.
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
        hasPlayerProfile: false,
      }),
    ).toEqual({ kind: 'social-steps' });
  });
});
