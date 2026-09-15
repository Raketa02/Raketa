/**
 * **Players** — the deck, walked the way a player walks it: the real route tree, the real
 * shell, the real stores and only `fetch` faked.
 *
 * What is asserted here is the set of decisions a build session could quietly undo. Four of
 * them are refusals, and a refusal is only observable as an absence — which is why they are
 * driven from the outside rather than unit-called:
 *
 * - **Yes and no are buttons, and there is no swipe.** The gesture is not the cheapest thing
 *   in the app on the most durable act in it, and no gesture library is added for one.
 * - **There is no *Show them again*.** The prototype's button makes `PASS_SUPPRESS`
 *   unmeasurable, so the honest ending is the pool and the count of your own yeses.
 * - **A spent deal is not an empty pool**, and the two empty states split on
 *   `players_in_range` — the advice is addressed to the player who can act on it.
 * - **Nobody is asked to declare on Players, and nothing on it says what the deal runs on.**
 *   Every deal runs under one ruler
 *   ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 *   §2), so the interstitial and the standing line are absences here.
 *
 * And one placement, which the whole suite walks by arriving through the bar: the deck is the
 * **Players** tab, at `/players`, with a *Deck | Radar* toggle for a header and no route under
 * Play (ADR-0169 §1).
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { LATER, MATCHED_WORD, matchedAnnouncement } from '@/features/challenges/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
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
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { usePlayPreferences } from '../store/playPreferences.store';
import { endPlaySession } from '../store/playSession.store';

import { declarationLine, declarationTitle, modeControlLabel } from './findAGamePresentation';
import {
  DECK_FOOTER,
  NOBODY_IN_RANGE_TITLE,
  PANE_LABEL,
  RADAR_LINE,
  SEEN_EVERYBODY_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  mutualToast,
  outgoingYeses,
  passedToast,
} from './deckPresentation';
import { SPORT_HEADING } from './SportChips';
import { playErrorMessage } from './playErrorMessage';
import { metaLine } from './playerCardPresentation';
import { promptControls, promptCopy } from './promptPresentation';
import { poolDescription } from './searchPresentation';

const DECK = '/api/v1/deck';
const TENNIS_INTENT = '/api/v1/play-intents/TENNIS';
const INTEREST = '/api/v1/interest';
const PASSES = '/api/v1/passes';
const DECLINES = '/api/v1/prompt-declines';
const RADIUS = '/api/v1/players/me/search-radius';

const SEARCH_ID = 'd0d1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';

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

/** One dealt card. Enough terms that the sheet has rows and the card has a reason line. */
function card(nickname: string, playerId: string): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 78,
    distance_km: 4,
    player_card: {
      nickname,
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
        term: 'INTENT_ALIGNMENT',
        weight: 40,
        value: 1,
        contribution: 40,
        evidence: {
          kind: 'intent_alignment',
          my_mode: 'FOR_FUN',
          their_intent: 'FOR_FUN',
          aligned: true,
        },
      },
    ],
    degraded_terms: [
      { term: 'RELIABILITY', reason: 'NOT_YET_ON_THIS_PLATFORM' },
      { term: 'SOCIAL_VIBE', reason: 'NOTHING_FROM_THEM' },
    ],
    modifiers: [{ code: 'CALIBRATION_VALUE', points: 3 }],
    liveness_reasons: ['RECENT_ACTIVITY'],
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
}

function deal({
  candidates = [card('Marek Z.', 'aaaaaaaa-0000-4000-8000-000000000001')],
  playersInRange = 7,
  radiusClamp = false,
  searchId = SEARCH_ID,
  myAreaCode = HERE,
  prompts = [],
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
    outstanding: { sport: 'PADEL', outstanding, cap: 10, ttl_days: 21 },
  };
}

const ME = GATE_USER.id;
const MAREK = 'aaaaaaaa-0000-4000-8000-000000000001';
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
  const marek = { player_id: MAREK, answer: 'ACCEPTED' as const, nickname: 'Marek Z.' };
  const me = { player_id: ME, answer: 'ACCEPTED' as const, nickname: 'ada' };
  const nobody = { player_id: null, answer: null, answer_by: null, nickname: null };
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
  { player_id: MAREK, nickname: 'Marek Z.' },
  { player_id: ME, nickname: 'ada' },
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

/** The spoken *Matched!* for the one card every walk says yes to. */
const MATCHED_SPOKEN = matchedAnnouncement({
  yours: [{ kind: 'person', playerId: ME, nickname: 'ada' }],
  theirs: [{ kind: 'person', playerId: MAREK, nickname: 'Marek Z.' }],
});

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, {
    ratings: [rating('PADEL'), rating('TENNIS')],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubInterest(transport);
  transport.on('POST', DECK, () => json(deal()));
  transport.on('POST', INTEREST, () => json(expressed(false), 201));
  transport.on('POST', PASSES, () => noContent());
  transport.on('POST', DECLINES, () => noContent());
  transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 22 }));
});

afterEach(async () => {
  stopWatchingHardwareBack();
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

describe('what the deck deals', () => {
  it('deals on arrival, for the sport the player is on, and draws one person', async () => {
    await openDeck();

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * **The one sentence a card may write from an `area_code`, end to end**
   * ([#279](https://github.com/Raketa02/Raketa/issues/279)).
   *
   * Both codes come off one response — theirs on the card, yours on the envelope — so this
   * asserts the whole path: the wire, the mapper that folds the searcher's own on, and the
   * line. It is here rather than only over `metaLine`, because the clause was unreachable on
   * every surface for as long as the second code had nothing serving it.
   */
  it('says a candidate is in your area when the two codes agree', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    const line = metaLine({ km: 4, theirAreaCode: HERE, myAreaCode: HERE });

    expect(screen.getByText(line)).toBeTruthy();
  });

  /** A search recorded before the area was kept drops the clause and keeps its kilometres. */
  it('keeps the kilometres and claims no area where the search recorded none', async () => {
    transport.on('POST', DECK, () => json(deal({ myAreaCode: null })));
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByText(metaLine({ km: 4, theirAreaCode: HERE }))).toBeTruthy();
  });

  /**
   * **The deal runs on the profile's week, whatever was improvised on Find a game**
   * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
   * §1). The deck used to be reached from the screen the week is edited on and dealt on the
   * working copy; it is reached from a tab of its own now, the tab press ends the Play session
   * on the way, and the ask carries no override at all — *"omit it, never send `null`"*.
   */
  it('deals on the profile’s week, whatever was improvised on Find a game', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText('Monday morning'));

    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    await screen.findByLabelText(/^Marek Z\./);

    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  it('deals again for a sport the player switches to, and only then', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(dealBodies()[1]).toEqual({ sport: 'TENNIS' });
  });

  /**
   * **A deal is not free, so the screen asks for one once per question and then keeps it.**
   *
   * `POST /deck` excludes everybody already dealt to this player for a day, so a second ask is
   * a *different* ten people — which is what makes *a spent deal deals again* work and what
   * made a re-ask on every chip press ruinous: toggling between two sports emptied a deck
   * nobody had answered a card of, and the ending then said, truthfully, that they had seen
   * everybody.
   */
  it('deals once per sport, however often the chips are toggled', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    fireEvent.press(screen.getByLabelText('Padel'));
    await screen.findByLabelText(/^Marek Z\./);
    fireEvent.press(screen.getByLabelText('Tennis'));
    await screen.findByLabelText(/^Marek Z\./);
    fireEvent.press(screen.getByLabelText('Padel'));
    await screen.findByLabelText(/^Marek Z\./);

    expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]);
  });

  /** Leaving Players replaces the stack, so the screen is genuinely re-entered rather than restored. */
  it('finds the deal it already holds when the player leaves the tab and comes back', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    await leaveAndReturn();

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * The other half of holding the deal: **how far through it the player is is part of it.**
   * Progress left behind on the screen would put every answered card back on arrival.
   */
  it('does not put an answered card back when the screen is re-entered', async () => {
    transport.on('POST', DECK, () =>
      json(
        deal({
          candidates: [
            card('Marek Z.', 'aaaaaaaa-0000-4000-8000-000000000001'),
            card('Ana K.', 'aaaaaaaa-0000-4000-8000-000000000002'),
          ],
        }),
      ),
    );
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
    await screen.findByLabelText(/^Ana K\./);

    await leaveAndReturn();

    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
    expect(screen.queryByLabelText(/^Marek Z\./)).toBeNull();
    expect(dealBodies()).toHaveLength(1);
  });

  /**
   * **A declaration is not part of the question any more.** The deck used to read it where a
   * search reads a mode, so a sport nobody had declared in opened ADR-0094's interstitial
   * before the deal could be refused. Every deal runs under one ruler now (ADR-0169 §2): an
   * undeclared sport deals, and nothing asks what kind of game.
   */
  it('deals a sport nobody has declared in, and asks nothing first', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

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
   * **A refusal is not a reason to deal on the next mount either**, which is the spelling of
   * *nothing in Play retries without the player asking* that a held deal newly needs:
   * `retryOnMount` defaults to true, so an errored query re-fires the moment a second observer
   * mounts — and here that is the player walking to Find a game and back, having pressed
   * nothing. Worse than a wasted request if the refusal was a timeout over a deal the server
   * did record, since the pool is then spent twice.
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

describe('yes and no', () => {
  it('are two named buttons, and the card announces no gesture at all', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByLabelText('Not today, Marek Z.')).toBeTruthy();
    expect(screen.getByLabelText("Let's play, Marek Z.")).toBeTruthy();
    // A swipe would have to be announced to a listener who cannot perform one, and there is
    // no alternative offered because there is no gesture.
    expect(screen.queryByLabelText(/swipe|drag/i)).toBeNull();
  });

  /**
   * The refusal, asserted where it can actually be broken. A build session reaching for a
   * swipe reaches for one of these two libraries first, and neither is a dependency this app
   * has ([#231](https://github.com/Raketa02/Raketa/issues/231) §3).
   */
  it('cost no new gesture dependency', () => {
    const manifest = require('../../../../package.json') as {
      dependencies: Record<string, string>;
    };

    expect(manifest.dependencies['react-native-gesture-handler']).toBeUndefined();
    expect(manifest.dependencies['react-native-reanimated']).toBeUndefined();
  });

  it('sends a yes with the deal it came off, and never a position', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(transport.requestsTo('POST', INTEREST)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
      search_id: SEARCH_ID,
    });
  });

  it('sends a pass the same way, and is told nothing back', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    await waitFor(() => expect(transport.requestsTo('POST', PASSES)).toHaveLength(1));
    expect(transport.requestsTo('POST', PASSES)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
      search_id: SEARCH_ID,
    });
  });

  /**
   * **Today's sentence, verbatim, and nowhere to go**: nothing pretends the other person has
   * been told, and a one-sided yes is not a screen (ADR-0167 §1).
   */
  it('says a one-sided yes is silent, because nobody is told, and stays on the deck', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(toasts()).toEqual([interestToast('Marek Z.')]));
    expect(screen).toHavePathname('/players');
  });

  /**
   * The one thing a yes tells you about the other person, and it is earned: they said it
   * first. The sentence comes off the **response** rather than off the press, which is why
   * the two arms are two runs — a client cannot know which it was until the answer lands.
   *
   * **And a mutual naming nothing is today's toast, verbatim, and no screen**: the pair
   * already have a game being arranged, or a gate refused — one answer, two causes,
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

  it('names the person a pass was about', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    await waitFor(() => expect(toasts()).toEqual([passedToast('Marek Z.')]));
  });

  it('moves to the next card once the one answered has left', async () => {
    transport.on('POST', DECK, () =>
      json(
        deal({
          candidates: [
            card('Marek Z.', 'aaaaaaaa-0000-4000-8000-000000000001'),
            card('Ana K.', 'aaaaaaaa-0000-4000-8000-000000000002'),
          ],
        }),
      ),
    );
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
    expect(screen.queryByLabelText(/^Marek Z\./)).toBeNull();
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

  it('holds an answer made offline rather than failing it, and says so', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    act(() => onlineManager.setOnline(false));
    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
  });
});

/**
 * **A mutual naming a challenge opens the yes screen** — *Matched!* — and the mutual-with-chat
 * toast is retired ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, §4; [#434](https://github.com/Raketa02/Raketa/issues/434)). Walked end to end: the deck,
 * the reply, the screen, and each of its two doors back out.
 */
describe('a mutual that named a challenge', () => {
  const TWO_CARDS = deal({
    candidates: [card('Marek Z.', MAREK), card('Ana K.', 'aaaaaaaa-0000-4000-8000-000000000002')],
  });

  /** A deal of two, and *Let's play* on the first, answered mutual with the named challenge. */
  async function sayYesToMarek(sport: 'TENNIS' | 'PADEL') {
    transport.on('POST', DECK, () => json(TWO_CARDS));
    transport.on('POST', INTEREST, () => json(expressed(true, 3, CHALLENGE), 201));
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () => json(matched(sport)));
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);
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
  /** The initials are hidden from assistive technology on purpose; a query about the drawing says so. */
  const HIDDEN_TOO = { includeHiddenElements: true } as const;

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
    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
    expect(screen.queryByLabelText(/^Marek Z\./)).toBeNull();
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
    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
  });

  /**
   * **The same landing as after a challenge's yes — `[Chats list, the room]` — reached by the
   * tab's own move.** The list is nowhere under the deck, so the shell lays it down and the room
   * is pushed over it: back from the room is the list with nothing behind it, and Play, entered
   * again, finds the deal it dealt on rather than dealing a second one. A tennis mutual is `ON`
   * from birth, so the door waits for the row to carry its game, as the challenge's does.
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
    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]);
  });

  /**
   * **Past the bound the door is the list, from the deck too** — and the list is reached by the
   * tab's own move alone, with no room to push over it: a worker that is down or behind must not
   * dead-end the player on a celebration, and the row will appear where they land.
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
   *
   * Offline rather than a reply simply slow to come: the harness runs every pending timer on
   * every navigation, so a request in flight across the tab press would be timed out by the
   * walk itself rather than answered late by the server.
   */
  it('opens the yes screen when the reply lands after the deck was left', async () => {
    transport.on('POST', DECK, () => json(TWO_CARDS));
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () => json(matched('PADEL')));
    let answer = (_response: Response) => {};
    transport.on('POST', INTEREST, () => new Promise<Response>((resolve) => (answer = resolve)));
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

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

describe('the empty deck', () => {
  it('states the pool and the count of your own yeses, and offers no way back', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    stubInterest(transport, {
      outgoing: [],
      mutual: [],
      outstanding: [{ sport: 'PADEL', outstanding: 2, cap: 10, ttl_days: 21 }],
    });
    await openDeck();

    expect(await screen.findByText(SEEN_EVERYBODY_TITLE)).toBeTruthy();
    expect(
      screen.getByText(
        poolDescription({
          playersInRange: 7,
          radiusKmUsed: 12,
          sportName: 'Padel',
        }),
      ),
    ).toBeTruthy();
    expect(screen.getByText(outgoingYeses(2))).toBeTruthy();

    // The struck control, asserted as an absence — the only way a refusal can be asserted.
    expect(screen.queryByLabelText(/show them again/i)).toBeNull();
  });

  it('reads an empty deal with nobody in range as the other state, and advises widening', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [], playersInRange: 0 })));
    await openDeck();

    expect(await screen.findByText(NOBODY_IN_RANGE_TITLE)).toBeTruthy();
    expect(screen.getByText(WIDEN_IN_YOU)).toBeTruthy();
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

    // The deal is spent, so the screen deals again — and a spent deal is never an ending.
    await waitFor(() => expect(dealBodies()).toHaveLength(2));
    expect(screen.queryByText(WIDEN_IN_YOU)).toBeNull();
  });

  /**
   * *"A spent deal deals again… the screen runs out of cards long before the pool does, and
   * only a fresh deal that comes back empty is the empty state."*
   */
  it('deals again when the last card is answered, and only then shows an ending', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(screen.queryByText(SEEN_EVERYBODY_TITLE)).toBeNull();

    transport.on('POST', DECK, () => json(deal({ candidates: [], searchId: 'second-deal' })));
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));

    expect(await screen.findByText(SEEN_EVERYBODY_TITLE)).toBeTruthy();
  });

  /**
   * The figure the old segment drew still moves on the tap's own answer — it is the **ending
   * sentence** that prints it, which is where it has room to say what it counts.
   */
  it('moves the ending’s own count on the answer’s response rather than on a second request', async () => {
    stubInterest(transport, {
      outgoing: [],
      mutual: [],
      outstanding: [{ sport: 'PADEL', outstanding: 2, cap: 10, ttl_days: 21 }],
    });
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    // The yes spends the hand, so the re-deal that follows lands on the ending.
    transport.on('POST', DECK, () => json(deal({ candidates: [], searchId: 'second-deal' })));
    fireEvent.press(screen.getByLabelText("Let's play, Marek Z."));

    expect(await screen.findByText(outgoingYeses(3))).toBeTruthy();
    // One read, at mount. The tap's answer carried the new count, so nothing asked again.
    expect(transport.requestsTo('GET', INTEREST)).toHaveLength(1);
  });
});

/**
 * **Players, the tab** ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1). The deck is the whole of the second column: no title row, a *Deck | Radar* toggle for a
 * header, chips only where there is a choice, and nothing asking anybody what kind of game.
 */
describe('Players, the tab', () => {
  /**
   * Lit on the deck, from the deck's side: the bar's order and roots are `theShell.test.tsx`'s,
   * and what this adds is that the column the deck lights is Players and not Play.
   */
  it('lights Players and not Play, and is its own root', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByRole('tab', { name: 'Players', selected: true })).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Play', selected: false })).toBeTruthy();
    expect(router.canGoBack()).toBe(false);
  });

  /** No title row: the toggle is the header, and there is no heading element to land on. */
  it('opens on Deck, with the toggle for a header and no title', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByRole('button', { name: PANE_LABEL.deck, selected: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: PANE_LABEL.radar, selected: false })).toBeTruthy();
    expect(screen.queryByRole('header')).toBeNull();
    expect(screen.queryByText(/Match me/)).toBeNull();
  });

  it('flips to a Radar pane that says it is not built, and back', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));

    expect(await screen.findByText(RADAR_LINE)).toBeTruthy();
    expect(screen.queryByLabelText(/^Marek Z\./)).toBeNull();
    expect(screen.getByRole('button', { name: PANE_LABEL.radar, selected: true })).toBeTruthy();
    // A pane and not a route: the toggle moved and the tab did not.
    expect(screen).toHavePathname('/players');

    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.deck }));

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
    expect(screen.queryByText(RADAR_LINE)).toBeNull();
  });

  /** The toggle is the screen's own state, and the screen is remounted on every arrival. */
  it('lands on Deck again after leaving from Radar, because Players always opens on Deck', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByText(RADAR_LINE);

    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
    expect(screen.getByRole('button', { name: PANE_LABEL.deck, selected: true })).toBeTruthy();
    expect(screen.queryByText(RADAR_LINE)).toBeNull();
  });

  /**
   * **Chips only when there is a choice.** Rated in two sports, the row is under the toggle and
   * reads and writes the same browsed sport Play's chips do; rated in one, the mock is seen
   * exactly. Rated in none is *Rate a sport first* — `NO_RATED_SPORT_LINE`, drawn off
   * `sportOnScreen` answering nothing (`domain/findAGame.test.ts`) — and it cannot be walked
   * here: the entry gate sends a player with no rating to the questionnaire before any tab is
   * drawn, which is the reason the screen represents the branch at all.
   */
  it('draws the sport chips for a player rated in two sports, under the toggle', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByText(SPORT_HEADING)).toBeTruthy();
    expect(screen.getByLabelText('Padel')).toBeTruthy();
    expect(screen.getByLabelText('Tennis')).toBeTruthy();
  });

  it('draws no chips for a player rated in one sport', async () => {
    stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.queryByText(SPORT_HEADING)).toBeNull();
    expect(screen.queryByLabelText('Padel')).toBeNull();
    expect(dealBodies()).toEqual([{ sport: 'PADEL' }]);
  });

  /**
   * **Nobody is asked to declare on Players, and nothing says what the deal runs on.** The
   * one-tap card and the *Dealing … · Change* line were the deck's for as long as it read a
   * declaration; every deal runs under one ruler now (ADR-0169 §2), and both are absences.
   */
  it('deals an undeclared player without an interstitial, and draws no standing line', async () => {
    stubProfileSurface(transport, {
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: {},
    });
    await openDeck();

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
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
    await screen.findByLabelText(/^Marek Z\./);

    const line = declarationLine({ intent: 'FOR_FUN', mode: undefined, sportName: 'Padel' });
    expect(screen.queryByLabelText(line.spoken)).toBeNull();
    expect(screen.queryByLabelText(line.actionLabel)).toBeNull();
  });
});

describe('the footer, and what it promises', () => {
  it('says what a pass does, and names the gesture that opens the reading', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    for (const line of DECK_FOOTER) {
      expect(screen.getByText(line)).toBeTruthy();
    }
  });

  it('opens SH.whyfit on a long press, which is what the footer said it would', async () => {
    await openDeck();
    fireEvent(await screen.findByLabelText(/^Marek Z\./), 'longPress');

    expect(await screen.findByLabelText('Why fit 78')).toBeTruthy();
  });
});

/**
 * **The questions a deal raises, and the two things that are different about asking them here.**
 *
 * A deal is not a press — the entry deal is an effect and a spent hand deals again on its own —
 * so *asked once* has to hold across deals rather than across searches. And the deck has no
 * week grid, so the one prompt whose *yes* is a request for one never reaches it
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
   * The half a `search_id` key would get wrong. A spent hand deals again by itself, and the
   * condition a prompt is raised on does not change because ten cards were answered — so a
   * question keyed by the deal would be put in front of the player again every ten cards.
   */
  it('is not asked again by the deal that follows it', async () => {
    transport.on('POST', DECK, () =>
      json(deal({ prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }] })),
    );
    await openDeck();
    await screen.findByText(KEEP_THIS_RADIUS);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));
    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));

    // Answering the last card spends the deal, so the screen deals again — and the second
    // answer raises the same question, off a second `search_id`.
    transport.on('POST', DECK, () =>
      json(
        deal({
          searchId: 'second-deal',
          prompts: [{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }],
        }),
      ),
    );
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
    await waitFor(() => expect(dealBodies()).toHaveLength(2));

    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
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
    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
  });

  /**
   * The half a `prompts[0]`-then-check would lose. Every later list starts with the same
   * leading code, so a screen that picked the first prompt and *then* found it answered would
   * go silent for the rest of the visit with a second question standing right behind it.
   */
  it('asks the question behind it on the deal that follows', async () => {
    const raising = () =>
      json(
        deal({
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

    // Answering the last card spends the deal, so the screen deals again — and the second
    // deal raises the same two questions, the first of which has been answered this visit.
    fireEvent.press(await screen.findByLabelText('Not today, Marek Z.'));
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
    expect(await screen.findByLabelText(/^Marek Z\./)).toBeTruthy();
    expect(screen.queryByText(REFRESH_YOUR_TIMES)).toBeNull();
  });
});
