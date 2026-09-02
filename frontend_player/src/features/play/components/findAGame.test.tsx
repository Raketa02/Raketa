/**
 * **Find a game**, walked the way a player walks it: the real route tree, the real shell, the
 * real stores and only `fetch` faked.
 *
 * The screen holds four facts with four different lifetimes, and every assertion below is
 * about one of them being kept — or, more often, about a write that must **not** happen. That
 * asymmetry is the ticket: a sport, a mode and a week edited here reach the server as an *ask*
 * on one search and never as a change to the player, and a suite that only checked the search
 * body would pass on a screen that quietly rewrote the profile every time somebody tried a
 * different Tuesday.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { offlineMessage } from '@/shared/errors';
import { courtSeatCount } from '@/shared/ui';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  stubGate,
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
import { endPlaySession } from '../store/playSession.store';

import { courtSummaryLabel } from './accessibilityPresentation';
import { playErrorMessage } from './playErrorMessage';
import { poolRankingStatus } from './searchingPresentation';
import { searchingFloorMs } from './searchingWait';
import {
  DECLARATION_BODY,
  NOBODY_IS_CONTACTED_BY_SEARCHING,
  RADIUS_IS_YOUR_PROFILE,
  WEEK_CHANGED_FROM_PROFILE,
  courtEntrySeatLine,
  courtEntryTag,
  courtEntryTitle,
  declarationTitle,
  searchControlLabel,
} from './findAGamePresentation';

const SEARCHES = '/api/v1/searches';
const RADIUS = '/api/v1/players/me/search-radius';
const PADEL_INTENT = '/api/v1/play-intents/PADEL';
const AVAILABILITY = '/api/v1/players/me/availability';

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

function shortlist(): Wire['ShortlistResponse'] {
  return {
    search: {
      search_id: 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
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
    },
    candidates: [],
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
  transport.on('POST', SEARCHES, () => json(shortlist()));
});

afterEach(async () => {
  transport.restore();
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  queryClient.clear();
  // The process-scoped store outlives a visit by design, so a suite has to stand in for the
  // process ending — which is the only thing that clears it.
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player, standing on Find a game with the profile read landed. */
async function openPlay(surface?: Wire['PlayerProfileReadResponse']) {
  if (surface !== undefined) stubProfileSurface(transport, surface);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  // The grid is the last thing the three reads produce, so its arrival is the screen's.
  await screen.findByLabelText('Tuesday evening');
}

/** Padel seats four, read off `Court`'s own coordinates rather than typed here. */
const PADEL_SEATS = courtSeatCount('padel');
const COURT_CARD = searchControlLabel(
  { kind: 'searchable', sport: 'padel' },
  {
    seats: PADEL_SEATS,
  },
);

const cell = (name: string) => screen.getByLabelText(name);
const isTicked = (name: string) => cell(name).props.accessibilityState?.checked === true;
const isSelected = (label: string) =>
  screen.getByLabelText(label).props.accessibilityState?.selected === true;
const searchButton = () =>
  screen.getByLabelText(
    searchControlLabel({ kind: 'searchable', sport: 'padel' }, { seats: PADEL_SEATS }) ?? '',
  );

const SEARCHING = poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' }).headline;

/**
 * Spend the floor, and wait for the latch to lift.
 *
 * Nothing behind it is reachable while it is up — it spreads `behindOverlay`, and a query that
 * does not ask for hidden elements will not find a screen that has hidden itself — so every
 * assertion about *Find a game* after a search goes through here. The clock is **driven**
 * rather than waited on: `expo-router/testing-library` installs jest's fake timers, and a
 * floor that is only asserted by elapsing is a floor no suite can afford to have lengthened.
 */
const latchLifted = async () => {
  await screen.findByText(SEARCHING);
  act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));
  await waitFor(() => expect(screen.queryByText(SEARCHING)).toBeNull());
};

/** Every request that would have changed the player rather than asked the engine something. */
const profileWrites = () => [
  ...transport.requestsTo('PUT', RADIUS),
  ...transport.requestsTo('PUT', AVAILABILITY),
  ...transport.requestsTo('PUT', PADEL_INTENT),
];

describe('what the screen opens on', () => {
  it('offers the sports the player is rated in, and opens on the first', async () => {
    await openPlay();

    expect(isSelected('Padel')).toBe(true);
    expect(screen.getByLabelText('Tennis')).toBeTruthy();
    expect(screen.queryByLabelText('Squash')).toBeNull();
  });

  /**
   * `mode_for_intent`, and the arity gap under it: a player who declared that either kind of
   * evening suits them is **not** searching in a third mode — `NO_PREFERENCE` inherits, and
   * where there is nothing to inherit from the mapping takes *for fun*.
   */
  it('opens the mode on the declaration', async () => {
    await openPlay({
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: { PADEL: 'NO_PREFERENCE' },
    });

    expect(isSelected('For fun, this search')).toBe(true);
    expect(isSelected('Competitive, this search')).toBe(false);
  });

  it('opens on a declared competitive intent', async () => {
    await openPlay({
      availability: [{ day: 2, part: 'EVENING' }],
      search_radius_km: 12,
      play_intents: { PADEL: 'COMPETITIVE' },
    });

    expect(isSelected('Competitive, this search')).toBe(true);
  });

  it('arrives with the grid already filled in from the profile', async () => {
    await openPlay();

    expect(isTicked('Tuesday evening')).toBe(true);
    expect(isTicked('Saturday morning')).toBe(true);
    expect(isTicked('Monday morning')).toBe(false);
  });
});

describe('what the screen never writes', () => {
  it('changes the sport and the mode without touching the profile', async () => {
    await openPlay();

    fireEvent.press(screen.getByLabelText('Tennis'));
    fireEvent.press(screen.getByLabelText('Competitive, this search'));

    await waitFor(() => expect(isSelected('Tennis')).toBe(true));
    expect(isSelected('Competitive, this search')).toBe(true);
    // ADR-0094's drift backstop is written for the sticky-tab case, so the toggle and the
    // declaration have to be able to disagree — which they cannot if this writes.
    expect(profileWrites()).toEqual([]);
  });

  it('edits the week without touching the profile', async () => {
    await openPlay();

    fireEvent.press(cell('Monday morning'));

    await waitFor(() => expect(isTicked('Monday morning')).toBe(true));
    expect(profileWrites()).toEqual([]);
  });
});

describe('changed from your profile', () => {
  it('is silent while the week is the profile’s', async () => {
    await openPlay();

    expect(screen.queryByText(WEEK_CHANGED_FROM_PROFILE)).toBeNull();
  });

  it('appears the moment a cell moves', async () => {
    await openPlay();

    fireEvent.press(cell('Monday morning'));

    expect(await screen.findByText(WEEK_CHANGED_FROM_PROFILE)).toBeTruthy();
  });

  /**
   * The comparison, made on every tap rather than a flag a toggle sets.
   *
   * A slot ticked on and off again is not a changed week, and anything that recorded *the
   * player touched the grid* would report it as changed for the rest of the visit.
   */
  it('goes away again when the cell is put back', async () => {
    await openPlay();

    fireEvent.press(cell('Monday morning'));
    await screen.findByText(WEEK_CHANGED_FROM_PROFILE);

    fireEvent.press(cell('Monday morning'));

    await waitFor(() => expect(screen.queryByText(WEEK_CHANGED_FROM_PROFILE)).toBeNull());
  });
});

describe('the way onto the court', () => {
  /** Both sports declared, so switching the chip stays searchable rather than opening the
   *  interstitial — the fact under test is the court's shape and not the declaration. */
  const BOTH_DECLARED: Wire['PlayerProfileReadResponse'] = {
    availability: [{ day: 2, part: 'EVENING' }],
    search_radius_km: 12,
    play_intents: { PADEL: 'FOR_FUN', TENNIS: 'FOR_FUN' },
  };

  /**
   * *The four* is a word about a Sport, and the chip is what changes it.
   *
   * Padel seats four and tennis two, so the same control has to say two different things
   * about two different courts — the bug this screen shipped with was that it said neither,
   * and a player pressing *Search* found out what shape the court was one screen later.
   */
  it('draws the court the sport actually plays on, and swaps it with the chip', async () => {
    await openPlay(BOTH_DECLARED);

    expect(screen.getByText(courtEntryTitle(4))).toBeTruthy();
    expect(screen.getByText(courtEntryTag({ seats: 4, sportName: 'Padel' }))).toBeTruthy();
    expect(screen.getByText(courtEntrySeatLine(4))).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Tennis'));

    expect(await screen.findByText(courtEntryTitle(2))).toBeTruthy();
    expect(screen.getByText(courtEntryTag({ seats: 2, sportName: 'Tennis' }))).toBeTruthy();
    expect(screen.queryByText(courtEntryTitle(4))).toBeNull();
  });

  /**
   * One way through, and the sentence that makes a picture of four seats safe to draw.
   *
   * A card and a *Search* button beside it would be two controls for one act; the card is
   * the control, so the verb is nowhere on the screen.
   */
  it('is the only control, and says nobody is contacted by pressing it', async () => {
    await openPlay();

    expect(screen.getByText(NOBODY_IS_CONTACTED_BY_SEARCHING)).toBeTruthy();
    expect(screen.queryByLabelText('Search')).toBeNull();
  });
});

describe('the search', () => {
  it('sends the sport and the mode, and no week at all where none was improvised', async () => {
    await openPlay();

    fireEvent.press(searchButton());

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1));
    const [request] = transport.requestsTo('POST', SEARCHES);
    expect(request?.body).toEqual({ sport: 'PADEL', mode: 'FOR_FUN' });
  });

  it('sends the improvised week as the override, and still writes nothing', async () => {
    await openPlay();

    fireEvent.press(cell('Monday morning'));
    fireEvent.press(searchButton());

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1));
    const [request] = transport.requestsTo('POST', SEARCHES);
    expect(request?.body).toMatchObject({
      availability_override: [
        { day: 2, part: 'EVENING' },
        { day: 6, part: 'MORNING' },
        { day: 1, part: 'MORNING' },
      ],
    });
    expect(profileWrites()).toEqual([]);
  });

  /** #247, from the screen: a blank grid is a legal answer and the search runs on it. */
  it('runs on a cleared week', async () => {
    await openPlay();

    fireEvent.press(cell('Tuesday evening'));
    fireEvent.press(cell('Saturday morning'));
    await waitFor(() => expect(isTicked('Tuesday evening')).toBe(false));

    fireEvent.press(searchButton());

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1));
    const [request] = transport.requestsTo('POST', SEARCHES);
    expect(request?.body).toMatchObject({ availability_override: [] });
  });

  /**
   * The one control on this screen whose value only reaches the engine through the profile.
   *
   * `RunSearchRequest` carries no radius, so a slider that did not write would be a distance
   * drawn on screen and used by nothing.
   */
  it('writes the radius the slider shows, before it searches', async () => {
    transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 13 }));
    await openPlay();

    fireEvent(screen.getByLabelText('How far to look'), 'accessibilityAction', {
      nativeEvent: { actionName: 'increment' },
    });
    fireEvent.press(searchButton());

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS)[0]?.body).toEqual({ search_radius_km: 13 });
  });

  /**
   * *Clamped where the server clamps it* — on the way **back** as well as on the way out.
   *
   * The write path re-checks the range and the step and answers with the radius as the profile
   * now holds it. A chosen value left standing on the screen would shadow that: the slider
   * would draw a distance nobody holds, and the next search would re-send the number the
   * server had already corrected away.
   */
  it('draws the radius the server kept, not the one the slider sent', async () => {
    transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 9 }));
    await openPlay();

    fireEvent(screen.getByLabelText('How far to look'), 'accessibilityAction', {
      nativeEvent: { actionName: 'increment' },
    });
    fireEvent.press(searchButton());
    await latchLifted();

    // The wait lifted onto the court, so coming back to the search screen is an **arrival** —
    // which is what the segment's *Find a game* half and ⚡ both are (#261).
    fireEvent.press(screen.getByLabelText('Play'));

    await waitFor(() =>
      expect(screen.getByLabelText('How far to look').props.accessibilityValue.now).toBe(9),
    );

    // And the corrected number is not re-sent: the second search finds the profile already
    // holding what the slider shows, so there is nothing to write.
    fireEvent.press(searchButton());

    await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(2));
    expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1);
  });

  /** The slider writes, and the screen says so rather than moving a durable value quietly. */
  it('says the radius is kept on the profile', async () => {
    await openPlay();

    expect(screen.getByText(RADIUS_IS_YOUR_PROFILE)).toBeTruthy();
  });

  /** The scale ends at a value the write path accepts, so the top cannot be over-driven. */
  it('holds the slider inside the bounds the server serves', async () => {
    await openPlay();

    const slider = screen.getByLabelText('How far to look');
    expect(slider.props.accessibilityValue).toMatchObject({ min: 1, max: 50, now: 12 });

    for (let press = 0; press < 60; press += 1) {
      fireEvent(slider, 'accessibilityAction', { nativeEvent: { actionName: 'increment' } });
    }

    await waitFor(() =>
      expect(screen.getByLabelText('How far to look').props.accessibilityValue.now).toBe(50),
    );
  });

  /**
   * A retry belongs to the act that failed. Nothing was minted, so `retryTarget` answers
   * *the-search* and the control the player already pressed is the retry — which is why the
   * sentence appears beside it rather than a second button appearing under it.
   */
  it('says what a refusal means, over the control that failed', async () => {
    transport.on('POST', SEARCHES, () => errorResponse(503, 'matchmaking_unavailable'));
    await openPlay();

    fireEvent.press(searchButton());

    expect(
      await screen.findByText(
        playErrorMessage({ code: 'matchmaking_unavailable' } as never) as string,
      ),
    ).toBeTruthy();
    expect(searchButton()).toBeTruthy();
  });
});

/**
 * The latch — *where the wait happens*, and the four things #269 fixed about it.
 *
 * It is asserted through the real screen because three of the four are only true **in
 * relation to the screen underneath**: that it covers it, that it lets go of it on a refusal,
 * and that it never becomes a place to be stranded.
 */
describe('the searching latch', () => {
  /** A request that never answers, so the wait can be looked at while it is still a wait. */
  const hangs = () => transport.on('POST', SEARCHES, () => new Promise<never>(() => undefined));

  it('covers the screen that launched it, and says what is happening', async () => {
    hangs();
    await openPlay();

    fireEvent.press(searchButton());

    expect(await screen.findByText(SEARCHING)).toBeTruthy();
    // The screen is behind an overlay that hides its descendants, which is the half of
    // *modal* a `Modal` cannot do for the tree it left behind.
    expect(screen.queryByText(RADIUS_IS_YOUR_PROFILE)).toBeNull();
  });

  /**
   * §B14's count came off a 650 ms timer, before the response existed. There is no number
   * here to print, because the only place one could come from has not answered.
   */
  it('prints no count while the response does not exist', async () => {
    hangs();
    await openPlay();

    fireEvent.press(searchButton());
    await screen.findByText(SEARCHING);

    expect(screen.queryByText(/in range/)).toBeNull();
  });

  /** And the number it does print is `players_in_range`, off the answer it waited for. */
  it('prints the pool’s own count once the response exists', async () => {
    await openPlay();

    fireEvent.press(searchButton());

    expect(await screen.findByText('7 in range for Padel')).toBeTruthy();
    // Readable at all only because the floor outlives an answer that arrives inside it —
    // §J6's *"so a fast answer does not flash past."*
    expect(screen.queryByText(SEARCHING)).not.toBeNull();
  });

  /**
   * It is a latch and not a destination, so there is nothing on it to press — no back, no
   * close, no cancel. The prototype's dead end was dissolved by binding the wait to the
   * response, not by furnishing it with a way out.
   */
  it('offers nothing to press', async () => {
    hangs();
    await openPlay();

    fireEvent.press(searchButton());
    await screen.findByText(SEARCHING);

    expect(screen.queryByRole('button')).toBeNull();
  });

  /**
   * A refusal has nothing to hold for: the wait ends, the screen comes back, and the sentence
   * is over the control that failed — `retryTarget`'s *the-search*, which is the button the
   * player already pressed.
   */
  it('lets go of the screen the moment the search is refused', async () => {
    transport.on('POST', SEARCHES, () => errorResponse(503, 'matchmaking_unavailable'));
    await openPlay();

    fireEvent.press(searchButton());

    expect(
      await screen.findByText(
        playErrorMessage({ code: 'matchmaking_unavailable' } as never) as string,
      ),
    ).toBeTruthy();
    expect(screen.queryByText(SEARCHING)).toBeNull();
  });

  /**
   * A paused request is not one in flight. `networkMode: 'online'` holds the search until the
   * connection returns, and a latch over that would bury the sentence that says so under a
   * screen with no way off it — which is the dead end again, arriving by a different door.
   */
  it('does not go up over a search the connection has paused', async () => {
    await openPlay();
    onlineManager.setOnline(false);

    fireEvent.press(searchButton());

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(screen.queryByText(SEARCHING)).toBeNull();
  });

  /**
   * **The case a fast stub cannot reach.** The floor runs from the answer, not from the press,
   * so a search slower than the floor prints its count for exactly as long as an instant one
   * does. Anchored the other way this assertion is zero milliseconds long, the number is drawn
   * for no frames, and §20.11's *announces the result once* announces nothing.
   */
  it('prints the count on a search that took longer than the floor', async () => {
    let answer = () => undefined as void;
    transport.on(
      'POST',
      SEARCHES,
      () => new Promise<Response>((resolve) => (answer = () => resolve(json(shortlist())))),
    );
    await openPlay();

    fireEvent.press(searchButton());
    await screen.findByText(SEARCHING);

    // Long past the floor, and still nothing to print: the wait is the request's.
    act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' }) * 3));
    expect(screen.queryByText(SEARCHING)).not.toBeNull();
    expect(screen.queryByText(/in range/)).toBeNull();

    answer();

    expect(await screen.findByText('7 in range for Padel')).toBeTruthy();
    await latchLifted();
  });

  /**
   * And it lifts on its own, without anybody asking it to — **onto the court**.
   *
   * The two halves are one assertion. A latch is *over the screen that launched it* rather than
   * a route, so the beat that holds the count is spent here and the builder is what is
   * underneath when it goes ([#271](https://github.com/Raketa02/Raketa/issues/271)). Pushed on
   * the response instead, the number would be printed over a screen already left behind.
   */
  it('lifts onto the builder, which is where a finished search goes', async () => {
    await openPlay();

    fireEvent.press(searchButton());
    await screen.findByText(SEARCHING);
    await latchLifted();

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    // And it arrived carrying the id the search minted, which is the only thing that could
    // have found the record this court is drawn from — an empty padel court, seating you.
    expect(
      await screen.findByLabelText(courtSummaryLabel({ sportName: 'Padel', filled: 1, seats: 4 })),
    ).toBeTruthy();
  });
});

describe('a sport nobody has declared in', () => {
  const UNDECLARED: Wire['PlayerProfileReadResponse'] = {
    availability: [{ day: 2, part: 'EVENING' }],
    search_radius_km: 12,
    play_intents: {},
  };

  /**
   * ADR-0094's one-tap interstitial — *"permanent, not a migration path"*. It is opened
   * knowingly, before `play_intent_not_declared` refuses, off a set difference the screen
   * already holds: rated, and absent from the declaration map.
   */
  it('asks before the search would be refused, and says what answering buys', async () => {
    await openPlay(UNDECLARED);

    expect(screen.getByText(declarationTitle('Padel'))).toBeTruthy();
    expect(screen.getByText(DECLARATION_BODY)).toBeTruthy();
    expect(screen.queryByLabelText(COURT_CARD ?? '')).toBeNull();
    expect(
      screen.getByLabelText(
        searchControlLabel({ kind: 'undeclared', sport: 'padel' }, { seats: PADEL_SEATS }) ?? '',
      ),
    ).toBeTruthy();
  });

  it('opens the search once the question is answered', async () => {
    transport.on('PUT', PADEL_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({
        sport: 'PADEL',
        intent: 'NO_PREFERENCE',
      }),
    );
    await openPlay(UNDECLARED);

    fireEvent.press(screen.getByLabelText('Either suits me, your usual at Padel'));

    await waitFor(() => expect(transport.requestsTo('PUT', PADEL_INTENT)).toHaveLength(1));
    expect(transport.requestsTo('PUT', PADEL_INTENT)[0]?.body).toEqual({
      intent: 'NO_PREFERENCE',
      surface: 'SEARCH_SWITCH',
    });
    expect(await screen.findByLabelText(COURT_CARD ?? '')).toBeTruthy();
  });
});
