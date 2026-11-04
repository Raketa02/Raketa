/**
 * The entry gate's rule, with no renderer and no network.
 *
 * These cases are the whole of "where does a player belong on launch", and each one is a
 * decision someone could plausibly get backwards.
 */

import type { AssessmentRun } from './Assessment';
import { entryDestination, type EntryInput } from './entryDecision';
import type { SkillRating } from './SkillRating';
import type { Sport } from '@/shared/vocabulary/sport';

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

/** What every signed-up account holds: it acts as a player and runs no club's groups. */
const A_PLAYER: EntryInput['profiles'] = { actsAsPlayer: true, administers: [] };

const OGRODY = { clubId: 'c0000000-0000-4000-8000-000000000001', clubName: 'Ogrody 33' };
const BONARKA = { clubId: 'c0000000-0000-4000-8000-000000000002', clubName: 'Bonarka Arena' };

/** Nothing set aside — the ordinary launch, and the default for most of these. */
const NONE_DEFERRED: readonly string[] = [];

describe('where a player belongs on launch', () => {
  it('sends a player with no ratings to the welcome screen', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('sends a rated player into the app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'app' });
  });

  it('resumes an unfinished run', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'welcome' });
  });

  it('lets a player rated elsewhere reach the app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
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
        named: true,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'social-steps' });
  });
});

/**
 * **An account with no nickname goes to the naming step before anything else**
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). Sign-up
 * creates the account with none and every destination after this one says the player's nickname,
 * so it is the first thing the gate asks — and it asks it of every shape, including the ones the
 * flow cannot produce, because a shape the gate does not route is a loop.
 */
describe('an account with no nickname yet', () => {
  it('is sent to the naming step, ahead of welcome', () => {
    // The ordinary case: signed up, closed the app before naming themselves, launched again.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'naming' });
  });

  it('is sent to the naming step ahead of an unfinished run', () => {
    // The flow cannot produce this — the naming step precedes welcome — but the gate does not
    // assume it away. The run is not lost: it is still unfinished, and the launch after the
    // naming resumes it.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: false,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'naming' });
  });

  it('is sent to the naming step ahead of the app, whatever else they hold', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: true,
        profiles: A_PLAYER,
      }),
    ).toEqual({ kind: 'naming' });
  });
});

/**
 * **The account's profiles are read ahead of every onboarding destination**
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §3). An account that only runs a club's groups has not asked to play: it goes to its
 * administrator area and never to onboarding — whatever its name, ratings or runs say.
 */
describe('an account that holds only administrator profiles', () => {
  const ADMINISTRATOR_ONLY: EntryInput['profiles'] = {
    actsAsPlayer: false,
    administers: [OGRODY],
  };

  it('is sent to the administrator area of its club', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        // An account an Invitation opened: the club typed a name, and nobody chose a nickname.
        named: true,
        hasPlayerProfile: false,
        profiles: ADMINISTRATOR_ONLY,
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('is sent there ahead of the naming step, and never into onboarding', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: false,
        profiles: ADMINISTRATOR_ONLY,
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens on the first club it administers, in the server’s order', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: true,
        hasPlayerProfile: false,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
      }),
    ).toEqual({ kind: 'administrator', clubId: BONARKA.clubId });
  });

  // Two profiles open in Player by default (ADR-0185 §3).
  it('does not take an account that also plays out of the player’s app', () => {
    expect(
      entryDestination({
        ratings: [rating('padel')],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: true,
        hasPlayerProfile: true,
        profiles: { actsAsPlayer: true, administers: [OGRODY] },
      }),
    ).toEqual({ kind: 'app' });
  });
});

/**
 * **An account with no profile at all is offered the player setup, from the Adult attestation**
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §3, [#517](https://github.com/Raketa02/Raketa/issues/517)). The only way to be one is an
 * administrator-only account whose club removed it: it does not act as a player and runs no
 * club's groups. Signing in again must never be a dead end, so it takes *Start playing*'s steps,
 * from the gate instead of from a row — and the first is the attestation, which it has never given.
 */
describe('an account that holds no profile at all', () => {
  const NO_PROFILE: EntryInput['profiles'] = { actsAsPlayer: false, administers: [] };

  it('is sent to Start playing’s first step, the Adult attestation', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        // The club typed a name, and nobody chose a nickname.
        named: false,
        hasPlayerProfile: false,
        profiles: NO_PROFILE,
      }),
    ).toEqual({ kind: 'start-playing' });
  });

  // Nothing player-side may be reached before the attestation (ADR-0185 §5) — not the naming, and
  // not a run, which the server would refuse `adult_attestation_missing` anyway.
  it('is asked for the attestation ahead of the naming and of anything a player owes', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: false,
        profiles: NO_PROFILE,
      }),
    ).toEqual({ kind: 'start-playing' });
  });
});

/**
 * **Named is holding a nickname** (ADR-0199 §3–§4). An account an Invitation opened holds no
 * player name and no nickname; once it has attested it acts as a player, and the naming step is
 * where it goes first.
 */
describe('an administrator who has just started playing', () => {
  it('is sent to the naming step, holding no nickname yet', () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
        named: false,
        hasPlayerProfile: false,
        profiles: { actsAsPlayer: true, administers: [OGRODY] },
      }),
    ).toEqual({ kind: 'naming' });
  });
});

/**
 * **An account with two profiles opens in the one used last** (ADR-0185 §3, ADR-0188 §2, #518) —
 * which the phone remembers, and which is checked against what the account holds *now*: an
 * administrator profile it no longer holds is Player (ADR-0188 §4), and Player is the default.
 */
describe('an account with two profiles', () => {
  const BOTH: EntryInput['profiles'] = { actsAsPlayer: true, administers: [OGRODY] };
  const IN_THE_APP = {
    ratings: [rating('padel')],
    runInProgress: undefined,
    deferredRunIds: NONE_DEFERRED,
    named: true,
    hasPlayerProfile: true,
  } as const;

  it('opens in the administrator profile it used last', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens in Player when Player was used last', () => {
    expect(
      entryDestination({ ...IN_THE_APP, profiles: BOTH, lastProfile: { kind: 'player' } }),
    ).toEqual({ kind: 'app' });
  });

  it('opens in Player when the club it used last no longer has it', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: BONARKA.clubId },
      }),
    ).toEqual({ kind: 'app' });
  });

  // The profile was chosen, and choosing it is choosing not to be asked a player's questions now:
  // they are still owed, and switching back to Player is where they are asked.
  it('opens in the administrator profile ahead of anything the player side still owes', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        named: false,
        ratings: [],
        profiles: BOTH,
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens an account running two clubs in the one it used last', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
        lastProfile: { kind: 'administrator', clubId: OGRODY.clubId },
      }),
    ).toEqual({ kind: 'administrator', clubId: OGRODY.clubId });
  });

  it('opens an account that does not play on its first club, whatever Player said', () => {
    expect(
      entryDestination({
        ...IN_THE_APP,
        profiles: { actsAsPlayer: false, administers: [BONARKA, OGRODY] },
        lastProfile: { kind: 'player' },
      }),
    ).toEqual({ kind: 'administrator', clubId: BONARKA.clubId });
  });
});
