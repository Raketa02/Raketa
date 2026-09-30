/**
 * **A half-built court, grown and ended** — the `LINE_UP_INCOMPLETE` arm walked the way a member
 * walks it: the real route tree, the real shell, the real builder at its second route, and only
 * `fetch` faked ([#362](https://github.com/Raketa02/Raketa/issues/362)).
 *
 * It sits beside `challengeScreen.test.tsx` because the two answers and these two acts are arms
 * of one fold, and it is a second file for the reason `send.test.tsx` is one beside
 * `builder.test.tsx`: what is under test here is a **journey across two screens and two
 * features**, and a suite that walked it inside the answer suite would make every fixture there
 * carry a court it does not need.
 *
 * What is asserted is the set of claims a build session could quietly undo:
 *
 * - **Any live member may fill, and nobody ends it for the others** — since ADR-0165 §4 the
 *   organiser has no *Withdraw* on a court somebody has joined ([#428](https://github.com/Raketa02/Raketa/issues/428)).
 * - **⚡ names the challenge and says nothing else about the court** — no sport, no mode, no
 *   locked seats, because all three are read off the challenge and refused beside it.
 * - **It pushes the builder under the challenge**, at `/chats/challenge/[id]/fill`, so the Chats
 *   column stays lit and *back* is correct by construction.
 * - **An accepted seat is not a control**: no clear badge, no press, no pool, and no sentence —
 *   and *Start over* is absent rather than disabled.
 * - **The send is `POST …/seats` and it pops back**, and nothing in the flow resets the shell.
 * - **The reader who has left reads a sentence about their own seat**, and their row stays.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { offlineMessage } from '@/shared/errors';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { PICK_PLAYERS_LABEL, endPlaySession, optimisedForLine } from '@/features/play/types';
import { PROPOSE_SHEET_TITLE, SEND_CHALLENGE_LABEL } from '../types';
import {
  CHALLENGES_PATH,
  datafileFor,
  datafileSettled,
  GATE_USER,
  launchIntoClassicPlay,
  launchSignedIn,
  stubChallenges,
  stubConversations,
  stubDatafile,
  stubGames,
  stubGate,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { OPEN_THE_CHAT } from '@/features/conversations/types';

import { standingLine } from './challengePresentation';
import { FILL_THE_SEATS, REMOVE_THE_CHALLENGE } from './challengeDetailPresentation';
import { LEAVE_THE_GAME } from './leaveGamePresentation';

const ME = GATE_USER.id;
const BEA = 'bbbbbbbb-0000-4000-8000-000000000002';
const CYRYL = 'cccccccc-0000-4000-8000-000000000003';
const DOROTA = 'dddddddd-0000-4000-8000-000000000004';

const CHALLENGE_ID = 'aaaaaaaa-0000-4000-8000-000000000001';
const LINEUP_ID = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const ROOM_ID = 'f1e2d3c4-b5a6-4978-8a9b-0c1d2e3f4a5c';

const READ_AT = '2026-09-08T12:00:00Z';

const DETAIL_PATH = `${CHALLENGES_PATH}/${CHALLENGE_ID}`;
const SEATS_PATH = `${DETAIL_PATH}/seats`;
const LINEUPS_PATH = '/api/v1/lineups';
const FORECASTS_PATH = '/api/v1/forecasts';

const NAMES: Readonly<Record<string, string>> = {
  [BEA]: 'bea_k',
  [CYRYL]: 'cyryl',
  [DOROTA]: 'dorota_w',
};

/** Enough of a rating for the entry gate; this suite is not about it. */
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

/**
 * A padel four with two seats taken and two open — `LINE_UP_INCOMPLETE`, which is what the
 * standing derives to when nothing is awaiting and the court is short.
 *
 * Which side the **reader** is on is the `organiser_id` on the row rather than anything about
 * the seats: one standing read twice, and the two permissions are what differ.
 */
function court(): Wire['SeatSchema'][] {
  return [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'A', player_id: BEA, answer: 'ACCEPTED', name: 'bea_k' },
    { side: 'B' },
    { side: 'B' },
  ];
}

function row(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return {
    challenge_id: CHALLENGE_ID,
    sport: 'PADEL',
    organiser_id: ME,
    standing: 'LINE_UP_INCOMPLETE',
    opened_at: '2026-09-08T08:00:00Z',
    seats: court(),
    ...over,
  };
}

function detail(
  over: Partial<Wire['ChallengeDetailResponse']> = {},
): Wire['ChallengeDetailResponse'] {
  return {
    read_at: READ_AT,
    challenge_id: CHALLENGE_ID,
    sport: 'PADEL',
    organiser_id: ME,
    standing: 'LINE_UP_INCOMPLETE',
    opened_at: '2026-09-08T08:00:00Z',
    seats: court(),
    ...over,
  };
}

function card(playerId: string): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    distance_km: 4,
    player_card: {
      name: NAMES[playerId] ?? 'anon',
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
      { seat_index: 1, relationship: 'PARTNER', player_id: BEA },
    ],
    B: [
      { seat_index: 2, relationship: 'OPPONENT', player_id: CYRYL },
      { seat_index: 3, relationship: 'OPPONENT', player_id: DOROTA },
    ],
  },
  forecast: { pct: 78, sigma_group: 0.41, provisional: false, assumption: null },
  split: { your_side: 3.2, their_side: 3.42, gap: -0.22 },
};

/** ⚡'s answer: the two who accepted come back as ordinary rows, and the two open seats fill. */
const filledCourt = (): Wire['LineupResponse'] => ({
  search: {
    search_id: LINEUP_ID,
    at: '2026-09-08T12:00:05Z',
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
  candidates: [card(BEA), card(CYRYL), card(DOROTA)],
  lineup: {
    seats: [
      { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
      { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: BEA },
      { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: CYRYL },
      { side: 'B', seat_index: 3, relationship: 'OPPONENT', player_id: DOROTA },
    ],
    arrangements: [ONE_WAY],
    group_reason: 'EVENEST_ARRANGEMENT',
  },
});

let transport: Transport;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubGames(transport);
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
  // The queue is app-wide and its hold is a timer these tests never let run.
  useToastQueue.getState().clear();
  queryClient.clear();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app, open Chats, and tap the one row — every assertion starts here. */
/**
 * Into the Chats inbox — by its column, with Classic play on, which is how the old loop is reached;
 * or with it **off**, by the inbox's route, because then the bar draws no Chats column and the
 * fill's point is that nothing on its path reads the flag (#550).
 */
async function launchIntoTheInbox(classicPlay: boolean) {
  if (classicPlay) {
    await launchIntoClassicPlay(transport);
    fireEvent.press(await screen.findByLabelText(/^Chats/));
  } else {
    await launchSignedIn('/chats');
    await datafileSettled(transport);
  }
  await waitFor(() => expect(screen).toHavePathname('/chats'));
}

async function openTheChallenge(
  answer: Wire['ChallengeDetailResponse'] = detail(),
  listed: Wire['ChallengeSchema'] = row(),
  rooms: readonly Wire['ConversationRowSchema'][] = [],
  classicPlay = true,
) {
  stubChallenges(transport, [listed], READ_AT);
  stubConversations(transport, rooms);
  transport.on('GET', DETAIL_PATH, () => json(answer));

  await launchIntoTheInbox(classicPlay);

  // A challenge row's name is `who, sport, line` and a conversation row's is `who, sport` — so
  // the trailing separator is what tells the two sections' rows apart when both hold this pair.
  fireEvent.press(await screen.findByLabelText(/, Padel, /));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
}

/**
 * The same screen by its route. A reader who said no has no row to tap — a no of one's own leaves
 * the inbox with the tap — and the screen still resolves for them (#390), which is what the two
 * cases about the reader who left are read on.
 */
async function openTheChallengeByRoute(
  answer: Wire['ChallengeDetailResponse'],
  listed: Wire['ChallengeSchema'],
  rooms: readonly Wire['ConversationRowSchema'][] = [],
) {
  stubChallenges(transport, [listed], READ_AT);
  stubConversations(transport, rooms);
  transport.on('GET', DETAIL_PATH, () => json(answer));

  await launchIntoTheInbox(true);

  act(() => router.push(`/chats/challenge/${CHALLENGE_ID}`));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
}

/** The room this challenge's first acceptance opened, as `GET /conversations` lists it. */
function conversationRow(
  over: Partial<Wire['ConversationRowSchema']> = {},
): Wire['ConversationRowSchema'] {
  return {
    conversation_id: ROOM_ID,
    challenge_id: CHALLENGE_ID,
    game_id: null,
    sport: 'PADEL',
    members: [
      { player_id: ME, name: 'me_' },
      { player_id: BEA, name: 'bea_k' },
    ],
    people: [
      { player_id: ME, name: 'me_' },
      { player_id: BEA, name: 'bea_k' },
    ],
    last_entry: null,
    ...over,
  };
}

/**
 * ⚡, and where it lands: the builder, **already holding a full court**.
 *
 * There is no seating beat to spend here, and that is the shape rather than an omission. ⚡'s
 * own wait is *under the court it is seating*, and on this journey the court is not on screen
 * yet — the fill runs on the challenge screen and the builder is pushed **onto its answer**,
 * which is *Find a game*'s shape exactly: press, the search runs, the builder arrives with a
 * court on it.
 */
async function fillTheSeats() {
  fireEvent.press(await screen.findByRole('button', { name: FILL_THE_SEATS }));
  await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}/fill`));
  await screen.findByRole('button', { name: SEND_CHALLENGE_LABEL });
}

/**
 * The pinned CTA and the sheet's own control carry **one label**, because the act is named once
 * — so the first press can only reach the CTA and the second can only reach the sheet's control,
 * which is `send.test.tsx`'s own walk.
 */
async function pressSend() {
  fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));
  await screen.findByText(PROPOSE_SHEET_TITLE);
  fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));
}

describe('the two controls', () => {
  /**
   * ADR-0150 §1, ADR-0165 §4, ADR-0175 §4. Growing a court and ending one are different acts,
   * and a court somebody has joined is nobody's to end for the others: the organiser has the fill
   * like anybody else, and **neither *Remove* nor *Withdraw*** — the acceptance criterion
   * [#428](https://github.com/Raketa02/Raketa/issues/428) names for once somebody has joined —
   * and no leave either, which is the Chats row's swipe alone.
   */
  it('offers the fill to any live member, and the organiser no way to end or leave it', async () => {
    await openTheChallenge();

    expect(await screen.findByRole('button', { name: FILL_THE_SEATS })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(screen.queryByText(/withdraw/i)).toBeNull();
    expect(screen.queryByLabelText(/withdraw/i)).toBeNull();
  });

  it('offers a member who is not the organiser the same act', async () => {
    await openTheChallenge(detail({ organiser_id: BEA }), row({ organiser_id: BEA }));

    expect(await screen.findByRole('button', { name: FILL_THE_SEATS })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
  });

  /**
   * §13.1: the invitee sentence reads the reader's **own seat**, not only their side — and the
   * row is not filtered away, because a departed seat is still a seat and a vanished row would
   * take the only available explanation with it. (**Not the pair rule**, which released them —
   * [#393](https://github.com/Raketa02/Raketa/issues/393).)
   */
  it('gives a reader who has left the sentence about their own seat and nothing to press', async () => {
    const left: Wire['SeatSchema'][] = [
      { side: 'A', player_id: BEA, answer: 'ACCEPTED', name: 'bea_k' },
      { side: 'A', player_id: ME, answer: 'DECLINED', name: 'me_' },
      { side: 'B' },
      { side: 'B' },
    ];

    await openTheChallengeByRoute(
      detail({ organiser_id: BEA, seats: left }),
      row({ organiser_id: BEA, seats: left }),
    );

    expect(
      await screen.findByText(
        standingLine({
          side: 'invitee',
          standing: 'LINE_UP_INCOMPLETE',
          accepted: 1,
          open: 3,
          ownAnswer: 'DECLINED',
        }),
      ),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: FILL_THE_SEATS })).toBeNull();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });

  /** Every act on this screen fails offline and none is sent later — one note above the pair. */
  it('greys the controls under one amber note when there is no connection', async () => {
    await openTheChallenge();
    await screen.findByRole('button', { name: FILL_THE_SEATS });

    act(() => onlineManager.setOnline(false));

    expect(await screen.findByText(offlineMessage('does-not-resume'))).toBeTruthy();
    expect(screen.getAllByText(offlineMessage('does-not-resume'))).toHaveLength(1);
    expect(screen.getByRole('button', { name: FILL_THE_SEATS }).props.accessibilityState).toEqual(
      expect.objectContaining({ disabled: true }),
    );
  });
});

describe('*Open the chat*', () => {
  /**
   * ADR-0149 §3: the door is a **client join** over the player's own rooms, because no route
   * serves a challenge its conversation and ADR-0146 forbids `challenges` knowing this context
   * exists. It fails soft, and the words are the conversation's so the three surfaces that draw
   * one cannot say three different things.
   */
  it('is drawn between the fill and the withdraw once the join answers', async () => {
    await openTheChallenge(detail(), row(), [conversationRow()]);

    expect(await screen.findByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it('opens the room the first acceptance opened', async () => {
    await openTheChallenge(detail(), row(), [conversationRow()]);

    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM_ID}`));
  });

  /**
   * **No door rather than a dead one.** A room the join cannot find is the ordinary state
   * rather than an error — a challenge nobody has answered has none, and a room is destroyed
   * when its episode ends.
   */
  it('is not drawn where the join finds no room', async () => {
    await openTheChallenge();

    await screen.findByRole('button', { name: FILL_THE_SEATS });
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('is not drawn to a reader who has left the court', async () => {
    const left: Wire['SeatSchema'][] = [
      { side: 'A', player_id: BEA, answer: 'ACCEPTED', name: 'bea_k' },
      { side: 'A', player_id: ME, answer: 'DECLINED', name: 'me_' },
      { side: 'B' },
      { side: 'B' },
    ];

    await openTheChallengeByRoute(
      detail({ organiser_id: BEA, seats: left }),
      row({ organiser_id: BEA, seats: left }),
      [conversationRow()],
    );

    await screen.findByText(
      standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 1,
        open: 3,
        ownAnswer: 'DECLINED',
      }),
    );
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });
});

describe('⚡ fill the seats', () => {
  /**
   * ADR-0150 §2: **the fill names the challenge it completes and says nothing else about the
   * court.** The sport, the mode and the locked seats are read off the challenge and refused
   * beside it — *a caller supplying one is offering a second place for a fact the challenge
   * already holds*.
   */
  it('names the challenge and nothing else about the court', async () => {
    await openTheChallenge();
    await fillTheSeats();

    expect(transport.requestsTo('POST', LINEUPS_PATH)[0]?.body).toEqual({
      completing_challenge_id: CHALLENGE_ID,
    });
  });

  /**
   * ADR-0150 §7: the builder is `features/play`'s screen at a **second route** under the
   * challenge, so the Chats column stays lit for free and *back* is correct by construction.
   */
  it('pushes the builder under the challenge, and back returns to it', async () => {
    await openTheChallenge();
    await fillTheSeats();

    expect(screen.getByLabelText(/^Chats/).props.accessibilityState).toEqual(
      expect.objectContaining({ selected: true }),
    );

    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
  });

  /** *Nothing outbound happens on the press: the send is still a separate press.* */
  it('reaches nobody until the send is pressed', async () => {
    await openTheChallenge();
    await fillTheSeats();

    expect(transport.requestsTo('POST', SEATS_PATH)).toEqual([]);
  });
});

/**
 * **Fill-the-seat is not closed by `classic_play`**
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7, [#479](https://github.com/Raketa02/Raketa/issues/479), [#550](https://github.com/Raketa02/Raketa/issues/550)).
 * The flag closes Find a game and the builder and pool under Play with it; a challenge already
 * sent still has to be fillable, and this journey reaches the builder at its own route and the
 * pool at Play's — which the gate lets through because it is opened on a search the fill already
 * ran, like any search under way.
 */
describe('with Classic play switched off', () => {
  beforeEach(() => stubDatafile(transport, datafileFor({ classic_play: 'off' })));

  it('still pushes the builder under the challenge', async () => {
    await openTheChallenge(detail(), row(), [], false);

    await fillTheSeats();

    expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}/fill`);
  });

  it('still opens the pool against a seat the fill took', async () => {
    await openTheChallenge(detail(), row(), [], false);
    await fillTheSeats();

    // Take the fill's pick back out of the seat, then fill the hole from the pool — the one way
    // to it from a full court, since a tap on somebody seated trades places.
    fireEvent.press(screen.getByLabelText(/^Remove cyryl from/));
    fireEvent.press(await screen.findByLabelText(PICK_PLAYERS_LABEL));

    await waitFor(() => expect(screen).toHavePathname('/play/pool'));
  });
});

describe('the court it pushes', () => {
  /**
   * ADR-0150 §8: **an accepted seat is not a control** — no clear badge, no press, no pool — and
   * the named refusal the source documentation asked for is never written, because a seat that
   * answers with a sentence is a control that refuses.
   */
  it('draws no clear badge on somebody who accepted, and says nothing when pressed', async () => {
    await openTheChallenge();
    await fillTheSeats();

    // The seat rather than the forecast card's face, which draws the same handle one card down.
    fireEvent.press(screen.getByLabelText(/^Your side, your partner, bea_k, level/));

    expect(screen.queryByLabelText(/^Clear/)).toBeNull();
    expect(useToastQueue.getState().queue).toEqual([]);
    // And the pool is not opened: the press produced nothing at all.
    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}/fill`));
  });

  /** ***Start over* is absent**, not disabled and not redefined to mean *empty it to these two*. */
  it('offers no way to start over on a court somebody has agreed to', async () => {
    await openTheChallenge();
    await fillTheSeats();

    expect(screen.queryByRole('button', { name: 'Start over' })).toBeNull();
  });

  /**
   * **No note about whom the answer was optimised for.** The engine answers `GROUP` for any
   * locked seat — `filledCourt()` says so — and on this journey the locked seats are the people
   * who said yes, not people the organiser picked, so the ordinary builder's caveat would be
   * false here and is not drawn.
   */
  it('says nothing about the answer being optimised for the group', async () => {
    await openTheChallenge();
    await fillTheSeats();

    expect(screen.queryByText(optimisedForLine('GROUP') ?? '')).toBeNull();
  });
});

describe('the send', () => {
  /**
   * *"The send's shape minus the mint"* — `{search_id, court}` on the challenge's own route, the
   * **whole** court and not the seats being filled, because an acceptance is to the game and not
   * to the side.
   */
  it('grows the court that stands rather than minting a second one', async () => {
    transport.on('POST', SEATS_PATH, () => json(row({ standing: 'AWAITING_ANSWERS' })));

    await openTheChallenge();
    await fillTheSeats();
    await pressSend();

    await waitFor(() => expect(transport.requestsTo('POST', SEATS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', SEATS_PATH)[0]?.body).toEqual({
      search_id: LINEUP_ID,
      court: [
        { side: 'A', player_id: ME },
        { side: 'A', player_id: BEA },
        { side: 'B', player_id: CYRYL },
        { side: 'B', player_id: DOROTA },
      ],
    });
    expect(transport.requestsTo('POST', CHALLENGES_PATH)).toEqual([]);
  });

  /**
   * Both closers are about what a **first** acceptance opens, and this court has already had
   * one — so the sheet draws neither rather than promising a chat that is already open.
   */
  it('promises no chat on a court whose chat is already open', async () => {
    await openTheChallenge();
    await fillTheSeats();

    fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));

    await screen.findByText(PROPOSE_SHEET_TITLE);
    expect(screen.queryByText(/start talking/)).toBeNull();
    expect(screen.queryByText(/Nothing opens until/)).toBeNull();
    // What it still owes is the fact the player cannot recover from.
    expect(screen.getByText('Nobody is contacted until you send it.')).toBeTruthy();
  });

  /**
   * **It pops back to the challenge screen**, which is the surface that draws the result — the
   * new seats, their fresh deadlines, and a standing that may now be awaiting answers again.
   * Nothing here resets the shell stack: `landOnHome`'s *there is nothing left to be behind* is
   * false when the thing behind is the challenge you were completing.
   */
  it('pops back to the challenge rather than landing on Now', async () => {
    transport.on('POST', SEATS_PATH, () => json(row({ standing: 'AWAITING_ANSWERS' })));

    await openTheChallenge();
    await fillTheSeats();
    await pressSend();

    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE_ID}`));
  });
});
