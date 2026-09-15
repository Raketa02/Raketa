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
import { planKeys } from '@/features/plans/types';
import { AppError, offlineMessage } from '@/shared/errors';
import {
  CHALLENGES_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubInterest,
  stubOutgoingYeses,
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
import {
  IM_IN,
  NOT_THIS_TIME,
  REMOVE_SHEET_BODY,
  REMOVE_SHEET_CLOSE_LABEL,
  REMOVE_SHEET_TITLE,
  REMOVE_THE_CHALLENGE,
  pairingAbsenceLine,
  removeRefusalMessage,
  saidYesOnPlayersLine,
} from './challengeDetailPresentation';
import { LEAVE_FROM_THE_LIST_BODY, LEAVE_THE_GAME } from './leaveGamePresentation';

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
  // The screen reads the reader's own yeses for the invitee's line; nobody, unless a test says.
  stubInterest(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * An empty list in the cache that no timer will collect — for the two walks that assert a mark
 * on an entry nothing is observing. `queryClient.clear()` in `afterEach` still takes it away.
 */
function seedUncollected(queryKey: readonly unknown[]): void {
  queryClient.getQueryCache().build(queryClient, { queryKey, gcTime: Infinity });
  queryClient.setQueryData(queryKey, []);
}

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

/**
 * **An invitation a swipe produced says so**
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8): one line under the organiser's card, exactly when the organiser is in the reader's own
 * outgoing list for the challenge's sport. Client-side, off the deck's read; ADR-0143's refusal
 * to tell an invitee why the engine picked them is untouched, because this is her own act.
 */
describe('the invitee’s line', () => {
  it('says You said yes to the organiser on Players when the reader did, in this sport', async () => {
    stubOutgoingYeses(transport, [EWA, 'SQUASH']);
    await openTheChallenge();

    expect(await screen.findByText(saidYesOnPlayersLine('ewa.m'))).toBeTruthy();
  });

  it('draws no such line when the yes was in another sport', async () => {
    stubOutgoingYeses(transport, [EWA, 'PADEL']);
    await openTheChallenge();
    await screen.findByLabelText(/^ewa\.m\. Match score 78\./);
    // An absence proves nothing until the list has landed.
    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/interest')).toHaveLength(1));

    expect(screen.queryByText(saidYesOnPlayersLine('ewa.m'))).toBeNull();
  });

  it('draws no such line for an organiser the reader never said yes to', async () => {
    await openTheChallenge();
    await screen.findByLabelText(/^ewa\.m\. Match score 78\./);
    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/interest')).toHaveLength(1));

    expect(screen.queryByText(/You said yes to/)).toBeNull();
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

    // The yes screen is pushed over this one the instant the reply lands (ADR-0167), so the
    // redraw is read through it: the screen underneath is hidden from assistive technology by
    // the stack, and a query that skipped it would find nothing rather than the wrong sentence.
    expect(
      await screen.findByText(standingLine({ side: 'invitee', standing: 'ON' }), {
        includeHiddenElements: true,
      }),
    ).toBeTruthy();
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
    // Built with no collection time, because the yes screen's push runs every pending timer
    // under the router harness — the entry's own collection included — and a seeded entry
    // that was collected before it could be looked at would read as never marked.
    seedUncollected(gameKeys.list());

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

  /**
   * **And the plan list**, on the same reasoning: a yes is what gives the reader an accepted seat
   * and so a row on `GET /plans` (ADR-0164 §3), and the list read before the yes held none for a
   * court they were still deciding about. The room this lands in pins the card from its first
   * frame because the list is marked here, rather than thirty seconds later when it goes stale.
   */
  it('marks the plan list out of date, because a yes gives the reader a row on it', async () => {
    await openTheChallenge();

    seedUncollected(planKeys.list());
    expect(queryClient.getQueryState(planKeys.list())?.isInvalidated).toBe(false);

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
      expect(queryClient.getQueryState(planKeys.list())?.isInvalidated).toBe(true),
    );
  });
});

/**
 * **The room an acceptance opens is the yes screen's now**
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md),
 * [#433](https://github.com/Raketa02/Raketa/issues/433)): the four walks that pinned *accept
 * pushes the room* — the room landing off a later read, the completing yes waiting for the row to
 * carry its game, a room still filling, and the room drawing the plan card — are rewritten to the
 * new exits in `yesScreen.test.tsx`. What stays here is what this screen still does about a room:
 * a no goes nowhere, and the door on later visits is drawn wherever the join answers.
 */
describe('the door on later visits', () => {
  const ROOM = 'cccccccc-0000-4000-8000-000000000007';
  const OLA = 'dddddddd-0000-4000-8000-000000000003';

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

describe('*Leave the game* on the arranging arm', () => {
  const OLA = 'dddddddd-0000-4000-8000-000000000003';
  const DEPARTURE_PATH = `${DETAIL_PATH}/departure`;

  /** A padel four with the organiser and me in, and two seats still deciding. */
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

  /**
   * **A yes can be taken back before the court is whole** (ADR-0165 §1,
   * [#427](https://github.com/Raketa02/Raketa/issues/427)): an accepted seat still waiting on the
   * others has the door, and it opens the same sheet the Chats list's swipe does.
   */
  it('is drawn for an accepted seat still waiting on the others, and opens the sheet', async () => {
    stubChallenges(transport, [row(waitingOnTwo)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(waitingOnTwo)));

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^ewa\.m.*, Padel, You/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));

    expect(await screen.findByText(LEAVE_FROM_THE_LIST_BODY)).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  /** The organiser is a player in that rule: once somebody has joined, they leave like anybody. */
  it('is drawn for the organiser once somebody has joined', async () => {
    const joined = { ...waitingOnTwo, organiser_id: ME };
    stubChallenges(transport, [row(joined)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(joined)));

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/, Padel, Waiting/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));

    expect(await screen.findByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
  });

  /**
   * **A court of one has nothing to leave.** The organiser nobody has joined yet is drawn no such
   * door — their exit there is #428's *Remove the challenge*.
   */
  it('is not drawn for an organiser nobody has joined yet', async () => {
    const mySend = {
      organiser_id: ME,
      seats: [
        { side: 'A' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
        { side: 'B' as const, player_id: EWA, answer: null, answer_by: at(20), nickname: 'ewa.m' },
      ],
    };
    await openTheChallenge(detail(mySend), row(mySend));

    expect(
      await screen.findByText(
        standingLine({ side: 'organiser', standing: 'AWAITING_ANSWERS', awaiting: 1 }),
      ),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });

  /** And never to a reader who has an answer to give: their two acts are the whole of the arm. */
  it('is not drawn to an invitee who has not answered', async () => {
    await openTheChallenge();

    expect(await screen.findByRole('button', { name: IM_IN })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });
});

describe('*Remove the challenge* on the arranging arm', () => {
  const OLA = 'dddddddd-0000-4000-8000-000000000003';
  const WITHDRAWAL_PATH = `${DETAIL_PATH}/withdrawal`;

  /** My padel four, just sent: two asked, nobody has answered. */
  const mySend = {
    sport: 'PADEL' as const,
    organiser_id: ME,
    standing: 'AWAITING_ANSWERS' as const,
    seats: [
      { side: 'A' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
      { side: 'A' as const, player_id: EWA, answer: null, answer_by: at(20), nickname: 'ewa.m' },
      { side: 'B' as const, player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
      { side: 'B' as const, player_id: null, answer: null, nickname: null },
    ],
  };

  /** The same court once Ewa has said yes: the organiser is a player now, and leaves like one. */
  const joined = {
    ...mySend,
    seats: [
      { side: 'A' as const, player_id: ME, answer: 'ACCEPTED' as const, nickname: 'me_' },
      { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
      { side: 'B' as const, player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
      { side: 'B' as const, player_id: null, answer: null, nickname: null },
    ],
  };

  /** What the route says back: the challenge as it now stands, every seat exactly as it was. */
  const REMOVED: Wire['ChallengeSchema'] = {
    ...row(mySend),
    standing: 'WITHDRAWN',
    ended_at: READ_AT,
  };

  const refused = (code: string) =>
    new AppError('conflict', 'business-conflict', 'test failure', { code });

  async function openMySend(court: typeof mySend = mySend) {
    stubChallenges(transport, [row(court)], READ_AT);
    transport.on('GET', DETAIL_PATH, () => json(detail(court)));

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/, Padel, /));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
  }

  /**
   * **The organiser's, while nobody has joined** (ADR-0165 §4,
   * [#428](https://github.com/Raketa02/Raketa/issues/428)) — the arm that had no organiser act
   * at all draws one, and it opens the withdrawal's sheet in the removal's words.
   */
  it('is drawn for an organiser nobody has joined, and opens the sheet that says it is gone for the invitees too', async () => {
    await openMySend();

    expect(
      await screen.findByText(
        standingLine({ side: 'organiser', standing: 'AWAITING_ANSWERS', awaiting: 2 }),
      ),
    ).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE }));

    expect(await screen.findByText(REMOVE_SHEET_TITLE)).toBeTruthy();
    for (const line of REMOVE_SHEET_BODY) expect(screen.getByText(line)).toBeTruthy();
    expect(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeTruthy();
    expect(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });

  /**
   * Pending, never optimistic, and **the reply is the exit**
   * ([#429](https://github.com/Raketa02/Raketa/issues/429)): the act closed the court and the
   * organiser's own removal leaves the inbox on the same reply, so the screen leaves rather than
   * redrawing into *You withdrew this* with nothing to press — the departure's own rule, for its
   * reason. The list underneath holds no row for it.
   */
  it('calls the withdrawal route on confirm and leaves the screen, landing on Chats with the row gone', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => json(REMOVED));
    await openMySend();

    fireEvent.press(await screen.findByRole('button', { name: REMOVE_THE_CHALLENGE }));
    await screen.findByText(REMOVE_SHEET_TITLE);
    stubChallenges(transport, [REMOVED], READ_AT);
    fireEvent.press(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toHaveLength(1);
    await waitFor(() => expect(screen.queryByLabelText(/, Padel, /)).toBeNull());
    expect(screen.queryByText(REMOVE_SHEET_TITLE)).toBeNull();
  });

  /**
   * **Once somebody has joined, neither *Remove* nor *Withdraw*** — the acceptance criterion in
   * as many words. The organiser is a player now, and the arm offers the player's door instead.
   */
  it('is not drawn once somebody has joined, and neither is any withdraw', async () => {
    await openMySend(joined);

    expect(await screen.findByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(screen.queryByText(/withdraw/i)).toBeNull();
    expect(screen.queryByLabelText(/withdraw/i)).toBeNull();
  });

  /** And never to an invitee, answered or not. */
  it('is not drawn to an invitee', async () => {
    await openTheChallenge();

    expect(await screen.findByRole('button', { name: IM_IN })).toBeTruthy();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
  });

  /**
   * **A refusal is said on the sheet, and the detail is re-read once it is dismissed**: somebody
   * said yes under the finger, so the arm re-folds into the one that offers *Leave the game*.
   */
  it('says why on the sheet when somebody has joined under the finger, and re-folds on Keep it open', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => {
      // The server's truth from here on: Ewa is in.
      transport.on('GET', DETAIL_PATH, () => json(detail(joined)));
      stubChallenges(transport, [row(joined)], READ_AT);
      return errorResponse(409, 'somebody_has_joined');
    });
    await openMySend();

    fireEvent.press(await screen.findByRole('button', { name: REMOVE_THE_CHALLENGE }));
    await screen.findByText(REMOVE_SHEET_TITLE);
    fireEvent.press(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(removeRefusalMessage(refused('somebody_has_joined')))).toBeTruthy();
    expect(screen.getByText(REMOVE_SHEET_TITLE)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL }));

    expect(await screen.findByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`);
  });
});
