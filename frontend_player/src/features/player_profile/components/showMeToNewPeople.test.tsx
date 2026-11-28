/**
 * ***Show me to new people* on You, walked the way a player walks it** — the real route tree, the real
 * bar, and only `fetch` faked ([#799](https://github.com/Rakieta02/Rakieta/issues/799); ADR-0204 §2; the
 * Home rows screens §9.1; the words §31.12).
 *
 * The row is the switch: *Show me to new people*, with *Players you don't share a group or a game with
 * can find you on Home, open your record and send you a request.* under it, the last row of *On your
 * card*, on by default. It writes at once, with no *Save*, and a refused write puts it back and says
 * why. It replaced *Show me in General* (#778), whose words are said nowhere any more.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { NICKNAME_ROW_TITLE } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  profileSurface,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

const SWITCH_PATH = '/api/v1/players/me/show-me-to-new-people';
const TITLE = 'Show me to new people';
const SENTENCE =
  "Players you don't share a group or a game with can find you on Home, open your record and send you a request.";

let transport: Transport;

/** The switch's route, as the server keeps it: a write is the profile read's from then on. */
function written(request: { readonly body: unknown }): Response {
  const { on } = request.body as Wire['SetShowMeToNewPeopleRequest'];
  stubProfileSurface(transport, profileSurface({ show_me_to_new_people: on }));
  return noContent();
}

function serve(on = true) {
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport, profileSurface({ show_me_to_new_people: on }));
  stubProfileOptions(transport);
  stubOwnRecord(transport);
}

beforeEach(() => {
  transport = installTransport();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player on the You tab, the profile read in. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  return screen.findByRole('switch', { name: TITLE });
}

const theSwitch = () => screen.getByRole('switch', { name: TITLE });
const isOn = () => theSwitch().props.accessibilityState?.checked;
const writes = () => transport.requestsTo('PUT', SWITCH_PATH);

describe('Show me to new people, on You', () => {
  it('is the last row of On your card, after Nickname, with its sentence under it', async () => {
    serve();
    await onYou();

    expect(screen.getByText(SENTENCE)).toBeTruthy();
    const drawn = screen.getAllByText(/./);
    const at = (text: string) => drawn.indexOf(screen.getByText(text));
    expect(at(NICKNAME_ROW_TITLE)).toBeLessThan(at(TITLE));
    expect(at(TITLE)).toBeLessThan(at(SENTENCE));
    expect(at(SENTENCE)).toBeLessThan(at('Account'));
    // The switch it replaced is said nowhere.
    expect(screen.queryByText('Show me in General')).toBeNull();
  });

  it('is on for a profile that shows itself to new people, and off for one that does not', async () => {
    serve(true);
    await onYou();
    expect(isOn()).toBe(true);

    screen.unmount();
    queryClient.clear();
    serve(false);
    await onYou();
    expect(isOn()).toBe(false);
  });

  it('turns off at once, with no Save — off while the write is out, and off once it lands', async () => {
    serve();
    let land: () => void = () => undefined;
    transport.on(
      'PUT',
      SWITCH_PATH,
      (request) => new Promise<Response>((resolve) => (land = () => resolve(written(request)))),
    );
    await onYou();

    fireEvent.press(theSwitch());

    await waitFor(() => expect(writes()).toHaveLength(1));
    expect(writes()[0]!.body).toEqual({ on: false });
    await waitFor(() => expect(isOn()).toBe(false));
    expect(screen.queryByRole('button', { name: /^Save/ })).toBeNull();

    await act(async () => land());

    await waitFor(() => expect(isOn()).toBe(false));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('turns back on, sending on', async () => {
    serve(false);
    transport.on('PUT', SWITCH_PATH, written);
    await onYou();

    fireEvent.press(theSwitch());

    await waitFor(() => expect(writes()).toHaveLength(1));
    expect(writes()[0]!.body).toEqual({ on: true });
    expect(isOn()).toBe(true);
  });

  it('stays where it was put after the write lands and You is opened again', async () => {
    serve();
    transport.on('PUT', SWITCH_PATH, written);
    await onYou();

    fireEvent.press(theSwitch());
    await waitFor(() => expect(writes()).toHaveLength(1));

    screen.unmount();
    queryClient.clear();
    await onYou();
    expect(isOn()).toBe(false);
  });

  it('goes back when the write is refused, and says why', async () => {
    serve();
    transport.on('PUT', SWITCH_PATH, () => errorResponse(409, 'concurrent_modification'));
    await onYou();

    fireEvent.press(theSwitch());

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(isOn()).toBe(true);
  });
});
