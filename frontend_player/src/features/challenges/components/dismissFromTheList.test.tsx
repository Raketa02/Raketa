/**
 * ***Remove this row* from the Chats list, walked the way the one left behind walks it**: the real
 * route tree, the real shell, the real rows, a finger on one of them, and only `fetch` faked
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md),
 * [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §5).
 *
 * The court both readings fit (ADR-0172 §7): my padel four, everybody said yes, and the three of
 * them left one by one — so the row reads *tomek.p left* under a `Called off` tag, and I am alone
 * on it with a day to wait. The row swipes to reveal *Remove this row*, which posts the
 * challenge's own dismissal door — no sheet — and the row is gone on the reply before any
 * re-read, with the Now card's list dropped and both lists re-read; a refusal re-reads and says
 * nothing; the revealed button is reachable by the row's accessibility action as well as by the
 * swipe; the invitee still deciding when the court was called off, and the hour's row naming
 * nobody, have the same door; and every other ending's row still reveals nothing. The card's own
 * trash is `nowRail.test.tsx`'s.
 *
 * The finger is `test-support/swipe.ts`'. The words are the deck's — `challengePresentation.ts`.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { gameKeys, type Game } from '@/features/games/types';
import {
  CHALLENGES_PATH,
  GAMES_PATH,
  GATE_USER,
  launchIntoClassicPlay,
  stubChallenges,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { swipe } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { REMOVE_THE_CHALLENGE } from './challengeDetailPresentation';
import { CALLED_OFF_TAG, NOBODY_FILLED_THE_SEAT, REMOVE_THIS_ROW } from './challengePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';
const EWA = 'dddddddd-0000-4000-8000-000000000004';

const LEFT_ALONE = 'ffffffff-0000-4000-8000-000000000006';
const PRESSED = 'ffffffff-0000-4000-8000-000000000007';
const LAPSED = 'ffffffff-0000-4000-8000-000000000008';
const GAME = 'aaaaaaaa-0000-4000-8000-00000000000a';
const OTHER_GAME = 'aaaaaaaa-0000-4000-8000-00000000000b';

const DISMISSAL_PATH = `${CHALLENGES_PATH}/${LEFT_ALONE}/dismissal`;
const READ_AT = '2026-09-12T09:00:00Z';
const ENDED_AT = '2026-09-12T08:00:00Z';
const REVEAL = theme.size.swipeRow.reveal;

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

/** My padel four that everybody left: the row this file is about. */
const LEFT_ALONE_ROW: Wire['ChallengeSchema'] = {
  challenge_id: LEFT_ALONE,
  sport: 'PADEL',
  organiser_id: ME,
  standing: 'CALLED_OFF',
  opened_at: '2026-09-11T08:00:00Z',
  ended_at: ENDED_AT,
  ended_by: TOMEK,
  game_id: GAME,
  seats: [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'A', player_id: EWA, answer: 'LEFT', name: 'ewa.m' },
    { side: 'B', player_id: OLA, answer: 'LEFT', name: 'ola.k' },
    { side: 'B', player_id: TOMEK, answer: 'LEFT', name: 'tomek.p' },
  ],
};

/** Somebody else's squash game that Ola pressed *Call it off* on, with me still seated. */
const PRESSED_ROW: Wire['ChallengeSchema'] = {
  challenge_id: PRESSED,
  sport: 'SQUASH',
  organiser_id: OLA,
  standing: 'CALLED_OFF',
  opened_at: '2026-09-11T07:00:00Z',
  ended_at: ENDED_AT,
  ended_by: OLA,
  game_id: OTHER_GAME,
  seats: [
    { side: 'A', player_id: OLA, answer: 'ACCEPTED', name: 'ola.k' },
    { side: 'B', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
  ],
};

/**
 * Ewa's tennis: she asked me to fill a seat somebody left and then left herself, the last on it,
 * so the court was called off while I was still deciding — a row, and never a card.
 */
const ASKED = 'ffffffff-0000-4000-8000-000000000009';
const ASKED_ROW: Wire['ChallengeSchema'] = {
  challenge_id: ASKED,
  sport: 'TENNIS',
  organiser_id: EWA,
  standing: 'CALLED_OFF',
  opened_at: '2026-09-11T06:00:00Z',
  ended_at: ENDED_AT,
  ended_by: EWA,
  game_id: 'aaaaaaaa-0000-4000-8000-00000000000c',
  seats: [
    { side: 'A', player_id: EWA, answer: 'LEFT', name: 'ewa.m' },
    { side: 'B', player_id: ME, answer: null, answer_by: '2026-09-13T08:00:00Z', name: 'me_' },
  ],
};

/** Ola's padel four the hour called off: nobody filled Tomek's seat by the day. */
const THE_HOURS = 'ffffffff-0000-4000-8000-00000000000a';
const THE_HOURS_ROW: Wire['ChallengeSchema'] = {
  challenge_id: THE_HOURS,
  sport: 'PADEL',
  organiser_id: OLA,
  standing: 'CALLED_OFF',
  opened_at: '2026-09-10T06:00:00Z',
  ended_at: ENDED_AT,
  ended_by: null,
  game_id: 'aaaaaaaa-0000-4000-8000-00000000000d',
  seats: [
    { side: 'A', player_id: OLA, answer: 'ACCEPTED', name: 'ola.k' },
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'B', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
    { side: 'B', player_id: TOMEK, answer: 'LEFT', name: 'tomek.p' },
  ],
};

/** A send of mine whose day ran out: an ending on its shelf, which reveals nothing. */
const LAPSED_ROW: Wire['ChallengeSchema'] = {
  challenge_id: LAPSED,
  sport: 'TENNIS',
  organiser_id: ME,
  standing: 'LAPSED',
  opened_at: '2026-09-10T08:00:00Z',
  ended_at: ENDED_AT,
  ended_by: EWA,
  seats: [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'B', player_id: EWA, answer: null, answer_by: ENDED_AT, name: 'ewa.m' },
  ],
};

/** The game behind the padel four, as Now's rail reads it. */
const CALLED_OFF_GAME: Wire['GameSchema'] = {
  game_id: GAME,
  challenge_id: LEFT_ALONE,
  sport: 'PADEL',
  kind: 'COUNTED',
  standing: 'CALLED_OFF',
  planned_at: '2026-09-13T18:00:00Z',
  entry_closes_at: null,
  called_off_at: ENDED_AT,
  called_off_by: { player_id: TOMEK, name: 'tomek.p' },
  seats: [
    { side: 'A', player_id: ME, name: 'me_' },
    { side: 'A', player_id: null, name: null },
    { side: 'B', player_id: null, name: null },
    { side: 'B', player_id: null, name: null },
  ],
  proposals: [],
};

let transport: Transport;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubGames(transport, [CALLED_OFF_GAME], READ_AT);
  stubPlans(transport, []);
  stubConversations(transport, []);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app with the rows, and open the Chats tab. */
async function openChats(
  rows: readonly Wire['ChallengeSchema'][] = [LEFT_ALONE_ROW, PRESSED_ROW, LAPSED_ROW],
) {
  stubChallenges(transport, rows, READ_AT);
  await launchIntoClassicPlay(transport);

  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
  await screen.findByLabelText(/^tomek\.p, Padel/);
}

const leftAlone = () => screen.getByLabelText(/^tomek\.p, Padel/);
const leftAloneIfListed = () => screen.queryByLabelText(/^tomek\.p, Padel/);
const pressed = () => screen.getByLabelText(/^ola\.k, Squash/);
const lapsed = () => screen.getByLabelText(/^ewa\.m, Tennis/);

/**
 * The dismissal answers, and **the server's lists tell the truth from then on**: the row and the
 * card are subtracted for me. A stub that went on serving them would hand them back on the
 * re-read, which is a server that never learned of the act.
 */
function dismissalAnswers() {
  transport.on('POST', DISMISSAL_PATH, () => {
    stubChallenges(transport, [PRESSED_ROW, LAPSED_ROW], READ_AT);
    stubGames(transport, [], READ_AT);
    return noContent();
  });
}

/** Swipe my row open, and press what it reveals. */
async function revealAndPress() {
  swipe(leftAlone(), -REVEAL);
  fireEvent.press(await screen.findByRole('button', { name: REMOVE_THIS_ROW }));
}

describe('the swipe', () => {
  it('reveals Remove this row on the called-off row I am alone on, and sends nothing yet', async () => {
    await openChats();

    expect(swipe(leftAlone(), -REVEAL)).toBe(true);

    expect(await screen.findByRole('button', { name: REMOVE_THIS_ROW })).toBeTruthy();
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(transport.requestsTo('POST', DISMISSAL_PATH)).toEqual([]);
  });

  /** The presser's court too: anybody still seated may clear it, the presser included. */
  it('reveals it on a called-off row somebody else pressed, while I am still seated', async () => {
    await openChats();

    expect(swipe(pressed(), -REVEAL)).toBe(true);
    expect(await screen.findByRole('button', { name: REMOVE_THIS_ROW })).toBeTruthy();
  });

  /**
   * The reader the challenge's door exists for (ADR-0175 §5): asked to fill a seat, still deciding
   * when the last departure called the court off — a row, never a card.
   */
  it('reveals it to the invitee the court was called off on while they were deciding', async () => {
    await openChats([LEFT_ALONE_ROW, ASKED_ROW]);
    const askedPath = `${CHALLENGES_PATH}/${ASKED}/dismissal`;
    transport.on('POST', askedPath, () => {
      stubChallenges(transport, [LEFT_ALONE_ROW], READ_AT);
      return noContent();
    });

    const row = screen.getByLabelText(/^ewa\.m, Tennis/);
    expect(swipe(row, -REVEAL)).toBe(true);
    fireEvent.press(await screen.findByRole('button', { name: REMOVE_THIS_ROW }));

    await waitFor(() => expect(transport.requestsTo('POST', askedPath)).toHaveLength(1));
    await waitFor(() => expect(screen.queryByLabelText(/^ewa\.m, Tennis/)).toBeNull());
    expect(leftAlone()).toBeTruthy();
  });

  /** The hour's row names nobody, draws the people the reader waited with, and has the same door. */
  it('reveals it on the row the hour called off, which says nobody filled the seat', async () => {
    await openChats([LEFT_ALONE_ROW, THE_HOURS_ROW]);

    const row = await screen.findByLabelText(/^ola\.k and ewa\.m, Padel/);
    expect(row.props.accessibilityLabel).toContain(NOBODY_FILLED_THE_SEAT);
    expect(row.props.accessibilityLabel).not.toMatch(/tomek\.p/);
    expect(swipe(row, -REVEAL)).toBe(true);
    expect(await screen.findByRole('button', { name: REMOVE_THIS_ROW })).toBeTruthy();
  });

  /** Every other ending keeps its day and moves nothing — no dead controls (#324). */
  it('reveals nothing on any other ending’s row', async () => {
    await openChats();

    expect(swipe(lapsed(), -REVEAL)).toBe(false);
    expect(screen.queryByRole('button', { name: REMOVE_THIS_ROW })).toBeNull();
    expect(lapsed().props.accessibilityActions).toBeUndefined();
  });

  /** A swipe is never the only path: the row offers the act in the rotor, under its own word. */
  it('is reachable from the row’s accessibility action as well', async () => {
    await openChats();
    dismissalAnswers();

    const row = leftAlone();
    expect(row.props.accessibilityActions).toEqual([
      expect.objectContaining({ label: REMOVE_THIS_ROW }),
    ]);
    const [action] = row.props.accessibilityActions as readonly { name: string }[];

    fireEvent(row, 'accessibilityAction', { nativeEvent: { actionName: action?.name } });

    await waitFor(() => expect(transport.requestsTo('POST', DISMISSAL_PATH)).toHaveLength(1));
    await waitFor(() => expect(leftAloneIfListed()).toBeNull());
  });
});

/**
 * A game as the games list holds it once mapped — whole, because Home's badge in the bar reads
 * every game in that list on every screen (#550), and a half-built one is not a game it can fold.
 * Two called-off courts; which one the reply drops is what the walk below is about.
 */
function cachedGame(gameId: string, challengeId: string): Game {
  return {
    gameId,
    challengeId,
    sport: 'padel',
    standing: 'CALLED_OFF',
    seats: [{ side: 'A', playerId: ME, name: 'me_' }, { side: 'B' }],
    plannedAt: READ_AT,
    calledOffAt: READ_AT,
    proposals: [],
    readAt: READ_AT,
  };
}

describe('the dismissal', () => {
  /**
   * **Gone without a refetch, and no sheet.** The reply says the court is cleared for me, and
   * the row is dropped on it — so the reply is what takes the row away, and the re-read that
   * follows is held here to prove it had nothing to do with it. The card's list loses the game
   * on the same reply.
   */
  it('takes the row away on the reply, with no sheet, and drops the card from the games list', async () => {
    await openChats();
    transport.on('POST', DISMISSAL_PATH, () => noContent());
    queryClient.setQueryData(gameKeys.list(), [
      cachedGame(GAME, LEFT_ALONE),
      cachedGame(OTHER_GAME, PRESSED),
    ]);
    const held = new Promise<Response>(() => undefined);
    transport.on('GET', CHALLENGES_PATH, () => held);
    transport.on('GET', GAMES_PATH, () => held);

    await revealAndPress();

    await waitFor(() => expect(leftAloneIfListed()).toBeNull());
    expect(pressed()).toBeTruthy();
    expect(lapsed()).toBeTruthy();
    expect(screen.queryByText(/before you|are you sure/i)).toBeNull();
    expect(transport.requestsTo('POST', DISMISSAL_PATH)).toHaveLength(1);
    expect(queryClient.getQueryData(gameKeys.list())).toEqual([cachedGame(OTHER_GAME, PRESSED)]);
  });

  /**
   * And then both lists a called-off court is drawn on are re-read, and the row is not back. The
   * games list is held on every screen by Home's badge in the bar (#550), so it is counted as a
   * read like the challenges.
   */
  it('re-reads the challenges and the games', async () => {
    await openChats();
    dismissalAnswers();
    const before = {
      challenges: transport.requestsTo('GET', CHALLENGES_PATH).length,
      games: transport.requestsTo('GET', GAMES_PATH).length,
    };

    await revealAndPress();

    await waitFor(() => {
      expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBeGreaterThan(
        before.challenges,
      );
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(before.games);
    });
    expect(leftAloneIfListed()).toBeNull();
    expect(screen.queryByText(CALLED_OFF_TAG)).toBeTruthy(); // Ola's court still wears its tag.
  });

  /** Pending, never optimistic: the row stays until the reply says it is gone. */
  it('keeps the row while the act is in flight', async () => {
    let answer: () => void = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', DISMISSAL_PATH, async () => {
      await held;
      stubChallenges(transport, [PRESSED_ROW, LAPSED_ROW], READ_AT);
      return noContent();
    });
    await openChats();

    await revealAndPress();

    await waitFor(() => expect(transport.requestsTo('POST', DISMISSAL_PATH)).toHaveLength(1));
    expect(leftAlone()).toBeTruthy();

    answer();
    await waitFor(() => expect(leftAloneIfListed()).toBeNull());
  });
});

describe('a refused dismissal', () => {
  /**
   * **A re-read and no words**, the trash's own posture: the row a listener is on is not the row
   * the server holds, and the fold the re-read lands on is the answer. Here the server still
   * holds it, so the row stays.
   */
  it('re-reads both lists and says nothing, and the row stays', async () => {
    await openChats();
    transport.on('POST', DISMISSAL_PATH, () => errorResponse(409, 'game_is_not_called_off'));
    const before = {
      challenges: transport.requestsTo('GET', CHALLENGES_PATH).length,
      games: transport.requestsTo('GET', GAMES_PATH).length,
    };

    await revealAndPress();

    await waitFor(() => {
      expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBeGreaterThan(
        before.challenges,
      );
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(before.games);
    });
    expect(leftAlone()).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
