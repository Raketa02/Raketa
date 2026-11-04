/**
 * **The naming, from the You tab** — the *Nickname* row and the screen behind it, walked through
 * the real route tree with only `fetch` faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7; [ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 *
 * The step's own suite proves the form — what is refused before a round trip, what the server
 * refuses, that the player is re-read before anything moves. What is proved here is what the
 * row adds: the row says the nickname, the box opens **pre-filled**, *Save* is the same act, a
 * taken handle is refused in the app's sentence under the box **on the tab too**, a save that
 * landed leaves the screen where it is with *Save* green and saying *Saved* over the re-read (6.1
 * `settled`, amended 2026-09-18), and the new nickname is what the row and the header card say on
 * the way back.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import { fillOf } from '@/test-support/drawn';
import {
  GATE_USER,
  launchSignedIn,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { NICKNAME_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { NICKNAME_LABEL } from './namingPresentation';
import { NICKNAME_ROW_TITLE, SAVE_NICKNAME } from './nicknamePresentation';

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

const NAMING_PATH = '/api/v1/users/me/name';
const ME_PATH = '/api/v1/users/me';

/** Ania, as she named herself at the step. */
const NICKNAME = 'ania.k';
/** What she renames herself to from You. */
const RENAMED = 'ak.padel';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  stubGate(transport, { nickname: NICKNAME, ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

const nicknameRow = (nickname: string) => doorRowLabel(NICKNAME_ROW_TITLE, nickname);

async function openNickname() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(nicknameRow(NICKNAME)));
  await screen.findByRole('header', { name: NICKNAME_ROW_TITLE });
}

describe('the Nickname row', () => {
  it('says the nickname, whole and without an @', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    expect(await screen.findByLabelText(nicknameRow(NICKNAME))).toBeTruthy();
    expect(screen.queryByText(`@${NICKNAME}`)).toBeNull();
    expect(screen.queryByText('Name')).toBeNull();
  });

  it('opens one box pre-filled with the nickname as read, no hint under it, and offers Save', async () => {
    await openNickname();

    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe(NICKNAME);
    expect(screen.queryByLabelText('Name')).toBeNull();
    // The rule is the box's error, drawn only when it is broken (ADR-0199 §3).
    expect(screen.queryByText(NICKNAME_RULE)).toBeNull();
    // Nothing has changed, and the button says so rather than merely being grey — and is
    // green, whole, because the state is the message.
    expect(screen.getByLabelText(SAVE_NICKNAME.savedLabel).props.accessibilityState?.disabled).toBe(
      true,
    );
    expect(fillOf(screen.getByLabelText(SAVE_NICKNAME.savedLabel))).toBe(theme.color.mintInk);
    // No question over the box: the step's title does not need repeating on an edit.
    expect(screen.queryByText('How should people see you?')).toBeNull();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), RENAMED);
    expect(screen.getByLabelText(SAVE_NICKNAME.label).props.accessibilityState?.disabled).toBe(
      false,
    );
    expect(fillOf(screen.getByLabelText(SAVE_NICKNAME.label))).toBe(theme.color.coralInk);
  });

  it('saves the nickname alone, re-reads the player, stays under Saved, and the tab says the new one', async () => {
    transport.on('PUT', NAMING_PATH, () => {
      // The server, once the naming is recorded: the same account, renamed.
      transport.on('GET', ME_PATH, () =>
        json<Wire['MeResponse']>({
          ...GATE_USER,
          nickname: RENAMED,
          has_player_profile: true,
        }),
      );
      return json<Wire['NamingResponse']>({ nickname: RENAMED });
    });
    await openNickname();
    const readsBefore = transport.requestsTo('GET', ME_PATH).length;

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), ` ${RENAMED} `);
    fireEvent.press(screen.getByLabelText(SAVE_NICKNAME.label));

    await waitFor(() => expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(1));
    // A nickname, and nothing else — trimmed, as the server's value object trims it.
    expect(transport.requestsTo('PUT', NAMING_PATH)[0]?.body).toEqual({ nickname: RENAMED });
    // Re-read, and the screen stays, under a *Save* gone green with nothing left to send.
    await waitFor(() => expect(transport.requestsTo('GET', ME_PATH).length).toBe(readsBefore + 1));
    expect(await screen.findByLabelText(SAVE_NICKNAME.savedLabel)).toBeTruthy();
    expect(screen).toHavePathname('/you/name');
    expect(fillOf(screen.getByLabelText(SAVE_NICKNAME.savedLabel))).toBe(theme.color.mintInk);
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe(RENAMED);

    // And the tab says the re-read on the way back: the row, and the header card large.
    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(await screen.findByLabelText(nicknameRow(RENAMED))).toBeTruthy();
    expect(screen.getAllByText(RENAMED)).toHaveLength(2);
    expect(screen.queryByText(NICKNAME)).toBeNull();
  });

  it('refuses a taken nickname in the app’s own sentence under the box, and stays', async () => {
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
    await openNickname();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'marek');
    fireEvent.press(screen.getByLabelText(SAVE_NICKNAME.label));

    expect(await screen.findByText('That nickname is taken. Pick another.')).toBeTruthy();
    expect(screen).toHavePathname('/you/name');
    expect(screen.queryByText(NICKNAME_RULE)).toBeNull();
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe('marek');
  });

  it('refuses a handle with a space in it before a round trip, the rule drawn as the error', async () => {
    await openNickname();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'ania k');
    fireEvent.press(screen.getByLabelText(SAVE_NICKNAME.label));

    expect(await screen.findByText(NICKNAME_RULE)).toBeTruthy();
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
  });

  it('goes back to the tab without saving, and the row is as it was', async () => {
    await openNickname();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'somebody.else');
    fireEvent.press(screen.getByLabelText('Back'));

    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
    expect(await screen.findByLabelText(nicknameRow(NICKNAME))).toBeTruthy();
  });
});
