/**
 * **A new person's walk into the app** — sign-up, the naming and the profile steps, up to the
 * gender step's *Finish*: what a link opened before the account existed waits through
 * ([#520](https://github.com/Raketa02/Raketa/issues/520) story 48, walked for a group link;
 * [#756](https://github.com/Raketa02/Raketa/issues/756), for a friend link).
 *
 * Each screen of it is its own suite's; a link suite walks it to prove the link outlives every one of
 * them. No questionnaire on the way: a level is asked where play begins (ADR-0200 §1, #730).
 *
 * **Starts on sign-in, signed out**, with the gate already serving an unnamed account at `email`
 * (`stubGate(transport, { email, nickname: null })`, and the profile surface's two reads). Serves the
 * server's answer to each step as it is given, and stops on the gender step with *Woman* chosen —
 * the suite presses **Finish**, the way into the app, once it has checked nothing was answered on
 * the way.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { GATE_USER, stubGate, stubLocation } from './onboardingRouter';
import { fakeLocation } from './platform';
import { json, type Transport, type Wire } from './transport';

export interface NewAccount {
  readonly email: string;
  readonly nickname: string;
}

export async function walkANewAccountToFinish(
  transport: Transport,
  { email, nickname }: NewAccount,
): Promise<void> {
  const created = { ...GATE_USER, email, nickname: null };

  stubLocation(fakeLocation({ fix: { latitude: 50.06, longitude: 19.94, accuracyMetres: 12 } }));
  transport.on('POST', '/api/v1/users', () => json<Wire['UserResponse']>(created, 201));
  transport.on('POST', '/api/v1/auth/login', () =>
    json<Wire['TokenResponse']>({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      expires_in: 900,
    }),
  );
  transport.on('PUT', '/api/v1/users/me/name', () => {
    stubGate(transport, { email, nickname });
    return json<Wire['NamingResponse']>({ nickname });
  });
  transport.on('POST', '/api/v1/players/me/profile', () => {
    stubGate(transport, { email, nickname, hasPlayerProfile: true });
    return json<Wire['PlayerProfileResponse']>(
      {
        player_id: GATE_USER.id,
        social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
        photo_ids: [],
        weekly_hours: [{ day: 3, hour: 19 }],
        location: { latitude: 50.06, longitude: 19.94 },
        created_at: '2026-09-26T10:00:00Z',
        updated_at: '2026-09-26T10:00:00Z',
      },
      201,
    );
  });

  // Sign-up.
  fireEvent.press(screen.getByLabelText('Create an account'));
  await waitFor(() => expect(screen).toHavePathname('/sign-up'));
  fireEvent.changeText(screen.getByLabelText('Email'), email);
  fireEvent.changeText(screen.getByLabelText('Password'), 'backhand42');
  fireEvent.changeText(screen.getByLabelText('Repeat password'), 'backhand42');
  fireEvent.press(screen.getByLabelText('I am 18 or over'));
  fireEvent.press(screen.getByLabelText('Create account'));

  // The naming.
  await waitFor(() => expect(screen).toHavePathname('/name'));
  fireEvent.changeText(screen.getByLabelText('Nickname'), nickname);
  fireEvent.press(screen.getByLabelText('Continue'));

  // The profile steps, straight after the naming.
  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/intro'));
  fireEvent.press(screen.getByLabelText('Next'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/availability'));
  fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
  fireEvent.press(screen.getByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/location'));
  fireEvent.press(screen.getByLabelText('Use my location'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/gender'));
  fireEvent.press(screen.getByLabelText('Woman'));
}
