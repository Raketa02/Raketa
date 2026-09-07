/**
 * **Match me**, walked the way a player walks it: the real route tree, the real shell, the
 * real stores and only `fetch` faked.
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
 * - **The count on the segment is filtered by the sport on screen**, so the number labels the
 *   deck it sits above.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  launchSignedIn,
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

import {
  declarationLine,
  declarationOptionLabel,
  declarationTitle,
  modeControlLabel,
} from './findAGamePresentation';
import {
  DECK_FOOTER,
  MATCH_ME_TITLE,
  NOBODY_IN_RANGE_TITLE,
  SEEN_EVERYBODY_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  mutualToast,
  outgoingYeses,
  passedToast,
} from './deckPresentation';
import { playErrorMessage } from './playErrorMessage';
import { metaLine } from './playerCardPresentation';
import { promptControls, promptCopy } from './promptPresentation';
import { poolDescription } from './searchPresentation';

const DECK = '/api/v1/deck';
const TENNIS_INTENT = '/api/v1/play-intents/TENNIS';
const PADEL_INTENT = '/api/v1/play-intents/PADEL';
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

function expressed(mutual: boolean, outstanding = 3): Wire['ExpressedInterestResponse'] {
  return {
    interest: {
      player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
      sport: 'PADEL',
      at: '2026-09-01T18:00:00Z',
      expires_at: '2026-09-08T18:00:00Z',
    },
    mutual,
    outstanding: { sport: 'PADEL', outstanding, cap: 10 },
  };
}

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
  transport.restore();
  onlineManager.setOnline(true);
  queryClient.clear();
  useToastQueue.getState().clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player standing on the deck, with the first deal already drawn. */
async function openDeck() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  // Find a game's grid is the last thing its three reads produce, so its arrival is the
  // segment being real rather than a control over a half-loaded screen.
  await screen.findByLabelText('Tuesday evening');

  fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
  await waitFor(() => expect(screen).toHavePathname('/play/deck'));
}

const dealBodies = () => transport.requestsTo('POST', DECK).map((request) => request.body);
const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);

describe('what the deck deals', () => {
  it('deals on arrival, for the sport Play is on, and draws one person', async () => {
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
   * The week is an **ask and never a correction**: a grid improvised on Find a game travels
   * as `availability_override`, and a grid that still equals the profile's is omitted rather
   * than sent — *"omit it, never send `null`"*.
   */
  it('sends the improvised week, and omits it when the grid is the profile’s', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText('Monday morning'));

    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
    await waitFor(() => expect(screen).toHavePathname('/play/deck'));
    await screen.findByLabelText(/^Marek Z\./);

    expect(dealBodies()).toEqual([
      {
        sport: 'PADEL',
        availability_override: [
          { day: 2, part: 'EVENING' },
          { day: 6, part: 'MORNING' },
          { day: 1, part: 'MORNING' },
        ],
      },
    ]);
  });

  it('deals again for a sport the player switches to, and only then', async () => {
    stubProfileSurface(transport, {
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: { PADEL: 'FOR_FUN', TENNIS: 'COMPETITIVE' },
    });
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
    stubProfileSurface(transport, {
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: { PADEL: 'FOR_FUN', TENNIS: 'COMPETITIVE' },
    });
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

  /** Leaving Match me replaces the stack, so the screen is genuinely re-entered rather than restored. */
  it('finds the deal it already holds when the player leaves the screen and comes back', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Find a game'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
    await waitFor(() => expect(screen).toHavePathname('/play/deck'));

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

    fireEvent.press(screen.getByLabelText('Find a game'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));

    expect(await screen.findByLabelText(/^Ana K\./)).toBeTruthy();
    expect(screen.queryByLabelText(/^Marek Z\./)).toBeNull();
    expect(dealBodies()).toHaveLength(1);
  });

  /**
   * **A week is part of the question**, so improvising one is a new ask and deals again. Held
   * on the sport alone, a grid the player had just edited would be silently answered by the
   * deal that ran before it.
   */
  it('deals again on an improvised week, because that is a different ask', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Find a game'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText('Monday morning'));
    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
    await screen.findByLabelText(/^Marek Z\./);

    await waitFor(() => expect(dealBodies()).toHaveLength(2));
    expect(dealBodies()[1]).toHaveProperty('availability_override');
  });

  /**
   * The deck has **no mode**, so it reads the declaration — and is refused with
   * `play_intent_not_declared` without one. ADR-0094's interstitial is therefore opened
   * knowingly, before the refusal, on this surface exactly as on the search screen.
   */
  it('asks what kind of game before dealing a sport nobody has declared in', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Tennis'));

    expect(await screen.findByText(declarationTitle('Tennis'))).toBeTruthy();
    expect(dealBodies()).toHaveLength(1);
  });

  /**
   * The surface is the deck's own — [#280](https://github.com/Raketa02/Raketa/issues/280).
   * The interstitial is one component with two callers, and the field whose whole job is to
   * say which screen it was is the one thing that must differ between them. It is asserted
   * from the outside because it is a value with no effect on this screen: nothing here reads
   * it back, so nothing but this would notice the two callers reporting the same screen.
   */
  it('reports the deck as the surface it was declared on', async () => {
    transport.on('PUT', TENNIS_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({ sport: 'TENNIS', intent: 'FOR_FUN' }),
    );
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);
    fireEvent.press(screen.getByLabelText('Tennis'));
    await screen.findByText(declarationTitle('Tennis'));

    fireEvent.press(screen.getByLabelText(declarationOptionLabel('FOR_FUN', 'Tennis')));

    await waitFor(() => expect(transport.requestsTo('PUT', TENNIS_INTENT)).toHaveLength(1));
    expect(transport.requestsTo('PUT', TENNIS_INTENT)[0]?.body).toEqual({
      intent: 'FOR_FUN',
      surface: 'DECK',
    });
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
  it('does not deal again when a screen whose deal was refused is re-entered', async () => {
    transport.on('POST', DECK, () => errorResponse(503, 'matchmaking_unavailable'));
    await openDeck();
    await screen.findByText(playErrorMessage({ code: 'matchmaking_unavailable' } as never));

    fireEvent.press(screen.getByLabelText('Find a game'));
    await screen.findByLabelText('Tuesday evening');
    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
    await waitFor(() => expect(screen).toHavePathname('/play/deck'));
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

  it('says a one-sided yes is silent, because nobody is told', async () => {
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(toasts()).toEqual([interestToast('Marek Z.')]));
  });

  /**
   * The one thing a yes tells you about the other person, and it is earned: they said it
   * first. The sentence comes off the **response** rather than off the press, which is why
   * the two arms are two runs — a client cannot know which it was until the answer lands.
   */
  it('tells a mutual to both sides', async () => {
    transport.on('POST', INTEREST, () => json(expressed(true)));
    await openDeck();
    fireEvent.press(await screen.findByLabelText("Let's play, Marek Z."));

    await waitFor(() => expect(toasts()).toEqual([mutualToast('Marek Z.')]));
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

describe('the empty deck', () => {
  it('states the pool and the count of your own yeses, and offers no way back', async () => {
    transport.on('POST', DECK, () => json(deal({ candidates: [] })));
    stubInterest(transport, {
      outgoing: [],
      mutual: [],
      outstanding: [{ sport: 'PADEL', outstanding: 2, cap: 10 }],
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
});

describe('the segment', () => {
  /**
   * **The count is struck**, and the refusal is only observable as an absence. `Match me · 3`
   * sat where a count of *cards waiting* would sit and was read as one — which is the number
   * the deck refuses to publish anywhere, the card included.
   */
  it('names the deck and puts no number beside it, on either screen', async () => {
    stubInterest(transport, {
      outgoing: [],
      mutual: [],
      outstanding: [
        { sport: 'PADEL', outstanding: 3, cap: 10 },
        { sport: 'TENNIS', outstanding: 9, cap: 10 },
      ],
    });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await screen.findByLabelText('Tuesday evening');

    expect(await screen.findByLabelText(MATCH_ME_TITLE)).toBeTruthy();
    expect(screen.queryByLabelText(/yeses/)).toBeNull();
    expect(screen.queryByText(/Match me ·/)).toBeNull();

    fireEvent.press(screen.getByLabelText(MATCH_ME_TITLE));
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByLabelText(MATCH_ME_TITLE)).toBeTruthy();
    expect(screen.queryByText(/Match me ·/)).toBeNull();
  });

  /**
   * The figure the segment used to draw still moves on the tap's own answer — it is the
   * **ending sentence** that prints it now, which is where it has room to say what it counts.
   */
  it('moves the ending’s own count on the answer’s response rather than on a second request', async () => {
    stubInterest(transport, {
      outgoing: [],
      mutual: [],
      outstanding: [{ sport: 'PADEL', outstanding: 2, cap: 10 }],
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

  it('takes the player back to Find a game as an arrival rather than a step back', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Find a game'));

    await waitFor(() => expect(screen).toHavePathname('/play'));
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

  /**
   * The bar reads its active column off the **first** path segment, so ⚡Play stays lit for
   * every screen inside Play — which is what the deck being `/play/deck` rather than a route
   * of its own buys.
   */
  it('keeps ⚡Play lit, because the deck is inside the tab', async () => {
    await openDeck();

    expect(screen.getByLabelText('Play').props.accessibilityState?.selected).toBe(true);
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

/**
 * **The declaration at rest on the second Play surface**
 * ([#295](https://github.com/Raketa02/Raketa/issues/295)).
 *
 * The deck is the one screen in the product where the durable answer *is* what the search runs
 * on — `SearchEnvelope.mode` is null exactly here — so the line has one state and no drift
 * variant. What is asserted is mostly that absence, which is only observable from outside.
 */
describe('the declaration, standing where there is no mode', () => {
  /** The line as the copy deck writes it, so an assertion is never a spelling of one. */
  const dealing = (intent: Wire['PlayIntent'], sportName: string) =>
    declarationLine({ intent, mode: undefined, sportName });

  const DEALT = dealing('FOR_FUN', 'Padel');

  it('says the deal runs on what the profile holds, under the chips it is chosen by', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    expect(screen.getByLabelText(DEALT.spoken)).toBeTruthy();
    expect(screen.getByLabelText(DEALT.actionLabel)).toBeTruthy();
  });

  /**
   * There is nothing on this screen for the declaration to disagree with — no segment, and
   * therefore no `differs` state and no *Update*. The absence of the control is the reason the
   * sentence can be written the way it is.
   */
  it('has no drift variant, because there is no switch to drift from', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    for (const mode of ['COMPETITIVE', 'FOR_FUN'] as const) {
      expect(screen.queryByLabelText(modeControlLabel(mode))).toBeNull();
      expect(
        screen.queryByLabelText(
          declarationLine({ intent: 'FOR_FUN', mode, sportName: 'Padel' }).spoken,
        ),
      ).toBeNull();
    }
    expect(DEALT.action).toBe('Change');
  });

  /**
   * The chip is what chooses which declaration is being read, and *either suits me* gets a frame
   * of its own — `declarationNamesAKind` is where that is argued, and
   * `findAGamePresentation.test` is where the two frames are compared. What this adds is that
   * the right one reaches the screen.
   */
  it('follows the chip, and claims no kind for an answer that named none', async () => {
    stubProfileSurface(transport, {
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: { PADEL: 'COMPETITIVE', TENNIS: 'NO_PREFERENCE' },
    });
    await openDeck();
    await screen.findByLabelText(dealing('COMPETITIVE', 'Padel').spoken);

    fireEvent.press(screen.getByLabelText('Tennis'));

    expect(await screen.findByLabelText(dealing('NO_PREFERENCE', 'Tennis').spoken)).toBeTruthy();
    expect(screen.queryByLabelText(dealing('FOR_FUN', 'Tennis').spoken)).toBeNull();
  });

  /**
   * *Change* means one thing across the tab: the declaration's home is the You tab (#296), and
   * the deck does not grow a second editor for it any more than it grows one for the radius.
   */
  it('sends Change to where the declaration lives, and writes nothing on the way', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText(DEALT.actionLabel));

    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(transport.requestsTo('PUT', PADEL_INTENT)).toEqual([]);
    expect(transport.requestsTo('PUT', TENNIS_INTENT)).toEqual([]);
  });

  /** An undeclared sport is the interstitial's state, and there is nothing yet to stand for. */
  it('is not drawn at all on a sport nobody has declared in', async () => {
    await openDeck();
    await screen.findByLabelText(/^Marek Z\./);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await screen.findByText(declarationTitle('Tennis'));

    for (const intent of ['COMPETITIVE', 'FOR_FUN', 'NO_PREFERENCE'] as const) {
      expect(screen.queryByLabelText(dealing(intent, 'Tennis').spoken)).toBeNull();
    }
  });
});
