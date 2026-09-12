/**
 * ***Fill the seat*, walked the way a player walks it from the game screen**: the real route tree,
 * the real shell, the game screen's plan lead, the real builder at its route under the challenge,
 * and only `fetch` faked.
 *
 * [#419](https://github.com/Raketa02/Raketa/issues/419) §1's acceptance criteria for the act are
 * assertions in this file and opinions nowhere else — the control is the primary act on the *Needs
 * a player* arm, above the court's other acts, and only while the agreed moment is ahead; the
 * press runs the challenge screen's own fill, naming the challenge and nothing else, with the
 * people **the game's seats** hold read as accepted; the builder is pushed under the challenge and
 * *back* returns to the game; and a refusal costs the screen what `actRefusal.ts` says. The
 * card's own door is `nowRail.test.tsx`'s.
 *
 * The word is `theActsWords.ts`' — `FILL_THE_SEAT`, the one spelling the card and the control
 * share — and the refusal sentence is `challengeErrorMessage`'s, as it is for every write in this
 * feature.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { endPlaySession } from '@/features/play/types';
import { AppError, offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GAMES_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPlans,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FILL_THE_SEAT } from '@/shared/vocabulary/theActsWords';

import { SEND_CHALLENGE_LABEL } from '../types';

import { CALL_IT_OFF } from './callOffPresentation';
import { challengeErrorMessage } from './challengeErrorMessage';
import { LEAVE_THIS_GAME } from './leaveGamePresentation';

const ME = GATE_USER.id;
const KASIA = 'cccccccc-0000-4000-8000-000000000003';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const DOROTA = 'dddddddd-0000-4000-8000-000000000004';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const LINEUP_ID = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';

const LINEUPS_PATH = '/api/v1/lineups';
const FORECASTS_PATH = '/api/v1/forecasts';
const SEATS_PATH = `/api/v1/challenges/${CHALLENGE}/seats`;

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';

const NAMES: Readonly<Record<string, string>> = {
  [ME]: 'me_',
  [KASIA]: 'kasia_w',
  [TOMEK]: 'tomek.p',
  [DOROTA]: 'dorota_w',
};

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

const THREE: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, nickname: 'me_' },
  { player_id: KASIA, nickname: 'kasia_w' },
  { player_id: TOMEK, nickname: 'tomek.p' },
];

/** A padel four after Marek left: three in, one open. */
const SHORT: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, nickname: 'me_' },
  { side: 'A', player_id: KASIA, nickname: 'kasia_w' },
  { side: 'B', player_id: TOMEK, nickname: 'tomek.p' },
  { side: 'B', player_id: null, nickname: null },
];

const FULL: Wire['GameSchema']['seats'] = [
  ...SHORT.slice(0, 3),
  { side: 'B', player_id: DOROTA, nickname: 'dorota_w' },
];

function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-08T09:00:00Z',
    entry_closes_at: '2026-09-20T09:00:00Z',
    seats: SHORT,
    proposals: [],
    ...over,
  };
}

function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    game_id: GAME,
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    locked_at: null,
    ...over,
  };
}

/** The whole plan, agreed for a day that is still ahead. */
const AHEAD = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-19',
  hour: '18:00',
  agreed_point: '2026-09-19T16:00:00Z',
});

/** The whole plan, agreed for yesterday evening — the moment has passed. */
const PASSED = plan({ ...AHEAD, day: '2026-09-11', agreed_point: '2026-09-11T16:00:00Z' });

function card(playerId: string): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname: NAMES[playerId] ?? 'anon',
      area_code: 'A+050612+0019938',
      social_tags: [],
      level: 3.1,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
  };
}

const ONE_WAY: Wire['ArrangementSchema'] = {
  pairing_id: 1,
  is_current: true,
  is_evenest: true,
  sides: {
    A: [
      { seat_index: 0, relationship: 'SELF', player_id: ME },
      { seat_index: 1, relationship: 'PARTNER', player_id: KASIA },
    ],
    B: [
      { seat_index: 2, relationship: 'OPPONENT', player_id: TOMEK },
      { seat_index: 3, relationship: 'OPPONENT', player_id: DOROTA },
    ],
  },
  forecast: { pct: 78, sigma_group: 0.41, provisional: false, assumption: null },
  split: { your_side: 3.2, their_side: 3.42, gap: -0.22 },
};

/** The fill's answer: the three still in come back as ordinary rows, and Dorota fills the seat. */
const filledCourt = (): Wire['LineupResponse'] => ({
  search: {
    search_id: LINEUP_ID,
    at: '2026-09-12T09:00:05Z',
    surface: 'LINEUP',
    mode: 'FOR_FUN',
    ruleset_version: 'ruleset-v1',
    engine_version: 'matchfit-v1',
    optimised_for: 'GROUP',
    index_stale: false,
    pool: {
      sport: 'PADEL',
      radius_km_used: 12,
      players_in_range: 7,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: [],
    rung_offers: null,
  },
  candidates: [card(KASIA), card(TOMEK), card(DOROTA)],
  lineup: {
    seats: [
      { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
      { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: KASIA },
      { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: TOMEK },
      { side: 'B', seat_index: 3, relationship: 'OPPONENT', player_id: DOROTA },
    ],
    arrangements: [ONE_WAY],
    group_reason: 'EVENEST_ARRANGEMENT',
  },
});

const refusal = (code: string): AppError =>
  new AppError('conflict', 'business-conflict', 'test failure', { code });

let transport: Transport;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  transport.on('POST', LINEUPS_PATH, () => json(filledCourt()));
  transport.on('POST', FORECASTS_PATH, () =>
    json<Wire['ForecastResponse']>({
      arrangements: [ONE_WAY],
      engine_version: 'matchfit-v1',
      ruleset_version: 'ruleset-v1',
    }),
  );
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Every list the screen reads, and the room behind it. */
function stubTheWorld({
  games = [game()],
  plans = [],
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
} = {}) {
  stubGames(transport, games, READ_AT);
  stubPlans(transport, plans);
  stubChallenges(transport, [], READ_AT);
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: GAME,
      sport: 'PADEL',
      members: THREE,
      people: THREE,
      last_entry: null,
    },
  ]);
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: GAME,
    sport: 'PADEL',
    members: THREE,
    people: THREE,
    entries: [],
  });
  stubEntries(transport, ROOM);
  stubPairing(transport, GAME, { refused: 409, code: 'pairing_is_history' });
}

/** In at the screen's own address, pushed from Now so *back* has somewhere to go. */
async function openTheGame(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));
  act(() => router.push(`/games/${GAME}`));
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  await screen.findByText(OPEN_THE_CHAT);
}

/** The press, and where it lands: the builder, already holding the court. */
async function fillTheSeat() {
  fireEvent.press(await screen.findByRole('button', { name: FILL_THE_SEAT }));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE}/fill`));
  await screen.findByRole('button', { name: SEND_CHALLENGE_LABEL });
}

describe('where the control is', () => {
  /** The primary act on this arm: under the chat door, above the court's other acts. */
  it('is the primary act on the Needs a player arm, above Leave this game', async () => {
    await openTheGame({ plans: [AHEAD] });

    const control = await screen.findByRole('button', { name: FILL_THE_SEAT });
    const buttons = screen.getAllByRole('button').map((one) => one.props.accessibilityLabel);

    expect(buttons.indexOf(FILL_THE_SEAT)).toBeGreaterThan(buttons.indexOf(OPEN_THE_CHAT));
    expect(buttons.indexOf(FILL_THE_SEAT)).toBeLessThan(buttons.indexOf(LEAVE_THIS_GAME));
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
    expect(control.props.accessibilityState.busy).toBe(false);
  });

  it('is not drawn on a full court', async () => {
    await openTheGame({ games: [game({ seats: FULL })], plans: [AHEAD] });

    await screen.findByRole('button', { name: LEAVE_THIS_GAME });
    expect(screen.queryByRole('button', { name: FILL_THE_SEAT })).toBeNull();
  });

  /**
   * **Once the moment has passed nobody may be seated into the game** — the send from the
   * builder would be refused with `game_moment_has_passed`, so the door stands down with the
   * leave, mirroring the server off the same instant rather than opening a builder that cannot
   * send.
   */
  it('is not drawn once the agreed moment has passed', async () => {
    await openTheGame({ plans: [PASSED] });

    await screen.findByText(OPEN_THE_CHAT);
    expect(screen.queryByRole('button', { name: FILL_THE_SEAT })).toBeNull();
    expect(screen.queryByRole('button', { name: LEAVE_THIS_GAME })).toBeNull();
  });
});

describe('the fill', () => {
  /** ADR-0150 §2: the fill names the challenge it completes and says nothing else about the court. */
  it('runs the challenge screen’s fill, naming the challenge and nothing else', async () => {
    await openTheGame();
    await fillTheSeat();

    expect(transport.requestsTo('POST', LINEUPS_PATH)).toHaveLength(1);
    expect(transport.requestsTo('POST', LINEUPS_PATH)[0]?.body).toEqual({
      completing_challenge_id: CHALLENGE,
    });
  });

  /**
   * **The people the game's seats hold are read as accepted** — not the challenge's, which is the
   * arrangement as it was sent and may have been re-seated since. An accepted seat is not a
   * control (ADR-0150 §8): no clear badge on Kasia or Tomek, and one on the newcomer alone.
   */
  it('opens the builder with the game’s seated players accepted, and the newcomer clearable', async () => {
    await openTheGame();
    await fillTheSeat();

    expect(screen.queryByRole('button', { name: /^Remove kasia_w/ })).toBeNull();
    expect(screen.queryByRole('button', { name: /^Remove tomek\.p/ })).toBeNull();
    expect(screen.getByRole('button', { name: /^Remove dorota_w/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Start over' })).toBeNull();
  });

  /** The builder is under the challenge, and *back* lands where you left — the game screen. */
  it('pushes the builder under the challenge, and back returns to the game', async () => {
    await openTheGame();
    await fillTheSeat();

    expect(transport.requestsTo('POST', SEATS_PATH)).toEqual([]);

    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
    expect(await screen.findByRole('button', { name: FILL_THE_SEAT })).toBeTruthy();
  });
});

describe('a refused fill', () => {
  /** A stale tap is a re-read, not a toast: the game moved under the finger. */
  it('re-reads the game and says nothing on game_moment_has_passed', async () => {
    transport.on('POST', LINEUPS_PATH, () => errorResponse(409, 'game_moment_has_passed'));

    await openTheGame({ plans: [AHEAD] });
    const games = transport.requestsTo('GET', GAMES_PATH).length;
    // The clock has moved on by the time the refusal is answered.
    stubGames(transport, [game()], '2026-09-19T17:00:00Z');

    fireEvent.press(await screen.findByRole('button', { name: FILL_THE_SEAT }));

    await waitFor(() =>
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(games),
    );
    expect(screen).toHavePathname(`/games/${GAME}`);
    expect(screen.queryByRole('alert')).toBeNull();
    // The re-read lands past the moment, and the door is gone with it.
    await waitFor(() => expect(screen.queryByRole('button', { name: FILL_THE_SEAT })).toBeNull());
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();
  });

  /** A hold is a fact about the account, said where the act was refused. */
  it('says the held note on account_held, and stays', async () => {
    transport.on('POST', LINEUPS_PATH, () => errorResponse(403, 'account_held'));

    await openTheGame();
    fireEvent.press(await screen.findByRole('button', { name: FILL_THE_SEAT }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(challengeErrorMessage(refusal('account_held')))).toBeTruthy();
    expect(screen).toHavePathname(`/games/${GAME}`);
  });

  /** The connection's absence is said once, in amber, and the control is greyed under it. */
  it('greys the control under an amber note when there is no connection', async () => {
    await openTheGame();
    await screen.findByRole('button', { name: FILL_THE_SEAT });

    onlineManager.setOnline(false);

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: FILL_THE_SEAT }).props.accessibilityState.disabled,
      ).toBe(true),
    );
    expect(screen.getAllByText(offlineMessage('does-not-resume')).length).toBeGreaterThan(0);
  });
});
