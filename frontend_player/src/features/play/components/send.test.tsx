/**
 * **The send**, walked the way a player walks it: search, ⚡, the court once full, `SH.propose`,
 * and the one act in this product that reaches another person. Real route tree, real shell,
 * real stores, only `fetch` faked.
 *
 * It sits beside `builder.test.tsx` because the court is the only honest harness for it — the
 * pinned CTA is *"the screen's own 10.1 slot, **calling** a challenges use-case"* — while every
 * claim under test belongs to `features/challenges/`, whose words it imports through that
 * feature's public surface
 * ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md) §8).
 *
 * What is asserted is the set of claims a build session could quietly undo, and three of them
 * are about a request that must **not** happen:
 *
 * - **Pending, not optimistic.** The stack is replaced on success only, so nothing is rolled
 *   forward and a refusal leaves the player exactly where they can act.
 * - **A duplicate submission is made rather than swallowed**, and carries no
 *   `Idempotency-Key`: the pair rule is the mechanism, and a key beside it would be a second
 *   one — the one that expires.
 * - **A refusal is followed by a re-read and never by a payload** — the origin search for the
 *   four gates, the player's own challenges for the pair — and **never by a re-run**.
 * - **When the re-read marks nobody the court says so**, rather than leaving somebody refused
 *   in front of four seats that all look fine.
 * - **`SH.propose` names no duration.** §14's obligation was discharged by deletion.
 * - **Offline the control closes and the screen says to wait.** The send is the one act that
 *   does not queue, so there is nothing to fail and nothing deferred — see the test's own note,
 *   which records where this sits against the ticket's wording.
 */

import { AccessibilityInfo } from 'react-native';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import {
  A_PAIR_HERE_IS_ALREADY_PLAYING,
  CHALLENGE_SENT,
  LINE_UP_CHANGED,
  NOTHING_MARKED_AFTER_THE_REFRESH,
  PROPOSE_SHEET_TITLE,
  SENDING_LABEL,
  SEND_CHALLENGE_LABEL,
  challengeErrorMessage,
  openChallengeLine,
} from '@/features/challenges/types';
import { offlineMessage, type AppError } from '@/shared/errors';
import { queryClient } from '@/shared/lib/query-client';
import { courtSeatCount } from '@/shared/ui';
import { useToastQueue } from '@/shared/store/toast.store';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import {
  launchIntoClassicPlay,
  stubGate,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession, usePlaySession } from '../store/playSession.store';

import { courtEntryLabel } from './findAGamePresentation';
import { USE_MATCHMAKING_LABEL } from './builderPresentation';
import { WITHHELD_SEAT_LINE } from './courtPresentation';
import { engineFillStatus, poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';

const SEARCHES = '/api/v1/searches';
const LINEUPS = '/api/v1/lineups';
const FORECASTS = '/api/v1/forecasts';
const CHALLENGES = '/api/v1/challenges';

const SEARCH_ID = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const LINEUP_ID = 'a1b2c3d4-0000-4000-8000-00000000000f';
const ME = 'aaaaaaaa-0000-4000-8000-000000000000';
const B = 'bbbbbbbb-0000-4000-8000-000000000001';
const C = 'cccccccc-0000-4000-8000-000000000002';
const D = 'dddddddd-0000-4000-8000-000000000003';

const NAMES: Readonly<Record<string, string>> = { [B]: 'bea_k', [C]: 'cyryl', [D]: 'dorota_w' };

const POOL_RANKING = poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline;
const ENGINE_FILL = engineFillStatus({ playersInRange: undefined, seats: 4 }).headline;

function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
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
      level: 2.8,
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

function envelope(
  searchId: string,
  over: Partial<Wire['SearchEnvelope']> = {},
): Wire['SearchEnvelope'] {
  return {
    search_id: searchId,
    at: '2026-08-31T18:00:00Z',
    surface: 'SHORTLIST',
    mode: 'FOR_FUN',
    ruleset_version: 'ruleset-v1',
    engine_version: 'matchfit-v1',
    optimised_for: 'SEARCHER',
    index_stale: false,
    pool: {
      sport: 'PADEL',
      radius_km_used: 12,
      players_in_range: 7,
      window: 'THIS_WEEK',
      post_gate: true,
    },
    radius_clamp: false,
    sorts_available: ['BEST_FIT'],
    rung_offers: null,
    ...over,
  };
}

const shortlist = (): Wire['ShortlistResponse'] => ({
  search: envelope(SEARCH_ID),
  candidates: [card(B), card(C), card(D)],
});

/** One way round, with a figure no arithmetic over these fixtures could produce. */
const ONE_WAY: Wire['ArrangementSchema'] = {
  pairing_id: 1,
  is_current: true,
  is_evenest: true,
  sides: {
    A: [
      { seat_index: 0, relationship: 'SELF', player_id: ME },
      { seat_index: 1, relationship: 'PARTNER', player_id: B },
    ],
    B: [
      { seat_index: 2, relationship: 'OPPONENT', player_id: C },
      { seat_index: 3, relationship: 'OPPONENT', player_id: D },
    ],
  },
  forecast: { pct: 78, sigma_group: 0.41, provisional: false, assumption: null },
  split: { your_side: 3.2, their_side: 3.42, gap: -0.22 },
};

/** ⚡'s answer with every seat taken — the court a send goes out from. */
const seatedFour = (): Wire['LineupResponse'] => ({
  search: envelope(LINEUP_ID, { surface: 'LINEUP' }),
  candidates: [card(B), card(C), card(D)],
  lineup: {
    seats: [
      { side: 'A', seat_index: 0, relationship: 'SELF', player_id: ME },
      { side: 'A', seat_index: 1, relationship: 'PARTNER', player_id: B },
      { side: 'B', seat_index: 2, relationship: 'OPPONENT', player_id: C },
      { side: 'B', seat_index: 3, relationship: 'OPPONENT', player_id: D },
    ],
    arrangements: [ONE_WAY],
    group_reason: 'EVENEST_ARRANGEMENT',
  },
});

/**
 * The origin, read back — **whoever the live gates still admit**.
 *
 * A withheld row keeps its place and carries no person, so a seat is marked by the set
 * difference against the rows that are left rather than by anything the row says.
 */
const readBack = (live: readonly Wire['CandidateSchema'][]): Wire['ShortlistResponse'] => ({
  search: envelope(LINEUP_ID, { surface: 'LINEUP' }),
  candidates: [...live],
});

/** One open challenge of the reader's own, holding one of the people on this court. */
const myChallengeWith = (playerId: string): Wire['ChallengeListResponse'] => ({
  read_at: '2026-08-31T10:00:00Z',
  challenges: [
    {
      challenge_id: '22222222-0000-4000-8000-000000000002',
      sport: 'TENNIS',
      organiser_id: ME,
      standing: 'AWAITING_ANSWERS',
      opened_at: '2026-08-31T09:00:00Z',
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED' },
        { side: 'B', player_id: playerId, answer_by: '2026-09-02T09:00:00Z' },
      ],
    },
  ],
});

let transport: Transport;
let announced: jest.SpyInstance;

/** What a listener was told, and with what politeness. */
const spoken = () => announced.mock.calls as [string, { queue: boolean }][];

/**
 * What is queued to be shown. Read off the store rather than off the screen, because a toast
 * is deliberately hidden from assistive technology — the host has already spoken it — and a
 * hidden element is not one a query finds.
 */
const toasts = () => useToastQueue.getState().queue;

/** The shape the two `code` tables read — the code, never the backend's own message. */
const refusalError = (code: string): AppError =>
  ({ recovery: 'business-conflict', kind: 'conflict', code }) as AppError;

beforeEach(() => {
  announced = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
  transport = installTransport();
  stubGate(transport, { id: ME, ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport);
  transport.on('POST', SEARCHES, () => json(shortlist()));
  transport.on('POST', LINEUPS, () => json(seatedFour()));
  transport.on('POST', FORECASTS, () =>
    json({
      arrangements: [ONE_WAY],
      engine_version: 'matchfit-v1',
      ruleset_version: 'ruleset-v1',
    } as Wire['ForecastResponse']),
  );
  transport.on('POST', CHALLENGES, () =>
    json<Wire['SentChallengeResponse']>(
      { challenge_id: '11111111-0000-4000-8000-000000000001' },
      201,
    ),
  );
});

afterEach(async () => {
  announced.mockRestore();
  transport.restore();
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  // The queue is app-wide and its hold is a timer these tests never let run.
  useToastQueue.getState().clear();
  queryClient.clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Search, spend both floors, fill the seats, and arrive at a court with the send under it. */
async function openAFullCourt() {
  await launchIntoClassicPlay(transport);
  fireEvent.press(await screen.findByLabelText('Play'));
  await screen.findByLabelText('Tuesday 19:00');

  fireEvent.press(screen.getByLabelText(courtEntryLabel(courtSeatCount('padel'))));
  await screen.findByText(POOL_RANKING);
  act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));
  await waitFor(() => expect(screen).toHavePathname('/play/builder'));

  fireEvent.press(await screen.findByLabelText(USE_MATCHMAKING_LABEL));
  await screen.findByText(ENGINE_FILL);
  act(() =>
    jest.advanceTimersByTime(searchingFloorMs({ kind: 'fill', seats: 4, collapsed: false })),
  );
  await waitFor(() => expect(screen.queryByText(ENGINE_FILL)).toBeNull());

  await screen.findByLabelText(SEND_CHALLENGE_LABEL);
}

/**
 * Open `SH.propose` and confirm it — the two presses one send actually is.
 *
 * The same label answers both, and that is the design: the act is named once, and the sheet is
 * plainly a confirmation *of that*. The court is hidden behind the sheet while it is up, so the
 * second press can only reach the sheet's own control.
 */
async function pressSend() {
  fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));
  await screen.findByText(PROPOSE_SHEET_TITLE);
  fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));
}

/** The one request under test, as the route received it. */
const sent = () => transport.requestsTo('POST', CHALLENGES);

describe('the pre-send sheet', () => {
  /**
   * §14's `{window}` obligation, discharged by **deletion**: a pre-send sentence naming a
   * duration must name the number the backend will derive, and no route gives one before the
   * first send. The real deadline is per seat and arrives immediately after the act.
   */
  it('states the irreversibility and names no duration', async () => {
    await openAFullCourt();

    fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));

    await screen.findByText(PROPOSE_SHEET_TITLE);
    expect(screen.getByText('Nobody is contacted until you send it.')).toBeTruthy();
    expect(screen.queryByText(/\b24\s?h\b|\bhours?\b|\ba day\b/i)).toBeNull();
  });

  /** §15: the whole handle, or nobody — one per line, and never joined into a phrase. */
  it('names everybody it is about to ask', async () => {
    await openAFullCourt();

    fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));

    await screen.findByText(PROPOSE_SHEET_TITLE);
    expect(screen.getByText('bea_k')).toBeTruthy();
    expect(screen.getByText('cyryl')).toBeTruthy();
    expect(screen.getByText('dorota_w')).toBeTruthy();
  });

  /** Nobody is contacted until you send it, and dismissal is always the non-committal option. */
  it('sends nothing until it is confirmed', async () => {
    await openAFullCourt();

    fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));

    await screen.findByText(PROPOSE_SHEET_TITLE);
    expect(sent()).toHaveLength(0);
  });
});

describe('the send', () => {
  /**
   * **The arrangement you built is what is recorded** — every A seat then every B, your own
   * seat among them, under the search that seated the four rather than the one arrived on.
   */
  it('carries the court exactly as it is drawn, under the search that seated it', async () => {
    await openAFullCourt();

    await pressSend();

    await waitFor(() => expect(sent()).toHaveLength(1));
    expect(sent()[0]?.body).toEqual({
      search_id: LINEUP_ID,
      court: [
        { side: 'A', player_id: ME },
        { side: 'A', player_id: B },
        { side: 'B', player_id: C },
        { side: 'B', player_id: D },
      ],
    });
  });

  /**
   * **Pending, not optimistic.** Success replaces the whole stack and ends the Play session, so
   * there is nothing rolled forward — which is the same fact that leaves a refusal somewhere to
   * be refused *to*.
   */
  it('replaces the stack on success, and the Play session goes with it', async () => {
    await openAFullCourt();

    await pressSend();

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(usePlaySession.getState().lineup).toBeUndefined();
  });

  /**
   * The destination is a placeholder, so the toast is the **entire** confirmation that the one
   * irreversible act in the feature succeeded — and the single announcement that interrupts.
   */
  it('confirms with a toast, and it is the one announcement that does not queue', async () => {
    await openAFullCourt();

    await pressSend();

    await waitFor(() => expect(toasts().map((toast) => toast.message)).toEqual([CHALLENGE_SENT]));
    // **The politeness is the message's and the speaking is the host's** (`toast.store.ts`), so
    // this is where the exception is checkable: `ToastHost` is mounted once at the app root and
    // is not in this harness's tree, and `Toast.test.tsx` is what holds it to `queue: false`.
    expect(toasts()[0]?.politeness).toBe('interrupting');
    // Nothing else spoke over it on the way: the send is the last thing the tab does.
    expect(spoken().map(([message]) => message)).not.toContain(CHALLENGE_SENT);
  });

  /**
   * **Pending, and nothing rolled forward.** While the reply is outstanding the CTA says so and
   * the player is still standing on their court: the stack is replaced on success only, which
   * is what leaves a refusal somewhere to land.
   */
  it('says so on the pinned control, and moves nobody until the reply arrives', async () => {
    await openAFullCourt();
    let answer = (_response: Response) => {};
    transport.on('POST', CHALLENGES, () => new Promise<Response>((resolve) => (answer = resolve)));

    await pressSend();

    expect(await screen.findByLabelText(SENDING_LABEL)).toBeTruthy();
    expect(screen).toHavePathname('/play/builder');
    expect(usePlaySession.getState().lineup?.seats).toEqual([B, C, D]);

    await act(async () => {
      answer(
        json<Wire['SentChallengeResponse']>(
          { challenge_id: '11111111-0000-4000-8000-000000000001' },
          201,
        ),
      );
    });
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  /**
   * **A duplicate submission is explicitly-valid repetition on the pair rule**: the second send
   * is made, read and refused by the same check that would refuse a stranger's. A key expires
   * and the rule does not, so a key beside it would be the weaker of two mechanisms for one
   * fact.
   */
  it('makes a second send rather than swallowing it, and the rule is what refuses one', async () => {
    await openAFullCourt();
    transport.on('POST', CHALLENGES, () => errorResponse(409, 'open_challenge_stands'));
    transport.on('GET', CHALLENGES, () => json(myChallengeWith(C)));

    await pressSend();
    await screen.findByText(openChallengeLine('cyryl'));
    await pressSend();

    await waitFor(() => expect(sent()).toHaveLength(2));
    expect(sent()[0]?.body).toEqual(sent()[1]?.body);
  });

  it('sends no idempotency key, so a repeat is refused by the rule rather than swallowed', async () => {
    await openAFullCourt();

    await pressSend();

    await waitFor(() => expect(sent()).toHaveLength(1));
    const names = Object.keys(sent()[0]?.headers ?? {}).map((header) => header.toLowerCase());
    expect(names).not.toContain('idempotency-key');
  });
});

describe('a refused send', () => {
  const refuse = (code: string, status = 409) =>
    transport.on('POST', CHALLENGES, () => errorResponse(status, code));

  /**
   * The remedy **reads the origin back** and never re-runs the search: a re-run mints an id the
   * whole line-up must adopt, and its untouched seats are only *probably* in the new answer.
   */
  it('re-reads the origin search and marks the seats its withheld rows identify', async () => {
    await openAFullCourt();
    const searchesBefore = transport.requestsTo('POST', SEARCHES).length;
    refuse('line_up_no_longer_sendable');
    transport.on('GET', `${SEARCHES}/${LINEUP_ID}`, () => json(readBack([card(B), card(C)])));

    await pressSend();

    expect(await screen.findByText(LINE_UP_CHANGED)).toBeTruthy();
    // Hidden from a listener, because the seat's own name already carries it (§20.1).
    await waitFor(() =>
      expect(screen.getByText(WITHHELD_SEAT_LINE, { includeHiddenElements: true })).toBeTruthy(),
    );
    expect(transport.requestsTo('GET', `${SEARCHES}/${LINEUP_ID}`)).toHaveLength(1);
    // The one request that must not happen.
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(searchesBefore);
  });

  /** Refused, refreshed, and every seat looks fine is a dead end — so it gets a sentence. */
  it('states it at court level when the re-read marks nobody', async () => {
    await openAFullCourt();
    refuse('line_up_no_longer_sendable');
    transport.on('GET', `${SEARCHES}/${LINEUP_ID}`, () =>
      json(readBack([card(B), card(C), card(D)])),
    );

    await pressSend();

    expect(await screen.findByText(NOTHING_MARKED_AFTER_THE_REFRESH)).toBeTruthy();
    expect(screen.queryByText(WITHHELD_SEAT_LINE, { includeHiddenElements: true })).toBeNull();
  });

  /**
   * The refusal names nobody. The **name** comes from the player's own challenges, which were
   * always theirs to read — #222 puts this gate on the embarrassment side, not the safety side.
   */
  it('re-reads the player’s own challenges for the name the refusal would not carry', async () => {
    await openAFullCourt();
    refuse('open_challenge_stands');
    transport.on('GET', CHALLENGES, () => json(myChallengeWith(C)));
    // The shell reads this list too, for the tab bar's badge, so what is asserted is the read
    // **this refusal** adds rather than the total — one request, and never one per seat.
    const before = transport.requestsTo('GET', CHALLENGES).length;

    await pressSend();

    expect(await screen.findByText(openChallengeLine('cyryl'))).toBeTruthy();
    expect(transport.requestsTo('GET', CHALLENGES).length - before).toBe(1);
  });

  /** The pair can be between two invitees, and that game is not this player's to read. */
  it('names nobody when the game in the way is not one of the organiser’s', async () => {
    await openAFullCourt();
    refuse('open_challenge_stands');
    transport.on('GET', CHALLENGES, () =>
      json<Wire['ChallengeListResponse']>({ read_at: '2026-08-31T10:00:00Z', challenges: [] }),
    );

    await pressSend();

    expect(await screen.findByText(A_PAIR_HERE_IS_ALREADY_PLAYING)).toBeTruthy();
  });

  /** Nothing is rolled forward, so a refusal leaves the player on the court they can act on. */
  it('leaves the stack alone, and the line-up on it', async () => {
    await openAFullCourt();
    refuse('line_up_no_longer_sendable');
    transport.on('GET', `${SEARCHES}/${LINEUP_ID}`, () =>
      json(readBack([card(B), card(C), card(D)])),
    );

    await pressSend();

    await screen.findByText(NOTHING_MARKED_AFTER_THE_REFRESH);
    expect(screen).toHavePathname('/play/builder');
    expect(usePlaySession.getState().lineup?.seats).toEqual([B, C, D]);
  });

  /**
   * A `409` that is neither refusal reads **nothing**. Branching on the status would send an
   * orphaned origin off to re-read a search that is gone, which answers the question with
   * itself.
   */
  it('reads nothing for a refusal that is about neither the gates nor the pair', async () => {
    await openAFullCourt();
    refuse('court_origin_not_found');
    const before = transport.requestsTo('GET', CHALLENGES).length;

    await pressSend();

    expect(
      await screen.findByText(challengeErrorMessage(refusalError('court_origin_not_found'))),
    ).toBeTruthy();
    expect(transport.requestsTo('GET', `${SEARCHES}/${LINEUP_ID}`)).toHaveLength(0);
    // Again a delta: the badge's own read is the shell's and is not this screen's to suppress.
    expect(transport.requestsTo('GET', CHALLENGES).length).toBe(before);
  });
});

describe('with no connection', () => {
  /**
   * The send is the one act in this app that does not queue: its answer window is derived **at
   * send**, so a tap deferred to the next reconnect would carry a deadline nobody chose. The
   * control closes and the sentence says to wait — Part 11's *button disabling is UX*, riding
   * on top of the `networkMode: 'always'` override that is the mechanism
   * (`features/challenges/hooks/challengeMutationOptions.ts`, and its own test holds that
   * half).
   *
   * **Where this sits against the ticket.** #274's acceptance criterion reads *"a send with no
   * connection waits rather than fails"*, and taken as a statement about the **mechanism** it
   * contradicts four settled records — [#239](https://github.com/Raketa02/Raketa/issues/239) §6,
   * `the-play-screens.md` §11.8, `offlineMessage`'s `does-not-resume` value, which exists for
   * this act alone, and the override itself. What is built is the reading that agrees with all
   * four: nothing is deferred, nothing fails, and the player is told to wait. A decision to flip
   * the mechanism to pausing would be an amendment to those records, not a build detail.
   */
  it('closes the control and says to wait, so nothing is sent and nothing is queued', async () => {
    await openAFullCourt();

    act(() => onlineManager.setOnline(false));

    expect(await screen.findByText(offlineMessage('does-not-resume'))).toBeTruthy();
    fireEvent.press(screen.getByLabelText(SEND_CHALLENGE_LABEL));
    expect(screen.queryByText(PROPOSE_SHEET_TITLE)).toBeNull();
    expect(sent()).toHaveLength(0);
  });
});
