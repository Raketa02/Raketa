/**
 * **The game screen on its two plan-lead rungs, walked the way a player walks it**: the real
 * route tree, the real shell, both doors into the screen, and only `fetch` faked.
 *
 * [#414](https://github.com/Raketa02/Raketa/issues/414)'s acceptance criteria are assertions in
 * this file and opinions nowhere else — the eyebrow is the format and the kind with no title
 * under it, the card at the top is the Now card with its doors left off, the plan card is the
 * chat's editable one with the panel inside it, *Open the chat* is dark and full width from both
 * routes, *We played* is a quiet secondary beneath it, the standing line and the checklist are
 * gone, and *Game on* is drawn by the same layout.
 *
 * The screen's score lead and its result arms are `gamePlan.test.tsx`'s and `result.test.tsx`'s
 * and are not re-walked here. The words are the decks' — `planPresentation.ts`,
 * `nowPresentation.ts`, and the eyebrow's four forms as the ticket spells them.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Image, Text } from 'react-native';

import { CALL_IT_OFF, LEAVE_THIS_GAME } from '@/features/challenges/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { BALANCE_FORECAST, OPEN_SEAT, PLAYERS } from '@/features/games/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { Card } from '@/shared/ui';
import { FILL_THE_SEAT, WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import {
  GATE_USER,
  PLANS_PATH,
  launchSignedIn,
  planSlotPath,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPlans,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { CARD_TAG, FINISH_THE_PLAN } from './nowPresentation';
import {
  EVERYBODY_SAID_YES,
  LOCK_THE_PLAN,
  NOTHING_IS_LEFT_TO_AGREE,
  NOT_AGREED_YET,
  PLAN_PANEL,
  SAVING,
  SLOT_NAME,
  STILL_TO_AGREE,
  THE_PLAN,
  counterLabel,
  dayChipName,
  planHeadingName,
} from './planPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const KASIA = 'cccccccc-0000-4000-8000-000000000003';
const MAREK = 'dddddddd-0000-4000-8000-000000000004';

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

const SINGLES_SEATS: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, name: 'me_' },
  { side: 'B', player_id: TOMEK, name: 'tomek.p' },
];

const DOUBLES_SEATS: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, name: 'me_' },
  { side: 'A', player_id: KASIA, name: 'kasia_w' },
  { side: 'B', player_id: TOMEK, name: 'tomek.p' },
  { side: 'B', player_id: MAREK, name: 'marekb' },
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
    seats: SINGLES_SEATS,
    proposals: [],
    ...over,
  };
}

/**
 * The court's row on `GET /plans` — **the challenge's** (ADR-0164 §1), which the game inherits: the
 * screen joins the game to it by `challenge_id`, and the writes are addressed by the same id. The
 * anchor is the game's `planned_at` once there is a game — which is why `stubTheWorld` lists no
 * row by default: the screen draws the card off the game's own anchor until the row lands, and
 * every test here that does not stub one is proving it.
 */
function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    challenge_id: CHALLENGE,
    anchor: PLANNED_AT,
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    locked_at: null,
    ...over,
  };
}

/** The whole plan, agreed for a day that is still ahead — the *Game on* rung's own values. */
const WHOLE = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-19',
  hour: '18:00',
  agreed_point: '2026-09-19T16:00:00Z',
});

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

/** Every list this screen and the room behind it read, and a room to open unless asked otherwise. */
function stubTheWorld({
  games = [game()],
  plans = [],
  room = true,
  members = PAIR,
  court = { refused: 409, code: 'pairing_is_history' },
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
  readonly room?: boolean;
  readonly members?: readonly Wire['ConversationMemberSchema'][];
  readonly court?: Parameters<typeof stubPairing>[2];
} = {}) {
  stubGames(transport, games, READ_AT);
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
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: GAME,
    sport: 'PADEL',
    members: [...members],
    people: [...members],
    entries: [],
  });
  stubEntries(transport, ROOM);
  // The court's pairing is #415's and walked in `features/games`; here it is a refusal by name
  // unless a case says otherwise, so the slot draws the players card alone and this suite's card
  // count is the plan's and the court's.
  stubPairing(transport, GAME, court);
}

/** In at the screen's own address under Now — the wide door's destination. */
async function openFromNow(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn(`/games/${GAME}`);
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  await screen.findByLabelText('Back');
}

/** In through the room's *Details* — the other address of the same component. */
async function openFromTheRoom(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));

  fireEvent.press(await screen.findByLabelText('Open the game'));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}/details`));
}

/** The chip for one slot, found by the name it says rather than by the value it draws. */
const slotChip = (name: string) => screen.getByLabelText(new RegExp(`^${name}:`));

/** The one light card on this screen — the plan's — found by its own heading. */
function thePlanCard() {
  const card = screen
    .UNSAFE_getAllByType(Card)
    .find((one) => within(one).queryByText(THE_PLAN) !== null);
  if (card === undefined) throw new Error('no plan card on the screen');
  return card;
}

/** Every string a card draws, in tree order — for saying what sits between what. */
const drawnIn = (card: ReturnType<typeof thePlanCard>) =>
  within(card)
    .UNSAFE_getAllByType(Text)
    .map((text) => text.props.children)
    .filter((child): child is string => typeof child === 'string');

describe('the head of the screen', () => {
  /**
   * **The format and the kind, and no title** — `DOUBLES · COUNTED`, as the ticket spells the
   * four forms. The eyebrow is the heading, because there is nothing under it: the card names
   * the people and the plan names the day. `Counted`, never `Competitive` (§5.4 #8).
   */
  it.each([
    ['singles, counted', game(), 'Singles · Counted'],
    ['singles, friendly', game({ kind: 'FRIENDLY' }), 'Singles · Friendly'],
    ['doubles, counted', game({ seats: DOUBLES_SEATS }), 'Doubles · Counted'],
    ['doubles, friendly', game({ seats: DOUBLES_SEATS, kind: 'FRIENDLY' }), 'Doubles · Friendly'],
  ])('is headed by the format and the kind — %s', async (_, served, eyebrow) => {
    await openFromNow({ games: [served] });

    expect(await screen.findByRole('header', { name: eyebrow })).toBeTruthy();
    expect(screen.queryByText(/competitive/i)).toBeNull();
    expect(screen.queryByText(/arranged/)).toBeNull();
  });
});

describe('the card at the top', () => {
  /**
   * The Now card with `doors={false}`: the tag, the sport word, the slots and the court, and
   * **neither door** — the screen is where both go. The one *Open the chat* on the screen is the
   * screen's own dark button, never the bubble.
   */
  it('is the Now card without its doors', async () => {
    await openFromNow();

    expect(await screen.findByText(CARD_TAG.planning!)).toBeTruthy();
    expect(screen.getByLabelText(/Padel/)).toBeTruthy();
    expect(screen.queryByText(FINISH_THE_PLAN)).toBeNull();
    expect(screen.getAllByLabelText(OPEN_THE_CHAT)).toHaveLength(1);
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();
  });

  /** The same faces join as the rail's, over the same list. */
  it('draws a face where the room has a photograph', async () => {
    await openFromNow({
      members: [
        { player_id: ME, name: 'me_' },
        { player_id: TOMEK, name: 'tomek.p', photo_id: 'p1', photo_url: TOMEK_PHOTO },
      ],
    });

    await screen.findByText(CARD_TAG.planning!);
    // Scoped to the card: since #415 the players card under it draws the same face off the same
    // join, and that row is `playersCard.test.tsx`'s.
    const faces = within(screen.getByLabelText(/Padel/))
      .UNSAFE_getAllByType(Image)
      .map((image) => image.props.source);

    expect(faces).toEqual([{ uri: TOMEK_PHOTO }]);
  });
});

describe('the plan card, editable here', () => {
  /** The chat's card, reused as it is: the eyebrow and the counter, three chips, the lock. */
  it('is headed The plan with its count, and offers the three slots as chips', async () => {
    await openFromNow();

    const heading = await screen.findByRole('header', { name: planHeadingName(undefined) });
    expect(within(heading).getByText(counterLabel(undefined))).toBeTruthy();

    for (const name of Object.values(SLOT_NAME)) {
      expect(screen.getByLabelText(`${name}: ${NOT_AGREED_YET}`)).toBeTruthy();
    }
  });

  /**
   * **The card is there before the row is** — drawn off the game's own anchor, which is what the
   * row's will be once it lands (ADR-0164 §4) — and stays as it was when the list answers with the
   * same empty court. The room cannot do this and draws nothing until its row; the game screen has
   * the one thing the anchor is derived from.
   */
  it('draws the card off the game’s own anchor while the plan list is still coming', async () => {
    let landed: () => void = () => {};
    const listLands = new Promise<void>((resolve) => {
      landed = resolve;
    });
    stubTheWorld();
    transport.on('GET', PLANS_PATH, async () => {
      await listLands;
      return json<Wire['PlanListResponse']>({ plans: [plan()] });
    });
    await launchSignedIn(`/games/${GAME}`);
    await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));

    // The card, with the lock greyed under it and the horizon the game's: the last day offered
    // is `planned_at + 7`, Tuesday the 15th.
    expect(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`)).toBeTruthy();
    expect(
      screen.getByRole('button', { name: LOCK_THE_PLAN }).props.accessibilityState.disabled,
    ).toBe(true);
    fireEvent.press(screen.getByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    expect(await screen.findByLabelText(dayChipName('2026-09-15'))).toBeTruthy();
    expect(screen.queryByLabelText(dayChipName('2026-09-16'))).toBeNull();

    landed();
    await act(async () => {
      await listLands;
    });
    expect(screen.getByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`)).toBeTruthy();
  });

  /**
   * **The plan is found by the game's challenge** (ADR-0164 §1): a row under another challenge is
   * not this game's, however its slots read, and the row under this one is — so the card draws
   * what the court's four people wrote in the chat before the court was whole.
   */
  it('draws the plan the game’s challenge id finds, and no other', async () => {
    await openFromNow({
      plans: [
        plan({ challenge_id: 'ffffffff-0000-4000-8000-000000000099', place: 'Somewhere else' }),
        plan({ place: 'Zabłocie Sport', day: '2026-09-13' }),
      ],
    });

    expect(await screen.findByLabelText('Where: Zabłocie Sport')).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`)).toBeTruthy();
    expect(screen.queryByText('Somewhere else')).toBeNull();
  });

  /**
   * **A chip opens its sheet and writes through the slot — pending, never optimistic.** The chip
   * goes busy with the value it already had, and the new one is drawn only once the server has
   * answered, exactly as in the room.
   */
  it('opens a chip’s sheet and writes the slot, showing pending and never the value being written', async () => {
    await openFromNow();

    let answer: (schema: Wire['PlanSchema']) => void = () => {};
    const held = new Promise<Wire['PlanSchema']>((resolve) => {
      answer = resolve;
    });
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), async () => json(await held));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-13')));

    expect(await screen.findByText(SAVING)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: ${SAVING}`)).toBeTruthy();
    expect(screen.queryByText('Sunday')).toBeNull();

    answer(plan({ day: '2026-09-13' }));
    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`)).toBeTruthy());
    expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'day'))[0]?.body).toEqual({
      day: '2026-09-13',
    });
  });

  /** A lock word **is** drawn here now — greyed below three, as the chat decided it. */
  it('draws the lock greyed while any slot is empty', async () => {
    await openFromNow({ plans: [plan({ place: 'Zabłocie Sport', day: '2026-09-13' })] });

    const lock = await screen.findByRole('button', { name: LOCK_THE_PLAN });
    expect(lock.props.accessibilityState.disabled).toBe(true);
    expect(screen.queryByText(/set all three/i)).toBeNull();
  });

  /**
   * **The panel is inside the card here**, between the chips and the lock — the note slot the
   * chat leaves empty (`planCard.test.tsx` holds that half).
   */
  it('draws the panel inside the card, between the chips and the lock', async () => {
    await openFromNow();

    await screen.findByText(PLAN_PANEL.title);
    const drawn = drawnIn(thePlanCard());

    expect(drawn).toContain(PLAN_PANEL.title);
    expect(drawn).toContain(PLAN_PANEL.body);
    expect(drawn.indexOf(SLOT_NAME.hour)).toBeLessThan(drawn.indexOf(PLAN_PANEL.title));
    expect(drawn.indexOf(PLAN_PANEL.title)).toBeLessThan(drawn.indexOf(LOCK_THE_PLAN));
  });

  /**
   * A hold is a fact about the account, met here off the same mutation cache the room reads:
   * every chip and the lock grey under one note that says so, and never a coral sentence.
   */
  it('greys every chip under one note when the account is held', async () => {
    await openFromNow();
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => errorResponse(403, 'account_held'));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-13')));

    await waitFor(() =>
      expect(slotChip(SLOT_NAME.hour).props.accessibilityState.disabled).toBe(true),
    );
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(
      screen.getByRole('button', { name: LOCK_THE_PLAN }).props.accessibilityState.disabled,
    ).toBe(true);
  });
});

describe('the two doors', () => {
  it('opens the room from Open the chat, coming in from Now', async () => {
    await openFromNow();

    fireEvent.press(await screen.findByText(OPEN_THE_CHAT));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  it('opens the room from Open the chat, coming in from the room’s Details', async () => {
    await openFromTheRoom();

    fireEvent.press(await screen.findByText(OPEN_THE_CHAT));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  /** ADR-0149 §3's join fails soft: no room, no door — and the rest of the screen stands. */
  it('draws no chat door where there is no room, and keeps everything else', async () => {
    await openFromNow({ room: false });

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.queryByText(OPEN_THE_CHAT)).toBeNull();
    expect(screen.getByText(WE_PLAYED)).toBeTruthy();
  });

  /** *We played* stays beneath, and still opens the score — a game can be played before it is planned. */
  it('keeps We played beneath, opening the score over the plan', async () => {
    await openFromNow();

    await screen.findByText(OPEN_THE_CHAT);
    expect(screen.queryByText('Send this score')).toBeNull();

    fireEvent.press(screen.getByText(WE_PLAYED));

    expect(screen.getByText('Send this score')).toBeTruthy();
    expect(screen.getByText('Leave it as it is')).toBeTruthy();
  });
});

describe('what went', () => {
  /** The standing line and the three-line checklist: the card and the counter carry both now. */
  it('draws no standing line and no checklist', async () => {
    await openFromNow({ plans: [WHOLE] });

    await screen.findByText(PLAN_PANEL.title);

    expect(screen.queryByText(/Nobody has said this one happened yet/)).toBeNull();
    expect(screen.queryByText(EVERYBODY_SAID_YES)).toBeNull();
    expect(screen.queryByText(NOTHING_IS_LEFT_TO_AGREE)).toBeNull();
    expect(screen.queryByText(new RegExp(`^${STILL_TO_AGREE}`))).toBeNull();
    expect(screen.queryByText(/This one counts/)).toBeNull();
  });
});

/**
 * **A seat somebody left** (#411 rules 5 and 6, ADR-0162): the screen is the plan lead — the seat
 * outranks the clock — with the empty seat on the card, an *Open seat* row on the players card,
 * the plan still editable, the chat door still there, and no *We played*, because a game with a
 * gap in it cannot be recorded. The forecast is absent because #416's pairing omits it, and the
 * block is drawn off the pairing alone — nothing here special-cases the seat.
 */
describe('an open seat', () => {
  const SHORT: Wire['GameSchema']['seats'] = [
    { side: 'A', player_id: ME, name: 'me_' },
    { side: 'A', player_id: KASIA, name: 'kasia_w' },
    { side: 'B', player_id: TOMEK, name: 'tomek.p' },
    { side: 'B', player_id: null, name: null },
  ];

  /** The pairing beside a short court: Levels for whoever is in, and no forecast (#416). */
  const NO_FORECAST: Wire['GamePairingResponse'] = {
    read_at: READ_AT,
    seats: [
      {
        player_id: ME,
        level: 2.71,
        band: 'Established',
        range: { low: 2.55, high: 2.87 },
        confidence: 74,
      },
    ],
  };

  it('withholds We played, and keeps the chat door', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], plans: [WHOLE] });

    expect(await screen.findByText(CARD_TAG['needs-a-player']!)).toBeTruthy();
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();
    expect(screen.queryByText(WE_PLAYED)).toBeNull();
  });

  /**
   * **The arm's acts, in the design's order** (#419): the chat door, then *Fill the seat* as the
   * primary act where *We played* would be, then the court's acts — *Call it off* for whoever
   * may, which here is nobody, since the challenge list holds no row — and *Leave this game*
   * last. On the full-court rungs there is no fill at all. The acts themselves are walked in
   * `features/challenges` (`fillTheSeat.test.tsx`, `callOff.test.tsx`).
   */
  it('offers Fill the seat as the primary act, between the chat door and Leave this game', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], plans: [WHOLE] });

    await screen.findByRole('button', { name: FILL_THE_SEAT });
    const buttons = screen.getAllByRole('button').map((one) => one.props.accessibilityLabel);

    expect(buttons.indexOf(OPEN_THE_CHAT)).toBeLessThan(buttons.indexOf(FILL_THE_SEAT));
    expect(buttons.indexOf(FILL_THE_SEAT)).toBeLessThan(buttons.indexOf(LEAVE_THIS_GAME));
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
  });

  it('offers no fill on a full court', async () => {
    await openFromNow({ plans: [WHOLE] });

    await screen.findByText(WE_PLAYED);
    expect(screen.queryByRole('button', { name: FILL_THE_SEAT })).toBeNull();
  });

  /** The plan survives a departure: the chips are live and the lock is drawn. */
  it('keeps the plan card editable', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], plans: [WHOLE] });

    await screen.findByText(PLAN_PANEL.title);
    expect(slotChip(SLOT_NAME.where).props.accessibilityState.disabled).toBe(false);
    expect(
      screen.getByRole('button', { name: LOCK_THE_PLAN }).props.accessibilityState.disabled,
    ).toBe(false);
  });

  /** A row with nobody in it: the words, no level row, and nothing to press. */
  it('draws the open seat as a row on the players card that is not a button', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], court: NO_FORECAST });

    // By role: the bar's second column says *Players* too, and it is a tab and not a heading.
    await screen.findByRole('header', { name: PLAYERS });
    expect(screen.getByText(OPEN_SEAT)).toBeTruthy();
    expect(screen.queryByRole('button', { name: new RegExp(OPEN_SEAT) })).toBeNull();
    expect(screen.getAllByRole('button', { name: /record$/i })).toHaveLength(3);
  });

  it('draws no forecast block, because the pairing carries none', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], court: NO_FORECAST });

    await screen.findByRole('header', { name: PLAYERS });
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
  });

  /** Past its moment the seat still outranks the clock: the plan lead, and not the grid. */
  it('is the plan lead even once the agreed moment has passed', async () => {
    await openFromNow({
      games: [game({ seats: SHORT })],
      plans: [plan({ ...WHOLE, day: '2026-09-11', agreed_point: '2026-09-11T16:00:00Z' })],
    });

    expect(await screen.findByText(CARD_TAG['needs-a-player']!)).toBeTruthy();
    expect(screen.getByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.queryByText('Send this score')).toBeNull();
  });
});

describe('Game on', () => {
  /** The same layout, with the plan whole: the card's tag, three chips with values, the lock live. */
  it('renders the same layout with the plan whole and the lock live', async () => {
    await openFromNow({ plans: [WHOLE] });

    expect(await screen.findByRole('header', { name: 'Singles · Counted' })).toBeTruthy();
    expect(screen.getByText(CARD_TAG['game-on']!)).toBeTruthy();

    expect(screen.getByLabelText(`${SLOT_NAME.where}: Zabłocie Sport, court 3`)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: Saturday`)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.hour}: 18:00`)).toBeTruthy();
    expect(
      screen.getByText(
        counterLabel({
          challengeId: CHALLENGE,
          anchor: PLANNED_AT,
          place: 'x',
          day: 'd',
          hour: 'h',
        }),
      ),
    ).toBeTruthy();

    const lock = screen.getByRole('button', { name: LOCK_THE_PLAN });
    expect(lock.props.accessibilityState.disabled).toBe(false);

    expect(screen.getByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();
    expect(screen.getByText(WE_PLAYED)).toBeTruthy();
  });

  /** The lock goes out from here too, and the counter reads Locked once it has landed. */
  it('locks the plan from here', async () => {
    await openFromNow({ plans: [WHOLE] });
    const lockPath = `/api/v1/plans/${CHALLENGE}/lock`;
    transport.on('PUT', lockPath, () => json({ ...WHOLE, locked_at: '2026-09-12T10:00:00Z' }));

    fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

    await waitFor(() => expect(transport.requestsTo('PUT', lockPath)).toHaveLength(1));
    await act(async () => {});
    expect(
      await screen.findByRole('header', {
        name: planHeadingName({
          challengeId: CHALLENGE,
          anchor: PLANNED_AT,
          lockedAt: '2026-09-12T10:00:00Z',
        }),
      }),
    ).toBeTruthy();
  });
});
