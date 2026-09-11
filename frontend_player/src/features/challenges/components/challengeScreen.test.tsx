/**
 * **The challenge screen, walked the way an invitee walks it**: the real route tree, the real
 * shell, the real inbox row it is opened from, and only `fetch` faked.
 *
 * Most of [#361](https://github.com/Raketa02/Raketa/issues/361)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the arms draw their sentence, the card
 * block is drawn while the arrangement is being decided and at no other time, the two answers
 * name no state the act cannot produce, the reply is the redraw, a stale tap re-reads rather than
 * complaining, offline greys the pair under one note, and an affordance is never removed without
 * the space saying what took it.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { gameKeys } from '@/features/games/types';
import { offlineMessage } from '@/shared/errors';
import {
  CHALLENGES_PATH,
  CONVERSATIONS_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { standingLine, yourAnswerWindowLine } from './challengePresentation';
import { IM_IN, NOT_THIS_TIME, pairingAbsenceLine } from './challengeDetailPresentation';

const ME = GATE_USER.id;
const EWA = 'bbbbbbbb-0000-4000-8000-000000000002';
const CHALLENGE_ID = 'aaaaaaaa-0000-4000-8000-000000000001';

const READ_AT = '2026-09-08T12:00:00Z';
const HOUR = 60 * 60 * 1000;

function at(hours: number): string {
  return new Date(Date.parse(READ_AT) + hours * HOUR).toISOString();
}

const DETAIL_PATH = `${CHALLENGES_PATH}/${CHALLENGE_ID}`;

/**
 * Whom the organiser's sentence would name. The **invitee's** sentences for these two standings
 * name nobody — *You said no*, *Your day ran out* — so this is the payload the fold requires and
 * the words never reach.
 */
const EWA_NAMED = { kind: 'player', nickname: 'ewa.m' } as const;

/** Enough of a rating for the entry gate to let the app through — this suite is not about it. */
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

/** The list's row, which is the only door to the screen — so every walk starts here. */
function row(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return {
    challenge_id: CHALLENGE_ID,
    sport: 'SQUASH',
    organiser_id: EWA,
    standing: 'AWAITING_ANSWERS',
    opened_at: at(-4),
    seats: [
      { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
    ],
    ...over,
  };
}

const A_CARD: Wire['SeatCardSchema'] = {
  person: {
    nickname: 'ewa.m',
    area_code: 'WAW-C',
    level: 2.71,
    band: 'Established',
    range: { low: 2.55, high: 2.87 },
    player_score: 91,
  },
  pairing: {
    fit: 78,
    distance_km: 3,
    terms: [],
    degraded_terms: [],
    concerns: [],
  },
};

function detail(
  over: Partial<Wire['ChallengeDetailResponse']> = {},
): Wire['ChallengeDetailResponse'] {
  return {
    read_at: READ_AT,
    challenge_id: CHALLENGE_ID,
    sport: 'SQUASH',
    organiser_id: EWA,
    standing: 'AWAITING_ANSWERS',
    opened_at: at(-4),
    seats: [
      { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m', card: A_CARD },
      { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
    ],
    ...over,
  };
}

let transport: Transport;

beforeEach(() => {
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  // Now draws the games list, and one test asserts that answering marks it out of date — which
  // needs an entry in the cache to mark.
  stubGames(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app, open Chats, and tap the one row — the walk every assertion here starts with. */
async function openTheChallenge(
  answer: Wire['ChallengeDetailResponse'] = detail(),
  listed: Wire['ChallengeSchema'] = row(),
) {
  stubChallenges(transport, [listed], READ_AT);
  transport.on('GET', DETAIL_PATH, () => json(answer));

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^ewa\.m, Squash/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
}

/**
 * The same screen by its route — the way in for a challenge whose row is no longer on the inbox,
 * which since a no of the reader's own leaves at once is the ordinary way a declined one is seen.
 */
async function openTheChallengeByRoute(
  answer: Wire['ChallengeDetailResponse'],
  listed: Wire['ChallengeSchema'],
) {
  stubChallenges(transport, [listed], READ_AT);
  transport.on('GET', DETAIL_PATH, () => json(answer));

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  act(() => router.push(`/chats/challenge/${CHALLENGE_ID}`));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
}

describe('the arms', () => {
  it('states the standing, in the reader’s own person', async () => {
    await openTheChallenge();

    expect(
      await screen.findByText(
        standingLine({ side: 'invitee', standing: 'AWAITING_ANSWERS', awaiting: 1 }),
      ),
    ).toBeTruthy();
  });

  /**
   * ADR-0143 §8: the card block is drawn while the arrangement is being decided and in no other
   * standing — and *that person is a stranger to you once more the moment they leave*.
   */
  it('draws no card once the challenge has ended', async () => {
    // Ended by the reader's own no, whose row has left the inbox with the tap — so the screen
    // is reached the second way in, a route (#390), which resolves exactly as before.
    await openTheChallengeByRoute(
      detail({
        standing: 'DECLINED',
        seats: [
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
          { side: 'B', player_id: ME, answer: 'DECLINED', nickname: 'me_' },
        ],
      }),
      row({
        standing: 'DECLINED',
        seats: [
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
          { side: 'B', player_id: ME, answer: 'DECLINED', nickname: 'me_' },
        ],
      }),
    );

    expect(
      await screen.findByText(
        standingLine({ side: 'invitee', standing: 'DECLINED', player: EWA_NAMED }),
      ),
    ).toBeTruthy();
    expect(screen.queryByLabelText(/^ewa\.m\. Match score/)).toBeNull();
  });

  /** The arrangement always answers, and the absence is a sentence rather than a refusal. */
  it('answers with the arrangement when there is no pairing to compute', async () => {
    await openTheChallenge(
      detail({
        pairing_absence: 'NOTHING_TO_COMPUTE',
        seats: [
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
          { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
        ],
      }),
    );

    expect(
      await screen.findByText(pairingAbsenceLine('NOTHING_TO_COMPUTE', 'Squash')),
    ).toBeTruthy();
    expect(await screen.findByRole('button', { name: IM_IN })).toBeTruthy();
  });
});

describe('the card block', () => {
  it('draws the person and the pairing as one element, leading with the handle', async () => {
    await openTheChallenge();

    const card = await screen.findByLabelText(/^ewa\.m\. Match score 78\./);

    expect(card).toBeTruthy();
  });

  /** ADR-0140: the segment disappears rather than reading `Score 0`. */
  it('says nothing about a score the platform has not watched', async () => {
    const noScore: Wire['SeatCardSchema'] = {
      ...A_CARD,
      person: { ...A_CARD.person, player_score: undefined },
    };

    await openTheChallenge(
      detail({
        seats: [
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m', card: noScore },
          { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
        ],
      }),
    );

    const card = await screen.findByLabelText(/^ewa\.m\. Match score 78\./);

    expect(String(card.props.accessibilityLabel)).not.toContain('Player Score');
  });
});

describe('the two answers', () => {
  it('offers both to an invitee whose seat is still waiting, and states the deadline', async () => {
    await openTheChallenge();

    expect(await screen.findByRole('button', { name: IM_IN })).toBeTruthy();
    expect(await screen.findByRole('button', { name: NOT_THIS_TIME })).toBeTruthy();
    expect(await screen.findByText(yourAnswerWindowLine('20 hours'))).toBeTruthy();
  });

  /**
   * **The reply is the redraw.** Both routes return the challenge as it now stands, which *is*
   * the server's derived standing — so what the player sees after tapping is what the platform
   * recorded rather than what the phone guessed.
   */
  it('redraws from the reply rather than from a guess', async () => {
    await openTheChallenge();

    transport.on('POST', `${DETAIL_PATH}/accept`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'ON',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
          ],
        }),
      ),
    );

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    expect(await screen.findByText(standingLine({ side: 'invitee', standing: 'ON' }))).toBeTruthy();
  });

  /**
   * §2.4's obligation: **the buttons are replaced by the sentence, never by nothing.** They and
   * the sentence come out of one fold, so there is no render in which one moved and the other
   * did not.
   */
  it('replaces the pair with the sentence rather than with a blank', async () => {
    await openTheChallenge();

    transport.on('POST', `${DETAIL_PATH}/decline`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'DECLINED',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'DECLINED', nickname: 'me_' },
          ],
        }),
      ),
    );

    fireEvent.press(await screen.findByRole('button', { name: NOT_THIS_TIME }));

    expect(
      await screen.findByText(
        standingLine({ side: 'invitee', standing: 'DECLINED', player: EWA_NAMED }),
      ),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: IM_IN })).toBeNull();
  });

  /**
   * A stale tap is a **re-read, not a toast**: the player lands on *Your day ran out*, which is a
   * sentence §13 already owned, and no new copy was written for the refusal.
   */
  it('re-reads and redraws when the window closed under the finger', async () => {
    await openTheChallenge();

    transport.on('POST', `${DETAIL_PATH}/accept`, () =>
      errorResponse(409, 'answer_window_has_passed'),
    );
    transport.on('GET', DETAIL_PATH, () =>
      json(
        detail({
          standing: 'LAPSED',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'LAPSED', answer_by: at(-1), nickname: 'me_' },
          ],
        }),
      ),
    );

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    expect(
      await screen.findByText(
        standingLine({ side: 'invitee', standing: 'LAPSED', player: EWA_NAMED }),
      ),
    ).toBeTruthy();
  });
});

describe('offline', () => {
  /**
   * The shipped pattern exactly: the pair greys out under **one** amber note — not one per
   * button, which would say the same thing twice about one connection — and the sentence is the
   * shared `does-not-resume` value with no third value beside it.
   *
   * **The act fails rather than pausing.** `networkMode: 'always'` is the mechanism and the
   * closed button is the courtesy over it: an answer deferred to the next reconnect can land past
   * a deadline as silence, or arrange a game at a moment nobody was present for.
   */
  it('greys the pair under one note, and says the act will not be sent later', async () => {
    await openTheChallenge();

    const accept = await screen.findByRole('button', { name: IM_IN });
    const decline = await screen.findByRole('button', { name: NOT_THIS_TIME });

    act(() => onlineManager.setOnline(false));

    expect(await screen.findAllByText(offlineMessage('does-not-resume'))).toHaveLength(1);
    expect(accept.props.accessibilityState?.disabled).toBe(true);
    expect(decline.props.accessibilityState?.disabled).toBe(true);
  });
});

describe('the arms with nothing to press', () => {
  /**
   * §2.1: **`ON` has an arm, and the inbox row is what reaches it.** A completed line-up keeps
   * its row while it is news and every row is a door, so this arm is reached the ordinary way.
   * The card is the game's (#324, ADR-0143 §8); the sentence is drawn here and on the row, and
   * by no system line — §3.4 refused the one #324 had given it.
   */
  it('draws the sentence for a completed line-up, and no card and no controls', async () => {
    const everybodyIn = {
      standing: 'ON' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'B' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
      ],
    };

    await openTheChallenge(detail(everybodyIn), row(everybodyIn));

    expect(await screen.findByText(standingLine({ side: 'invitee', standing: 'ON' }))).toBeTruthy();
    expect(screen.queryByRole('button', { name: IM_IN })).toBeNull();
    expect(screen.queryByLabelText(/^ewa\.m\. Match score/)).toBeNull();
  });
});

describe('the two refusals that are not a sentence', () => {
  /**
   * `challenge_not_found` is **one code for two cases** — it is gone, or it was never yours — so
   * there is nothing behind this screen and nowhere to stay. Landing back on the inbox is the
   * honest place to say so.
   */
  it('leaves the screen when the challenge is no longer there', async () => {
    await openTheChallenge();

    transport.on('POST', `${DETAIL_PATH}/accept`, () => errorResponse(404, 'challenge_not_found'));

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
  });

  /**
   * **The neighbours are fetched.** An accept that fills the last seat opens a game and a
   * conversation in the same transaction, in caches the reply says nothing about — so the games
   * list is marked out of date rather than assembled here from a row the server has not
   * described.
   *
   * What is asserted is the **invalidation** and not a request: `GET /games` is not mounted from
   * behind this screen, so it is marked stale and refetches when Now next draws it. Asserting a
   * socket call here would be asserting that the wrong thing happens.
   */
  it('marks the games list out of date, because an accept can have opened one', async () => {
    await openTheChallenge();

    // Seeded rather than mounted: Now is not on screen from behind a pushed challenge, and what
    // is under test is the hook's cache effect rather than which tab happened to draw the list.
    queryClient.setQueryData(gameKeys.list(), []);

    transport.on('POST', `${DETAIL_PATH}/accept`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'ON',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
          ],
        }),
      ),
    );

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    await waitFor(() =>
      expect(queryClient.getQueryState(gameKeys.list())?.isInvalidated).toBe(true),
    );
  });
});

describe('the room an acceptance opens', () => {
  const ROOM = 'cccccccc-0000-4000-8000-000000000007';
  const OLA = 'dddddddd-0000-4000-8000-000000000003';

  const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

  /**
   * The room this challenge opened, as `GET /conversations` lists it once the teller has written
   * it — and, once the teller has been told the game, carrying it.
   */
  const listed = (
    members: readonly Wire['ConversationMemberSchema'][],
    gameId: string | null = null,
  ): Wire['ConversationRowSchema'] => ({
    conversation_id: ROOM,
    challenge_id: CHALLENGE_ID,
    game_id: gameId,
    sport: 'SQUASH',
    members: [...members],
    people: [...members],
    last_entry: null,
  });

  const opened = (members: readonly Wire['ConversationMemberSchema'][]) => {
    stubConversation(transport, {
      read_at: READ_AT,
      conversation_id: ROOM,
      challenge_id: CHALLENGE_ID,
      game_id: null,
      sport: 'SQUASH',
      members: [...members],
      people: [...members],
      entries: [],
    });
    stubEntries(transport, ROOM);
  };

  const EWA_AND_ME = [
    { player_id: EWA, nickname: 'ewa.m' },
    { player_id: ME, nickname: 'me_' },
  ];

  /**
   * **`I'm in` goes to the room, and the room is waited for.** The accept's reply says nothing
   * about a conversation and the room is written off the outbox after it — so the list answers
   * empty at first, and the screen keeps asking until the row is there, then pushes it. What is
   * asserted is the push landing off a **later** read: the first answers still hold nothing.
   *
   * A singles yes is the yes that completes the court, so the reply is `ON` and the row the wait
   * ends on carries the game — which the teller's opening reads for itself.
   */
  it('goes to the room once the list holds it, not on the first read that does not', async () => {
    await openTheChallenge();
    opened(EWA_AND_ME);

    transport.on('POST', `${DETAIL_PATH}/accept`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'ON',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
          ],
        }),
      ),
    );

    // The teller is a delivery behind the reply: the first two reads after the accept find no
    // room, and only the third does.
    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    transport.on('GET', CONVERSATIONS_PATH, () => {
      const since = transport.requestsTo('GET', CONVERSATIONS_PATH).length - before;
      return json<Wire['ConversationListResponse']>({
        read_at: READ_AT,
        conversations: since >= 3 ? [listed(EWA_AND_ME, GAME)] : [],
      });
    });

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`), {
      timeout: 5000,
    });
    expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length - before).toBeGreaterThanOrEqual(
      3,
    );
  });

  /**
   * **A yes that completed the court waits for the room to know its game.** `ON` says a game
   * exists — opened inline with the accept — while the room is told which off the outbox a
   * moment later, and nothing nudges when it is. A push on the first read that listed the room
   * would land in one drawing no plan card; so the row without its game is a door and not yet an
   * arrival, and the push waits for the read that carries it.
   */
  it('waits for the room to carry its game when the yes completed the court', async () => {
    await openTheChallenge();
    opened(EWA_AND_ME);

    transport.on('POST', `${DETAIL_PATH}/accept`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'ON',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
          ],
        }),
      ),
    );

    // The room is listed at once — membership is derived live — and learns its game two reads
    // later, which is the teller's note landing.
    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    transport.on('GET', CONVERSATIONS_PATH, () => {
      const since = transport.requestsTo('GET', CONVERSATIONS_PATH).length - before;
      return json<Wire['ConversationListResponse']>({
        read_at: READ_AT,
        conversations: [listed(EWA_AND_ME, since >= 3 ? GAME : null)],
      });
    });

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`), {
      timeout: 5000,
    });
    // Not pushed off the reads that listed the room without its game.
    expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length - before).toBeGreaterThanOrEqual(
      3,
    );
  });

  /** A yes that did not complete the court waits for the room alone: there is no game to know. */
  it('goes straight to a room still filling, which has no game to wait for', async () => {
    const stillFilling = {
      sport: 'PADEL' as const,
      standing: 'AWAITING_ANSWERS' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'A' as const, player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
        { side: 'B' as const, player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
        { side: 'B' as const, player_id: null, answer: null, nickname: null },
      ],
    };
    stubChallenges(transport, [row(stillFilling)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(stillFilling)));
    stubConversations(transport, []);
    opened(EWA_AND_ME);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^ewa\.m.*, Padel, .*to answer/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    transport.on('POST', `${DETAIL_PATH}/accept`, () => {
      stubConversations(transport, [{ ...listed(EWA_AND_ME), sport: 'PADEL' }]);
      return json<Wire['ChallengeSchema']>(
        row({
          ...stillFilling,
          seats: stillFilling.seats.map((seat) =>
            seat.player_id === ME ? { ...seat, answer: 'ACCEPTED' as const } : seat,
          ),
        }),
      );
    });

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`), {
      timeout: 5000,
    });
  });

  /**
   * **The acceptance that completes a four lands in a room with a plan card, and Now has the
   * game as Planning.** The accept opens the game inline, so `GET /games` holds it on the
   * re-read the reply triggers; the room carries its `game_id`; and no plan exists yet, which is
   * the card with three empty slots and the rail's *Planning* tag. Asserted end to end because
   * the two are a join of three lists at two surfaces, and a stale one on either is a blank.
   */
  it('lands in a room drawing the plan card, and Now draws the game as Planning', async () => {
    const OLA_TOO = [
      { player_id: EWA, nickname: 'ewa.m' },
      { player_id: OLA, nickname: 'ola.k' },
      { player_id: 'eeeeeeee-0000-4000-8000-000000000004', nickname: 'piotr' },
      { player_id: ME, nickname: 'me_' },
    ];
    const lastSeat = {
      sport: 'PADEL' as const,
      standing: 'AWAITING_ANSWERS' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'A' as const, player_id: OLA, answer: 'ACCEPTED' as const, nickname: 'ola.k' },
        {
          side: 'B' as const,
          player_id: 'eeeeeeee-0000-4000-8000-000000000004',
          answer: 'ACCEPTED' as const,
          nickname: 'piotr',
        },
        { side: 'B' as const, player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
      ],
    };
    const game: Wire['GameSchema'] = {
      game_id: GAME,
      challenge_id: CHALLENGE_ID,
      sport: 'PADEL',
      kind: 'COUNTED',
      standing: 'AWAITING_ENTRY',
      planned_at: READ_AT,
      entry_closes_at: at(8 * 24),
      seats: lastSeat.seats.map((seat) => ({
        side: seat.side,
        player_id: seat.player_id,
        nickname: seat.nickname,
      })),
      proposals: [],
    };

    stubChallenges(transport, [row(lastSeat)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(lastSeat)));
    // Not a member until the yes: the list holds the others' room and not this reader's.
    stubConversations(transport, []);
    stubPlans(transport, []);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^ewa\.m.*, Padel, .*to answer/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    transport.on('POST', `${DETAIL_PATH}/accept`, () => {
      // Everything the accept opened, as the reads after it find them: the game is inline
      // with the accept, the room's membership is derived live, and its `game_id` is noted.
      stubGames(transport, [game], READ_AT);
      stubConversations(transport, [{ ...listed(OLA_TOO), sport: 'PADEL', game_id: GAME }]);
      stubConversation(transport, {
        read_at: READ_AT,
        conversation_id: ROOM,
        challenge_id: CHALLENGE_ID,
        game_id: GAME,
        sport: 'PADEL',
        members: OLA_TOO,
        people: OLA_TOO,
        entries: [],
      });
      stubEntries(transport, ROOM);
      return json<Wire['ChallengeSchema']>(
        row({
          ...lastSeat,
          standing: 'ON',
          seats: lastSeat.seats.map((seat) => ({ ...seat, answer: 'ACCEPTED' as const })),
        }),
      );
    });

    fireEvent.press(await screen.findByRole('button', { name: IM_IN }));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`), {
      timeout: 5000,
    });

    // The plan card, pinned under the header: three slots, nothing agreed.
    expect(await screen.findByLabelText('Where: Not agreed yet')).toBeTruthy();

    // And Now, one tab over, has the game with the rail's word on it. The bar stands down in a
    // room, so the way to the tab is back out of it and out of the challenge behind it.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(screen.getByLabelText('Now'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    // The rail's tag for a game with nothing agreed yet, spelled by the words themselves — and
    // the card's three slots, each saying so under a dim bar (#413).
    expect(await screen.findByText('Planning')).toBeTruthy();
    expect(screen.getAllByText('Not agreed yet')).toHaveLength(3);
  });

  /** A no has no room to go to: the reader is outside whatever room the others keep. */
  it('stays on the sentence after Not this time, whatever the list holds', async () => {
    await openTheChallenge();
    stubConversations(transport, [listed(EWA_AND_ME)]);

    transport.on('POST', `${DETAIL_PATH}/decline`, () =>
      json<Wire['ChallengeSchema']>(
        row({
          standing: 'DECLINED',
          seats: [
            { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
            { side: 'B', player_id: ME, answer: 'DECLINED', nickname: 'me_' },
          ],
        }),
      ),
    );

    fireEvent.press(await screen.findByRole('button', { name: NOT_THIS_TIME }));

    expect(
      await screen.findByText(
        standingLine({ side: 'invitee', standing: 'DECLINED', player: EWA_NAMED }),
      ),
    ).toBeTruthy();
    expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`);
  });

  /**
   * **The door is drawn on every arm the join answers on**, not only the half-built court's.
   * A padel four where the reader has said yes and two seats are still awaiting is
   * `AWAITING_ANSWERS` with no act left — and the room the first yes opened is already being
   * talked in, so the arm's one control is the way into it.
   */
  it('draws Open the chat on an accepted seat still waiting on the others', async () => {
    const waitingOnTwo = {
      sport: 'PADEL' as const,
      standing: 'AWAITING_ANSWERS' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'A' as const, player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
        { side: 'B' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
        { side: 'B' as const, player_id: null, answer: null, nickname: null },
      ],
    };
    stubChallenges(transport, [row(waitingOnTwo)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(waitingOnTwo)));
    stubConversations(transport, [listed(EWA_AND_ME)]);
    opened(EWA_AND_ME);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    // The room's own row is on the tab beside the challenge's, spoken in the same dialect up to
    // the sport — so the challenge row is picked out by the sentence it goes on to say.
    fireEvent.press(await screen.findByLabelText(/^ewa\.m.*, Padel, You/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  /** And on a court that is on — reached from the row, with the room still standing. */
  it('draws Open the chat on a completed line-up while its room stands', async () => {
    const everybodyIn = {
      standing: 'ON' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'B' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
      ],
    };
    stubChallenges(transport, [row(everybodyIn)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(everybodyIn)));
    stubConversations(transport, [listed(EWA_AND_ME)]);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^ewa\.m, Squash, You/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    expect(await screen.findByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  /** No door rather than a dead one: a room the list does not hold draws nothing. */
  it('draws no door where the list holds no room for this challenge', async () => {
    const everybodyIn = {
      standing: 'ON' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'B' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
      ],
    };
    await openTheChallenge(detail(everybodyIn), row(everybodyIn));

    expect(await screen.findByText(standingLine({ side: 'invitee', standing: 'ON' }))).toBeTruthy();
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });
});
