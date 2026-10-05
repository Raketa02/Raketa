/**
 * **A pull on the Chats tab re-reads both of its lists**, walked the way a player waiting on
 * somebody else's act walks it: the real route tree, the real shell, the real rows, and only
 * `fetch` faked. Both reads are asked again on the pull, the control spins until both have
 * answered, and what the server now says is what the tab then shows. The control itself —
 * spinning, settling, refusing a second pull in flight — is `ShellScreen.test.tsx`'s.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { RefreshControl } from 'react-native';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  CHALLENGES_PATH,
  CONVERSATIONS_PATH,
  GATE_USER,
  launchIntoClassicPlay,
  stubChallenges,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const READ_AT = '2026-09-12T09:00:00Z';

const PADEL_RATING: Wire['RatingResponse'] = {
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

/** Tomek's send, arriving while the tab is open — the row a pull is for. */
const TOMEKS_SEND: Wire['ChallengeSchema'] = {
  challenge_id: 'ffffffff-0000-4000-8000-000000000006',
  sport: 'PADEL',
  organiser_id: TOMEK,
  standing: 'AWAITING_ANSWERS',
  opened_at: '2026-09-12T08:55:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
    { side: 'B', player_id: ME, answer: null, answer_by: '2026-09-13T08:55:00Z', name: 'me_' },
  ],
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubGames(transport, [], READ_AT);
  stubPlans(transport, []);
  stubConversations(transport, []);
  stubChallenges(transport, [], READ_AT);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function openChats() {
  await launchIntoClassicPlay(transport);
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
}

const control = () => screen.UNSAFE_getByType(RefreshControl);

it('re-reads the challenges and the rooms on a pull, and shows what arrived', async () => {
  await openChats();
  const before = {
    challenges: transport.requestsTo('GET', CHALLENGES_PATH).length,
    rooms: transport.requestsTo('GET', CONVERSATIONS_PATH).length,
  };
  expect(screen.queryByLabelText(/^tomek\.p, Padel/)).toBeNull();
  // The server has moved since the tab was read: Tomek asked.
  stubChallenges(transport, [TOMEKS_SEND], READ_AT);

  await act(async () => {
    fireEvent(control(), 'refresh');
  });

  await waitFor(() => {
    expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBe(before.challenges + 1);
    expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length).toBe(before.rooms + 1);
  });
  expect(await screen.findByLabelText(/^tomek\.p, Padel/)).toBeTruthy();
  await waitFor(() => expect(control().props.refreshing).toBe(false));
});

it('spins until both lists have answered', async () => {
  await openChats();
  let answer: () => void = () => {};
  const held = new Promise<void>((resolve) => {
    answer = resolve;
  });
  transport.on('GET', CONVERSATIONS_PATH, async () => {
    await held;
    return json<Wire['ConversationListResponse']>({ read_at: READ_AT, conversations: [] });
  });

  await act(async () => {
    fireEvent(control(), 'refresh');
  });

  await waitFor(() => expect(control().props.refreshing).toBe(true));
  answer();
  await waitFor(() => expect(control().props.refreshing).toBe(false));
});
