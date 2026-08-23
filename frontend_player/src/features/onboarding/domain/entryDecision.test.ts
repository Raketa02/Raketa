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
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('sends a rated player into the app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: 'app' });
  });

  it('resumes an unfinished run', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });

  it('parks an unfinished run when the player is already rated elsewhere', () => {
    // **This reverses the original order, and the argument it reversed is still right
    // about its own player.** Resuming whatever else she held was written so that a padel
    // player half way through tennis would not have those answers stranded — and nothing
    // is stranded now, because `ADR-0084` gives Now a door back into a parked run. What
    // the old order cost is the case that decides it: four squash questions answered on a
    // tram standing between her and the padel match she has paid for.
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: 'app' });
  });

  it('resumes it for a player holding no rating at all, however old the run', () => {
    // The first walk through onboarding, for whom there is no app to be kept out of and
    // no door to be shown. Age is not an input here and is not one on the server either:
    // a parked run continues where it stopped, and the questionnaire's own control walks
    // back through the answers (`ADR-0020`).
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
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
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('lets a player rated elsewhere reach the app, deferral or no deferral', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
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
      }),
    ).toEqual({ kind: 'resume', run: RUN });
  });
});
