/**
 * The naming step — *How should people see you?* — driven through the real route tree and the
 * network boundary.
 *
 * Only `fetch` is faked. The router, the entry gate, the http client, the mappers, the use-case,
 * the mutation, the schema and the screen all run for real, so a pass here means an unnamed
 * account is held at the step, refused in words, and let through once the server has recorded
 * a name — end to end minus the socket
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §3).
 *
 * Every assertion is about what a player can see or what left the device. None reads a store's
 * internals or a hook's return shape.
 */

import { onlineManager } from '@tanstack/react-query';
import { renderRouter } from 'expo-router/testing-library';
import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import {
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  GATE_USER,
  ONBOARDING_ROUTES,
  launchSignedIn,
  stubGate as stubGateWith,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { ADULT_LABEL, NICKNAME_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { CONTINUE, NAME_LABEL, NAMING_TITLE, NICKNAME_LABEL } from './namingPresentation';

const NAMING_PATH = '/api/v1/users/me/name';
const ME_PATH = '/api/v1/users/me';

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

/** What the server records — the name **as normalised**, which is not always what was typed. */
function stubNaming(recorded: Wire['NamingResponse']) {
  transport.on('PUT', NAMING_PATH, () => json(recorded));
}

/** The users context's own refusal: another player holds the handle, and nothing was recorded. */
function stubNicknameTaken() {
  transport.on('PUT', NAMING_PATH, () =>
    json(
      {
        code: 'nickname_already_taken',
        message: 'nickname already taken',
        trace_id: 'trace-test',
        details: { field: 'nickname' },
      } satisfies Wire['ErrorResponse'],
      409,
    ),
  );
}

/** A launch by an account that signed up and never named itself. */
async function launchUnnamed() {
  stubGate({ name: null });
  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/name'));
}

function fillNaming(name = 'Ania Kowalska', nickname = 'ania_k') {
  fireEvent.changeText(screen.getByLabelText(NAME_LABEL), name);
  fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), nickname);
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

// ---------------------------------------------------------------------------
// Where an unnamed account lands
// ---------------------------------------------------------------------------

describe('the entry gate and the naming step', () => {
  /**
   * **The ticket's first sentence, as one walk**: sign up with an email and a password, and be
   * asked *How should people see you?* before anything else. Registration answers an unnamed
   * account, the sign-in opens the session, and the gate's first read of `/me` sends it here.
   */
  it('asks a player who has just signed up how people should see them, before anything else', async () => {
    setSessionStatus('unauthenticated');
    transport.on('POST', '/api/v1/users', () =>
      json<Wire['UserResponse']>({ ...GATE_USER, name: null, nickname: null }, 201),
    );
    transport.on('POST', '/api/v1/auth/login', () =>
      json<Wire['TokenResponse']>({
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );
    stubGate({ name: null });

    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-up' });
    await waitFor(() => expect(screen).toHavePathname('/sign-up'));
    expect(screen.queryByLabelText(NICKNAME_LABEL)).toBeNull();
    fireEvent.changeText(screen.getByLabelText('Email'), 'ania@example.com');
    fireEvent.changeText(screen.getByLabelText('Password'), 'hunter2hunter2');
    fireEvent.changeText(screen.getByLabelText('Repeat password'), 'hunter2hunter2');
    fireEvent.press(screen.getByLabelText(ADULT_LABEL));
    fireEvent.press(screen.getByLabelText('Create account'));

    await waitFor(() => expect(screen).toHavePathname('/name'));
    expect(screen.getByText(NAMING_TITLE)).toBeTruthy();
    expect(screen.queryByText("Let's set you up")).toBeNull();
  });

  it('sends a session whose player has no name to the naming step, and not to welcome', async () => {
    await launchUnnamed();

    expect(screen.getByText(NAMING_TITLE)).toBeTruthy();
    expect(screen.queryByText("Let's set you up")).toBeNull();
    // The two boxes, and the handle's rule stated under its box before anything is typed.
    expect(screen.getByLabelText(NAME_LABEL)).toBeTruthy();
    expect(screen.getByLabelText(NICKNAME_LABEL)).toBeTruthy();
    expect(screen.getByText(NICKNAME_RULE)).toBeTruthy();
  });

  it('passes a named player to welcome without showing the step', async () => {
    stubGate();

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(screen.queryByText(NAMING_TITLE)).toBeNull();
  });

  /**
   * The name is asked before anything else — before an unfinished run, before the app —
   * because every destination after it says the player's name. The flow cannot produce a
   * run by an unnamed account, and the gate routes it anyway rather than looping.
   */
  it('holds an unnamed account at the step even when it holds a rating and a profile', async () => {
    stubGate({
      name: null,
      hasPlayerProfile: true,
      ratings: [
        {
          sport: 'PADEL',
          mu: 2.71,
          sigma: 0.62,
          confidence: 28,
          range: { low: 2.09, high: 3.33 },
          band: { name: 'Established', lower: 2.7, upper: 3.8 },
          status: 'initial_estimate',
          engine_version: 'racketskill-v3',
          updated_at: '2026-08-14T09:00:00Z',
        },
      ],
    });

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname('/name'));
  });
});

// ---------------------------------------------------------------------------
// The step cannot be skipped
// ---------------------------------------------------------------------------

describe("the device's own back button", () => {
  beforeEach(watchHardwareBack);
  afterEach(stopWatchingHardwareBack);

  it('is claimed and refused, so the step is not left', async () => {
    await launchUnnamed();

    expect(pressHardwareBack()).toBe(true);

    // Still here. The screen draws no back control, and the press does what the missing
    // control says rather than something louder — there is nothing under this group an
    // unnamed player may see.
    await waitFor(() => expect(screen).toHavePathname('/name'));
    expect(screen.getByText(NAMING_TITLE)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Submitting the naming
// ---------------------------------------------------------------------------

describe('submitting the naming', () => {
  it('refuses a taken nickname in words under its box, and stays', async () => {
    await launchUnnamed();
    stubNicknameTaken();

    fillNaming();
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    expect(await screen.findByText('That nickname is taken. Pick another.')).toBeTruthy();
    expect(screen).toHavePathname('/name');
    // The rule gives way to the refusal under the one box; it is not drawn twice.
    expect(screen.queryByText(NICKNAME_RULE)).toBeNull();
    // What was typed is still in the boxes — the player changes the handle, not the form.
    expect(screen.getByLabelText(NAME_LABEL).props.value).toBe('Ania Kowalska');
    // And nothing was re-read: a refusal recorded nothing, so there is nothing new to read.
    expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(1);
  });

  it('refuses a handle with a space in it before a round trip, in the rule’s own words', async () => {
    await launchUnnamed();

    fillNaming('Ania Kowalska', 'ania k');
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    expect(await screen.findByText(NICKNAME_RULE)).toBeTruthy();
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
  });

  it('asks for a name when the box is empty, and sends nothing', async () => {
    await launchUnnamed();

    fillNaming('', 'ania_k');
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    expect(await screen.findByText('Enter your name.')).toBeTruthy();
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
  });

  /**
   * **Submits, re-reads `/me`, and only then moves on** — ADR-0171 §3, as routing. The
   * gate's answer for a player who has just named themselves and holds nothing else is
   * welcome, and it is the gate that answers: the step hands the next destination back to
   * the one rule that knows it.
   */
  it('records the name, re-reads the player, and moves on to welcome', async () => {
    await launchUnnamed();
    stubNaming({ name: 'Ania Kowalska', nickname: 'ania_k' });
    // The server, once the naming is recorded: the same account, now named.
    transport.on('GET', ME_PATH, () =>
      json<Wire['MeResponse']>({ ...GATE_USER, name: 'Ania Kowalska', nickname: 'ania_k' }),
    );

    fillNaming();
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(screen.getByText("Let's set you up")).toBeTruthy();

    // Both fields, always: the naming is one act carrying both.
    const [naming] = transport.requestsTo('PUT', NAMING_PATH);
    expect(naming?.body).toEqual({ name: 'Ania Kowalska', nickname: 'ania_k' });
    // Re-read before moving on: the launch's read, and one more after the naming.
    expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(2);
  });

  /**
   * **And only then** — ADR-0171 §3. The naming is recorded and the re-read is in flight; the
   * screen holds until `/me` has answered, because a gate reading the cache a moment early would
   * be reading the player it was about to replace.
   */
  it('holds the step until the re-read has answered, and moves the moment it has', async () => {
    await launchUnnamed();
    stubNaming({ name: 'Ania Kowalska', nickname: 'ania_k' });
    let answer: (response: Response) => void = () => {};
    transport.on(
      'GET',
      ME_PATH,
      () =>
        new Promise<Response>((resolve) => {
          answer = resolve;
        }),
    );

    fillNaming();
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    await waitFor(() => expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(2));
    // Recorded, re-read asked for, and still here — the step, not the gate, is what is waiting.
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(1);
    expect(screen).toHavePathname('/name');
    expect(screen.getByText(NAMING_TITLE)).toBeTruthy();

    answer(json<Wire['MeResponse']>({ ...GATE_USER, name: 'Ania Kowalska', nickname: 'ania_k' }));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
  });

  /**
   * The form trims and collapses before it sends, as the server's value object does, so what
   * leaves the device is what the server would have recorded anyway — and the screen shows no
   * refusal for a name that only *looked* too short.
   */
  it('sends the name trimmed and collapsed, as the server records it', async () => {
    await launchUnnamed();
    stubNaming({ name: 'Ania Kowalska', nickname: 'ania_k' });
    transport.on('GET', ME_PATH, () =>
      json<Wire['MeResponse']>({ ...GATE_USER, name: 'Ania Kowalska', nickname: 'ania_k' }),
    );

    fillNaming('  Ania   Kowalska ');
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    const [naming] = transport.requestsTo('PUT', NAMING_PATH);
    expect(naming?.body).toEqual({ name: 'Ania Kowalska', nickname: 'ania_k' });
  });

  /**
   * **A naming the app could not confirm is not one it moves on from.** The act was recorded;
   * the re-read failed; the screen says so and stays. The act is repeatable — naming yourself
   * with the handle you already hold is admitted — so the second *Continue* is the same request,
   * and this time the re-read answers.
   */
  it('stays when the re-read fails, and the next Continue records and re-reads again', async () => {
    await launchUnnamed();
    stubNaming({ name: 'Ania Kowalska', nickname: 'ania_k' });
    transport.on('GET', ME_PATH, () => errorResponse(503, 'service_unavailable'));

    fillNaming();
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    // A read is retried on its own before it surfaces — the query client's rule for every
    // read, and the re-read is one — so the sentence arrives after the backoff has run out.
    expect(
      await screen.findByText(
        "We couldn't reach Raketa. Check your connection and try again.",
        {},
        { timeout: 15_000 },
      ),
    ).toBeTruthy();
    expect(screen).toHavePathname('/name');
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(1);
    expect(transport.requestsTo('GET', ME_PATH).length).toBeGreaterThan(2);

    transport.on('GET', ME_PATH, () =>
      json<Wire['MeResponse']>({ ...GATE_USER, name: 'Ania Kowalska', nickname: 'ania_k' }),
    );
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    await waitFor(() => expect(screen).toHavePathname('/welcome'));
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(2);
  });

  it('says the platform could not be reached and stays, with the boxes as they were', async () => {
    await launchUnnamed();
    transport.on('PUT', NAMING_PATH, () => errorResponse(503, 'service_unavailable'));

    fillNaming();
    fireEvent.press(screen.getByLabelText(CONTINUE.label));

    // A refusal against no field is the banner's, above the form.
    expect(
      await screen.findByText("We couldn't reach Raketa. Check your connection and try again."),
    ).toBeTruthy();
    expect(screen).toHavePathname('/name');
    expect(screen.getByLabelText(NAME_LABEL).props.value).toBe('Ania Kowalska');
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe('ania_k');
  });
});
