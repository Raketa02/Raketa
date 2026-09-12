/**
 * **The game screen's plan, walked the way a player walks it**: the real route tree, the real
 * shell, both doors into the screen, and only `fetch` faked.
 *
 * Most of [#368](https://github.com/Raketa02/Raketa/issues/368)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the three plan arms are on the screen the
 * result argument already keys, *Open the chat* is drawn whichever door you came in by, *We
 * played* is available on every entry arm, one component answers two routes, and the corrections
 * to the details design are absences rather than sentences. **Since
 * [#414](https://github.com/Raketa02/Raketa/issues/414) the two plan-lead rungs draw the chat's
 * editable card** — that layout is `gameScreenPlanLead.test.tsx`'s — so what is read-only in
 * `Tag`s with the checklist under it is the **score lead**, and those assertions stand there.
 *
 * The words are `planPresentation.test.ts`'s and the ladder is `ladder.test.ts`'s; what is asserted
 * here is that the screen is wired to both, against the **copy deck** wherever a sentence has a
 * home.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { BALANCE_FORECAST, PLAYERS, recordLabel } from '@/features/games/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import {
  GATE_USER,
  launchSignedIn,
  pairingPath,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { RUNGS } from '../domain/ladder';

import { doorLabel } from './nowPresentation';
import {
  EVERYBODY_SAID_YES,
  LOCK_THE_PLAN,
  NOTHING_IS_LEFT_TO_AGREE,
  NOT_AGREED_YET,
  PLAN_PANEL,
  PLAN_SPOKEN_LEAD,
  SLOT_NAME,
  STILL_TO_AGREE,
  counterLabel,
} from './planPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';

/** Four days before it, which is when the line-up completed. */
const PLANNED_AT = '2026-09-08T09:00:00Z';

/** What `worthLine` says about a counted game — cited here exactly as the checklist cites it. */
const WORTH_COUNTED = 'This one counts, so an agreed score becomes part of your record.';

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

/** The whole plan, agreed for a day that is still ahead — the *Game on* arm's own values. */
const WHOLE = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-19',
  hour: '18:00',
  agreed_point: '2026-09-19T16:00:00Z',
});

/** The whole plan, agreed for this morning — the *Needs result* arm's, which leads with the score. */
const PASSED = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-12',
  hour: '08:00',
  agreed_point: '2026-09-12T06:00:00Z',
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
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
  readonly room?: boolean;
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
            members: PAIR,
            people: PAIR,
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
    members: PAIR,
    people: PAIR,
    entries: [],
  });
  stubEntries(transport, ROOM);
  stubPairing(transport, GAME, {
    read_at: READ_AT,
    forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
    split: { your_side: 2.7, their_side: 2.71, gap: -0.01 },
    at_stake: { win_delta: 0.08, loss_delta: -0.08 },
    seats: [],
  });
}

/**
 * In through the Now card's wide door — the one §5.2 gives every rung, and since #413 the only
 * way in from the rail: the body is not pressable, and an ending carries no door at all.
 */
async function openFromNow(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));

  const verbs = RUNGS.map(doorLabel).filter((verb): verb is string => verb !== undefined);
  fireEvent.press(await screen.findByLabelText(new RegExp(`^(${[...new Set(verbs)].join('|')})$`)));
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
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

describe('the three plan arms', () => {
  /**
   * §5.1's *Planning*, as #414 redrew it: the plan as it stands in **chips to fill**, the panel
   * inside the card, and the count of what is set where the checklist's list of what is missing
   * used to be — the counter says how much, the chips say which.
   */
  it('draws the plan as chips to fill, and counts what is set', async () => {
    await openFromNow();

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    for (const name of Object.values(SLOT_NAME)) {
      expect(screen.getByLabelText(`${name}: ${NOT_AGREED_YET}`)).toBeTruthy();
    }
    expect(screen.getByText(counterLabel(undefined))).toBeTruthy();
    expect(screen.queryByText(new RegExp(`^${STILL_TO_AGREE}`))).toBeNull();
  });

  /** *Game on*: the plan, whole, in the chips — the values, and never a part of a day. */
  it('draws the plan whole once there is nothing left to agree', async () => {
    await openFromNow({ plans: [WHOLE] });

    // #335's shorter value is drawn and §20.4's whole one is spoken — on the chip and on the card.
    expect(
      await screen.findByLabelText(`${SLOT_NAME.where}: Zabłocie Sport, court 3`),
    ).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: Saturday`)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.hour}: 18:00`)).toBeTruthy();
    expect(
      screen.getByText(counterLabel({ gameId: GAME, place: 'x', day: 'd', hour: 'h' })),
    ).toBeTruthy();
    expect(screen.queryByText(NOTHING_IS_LEFT_TO_AGREE)).toBeNull();
  });

  /**
   * *Today* and *Needs result* are one arm here: the plan, and how long is left to say you played
   * — which is the screen's own clock, folded from `entry_closes_at` against the list's `read_at`.
   */
  it('draws the plan and the window left, once the agreed point has passed', async () => {
    await openFromNow({
      plans: [
        plan({
          place: 'Zabłocie Sport',
          day: '2026-09-12',
          hour: '08:00',
          agreed_point: '2026-09-12T06:00:00Z',
        }),
      ],
    });

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    // The window is the **screen's** own sentence, folded from `entry_closes_at` against the
    // games list's `read_at` and never restated by the plan block beneath it.
    expect(
      screen.getByText('Nobody has said this one happened yet — 8 days left to say you played.'),
    ).toBeTruthy();
  });

  /**
   * §5.1: the four confirm arms and the ended arms are **built and untouched**. A settled game has
   * no plan panel over it — an agreement about a future, above a record of a past.
   */
  it('draws nothing of the plan on an arm that is not an entry', async () => {
    // Through the room: an ended game's card on Now carries no door (#413), so the screen behind
    // it is reached by its other address.
    await openFromTheRoom({
      games: [game({ standing: 'CONFIRMED', played_at: READ_AT, entry_closes_at: null })],
      plans: [WHOLE],
    });

    expect(await screen.findByText('Agreed.')).toBeTruthy();
    expect(screen.queryByText(PLAN_PANEL.title)).toBeNull();
    expect(screen.queryByText(EVERYBODY_SAID_YES)).toBeNull();
    // The worth line is the checklist's third line on an entry arm and the screen's everywhere
    // else, so it is printed exactly once here too.
    expect(screen.getAllByText(WORTH_COUNTED)).toHaveLength(1);
  });
});

describe('the plan is read-only on the score lead', () => {
  /**
   * §5.4's fifth correction, and ADR-0149 §4 under it — narrowed by #414 to the two rungs that
   * lead with the score, where the plan is context for a score rather than the errand: *a control
   * that cannot be operated must not offer the affordance of one.* §24.5 makes the three one
   * element, which is the reason `Tag` was chosen over `Chip` in the first place.
   */
  it('is one element with no action, and names each slot inside it', async () => {
    await openFromNow({ plans: [PASSED] });

    const spoken = await screen.findByLabelText(new RegExp(`^${PLAN_SPOKEN_LEAD}`));

    expect(spoken).toBeTruthy();
    expect(spoken.props.accessibilityRole).toBeUndefined();
    expect(spoken.props.accessibilityLabel).toBe(
      `${PLAN_SPOKEN_LEAD} Where, Zabłocie Sport, court 3. Day, Saturday. Hour, 08:00.`,
    );
    expect(screen.queryByText(LOCK_THE_PLAN)).toBeNull();
  });

  it('says an unfilled slot is not agreed yet rather than offering a way to fill it', async () => {
    // The agreed day is today, so the score leads — with the place and the hour still to agree.
    await openFromNow({
      plans: [plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' })],
    });

    const spoken = await screen.findByLabelText(new RegExp(`^${PLAN_SPOKEN_LEAD}`));
    expect(spoken.props.accessibilityLabel).toContain(NOT_AGREED_YET);
    expect(screen.queryByLabelText(`${SLOT_NAME.where}: ${NOT_AGREED_YET}`)).toBeNull();
  });
});

describe('the two acts on an entry arm', () => {
  /**
   * §5.1: *always drawn, whichever door you came in by* — arriving from Now it is the point, and
   * arriving from Details it is the way back. Drawing it conditionally would make the surface
   * depend on its door.
   */
  it('draws Open the chat coming in from Now', async () => {
    await openFromNow({ plans: [WHOLE] });

    fireEvent.press(await screen.findByText(OPEN_THE_CHAT));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  it('draws Open the chat coming in from the room', async () => {
    await openFromTheRoom({ plans: [WHOLE] });

    expect(await screen.findByText(OPEN_THE_CHAT)).toBeTruthy();
  });

  /**
   * ADR-0149 §3's join fails soft: a conversation is destroyed when the episode ends, so a game
   * with no room draws **no door** rather than a dead one.
   */
  it('draws no door where there is no room left to open', async () => {
    await openFromNow({ plans: [WHOLE], room: false });

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.queryByText(OPEN_THE_CHAT)).toBeNull();
  });

  /**
   * *We played* is available in **every** entry arm, not only the two that lead with it: entry is
   * gated on the entry window and nothing else, so four people can arrange a game at six and play
   * it at eight without filling a slot.
   */
  it('takes a score on the Planning arm, with nothing agreed at all', async () => {
    await openFromNow();

    fireEvent.press(await screen.findByText(WE_PLAYED));

    expect(screen.getByText('Send this score')).toBeTruthy();
  });
});

describe('the two landings inside one standing', () => {
  /**
   * §5.2: *Planning* and *Game on* arrive at **the Planning arm**, *Today* and *Needs result* at
   * **the score grid** — and *the verb names what you arrive at*, so the card's door and the
   * screen's landing are one fact rather than two tables.
   */
  it('leads with the plan where the moment is still ahead, and keeps the grid a press away', async () => {
    await openFromNow({ plans: [WHOLE] });

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.queryByText('Send this score')).toBeNull();

    fireEvent.press(screen.getByText(WE_PLAYED));

    expect(screen.getByText('Send this score')).toBeTruthy();
  });

  /** The grid **is** the screen once the agreed point has passed, so nothing opens it and it never closes. */
  it('leads with the score once the agreed point has passed', async () => {
    await openFromNow({
      plans: [
        plan({
          place: 'Zabłocie Sport',
          day: '2026-09-12',
          hour: '08:00',
          agreed_point: '2026-09-12T06:00:00Z',
        }),
      ],
    });

    expect(await screen.findByText('Send this score')).toBeTruthy();
    expect(screen.queryByText(WE_PLAYED)).toBeNull();
  });

  /** The agreed **day** is today, so the moment is here even with an hour still to agree. */
  it('leads with the score on the agreed day', async () => {
    await openFromNow({
      plans: [plan({ day: '2026-09-12', agreed_point: '2026-09-12T22:00:00Z' })],
    });

    expect(await screen.findByText('Send this score')).toBeTruthy();
    expect(screen.queryByText(WE_PLAYED)).toBeNull();
  });
});

describe('the checklist, on the score lead', () => {
  /**
   * Three lines, capped, in one order — what is true now, what is still to agree, what it moves.
   * The third is **cited, not written**: `worthLine`'s built and tested sentence. Drawn on the
   * two rungs that lead with the score; on the plan lead the card and the counter carry it (#414).
   */
  it('is three lines in one order, the third of them cited', async () => {
    await openFromNow({ plans: [PASSED] });

    expect(
      (
        await screen.findByLabelText(
          `${EVERYBODY_SAID_YES} ${NOTHING_IS_LEFT_TO_AGREE} ${WORTH_COUNTED}`,
        )
      ).props.accessibilityLabel,
    ).toContain(WORTH_COUNTED);
  });

  /** A `GameKind` this build cannot read drops the clause and the other two lines stand. */
  it('drops its third line rather than writing one when the kind is unreadable', async () => {
    await openFromNow({ games: [game({ kind: 'SOMETHING_NEW' as never })], plans: [PASSED] });

    expect(await screen.findByText(EVERYBODY_SAID_YES)).toBeTruthy();
    expect(screen.queryByText(WORTH_COUNTED)).toBeNull();
  });
});

describe('one component, two routes', () => {
  /**
   * ADR-0149 §5's shape: each address lights its own column and *back* is correct by construction,
   * with **no `from` parameter** — so the same arm is drawn through both doors.
   */
  it('draws the same arm through the room’s Details door', async () => {
    await openFromTheRoom({ plans: [WHOLE] });

    expect(await screen.findByText(PLAN_PANEL.title)).toBeTruthy();
    expect(screen.getByLabelText(`${SLOT_NAME.day}: Saturday`)).toBeTruthy();
    expect(
      screen.getByText(counterLabel({ gameId: GAME, place: 'x', day: 'd', hour: 'h' })),
    ).toBeTruthy();
  });

  /**
   * Each address lights its **own** column, which is what a `from` parameter would have cost:
   * `tabForPathname` reads the first segment and stays pure, so `games/…` is Now's and
   * `chats/…` is Chats'.
   */
  it('lights the column its own address is under', async () => {
    const lit = () =>
      screen
        .getAllByRole('tab')
        .filter((tab) => tab.props.accessibilityState?.selected === true)
        .map((tab) => tab.props.accessibilityLabel);

    await openFromTheRoom({ plans: [WHOLE] });
    expect(lit()).toEqual(['Chats']);

    fireEvent.press(screen.getByLabelText(/^Now/));
    await waitFor(() => expect(screen).toHavePathname('/'));

    fireEvent.press(await screen.findByLabelText(doorLabel('game-on')!));
    await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
    expect(lit()).toEqual(['Now']);
  });

  /** *Details* lands on the arm the standing derives, and an ended game's arm has no plan on it. */
  it('lands on the arm the standing derives', async () => {
    await openFromTheRoom({
      games: [game({ standing: 'UNSCORED', played_at: READ_AT, entry_closes_at: null })],
      plans: [WHOLE],
    });

    expect(await screen.findByText('Nobody agreed a score.')).toBeTruthy();
    expect(screen.queryByText(PLAN_PANEL.title)).toBeNull();
  });
});

describe('the eight corrections, re-decided by the design, and the two refusals', () => {
  /**
   * §5.4, each one a record read out — and three of them re-decided by #410's design, which wins:
   * **a lock word is drawn** (greyed, the chat's own control), **a date is drawn** (on the card at
   * the top, beside the weekday), and the slots are `Chip`s. What still stands: no part of day, no
   * *set all three first*, no duration the build does not hold, and a `GameKind` rather than a
   * search's mode — `Counted`, never `Competitive`.
   */
  it('draws what the design won, and none of what the records still refuse', async () => {
    await openFromNow({ plans: [WHOLE] });

    await screen.findByText(PLAN_PANEL.title);

    expect(screen.getByText(LOCK_THE_PLAN)).toBeTruthy();
    expect(screen.queryByText(/set all three/i)).toBeNull();
    expect(screen.getByText('19 Sep')).toBeTruthy();
    expect(screen.queryByText(/morning|afternoon|evening/i)).toBeNull();
    // *60 min* is a duration nothing in this build holds — no booking, no court, no slot length.
    expect(screen.queryByText(/\d+\s*min\b/i)).toBeNull();
    expect(screen.queryByText(/competitive/i)).toBeNull();
  });

  /**
   * §5.5, **reversed by ADR-0161**: the plan lead draws the court's pairing — the forecast block
   * and the player rows — from a read of its own beside the game. The score lead still does not:
   * the grid is the screen there, and the pairing is read on the plan lead's `court` slot and
   * nowhere else. The blocks' own anatomy is `forecastBlock.test.tsx`'s and `playersCard.test.tsx`'s;
   * what is asserted here is which lead draws them.
   */
  it('draws the forecast and the player rows on the plan lead, and not on the score lead', async () => {
    await openFromNow({ plans: [WHOLE] });

    expect(await screen.findByText(BALANCE_FORECAST)).toBeTruthy();
    expect(screen.getByText(PLAYERS)).toBeTruthy();
    expect(screen.getByText('90%')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: recordLabel({ nickname: 'tomek.p', yours: false }) }),
    ).toBeTruthy();
  });

  it('draws no forecast and no player rows on the score lead', async () => {
    await openFromNow({ plans: [PASSED] });

    await screen.findByText(PLAN_PANEL.title);

    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText(PLAYERS)).toBeNull();
    expect(screen.queryByText(/%/)).toBeNull();
    expect(transport.requestsTo('GET', pairingPath(GAME))).toHaveLength(0);
  });
});
