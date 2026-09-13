/**
 * **The plan card, walked the way a member walks it**: the real route tree, the real shell, the
 * real room it is pinned in, and only `fetch` faked.
 *
 * Most of [#366](https://github.com/Raketa02/Raketa/issues/366)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — a chip reads its value or its name, the day
 * row shrinks and then empties with the refusal sentence beneath it, the hour row is the offered
 * grid, a past combination is refused in written copy rather than by a disabled control, nothing
 * is optimistic, and a slot can be changed as many times as anybody likes. So are
 * [#403](https://github.com/Raketa02/Raketa/issues/403)'s: the eyebrow and the counter, the lock
 * greyed below three slots and live at three, busy with its own word while it goes out, gone once
 * it has, each refusal by its code, and a lock that freezes nothing.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  PLANS_PATH,
  launchSignedIn,
  planSlotPath,
  resetLiveStream,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubLiveStream,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { fakeLiveStream, type FakeLiveStream } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOURS_OFFERED, type Plan } from '../domain/slots';

import { planErrorMessage } from './planErrorMessage';
import {
  LOCKED,
  LOCKING,
  LOCK_THE_PLAN,
  NO_DAY_LEFT_TO_SET,
  lockWaitsLine,
  PLAN_PANEL,
  QUICK_CHIP,
  RECORD_PLACE,
  SAVING,
  NOT_AGREED_YET,
  SLOT_NAME,
  THE_PLAN,
  counterLabel,
  dayChipLabel,
  dayChipName,
  planHeadingName,
} from './planPresentation';
import { mapErrorResponse, recoveryMessage } from '@/shared/errors';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

/** Saturday the 12th of September 2026, 09:00 in Warsaw — the day the line-up completed. */
const PLANNED_AT = '2026-09-12T07:00:00Z';

/** Wednesday the 9th, 09:00 in Warsaw — when the challenge was sent, three days before. */
const SENT_AT = '2026-09-09T07:00:00Z';

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

function room(
  gameId: string | null = GAME,
  readAt: string = PLANNED_AT,
): Wire['ConversationResponse'] {
  return {
    read_at: readAt,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: gameId,
    sport: 'PADEL',
    members: PAIR,
    people: PAIR,
    entries: [],
  };
}

function game(): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: PLANNED_AT,
    entry_closes_at: '2026-09-20T07:00:00Z',
    seats: [
      { side: 'A', player_id: ME, nickname: 'me_' },
      { side: 'B', player_id: TOMEK, nickname: 'tomek.p' },
    ],
    proposals: [],
  };
}

/** The row `GET /plans` lists for this court — with nothing agreed, and anchored at the filling. */
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

/** The same row as this feature reads it — for the deck's own functions. */
function agreed(over: Partial<Plan> = {}): Plan {
  return { challengeId: CHALLENGE, anchor: PLANNED_AT, ...over };
}

/** All three set, and the lock still to say so. */
const COMPLETE: Partial<Wire['PlanSchema']> = {
  place: 'Zabłocie Sport',
  day: '2026-09-13',
  hour: '18:00:00',
};

const LOCKED_AT = '2026-09-12T10:00:00Z';

const lockPath = `/api/v1/plans/${CHALLENGE}/lock`;

/** The refusal's own sentence, off the deck — never a raw string. */
const refusalSentence = (status: number, code: string) =>
  planErrorMessage(mapErrorResponse(status, { code, message: 'x' }));

let transport: Transport;
/** The room's live channel, driven by the one describe that is about what arrives on it. */
let channel: FakeLiveStream;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  channel = fakeLiveStream();
  stubLiveStream(channel);
});

afterEach(async () => {
  transport.restore();
  resetLiveStream();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * Land in the app, open Chats, tap the one row — the walk every assertion here starts with.
 *
 * `readAt` is **the room's** instant, because that is *today* on this card in the chat — and the
 * games list is folded at the same instant, so the header's rung and the card agree. `GET /plans`
 * carries none, deliberately. `agreed` defaults to the row every court the reader may plan has —
 * three nulls and the anchor — since ADR-0164 an absence there means the list has not landed.
 */
async function openTheRoom({
  agreed = plan(),
  gameId = GAME,
  readAt = PLANNED_AT,
  listLands,
}: {
  readonly agreed?: Wire['PlanSchema'];
  readonly gameId?: string | null;
  readonly readAt?: string;
  /** Holds `GET /plans` until this resolves — for the one test about the list not having landed. */
  readonly listLands?: Promise<unknown>;
} = {}) {
  stubGames(transport, gameId === null ? [] : [game()], readAt);
  if (listLands === undefined) stubPlans(transport, [agreed]);
  else {
    transport.on('GET', PLANS_PATH, async () => {
      await listLands;
      return json<Wire['PlanListResponse']>({ plans: [agreed] });
    });
  }
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: gameId,
      sport: 'PADEL',
      members: PAIR,
      people: PAIR,
      last_entry: null,
    },
  ]);
  stubConversation(transport, room(gameId, readAt));
  stubEntries(transport, ROOM);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
}

/** The chip for one slot, found by the name it says rather than by the value it draws. */
const slotChip = (name: string) => screen.getByLabelText(new RegExp(`^${name}:`));

/**
 * Let an answered response finish its way through the http client and the Query cache, **and
 * reach the screen**. The path is microtasks up to the cache and then one `setTimeout(0)` —
 * Query's `notifyManager` delivers cache updates on a macrotask — and this tree runs on the fake
 * timers `expo-router/testing-library` installs, so that last step has to be advanced by hand
 * rather than waited for. Sized by the bad path: with `usePlanWrite`'s cancel removed, the hour
 * rolls back exactly here.
 */
async function drained(read: Promise<unknown>): Promise<void> {
  const turns = async () => {
    for (let turn = 0; turn < 20; turn += 1) await Promise.resolve();
  };
  await act(async () => {
    await read;
    await turns();
  });
  act(() => {
    jest.advanceTimersByTime(1);
  });
  await act(turns);
}

describe('the card', () => {
  it('is the three slot chips, in where · day · hour order', async () => {
    await openTheRoom();

    expect(await screen.findByText(SLOT_NAME.where)).toBeTruthy();
    expect(screen.getByText(SLOT_NAME.day)).toBeTruthy();
    expect(screen.getByText(SLOT_NAME.hour)).toBeTruthy();
  });

  /**
   * The eyebrow and the counter are **one `header` element** — the heading and its count, which is
   * `YOUR GAMES · n`'s own shape — and the count is derived from the three fields, never sent.
   */
  it('is headed by the eyebrow and a count of the filled slots', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });

    const heading = await screen.findByRole('header', {
      name: planHeadingName(agreed({ day: '2026-09-13' })),
    });
    expect(within(heading).getByText(THE_PLAN)).toBeTruthy();
    expect(within(heading).getByText(counterLabel(agreed({ day: '2026-09-13' })))).toBeTruthy();
  });

  it('counts nought where nothing has been agreed', async () => {
    await openTheRoom();

    expect(await screen.findByText(counterLabel(agreed()))).toBeTruthy();
  });

  /**
   * **No panel in the room** — §3.2, still. The card grew a `note` slot for the game screen,
   * where the panel is drawn inside it ([#414](https://github.com/Raketa02/Raketa/issues/414),
   * `gameScreenPlanLead.test.tsx`); the room passes none, because the panel would be permanent
   * chrome above a composer (ADR-0145 §6).
   */
  it('draws no panel in the room', async () => {
    await openTheRoom();

    await screen.findByText(THE_PLAN);
    expect(screen.queryByText(PLAN_PANEL.title)).toBeNull();
    expect(screen.queryByText(PLAN_PANEL.body)).toBeNull();
  });

  /** §22.2: a chip reads its value once there is one, and the day is drawn as a weekday. */
  it('reads each value where there is one', async () => {
    await openTheRoom({
      agreed: plan({ place: 'Zabłocie Sport, court 3', day: '2026-09-13', hour: '18:00:00' }),
    });

    // The place is drawn without its court — #335's shorter value — and spoken whole.
    expect(await screen.findByText('Zabłocie Sport')).toBeTruthy();
    expect(screen.getByLabelText('Where: Zabłocie Sport, court 3')).toBeTruthy();
    expect(screen.getByText('Sunday')).toBeTruthy();
    expect(screen.getByText('18:00')).toBeTruthy();
  });

  /**
   * **The card is drawn from the room's opening** (ADR-0164 §2, #425): a room whose court is
   * still filling has a plan — the challenge's — and pins it with three empty slots and, where
   * the lock will be, the count line: two of a padel four are in. The header still draws the
   * sport alone and no *Details* door, which `conversationScreen.test.tsx` holds.
   */
  it('is drawn with three empty slots and the count line where the room has no game', async () => {
    await openTheRoom({ gameId: null });

    expect(await screen.findByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`)).toBeTruthy();
    expect(screen.getByText(counterLabel(agreed()))).toBeTruthy();
    expect(screen.getByText(lockWaitsLine({ in: 2, seats: 4 }))).toBeTruthy();
    expect(screen.queryByRole('button', { name: LOCK_THE_PLAN })).toBeNull();
  });

  /**
   * **A row that has not landed draws nothing** — the row is what says there is a plan to draw
   * and carries the anchor to draw it with, and a card that announced its own loading would be
   * chrome flickering above a stream.
   */
  it('is not drawn until the plan list has landed', async () => {
    let landed: () => void = () => {};
    const listLands = new Promise<void>((resolve) => {
      landed = resolve;
    });
    await openTheRoom({ gameId: null, listLands });

    // The room is up once its header names the other person — whole, in the spoken name, which
    // is the conversation's own deck and not this feature's to spell; the start is enough here.
    await screen.findByRole('header', { name: /^tomek\.p/ });
    expect(screen.queryByText(SLOT_NAME.day)).toBeNull();

    landed();
    expect(await screen.findByText(SLOT_NAME.day)).toBeTruthy();
  });
});

describe('the day row', () => {
  it('offers today and the six days after it', async () => {
    await openTheRoom();

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));

    for (const day of ['2026-09-12', '2026-09-13', '2026-09-18']) {
      expect(await screen.findByLabelText(dayChipName(day))).toBeTruthy();
    }
    // Seven days is seven weekdays and never eight: the row stops the day **before** it would
    // offer today's weekday a second time, which is what makes a weekday name identify a chip.
    expect(screen.getAllByLabelText(dayChipName('2026-09-12'))).toHaveLength(1);
  });

  /**
   * **The horizon is the row's anchor** (ADR-0164 §4) — the send while the court is filling, so a
   * room with no game offers a shorter row than its game will, and the same seven once it fills.
   * *Today* is the room's own `read_at`.
   */
  it('runs from the send while the room has no game', async () => {
    await openTheRoom({ gameId: null, agreed: plan({ anchor: SENT_AT }) });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));

    expect(await screen.findByLabelText(dayChipName('2026-09-16'))).toBeTruthy();
    expect(screen.queryByLabelText(dayChipName('2026-09-17'))).toBeNull();
  });

  /** The row is clamped to `anchor + PLAN_HORIZON` and shrinks as the week runs out. */
  it('shrinks as the horizon runs out', async () => {
    await openTheRoom({ readAt: '2026-09-16T07:00:00Z' });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));

    expect(await screen.findByLabelText(dayChipName('2026-09-19'))).toBeTruthy();
    expect(screen.queryByLabelText(dayChipName('2026-09-20'))).toBeNull();
  });

  /**
   * **Inside the entry grace no day may be set**, and the honest drawing of that is a row of no
   * chips with the refusal sentence beneath it.
   */
  it('draws no chips and says why inside the entry grace', async () => {
    await openTheRoom({ readAt: '2026-09-20T07:00:00Z' });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));

    expect(await screen.findByText(NO_DAY_LEFT_TO_SET)).toBeTruthy();
    expect(screen.queryByLabelText(dayChipName('2026-09-19'))).toBeNull();
  });

  /** The day already agreed stays on the row and stays pressable: a plan is never unmade. */
  it('keeps the agreed day on the row, drawn as the chosen one', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: Sunday`));

    const chosen = await screen.findByLabelText(dayChipName('2026-09-13'));
    expect(chosen.props.accessibilityState.selected).toBe(true);
  });
});

describe('the hour row', () => {
  it('is 30-minute steps between 06:00 and 23:00', async () => {
    await openTheRoom();

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`));

    expect(await screen.findByText('06:00')).toBeTruthy();
    expect(screen.getByText('06:30')).toBeTruthy();
    expect(screen.getByText('23:00')).toBeTruthy();
    expect(screen.queryByText('05:30')).toBeNull();
    expect(screen.queryByText('23:30')).toBeNull();
    expect(HOURS_OFFERED).toHaveLength(35);
  });
});

describe('recording a slot', () => {
  /**
   * **The writes are the challenge's** (ADR-0164 §1): a room with no game records a slot on the
   * same route its game will, and the chip reads the reply like any other.
   */
  it('records a slot in a room with no game, on the challenge-addressed route', async () => {
    await openTheRoom({ gameId: null });
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => json(plan({ day: '2026-09-13' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-13')));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'day'))).toHaveLength(1),
    );
    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`)).toBeTruthy());
    expect(screen.getByText(counterLabel(agreed({ day: '2026-09-13' })))).toBeTruthy();
  });

  it('sends the day and closes the row behind it', async () => {
    await openTheRoom();
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => json(plan({ day: '2026-09-13' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-13')));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'day'))).toHaveLength(1),
    );
    expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'day'))[0]?.body).toEqual({
      day: '2026-09-13',
    });
    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`)).toBeTruthy());
  });

  /**
   * **No optimistic write.** A slot change writes a line other people read, so the chip goes busy
   * with the value it already had and the new one is drawn only once the server has answered.
   */
  it('shows the chip pending and never the value being written', async () => {
    await openTheRoom();

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
  });

  /**
   * §22.2's one refusal, and it is **written copy rather than a disabled control** — the day and
   * the hour are filled in either order, so either can be the second and the sentence names both
   * remedies, with both chips directly above it.
   */
  it('draws a past combination as a sentence, not as a closed chip', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });
    transport.on('PUT', planSlotPath(CHALLENGE, 'hour'), () =>
      errorResponse(409, 'that_moment_has_already_passed'),
    );

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByText('18:00'));

    const sentence = planErrorMessage(
      mapErrorResponse(409, { code: 'that_moment_has_already_passed', message: 'x' }),
    );
    expect(await screen.findByText(sentence)).toBeTruthy();

    // Both remedies stay open: nothing is disabled by the refusal.
    const day = slotChip(SLOT_NAME.day);
    expect(day.props.accessibilityState.disabled).toBe(false);
  });

  /** Any member may change any slot, any number of times — the line is the friction. */
  it('lets a filled slot be changed again', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => json(plan({ day: '2026-09-14' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: Sunday`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-14')));

    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Monday`)).toBeTruthy());
  });

  /** The place is tidied on the way out — one line, and never truncated. */
  it('sends the place as one line', async () => {
    await openTheRoom();
    transport.on('PUT', planSlotPath(CHALLENGE, 'place'), () =>
      json(plan({ place: 'Zabłocie Sport' })),
    );

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`));
    fireEvent.changeText(await screen.findByLabelText(SLOT_NAME.where), '  Zabłocie   Sport ');
    fireEvent.press(screen.getByText(RECORD_PLACE));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'place'))[0]?.body).toEqual({
        place: 'Zabłocie Sport',
      }),
    );
  });

  /** **A slot is never emptied**, so a blank box is not a way of clearing one. */
  it('will not record a blank place', async () => {
    await openTheRoom();

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`));
    fireEvent.changeText(await screen.findByLabelText(SLOT_NAME.where), '   ');

    const record = await screen.findByLabelText(RECORD_PLACE);
    expect(record.props.accessibilityState.disabled).toBe(true);
  });
});

describe('the lock', () => {
  /** The button, found by its name — the same whether greyed, live or busy. */
  const lockButton = () => screen.getByRole('button', { name: LOCK_THE_PLAN });

  /** The counter's own sentence for a plan with every slot set and no lock. */
  const ALL_THREE = counterLabel(agreed({ place: 'x', day: '2026-09-13', hour: '18:00' }));
  const TWO = counterLabel(agreed({ place: 'x', day: '2026-09-13' }));

  /**
   * **The lock waits for the court** (ADR-0164 §5): while the room has no game the button is
   * **absent, not disabled**, and in its place stands the count line — the room's members over
   * the sport's seats. Two of a padel four are in, so `2 of 4`.
   */
  it('is absent while the room has no game, with the count line where it will be', async () => {
    await openTheRoom({ gameId: null, agreed: plan(COMPLETE) });

    expect(await screen.findByText(lockWaitsLine({ in: 2, seats: 4 }))).toBeTruthy();
    expect(screen.queryByRole('button', { name: LOCK_THE_PLAN })).toBeNull();
    expect(screen.queryByText(LOCK_THE_PLAN)).toBeNull();
  });

  /**
   * **The line becomes the button on the nudge that brings the game** (#406 as amended by
   * ADR-0164): the last acceptance's line arrives, the re-read room carries a game, and the
   * re-read games list says so — the slots recorded before are still shown, because it is the
   * same plan.
   */
  it('appears when the court fills, over the slots recorded before', async () => {
    await openTheRoom({
      gameId: null,
      agreed: plan({ place: 'Zabłocie Sport', day: '2026-09-13' }),
    });
    await screen.findByText(lockWaitsLine({ in: 2, seats: 4 }));

    stubGames(transport, [game()], PLANNED_AT);
    stubConversation(transport, {
      ...room(),
      entries: [
        {
          type: 'system_line',
          seq: 1,
          code: 'SEAT_ACCEPTED',
          occurred_at: PLANNED_AT,
          actor_id: TOMEK,
          values: {},
        },
      ],
    });
    act(() => channel.nudge(ROOM));

    expect(await screen.findByRole('button', { name: LOCK_THE_PLAN })).toBeTruthy();
    expect(screen.queryByText(lockWaitsLine({ in: 2, seats: 4 }))).toBeNull();
    expect(screen.getByLabelText('Where: Zabłocie Sport')).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`)).toBeTruthy();
  });

  /**
   * **Greyed and not pressable while any slot is empty** — 6.1's `disabled`, announced — and the
   * sentence #324 owes a greyed control is the counter directly above it, which already says
   * `2 of 3 set`. The label carries no reason.
   */
  it('is greyed while any slot is empty', async () => {
    await openTheRoom({ agreed: plan({ place: 'Zabłocie Sport', day: '2026-09-13' }) });

    await screen.findByText(TWO);
    expect(lockButton().props.accessibilityState.disabled).toBe(true);
    expect(screen.getByText(LOCK_THE_PLAN)).toBeTruthy();
    expect(screen.queryByText(/set all three/i)).toBeNull();
  });

  it('is live once all three are set', async () => {
    await openTheRoom({ agreed: plan(COMPLETE) });

    await screen.findByText(ALL_THREE);
    expect(lockButton().props.accessibilityState.disabled).toBe(false);
  });

  /** `PUT`, no body: the value is the three slots and they are already recorded. */
  it('sends the lock with no body, and the counter reads Locked once it lands', async () => {
    await openTheRoom({ agreed: plan(COMPLETE) });
    transport.on('PUT', lockPath, () => json(plan({ ...COMPLETE, locked_at: LOCKED_AT })));

    fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

    await waitFor(() => expect(transport.requestsTo('PUT', lockPath)).toHaveLength(1));
    expect(transport.requestsTo('PUT', lockPath)[0]?.body).toBeUndefined();

    expect(await screen.findByText(LOCKED)).toBeTruthy();
    expect(screen.queryByText(ALL_THREE)).toBeNull();
    expect(
      screen.getByRole('header', {
        name: planHeadingName(agreed({ lockedAt: LOCKED_AT })),
      }),
    ).toBeTruthy();
  });

  /**
   * **Pending, never optimistic.** The press is blocked, the word changes, and the counter keeps
   * saying `3 of 3 set` until the server has answered — busy and disabled are both greyed, so the
   * word is the only thing telling them apart.
   */
  it('goes busy with its own word while the lock is going out', async () => {
    await openTheRoom({ agreed: plan(COMPLETE) });

    let answer: (schema: Wire['PlanSchema']) => void = () => {};
    const held = new Promise<Wire['PlanSchema']>((resolve) => {
      answer = resolve;
    });
    transport.on('PUT', lockPath, async () => json(await held));

    fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

    const busy = await screen.findByRole('button', { name: LOCKING });
    expect(busy.props.accessibilityState.busy).toBe(true);
    expect(busy.props.accessibilityState.disabled).toBe(true);
    expect(screen.getByText(ALL_THREE)).toBeTruthy();
    expect(screen.queryByText(LOCKED)).toBeNull();

    answer(plan({ ...COMPLETE, locked_at: LOCKED_AT }));
    await screen.findByText(LOCKED);
  });

  /**
   * **Gone, not settled.** A second lock records nothing and answers `200`, so a control still
   * offering the act would be one that provably does nothing; the counter's word is the carrier.
   */
  it('is gone once the plan is locked, and the word Locked carries the fact', async () => {
    await openTheRoom({ agreed: plan({ ...COMPLETE, locked_at: LOCKED_AT }) });

    expect(await screen.findByText(LOCKED)).toBeTruthy();
    expect(screen.queryByRole('button', { name: LOCK_THE_PLAN })).toBeNull();
    expect(screen.queryByText(LOCK_THE_PLAN)).toBeNull();
  });

  /**
   * **A lock freezes nothing** (ADR-0155 §4). Every chip stays live on a locked plan, a move
   * writes its own line, and the plan stays locked.
   */
  it('leaves every slot editable, and the plan stays locked after a move', async () => {
    await openTheRoom({ agreed: plan({ ...COMPLETE, locked_at: LOCKED_AT }) });
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () =>
      json(plan({ ...COMPLETE, day: '2026-09-14', locked_at: LOCKED_AT })),
    );

    await screen.findByText(LOCKED);
    expect(slotChip(SLOT_NAME.day).props.accessibilityState.disabled).toBe(false);

    fireEvent.press(screen.getByLabelText(`${SLOT_NAME.day}: Sunday`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-14')));

    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Monday`)).toBeTruthy());
    expect(screen.getByText(LOCKED)).toBeTruthy();
    expect(screen.queryByRole('button', { name: LOCK_THE_PLAN })).toBeNull();
  });

  describe('refused', () => {
    /**
     * Unreachable through the UI — the button is greyed below three — and handled anyway: the
     * button is UX and the server is the correctness mechanism. The sentence is the code's own.
     */
    it('by an incomplete plan, in a sentence naming the remedy', async () => {
      await openTheRoom({ agreed: plan(COMPLETE) });
      transport.on('PUT', lockPath, () => errorResponse(409, 'the_plan_is_not_complete'));

      fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

      expect(
        await screen.findByText(refusalSentence(409, 'the_plan_is_not_complete')),
      ).toBeTruthy();
      // The retry is the control that failed, and it is still there.
      expect(lockButton().props.accessibilityState.disabled).toBe(false);
    });

    /**
     * The absent button makes it unreachable from a room with no game; a game with a seat later
     * left open still draws the button, and the server's answer is a sentence rather than silence.
     */
    it('by a court that is not whole, in its own sentence', async () => {
      await openTheRoom({ agreed: plan(COMPLETE) });
      transport.on('PUT', lockPath, () => errorResponse(409, 'the_court_is_not_whole'));

      fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

      expect(await screen.findByText(refusalSentence(409, 'the_court_is_not_whole'))).toBeTruthy();
      expect(lockButton().props.accessibilityState.disabled).toBe(false);
    });

    it('by a game that is over, in the sentence every plan write shares', async () => {
      await openTheRoom({ agreed: plan(COMPLETE) });
      transport.on('PUT', lockPath, () => errorResponse(409, 'plan_is_history'));

      fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

      expect(await screen.findByText(refusalSentence(409, 'plan_is_history'))).toBeTruthy();
    });

    it('by a plan that is not this reader’s, in its own sentence', async () => {
      await openTheRoom({ agreed: plan(COMPLETE) });
      transport.on('PUT', lockPath, () => errorResponse(404, 'plan_not_found'));

      fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

      expect(await screen.findByText(refusalSentence(404, 'plan_not_found'))).toBeTruthy();
    });

    /** Each refusal is a sentence of its own, and none of them is the fallback. */
    it('by each code in a different sentence', () => {
      const sentences = [
        refusalSentence(409, 'the_plan_is_not_complete'),
        refusalSentence(409, 'the_court_is_not_whole'),
        refusalSentence(409, 'plan_is_history'),
        refusalSentence(404, 'plan_not_found'),
      ];

      expect(new Set(sentences).size).toBe(4);
      expect(sentences).not.toContain(refusalSentence(409, 'a_code_this_build_has_never_seen'));
    });

    /**
     * **A hold is a fact about the account, not about the lock that met it.** It reaches the room's
     * fold off this feature's mutation cache and draws as the room's one amber note — whose words
     * are that feature's to assert — rather than as a coral sentence here, and every control that
     * writes, the chips and the button, greys under it.
     */
    it('by a held account, as one note over greyed controls and never a coral sentence', async () => {
      await openTheRoom({ agreed: plan(COMPLETE) });
      transport.on('PUT', lockPath, () => errorResponse(403, 'account_held'));

      fireEvent.press(await screen.findByRole('button', { name: LOCK_THE_PLAN }));

      await waitFor(() => expect(lockButton().props.accessibilityState.disabled).toBe(true));
      expect(slotChip(SLOT_NAME.day).props.accessibilityState.disabled).toBe(true);

      // One note, and it is not this card's: the fallback a 403 would otherwise draw is absent,
      // and so is any sentence the plan's own table could have written for it.
      const held = mapErrorResponse(403, { code: 'account_held', message: 'x' });
      expect(screen.getAllByRole('alert')).toHaveLength(1);
      expect(screen.queryByText(recoveryMessage(held))).toBeNull();
      expect(screen.queryByText(planErrorMessage(held))).toBeNull();
    });
  });
});

describe('a held account', () => {
  /**
   * A hold stops you writing anywhere another player sees it and **never stops you reading**. The
   * note that says why is the room's — one note for every refused control on the screen — which is
   * the condition a greyed chip comes with.
   */
  it('greys every chip and keeps the card', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });
    transport.on('POST', `/api/v1/conversations/${ROOM}/messages`, () =>
      errorResponse(403, 'account_held'),
    );

    fireEvent.changeText(await screen.findByLabelText('Message'), 'six?');
    fireEvent.press(screen.getByText('Send'));

    await waitFor(() =>
      expect(slotChip(SLOT_NAME.day).props.accessibilityState.disabled).toBe(true),
    );
    expect(screen.getByText('Sunday')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: LOCK_THE_PLAN }).props.accessibilityState.disabled,
    ).toBe(true);
  });

  /**
   * The chips' own refusal reaches the room's fold too — a hold met on a slot write is the same
   * fact as one met on the send, and it was `planErrorMessage`'s stated shape before anything
   * wired it. The note's words are the room's to assert; what is this card's is that every chip
   * greys and no coral sentence is drawn for it.
   */
  it('is told by a slot write, not only by the send', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });
    transport.on('PUT', planSlotPath(CHALLENGE, 'hour'), () => errorResponse(403, 'account_held'));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByText('18:00'));

    await waitFor(() =>
      expect(slotChip(SLOT_NAME.day).props.accessibilityState.disabled).toBe(true),
    );
    expect(slotChip(SLOT_NAME.hour).props.accessibilityState.disabled).toBe(true);
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(
      screen.queryByText(
        recoveryMessage(mapErrorResponse(403, { code: 'account_held', message: 'x' })),
      ),
    ).toBeNull();
  });
});

describe('the quick chips beside it', () => {
  /**
   * One chip per unfilled slot, in slot order — and the plan is what says which are unfilled.
   * The rule and the words are this feature's; the row that draws them is the room's, because a
   * chip is a message and the send is the composer's.
   */
  it('ask only about the slots that are still empty', async () => {
    await openTheRoom({ agreed: plan({ place: 'Zabłocie Sport', hour: '18:00:00' }) });

    // The row is drawn before the plan lands — three questions, which is what *no plan* means —
    // and narrows the moment it does, so the card reading its values is what says it has.
    await waitFor(() => expect(screen.getByLabelText('Where: Zabłocie Sport')).toBeTruthy());

    expect(screen.getByText(QUICK_CHIP.day)).toBeTruthy();
    expect(screen.queryByText(QUICK_CHIP.where)).toBeNull();
    expect(screen.queryByText(QUICK_CHIP.hour)).toBeNull();
  });
});

describe('what another member set arrives on the nudge', () => {
  /** One line, as the room re-reads it: the code, who, and the value the slot now holds. */
  function line(
    seq: number,
    code: string,
    values: Readonly<Record<string, string>> = {},
  ): Wire['SystemLineSchema'] {
    return { type: 'system_line', seq, code, occurred_at: PLANNED_AT, actor_id: TOMEK, values };
  }

  /**
   * **The card follows the line, on every phone in the room** ([#405](https://github.com/Raketa02/Raketa/issues/405)).
   * A slot somebody else set reaches this phone as a system line on the nudge, and the card is
   * read off `GET /plans` — so the nudge re-reads that list beside the room, and the chip says the
   * value with nothing pressed here.
   */
  it('draws the place another member set, with nothing pressed', async () => {
    await openTheRoom();
    await screen.findByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`);

    stubPlans(transport, [plan({ place: 'Zabłocie Sport' })]);
    stubConversation(transport, {
      ...room(),
      entries: [line(1, 'PLACE_RECORDED', { value: 'Zabłocie Sport' })],
    });
    act(() => channel.nudge(ROOM));

    expect(await screen.findByLabelText('Where: Zabłocie Sport')).toBeTruthy();
    expect(screen.getByText(counterLabel(agreed({ place: 'Zabłocie Sport' })))).toBeTruthy();
  });

  /**
   * The lock is the same fact one act later: somebody else agreed it, the line says so, and the
   * counter reads `Locked` with the button **gone** — a control still offering the act would be one
   * that provably does nothing, and until this phone re-read the plan that is exactly what it was.
   */
  it('reads Locked and drops the button when another member locks it', async () => {
    await openTheRoom({ agreed: plan(COMPLETE) });
    await screen.findByRole('button', { name: LOCK_THE_PLAN });

    stubPlans(transport, [plan({ ...COMPLETE, locked_at: LOCKED_AT })]);
    stubConversation(transport, { ...room(), entries: [line(1, 'PLAN_LOCKED')] });
    act(() => channel.nudge(ROOM));

    expect(await screen.findByText(LOCKED)).toBeTruthy();
    expect(screen.queryByRole('button', { name: LOCK_THE_PLAN })).toBeNull();
  });

  /** The quick chips read the same row, so a question about a slot somebody just filled goes. */
  it('stops asking about the slot another member filled', async () => {
    await openTheRoom();
    await screen.findByText(QUICK_CHIP.hour);

    stubPlans(transport, [plan({ hour: '18:00:00' })]);
    stubConversation(transport, {
      ...room(),
      entries: [line(1, 'HOUR_RECORDED', { value: '18:00' })],
    });
    act(() => channel.nudge(ROOM));

    await waitFor(() => expect(screen.queryByText(QUICK_CHIP.hour)).toBeNull());
    expect(screen.getByText(QUICK_CHIP.where)).toBeTruthy();
    expect(screen.getByText(QUICK_CHIP.day)).toBeTruthy();
  });

  /**
   * **The write-in and the re-read can cross, and the write-in wins.** A nudge for the day's line
   * starts a `GET /plans`; this phone records the hour while that read is in flight; the `PUT`
   * answers first and is written in. The older read landing afterwards must not roll the hour
   * back to empty — which is what it would do, for a second, until the hour's own nudge repaired
   * it. Nothing here is optimistic: what is refused is a read that can only be older than the reply.
   */
  it('keeps a value this phone just recorded when an older read lands after it', async () => {
    await openTheRoom({ agreed: plan({ day: '2026-09-13' }) });
    await screen.findByLabelText(`${SLOT_NAME.day}: Sunday`);

    let answerTheRead: (plans: Wire['PlanSchema'][]) => void = () => {};
    const held = new Promise<Wire['PlanSchema'][]>((resolve) => {
      answerTheRead = resolve;
    });
    /** The read the nudge starts, so the test can wait for it to have been answered in full. */
    let read: Promise<Response> = Promise.resolve(json({ plans: [] }));
    transport.on('GET', PLANS_PATH, () => {
      read = held.then((plans) => json<Wire['PlanListResponse']>({ plans }));
      return read;
    });
    transport.on('PUT', planSlotPath(CHALLENGE, 'hour'), () =>
      json(plan({ day: '2026-09-13', hour: '18:00:00' })),
    );

    act(() => channel.nudge(ROOM));
    await waitFor(() => expect(transport.requestsTo('GET', PLANS_PATH).length).toBeGreaterThan(1));

    fireEvent.press(screen.getByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`));
    fireEvent.press(await screen.findByText('18:00'));
    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.hour}: 18:00`)).toBeTruthy());

    // The read the nudge started answers now, with the plan as it stood before the hour — and
    // the test waits for that answer to have been handled, not merely sent: without the cancel
    // this is the point at which the hour rolled back, which is how the drain was sized.
    answerTheRead([plan({ day: '2026-09-13' })]);
    await drained(read);

    expect(screen.getByLabelText(`${SLOT_NAME.hour}: 18:00`)).toBeTruthy();
    expect(screen.queryByLabelText(`${SLOT_NAME.hour}: ${NOT_AGREED_YET}`)).toBeNull();
  });

  /**
   * The day sheet reads `agreed` off the plan, so another member's day landing while it is up
   * moves the chosen chip under this player's thumb — and their own pick still writes their day.
   * *Any member may change any slot, any number of times*: no new behaviour, asserted.
   */
  it('moves the chosen day under an open sheet, and the player’s pick still writes theirs', async () => {
    await openTheRoom();
    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
    await screen.findByLabelText(dayChipName('2026-09-13'));

    stubPlans(transport, [plan({ day: '2026-09-13' })]);
    stubConversation(transport, {
      ...room(),
      entries: [line(1, 'DAY_RECORDED', { value: '2026-09-13' })],
    });
    act(() => channel.nudge(ROOM));

    await waitFor(() =>
      expect(
        screen.getByLabelText(dayChipName('2026-09-13')).props.accessibilityState.selected,
      ).toBe(true),
    );

    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => json(plan({ day: '2026-09-14' })));
    fireEvent.press(screen.getByLabelText(dayChipName('2026-09-14')));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'day'))[0]?.body).toEqual({
        day: '2026-09-14',
      }),
    );
    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Monday`)).toBeTruthy());
  });

  /**
   * A typed note is the player's. Somebody else's place landing under the open sheet moves the
   * chip behind it and never the words in the box — *a refusal puts the words back in the box*,
   * and so does another member's value; recording then writes what this player typed.
   */
  it('keeps the words in the where box when another member sets the place underneath', async () => {
    await openTheRoom();
    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`));
    fireEvent.changeText(await screen.findByLabelText(SLOT_NAME.where), 'Hala Cracovia');

    stubPlans(transport, [plan({ place: 'Zabłocie Sport' })]);
    stubConversation(transport, {
      ...room(),
      entries: [line(1, 'PLACE_RECORDED', { value: 'Zabłocie Sport' })],
    });
    act(() => channel.nudge(ROOM));
    // The chip is behind the sheet — hidden from assistive tech while the modal is up, and
    // exactly where the other member's value lands.
    await screen.findByLabelText('Where: Zabłocie Sport', { includeHiddenElements: true });

    expect(screen.getByDisplayValue('Hala Cracovia')).toBeTruthy();

    transport.on('PUT', planSlotPath(CHALLENGE, 'place'), () =>
      json(plan({ place: 'Hala Cracovia' })),
    );
    fireEvent.press(screen.getByText(RECORD_PLACE));
    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(CHALLENGE, 'place'))[0]?.body).toEqual({
        place: 'Hala Cracovia',
      }),
    );
  });
});

/** The row is drawn short and spoken whole — §20.4, one surface over. */
it('draws a short weekday on the row and speaks the whole one', async () => {
  await openTheRoom();

  fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: ${NOT_AGREED_YET}`));
  const chip = await screen.findByLabelText(dayChipName('2026-09-13'));

  expect(within(chip).getByText(dayChipLabel('2026-09-13'))).toBeTruthy();
  expect(dayChipLabel('2026-09-13')).toBe('Sun');
});
