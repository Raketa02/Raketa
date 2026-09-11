/**
 * **Now's rail, walked the way a player walks it**: the real route tree, the real shell, the real
 * Now tab, and only `fetch` faked.
 *
 * Most of [#367](https://github.com/Raketa02/Raketa/issues/367)'s and
 * [#413](https://github.com/Raketa02/Raketa/issues/413)'s acceptance criteria are assertions in
 * this file and opinions nowhere else — the tab stops being a placeholder, the card's name is
 * folded from the standing, the slot count and the clock at read time, the three slots are drawn
 * with the right ones settled, every door in §5.2's table works, **the body opens nothing**, the
 * bubble opens the room on every live card, a face is drawn where the room has one, an ending
 * keeps its card for a day, and the order is the server's.
 *
 * The ladder itself is `domain/ladder.test.ts`'s and the words are
 * `nowPresentation.test.ts`'s; what is asserted here is that the screen is wired to both, and it
 * asserts against the **copy deck** rather than against strings wherever a sentence has a home.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { Image, StyleSheet, View, type ViewStyle } from 'react-native';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { NOW_COPY } from '@/features/shell/types';
import { SEAT_NAME_LETTERS } from '@/features/play/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import {
  GATE_USER,
  launchSignedIn,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { GAME_CARD_NAMES } from '../domain/gameCard';
import { PLAN_SLOTS } from '../domain/slots';

import { ACCENT, CARD_TAG, FINISH_THE_PLAN, doorLabel, gamesHeading } from './nowPresentation';
import { NOT_AGREED_YET, SLOT_EYEBROW } from './planPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';

/** Four days before it, which is when the line-up completed. */
const PLANNED_AT = '2026-09-08T09:00:00Z';

/** A signed link, as the room mints one — the only address a photograph has. */
const TOMEK_PHOTO = 'https://photos.example.test/tomek.jpg?sig=abc';

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
  members = PAIR,
  readAt = READ_AT,
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
  readonly room?: boolean;
  readonly members?: readonly Wire['ConversationMemberSchema'][];
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
            members: [...members],
            people: [...members],
            last_entry: null,
          },
        ]
      : [],
  );

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));
}

/** The one card's body — the element a listener meets first, named for the tag and the sport. */
const theCard = () => screen.findByLabelText(/Padel/);

/**
 * **The three settled bars, in slot order**, found by the one width only a semantic bar has.
 *
 * Bright is agreed and dim is not, and the colours are read off the card's own accent table rather
 * than restated: what is asserted is that the card draws what the plan holds, not which lime.
 */
function bars(): readonly string[] {
  return screen
    .UNSAFE_getAllByType(View)
    .map((box) => StyleSheet.flatten(box.props.style as ViewStyle))
    .filter((style) => style?.width === theme.size.semanticBar)
    .map((style) => style.backgroundColor)
    .filter((fill): fill is string => typeof fill === 'string');
}

const BRIGHT = ACCENT.planning.bar;
const DIM = theme.color.onDarkHair;

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

/**
 * **The three mocks, as three fixtures.** Mock 1 has *where* set; mock 2 has *day* set; mock 3
 * has *where* and *day* set — and on all three the card is Planning, the tag says so, the three
 * slots are labelled in the app's own order, and the bar beside each one is bright exactly where
 * the plan holds a value.
 */
describe('the Planning card, against the three mocks', () => {
  const labels = () => PLAN_SLOTS.map((slot) => SLOT_EYEBROW[slot]);

  it('draws the tag and the three slot labels in slot order, on every one of them', async () => {
    await landOnNow({ plans: [plan({ place: 'Zabłocie Sport' })] });

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    for (const label of labels()) expect(screen.getByText(label)).toBeTruthy();
  });

  it('mock 1 — where is set: the place bright, the day and the time not agreed yet', async () => {
    await landOnNow({ plans: [plan({ place: 'Zabłocie Sport, court 3' })] });

    await theCard();
    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
    expect(bars()).toEqual([BRIGHT, DIM, DIM]);
  });

  it('mock 2 — day is set: the weekday whole and the date beside it, the rest not agreed', async () => {
    await landOnNow({ plans: [plan({ day: '2026-09-13', agreed_point: '2026-09-13T22:00:00Z' })] });

    await theCard();
    expect(screen.getByText('Sunday')).toBeTruthy();
    expect(screen.getByText('13 Sep')).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
    expect(bars()).toEqual([DIM, BRIGHT, DIM]);
  });

  it('mock 3 — where and day are set: two bright bars and one dim', async () => {
    await landOnNow({
      plans: [
        plan({
          place: 'Zabłocie Sport',
          day: '2026-09-13',
          agreed_point: '2026-09-13T22:00:00Z',
        }),
      ],
    });

    await theCard();
    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.getByText('Sunday')).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(1);
    expect(bars()).toEqual([BRIGHT, BRIGHT, DIM]);
  });

  /** §20.4: the visible place is the shorter value, the spoken one is whole. */
  it('shortens the place for the eye and speaks it whole', async () => {
    await landOnNow({ plans: [plan({ place: 'Zabłocie Sport, court 3' })] });

    const card = await theCard();

    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.queryByText('Zabłocie Sport, court 3')).toBeNull();
    expect(card.props.accessibilityLabel).toContain('Zabłocie Sport, court 3');
  });
});

describe('the sport word', () => {
  it('is the sport alone on a counted game', async () => {
    await landOnNow();

    expect(await screen.findByText('Padel')).toBeTruthy();
  });

  it('marks a friendly, and nothing else about the game', async () => {
    await landOnNow({ games: [game({ kind: 'FRIENDLY' })] });

    expect(await screen.findByText('Padel · Friendly')).toBeTruthy();
    expect(screen.queryByText(/singles/i)).toBeNull();
  });
});

describe('the four rungs, folded at read time', () => {
  /** The instant is the games list's, never the phone's — `GET /plans` carries none. */
  const nameOf = async (agreed: Wire['PlanSchema'] | undefined) => {
    await landOnNow({ plans: agreed === undefined ? [] : [agreed] });
    return screen;
  };

  it('is Planning with nothing agreed, and every slot says so', async () => {
    await nameOf(undefined);

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(3);
    expect(bars()).toEqual([DIM, DIM, DIM]);
  });

  it('is Game on once all three are filled and the day is ahead, with three bright bars', async () => {
    await nameOf(
      plan({
        place: 'Zabłocie Sport',
        day: '2026-09-19',
        hour: '18:00',
        agreed_point: '2026-09-19T16:00:00Z',
      }),
    );

    expect(await screen.findByText(CARD_TAG['game-on']!)).toBeTruthy();
    expect(screen.getByText('18:00')).toBeTruthy();
    expect(screen.getByText('Saturday')).toBeTruthy();
    expect(screen.getByText('19 Sep')).toBeTruthy();
    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.queryByText(NOT_AGREED_YET)).toBeNull();
    // Every card but Planning is drawn on the soft default — the same bar in the same colour.
    expect(bars()).toEqual(Array(3).fill(ACCENT['game-on'].bar));
  });

  it('is Today on the agreed day, whatever is still to agree', async () => {
    await nameOf(plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' }));

    expect(await screen.findByText(CARD_TAG.today!)).toBeTruthy();
    // #324's second amendment: a Today card may genuinely have no hour, and the dim bar is the alarm.
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
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

    expect(await screen.findByText(CARD_TAG['needs-result']!)).toBeTruthy();
    expect(screen.getByText('8 days left')).toBeTruthy();
  });
});

describe('every door in the table', () => {
  const openTheGame = async () => waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));

  it('opens the game from Finish the plan on Planning', async () => {
    await landOnNow();

    fireEvent.press(await screen.findByText(FINISH_THE_PLAN));
    await openTheGame();
  });

  /** The body is not a door: the two buttons are the only doors, and pressing the card does nothing. */
  it('opens nothing from the body', async () => {
    await landOnNow();

    const card = await theCard();
    fireEvent.press(card);

    expect(card.props.accessibilityRole).toBeUndefined();
    expect(card.props.onPress).toBeUndefined();
    expect(screen).toHavePathname('/');
  });

  it('opens the room from the bubble', async () => {
    await landOnNow();

    fireEvent.press(await screen.findByLabelText(OPEN_THE_CHAT));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  /** The join fails soft: a challenge with no room draws no bubble rather than a dead one. */
  it('draws no bubble where there is no room to open', async () => {
    await landOnNow({ room: false });

    await screen.findByText(FINISH_THE_PLAN);
    expect(screen.queryByLabelText(OPEN_THE_CHAT)).toBeNull();
  });

  it('names the door for the act the standing can take', async () => {
    await landOnNow({
      plans: [plan({ day: '2026-09-12', hour: '08:00', agreed_point: '2026-09-12T06:00:00Z' })],
    });

    expect(await screen.findByText(doorLabel('needs-result')!)).toBeTruthy();
  });

  /** *Counted* offers nothing: the app does not name an act a state cannot take. */
  it('offers no door on an ending', async () => {
    await landOnNow({
      games: [game({ standing: 'CONFIRMED', played_at: READ_AT, entry_closes_at: null })],
    });

    expect(await screen.findByText(CARD_TAG.counted!)).toBeTruthy();
    const verbs = GAME_CARD_NAMES.map(doorLabel).filter(
      (verb): verb is string => verb !== undefined,
    );
    for (const verb of new Set(verbs)) expect(screen.queryByText(verb)).toBeNull();
  });
});

/**
 * **Every other name still draws its door's word and its one line** — the same shell on soft
 * defaults, so no card loses a fact it drew before. One fixture per name the rail can reach, each
 * asserting the wide door's word off the deck and the line the standing says.
 */
describe('every other name, on the same shell', () => {
  const FULL = {
    place: 'Zabłocie Sport',
    day: '2026-09-19',
    hour: '18:00',
    agreed_point: '2026-09-19T16:00:00Z',
  };

  it.each([
    ['game-on', game(), plan(FULL), undefined],
    ['today', game(), plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' }), undefined],
    [
      'confirm',
      game({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-11T18:00:00Z',
        entry_closes_at: null,
        proposals: [
          {
            side: 'B',
            proposed_by: TOMEK,
            score: { sets: [{ a: 4, b: 6 }] },
            proposed_at: '2026-09-11T20:00:00Z',
            answer_by: '2026-09-13T20:00:00Z',
            settles_at: '2026-09-13T20:00:00Z',
          },
        ],
      }),
      undefined,
      /^tomek\.p put a score up\./,
    ],
    [
      'counted',
      game({ standing: 'CONFIRMED', played_at: READ_AT, entry_closes_at: null }),
      undefined,
      'Agreed.',
    ],
    [
      'uncounted',
      game({ standing: 'UNSCORED', played_at: READ_AT, entry_closes_at: null }),
      undefined,
      'Nobody agreed a score.',
    ],
    [
      'never-played',
      game({ standing: 'NEVER_PLAYED', entry_closes_at: '2026-09-12T08:00:00Z' }),
      undefined,
      /^Nobody said this one happened before the window closed/,
    ],
  ] as const)('%s draws its tag, its door and its line', async (name, served, agreed, line) => {
    await landOnNow({ games: [served], plans: agreed === undefined ? [] : [agreed] });

    // `findAll`, because the word can be drawn twice: on *Confirm the result* the door says it too.
    expect((await screen.findAllByText(CARD_TAG[name]!)).length).toBeGreaterThan(0);

    // By role, because on *Confirm the result* the tag's word and the door's verb coincide: the
    // name is a word in a pill and the door is the one that is a button.
    const verb = doorLabel(name);
    if (verb === undefined) {
      for (const other of GAME_CARD_NAMES.map(doorLabel)) {
        if (other !== undefined) expect(screen.queryByRole('button', { name: other })).toBeNull();
      }
    } else {
      expect(screen.getByRole('button', { name: verb })).toBeTruthy();
    }

    if (line !== undefined) expect(screen.getByText(line)).toBeTruthy();
  });
});

describe('the court', () => {
  /** The ring is the mark; the caption is the handle's first letters on every seat, yours too. */
  it('captions your own seat with three letters of your handle, never with you', async () => {
    await landOnNow();

    await theCard();
    // The court is drawn into a hidden subtree — the card's own name says the sport — so the
    // captions are looked for where they are drawn rather than where they are announced.
    const drawn = { includeHiddenElements: true };

    expect(screen.getByText('me_'.slice(0, SEAT_NAME_LETTERS), drawn)).toBeTruthy();
    expect(screen.getByText('tomek.p'.slice(0, SEAT_NAME_LETTERS), drawn)).toBeTruthy();
    expect(screen.queryByText('you', drawn)).toBeNull();
  });

  it('draws a face where the room has a photograph, and posters where it has none', async () => {
    await landOnNow({
      members: [
        { player_id: ME, nickname: 'me_' },
        { player_id: TOMEK, nickname: 'tomek.p', photo_id: 'p1', photo_url: TOMEK_PHOTO },
      ],
    });

    await theCard();
    const faces = screen.UNSAFE_getAllByType(Image).map((image) => image.props.source);

    expect(faces).toEqual([{ uri: TOMEK_PHOTO }]);
  });

  it('draws posters in every seat where there is no room, and nothing fails', async () => {
    await landOnNow({ room: false });

    await theCard();
    expect(screen.UNSAFE_queryAllByType(Image)).toHaveLength(0);
  });
});

describe('how long an ending keeps its card', () => {
  const ended = (playedAt: string) =>
    game({ standing: 'CONFIRMED', played_at: playedAt, entry_closes_at: null });

  it('keeps it for a day', async () => {
    await landOnNow({ games: [ended('2026-09-11T10:00:00Z')] });

    expect(await screen.findByText(gamesHeading(1))).toBeTruthy();
    expect(screen.getByText(CARD_TAG.counted!)).toBeTruthy();
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

    const drawn = await screen.findAllByLabelText(/Padel/);

    expect(drawn).toHaveLength(2);
    expect(drawn[0]?.props.accessibilityLabel).toContain(CARD_TAG.uncounted!);
    expect(drawn[1]?.props.accessibilityLabel).toContain(CARD_TAG.planning!);
  });
});
