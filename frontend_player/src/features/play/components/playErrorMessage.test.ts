/**
 * The `code` table over the recovery fallback, for the six refusals a Play surface can meet.
 *
 * What is asserted here is not the wording — copy changes — but the two things that would
 * stop being true silently: that a refusal with a **remedy** says the remedy, and that the
 * four 503s say **one** sentence, because the platform's four ways of being unable to answer
 * are one fact to somebody holding a phone.
 */

import { AppError } from '@/shared/errors';

import { playErrorMessage } from './playErrorMessage';

function refusal(code: string, recovery: AppError['recovery'] = 'business-conflict'): AppError {
  return new AppError('conflict', recovery, 'a diagnostic nobody reads', { code });
}

/** A 503, classified the way `mapError` really classifies one. */
function outage(code: string): AppError {
  return new AppError('server', 'retryable-automatically', 'a diagnostic nobody reads', { code });
}

const OUTAGES = [
  'matchmaking_unavailable',
  'gate_data_unavailable',
  'index_too_stale',
  'search_not_recorded',
] as const;

describe('the refusals a player can do something about', () => {
  it('sends an orphaned line-up back to the search rather than to "our end"', () => {
    // The whole reason this table exists over the fallback: `404` maps to `terminal`, which
    // renders "Something went wrong at our end" for a state whose actual remedy is to run
    // the search again.
    const said = playErrorMessage(refusal('search_not_found', 'terminal'));

    expect(said).not.toBe(
      playErrorMessage(new AppError('not-found', 'terminal', 'unrecognised', { code: 'nope' })),
    );
    expect(said.toLowerCase()).toContain('search');
  });

  it('names no cause on an orphaned line-up — one code carries four of them', () => {
    // The search does not exist, it is somebody else's, it was for another sport, or it never
    // showed one of these people. Telling them apart would answer questions about strangers
    // one probe at a time, and a sentence that guessed would be answering them for the server.
    const said = playErrorMessage(refusal('search_not_found', 'terminal')).toLowerCase();

    for (const cause of ['blocked', 'someone else', 'somebody else', 'sport']) {
      expect(said).not.toContain(cause);
    }
  });

  it('gives each refusal about you its own sentence', () => {
    const said = [
      'sport_not_rated',
      'play_intent_not_declared',
      'player_profile_not_committed',
      'account_held',
    ].map((code) => playErrorMessage(refusal(code)));

    expect(said.every((sentence) => sentence.length > 0)).toBe(true);
    expect(new Set(said).size).toBe(said.length);
  });
});

describe('the platform being unable to answer', () => {
  it('says one sentence for every 503, distinguished only in the log', () => {
    const said = OUTAGES.map(outage).map(playErrorMessage);

    expect(new Set(said).size).toBe(1);
  });

  it('says it is us and it will pass, without naming a mechanism', () => {
    const said = playErrorMessage(outage('matchmaking_unavailable'));

    for (const internals of ['engine', 'index', 'gate', 'record']) {
      expect(said.toLowerCase()).not.toContain(internals);
    }
  });

  it('stops blaming the player’s connection for a server that answered', () => {
    // `mapError` classifies every 5xx as `retryable-automatically`, whose fallback sentence
    // is "We couldn't reach Raketa. Check your connection and try again" — false of a 503,
    // which is Raketa reached and answering.
    const reached = playErrorMessage(outage('index_too_stale')).toLowerCase();

    expect(reached).not.toContain('connection');
    expect(reached).not.toContain("couldn't reach");
  });
});

describe('under the table', () => {
  it('falls through to the recovery category for a code this build has never seen', () => {
    // Old app versions live on real phones for months. A code added after this build shipped
    // still says something true about what to do next.
    expect(playErrorMessage(refusal('a_code_from_next_year'))).toBe(
      playErrorMessage(new AppError('conflict', 'business-conflict', 'x')),
    );
  });

  it('never renders the backend’s own message', () => {
    expect(playErrorMessage(refusal('search_not_found'))).not.toContain(
      'a diagnostic nobody reads',
    );
  });
});
