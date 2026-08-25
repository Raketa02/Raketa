/**
 * The onboarding pass's rules, with no renderer, no store and no router.
 *
 * These are the flow's decisions — which sport is this of how many, and where does the
 * player go after it — and every one of them was inside a mounted screen until this
 * module existed. Prior art for the shape is `entryDecision.test` and the sport-queue
 * tests this file replaces.
 */

import {
  admissionTo,
  begin,
  nextDestination,
  positionOf,
  recordRated,
  toggleSport,
  type OnboardingPass,
} from './onboardingPass';

const PADEL_RUN = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const TENNIS_RUN = 'b7c8d9e0-1f2a-4b3c-8d4e-5f6a7b8c9d0e';

/**
 * The two players a destination can be asked about: one who has finished onboarding's
 * second part, and one who has not.
 *
 * `SET_UP` is also what a launch that has not answered the question yet reads as — the
 * fail-safe direction, because the closing screens lead to the app and the entry gate there
 * has the last word.
 */
const SET_UP = { hasPlayerProfile: true };
const NOT_SET_UP = { hasPlayerProfile: false };

/** A pass over these sports with those runs already rated, built the way the app builds it. */
function passOver(queue: readonly ('padel' | 'tennis' | 'squash')[]): OnboardingPass {
  return begin(queue);
}

describe('beginning a pass', () => {
  it('takes the sports chosen, in the order they were chosen, with nothing rated', () => {
    expect(begin(['tennis', 'padel'])).toEqual({ queue: ['tennis', 'padel'], rated: [] });
  });

  it('discards what an earlier pass produced', () => {
    const first = recordRated(passOver(['padel']), { assessmentId: PADEL_RUN, sport: 'padel' });

    // A new queue is a new walk through onboarding, and the closing screens account for
    // *this* walk. Carrying padel forward would put a sport the player answered nothing
    // about today on a screen saying these are the ratings you just produced.
    expect(begin(['tennis']).rated).toEqual([]);
    expect(first.rated).toHaveLength(1);
  });
});

describe('choosing sports', () => {
  // A queue, not a pass: the picker's selection is a list a player is still building, and
  // calling that a pass is what made "no pass" and "a pass nobody ended" the same value.
  it('keeps the order they were chosen in', () => {
    let queue = toggleSport([], 'tennis');
    queue = toggleSport(queue, 'padel');

    // Not registry order: the first sport tapped is the first assessment, and that is the
    // only thing the order means.
    expect(queue).toEqual(['tennis', 'padel']);
  });

  it('removes a sport that was already chosen', () => {
    expect(toggleSport(['tennis', 'padel', 'squash'], 'padel')).toEqual(['tennis', 'squash']);
  });

  it('does not mutate the queue it was given', () => {
    const queue: readonly ('padel' | 'tennis')[] = ['tennis'];
    toggleSport(queue, 'padel');
    expect(queue).toEqual(['tennis']);
  });
});

describe('recording a rated run', () => {
  it('keeps them in the order they were produced', () => {
    let pass = recordRated(passOver(['padel', 'tennis']), {
      assessmentId: PADEL_RUN,
      sport: 'padel',
    });
    pass = recordRated(pass, { assessmentId: TENNIS_RUN, sport: 'tennis' });

    expect(pass.rated).toEqual([
      { assessmentId: PADEL_RUN, sport: 'padel' },
      { assessmentId: TENNIS_RUN, sport: 'tennis' },
    ]);
  });

  it('records the same run twice as the same pass, not as a second card', () => {
    const once = recordRated(passOver(['padel']), { assessmentId: PADEL_RUN, sport: 'padel' });
    const twice = recordRated(once, { assessmentId: PADEL_RUN, sport: 'padel' });

    expect(twice.rated).toHaveLength(1);
    // The *same* pass, by identity. The result screen records what it is showing, and it
    // shows it again on every refetch and every remount — a new object each time would
    // re-render the screen out from under a player who did nothing.
    expect(twice).toBe(once);
  });
});

describe('position across sports', () => {
  it("counts the sport's place in the queue", () => {
    expect(positionOf(passOver(['tennis', 'padel']), 'padel')).toEqual({ index: 2, total: 2 });
    expect(positionOf(passOver(['tennis', 'padel']), 'tennis')).toEqual({ index: 1, total: 2 });
  });

  it('is unmoved by an abandoned sport, which was still chosen', () => {
    // Dropping it would turn "Rating 2 of 2" into "Rating 1 of 1" as a reward for giving
    // up on the first one.
    const pass = passOver(['tennis', 'padel']);
    nextDestination(pass, 'tennis', SET_UP);

    expect(pass.queue).toEqual(['tennis', 'padel']);
    expect(positionOf(pass, 'padel')).toEqual({ index: 2, total: 2 });
  });

  it('has no position for a sport outside the pass', () => {
    // No longer reachable on a screen — `admissionTo` turns those players away — but it
    // stays the honest answer, and it is *why* they can be turned away rather than drawn
    // a bar with no denominator.
    expect(positionOf(begin([]), 'padel')).toBeUndefined();
    expect(positionOf(passOver(['tennis']), 'padel')).toBeUndefined();
  });

  it('has no position at all when no pass is running', () => {
    expect(positionOf(undefined, 'padel')).toBeUndefined();
  });

  it('reads a resumed run as one of one, through the ordinary rule', () => {
    // The defect this replaced: with nothing ending a pass, a run resumed after a walk
    // that rated two sports was still inside that walk and read "Rating 2 of 2". A resumed
    // run is now a genuine pass of one sport, and needs no special case to say so.
    expect(positionOf(begin(['padel']), 'padel')).toEqual({ index: 1, total: 1 });
  });
});

describe('where the player goes after a sport', () => {
  it('rates the next sport they chose', () => {
    expect(nextDestination(passOver(['tennis', 'padel', 'squash']), 'padel', SET_UP)).toEqual({
      kind: 'rate',
      sport: 'squash',
    });
  });

  it('offers the next sport whether or not this one produced a rating', () => {
    // Abandoning is the player saying stop *to this sport*. The rest of what they chose is
    // still what they chose, so the queue is not edited and the offer does not change.
    expect(nextDestination(passOver(['tennis', 'padel']), 'tennis', SET_UP)).toEqual({
      kind: 'rate',
      sport: 'padel',
    });
  });

  it('offers the next sport before it looks at setting up at all', () => {
    // The second part is what follows the *queue*, not what follows a sport. A player with
    // two sports to go is owed the second of them first.
    expect(nextDestination(passOver(['tennis', 'padel']), 'tennis', NOT_SET_UP)).toEqual({
      kind: 'rate',
      sport: 'padel',
    });
  });

  it('shows the closing screens after the last sport, when setting up is behind them', () => {
    const pass = recordRated(passOver(['padel']), { assessmentId: PADEL_RUN, sport: 'padel' });

    expect(nextDestination(pass, 'padel', SET_UP)).toEqual({ kind: 'closing' });
  });

  it('shows the closing screens even when the last sport is the one that produced nothing', () => {
    // Padel was rated, tennis was abandoned. The done screen accounts for the rating they
    // did make; ending on an abandonment is not a reason to be told none of it.
    const pass = recordRated(passOver(['padel', 'tennis']), {
      assessmentId: PADEL_RUN,
      sport: 'padel',
    });

    expect(nextDestination(pass, 'tennis', SET_UP)).toEqual({ kind: 'closing' });
  });

  it('sends a player with no Player profile into the second part instead', () => {
    // Onboarding is two parts, and the closing screens sit on the far side of the second
    // one: the done screen accounts for the ratings, and it is the commit at the end of the
    // six steps that makes the account true of the account.
    const pass = recordRated(passOver(['padel']), { assessmentId: PADEL_RUN, sport: 'padel' });

    expect(nextDestination(pass, 'padel', NOT_SET_UP)).toEqual({ kind: 'social-steps' });
  });

  it('sends them there after an abandonment just the same', () => {
    // The way out of a sport is the way out of a sport, however the sport ended. What is
    // still owed is owed either way.
    const pass = recordRated(passOver(['padel', 'tennis']), {
      assessmentId: PADEL_RUN,
      sport: 'padel',
    });

    expect(nextDestination(pass, 'tennis', NOT_SET_UP)).toEqual({ kind: 'social-steps' });
  });

  it('goes straight to the app when the pass produced nothing', () => {
    // There is no account to give, the done screen has only its empty state to show, and
    // answering *stop* with two more screens is the wrong response to what was asked.
    expect(nextDestination(passOver(['padel']), 'padel', SET_UP)).toEqual({ kind: 'app' });
  });

  it('goes to the app even with setting up still to do, and lets the gate answer', () => {
    // Nothing was rated *in this pass*, so this rule has nothing to account for and no way
    // to know what an earlier walk produced. The entry gate reads both facts and will turn
    // a player who is genuinely owed the second part into it.
    expect(nextDestination(passOver(['padel']), 'padel', NOT_SET_UP)).toEqual({ kind: 'app' });
  });

  it('goes straight to the app from a sport outside the pass that produced nothing', () => {
    // The resumed run that was abandoned: nothing was chosen, nothing was rated.
    expect(nextDestination(begin([]), 'padel', SET_UP)).toEqual({ kind: 'app' });
  });

  it('goes straight to the app when no pass is running', () => {
    // The same answer as a pass that produced nothing, for the same reason: there is
    // nothing to account for. This is what sends a player who abandons a resumed run into
    // the app rather than to a summary of an earlier walk's ratings.
    expect(nextDestination(undefined, 'padel', SET_UP)).toEqual({ kind: 'app' });
  });

  it('shows the closing screens from a sport outside the pass once something was rated', () => {
    // A deep link into a sport nobody queued, in a pass that already rated one. There is
    // an account to give, so it is still owed.
    const pass = recordRated(passOver(['padel']), { assessmentId: PADEL_RUN, sport: 'padel' });

    expect(nextDestination(pass, 'squash', SET_UP)).toEqual({ kind: 'closing' });
  });
});

describe('being admitted to a questionnaire', () => {
  // Onboarding happens once, at the beginning: there is no re-take from inside the app,
  // so the only ways onto a question are the picker's queue and the gate resuming an
  // unfinished run.
  it('admits a sport that is in the pass', () => {
    expect(admissionTo(passOver(['padel', 'tennis']), 'tennis')).toEqual({ kind: 'admit' });
  });

  it('begins a pass of one sport when none is running, which is the resumed run', () => {
    expect(admissionTo(undefined, 'padel')).toEqual({ kind: 'begin' });
  });

  it('starts a player over when a pass is running without this sport', () => {
    // The link nobody in this app can produce: a well-formed URL naming a sport that was
    // never chosen, arriving mid-walk. There is no honest progress to draw for it.
    expect(admissionTo(passOver(['padel']), 'squash')).toEqual({ kind: 'start-over' });
  });

  it('is unmoved by what the pass has already rated', () => {
    // Admission is about the queue, not about outcomes: a sport whose run was abandoned
    // was still chosen, and it keeps its place.
    const pass = recordRated(passOver(['padel', 'tennis']), {
      assessmentId: PADEL_RUN,
      sport: 'padel',
    });

    expect(admissionTo(pass, 'padel')).toEqual({ kind: 'admit' });
    expect(admissionTo(pass, 'tennis')).toEqual({ kind: 'admit' });
    expect(admissionTo(pass, 'squash')).toEqual({ kind: 'start-over' });
  });
});
