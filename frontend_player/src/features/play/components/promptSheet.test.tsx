/**
 * **`SH.saveav`**, walked the way a player walks it: the real screen, the real search, the
 * real sheet, and only `fetch` faked.
 *
 * Four things are asserted here and none of them is the wording — the copy deck's own suite
 * holds that. **Where each answer lands**: a *yes* is a `PUT` through the route that owns the
 * value and never a decline, a *not now* is a row about the question and never a value.
 * **That dismissal is an answer**, because a question nobody answers is a question asked
 * forever. **That the sheet cannot precede the search**, which is what makes *"either way the
 * search runs now"* true. And **that a cleared week is drawn rather than described**, on the
 * one prompt where the whole grid is the dropped half.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { onlineManager } from '@tanstack/react-query';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { courtSeatCount } from '@/shared/ui';
import {
  launchIntoClassicPlay,
  stubGate,
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

import { playErrorMessage } from './playErrorMessage';
import { promptControls, promptCopy, PROMPT_CLOSER } from './promptPresentation';
import { searchControlLabel } from './findAGamePresentation';
import { searchingFloorMs } from './searchingWait';

const SEARCHES = '/api/v1/searches';
const DECLINES = '/api/v1/prompt-declines';
const AVAILABILITY = '/api/v1/players/me/availability';
const RADIUS = '/api/v1/players/me/search-radius';
const PADEL_INTENT = '/api/v1/play-intents/PADEL';

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

/** A search that raised these questions. The profile's own week is Tue evening + Sat morning. */
function shortlist(
  prompts: Wire['PromptSchema'][],
  searchId = 'e0f1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b',
): Wire['ShortlistResponse'] {
  return {
    search: {
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
      prompts,
    },
    candidates: [],
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  transport.on('POST', DECLINES, () => noContent());
  transport.on('PUT', AVAILABILITY, () =>
    json<Wire['AvailabilityResponse']>({ availability: [{ day: 1, part: 'MORNING' }] }),
  );
  transport.on('PUT', RADIUS, () => json<Wire['SearchRadiusResponse']>({ search_radius_km: 22 }));
  transport.on('PUT', PADEL_INTENT, () =>
    json<Wire['PlayIntentDeclarationResponse']>({ sport: 'PADEL', intent: 'COMPETITIVE' }),
  );
});

afterEach(async () => {
  transport.restore();
  onlineManager.setOnline(true);
  queryClient.clear();
  usePlayPreferences.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Padel seats four, read off `Court`'s own coordinates rather than typed here. */
const PADEL_SEATS = courtSeatCount('padel');

const searchControl = () =>
  screen.getByLabelText(
    searchControlLabel(
      { kind: 'searchable', sport: 'padel', intent: 'FOR_FUN' },
      { seats: PADEL_SEATS },
    ) ?? '',
  );

/** Press *Search* and spend the floor, so the latch lifts onto whatever comes next. */
async function pressSearch(ran: number) {
  fireEvent.press(searchControl());
  await waitFor(() => expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(ran));
  act(() => jest.advanceTimersByTime(searchingFloorMs({ kind: 'pool' })));
}

/** Sign in and stand on Find a game with the profile read landed. */
async function openPlay() {
  await launchIntoClassicPlay(transport);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  await screen.findByLabelText('Tuesday evening');
}

/** …and run a search that raises `prompts`. */
async function search(prompts: Wire['PromptSchema'][]) {
  transport.on('POST', SEARCHES, () => json(shortlist(prompts)));

  await openPlay();
  await pressSearch(1);
}

const KEEP_THESE_TIMES = promptCopy({
  prompt: 'KEEP_THESE_TIMES',
  week: [],
  profileWeek: [],
}).title;

/** The week `stubProfileSurface` serves — Tuesday evening and Saturday morning. */
const PROFILE_WEEK = [
  { day: 2, part: 'evening' },
  { day: 6, part: 'morning' },
] as const;

const profileWrites = () => [
  ...transport.requestsTo('PUT', RADIUS),
  ...transport.requestsTo('PUT', AVAILABILITY),
  ...transport.requestsTo('PUT', PADEL_INTENT),
];

describe('the question a search raised', () => {
  it('is asked after the search has run, which is what makes it never block', async () => {
    await search([{ prompt: 'KEEP_THESE_TIMES', slots: [{ day: 2, part: 'EVENING' }] }]);

    // The sheet is on screen and the search it is about is already recorded. There is
    // nothing left for a dismissal to swallow, which is the whole of §F2's closer.
    expect(await screen.findByText(KEEP_THESE_TIMES)).toBeTruthy();
    expect(transport.requestsTo('POST', SEARCHES)).toHaveLength(1);
    expect(screen.getByText(PROMPT_CLOSER, { exact: false })).toBeTruthy();
  });

  /** The response orders them so that the first one a client understands is a stable choice. */
  it('asks the first of several, and only that one', async () => {
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }, { prompt: 'REFRESH_YOUR_TIMES' }]);

    expect(await screen.findByText('Keep 22 km?')).toBeTruthy();
    expect(screen.queryByText('Is this week still right?')).toBeNull();
  });

  it('asks nothing where the search raised nothing, and goes straight to the court', async () => {
    await search([]);

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  });

  /**
   * The count is asserted by the copy deck; what is asserted here is that the marks the
   * sentence names are **drawn** — a plus on what the search added, a dash on what it
   * dropped, and nothing at all on a slot that was off and stayed off.
   */
  it('draws the week the search ran on against the week on the profile', async () => {
    await search([
      {
        prompt: 'KEEP_THESE_TIMES',
        slots: [
          { day: 2, part: 'EVENING' },
          { day: 1, part: 'MORNING' },
        ],
      },
    ]);
    await screen.findByText(KEEP_THESE_TIMES);

    expect(screen.getByLabelText('Monday morning, newly added')).toBeTruthy();
    expect(screen.getByLabelText('Saturday morning, dropped')).toBeTruthy();
    // The one cell both weeks hold is named and says nothing else — `checked` is the
    // editor's, and this grid is not interactive.
    expect(screen.getByLabelText('Tuesday evening')).toBeTruthy();
    expect(screen.queryByLabelText('Friday afternoon')).toBeNull();
  });

  /**
   * #277's second body, and the drawing under it: on a cleared week the whole grid is the
   * dropped half, so there is no *new* half to describe and no plus to draw.
   */
  it('draws a cleared week as all dash, under the body that says what happens to it', async () => {
    await search([{ prompt: 'KEEP_THESE_TIMES', slots: [] }]);
    await screen.findByText(KEEP_THESE_TIMES);

    expect(
      screen.getByText(
        // The stubbed profile holds two cells, and the body quotes that count beside the
        // sentence that replaces *"0 slots now"*.
        promptCopy({ prompt: 'KEEP_THESE_TIMES', week: [], profileWeek: PROFILE_WEEK }).body,
      ),
    ).toBeTruthy();
    expect(screen.getAllByLabelText(/, dropped$/)).toHaveLength(2);
    expect(screen.queryByLabelText(/newly added$/)).toBeNull();
  });
});

describe('yes — through the route that owns the value', () => {
  it('saves the week the search ran on, and writes no decline', async () => {
    await search([
      {
        prompt: 'KEEP_THESE_TIMES',
        slots: [
          { day: 2, part: 'EVENING' },
          { day: 1, part: 'MORNING' },
        ],
      },
    ]);
    await screen.findByText(KEEP_THESE_TIMES);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THESE_TIMES').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', AVAILABILITY)).toHaveLength(1));
    expect(transport.requestsTo('PUT', AVAILABILITY)[0]?.body).toEqual({
      availability: [
        { day: 2, part: 'EVENING' },
        { day: 1, part: 'MORNING' },
      ],
    });
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });

  it('makes the widening the profile’s radius', async () => {
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS)[0]?.body).toEqual({ search_radius_km: 22 });
  });

  it('declares the mode the searches kept choosing, on the drift prompt’s own surface', async () => {
    await search([{ prompt: 'UPDATE_PLAY_INTENT', mode: 'COMPETITIVE' }]);
    await screen.findByText('Your searches say something else');

    fireEvent.press(screen.getByLabelText(promptControls('UPDATE_PLAY_INTENT').accept));

    await waitFor(() => expect(transport.requestsTo('PUT', PADEL_INTENT)).toHaveLength(1));
    expect(transport.requestsTo('PUT', PADEL_INTENT)[0]?.body).toEqual({
      intent: 'COMPETITIVE',
      surface: 'DRIFT_PROMPT',
    });
  });

  it('goes on to the court once the write has landed', async () => {
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  });

  /**
   * The one *yes* that writes nothing and stays put. `REFRESH_YOUR_TIMES` carries no value,
   * and it is only ever raised on a week the profile already holds — so what it offers is the
   * grid, which is on the screen this sheet is over.
   */
  it('hands the player back to their week rather than writing one', async () => {
    await search([{ prompt: 'REFRESH_YOUR_TIMES' }]);
    await screen.findByText('Is this week still right?');

    fireEvent.press(screen.getByLabelText(promptControls('REFRESH_YOUR_TIMES').accept));

    await waitFor(() => expect(screen.queryByText('Is this week still right?')).toBeNull());
    expect(screen).toHavePathname('/play');
    expect(await screen.findByLabelText('Tuesday evening')).toBeTruthy();
    expect(profileWrites()).toEqual([]);
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });

  /** A refusal keeps the sheet up over the control that failed, which is the retry. */
  it('says why a write was refused, and keeps the question on screen', async () => {
    transport.on('PUT', RADIUS, () => errorResponse(503, 'matchmaking_unavailable'));
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));

    expect(
      await screen.findByText(
        playErrorMessage({ code: 'matchmaking_unavailable' } as never) as string,
      ),
    ).toBeTruthy();
    expect(screen.getByText('Keep 22 km?')).toBeTruthy();
    expect(screen).toHavePathname('/play');
  });
});

describe('not now — a row about the question, and never a value', () => {
  it('is written when the button is pressed', async () => {
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));

    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));
    // Keyed by the question and never by the value quoted: declining *keep 22 km?* answers
    // *keep 32 km?* next week, because the player answered about a habit.
    expect(transport.requestsTo('POST', DECLINES)[0]?.body).toEqual({
      prompt: 'KEEP_THIS_RADIUS',
      sport: 'PADEL',
    });
    expect(profileWrites()).toEqual([]);
  });

  /** Dismissal is a decline: closing the sheet is an answer, not an escape. */
  it('is written when the sheet is closed instead of answered', async () => {
    await search([{ prompt: 'REFRESH_YOUR_TIMES' }]);
    await screen.findByText('Is this week still right?');

    fireEvent.press(screen.getByLabelText(promptControls('REFRESH_YOUR_TIMES').close));

    await waitFor(() => expect(transport.requestsTo('POST', DECLINES)).toHaveLength(1));
    expect(transport.requestsTo('POST', DECLINES)[0]?.body).toEqual({
      prompt: 'REFRESH_YOUR_TIMES',
      sport: 'PADEL',
    });
  });

  it('says what it costs, and says nothing of the kind on the prompt it costs nothing on', async () => {
    await search([{ prompt: 'REFRESH_YOUR_TIMES' }]);
    await screen.findByText('Is this week still right?');

    // Thirty days of silence nobody is told about is a hidden mechanism.
    expect(screen.getByText(/Not now means not for a month\./, { exact: false })).toBeTruthy();
  });

  it('carries no suppression sentence on the one prompt with no suppression', async () => {
    await search([{ prompt: 'KEEP_THESE_TIMES', slots: [{ day: 2, part: 'EVENING' }] }]);
    await screen.findByText(KEEP_THESE_TIMES);

    expect(screen.queryByText(/not for a month/)).toBeNull();
  });

  /**
   * The route refuses a decline of `KEEP_THESE_TIMES` with `prompt_does_not_suppress` — a
   * grid is a different grid next Tuesday — so the app does not send one. The sheet still
   * closes, and the search still stands.
   */
  it('sends nothing for the prompt a decline buys nothing on', async () => {
    await search([{ prompt: 'KEEP_THESE_TIMES', slots: [{ day: 2, part: 'EVENING' }] }]);
    await screen.findByText(KEEP_THESE_TIMES);

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THESE_TIMES').decline));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
    expect(profileWrites()).toEqual([]);
  });

  it('lets the court through, because the search it is about already ran', async () => {
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').decline));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  });
});

describe('one question, one answer', () => {
  /**
   * The sheet is dismissible while a *yes* is in flight — an offline write is **paused**
   * rather than pending, and a modal that could not be closed until the connection came back
   * is the dead end the searching latch exists to dissolve. So the dismissal has to know that
   * the question has already been answered.
   */
  it('writes no decline when the sheet is closed after a yes was sent', async () => {
    transport.on('PUT', RADIUS, () => new Promise<never>(() => undefined));
    await search([{ prompt: 'KEEP_THIS_RADIUS', radius_km: 22 }]);
    await screen.findByText('Keep 22 km?');

    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').accept));
    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS)).toHaveLength(1));
    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THIS_RADIUS').close));

    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
    // Both answers to one question is the one outcome neither control may produce.
    expect(transport.requestsTo('POST', DECLINES)).toEqual([]);
  });

  /**
   * **A second search asks its own question**, and this is the one flow where that happens
   * without the screen being left and re-entered: *Let me fix it now* keeps the player on the
   * grid, so they edit it and search again from the same mount. A sheet that remembered
   * having been answered would swallow the question the edit was made for.
   */
  it('asks again on the next search from the same screen', async () => {
    let searches = 0;
    transport.on('POST', SEARCHES, () => {
      searches += 1;
      return json(
        searches === 1
          ? shortlist([{ prompt: 'REFRESH_YOUR_TIMES' }])
          : shortlist(
              [
                {
                  prompt: 'KEEP_THESE_TIMES',
                  slots: [
                    { day: 2, part: 'EVENING' },
                    { day: 1, part: 'MORNING' },
                  ],
                },
              ],
              'f1a2b3c4-d5e6-4f70-8a9b-0c1d2e3f4a5b',
            ),
      );
    });

    await openPlay();
    await pressSearch(1);
    await screen.findByText('Is this week still right?');

    fireEvent.press(screen.getByLabelText(promptControls('REFRESH_YOUR_TIMES').accept));
    await waitFor(() => expect(screen.queryByText('Is this week still right?')).toBeNull());

    // Handed back to the grid, on the screen that has one: edit it and search again.
    fireEvent.press(await screen.findByLabelText('Monday morning'));
    await pressSearch(2);

    expect(await screen.findByText(KEEP_THESE_TIMES)).toBeTruthy();
    // And the second question can be **answered** — the guard that stops one question being
    // answered twice is per question, so a sheet that carried it over would be a modal with
    // no way out on every search after the first.
    fireEvent.press(screen.getByLabelText(promptControls('KEEP_THESE_TIMES').decline));
    await waitFor(() => expect(screen).toHavePathname('/play/builder'));
  });
});
