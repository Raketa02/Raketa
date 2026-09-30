/**
 * **Now's rail, walked the way a player walks it**: the real route tree, the real shell, the real
 * Home tab, and only `fetch` faked.
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
import { REMOVE_THIS_CARD } from '@/features/games/types';
import { HOME_COPY } from '@/features/shell/types';
import { SEAT_NAME_LETTERS, endPlaySession } from '@/features/play/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { FILL_THE_SEAT } from '@/shared/vocabulary/theActsWords';
import {
  GAMES_PATH,
  GATE_USER,
  launchSignedIn,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { setDeviceZone } from '@/test-support/deviceZone';
import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GAME_CARD_NAMES } from '../domain/gameCard';
import { PLAN_SLOTS } from '../domain/slots';

import {
  ACCENT,
  CARD_TAG,
  FINISH_THE_PLAN,
  STAGE_DOT,
  WHAT_HAPPENED,
  doorLabel,
  gamesHeading,
} from './nowPresentation';
import { NOT_AGREED_YET, SLOT_EYEBROW, TODAY } from './planPresentation';

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
  { player_id: ME, name: 'me_' },
  { player_id: TOMEK, name: 'tomek.p' },
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
      { side: 'A', player_id: ME, name: 'me_' },
      { side: 'B', player_id: TOMEK, name: 'tomek.p' },
    ],
    proposals: [],
    ...over,
  };
}

/** The court's row on `GET /plans` — the challenge's, which the game inherits (ADR-0164 §1). */
function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    challenge_id: CHALLENGE,
    anchor: PLANNED_AT,
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    ...over,
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land on the Home tab with these games, these plans and — optionally — a room to open. */
async function landOnHome({
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
    await landOnHome({ games: [] });

    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen.getByText(HOME_COPY.empty.act)).toBeTruthy();
    expect(screen.getByText(gamesHeading(0))).toBeTruthy();
  });

  it('heads the rail with its own count', async () => {
    await landOnHome({
      games: [game(), game({ game_id: 'aaaaaaaa-0000-4000-8000-00000000000a' })],
    });

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
    await landOnHome({ plans: [plan({ place: 'Zabłocie Sport' })] });

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    for (const label of labels()) expect(screen.getByText(label)).toBeTruthy();
  });

  it('mock 1 — where is set: the place bright, the day and the time not agreed yet', async () => {
    await landOnHome({ plans: [plan({ place: 'Zabłocie Sport, court 3' })] });

    await theCard();
    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
    expect(bars()).toEqual([BRIGHT, DIM, DIM]);
  });

  it('mock 2 — day is set: the weekday whole and the date beside it, the rest not agreed', async () => {
    await landOnHome({
      plans: [plan({ day: '2026-09-13', agreed_point: '2026-09-13T22:00:00Z' })],
    });

    await theCard();
    expect(screen.getByText('Sunday')).toBeTruthy();
    expect(screen.getByText('13 Sep')).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
    expect(bars()).toEqual([DIM, BRIGHT, DIM]);
  });

  it('mock 3 — where and day are set: two bright bars and one dim', async () => {
    await landOnHome({
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
    await landOnHome({ plans: [plan({ place: 'Zabłocie Sport, court 3' })] });

    const card = await theCard();

    expect(screen.getByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.queryByText('Zabłocie Sport, court 3')).toBeNull();
    expect(card.props.accessibilityLabel).toContain('Zabłocie Sport, court 3');
  });
});

describe('the sport word', () => {
  it('is the sport alone on a counted game', async () => {
    await landOnHome();

    expect(await screen.findByText('Padel')).toBeTruthy();
  });

  it('marks a friendly, and nothing else about the game', async () => {
    await landOnHome({ games: [game({ kind: 'FRIENDLY' })] });

    expect(await screen.findByText('Padel · Friendly')).toBeTruthy();
    expect(screen.queryByText(/singles/i)).toBeNull();
  });
});

describe('the four rungs, folded at read time', () => {
  /** The instant is the games list's, never the phone's — `GET /plans` carries none. */
  const nameOf = async (agreed: Wire['PlanSchema'] | undefined) => {
    await landOnHome({ plans: agreed === undefined ? [] : [agreed] });
    return screen;
  };

  it('is Planning with nothing agreed, and every slot says so', async () => {
    await nameOf(undefined);

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(3);
    expect(bars()).toEqual([DIM, DIM, DIM]);
  });

  /**
   * **A game opened over a full plan lands as *Game on* on its first read** (ADR-0164 §7): the
   * plan is the challenge's, its four people filled every slot in the chat before the court was
   * whole, and the card joins the game to that row by the challenge it was opened from — so the
   * rail never draws *Planning* for a plan that is already made.
   */
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

  /**
   * **Now is games only** (ADR-0164 §7). A court that is not whole has a plan — its row is on the
   * list, and the room draws it — and no game, so the rail draws nothing for it: not a card, and
   * not a count.
   */
  it('draws no card for a court that is not whole, whatever its plan says', async () => {
    await landOnHome({ games: [], plans: [plan({ place: 'Zabłocie Sport', day: '2026-09-19' })] });

    expect(await screen.findByText(gamesHeading(0))).toBeTruthy();
    expect(screen.queryByText(CARD_TAG.planning!)).toBeNull();
    expect(screen.queryByText('Zabłocie Sport')).toBeNull();
  });

  /**
   * **The day of the game is the day row's to say, and no card's** (ADR-0166). A day-only plan on
   * the day is *Planning* — the plan is not made — with `Today` where the weekday would be and
   * the date beside it, and a dim bar under the two slots still to agree, which is the alarm
   * #324's second amendment wanted, said by the slots rather than by a name.
   */
  it('is Planning on the agreed day while something is still to agree, and the day row says Today', async () => {
    await nameOf(plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' }));

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    expect(screen.getByText(TODAY)).toBeTruthy();
    expect(screen.getByText('12 Sep')).toBeTruthy();
    expect(screen.queryByText('Saturday')).toBeNull();
    expect(screen.getAllByText(NOT_AGREED_YET)).toHaveLength(2);
    expect(bars()).toEqual([DIM, ACCENT.planning.bar, DIM]);
  });

  it('is Game on on the agreed day once all three are filled, and the day row says Today', async () => {
    await nameOf(
      plan({
        place: 'Zabłocie Sport',
        day: '2026-09-12',
        hour: '18:00',
        agreed_point: '2026-09-12T16:00:00Z',
      }),
    );

    expect(await screen.findByText(CARD_TAG['game-on']!)).toBeTruthy();
    expect(screen.getByText(TODAY)).toBeTruthy();
    expect(screen.getByText('12 Sep')).toBeTruthy();
    expect(screen.queryByText('Saturday')).toBeNull();
    // The card leads with the plan, not the score: *We played* is one press in, on the screen.
    expect(screen.getByRole('button', { name: doorLabel('game-on')! })).toBeTruthy();
  });

  /** *Today* is the games list's own day, in the platform zone — never the device's. */
  it('says Today in the platform zone, never the device one', async () => {
    const held = process.env.TZ;
    setDeviceZone('Pacific/Midway');
    try {
      await nameOf(plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' }));

      expect(await screen.findByText(TODAY)).toBeTruthy();
    } finally {
      setDeviceZone(held);
    }
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
    await landOnHome();

    fireEvent.press(await screen.findByText(FINISH_THE_PLAN));
    await openTheGame();
  });

  /** The body is not a door: the two buttons are the only doors, and pressing the card does nothing. */
  it('opens nothing from the body', async () => {
    await landOnHome();

    const card = await theCard();
    fireEvent.press(card);

    expect(card.props.accessibilityRole).toBeUndefined();
    expect(card.props.onPress).toBeUndefined();
    expect(screen).toHavePathname('/');
  });

  it('opens the room from the bubble', async () => {
    await landOnHome();

    fireEvent.press(await screen.findByLabelText(OPEN_THE_CHAT));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  /** The join fails soft: a challenge with no room draws no bubble rather than a dead one. */
  it('draws no bubble where there is no room to open', async () => {
    await landOnHome({ room: false });

    await screen.findByText(FINISH_THE_PLAN);
    expect(screen.queryByLabelText(OPEN_THE_CHAT)).toBeNull();
  });

  it('names the door for the act the standing can take', async () => {
    await landOnHome({
      plans: [plan({ day: '2026-09-12', hour: '08:00', agreed_point: '2026-09-12T06:00:00Z' })],
    });

    expect(await screen.findByText(doorLabel('needs-result')!)).toBeTruthy();
  });

  /** *Counted* offers nothing: the app does not name an act a state cannot take. */
  it('offers no door on an ending', async () => {
    await landOnHome({
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
    [
      // No line under the slots: the tag is the whole of what the card says (ADR-0172 §8).
      'called-off',
      game({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-12T08:00:00Z',
        called_off_by: { player_id: TOMEK, name: 'tomek.p' },
      }),
      undefined,
      undefined,
    ],
  ] as const)('%s draws its tag, its door and its line', async (name, served, agreed, line) => {
    await landOnHome({ games: [served], plans: agreed === undefined ? [] : [agreed] });

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

/**
 * **The fifth rung, above the clock** (#411 rule 5, ADR-0162): a seat somebody left is drawn
 * empty on the court, the tag says what is needed, the door is *Fill the seat* — opening the
 * game screen, where the fill is the arm's primary act (#419, landed there by #429 F1) — and a
 * listener, who cannot see the court, is told the gap.
 */
describe('Needs a player', () => {
  const SHORT: Wire['GameSchema']['seats'] = [
    { side: 'A', player_id: ME, name: 'me_' },
    { side: 'B', player_id: null, name: null },
  ];

  /** A plan whose agreed point has passed — the clock says *Needs result*, and loses. */
  const PASSED = plan({
    place: 'Zabłocie Sport',
    day: '2026-09-11',
    hour: '20:00',
    agreed_point: '2026-09-11T18:00:00Z',
  });

  /** The same plan, agreed for a day still ahead. */
  const AHEAD = plan({ ...PASSED, day: '2026-09-19', agreed_point: '2026-09-19T18:00:00Z' });

  it('draws its tag above the clock, and Fill the seat as its door', async () => {
    await landOnHome({ games: [game({ seats: SHORT })], plans: [AHEAD] });

    expect(await screen.findByText(CARD_TAG['needs-a-player']!)).toBeTruthy();
    expect(screen.queryByText(CARD_TAG['game-on']!)).toBeNull();
    expect(screen.getByRole('button', { name: FILL_THE_SEAT })).toBeTruthy();
    expect(doorLabel('needs-a-player')).toBe(FILL_THE_SEAT);
  });

  /**
   * **Past the moment nobody may be seated into the game**, so the door stands down with the
   * screen's own fill, mirroring `game_moment_has_passed` — the tag still outranks the clock,
   * and the bubble is the card's one door.
   */
  it('draws no wide door once the agreed moment has passed, and still outranks the clock', async () => {
    await landOnHome({ games: [game({ seats: SHORT })], plans: [PASSED] });

    expect(await screen.findByText(CARD_TAG['needs-a-player']!)).toBeTruthy();
    expect(screen.queryByText(CARD_TAG['needs-result']!)).toBeNull();
    expect(screen.queryByRole('button', { name: FILL_THE_SEAT })).toBeNull();
    expect(screen.getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
    expect(screen.queryByText(/left to say you played/)).toBeNull();
  });

  /**
   * **The door opens the game screen and runs nothing** — the same screen the room's *Details*
   * opens, where the fill is the arm's primary act ([#429](https://github.com/Raketa02/Raketa/issues/429)
   * F1, reversing #419's *run from the card*). It is drawn in the stage dot's own colour, so the
   * tag and the door say the same thing twice — once in a word, once in a fill — rather than the
   * settled green over an errand still open.
   */
  it('opens the game from Fill the seat, and mints no search on the way', async () => {
    await landOnHome({ games: [game({ seats: SHORT })], plans: [AHEAD] });

    const door = await screen.findByRole('button', { name: FILL_THE_SEAT });
    expect(StyleSheet.flatten(door.props.style as ViewStyle).backgroundColor).toBe(
      STAGE_DOT['needs-a-player'],
    );

    fireEvent.press(door);

    await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
    expect(transport.requestsTo('POST', '/api/v1/lineups')).toHaveLength(0);
  });

  it('draws the open seat empty — no face, no letters — and the rest of the court as it was', async () => {
    await landOnHome({ games: [game({ seats: SHORT })] });

    await theCard();
    const drawn = { includeHiddenElements: true };

    expect(screen.getByText('me_'.slice(0, SEAT_NAME_LETTERS), drawn)).toBeTruthy();
    expect(screen.queryByText('?', drawn)).toBeNull();
    // The empty seat is the builder's own drawing of one — a dashed outline and nothing in it.
    const dashed = screen
      .UNSAFE_getAllByType(View)
      .filter((box) => StyleSheet.flatten(box.props.style as ViewStyle)?.borderStyle === 'dashed');
    expect(dashed).toHaveLength(1);
  });

  it('says the open seat aloud, because the court is not read', async () => {
    await landOnHome({ games: [game({ seats: SHORT })] });

    expect(await screen.findByLabelText(/^Needs a player\. Padel\. An open seat\./)).toBeTruthy();
  });
});

describe('the court', () => {
  /** The ring is the mark; the caption is the handle's first letters on every seat, yours too. */
  it('captions your own seat with three letters of your handle, never with you', async () => {
    await landOnHome();

    await theCard();
    // The court is drawn into a hidden subtree — the card's own name says the sport — so the
    // captions are looked for where they are drawn rather than where they are announced.
    const drawn = { includeHiddenElements: true };

    expect(screen.getByText('me_'.slice(0, SEAT_NAME_LETTERS), drawn)).toBeTruthy();
    expect(screen.getByText('tomek.p'.slice(0, SEAT_NAME_LETTERS), drawn)).toBeTruthy();
    expect(screen.queryByText('you', drawn)).toBeNull();
  });

  it('draws a face where the room has a photograph, and posters where it has none', async () => {
    await landOnHome({
      members: [
        { player_id: ME, name: 'me_' },
        { player_id: TOMEK, name: 'tomek.p', photo_id: 'p1', photo_url: TOMEK_PHOTO },
      ],
    });

    await theCard();
    const faces = screen.UNSAFE_getAllByType(Image).map((image) => image.props.source);

    expect(faces).toEqual([{ uri: TOMEK_PHOTO }]);
  });

  it('draws posters in every seat where there is no room, and nothing fails', async () => {
    await landOnHome({ room: false });

    await theCard();
    expect(screen.UNSAFE_queryAllByType(Image)).toHaveLength(0);
  });
});

describe('how long an ending keeps its card', () => {
  const ended = (playedAt: string) =>
    game({ standing: 'CONFIRMED', played_at: playedAt, entry_closes_at: null });

  it('keeps it for a day', async () => {
    await landOnHome({ games: [ended('2026-09-11T10:00:00Z')] });

    expect(await screen.findByText(gamesHeading(1))).toBeTruthy();
    expect(screen.getByText(CARD_TAG.counted!)).toBeTruthy();
  });

  it('and then leaves, which is what keeps the day line honest', async () => {
    await landOnHome({ games: [ended('2026-09-11T08:00:00Z')] });

    expect(await screen.findByText(gamesHeading(0))).toBeTruthy();
    expect(screen.getByText(HOME_COPY.empty.line)).toBeTruthy();
  });

  /**
   * **The fourth end is shelved from the act** (ADR-0163, #419 §3): `entry_closes_at` is `null`
   * on it, so the card reads `called_off_at` — a day, as the other endings get — and the tag's
   * dot is the quiet hairline.
   */
  const calledOff = (at: string) =>
    game({
      standing: 'CALLED_OFF',
      entry_closes_at: null,
      called_off_at: at,
      called_off_by: { player_id: TOMEK, name: 'tomek.p' },
    });

  it('keeps a called-off game for a day, with its tag', async () => {
    await landOnHome({ games: [calledOff('2026-09-11T10:00:00Z')] });

    expect(await screen.findByText(gamesHeading(1))).toBeTruthy();
    expect(screen.getByText(CARD_TAG['called-off']!)).toBeTruthy();
  });

  it('and then the called-off card leaves too', async () => {
    await landOnHome({ games: [calledOff('2026-09-11T08:00:00Z')] });

    expect(await screen.findByText(gamesHeading(0))).toBeTruthy();
  });
});

/**
 * **The called-off card offers two things and names nobody**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §5, §8): no line under the slots, *What happened?* opening the game screen, and the trash —
 * spoken *Remove this card* — which sends the dismissal and takes the card off the rail on the
 * reply, with no sheet and before any re-read.
 */
describe('the called-off card', () => {
  const DISMISSAL_PATH = `${GAMES_PATH}/${GAME}/dismissal`;
  const calledOff = game({
    standing: 'CALLED_OFF',
    entry_closes_at: null,
    called_off_at: '2026-09-11T10:00:00Z',
    called_off_by: { player_id: TOMEK, name: 'tomek.p' },
    seats: [
      { side: 'A', player_id: ME, name: 'me_' },
      { side: 'B', player_id: null, name: null },
    ],
  });

  it('draws What happened? and the trash, and no line under the slots', async () => {
    await landOnHome({ games: [calledOff], room: false });

    expect(await screen.findByRole('button', { name: WHAT_HAPPENED })).toBeTruthy();
    expect(screen.getByRole('button', { name: REMOVE_THIS_CARD })).toBeTruthy();
    expect(screen.queryByLabelText(OPEN_THE_CHAT)).toBeNull();
    // The tag once, in the header — and nowhere else: the line under the slots is gone.
    expect(screen.getAllByText(CARD_TAG['called-off']!)).toHaveLength(1);
    expect(screen.queryByText('tomek.p')).toBeNull();
  });

  it('opens the game screen from What happened?', async () => {
    await landOnHome({ games: [calledOff], room: false });

    fireEvent.press(await screen.findByRole('button', { name: WHAT_HAPPENED }));
    await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  });

  it('sends the dismissal from the trash, and the card leaves the rail on the reply', async () => {
    await landOnHome({ games: [calledOff], room: false });
    const trash = await screen.findByRole('button', { name: REMOVE_THIS_CARD });
    transport.on('POST', DISMISSAL_PATH, () => noContent());
    // The list is held open after the act, so the card that goes went on the reply and not on
    // a server that was asked again.
    const held = new Promise<Response>(() => undefined);
    transport.on('GET', GAMES_PATH, () => held);

    fireEvent.press(trash);

    await waitFor(() => expect(screen.queryByText(CARD_TAG['called-off']!)).toBeNull());
    expect(await screen.findByText(gamesHeading(0))).toBeTruthy();
    expect(transport.requestsTo('POST', DISMISSAL_PATH)).toHaveLength(1);
    expect(screen.queryByText(/before you|are you sure/i)).toBeNull();
  });

  /** A refusal is a re-read and no words: the fold the re-read lands on is the answer. */
  it('re-reads the rail when the dismissal is refused, and the card stays', async () => {
    await landOnHome({ games: [calledOff], room: false });
    transport.on('POST', DISMISSAL_PATH, () => errorResponse(409, 'game_is_not_called_off'));
    const before = transport.requestsTo('GET', GAMES_PATH).length;

    fireEvent.press(await screen.findByRole('button', { name: REMOVE_THIS_CARD }));

    await waitFor(() =>
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(before),
    );
    expect(screen.getByText(CARD_TAG['called-off']!)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
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

    await landOnHome({
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
