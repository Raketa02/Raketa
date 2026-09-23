/**
 * **The naming, from the You tab** — the *Name* row and the screen behind it, walked through
 * the real route tree with only `fetch` faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7).
 *
 * The step's own suite proves the form — what is refused before a round trip, what the server
 * refuses, that the player is re-read before anything moves. What is proved here is what the
 * row adds: the boxes open **pre-filled**, *Save* is the same act, a taken handle is refused in
 * the app's sentence under the box **on the tab too**, a save that landed leaves the screen
 * where it is with *Save* green and saying *Saved* over the re-read (6.1 `settled`, amended
 * 2026-09-18), and it is what the row and the header say on the way back.
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
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { NICKNAME_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import { NAME_ROW_TITLE, SAVE_NAME, nameLine } from './namePresentation';
import { NAME_LABEL, NICKNAME_LABEL } from './namingPresentation';

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

const NAME = GATE_USER.name ?? '';
const NICKNAME = GATE_USER.nickname ?? '';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

async function openName() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(
    await screen.findByLabelText(doorRowLabel(NAME_ROW_TITLE, nameLine(NAME, NICKNAME))),
  );
  await screen.findByRole('header', { name: NAME_ROW_TITLE });
}

describe('the Name row', () => {
  it('opens the two boxes pre-filled with the player as read, and offers Save', async () => {
    await openName();

    expect(screen.getByLabelText(NAME_LABEL).props.value).toBe(NAME);
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe(NICKNAME);
    expect(screen.getByText(NICKNAME_RULE)).toBeTruthy();
    // Nothing has changed, and the button says so rather than merely being grey — and is
    // green, whole, because the state is the message.
    expect(screen.getByLabelText(SAVE_NAME.savedLabel).props.accessibilityState?.disabled).toBe(
      true,
    );
    expect(fillOf(screen.getByLabelText(SAVE_NAME.savedLabel))).toBe(theme.color.mintInk);
    // No question over the boxes: the step's title does not need repeating on an edit.
    expect(screen.queryByText('How should people see you?')).toBeNull();

    fireEvent.changeText(screen.getByLabelText(NAME_LABEL), 'Ada K');
    expect(screen.getByLabelText(SAVE_NAME.label).props.accessibilityState?.disabled).toBe(false);
    expect(fillOf(screen.getByLabelText(SAVE_NAME.label))).toBe(theme.color.coralInk);
  });

  it('saves through the naming act, re-reads the player, stays green under Saved, and the row says the new name', async () => {
    // The server records the name normalised, and the re-read is what every screen then says.
    transport.on('PUT', NAMING_PATH, () =>
      json<Wire['NamingResponse']>({ name: 'Ada King', nickname: 'ada.k' }),
    );
    await openName();
    const readsBefore = transport.requestsTo('GET', ME_PATH).length;

    fireEvent.changeText(screen.getByLabelText(NAME_LABEL), '  Ada   King ');
    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'ada.k');
    fireEvent.press(screen.getByLabelText(SAVE_NAME.label));

    await waitFor(() => expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', NAMING_PATH)[0]?.body).toEqual({
      name: 'Ada King',
      nickname: 'ada.k',
    });
    // Re-read, and the screen stays: the stub still answers the gate's name, and that is what
    // the boxes then hold — the route's answer written into the cache is the server's re-read,
    // never the box — under a *Save* gone green with nothing left to send.
    await waitFor(() => expect(transport.requestsTo('GET', ME_PATH).length).toBe(readsBefore + 1));
    expect(await screen.findByLabelText(SAVE_NAME.savedLabel)).toBeTruthy();
    expect(screen).toHavePathname('/you/name');
    expect(fillOf(screen.getByLabelText(SAVE_NAME.savedLabel))).toBe(theme.color.mintInk);
    expect(screen.getByLabelText(NAME_LABEL).props.value).toBe(NAME);
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe(NICKNAME);

    // And the row says the re-read on the way back.
    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(
      await screen.findByLabelText(doorRowLabel(NAME_ROW_TITLE, nameLine(NAME, NICKNAME))),
    ).toBeTruthy();
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
    await openName();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'marek');
    fireEvent.press(screen.getByLabelText(SAVE_NAME.label));

    expect(await screen.findByText('That nickname is taken. Pick another.')).toBeTruthy();
    expect(screen).toHavePathname('/you/name');
    // The rule gives way to the refusal under the one box; the boxes hold what was typed.
    expect(screen.queryByText(NICKNAME_RULE)).toBeNull();
    expect(screen.getByLabelText(NICKNAME_LABEL).props.value).toBe('marek');
  });

  it('refuses a handle with a space in it before a round trip, in the rule’s own words', async () => {
    await openName();

    fireEvent.changeText(screen.getByLabelText(NICKNAME_LABEL), 'ada k');
    fireEvent.press(screen.getByLabelText(SAVE_NAME.label));

    expect(await screen.findByText(NICKNAME_RULE)).toBeTruthy();
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
  });

  it('goes back to the tab without saving, and the row is as it was', async () => {
    await openName();

    fireEvent.changeText(screen.getByLabelText(NAME_LABEL), 'Somebody Else');
    fireEvent.press(screen.getByLabelText('Back'));

    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(transport.requestsTo('PUT', NAMING_PATH)).toHaveLength(0);
    expect(
      await screen.findByLabelText(doorRowLabel(NAME_ROW_TITLE, nameLine(NAME, NICKNAME))),
    ).toBeTruthy();
  });
});
