/**
 * **The yes screen, walked the way a player walks it**: the real route tree, the real shell, the
 * challenge screen it is pushed over, and only `fetch` faked — `challengeScreen.test.tsx`'s own
 * seam, which is where these walks began as *the room an acceptance opens*
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md),
 * [#433](https://github.com/Raketa02/Raketa/issues/433)).
 *
 * The four tests that pinned *accept pushes the room* are rewritten here to the new exits: a yes
 * lands on the yes screen with no bar and the whole handles spoken; *Open the chat* waits on the
 * button and lands as `[Chats list, the room]`, or on the list past the bound; *Later* and the
 * device's back land on the list with the challenge screen gone; a padel four draws three faces
 * and an empty seat, reader first, whichever side the reader's seat is on; and the reader's own
 * face is read off their own record while everybody else's comes off the seat cards.
 *
 * A good test drives the seam a player crosses and asserts what is on the phone; none of these
 * knows which hook polled what.
 */

import { AccessibilityInfo } from 'react-native';
import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
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
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { IM_IN } from './challengeDetailPresentation';
import { LATER, yesAnnouncement } from './yesScreenPresentation';

const ME = GATE_USER.id;
const EWA = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'dddddddd-0000-4000-8000-000000000003';
const KUBA = 'eeeeeeee-0000-4000-8000-000000000004';
const CHALLENGE_ID = 'aaaaaaaa-0000-4000-8000-000000000001';
const ROOM = 'cccccccc-0000-4000-8000-000000000007';
const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

const READ_AT = '2026-09-08T12:00:00Z';
const HOUR = 60 * 60 * 1000;

function at(hours: number): string {
  return new Date(Date.parse(READ_AT) + hours * HOUR).toISOString();
}

const DETAIL_PATH = `${CHALLENGES_PATH}/${CHALLENGE_ID}`;
const CHALLENGE_SCREEN = `/chats/challenge/${CHALLENGE_ID}`;
const YES_SCREEN = `${CHALLENGE_SCREEN}/yes`;
const THE_ROOM = `/chats/conversation/${ROOM}`;
const OWN_RECORD = '/api/v1/players/me/record';

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

type Seat = Wire['SeatSchema'];

/** Ewa's squash challenge to you, still to answer — the singles court every walk starts on. */
const SINGLES: readonly Seat[] = [
  { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
  { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
];

/** The same seats once you have said yes — the reply, and what the reads after it find. */
const accepted = (seats: readonly Seat[]): Seat[] =>
  seats.map((seat) => (seat.player_id === ME ? { ...seat, answer: 'ACCEPTED' } : seat));

function row(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return {
    challenge_id: CHALLENGE_ID,
    sport: 'SQUASH',
    organiser_id: EWA,
    standing: 'AWAITING_ANSWERS',
    opened_at: at(-4),
    seats: [...SINGLES],
    ...over,
  };
}

const card = (nickname: string, photoUrl?: string): Wire['SeatCardSchema'] => ({
  person: {
    nickname,
    area_code: 'WAW-C',
    level: 2.71,
    band: 'Established',
    range: { low: 2.55, high: 2.87 },
    ...(photoUrl === undefined ? {} : { photo_id: `photo-${nickname}`, photo_url: photoUrl }),
  },
  pairing: { fit: 78, distance_km: 3, terms: [], degraded_terms: [], concerns: [] },
});

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
    seats: SINGLES.map((seat) =>
      seat.player_id === EWA ? { ...seat, card: card('ewa.m') } : seat,
    ),
    ...over,
  };
}

/** Your own record, as `GET /players/me/record` answers — with or without a photograph. */
function ownRecord(photoUrl?: string): Wire['PlayerRecordResponse'] {
  return {
    is_self: true,
    nickname: 'me_',
    area_code: 'WAW-C',
    social_tags: [],
    sports: [{ sport: 'SQUASH', level: 2.7, band: 'Established' }],
    ...(photoUrl === undefined ? {} : { photo_id: 'photo-me', photo_url: photoUrl }),
  };
}

/** The room this challenge opened, as `GET /conversations` lists it once the teller has written it. */
const listed = (
  members: readonly Wire['ConversationMemberSchema'][],
  gameId: string | null = null,
  sport: Wire['Sport'] = 'SQUASH',
): Wire['ConversationRowSchema'] => ({
  conversation_id: ROOM,
  challenge_id: CHALLENGE_ID,
  game_id: gameId,
  sport,
  members: [...members],
  people: [...members],
  last_entry: null,
});

const opened = (members: readonly Wire['ConversationMemberSchema'][], gameId: string | null) => {
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE_ID,
    game_id: gameId,
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

let transport: Transport;
let announced: jest.SpyInstance;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubGames(transport);
  announced = jest.spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions');
});

afterEach(async () => {
  stopWatchingHardwareBack();
  announced.mockRestore();
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app, open Chats, and tap the row — then say yes. */
async function openTheChallenge(
  answer: Wire['ChallengeDetailResponse'] = detail(),
  listedRow: Wire['ChallengeSchema'] = row(),
  rowLabel: RegExp = /^ewa\.m, Squash/,
) {
  stubChallenges(transport, [listedRow], READ_AT);
  transport.on('GET', DETAIL_PATH, () => json(answer));

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(rowLabel));
  await waitFor(() => expect(screen).toHavePathname(CHALLENGE_SCREEN));
}

/**
 * The accept's reply, and everything the reads after it find: the detail as accepted, so a
 * re-read agrees with the redraw. The rooms list is each walk's own, because it is the wait.
 */
function stubAccept(reply: Wire['ChallengeSchema'], detailAfter: Wire['ChallengeDetailResponse']) {
  transport.on('POST', `${DETAIL_PATH}/accept`, () => {
    transport.on('GET', DETAIL_PATH, () => json(detailAfter));
    return json<Wire['ChallengeSchema']>(reply);
  });
}

async function sayYes() {
  fireEvent.press(await screen.findByRole('button', { name: IM_IN }));
  await waitFor(() => expect(screen).toHavePathname(YES_SCREEN));
  // The pathname moves a beat before the screen is on the tree.
  await screen.findByTestId('yes-screen');
}

const yesScreen = () => within(screen.getByTestId('yes-screen'));
/** The initials are hidden from assistive technology on purpose; a query about the drawing says so. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const tabs = () => screen.queryAllByRole('tab');
const SINGLES_SPOKEN = yesAnnouncement({
  yours: [{ kind: 'person', playerId: ME, nickname: 'me_' }],
  theirs: [{ kind: 'person', playerId: EWA, nickname: 'ewa.m' }],
});

describe('a yes lands on the yes screen', () => {
  it('is the pathname the instant I’m in is answered, with no bar, and speaks both whole handles', async () => {
    await openTheChallenge();
    stubConversations(transport, []);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    await sayYes();

    expect(screen).toHaveSearchParams(expect.objectContaining({ which: 'challenge' }));
    expect(tabs()).toHaveLength(0);
    // The header is the picture as a sentence, and the sentence is what a listener hears.
    expect(await yesScreen().findByRole('header', { name: SINGLES_SPOKEN })).toBeTruthy();
    await waitFor(() => expect(announced).toHaveBeenCalledWith(SINGLES_SPOKEN, expect.anything()));
    // Whole handles and never the initials: nothing on the screen speaks `EM` or `ME`.
    expect(yesScreen().queryByLabelText(/\bEM\b/)).toBeNull();
    // Two faces, both posters — Ewa's card carries no photograph, and nothing was read for yours.
    expect(yesScreen().getAllByTestId('yes-tile-poster')).toHaveLength(2);
    expect(yesScreen().queryAllByTestId('yes-tile-empty')).toHaveLength(0);
    expect(yesScreen().getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
    expect(yesScreen().getByRole('button', { name: LATER })).toBeTruthy();
  });

  it('draws the reader’s own photograph off their own record, and a poster carries the initials', async () => {
    await openTheChallenge(
      detail({
        seats: SINGLES.map((seat) =>
          seat.player_id === EWA
            ? { ...seat, card: card('ewa.m', 'https://photos.example/ewa') }
            : seat,
        ),
      }),
    );
    stubConversations(transport, []);
    transport.on('GET', OWN_RECORD, () => json(ownRecord('https://photos.example/me')));
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    await sayYes();

    // One read of your own record, fired on open, and both tiles are photographs.
    await waitFor(() => expect(yesScreen().getAllByTestId('yes-tile-photo')).toHaveLength(2));
    expect(transport.requestsTo('GET', OWN_RECORD)).toHaveLength(1);
    // No letters over a face — asked with the hidden included, since the initials are a drawing
    // hidden from the reader by design, and a query that skipped them would pass for nothing.
    expect(yesScreen().queryByText('EM', HIDDEN_TOO)).toBeNull();
    expect(yesScreen().queryByText('ME', HIDDEN_TOO)).toBeNull();
  });

  it('draws the initials over a poster, upper-cased, and the poster if the record does not answer', async () => {
    await openTheChallenge();
    stubConversations(transport, []);
    // No stub for the own record: the read fails, and the poster stands in.
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    await sayYes();

    expect(await yesScreen().findByText('EM', HIDDEN_TOO)).toBeTruthy();
    expect(yesScreen().getByText('ME', HIDDEN_TOO)).toBeTruthy();
    // And never spoken: the drawing is hidden from the reader, and the header carries the handles.
    expect(yesScreen().queryByText('EM')).toBeNull();
    expect(yesScreen().getAllByTestId('yes-tile-poster')).toHaveLength(2);
  });
});

describe('Open the chat', () => {
  /**
   * **The awaited door moved behind the button.** The accept's reply says nothing about a
   * conversation and the room is written off the outbox after it — so the list answers empty at
   * first, the screen keeps asking, and *Open the chat* pressed before the row is there waits on
   * the button. What is asserted is the landing off a **later** read, and where it lands: the
   * room over the Chats list, with the challenge screen and the yes screen gone.
   */
  it('waits on the button until the room is listed, then lands in it over the Chats list', async () => {
    await openTheChallenge();
    opened(EWA_AND_ME, GAME);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    // The teller is a delivery behind the reply: the list holds no room until it has written
    // one, however many times it is asked.
    let written = false;
    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    transport.on('GET', CONVERSATIONS_PATH, () =>
      json<Wire['ConversationListResponse']>({
        read_at: READ_AT,
        conversations: written ? [listed(EWA_AND_ME, GAME)] : [],
      }),
    );

    await sayYes();

    const door = yesScreen().getByRole('button', { name: OPEN_THE_CHAT });
    expect(door.props.accessibilityState?.busy).toBe(false);
    expect(door.props.accessibilityState?.disabled).toBe(false);
    fireEvent.press(door);

    // Busy, and never disabled: a door is waited on, not taken away — and the screen keeps
    // asking the list while it waits, rather than reading it once and giving up.
    const waiting = yesScreen().getByRole('button', { name: OPEN_THE_CHAT });
    expect(waiting.props.accessibilityState?.busy).toBe(true);
    await waitFor(() =>
      expect(
        transport.requestsTo('GET', CONVERSATIONS_PATH).length - before,
      ).toBeGreaterThanOrEqual(3),
    );
    expect(screen).toHavePathname(YES_SCREEN);
    expect(
      yesScreen().getByRole('button', { name: OPEN_THE_CHAT }).props.accessibilityState?.busy,
    ).toBe(true);

    written = true;
    await waitFor(() => expect(screen).toHavePathname(THE_ROOM), { timeout: 5000 });

    // Back from the room is the Chats list: the celebration and the challenge screen are gone.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(tabs()).toHaveLength(5);
  });

  /**
   * **A yes that completed the court waits for the room to know its game.** `ON` says a game
   * exists — opened inline with the accept — while the room is told which off the outbox a
   * moment later. The row without its game is a door and not yet an arrival, so the landing
   * waits for the read that carries it.
   */
  it('waits for the row to carry its game when the yes completed the court', async () => {
    await openTheChallenge();
    opened(EWA_AND_ME, GAME);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    // The room is listed at once — membership is derived live — and learns its game only when
    // the teller's note lands, however many times the list is asked before that.
    let noted = false;
    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    transport.on('GET', CONVERSATIONS_PATH, () =>
      json<Wire['ConversationListResponse']>({
        read_at: READ_AT,
        conversations: [listed(EWA_AND_ME, noted ? GAME : null)],
      }),
    );

    await sayYes();
    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));

    // Not off the reads that list the room without its game: still waiting, still asking.
    await waitFor(() =>
      expect(
        transport.requestsTo('GET', CONVERSATIONS_PATH).length - before,
      ).toBeGreaterThanOrEqual(3),
    );
    expect(screen).toHavePathname(YES_SCREEN);

    noted = true;
    await waitFor(() => expect(screen).toHavePathname(THE_ROOM), { timeout: 5000 });
  });

  /** A yes that did not complete the court waits for the room alone: there is no game to know. */
  it('lands in a room still filling as soon as it is listed', async () => {
    const stillFilling = {
      sport: 'PADEL' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'A' as const, player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
        { side: 'B' as const, player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
        { side: 'B' as const, player_id: null, answer: null, nickname: null },
      ],
    };
    await openTheChallenge(
      detail(stillFilling),
      row(stillFilling),
      /^ewa\.m.*, Padel, .*to answer/,
    );
    stubConversations(transport, []);
    opened(EWA_AND_ME, null);
    transport.on('POST', `${DETAIL_PATH}/accept`, () => {
      stubConversations(transport, [listed(EWA_AND_ME, null, 'PADEL')]);
      transport.on('GET', DETAIL_PATH, () =>
        json(detail({ ...stillFilling, seats: accepted(stillFilling.seats) })),
      );
      return json<Wire['ChallengeSchema']>(
        row({ ...stillFilling, seats: accepted(stillFilling.seats) }),
      );
    });

    await sayYes();
    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(THE_ROOM), { timeout: 5000 });
  });

  /**
   * **The acceptance that completes a four lands, one tap later, in a room with a plan card, and
   * Now has the game as Planning.** The accept opens the game inline, so `GET /games` holds it on
   * the re-read the reply triggers; the room carries its `game_id`; and no plan exists yet, which
   * is the card with three empty slots and the rail's *Planning* tag. Asserted end to end because
   * the two are a join of three lists at two surfaces, and a stale one on either is a blank — and
   * because back from the room is the Chats list now, never the challenge screen.
   */
  it('lands in a room drawing the plan card, and Now draws the game as Planning', async () => {
    const PIOTR = 'ffffffff-0000-4000-8000-000000000006';
    const FOUR = [
      { player_id: EWA, nickname: 'ewa.m' },
      { player_id: OLA, nickname: 'ola.k' },
      { player_id: PIOTR, nickname: 'piotr' },
      { player_id: ME, nickname: 'me_' },
    ];
    const lastSeat = {
      sport: 'PADEL' as const,
      seats: [
        { side: 'A' as const, player_id: EWA, answer: 'ACCEPTED' as const, nickname: 'ewa.m' },
        { side: 'A' as const, player_id: OLA, answer: 'ACCEPTED' as const, nickname: 'ola.k' },
        { side: 'B' as const, player_id: PIOTR, answer: 'ACCEPTED' as const, nickname: 'piotr' },
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
    await openTheChallenge(detail(lastSeat), row(lastSeat), /^ewa\.m.*, Padel, .*to answer/);
    // Not a member until the yes: the list holds the others' room and not this reader's.
    stubConversations(transport, []);
    stubPlans(transport, []);

    transport.on('POST', `${DETAIL_PATH}/accept`, () => {
      // Everything the accept opened, as the reads after it find them: the game inline with
      // the accept, the room's membership derived live and its `game_id` noted, and the court's
      // plan row the reader's now (ADR-0164 §3).
      stubGames(transport, [game], READ_AT);
      stubPlans(transport, [
        {
          challenge_id: CHALLENGE_ID,
          anchor: READ_AT,
          place: null,
          day: null,
          hour: null,
          agreed_point: null,
        },
      ]);
      stubConversations(transport, [listed(FOUR, GAME, 'PADEL')]);
      stubConversation(transport, {
        read_at: READ_AT,
        conversation_id: ROOM,
        challenge_id: CHALLENGE_ID,
        game_id: GAME,
        sport: 'PADEL',
        members: FOUR,
        people: FOUR,
        entries: [],
      });
      stubEntries(transport, ROOM);
      const done = { ...lastSeat, standing: 'ON' as const, seats: accepted(lastSeat.seats) };
      transport.on('GET', DETAIL_PATH, () => json(detail(done)));
      return json<Wire['ChallengeSchema']>(row(done));
    });

    await sayYes();
    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));
    await waitFor(() => expect(screen).toHavePathname(THE_ROOM), { timeout: 5000 });

    // The plan card, pinned under the header: three slots, nothing agreed.
    expect(await screen.findByLabelText('Where: Not agreed yet')).toBeTruthy();

    // Back is the Chats list — not the celebration, not the challenge screen — and Now, one
    // tab over, has the game with the rail's word on it.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(screen.getByLabelText('Now'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByText('Planning')).toBeTruthy();
    expect(screen.getAllByText('Not agreed yet')).toHaveLength(3);
  });

  /**
   * **Past the bound the door is the list.** A room that never lists within the bound is a
   * delivery worker that is down or behind; the tap lands on the Chats list, where the row will
   * appear, rather than dead-ending on a celebration.
   */
  it('lands on the Chats list when the room is not listed within the bound', async () => {
    await openTheChallenge();
    stubConversations(transport, []);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    await sayYes();
    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));

    // Not at once: the list is asked its whole bound first, and the tap waits on the button.
    await waitFor(() =>
      expect(
        transport.requestsTo('GET', CONVERSATIONS_PATH).length - before,
      ).toBeGreaterThanOrEqual(3),
    );
    expect(screen).toHavePathname(YES_SCREEN);

    await waitFor(() => expect(screen).toHavePathname('/chats'), { timeout: 9000 });
    expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length - before).toBeGreaterThanOrEqual(
      8,
    );
    expect(tabs()).toHaveLength(5);
  }, 12000);
});

describe('Later', () => {
  it('lands on the Chats list with the challenge screen gone', async () => {
    await openTheChallenge();
    stubConversations(transport, []);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    await sayYes();
    fireEvent.press(yesScreen().getByRole('button', { name: LATER }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(tabs()).toHaveLength(5);
    // The challenge screen went with it: the list is the bottom of the stack, with nothing to
    // go back to, and no door of the celebration is left anywhere on the tree.
    expect(router.canGoBack()).toBe(false);
    expect(screen.queryByRole('button', { name: LATER, ...HIDDEN_TOO })).toBeNull();
  });

  it('is what the device’s back does', async () => {
    watchHardwareBack();
    await openTheChallenge();
    stubConversations(transport, []);
    stubAccept(
      row({ standing: 'ON', seats: accepted(SINGLES) }),
      detail({ standing: 'ON', seats: accepted(SINGLES) }),
    );

    await sayYes();

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    // And the challenge screen is gone with it, exactly as after *Later*.
    expect(router.canGoBack()).toBe(false);
    expect(screen.queryByRole('button', { name: IM_IN, ...HIDDEN_TOO })).toBeNull();
  });
});

describe('a padel four', () => {
  const OLA_SEAT: Seat = {
    side: 'A',
    player_id: OLA,
    answer: null,
    answer_by: at(20),
    nickname: 'ola.n',
  };
  const KUBA_SEAT: Seat = { side: 'B', player_id: KUBA, answer: 'ACCEPTED', nickname: 'kuba.w' };
  const EWA_SEAT: Seat = { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' };

  /**
   * Three faces and one empty seat, reader first and the reader's side left — the seat still
   * deciding is Ola's, on side A beside Ewa, and the reader is on side B beside Kuba.
   */
  it('draws three faces and an empty seat, reader first, with the reader on side B', async () => {
    const seats: Seat[] = [
      EWA_SEAT,
      OLA_SEAT,
      KUBA_SEAT,
      { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
    ];
    const four = { sport: 'PADEL' as const, seats };
    await openTheChallenge(detail(four), row(four), /^ewa\.m.*, Padel, .*to answer/);
    stubConversations(transport, []);
    stubAccept(
      row({ ...four, seats: accepted(seats) }),
      detail({ ...four, seats: accepted(seats) }),
    );

    await sayYes();

    const spoken = yesAnnouncement({
      yours: [
        { kind: 'person', playerId: ME, nickname: 'me_' },
        { kind: 'person', playerId: KUBA, nickname: 'kuba.w' },
      ],
      theirs: [{ kind: 'person', playerId: EWA, nickname: 'ewa.m' }, { kind: 'empty' }],
    });
    expect(await yesScreen().findByRole('header', { name: spoken })).toBeTruthy();
    expect(yesScreen().getAllByTestId('yes-tile-poster')).toHaveLength(3);
    expect(yesScreen().getAllByTestId('yes-tile-empty')).toHaveLength(1);
    // Reader first, on the left: the first tile drawn is yours.
    const initials = yesScreen()
      .getAllByText(/^[A-Z]{2}$/, HIDDEN_TOO)
      .map((one) => one.props.children);
    expect(initials).toEqual(['ME', 'KW', 'EM']);
  });

  it('puts the reader’s side left when their seat is on side A', async () => {
    const seats: Seat[] = [
      { side: 'A', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
      OLA_SEAT,
      KUBA_SEAT,
      { side: 'B', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
    ];
    const four = { sport: 'PADEL' as const, seats };
    // The row names the others in seat order, so it opens with Ola here rather than Ewa.
    await openTheChallenge(detail(four), row(four), /^ola\.n.*, Padel, .*to answer/);
    stubConversations(transport, []);
    stubAccept(
      row({ ...four, seats: accepted(seats) }),
      detail({ ...four, seats: accepted(seats) }),
    );

    await sayYes();

    const spoken = yesAnnouncement({
      yours: [{ kind: 'person', playerId: ME, nickname: 'me_' }, { kind: 'empty' }],
      theirs: [
        { kind: 'person', playerId: KUBA, nickname: 'kuba.w' },
        { kind: 'person', playerId: EWA, nickname: 'ewa.m' },
      ],
    });
    expect(await yesScreen().findByRole('header', { name: spoken })).toBeTruthy();
    const initials = yesScreen()
      .getAllByText(/^[A-Z]{2}$/, HIDDEN_TOO)
      .map((one) => one.props.children);
    expect(initials).toEqual(['ME', 'KW', 'EM']);
  });
});

describe('a link that is not a yes', () => {
  it('draws nothing and leaves for the Chats list when the reader holds no accepted seat', async () => {
    await openTheChallenge();
    stubConversations(transport, []);

    // Straight to the route, on a challenge the reader has not said yes to.
    act(() => router.push({ pathname: YES_SCREEN, params: { which: 'challenge' } }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(screen.queryByRole('button', { name: LATER })).toBeNull();
  });

  it('leaves for the Chats list on a which-yes it cannot read', async () => {
    await openTheChallenge();
    stubConversations(transport, []);

    act(() => router.push({ pathname: YES_SCREEN, params: { which: 'birthday' } }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
  });
});
