/**
 * **Players** — the deck, walked the way a player walks it: the real route tree, the real
 * shell, the real stores and only `fetch` faked.
 *
 * What is asserted here is the set of decisions a build session could quietly undo, most of
 * them [ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)'s:
 *
 * - **A drag is an answer, and the three buttons remain the path.** Past the threshold the
 *   card flies in the drag's direction; short of it, it settles. The stamps track the finger,
 *   the motor ticks once at the threshold, and under reduced motion the answer still lands.
 * - **The counter is true and the chip names nobody.** `remaining + unanswered` and
 *   `cap − outstanding`, counting down per answer; the chip reads the envelope, is absent at
 *   nought, and drops on a liker's mutual.
 * - **The next hand is asked for at two and appended**, so the stack never runs dry while the
 *   pool says there are people.
 * - **At the ceiling a stranger's card settles with a toast; a liker's card flies.**
 * - **Two endings, and only one offers the reset.** *Show them again* clears and deals afresh;
 *   *Nobody in range* keeps its advice and has no reset.
 * - **The pass toast and the one-sided yes toast are gone**; every answer is spoken; the one
 *   toast left is a mutual naming no chat, and a mutual naming a challenge is the yes screen.
 * - **Nobody is asked to declare on Players**, and the deck is the second tab, at `/players`.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { AccessibilityInfo } from 'react-native';

import { onlineManager } from '@tanstack/react-query';

import { LATER, MATCHED_WORD, matchedAnnouncement } from '@/features/challenges/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { RECORD_TITLE, fitRowLabel, recordCloseLabel } from '@/features/player_record/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  CHALLENGES_PATH,
  CONVERSATIONS_PATH,
  GATE_USER,
  launchSignedIn,
  resetHaptics,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubHaptics,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeHaptics, type FakeHaptics } from '@/test-support/platform';
import { dragTo, release, swipe } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { searchKeys } from '../hooks/searchKeys';
import type { MyInterest } from '../mappers/interestMappers';
import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession } from '../store/playSession.store';

import { declarationLine, declarationTitle, modeControlLabel } from './findAGamePresentation';
import {
  NOBODY_IN_RANGE_TITLE,
  PANE_LABEL,
  SEEN_EVERYBODY_TITLE,
  SHOW_THEM_AGAIN_LABEL,
  TRY_THE_RADAR_LABEL,
  WIDEN_IN_YOU,
  deckCounter,
  interestAnnouncement,
  mutualToast,
  passedAnnouncement,
  seenEverybodyLine,
  wantToPlayYouChip,
} from './deckPresentation';
import { deckMetaLine } from './deckCardPresentation';
import { SPORT_HEADING } from './SportChips';
import { CAP_REACHED_SENTENCE, playErrorMessage } from './playErrorMessage';
import { promptControls, promptCopy } from './promptPresentation';
import { BACK_TO_YOU_LABEL } from './radarPresentation';
import { poolDescription } from './searchPresentation';

const DECK = '/api/v1/deck';
const RADAR = '/api/v1/radar';
const RESET = '/api/v1/deck/reset';
const TENNIS_INTENT = '/api/v1/play-intents/TENNIS';
const INTEREST = '/api/v1/interest';
const PASSES = '/api/v1/passes';
const DECLINES = '/api/v1/prompt-declines';
const RADIUS = '/api/v1/players/me/search-radius';
const PLAYERS = '/api/v1/players';

const SEARCH_ID = 'd0d1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';

const { commit } = theme.size.deckSwipe;

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

/** The square both people are in, so the meta line's one licensed clause has a pairing. */
const HERE = 'A+050612+0019938';

/** One dealt card. Enough terms that the sheet has rows and the tiles have figures. */
function card(
  name: string,
  playerId: string,
  over: Partial<Wire['CandidateSchema']> = {},
): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    // One decimal, spot to spot (ADR-0174 §2) — the evidence's `km` below stays the engine's
    // whole input, and the card prints this one.
    distance_km: 1.9,
    player_card: {
      name,
      area_code: HERE,
      social_tags: ['PLAYS_TO_WIN'],
      level: 2.83,
      band: 'Established',
      range: { low: 2.55, high: 2.87 },
    },
    concerns: [],
    terms: [
      {
        term: 'LEVEL_FIT',
        weight: 30,
        value: 0.8,
        contribution: 24,
        evidence: {
          kind: 'level_fit',
          my_mu: 2.71,
          their_mu: 2.83,
          delta: 0.12,
          direction: 'ABOVE',
        },
      },
      {
        term: 'DISTANCE',
        weight: 20,
        value: 0.7,
        contribution: 14,
        evidence: {
          kind: 'distance',
          km: 4,
          area_code: HERE,
          outside_their_radius: false,
        },
      },
      {
        term: 'PREDICTED_BALANCE',
        weight: 40,
        value: 1,
        contribution: 40,
        evidence: {
          kind: 'predicted_balance',
          pct: 72,
          my_sigma: 0.2,
          their_sigma: 0.2,
          confidence: 60,
        },
      },
    ],
    degraded_terms: [
      { term: 'RELIABILITY', reason: 'NOT_YET_ON_THIS_PLATFORM' },
      { term: 'SOCIAL_VIBE', reason: 'NOTHING_FROM_THEM' },
    ],
    modifiers: [{ code: 'CALIBRATION_VALUE', points: 3 }],
    liveness_reasons: ['RECENT_ACTIVITY'],
    ...over,
  };
}

interface DealtOver {
  readonly candidates?: readonly Wire['CandidateSchema'][];
  readonly playersInRange?: number;
  readonly radiusClamp?: boolean;
  readonly searchId?: string;
  /**
   * The searcher's own area, as the search ran on it. Defaulted to the dealt card's own,
   * because that is the pairing the one licensed sentence is *about*.
   *
   * **`null` is the record's absence and the wire's is omission** — the two spellings of the
   * one fact, not two facts. A search recorded before the backend kept an area has a null
   * column, and the response leaves `my_area_code` out rather than sending it empty; passing
   * `null` here asks this fixture for that response.
   */
  readonly myAreaCode?: string | null;
  /** The questions this deal raises. Empty on every fixture that is not about them. */
  readonly prompts?: readonly Wire['PromptSchema'][];
  /** The pool beyond this hand. Nought unless a walk is about the counter or the next hand. */
  readonly remaining?: number;
  /** The people waiting. Nought unless a walk is about the chip. */
  readonly wantToPlayYou?: number;
}

function deal({
  candidates = [card('Marek Z.', 'aaaaaaaa-0000-4000-8000-000000000001')],
  playersInRange = 7,
  radiusClamp = false,
  searchId = SEARCH_ID,
  myAreaCode = HERE,
  prompts = [],
  remaining = 0,
  wantToPlayYou = 0,
}: DealtOver = {}): Wire['ShortlistResponse'] {
  return {
    search: {
      search_id: searchId,
      at: '2026-09-01T18:00:00Z',
      surface: 'DECK',
      // Null exactly on the deck, which has no mode.
      mode: null,
      ruleset_version: 'ruleset-v1',
      engine_version: 'matchfit-v1',
      optimised_for: 'SEARCHER',
      index_stale: false,
      pool: {
        sport: 'PADEL',
        radius_km_used: 12,
        players_in_range: playersInRange,
        window: 'THIS_WEEK',
        post_gate: true,
        remaining,
        want_to_play_you: wantToPlayYou,
      },
      radius_clamp: radiusClamp,
      sorts_available: [],
      rung_offers: null,
      ...(myAreaCode === null ? {} : { my_area_code: myAreaCode }),
      prompts: [...prompts],
    },
    candidates: [...candidates],
  };
}

function expressed(
  mutual: boolean,
  outstanding = 3,
  challengeId: string | null = null,
): Wire['ExpressedInterestResponse'] {
  return {
    interest: {
      player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
      sport: 'PADEL',
      at: '2026-09-01T18:00:00Z',
      expires_at: '2026-09-08T18:00:00Z',
    },
    mutual,
    challenge_id: challengeId,
    outstanding: { sport: 'PADEL', outstanding, cap: 20, ttl_days: 21 },
  };
}

/** Where padel stands: `outstanding` of a cap of 20, and a yes lives 21 days. */
function standing(outstanding: number, cap = 20): Wire['InterestListResponse'] {
  return {
    outgoing: [],
    mutual: [],
    outstanding: [{ sport: 'PADEL', outstanding, cap, ttl_days: 21 }],
  };
}

const ME = GATE_USER.id;
const MAREK = 'aaaaaaaa-0000-4000-8000-000000000001';
const ANA = 'aaaaaaaa-0000-4000-8000-000000000002';
const OLA = 'aaaaaaaa-0000-4000-8000-000000000003';
const TOMEK = 'aaaaaaaa-0000-4000-8000-000000000004';
const CHALLENGE = 'cccccccc-0000-4000-8000-00000000000c';
const ROOM = 'cccccccc-0000-4000-8000-000000000007';
const GAME = 'cccccccc-0000-4000-8000-000000000009';
const READ_AT = '2026-09-01T18:00:00Z';

const YES_SCREEN = `/chats/challenge/${CHALLENGE}/yes`;
const THE_ROOM = `/chats/conversation/${ROOM}`;

/**
 * **The challenge the mutual named**, as `GET /challenges/{id}` answers when the yes screen asks
 * for it — the deck never held it. In tennis the two of them face each other and the court is
 * `ON` from birth; in padel they are partners on one side with the other still to fill
 * (ADR-0154 §2). Neither seat carries a card: a mutual-born court is drawn on posters here.
 */
function matched(sport: 'TENNIS' | 'PADEL'): Wire['ChallengeDetailResponse'] {
  const marek = { player_id: MAREK, answer: 'ACCEPTED' as const, name: 'Marek Z.' };
  const me = { player_id: ME, answer: 'ACCEPTED' as const, name: 'ada' };
  const nobody = { player_id: null, answer: null, answer_by: null, name: null };
  return {
    read_at: READ_AT,
    challenge_id: CHALLENGE,
    sport,
    mode: null,
    window: null,
    organiser_id: MAREK,
    standing: sport === 'TENNIS' ? 'ON' : 'LINE_UP_INCOMPLETE',
    opened_at: READ_AT,
    seats:
      sport === 'TENNIS'
        ? [
            { side: 'A', ...marek },
            { side: 'B', ...me },
          ]
        : [
            { side: 'A', ...marek },
            { side: 'A', ...me },
            { side: 'B', ...nobody },
            { side: 'B', ...nobody },
          ],
  };
}

const MAREK_AND_ME = [
  { player_id: MAREK, name: 'Marek Z.' },
  { player_id: ME, name: 'ada' },
];

/** The room the mutual's challenge opened, listed and openable. */
function theRoomIsThere(sport: 'TENNIS' | 'PADEL', gameId: string | null) {
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: gameId,
      sport,
      members: MAREK_AND_ME,
      people: MAREK_AND_ME,
      last_entry: null,
    },
  ]);
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: gameId,
    sport,
    members: MAREK_AND_ME,
    people: MAREK_AND_ME,
    entries: [],
  });
  stubEntries(transport, ROOM);
}

/** Marek's record, as `GET /players/{id}/record` answers when the sheet asks for it. */
function mareksRecord(): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    name: 'Marek Z.',
    nickname: 'marek_z',
    area_code: HERE,
    social_tags: ['PLAYS_TO_WIN'],
    sports: [{ sport: 'PADEL', level: 2.83, band: 'Established' }],
    skill: {
      sport: 'PADEL',
      level: 2.83,
      band: 'Established',
      confidence: 40,
      counted_games: 3,
      likely_range: { low: 2.55, high: 2.87 },
      last_five: ['WIN', 'LOSS', 'WIN'],
    },
    reliability: {
      player_score: 88,
      strands: [{ strand: 'SHOWS_UP', good: 3, opportunities: 3, pct: 100 }],
    },
    variety: { distinct_opponents: 3, times_on_court: 3 },
  };
}

/** The spoken *Matched!* for the one card every walk says yes to. */
const MATCHED_SPOKEN = matchedAnnouncement({
  yours: [{ kind: 'person', playerId: ME, name: 'ada' }],
  theirs: [{ kind: 'person', playerId: MAREK, name: 'Marek Z.' }],
});

let transport: Transport;
let haptics: FakeHaptics;

/** What was said to a screen reader. Cleared per case, since RN's stub is one mock. */
let spoken: jest.SpyInstance<
  void,
  Parameters<typeof AccessibilityInfo.announceForAccessibilityWithOptions>
>;

beforeEach(() => {
  transport = installTransport();
  haptics = fakeHaptics();
  stubHaptics(haptics);
  spoken = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
  spoken.mockClear();
  stubGate(transport, {
    ratings: [rating('PADEL'), rating('TENNIS')],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport, standing(8));
  transport.on('POST', DECK, () => json(deal()));
  // The Radar pane reads its own surface; an empty reading is enough for the walks here, which
  // are about the toggle. The pane itself is `radar.test.tsx`'s.
  transport.on('POST', RADAR, () => json(deal({ candidates: [] })));
  transport.on('POST', INTEREST, () => json(expressed(false), 201));
  transport.on('POST', PASSES, () => noContent());
  transport.on('POST', RESET, () => noContent());
  transport.on('POST', DECLINES, () => noContent());
  transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 22 }));
  transport.on('GET', `${PLAYERS}/${MAREK}/record?sport=PADEL`, () => json(mareksRecord()));
});

afterEach(async () => {
  // The OS switch is set in one case below, and **set back rather than restored**: React
  // Native's `AccessibilityInfo` is already a Jest mock, so a spy over it cannot be restored.
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
  jest.restoreAllMocks();
  stopWatchingHardwareBack();
  resetHaptics();
  transport.restore();
  onlineManager.setOnline(true);
  queryClient.clear();
  useToastQueue.getState().clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player standing on the deck — the Players tab, one press from anywhere. */
async function openDeck() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Players'));
  await waitFor(() => expect(screen).toHavePathname('/players'));
}

/** Leave for Play and come back, which is how the deck is re-entered now that it is a tab. */
async function leaveAndReturn() {
  fireEvent.press(screen.getByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  await screen.findByLabelText('Tuesday evening');
  fireEvent.press(screen.getByLabelText('Players'));
  await waitFor(() => expect(screen).toHavePathname('/players'));
}

const dealBodies = () => transport.requestsTo('POST', DECK).map((request) => request.body);
const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);
const announced = () => spoken.mock.calls.map(([message]) => message);

/**
 * The card on screen — the one element, named by the person and then by their Fit. The *i*
 * button is named `{name}’s record`, so the name alone would find two elements.
 */
const cardOf = (name: string) => new RegExp(`^${name.replace(/\./g, '\\.')}\\. Fit `);
const MAREK_CARD = cardOf('Marek Z.');
const ANA_CARD = cardOf('Ana K.');
const marek = () => screen.getByLabelText(MAREK_CARD);

/** The stamps and the cards behind are hidden from a listener on purpose. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

const THREE_CARDS = deal({
  candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA), card('Ola W.', OLA)],
  remaining: 5,
});

describe('what the deck deals', () => {
  it('deals on arrival, for the sport the player is on, and draws one person', async () => {
    await openDeck();

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * **The one sentence a card may write from an `area_code`, end to end**
   * ([#279](https://github.com/Raketa02/Raketa/issues/279)) — and, since ADR-0169 §7, the
   * liveness code's own words after it. Both codes come off one response, so this asserts the
   * whole path: the wire, the mapper that folds the searcher's own on, and the line.
   */
  it('says a candidate is in your area and around this week when the codes say so', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    const line = deckMetaLine({
      km: 1.9,
      theirAreaCode: HERE,
      myAreaCode: HERE,
      aroundThisWeek: true,
    });

    expect(line).toBe('In your area · 1,9 km · around this week');
    expect(screen.getByText(line ?? '')).toBeTruthy();
  });

  /** A search recorded before the area was kept drops the clause and keeps its kilometres. */
  it('keeps the kilometres and claims no area where the search recorded none', async () => {
    transport.on('POST', DECK, () => json(deal({ myAreaCode: null })));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(deckMetaLine({ km: 1.9, theirAreaCode: HERE, aroundThisWeek: true })).toBe(
      '1,9 km · around this week',
    );
    expect(screen.getByText('1,9 km · around this week')).toBeTruthy();
  });

  /**
   * **The deal runs on the profile's week, whatever was improvised on Find a game** (ADR-0169
   * §1). The ask carries no override at all — *"omit it, never send `null`"*.
   */
  it('deals on the profile’s week, whatever was improvised on Find a game', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText('Monday morning'));

    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    await screen.findByLabelText(MAREK_CARD);

    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  it('deals again for a sport the player switches to, and only then', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(dealBodies()[1]).toEqual({ sport: 'TENNIS' });
  });

  /**
   * **A deal is not free, so the screen asks for one once per question and then keeps it.**
   *
   * `POST /deck` excludes everybody already dealt to this player for a day, so a second ask is
   * a *different* ten people — which is what makes the next hand work and what made a re-ask
   * on every chip press ruinous.
   */
  it('deals once per sport, however often the chips are toggled', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    fireEvent.press(screen.getByLabelText('Padel'));
    await screen.findByLabelText(MAREK_CARD);
    fireEvent.press(screen.getByLabelText('Tennis'));
    await screen.findByLabelText(MAREK_CARD);
    fireEvent.press(screen.getByLabelText('Padel'));
    await screen.findByLabelText(MAREK_CARD);

    expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]);
  });

  /** Leaving Players replaces the stack, so the screen is genuinely re-entered rather than restored. */
  it('finds the deal it already holds when the player leaves the tab and comes back', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    await leaveAndReturn();

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * The other half of holding the deal: **how far through it the player is is part of it.**
   * Progress left behind on the screen would put every answered card back on arrival.
   */
  it('does not put an answered card back when the screen is re-entered', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA)] })),
    );
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);

    await leaveAndReturn();

    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
    expect(screen.queryByLabelText(MAREK_CARD)).toBeNull();
    expect(dealBodies()).toHaveLength(1);
  });

  /**
   * **A declaration is not part of the question.** Every deal runs under one ruler (ADR-0169
   * §2): an undeclared sport deals, and nothing asks what kind of game.
   */
  it('deals a sport nobody has declared in, and asks nothing first', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByLabelText('Tennis'));

    await waitFor(() => expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]));
    expect(screen.queryByText(declarationTitle('Tennis'))).toBeNull();
    expect(transport.requestsTo('PUT', TENNIS_INTENT)).toEqual([]);
  });

  it('says what a refusal means, and offers the act that failed as the retry', async () => {
    transport.on('POST', DECK, () => errorResponse(503, 'matchmaking_unavailable'));
    await openDeck();

    const said = await screen.findByText(
      playErrorMessage({ code: 'matchmaking_unavailable' } as never),
    );
    expect(said).toBeTruthy();

    // Nothing retried on its own: one refusal is one request until a player asks again.
    expect(dealBodies()).toHaveLength(1);

    transport.on('POST', DECK, () => json(deal()));
    fireEvent.press(screen.getByLabelText('Deal again'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));
  });

  /**
   * **A refusal is not a reason to deal on the next mount either**: `retryOnMount` defaults to
   * true, so an errored query re-fires the moment a second observer mounts — and here that is
   * the player walking to Find a game and back, having pressed nothing.
   */
  it('does not deal again when a tab whose deal was refused is re-entered', async () => {
    transport.on('POST', DECK, () => errorResponse(503, 'matchmaking_unavailable'));
    await openDeck();
    await screen.findByText(playErrorMessage({ code: 'matchmaking_unavailable' } as never));

    await leaveAndReturn();
    await screen.findByText(playErrorMessage({ code: 'matchmaking_unavailable' } as never));

    expect(dealBodies()).toHaveLength(1);
  });
});

describe('yes and no, by the buttons', () => {
  /**
   * **The three buttons remain and answer** — the test that pinned *no gesture dependency*
   * became this one (ADR-0169 §3): a screen reader consumes the drag, so the buttons are the
   * accessible path and are never removed. The drag is built on React Native's own responder,
   * which `test-support/swipe.ts` drives directly and no library is added for.
   */
  it('are three named buttons that remain beside the drag, and the card announces no gesture', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByRole('button', { name: 'Not today, Marek Z.' })).toBeTruthy();
    expect(screen.getByRole('button', { name: "Let's play, Marek Z." })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Marek Z.’s record' })).toBeTruthy();
    // A drag would have to be announced to a listener who cannot perform one; the buttons
    // are the path, so nothing announces a gesture.
    expect(screen.queryByLabelText(/swipe|drag/i)).toBeNull();
  });

  it('sends a yes with the deal it came off, and never a position', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(transport.requestsTo('POST', INTEREST)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: MAREK,
      search_id: SEARCH_ID,
    });
  });

  it('sends a pass the same way, and is told nothing back', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    await waitFor(() => expect(transport.requestsTo('POST', PASSES)).toHaveLength(1));
    expect(transport.requestsTo('POST', PASSES)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: MAREK,
      search_id: SEARCH_ID,
    });
  });

  /**
   * **The pass toast and the one-sided yes toast are gone** (ADR-0169 §3): the stamp and the
   * card leaving are the feedback. What survives of each is the spoken result, in the retired
   * toast's own words, so a listener who drags nothing and sees no stamp is still told.
   */
  it('speaks a pass, and shows no toast for it', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    await waitFor(() => expect(announced()).toEqual([passedAnnouncement('Marek Z.')]));
    expect(toasts()).toEqual([]);
  });

  it('speaks a one-sided yes off the reply, shows no toast, and stays on the deck', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(announced()).toEqual([interestAnnouncement('Marek Z.')]));
    expect(toasts()).toEqual([]);
    expect(screen).toHavePathname('/players');
  });

  /**
   * The one toast left. **A mutual naming nothing is today's toast, verbatim, and no screen**:
   * the pair already have a game being arranged, or a gate refused — one answer, two causes,
   * deliberately not told apart (ADR-0154 §3) — and a full-screen celebration must never
   * overstate what happened (ADR-0167 §1).
   */
  it('tells a mutual naming no chat to both sides, verbatim, and stays on the deck', async () => {
    transport.on('POST', INTEREST, () => json(expressed(true)));
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(toasts()).toEqual([mutualToast('Marek Z.')]));
    expect(screen).toHavePathname('/players');
  });

  it('moves to the next card once the one answered has left', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA)] })),
    );
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
    expect(screen.queryByLabelText(MAREK_CARD)).toBeNull();
  });

  /**
   * A refusal puts the card back, which is what keeps `retryTarget`'s rule true here: the
   * retry is the control the player already pressed, and it cannot be that control if the
   * person it was about is gone.
   */
  it('returns the card when the answer is refused, with the sentence above it', async () => {
    transport.on('POST', PASSES, () => errorResponse(409, 'origin_search_not_found'));
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    await screen.findByText(playErrorMessage({ code: 'origin_search_not_found' } as never));
    expect(screen.getByLabelText('Not today, Marek Z.')).toBeTruthy();
  });

  /** The server stays the authority: a `409` at the ceiling returns the card like any refusal. */
  it('returns the card on a 409 the client did not predict', async () => {
    transport.on('POST', INTEREST, () => errorResponse(409, 'outstanding_interest_cap_reached'));
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await screen.findByText(CAP_REACHED_SENTENCE);
    expect(screen.getByLabelText("Let's play, Marek Z.")).toBeTruthy();
  });

  it('holds an answer made offline rather than failing it, and says so', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    act(() => onlineManager.setOnline(false));
    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
  });
});

/**
 * **A swipe is an answer** (ADR-0169 §3). Walked at the responder, in the order the responder
 * system calls it, by `test-support/swipe.ts`.
 */
describe('yes and no, by the drag', () => {
  it('flies right past the threshold and sends the yes', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(swipe(marek(), commit)).toBe(true);

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(transport.requestsTo('POST', INTEREST)[0]?.body).toMatchObject({ player_id: MAREK });
  });

  it('flies left past the threshold and sends the pass', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    swipe(marek(), -commit);

    await waitFor(() => expect(transport.requestsTo('POST', PASSES)).toHaveLength(1));
    expect(announced()).toEqual([passedAnnouncement('Marek Z.')]);
  });

  /** Released early, the card settles back: nothing sent, the same person still up. */
  it('settles back short of the threshold, and sends nothing', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    swipe(marek(), commit - 1);
    await act(async () => {});

    expect(transport.requestsTo('POST', PASSES)).toHaveLength(0);
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
    expect(screen.getByLabelText(MAREK_CARD)).toBeTruthy();
  });

  /** The stamps are feedback: invisible at rest, following the finger, full at the threshold. */
  it('draws the stamp under the thumb, full at the threshold', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    const opacityOf = (said: 'yes' | 'no') => {
      const styles = [screen.getByTestId(`deck-stamp-${said}`, HIDDEN_TOO).props.style].flat(3) as (
        { opacity?: unknown } | undefined
      )[];
      return Number(styles.find((entry) => entry?.opacity !== undefined)?.opacity);
    };
    expect(opacityOf('yes')).toBe(0);

    dragTo(marek(), commit / 2);
    expect(opacityOf('yes')).toBeCloseTo(0.5, 5);
    expect(opacityOf('no')).toBe(0);
    release(marek());

    // The words are the buttons' own, uppercased by the stamp — and never a control.
    expect(screen.getByText("Let's play", HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Not today', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByRole('button', { name: "Let's play" })).toBeNull();
  });

  it('ticks the motor once at the threshold', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    swipe(marek(), commit + 40);

    expect(haptics.felt).toEqual(['light']);
  });

  /** Reduce motion: no motion, no haptic — and the answer still lands. */
  it('lands the answer under reduced motion, with no tick', async () => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    // The root's one read of the OS motion switch resolves off the render that mounted it.
    await act(async () => {});

    swipe(marek(), commit + 40);

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(haptics.felt).toEqual([]);
  });
});

describe('the stack', () => {
  /** Two real cards behind, the hand's next two people, and only when that many remain. */
  it('draws the next two people behind the top card', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByText('Ana K.', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Ola W.', HIDDEN_TOO)).toBeTruthy();
    // Behind, not beside: the top card is the one element a listener meets.
    expect(screen.queryByLabelText(ANA_CARD)).toBeNull();
  });

  it('draws one behind when one remains, and none when none does', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA)] })),
    );
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByText('Ana K.', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText('Ola W.', HIDDEN_TOO)).toBeNull();

    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);

    expect(screen.queryByText('Marek Z.', HIDDEN_TOO)).toBeNull();
  });

  /**
   * **The next hand at two, appended** (ADR-0169 §5): answering down to two unanswered asks
   * for the next hand and the cards behind stay real — and the join is invisible, because the
   * cards already dealt are kept in front of the new ones.
   */
  it('asks for the next hand when two remain, and puts it behind the cards in hand', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    expect(dealBodies()).toHaveLength(1);

    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Tomek P.', TOMEK)], searchId: 'second-hand', remaining: 0 })),
    );
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);

    await waitFor(() => expect(dealBodies()).toHaveLength(2));
    expect(await screen.findByText('Tomek P.', HIDDEN_TOO)).toBeTruthy();
    // Ana is still up, Ola still next: the new hand went behind, not in front.
    expect(screen.getByLabelText(ANA_CARD)).toBeTruthy();
    expect(screen.getByText('Ola W.', HIDDEN_TOO)).toBeTruthy();
  });

  /** Every card cites the hand it came off — the origin key — whichever hand is the latest. */
  it('answers a card from the first hand with the first hand’s search id', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Tomek P.', TOMEK)], searchId: 'second-hand', remaining: 0 })),
    );
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    fireEvent.press(screen.getByLabelText("Let's play, Ana K."));

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(transport.requestsTo('POST', INTEREST)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: ANA,
      search_id: SEARCH_ID,
    });
  });

  /**
   * **An answer given while the next hand is in flight stays given.** The hand is folded onto
   * what the entry holds *when it lands*, not what it held when it was asked for — a fold over
   * the pre-flight entry would put back every card answered during the POST.
   */
  it('keeps an answer given while the next hand was in flight', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    let land = (_response: Response) => {};
    transport.on('POST', DECK, () => new Promise<Response>((resolve) => (land = resolve)));
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    // Ana is answered while the second hand is still on its way.
    fireEvent.press(screen.getByLabelText('Not today, Ana K.'));
    await screen.findByLabelText(cardOf('Ola W.'));

    await act(async () => {
      land(
        json(
          deal({ candidates: [card('Tomek P.', TOMEK)], searchId: 'second-hand', remaining: 0 }),
        ),
      );
    });

    expect(await screen.findByText('Tomek P.', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByLabelText(cardOf('Ola W.'))).toBeTruthy();
    expect(screen.queryByLabelText(ANA_CARD)).toBeNull();
    expect(screen.queryByText('Ana K.', HIDDEN_TOO)).toBeNull();
  });

  it('does not ask for the next hand when the pool has nobody beyond this one', async () => {
    transport.on('POST', DECK, () =>
      json({
        ...THREE_CARDS,
        search: { ...THREE_CARDS.search, pool: { ...THREE_CARDS.search.pool, remaining: 0 } },
      }),
    );
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);
    await act(async () => {});

    expect(dealBodies()).toHaveLength(1);
  });
});

describe('the counter', () => {
  /**
   * *N left* is the pool beyond the hand plus the hand still unanswered, and *N yeses to give*
   * is the cap less the outstanding — both off the wire, the cap the mapper used to drop.
   */
  it('reads remaining plus unanswered, and cap less outstanding', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(await screen.findByText(deckCounter({ left: 8, give: 12 }))).toBeTruthy();
  });

  it('counts down one per answer, and the budget on the yes’s own reply', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    transport.on('POST', INTEREST, () => json(expressed(false, 9), 201));
    await openDeck();
    await screen.findByText(deckCounter({ left: 8, give: 12 }));

    // The pass takes the hand to two, so the next hand is asked for: one more card in hand and
    // one fewer beyond it, which is the same seven — the counter counts the pool, not the hand.
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Tomek P.', TOMEK)], searchId: 'second-hand', remaining: 4 })),
    );
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    expect(await screen.findByText(deckCounter({ left: 7, give: 12 }))).toBeTruthy();

    fireEvent.press(screen.getByLabelText("Let's play, Ana K."));
    expect(await screen.findByText(deckCounter({ left: 6, give: 11 }))).toBeTruthy();
    // One read, at mount. The tap's answer carried the new count, so nothing asked again.
    expect(transport.requestsTo('GET', INTEREST)).toHaveLength(1);
  });

  it('says what is left alone until the interest read has landed', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    transport.on('GET', INTEREST, () => new Promise<Response>(() => {}));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(await screen.findByText(deckCounter({ left: 8 }))).toBeTruthy();
  });

  /**
   * The same reply moves the reader's own list, which is what *You said yes* on the builder's
   * cards and the challenge screen is drawn from (ADR-0169 §8) — so a builder opened straight
   * after a swipe tags the person without a second read, and a mutual is never on it.
   */
  it('puts a one-sided yes on the reader’s own list off the reply, and leaves a mutual off it', async () => {
    transport.on('POST', DECK, () => json(THREE_CARDS));
    transport.on('POST', INTEREST, () => json(expressed(false, 9), 201));
    await openDeck();
    await screen.findByText(deckCounter({ left: 8, give: 12 }));

    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));
    await screen.findByText(deckCounter({ left: 7, give: 11 }));
    expect(queryClient.getQueryData<MyInterest>(searchKeys.interest())?.outgoing).toEqual({
      padel: [MAREK],
    });

    transport.on('POST', INTEREST, () => json(expressed(true, 9), 201));
    fireEvent.press(screen.getByLabelText("Let's play, Ana K."));
    await waitFor(() => expect(toasts()).toEqual([mutualToast('Ana K.')]));
    expect(queryClient.getQueryData<MyInterest>(searchKeys.interest())?.outgoing).toEqual({
      padel: [MAREK],
    });
    expect(transport.requestsTo('GET', INTEREST)).toHaveLength(1);
  });
});

describe('the chip', () => {
  it('reads the envelope’s count and names nobody', async () => {
    transport.on('POST', DECK, () => json(deal({ wantToPlayYou: 2 })));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByText(wantToPlayYouChip(2))).toBeTruthy();
  });

  it('is not drawn at nought', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.queryByText(/want to play you/)).toBeNull();
  });

  /** A liker's yes come back mutual is one of the people counted, answered. */
  it('drops by one when a yes on a liker’s card comes back mutual', async () => {
    transport.on('POST', DECK, () =>
      json(
        deal({
          candidates: [
            card('Marek Z.', MAREK, { inclusion_reason: 'INTEREST_LIFT' }),
            card('Ana K.', ANA),
          ],
          wantToPlayYou: 2,
        }),
      ),
    );
    transport.on('POST', INTEREST, () => json(expressed(true)));
    await openDeck();
    await screen.findByText(wantToPlayYouChip(2));

    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    expect(await screen.findByText(wantToPlayYouChip(1))).toBeTruthy();
  });

  it('does not drop for a mutual on somebody the deal did not count', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA)], wantToPlayYou: 2 })),
    );
    transport.on('POST', INTEREST, () => json(expressed(true)));
    await openDeck();
    await screen.findByText(wantToPlayYouChip(2));

    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));
    await waitFor(() => expect(toasts()).toEqual([mutualToast('Marek Z.')]));

    expect(screen.getByText(wantToPlayYouChip(2))).toBeTruthy();
  });
});

/**
 * **At the ceiling** (ADR-0169 §3): the client pre-empts the one refusal it can read, and the
 * exemption runs the way the server's does — a yes that closes a mutual is never outstanding.
 */
describe('at the ceiling', () => {
  it('settles a stranger’s card with the ceiling’s sentence, and sends nothing', async () => {
    stubInterest(transport, standing(20));
    await openDeck();
    await screen.findByText(deckCounter({ left: 1, give: 0 }));

    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(toasts()).toEqual([CAP_REACHED_SENTENCE]));
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
    expect(screen.getByLabelText(MAREK_CARD)).toBeTruthy();
  });

  it('settles it on a drag too', async () => {
    stubInterest(transport, standing(20));
    await openDeck();
    await screen.findByText(deckCounter({ left: 1, give: 0 }));

    swipe(marek(), commit + 40);
    await act(async () => {});

    expect(toasts()).toEqual([CAP_REACHED_SENTENCE]);
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
    expect(screen.getByLabelText(MAREK_CARD)).toBeTruthy();
  });

  it('sends a liker’s yes whatever the count, because it closes a mutual', async () => {
    stubInterest(transport, standing(20));
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [card('Marek Z.', MAREK, { inclusion_reason: 'INTEREST_LIFT' })] })),
    );
    transport.on('POST', INTEREST, () => json(expressed(true, 20)));
    await openDeck();
    await screen.findByText(deckCounter({ left: 1, give: 0 }));

    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(toasts()).toEqual([mutualToast('Marek Z.')]);
  });

  /** A pass is not a yes: the ceiling withholds nothing from it. */
  it('lets a pass through at the ceiling', async () => {
    stubInterest(transport, standing(20));
    await openDeck();
    await screen.findByText(deckCounter({ left: 1, give: 0 }));

    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));

    await waitFor(() => expect(transport.requestsTo('POST', PASSES)).toHaveLength(1));
    expect(toasts()).toEqual([]);
  });
});

/**
 * **The record sheet, from the i and from the long press**, with the deck's pairing in hand so
 * *why this Fit* lives behind the sheet's fit row (ADR-0169 §3).
 */
describe('the record', () => {
  it('opens the record sheet from the i, with the pairing’s fit row — and no foot', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByRole('button', { name: 'Marek Z.’s record' }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(await screen.findByRole('button', { name: fitRowLabel(78) })).toBeTruthy();
    // The deck's *i* fills the sheet's slot with nothing (ADR-0174 §4): the deck's own buttons
    // are one tap away, and two places to answer at once invites a double tap. The sheet
    // therefore names no second *Let's play* — the one under the sheet, hidden from a listener
    // while it is up, is the only element by that name, and it is the deck's.
    expect(screen.queryByTestId('radar-sheet-foot')).toBeNull();
    expect(screen.getAllByLabelText("Let's play, Marek Z.", HIDDEN_TOO)).toHaveLength(1);
  });

  it('opens the same sheet on a long press — the i’s twin, with no hint line to say so, and no foot', async () => {
    await openDeck();
    fireEvent(await screen.findByLabelText(MAREK_CARD), 'longPress');

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(screen.queryByTestId('radar-sheet-foot')).toBeNull();
  });

  /**
   * **The intro, on the card and on the sheet** — quoted, where they wrote one, and the gap
   * closed where they did not (ADR-0170 §4, [#445](https://github.com/Raketa02/Raketa/issues/445)).
   * Both surfaces read the same field off two different routes: the card's is the search
   * record's, the sheet's is the profile's.
   */
  it('draws the intro on the card and under the name on the record, and neither where there is none', async () => {
    const LINE = 'Two games in. Moved here in September, still learning the city.';
    transport.on('POST', DECK, () =>
      json(
        deal({
          candidates: [
            card('Marek Z.', MAREK, {
              player_card: { ...card('Marek Z.', MAREK).player_card, intro: LINE },
            }),
            card('Ana K.', ANA),
          ],
        }),
      ),
    );
    transport.on('GET', `${PLAYERS}/${MAREK}/record?sport=PADEL`, () =>
      json({ ...mareksRecord(), intro: LINE }),
    );
    transport.on('GET', `${PLAYERS}/${ANA}/record?sport=PADEL`, () =>
      json({ ...mareksRecord(), name: 'Ana K.', nickname: 'ana_k' }),
    );
    await openDeck();

    // On the card: inside the drawing's marks, and spoken as their own words.
    expect(await screen.findByText(`“${LINE}”`)).toBeTruthy();
    expect(marek().props.accessibilityLabel).toContain(`“${LINE}”`);

    // On the sheet, under the name — the header is one element, spoken name and `@nickname`
    // first (ADR-0171 §4) and the line inside its marks straight after.
    fireEvent(marek(), 'longPress');
    await screen.findByText(RECORD_TITLE);
    expect(
      await screen.findByLabelText(new RegExp(`^Marek Z\\.\\. @marek_z\\. “${LINE}”`)),
    ).toBeTruthy();
    expect(screen.getByText(`“${LINE}”`)).toBeTruthy();

    // And Ana, who wrote none: the card closes the gap rather than drawing empty marks, and
    // so does her sheet — the identity line sits straight under the handle.
    fireEvent.press(screen.getByLabelText(recordCloseLabel(false)));
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(ANA_CARD);
    expect(screen.getByLabelText(ANA_CARD).props.accessibilityLabel).not.toContain('“');

    fireEvent(screen.getByLabelText(ANA_CARD), 'longPress');
    await screen.findByText(RECORD_TITLE);
    const header = await screen.findByLabelText(/^Ana K\.\. /);
    expect(header.props.accessibilityLabel).not.toContain('“');
    expect(screen.queryByText(/“/)).toBeNull();
  });

  /** The Fit breakdown is one row further in: the sheet's fit row opens it, and never the card. */
  it('opens the Fit breakdown from the record’s fit row', async () => {
    await openDeck();
    fireEvent(await screen.findByLabelText(MAREK_CARD), 'longPress');
    await screen.findByText(RECORD_TITLE);

    fireEvent.press(await screen.findByRole('button', { name: fitRowLabel(78) }));

    expect(await screen.findByLabelText('Why fit 78')).toBeTruthy();
  });
});

/**
 * **A mutual naming a challenge opens the yes screen** — *Matched!* — and the mutual-with-chat
 * toast is retired (ADR-0167 §1, §4; [#434](https://github.com/Raketa02/Raketa/issues/434)).
 * Walked end to end: the deck, the reply, the screen, and each of its two doors back out.
 */
describe('a mutual that named a challenge', () => {
  const TWO_CARDS = deal({ candidates: [card('Marek Z.', MAREK), card('Ana K.', ANA)] });

  /** A deal of two, and *Let's play* on the first, answered mutual with the named challenge. */
  async function sayYesToMarek(sport: 'TENNIS' | 'PADEL') {
    transport.on('POST', DECK, () => json(TWO_CARDS));
    transport.on('POST', INTEREST, () => json(expressed(true, 3, CHALLENGE), 201));
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () => json(matched(sport)));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    if (sport === 'TENNIS') {
      fireEvent.press(screen.getByLabelText('Tennis'));
      await waitFor(() => expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]));
    }
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));
    await waitFor(() => expect(screen).toHavePathname(YES_SCREEN));
    // The pathname moves a beat before the screen is on the tree.
    await screen.findByTestId('yes-screen');
  }

  const yesScreen = () => within(screen.getByTestId('yes-screen'));

  it.each(['TENNIS', 'PADEL'] as const)(
    'opens the yes screen as a mutual’s, with two tiles and no vs, in %s',
    async (sport) => {
      await sayYesToMarek(sport);

      expect(screen).toHaveSearchParams(expect.objectContaining({ which: 'mutual' }));
      expect(screen.queryAllByRole('tab')).toHaveLength(0);
      // The picture as a sentence — *Matched! You and Marek Z.* — and the word on the screen.
      expect(await yesScreen().findByRole('header', { name: MATCHED_SPOKEN })).toBeTruthy();
      expect(yesScreen().getByText(MATCHED_WORD)).toBeTruthy();
      // You and them, and nothing else: no `vs`, and no empty seat — not even in padel, where
      // the court has a side still to fill.
      expect(yesScreen().getAllByTestId('yes-tile-poster')).toHaveLength(2);
      expect(yesScreen().queryAllByTestId('yes-tile-empty')).toHaveLength(0);
      expect(yesScreen().queryByText('vs', HIDDEN_TOO)).toBeNull();
      // And the retired sentence is not said: the screen is the whole of what a mutual says.
      expect(toasts()).toEqual([]);
      expect(yesScreen().getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
      expect(yesScreen().getByRole('button', { name: LATER })).toBeTruthy();
    },
  );

  it('goes back to the deck on Later, with the next card up', async () => {
    await sayYesToMarek('PADEL');
    fireEvent.press(yesScreen().getByRole('button', { name: LATER }));

    await waitFor(() => expect(screen).toHavePathname('/players'));
    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
    expect(screen.queryByLabelText(MAREK_CARD)).toBeNull();
    // The same deal, found rather than dealt again.
    expect(dealBodies()).toHaveLength(1);
  });

  it('is what the device’s back does', async () => {
    watchHardwareBack();
    await sayYesToMarek('PADEL');

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);
    await waitFor(() => expect(screen).toHavePathname('/players'));
    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
  });

  /**
   * **The same landing as after a challenge's yes — `[Chats list, the room]` — reached by the
   * tab's own move.** The list is nowhere under the deck, so the shell lays it down and the room
   * is pushed over it: back from the room is the list with nothing behind it, and Players,
   * entered again, finds the deal it dealt on rather than dealing a second one.
   */
  it('opens the room under the Chats tab, back is the Chats list, and Players keeps its held deal', async () => {
    await sayYesToMarek('TENNIS');
    theRoomIsThere('TENNIS', GAME);

    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));
    await waitFor(() => expect(screen).toHavePathname(THE_ROOM), { timeout: 5000 });

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(screen.getAllByRole('tab')).toHaveLength(5);
    // The list is the bottom of the stack: no deck, no celebration behind it.
    expect(router.canGoBack()).toBe(false);

    // Players, entered again, holds the deal — the next card is up and nothing was dealt.
    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]);
  });

  /**
   * **Past the bound the door is the list, from the deck too** — and the list is reached by the
   * tab's own move alone, with no room to push over it.
   */
  it('lands on the Chats list when the room is not listed within the bound, with the deck gone', async () => {
    const before = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    await sayYesToMarek('PADEL');
    fireEvent.press(yesScreen().getByRole('button', { name: OPEN_THE_CHAT }));

    // Not at once: the list is asked its whole bound first, and the tap waits on the button.
    await waitFor(() =>
      expect(
        transport.requestsTo('GET', CONVERSATIONS_PATH).length - before,
      ).toBeGreaterThanOrEqual(3),
    );
    expect(screen).toHavePathname(YES_SCREEN);

    await waitFor(() => expect(screen).toHavePathname('/chats'), { timeout: 9000 });
    expect(screen.getAllByRole('tab')).toHaveLength(5);
    expect(router.canGoBack()).toBe(false);
  }, 12000);

  /**
   * **A slow reply must not swallow the moment.** The yes is optimistic and the reply may land
   * after the player has moved on — here made in a tunnel, held until the connection returns
   * (`networkMode: 'online'`), and answered once they have gone to Chats and the deck is off the
   * stack. The screen still opens, wherever they are, because the push lives with the mutation
   * and not with the screen that fired it (ADR-0167 §1).
   */
  it('opens the yes screen when the reply lands after the deck was left', async () => {
    transport.on('POST', DECK, () => json(TWO_CARDS));
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () => json(matched('PADEL')));
    let answer = (_response: Response) => {};
    transport.on('POST', INTEREST, () => new Promise<Response>((resolve) => (answer = resolve)));
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    act(() => onlineManager.setOnline(false));
    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));
    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();

    // Gone to Chats before the reply: the deck is off the stack, and nothing has been sent.
    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);

    // The connection returns, the yes goes, and the reply lands on Chats.
    act(() => onlineManager.setOnline(true));
    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    await act(async () => {
      answer(json(expressed(true, 3, CHALLENGE), 201));
    });

    await waitFor(() => expect(screen).toHavePathname(YES_SCREEN));
    await screen.findByTestId('yes-screen');
    expect(await yesScreen().findByRole('header', { name: MATCHED_SPOKEN })).toBeTruthy();
    expect(toasts()).toEqual([]);
    // And *Later* is a pop to wherever the reply found them.
    fireEvent.press(yesScreen().getByRole('button', { name: LATER }));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
  });
});

describe('the two endings', () => {
  /**
   * *You have seen everybody* draws the mock — the radius the deal ran on and how long a yes
   * lives, read off the interest row — with **Show them again** and **Try the radar**.
   */
  it('draws the radius and the life of a yes from the wire, with both buttons', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    await openDeck();

    expect(await screen.findByText(SEEN_EVERYBODY_TITLE)).toBeTruthy();
    expect(screen.getByText(seenEverybodyLine({ radiusKm: 12, ttlDays: 21 }))).toBeTruthy();
    expect(screen.getByRole('button', { name: SHOW_THEM_AGAIN_LABEL })).toBeTruthy();
    expect(screen.getByRole('button', { name: TRY_THE_RADAR_LABEL })).toBeTruthy();
    // Nobody's count of cards on an ending: the counter is the card's.
    expect(screen.queryByText(/left/)).toBeNull();
  });

  it('reads an empty deal with nobody in range as the other state, advises widening, and offers no reset', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [], playersInRange: 0 })));
    await openDeck();

    expect(await screen.findByText(NOBODY_IN_RANGE_TITLE)).toBeTruthy();
    expect(
      screen.getByText(
        poolDescription({ playersInRange: 0, radiusKmUsed: 12, sportName: 'Padel' }),
      ),
    ).toBeTruthy();
    expect(screen.getByText(WIDEN_IN_YOU)).toBeTruthy();
    // The reset would deal nobody, so it is not offered — asserted as an absence.
    expect(screen.queryByRole('button', { name: SHOW_THEM_AGAIN_LABEL })).toBeNull();
  });

  /** Nobody is asked for something they cannot give: `radius_clamp` gates the sentence. */
  it('never advises widening to a player already at their own ceiling', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ candidates: [], playersInRange: 0, radiusClamp: true })),
    );
    await openDeck();

    expect(await screen.findByText(NOBODY_IN_RANGE_TITLE)).toBeTruthy();
    expect(screen.queryByText(WIDEN_IN_YOU)).toBeNull();
  });

  it('never advises widening to a player who has simply answered everybody', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    // The hand is spent, so the screen deals again — and a spent hand is never an ending.
    await waitFor(() => expect(dealBodies()).toHaveLength(2));
    expect(screen.queryByText(WIDEN_IN_YOU)).toBeNull();
  });

  /**
   * *"A spent deal deals again… the screen runs out of cards long before the pool does, and
   * only a fresh deal that comes back empty is the empty state."*
   */
  it('deals again when the last card is answered, and only then shows an ending', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    // A new deal is a new `search_id` — here re-dealing the same person, which the route does
    // only after the dealt memory has lapsed, and which is then a new card.
    transport.on('POST', DECK, () => json(deal({ searchId: 'second-deal' })));
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(screen.queryByText(SEEN_EVERYBODY_TITLE)).toBeNull();

    transport.on('POST', DECK, () => json(deal({ candidates: [], searchId: 'third-deal' })));
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    expect(await screen.findByText(SEEN_EVERYBODY_TITLE)).toBeTruthy();
  }, 12000);

  /**
   * **Show them again** is `POST /deck/reset` for this sport, then a fresh deal — with nothing
   * answered on it, so the people it re-deals are dealt and not hidden.
   */
  it('resets for this sport and deals afresh on Show them again', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    await openDeck();
    await screen.findByText(SEEN_EVERYBODY_TITLE);

    transport.on('POST', DECK, () => json(deal({ searchId: 'after-the-reset' })));
    fireEvent.press(screen.getByRole('button', { name: SHOW_THEM_AGAIN_LABEL }));

    await waitFor(() => expect(transport.requestsTo('POST', RESET)).toHaveLength(1));
    expect(transport.requestsTo('POST', RESET)[0]?.body).toEqual({ sport: 'PADEL' });
    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(dealBodies()).toHaveLength(2);
    expect(screen.queryByText(SEEN_EVERYBODY_TITLE)).toBeNull();
  });

  it('re-deals somebody answered before the reset, because the reset starts the deal over', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    transport.on('POST', DECK, () => json(deal({ candidates: [], searchId: 'second-deal' })));
    fireEvent.press(screen.getByLabelText('Not today, Marek Z.'));
    // Marek was answered; the second hand is empty; the ending is up.
    await screen.findByText(SEEN_EVERYBODY_TITLE);

    // The reset deals Marek again — on the very same `search_id` the fixture served first, which
    // is the harshest case — and he is dealt, not hidden as already answered.
    transport.on('POST', DECK, () => json(deal()));
    fireEvent.press(screen.getByRole('button', { name: SHOW_THEM_AGAIN_LABEL }));

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(screen.getByLabelText('Not today, Marek Z.')).toBeTruthy();
    // Three deals and a flight between them: past the default five seconds under a full run.
  }, 12000);

  it('leaves the ending up with the sentence when the reset is refused', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    transport.on('POST', RESET, () => errorResponse(409, 'sport_not_rated'));
    await openDeck();
    await screen.findByText(SEEN_EVERYBODY_TITLE);

    fireEvent.press(screen.getByRole('button', { name: SHOW_THEM_AGAIN_LABEL }));

    expect(
      await screen.findByText(playErrorMessage({ code: 'sport_not_rated' } as never)),
    ).toBeTruthy();
    expect(screen.getByText(SEEN_EVERYBODY_TITLE)).toBeTruthy();
    expect(dealBodies()).toHaveLength(1);
  }, 12000);

  it('flips to the Radar pane on Try the radar', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    await openDeck();
    await screen.findByText(SEEN_EVERYBODY_TITLE);

    fireEvent.press(screen.getByRole('button', { name: TRY_THE_RADAR_LABEL }));

    expect(await screen.findByLabelText(BACK_TO_YOU_LABEL)).toBeTruthy();
    expect(screen.getByRole('button', { name: PANE_LABEL.radar, selected: true })).toBeTruthy();
    expect(screen).toHavePathname('/players');
  });
});

/**
 * **Players, the tab** (ADR-0169 §1). The deck is the whole of the second column: no title row,
 * a *Deck | Radar* toggle for a header, chips only where there is a choice, and nothing asking
 * anybody what kind of game.
 */
describe('Players, the tab', () => {
  it('lights Players and not Play, and is its own root', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByRole('tab', { name: 'Players', selected: true })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Play', selected: false })).toBeTruthy();
    expect(router.canGoBack()).toBe(false);
  });

  /** No title row: the toggle is the header, and there is no heading element to land on. */
  it('opens on Deck, with the toggle for a header and no title', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByRole('button', { name: PANE_LABEL.deck, selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: PANE_LABEL.radar, selected: false })).toBeTruthy();
    expect(screen.queryByRole('header')).toBeNull();
    expect(screen.queryByText(/Match me/)).toBeNull();
  });

  it('flips to the Radar pane, and back', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));

    expect(await screen.findByLabelText(BACK_TO_YOU_LABEL)).toBeTruthy();
    expect(screen.queryByLabelText(MAREK_CARD)).toBeNull();
    expect(screen.getByRole('button', { name: PANE_LABEL.radar, selected: true })).toBeTruthy();
    // A pane and not a route: the toggle moved and the tab did not.
    expect(screen).toHavePathname('/players');

    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.deck }));

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(screen.queryByLabelText(BACK_TO_YOU_LABEL)).toBeNull();
  });

  /** The toggle is the screen's own state, and the screen is remounted on every arrival. */
  it('lands on Deck again after leaving from Radar, because Players always opens on Deck', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByLabelText(BACK_TO_YOU_LABEL);

    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(screen.getByRole('button', { name: PANE_LABEL.deck, selected: true })).toBeTruthy();
    expect(screen.queryByLabelText(BACK_TO_YOU_LABEL)).toBeNull();
  });

  /**
   * **Chips only when there is a choice.** Rated in two sports, the row is under the toggle and
   * reads and writes the same browsed sport Play's chips do; rated in one, the mock is seen
   * exactly.
   */
  it('draws the sport chips for a player rated in two sports, under the toggle', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.getByText(SPORT_HEADING)).toBeTruthy();
    expect(screen.getByLabelText('Padel')).toBeTruthy();
    expect(screen.getByLabelText('Tennis')).toBeTruthy();
  });

  it('draws no chips for a player rated in one sport', async () => {
    stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    expect(screen.queryByText(SPORT_HEADING)).toBeNull();
    expect(screen.queryByLabelText('Padel')).toBeNull();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * **Nobody is asked to declare on Players, and nothing says what the deal runs on.** Every
   * deal runs under one ruler (ADR-0169 §2), and both are absences.
   */
  it('deals an undeclared player without an interstitial, and draws no standing line', async () => {
    stubProfileSurface(transport, {
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: {},
    });
    await openDeck();

    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
    expect(screen.queryByText(declarationTitle('Padel'))).toBeNull();
    for (const intent of ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const) {
      const line = declarationLine({ intent, mode: undefined, sportName: 'Padel' });
      expect(screen.queryByLabelText(line.spoken)).toBeNull();
      expect(screen.queryByLabelText(line.actionLabel)).toBeNull();
    }
    for (const mode of ['COMPETITIVE', 'FOR_FUN'] as const) {
      expect(screen.queryByLabelText(modeControlLabel(mode))).toBeNull();
    }
  });

  it('draws no standing line for a declared player either', async () => {
    await openDeck();
    await screen.findByLabelText(MAREK_CARD);

    const line = declarationLine({ intent: 'FOR_FUN', mode: undefined, sportName: 'Padel' });
    expect(screen.queryByLabelText(line.spoken)).toBeNull();
    expect(screen.queryByLabelText(line.actionLabel)).toBeNull();
  });
});

/**
 * **The questions a deal raises, and the two things that are different about asking them here.**
 *
 * A deal is not a press — the entry deal falls out of arriving and the next hand is asked for on
 * its own — so *asked once* has to hold across hands rather than across searches. And the deck
 * has no week grid, so the one prompt whose *yes* is a request for one never reaches it
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 */
describe('the question a deal raised', () => {
  const KEEP_THIS_RADIUS = promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 22 }).title;
  const REFRESH_YOUR_TIMES = promptCopy({ prompt: 'REFRESH_YOUR_TIMES' }).title;
  const UPDATE_PLAY_INTENT = promptCopy({
    prompt: 'UPDATE_PLAY_INTENT',
    sportName: 'Padel',
    mode: 'FOR_FUN',
  }).title;

  it('is asked over the card the deal has already dealt', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }] })),
    );
    await openDeck();

    // There is no push to stand in front of and no wait to lift: the deal is recorded, the
    // card is behind the sheet, and closing it is the whole of where anybody goes.
    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    expect(dealBodies()).toHaveLength(1);
  });

  it('writes its yes through the route that owns the value', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }] })),
    );
    await openDeck();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS)[0]?.body).toEqual({ search_radius_km: 22 });
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });

  /**
   * The half a `search_id` key would get wrong. The next hand is a new deal, and the condition
   * a prompt is raised on does not change because a hand was answered — so a question keyed
   * by the deal would be put in front of the player again on every hand.
   */
  it('is not asked again by the hand that follows it', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }] })),
    );
    await openDeck();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));
    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));

    // Answering the last card spends the hand, so the screen deals again — and the second
    // hand raises the same question, off a second `search_id`.
    transport.on('POST', DECK, () =>
      json(
        deal({
          candidates: [card('Ana K.', ANA)],
          searchId: 'second-deal',
          prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }],
        }),
      ),
    );
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(await screen.findByLabelText(ANA_CARD)).toBeTruthy();
    expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull();
  });

  /**
   * One deal asks one question. Answering promotes whatever was behind it, and a second sheet
   * opening onto the first one closing is the stack the response ordering exists to prevent.
   */
  it('does not put the question behind it onto the same deal', async () => {
    transport.on('POST', DECK, () =>
      json(
        deal({
          prompts: [
            { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 },
            { prompt: 'UPDATE_PLAY_INTENT', mode: 'FOR_FUN' },
          ],
        }),
      ),
    );
    await openDeck();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));

    await waitFor(() => expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull());
    expect(screen.queryByText(UPDATE_PLAY_INTENT)).toBeNull();
    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
  });

  /**
   * The half a `prompts[0]`-then-check would lose. Every later list starts with the same
   * leading code, so a screen that picked the first prompt and *then* found it answered would
   * go silent for the rest of the visit with a second question standing right behind it.
   */
  it('asks the question behind it on the hand that follows', async () => {
    const raising = () =>
      json(
        deal({
          candidates: [
            card(
              `Player ${transport.requestsTo('POST', DECK).length}`,
              `aaaaaaaa-0000-4000-8000-00000000001${transport.requestsTo('POST', DECK).length}`,
            ),
          ],
          searchId: `deal-${transport.requestsTo('POST', DECK).length}`,
          prompts: [
            { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 },
            { prompt: 'UPDATE_PLAY_INTENT', mode: 'FOR_FUN' },
          ],
        }),
      );
    transport.on('POST', DECK, raising);
    await openDeck();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));
    await waitFor(() => expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull());

    // Answering the last card spends the hand, so the screen deals again — and the second
    // hand raises the same two questions, the first of which has been answered this visit.
    fireEvent.press(await screen.findByLabelText('Not today, Player 1'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(await screen.findByText(UPDATE_PLAY_INTENT)).toBeTruthy();
    expect(screen.queryByText(KEEP_THIS_RADIUS)).toBeNull();
  });

  /**
   * `REFRESH_YOUR_TIMES`'s *yes* hands the player back to the week grid, and this screen has
   * none. It is **dropped** rather than truncated to, which is why the fixture puts it first:
   * what the sheet asks is the next question the deck can honour.
   */
  it('is never the one whose yes is a week grid this screen does not have', async () => {
    transport.on('POST', DECK, () =>
      json(
        deal({
          prompts: [
            { prompt: 'REFRESH_YOUR_TIMES' },
            { prompt: 'KEEP_THIS_RADIUS', radius_km: 22 },
          ],
        }),
      ),
    );
    await openDeck();

    expect(await screen.findByText(KEEP_THIS_RADIUS)).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });

  it('leaves the card alone where the only question raised is that one', async () => {
    transport.on('POST', DECK, () => json(deal({ prompts: [{ prompt: 'REFRESH_YOUR_TIMES' }] })));
    await openDeck();

    // No sheet at all — the card the deal dealt is reachable, which it would not be behind one.
    expect(await screen.findByLabelText(MAREK_CARD)).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });
});
