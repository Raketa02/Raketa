/**
 * **Now's rail, walked the way a player walks it**: the real route tree, the real shell, the real
 * Now tab, and only `fetch` faked.
 *
 * Most of [#367](https://github.com/Raketa02/Raketa/issues/367)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the tab stops being a placeholder, the
 * card's name is folded from the standing, the slot count and the clock at read time, every door
 * in §5.2's table works, the body goes wherever the button goes, the ✉ opens the room on every
 * live card, an ending keeps its card for a day, and the order is the server's.
 *
 * The ladder itself is `domain/ladder.test.ts`'s and the words are
 * `nowPresentation.test.ts`'s; what is asserted here is that the screen is wired to both, and it
 * asserts against the **copy deck** rather than against strings wherever a sentence has a home.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { NOW_COPY } from '@/features/shell/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchSignedIn,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { CARD_TAG, DOOR_LABEL, NOTHING_LEFT_TO_AGREE, gamesHeading } from './nowPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';

/** Four days before it, which is when the line-up completed. */
const PLANNED_AT = '2026-09-08T09:00:00Z';

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

const PAIR: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, nickname: 'me_' },
  { player_id: TOMEK, nickname: 'tomek.p' },
];

function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: PLANNED_AT,
    entry_closes_at: '2026-09-20T09:00:00Z',
    seats: [
      { side: 'A', player_id: ME, nickname: 'me_' },
      { side: 'B', player_id: TOMEK, nickname: 'tomek.p' },
    ],
    proposals: [],
    ...over,
  };
}

function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return { game_id: GAME, place: null, day: null, hour: null, agreed_point: null, ...over };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land on the Now tab with these games, these plans and — optionally — a room to open. */
async function landOnNow({
  games = [game()],
  plans = [],
  room = true,
  readAt = READ_AT,
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
  readonly room?: boolean;
  readonly readAt?: string;
} = {}) {
  stubGames(transport, games, readAt);
  stubPlans(transport, plans);
  stubConversations(
    transport,
    room
      ? [
          {
            conversation_id: ROOM,
            challenge_id: CHALLENGE,
            game_id: GAME,
            sport: 'PADEL',
            members: PAIR,
            last_entry: null,
          },
        ]
      : [],
  );

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));
}

describe('the tab stops being a placeholder', () => {
  it('says what Now is and points at the act when it holds nothing', async () => {
    await landOnNow({ games: [] });

    expect(await screen.findByText(NOW_COPY.empty.line)).toBeTruthy();
    expect(screen.getByText(NOW_COPY.empty.act)).toBeTruthy();
    expect(screen.getByText(gamesHeading(0))).toBeTruthy();
  });

  it('heads the rail with its own count', async () => {
    await landOnNow({ games: [game(), game({ game_id: 'aaaaaaaa-0000-4000-8000-00000000000a' })] });

    expect(await screen.findByText(gamesHeading(2))).toBeTruthy();
  });
});

describe('the four rungs, folded at read time', () => {
  /** The instant is the games list's, never the phone's — `GET /plans` carries none. */
  const nameOf = async (agreed: Wire['PlanSchema'] | undefined) => {
    await landOnNow({ plans: agreed === undefined ? [] : [agreed] });
    return screen;
  };

  it('is Planning with the next slot to agree, where nothing has been', async () => {
    await nameOf(undefined);

    expect(await screen.findByText(CARD_TAG.planning!.label)).toBeTruthy();
    expect(screen.getByText('Still to agree: where')).toBeTruthy();
  });

  it('is Game on once all three are filled and the day is ahead', async () => {
    await nameOf(
      plan({
        place: 'Zabłocie Sport',
        day: '2026-09-19',
        hour: '18:00',
        agreed_point: '2026-09-19T16:00:00Z',
      }),
    );

    expect(await screen.findByText(CARD_TAG['game-on']!.label)).toBeTruthy();
    expect(screen.getByText(NOTHING_LEFT_TO_AGREE)).toBeTruthy();
    // The hour is the figure, so the line takes the day and the place and never the hour again.
    expect(screen.getByText('18:00')).toBeTruthy();
    expect(screen.getByText('Saturday · Zabłocie Sport')).toBeTruthy();
  });

  it('is Today on the agreed day, whatever is still to agree', async () => {
    await nameOf(plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' }));

    expect(await screen.findByText(CARD_TAG.today!.label)).toBeTruthy();
    // #324's second amendment: a Today card may genuinely have no hour, and this is the alarm.
    expect(screen.getByText('Still to agree: where')).toBeTruthy();
  });

  it('is Needs result once the agreed point has passed, with the window left on it', async () => {
    await nameOf(
      plan({
        place: 'Zabłocie Sport',
        day: '2026-09-12',
        hour: '08:00',
        agreed_point: '2026-09-12T06:00:00Z',
      }),
    );

    expect(await screen.findByText(CARD_TAG['needs-result']!.label)).toBeTruthy();
    expect(screen.getByText('8 days left')).toBeTruthy();
  });
});

describe('every door in the table', () => {
  const openTheGame = async () => waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));

  /**
   * **The named door is drawn and hidden**, so every query for it says so.
   *
   * §24.5 makes the card and its door one accessibility element whose name ends with the verb, so
   * a second element announcing `Open` beside it would be the double announcement 6.8 refuses. A
   * test that could not see it would be testing the wrong half.
   */
  const door = (verb: string) => screen.findByText(verb, { includeHiddenElements: true });

  it('opens the game from the named door', async () => {
    await landOnNow();

    fireEvent.press(await door(DOOR_LABEL.open));
    await openTheGame();
  });

  /** #336 made the body and the door one action, so they go to one place. */
  it('opens the game from the body too', async () => {
    await landOnNow();

    fireEvent.press(await screen.findByLabelText(/Padel, singles/));
    await openTheGame();
  });

  it('opens the room from the ✉', async () => {
    await landOnNow();

    fireEvent.press(await screen.findByLabelText('Open the chat'));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  /** The join fails soft: a challenge with no room draws no door rather than a dead one. */
  it('draws no ✉ where there is no room to open', async () => {
    await landOnNow({ room: false });

    await door(DOOR_LABEL.open);
    expect(screen.queryByLabelText('Open the chat')).toBeNull();
  });

  it('names the door for the act the standing can take', async () => {
    await landOnNow({
      plans: [plan({ day: '2026-09-12', hour: '08:00', agreed_point: '2026-09-12T06:00:00Z' })],
    });

    expect(await door(DOOR_LABEL['we-played'])).toBeTruthy();
  });

  /** *Counted* offers nothing: the app does not name an act a state cannot take. */
  it('offers no door on an ending', async () => {
    await landOnNow({
      games: [game({ standing: 'CONFIRMED', played_at: READ_AT, entry_closes_at: null })],
    });

    expect(await screen.findByText(CARD_TAG.counted!.label)).toBeTruthy();
    for (const verb of Object.values(DOOR_LABEL)) {
      expect(screen.queryByText(verb, { includeHiddenElements: true })).toBeNull();
    }
  });
});

describe('how long an ending keeps its card', () => {
  const ended = (playedAt: string) =>
    game({ standing: 'CONFIRMED', played_at: playedAt, entry_closes_at: null });

  it('keeps it for a day', async () => {
    await landOnNow({ games: [ended('2026-09-11T10:00:00Z')] });

    expect(await screen.findByText(gamesHeading(1))).toBeTruthy();
    expect(screen.getByText(CARD_TAG.counted!.label)).toBeTruthy();
  });

  it('and then leaves, which is what keeps the day line honest', async () => {
    await landOnNow({ games: [ended('2026-09-11T08:00:00Z')] });

    expect(await screen.findByText(gamesHeading(0))).toBeTruthy();
    expect(screen.getByText(NOW_COPY.empty.line)).toBeTruthy();
  });
});

describe('the order', () => {
  /**
   * **The server's, and stable.** Nothing here re-sorts: a clock sort silently re-orders a
   * player's cards between sessions, and the cost of the served order is stated instead — a game
   * arranged this morning for next Saturday sits ahead of one arranged last week that is tonight.
   */
  it('is the one the list arrived in', async () => {
    const second = 'aaaaaaaa-0000-4000-8000-00000000000a';

    await landOnNow({
      games: [
        game({ standing: 'UNSCORED', played_at: READ_AT, entry_closes_at: null }),
        game({ game_id: second, challenge_id: 'cccccccc-0000-4000-8000-00000000000c' }),
      ],
    });

    const drawn = await screen.findAllByLabelText(/Padel, singles/);

    expect(drawn).toHaveLength(2);
    expect(drawn[0]?.props.accessibilityLabel).toContain(CARD_TAG.uncounted!.label);
    expect(drawn[1]?.props.accessibilityLabel).toContain(CARD_TAG.planning!.label);
  });
});
