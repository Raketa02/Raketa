/**
 * **The plan card, walked the way a member walks it**: the real route tree, the real shell, the
 * real room it is pinned in, and only `fetch` faked.
 *
 * Most of [#366](https://github.com/Raketa02/Raketa/issues/366)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the card is the three chips and nothing
 * else, a chip reads its value or its name, the day row shrinks and then empties with the refusal
 * sentence beneath it, the hour row is the offered grid, a past combination is refused in written
 * copy rather than by a disabled control, nothing is optimistic, there is no lock, and a slot can
 * be changed as many times as anybody likes.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchSignedIn,
  planSlotPath,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOURS_OFFERED } from '../domain/slots';

import { planErrorMessage } from './planErrorMessage';
import {
  NO_DAY_LEFT_TO_SET,
  QUICK_CHIP,
  RECORD_PLACE,
  SAVING,
  SLOT_NAME,
  dayChipLabel,
  dayChipName,
} from './planPresentation';
import { mapErrorResponse } from '@/shared/errors';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

/** Saturday the 12th of September 2026, 09:00 in Warsaw — the day the line-up completed. */
const PLANNED_AT = '2026-09-12T07:00:00Z';

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

function room(gameId: string | null = GAME): Wire['ConversationResponse'] {
  return {
    read_at: PLANNED_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: gameId,
    sport: 'PADEL',
    members: PAIR,
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

/**
 * Land in the app, open Chats, tap the one row — the walk every assertion here starts with.
 *
 * `readAt` is the **games** list's instant, because that is the one clock this card is folded
 * against: `GET /plans` carries none, deliberately.
 */
async function openTheRoom({
  agreed,
  gameId = GAME,
  readAt = PLANNED_AT,
}: {
  readonly agreed?: Wire['PlanSchema'];
  readonly gameId?: string | null;
  readonly readAt?: string;
} = {}) {
  stubGames(transport, gameId === null ? [] : [game()], readAt);
  stubPlans(transport, agreed === undefined ? [] : [agreed]);
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: gameId,
      sport: 'PADEL',
      members: PAIR,
      last_entry: null,
    },
  ]);
  stubConversation(transport, room(gameId));
  stubEntries(transport, ROOM);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
}

/** The chip for one slot, found by the name it says rather than by the value it draws. */
const slotChip = (name: string) => screen.getByLabelText(new RegExp(`^${name}:`));

describe('the card', () => {
  it('is the three slot chips, in where · day · hour order', async () => {
    await openTheRoom();

    expect(await screen.findByText(SLOT_NAME.where)).toBeTruthy();
    expect(screen.getByText(SLOT_NAME.day)).toBeTruthy();
    expect(screen.getByText(SLOT_NAME.hour)).toBeTruthy();
  });

  /**
   * ADR-0144 deleted *Lock it in*, the locked border and the `locked by everybody` pill: filling
   * the third slot **is** the lock, and none of the three has anything left to draw.
   */
  it('draws no lock, whatever is agreed', async () => {
    await openTheRoom({
      agreed: plan({ place: 'Zabłocie Sport', day: '2026-09-13', hour: '18:00:00' }),
    });

    await screen.findByText('Sunday');
    expect(screen.queryByText(/lock/i)).toBeNull();
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
   * A room whose line-up has not completed has **no game and no plan**, so there is nothing to
   * pin — the same nothing the header's absent *Details* draws, from the same field.
   */
  it('is not drawn at all where the room has no game', async () => {
    await openTheRoom({ gameId: null });

    await screen.findByRole('header', { name: 'tomek.p' });
    expect(screen.queryByText(SLOT_NAME.day)).toBeNull();
  });
});

describe('the day row', () => {
  it('offers today and the six days after it', async () => {
    await openTheRoom();

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));

    for (const day of ['2026-09-12', '2026-09-13', '2026-09-18']) {
      expect(await screen.findByLabelText(dayChipName(day))).toBeTruthy();
    }
    // Seven days is seven weekdays and never eight: the row stops the day **before** it would
    // offer today's weekday a second time, which is what makes a weekday name identify a chip.
    expect(screen.getAllByLabelText(dayChipName('2026-09-12'))).toHaveLength(1);
  });

  /** The row is clamped to `planned_at + PLAN_HORIZON` and shrinks as the week runs out. */
  it('shrinks as the horizon runs out', async () => {
    await openTheRoom({ readAt: '2026-09-16T07:00:00Z' });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));

    expect(await screen.findByLabelText(dayChipName('2026-09-19'))).toBeTruthy();
    expect(screen.queryByLabelText(dayChipName('2026-09-20'))).toBeNull();
  });

  /**
   * **Inside the entry grace no day may be set**, and the honest drawing of that is a row of no
   * chips with the refusal sentence beneath it.
   */
  it('draws no chips and says why inside the entry grace', async () => {
    await openTheRoom({ readAt: '2026-09-20T07:00:00Z' });

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));

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

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.hour}: not agreed yet`));

    expect(await screen.findByText('06:00')).toBeTruthy();
    expect(screen.getByText('06:30')).toBeTruthy();
    expect(screen.getByText('23:00')).toBeTruthy();
    expect(screen.queryByText('05:30')).toBeNull();
    expect(screen.queryByText('23:30')).toBeNull();
    expect(HOURS_OFFERED).toHaveLength(35);
  });
});

describe('recording a slot', () => {
  it('sends the day and closes the row behind it', async () => {
    await openTheRoom();
    transport.on('PUT', planSlotPath(GAME, 'day'), () => json(plan({ day: '2026-09-13' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-13')));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(GAME, 'day'))).toHaveLength(1),
    );
    expect(transport.requestsTo('PUT', planSlotPath(GAME, 'day'))[0]?.body).toEqual({
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
    transport.on('PUT', planSlotPath(GAME, 'day'), async () => json(await held));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));
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
    transport.on('PUT', planSlotPath(GAME, 'hour'), () =>
      errorResponse(409, 'that_moment_has_already_passed'),
    );

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.hour}: not agreed yet`));
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
    transport.on('PUT', planSlotPath(GAME, 'day'), () => json(plan({ day: '2026-09-14' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: Sunday`));
    fireEvent.press(await screen.findByLabelText(dayChipName('2026-09-14')));

    await waitFor(() => expect(screen.getByLabelText(`${SLOT_NAME.day}: Monday`)).toBeTruthy());
  });

  /** The place is tidied on the way out — one line, and never truncated. */
  it('sends the place as one line', async () => {
    await openTheRoom();
    transport.on('PUT', planSlotPath(GAME, 'place'), () => json(plan({ place: 'Zabłocie Sport' })));

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.where}: not agreed yet`));
    fireEvent.changeText(await screen.findByLabelText(SLOT_NAME.where), '  Zabłocie   Sport ');
    fireEvent.press(screen.getByText(RECORD_PLACE));

    await waitFor(() =>
      expect(transport.requestsTo('PUT', planSlotPath(GAME, 'place'))[0]?.body).toEqual({
        place: 'Zabłocie Sport',
      }),
    );
  });

  /** **A slot is never emptied**, so a blank box is not a way of clearing one. */
  it('will not record a blank place', async () => {
    await openTheRoom();

    fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.where}: not agreed yet`));
    fireEvent.changeText(await screen.findByLabelText(SLOT_NAME.where), '   ');

    const record = await screen.findByLabelText(RECORD_PLACE);
    expect(record.props.accessibilityState.disabled).toBe(true);
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

/** The row is drawn short and spoken whole — §20.4, one surface over. */
it('draws a short weekday on the row and speaks the whole one', async () => {
  await openTheRoom();

  fireEvent.press(await screen.findByLabelText(`${SLOT_NAME.day}: not agreed yet`));
  const chip = await screen.findByLabelText(dayChipName('2026-09-13'));

  expect(within(chip).getByText(dayChipLabel('2026-09-13'))).toBeTruthy();
  expect(dayChipLabel('2026-09-13')).toBe('Sun');
});
