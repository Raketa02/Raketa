/**
 * ***Start playing*, walked** — an administrator who has never played becomes a player on the same
 * account: the Adult attestation with sign-up's tick box, the naming asking only for the nickname,
 * then the questionnaire and the social steps, and afterwards both profiles
 * ([#517](https://github.com/Raketa02/Raketa/issues/517), PRD #500 story 133, ADR-0185 §3–§5).
 *
 * The real route tree with the socket faked. **The account is a small fake of the server**
 * (`account`): the attestation, the naming, a rating and the committed profile each change what the
 * next `GET /users/me` says, as they would — which is what the entry gate routes by at every step.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchSignedIn,
  NOW_TAB_LINE,
  resetLocation,
  SPORTS_SERVED,
  stubGate,
  stubLocation,
  stubProfileOptions,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import { CLUB, CLUB_ID, club, O3_CLUB_GROUP } from '@/test-support/officialGroupsServer';
import { fakeLocation } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  noContent,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { ADMINISTRATOR_COPY } from './administratorCopy';

const COPY = ADMINISTRATOR_COPY;
const YOU = `/administrator/${CLUB_ID}/you`;

const ATTESTATION_PATH = '/api/v1/users/me/adult-attestation';
const NAMING_PATH = '/api/v1/users/me/name';
const COMMIT_PATH = '/api/v1/players/me/profile';
const PADEL_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const stepPath = `/api/v1/assessments/${PADEL_ID}`;

/** The sentence under the box when it is not ticked — sign-up's own. */
const NOT_ATTESTED = 'Confirm that you are 18 or over — Raketa is for adults only.';

const OGRODY: Wire['AdministeredClubSchema'] = { club_id: CLUB_ID, club_name: CLUB.name };

// ---------------------------------------------------------------------------
// The account, faked
// ---------------------------------------------------------------------------

/**
 * **Marta's account, as the server holds it** — named by the club, no nickname, never attested,
 * running Ogrody 33's groups. Each act below moves it, and `GET /users/me` answers what it holds
 * now: *acts as a player* once it has attested or holds a Player profile (ADR-0185 §2).
 */
function account({
  administers = [OGRODY],
}: { readonly administers?: Wire['AdministeredClubSchema'][] } = {}) {
  const state = {
    attested: false,
    nickname: null as string | null,
    ratings: [] as Wire['RatingResponse'][],
    hasPlayerProfile: false,
  };

  const me = (): Wire['MeResponse'] => ({
    ...GATE_USER,
    email: 'marta@ogrody33.example',
    name: 'Marta Nowak',
    nickname: state.nickname,
    adult_attested: state.attested,
    has_player_profile: state.hasPlayerProfile,
    profiles: {
      acts_as_player: state.attested || state.hasPlayerProfile,
      administers,
      pending_invitations: [],
    },
  });

  return {
    state,
    install(transport: Transport) {
      transport.on('GET', '/api/v1/users/me', () => json(me()));
      transport.on('GET', '/api/v1/ratings', () =>
        json<Wire['RatingsResponse']>({ ratings: [...state.ratings] }),
      );
      transport.on('POST', ATTESTATION_PATH, () => {
        state.attested = true;
        return noContent();
      });
      transport.on('PUT', NAMING_PATH, (request) => {
        const body = request.body as Wire['NameRequest'];
        state.nickname = body.nickname;
        return json<Wire['NamingResponse']>({ name: body.name, nickname: body.nickname });
      });
      transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
      transport.on('POST', '/api/v1/assessments', () => json(outstanding(), 201));
      transport.on('POST', `${stepPath}/answers`, () => {
        transport.on('GET', stepPath, () => json(finished()));
        state.ratings = [PADEL_RATING];
        return json(finished());
      });
      transport.on('POST', COMMIT_PATH, () => {
        state.hasPlayerProfile = true;
        return json(PROFILE, 201);
      });
    },
  };
}

function outstanding(): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: PADEL_ID,
    status: 'in_progress',
    questions_asked: 0,
    transcript: transcriptOf(0),
    question: {
      id: 'q-overhead',
      category: 'Match execution',
      tier: 'standard',
      situation: 'A deep lob pushes you off the net',
      text: 'How often do you play a controlled overhead?',
      qualifier: 'A normal match against players at your level',
      options: [
        { id: 'rarely', text: 'Rarely' },
        { id: 'usually', text: 'Usually' },
      ],
    },
  };
}

const RESULT: Wire['ResultResponse'] = {
  mu: 2.71,
  sigma: 0.62,
  confidence: 30,
  confidence_ceiling: 30,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questions_asked: 1,
  engine_version: 'racketskill-v3',
  calibration_priority: 'standard',
  confidence_reason: {
    key: 'limited-match-evidence',
    sentence: 'We have not seen you play yet, so this is a starting estimate.',
  },
  factors: [],
  uncertainty_factors: [],
};

function finished(): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: PADEL_ID,
    status: 'completed',
    questions_asked: 1,
    transcript: transcriptOf(1),
    question: null,
    result: RESULT,
  };
}

const PADEL_RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: RESULT.mu,
  sigma: RESULT.sigma,
  confidence: RESULT.confidence,
  range: RESULT.range,
  band: RESULT.band,
  status: RESULT.status,
  engine_version: RESULT.engine_version,
  updated_at: '2026-09-26T12:00:00Z',
};

const PROFILE: Wire['PlayerProfileResponse'] = {
  player_id: GATE_USER.id,
  social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
  photo_ids: [],
  availability: [{ day: 3, part: 'EVENING' }],
  location: { latitude: 50.06, longitude: 19.94 },
  search_radius_km: 10,
  proposals_opt_in: {
    accepted: true,
    copy_version: 'proposals-opt-in.v3',
    surface: 'ONBOARDING',
    answered_at: '2026-09-26T12:00:00Z',
  },
  created_at: '2026-09-26T12:00:00Z',
  updated_at: '2026-09-26T12:00:00Z',
};

// ---------------------------------------------------------------------------

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  // The shell's reads, for the moment the walk lands in the app; the account is re-stubbed over them.
  stubGate(transport);
  club([O3_CLUB_GROUP]).install(transport);
  stubProfileOptions(transport);
  stubLocation(
    fakeLocation({ fix: { latitude: 50.0614, longitude: 19.9366, accuracyMetres: 12 } }),
  );
});

afterEach(async () => {
  transport.restore();
  resetLocation();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const attestations = () => transport.requestsTo('POST', ATTESTATION_PATH);
const namings = () =>
  transport.requestsTo('PUT', NAMING_PATH).map((request) => request.body as Wire['NameRequest']);

/** Launch as Marta, open You from the bar, and tap *Start playing*. */
async function startPlaying() {
  const held = account();
  held.install(transport);
  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname(`/administrator/${CLUB_ID}`));
  fireEvent.press(await screen.findByRole('tab', { name: 'You' }));
  await waitFor(() => expect(screen).toHavePathname(YOU));

  fireEvent.press(await screen.findByRole('button', { name: /^Start playing,/ }));

  await waitFor(() => expect(screen).toHavePathname(`${YOU}/start-playing`));
  expect(await screen.findByRole('checkbox', { name: 'I am 18 or over' })).toBeTruthy();
  return held;
}

/** Tick the box and continue — the attestation recorded, and the gate's next step. */
async function attest() {
  fireEvent.press(screen.getByRole('checkbox', { name: 'I am 18 or over' }));
  fireEvent.press(screen.getByRole('button', { name: 'Continue' }));
  await waitFor(() => expect(screen).toHavePathname('/name'));
}

// ---------------------------------------------------------------------------

describe('the Adult attestation', () => {
  it('is Start playing’s first step, with sign-up’s tick box unticked', async () => {
    await startPlaying();

    expect(screen.getByRole('header', { name: 'Start playing' })).toBeTruthy();
    expect(
      screen.getByRole('checkbox', { name: 'I am 18 or over' }).props.accessibilityState,
    ).toEqual({ checked: false, disabled: false });
  });

  it('refuses to go on unticked, in sign-up’s words, and records nothing', async () => {
    await startPlaying();

    fireEvent.press(screen.getByRole('button', { name: 'Continue' }));

    expect(await screen.findByText(NOT_ATTESTED)).toBeTruthy();
    expect(screen).toHavePathname(`${YOU}/start-playing`);
    expect(attestations()).toEqual([]);
  });

  it('records the attestation, and hands the next step to the gate', async () => {
    await startPlaying();

    await attest();

    expect(attestations().map((request) => request.body)).toEqual([{ adult_attested: true }]);
  });

  it('goes back to the You tab untouched', async () => {
    await startPlaying();

    fireEvent.press(screen.getByRole('button', { name: 'Back' }));

    await waitFor(() => expect(screen).toHavePathname(YOU));
    expect(attestations()).toEqual([]);
    expect(screen.getByRole('button', { name: /^Start playing,/ })).toBeTruthy();
  });

  it('says it could not reach Raketa and stays, ticked, when the attestation is not recorded', async () => {
    await startPlaying();
    transport.on('POST', ATTESTATION_PATH, () => errorResponse(503, 'service_unavailable'));

    fireEvent.press(screen.getByRole('checkbox', { name: 'I am 18 or over' }));
    fireEvent.press(screen.getByRole('button', { name: 'Continue' }));

    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen).toHavePathname(`${YOU}/start-playing`);
    expect(
      screen.getByRole('checkbox', { name: 'I am 18 or over' }).props.accessibilityState.checked,
    ).toBe(true);
  });
});

describe('the naming, after the attestation', () => {
  it('asks only for the nickname, and sends the name the club gave with it', async () => {
    await startPlaying();
    await attest();

    expect(screen.queryByLabelText('Name')).toBeNull();
    expect(
      screen.getByText('People will see you as Marta Nowak. Pick a nickname to go with it.'),
    ).toBeTruthy();

    fireEvent.changeText(screen.getByLabelText('Nickname'), 'marta_n');
    fireEvent.press(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(namings()).toEqual([{ name: 'Marta Nowak', nickname: 'marta_n' }]);
  });
});

describe('Start playing, from start to end', () => {
  it('walks the attestation, the nickname, the questionnaire and the social steps into the app, holding both profiles', async () => {
    const held = await startPlaying();
    await attest();

    // The naming: the nickname alone.
    fireEvent.changeText(screen.getByLabelText('Nickname'), 'marta_n');
    fireEvent.press(screen.getByRole('button', { name: 'Continue' }));
    await waitFor(() => expect(screen).toHavePathname('/welcome'));

    // The questionnaire: one sport, one question, one result.
    fireEvent.press(screen.getByLabelText('Get started'));
    await waitFor(() => expect(screen).toHavePathname('/sports'));
    fireEvent.press(await screen.findByLabelText('Padel'));
    fireEvent.press(screen.getByLabelText('Rate 1 sport'));
    fireEvent.press(await screen.findByLabelText('Usually'));
    fireEvent.press(screen.getByLabelText('Confirm answer'));
    await waitFor(() => expect(screen).toHavePathname(`/result/${PADEL_ID}`));
    fireEvent.press(await screen.findByLabelText('See your ratings'));
    await waitFor(() => expect(screen).toHavePathname('/done'));

    // The social steps, into the commit.
    fireEvent.press(await screen.findByLabelText('Finish setting up'));
    await waitFor(() => expect(screen).toHavePathname('/tags'));
    fireEvent.press(await screen.findByLabelText('Plays to win'));
    fireEvent.press(screen.getByLabelText('Here to improve'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/intro'));
    fireEvent.press(screen.getByLabelText('Next'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));
    fireEvent.press(screen.getByLabelText('Wednesday evening'));
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/location'));
    fireEvent.press(screen.getByLabelText('Use my location'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/radius'));
    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/gender'));
    fireEvent.press(screen.getByLabelText('Woman'));
    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/opt-in'));
    fireEvent.press(screen.getByLabelText('Yes — suggest games'));
    fireEvent.press(screen.getByLabelText('Finish — show me players'));
    await waitFor(() => expect(screen).toHavePathname('/data'));
    fireEvent.press(screen.getByLabelText('Start playing'));

    // In the app, as a player.
    expect(await screen.findByText(NOW_TAB_LINE)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(held.state).toEqual({
      attested: true,
      nickname: 'marta_n',
      ratings: [PADEL_RATING],
      hasPlayerProfile: true,
    });

    // **And still an Administrator**: the area opens on the next launch, and its You tab no longer
    // offers Start playing, because the account plays.
    screen.unmount();
    queryClient.clear();
    await launchSignedIn(YOU);
    expect(await screen.findByRole('header', { name: 'Marta Nowak' })).toBeTruthy();
    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Start playing/ })).toBeNull();
  });
});

describe('an account that holds no profile at all', () => {
  // An administrator-only account its club removed (ADR-0185 §3): signing in again is never a
  // dead end, and it takes Start playing's steps from the gate.
  it('is sent to Start playing on launch, with no way back to an area it no longer has', async () => {
    account({ administers: [] }).install(transport);
    // Nothing a player owes the gate is waited on: a run it cannot have is no question to answer.
    transport.on('GET', '/api/v1/assessments/in-progress', neverResponds());

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/start-playing'));
    expect(screen.queryByRole('button', { name: 'Back' })).toBeNull();

    // Once it plays, the gate asks what a player owes it again.
    stubRunsInProgress(transport, []);
    await attest();
    expect(screen.getByLabelText('Nickname')).toBeTruthy();
    expect(screen.queryByLabelText('Name')).toBeNull();
  });
});

describe('an account that holds no profile, and does not want to play', () => {
  // The step is where the gate put it, so a way out has to be on it: signing in again must never
  // be a dead end (ADR-0185 §3), and neither may this.
  it('is offered Sign out on the step, in place of a way back', async () => {
    account({ administers: [] }).install(transport);
    transport.on('POST', '/api/v1/auth/logout', () =>
      json<Wire['LogoutResponse']>({ message: 'Logged out successfully' }),
    );
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/start-playing'));

    fireEvent.press(screen.getByRole('link', { name: 'Sign out' }));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
    expect(attestations()).toEqual([]);
  });

  it('is not offered it when the step was pushed from the You tab, which has its own', async () => {
    await startPlaying();

    expect(screen.queryByRole('link', { name: 'Sign out' })).toBeNull();
  });
});

describe('the You tab’s row', () => {
  it('says what Start playing leads to', async () => {
    account().install(transport);
    await launchSignedIn(YOU);

    expect(
      await screen.findByRole('button', {
        name: `${COPY.you.startPlaying}, ${COPY.you.startPlayingLine}`,
      }),
    ).toBeTruthy();
  });
});
