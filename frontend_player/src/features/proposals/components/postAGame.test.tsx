/**
 * ***Post a game*, walked** — from a group's page, every control, each of the grid's nine looks, a
 * cell's sheet, the guards on the button, the way back to the tab it was opened from and the landing
 * on *You’re in* ([#558](https://github.com/Raketa02/Raketa/issues/558),
 * [#848](https://github.com/Raketa02/Raketa/issues/848); the screens A5; mocks 15–35; the
 * mechanics §9; the backend's #546).
 *
 * The real route tree from Play › Groups, with `fetch`, the payment provider's phone half and the
 * platform edges faked. **The grid is read at `DECK_READ_AT`** — Wednesday 30 September 2026, 10:00
 * in Warsaw — so week one is Wednesday to Tuesday and a Saturday cell is *Saturday*. The transport
 * drops the query string before matching, so what a read asked is read off its URL (`askedOf`).
 * The ten seconds in front of a rescue's join are walked by advancing the fake clock past them,
 * never by polling (`theFill.test.tsx`'s rule).
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet, type StyleProp, type TextStyle } from 'react-native';

import { PAYMENTS_COPY } from '@/features/payments/types';
import { RECORD_TITLE } from '@/features/player_record/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { FILL_COPY, POSTING_COPY, PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  ANIA,
  DECK_READ_AT,
  KAROL,
  KUBA,
  ZOFIA,
  groupDeck,
  liveYes,
  proposalDetails,
  deckCard,
  seatToFill,
  seatsPath,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
} from '@/test-support/groupDeck';
import { bookedSides, bookingDetails, stubBooking } from '@/test-support/home';
import {
  GATE_USER,
  LIVE_YESES_PATH,
  PAYMENT_TERMS_IN_FORCE,
  launchSignedIn,
  resetClipboard,
  resetHaptics,
  resetPayments,
  resetShare,
  stubClipboard,
  stubGate,
  stubHaptics,
  stubLiveYeses,
  stubMyGroups,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import {
  FAKE_CARD_NUMBER,
  TEST_CARDS,
  fakeClipboard,
  fakeHaptics,
  fakePayments,
  fakeShare,
} from '@/test-support/platform';
import {
  BONARKA,
  ENOUGH,
  FEW,
  HOT,
  OGRODY,
  THIN,
  askedOf,
  forFunFit,
  freeCourt,
  postStillFilling,
  postedAnswer,
  postingCell,
  postingGrid,
  postingGridPath,
  postingSlot,
  postingSlotPath,
  postsPath,
  slotFit,
  stubPostingGrid,
  stubPostingSlot,
} from '@/test-support/posting';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

const COPY = POSTING_COPY;
const SECOND = 1_000;
const HIDDEN_TOO = { includeHiddenElements: true } as const;

/** The Game a rescue's booking opened. */
const GAME_ID = 'a1000000-0000-4000-8000-000000000009';

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 10,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

/** Ten of the crew rated in padel and four in tennis — mock 16's *Padel 10 · Tennis 4*. */
const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://rakieta.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [
    {
      sport: 'PADEL',
      rated_count: 10,
      first_rated: [
        { player_id: GATE_USER.id, nickname: 'ada' },
        { player_id: 'e0000000-0000-4000-8000-000000000002', nickname: 'Member 2' },
        { player_id: 'e0000000-0000-4000-8000-000000000003', nickname: 'Member 3' },
        { player_id: 'e0000000-0000-4000-8000-000000000004', nickname: 'Member 4' },
      ],
    },
    {
      sport: 'TENNIS',
      rated_count: 4,
      first_rated: [{ player_id: GATE_USER.id, nickname: 'ada' }],
    },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

/** The days of week one, as the grid's cells are keyed. */
const WED = '2026-09-30';
const THU = '2026-10-01';
const FRI = '2026-10-02';
const SAT = '2026-10-03';

/**
 * **A week with every look the server decides** — today's morning over, a few and an enough with no
 * court, a thin one and hot ones, one outside the reader's week, one with a game happening, and one
 * past the cap.
 */
const EVERY_LOOK: Readonly<Record<string, Partial<Wire['PostingCellSchema']>>> = {
  [`${WED}:MORNING`]: { ...HOT, past: true },
  [`${THU}:MORNING`]: FEW,
  [`${THU}:AFTERNOON`]: ENOUGH,
  [`${THU}:EVENING`]: THIN,
  [`${FRI}:MORNING`]: { ...HOT, outside_your_hours: true },
  [`${FRI}:EVENING`]: { ...HOT, happening: true },
  [`${SAT}:EVENING`]: { ...HOT, fits_free: 8 },
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, {
    ratings: [rating('PADEL', 2.71), rating('TENNIS', 3.1)],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  stubPayments(fakePayments());
  stubPaymentMethod(transport, VISA_4312);
  stubLiveYeses(transport, []);
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  resetHaptics();
  resetPayments();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Serve the crew's page and its reads; the grid draws `cells` in either week. */
function serveTheCrew(
  cells: Readonly<Record<string, Partial<Wire['PostingCellSchema']>>> = EVERY_LOOK,
  deck: Wire['GroupDeckResponse'] = groupDeck(),
) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, deck);
  stubPostingGrid(transport, CREW.id, (request) =>
    postingGrid({ week: askedOf(request).week === '2' ? 2 : 1, cells }),
  );
  stubPostingSlot(transport, CREW.id);
}

/** The crew's page, on whichever tab it opens. */
async function openThePage() {
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

/** From You’re in's floating button — the screen up, the grid read. */
async function openPosting(cells?: Parameters<typeof serveTheCrew>[0]) {
  serveTheCrew(cells);
  await openThePage();
  fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
  fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}/post`));
  await screen.findByTestId('posting-grid-week-1');
}

/** From Games' *Nothing picked right now*, its third door (Q96) — the screen up, the grid read. */
async function openPostingFromGames() {
  serveTheCrew();
  await openThePage();
  expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  fireEvent.press(screen.getByRole('button', { name: POST_A_GAME }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}/post`));
  await screen.findByTestId('posting-grid-week-1');
}

/** The two doors, each with the tab it is on — the origin a back-out returns to. */
const DOORS = [
  ['You’re in’s floating button', 'You’re in', openPosting],
  ['Games’ Nothing picked right now', 'Games', openPostingFromGames],
] as const;

const POST_A_GAME = 'Post a game';

/** The page's tab, selected — hidden too, for the page under *It's a game!*. */
const onTab = (name: string) =>
  screen.findByRole('button', { name: new RegExp(`^${name}`), selected: true, ...HIDDEN_TOO });

const cellOf = (day: string, range: Wire['DayRange']) =>
  screen.getByTestId(`posting-cell-${day}-${range}`);

const gridAsks = () =>
  transport.requestsTo('GET', postingGridPath(CREW.id)).map((request) => askedOf(request));
const lastGridAsk = () => gridAsks().at(-1);
const slotAsks = () =>
  transport.requestsTo('GET', postingSlotPath(CREW.id)).map((request) => askedOf(request));
const posts = () => transport.requestsTo('POST', postsPath(CREW.id));
const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);

const postButton = () => screen.getByRole('button', { name: COPY.post });

/** A bound as its keys say it — the figure itself is drawn, and spoken on the keys. */
const bound = (key: string) =>
  (screen.getByLabelText(key).props.accessibilityValue as { readonly text: string }).text;

/** Whether a control is shut — `disabled` to a listener, as every shut key here is. */
const shut = (element: {
  readonly props: { readonly accessibilityState?: { readonly disabled?: boolean } };
}) => element.props.accessibilityState?.disabled === true;

/** The colour a text is drawn in, as its own style sets it. */
const inkOf = (element: { readonly props: { readonly style?: unknown } }) =>
  (StyleSheet.flatten(element.props.style as StyleProp<TextStyle>) as TextStyle | undefined)?.color;

/** Open Saturday evening's sheet and pick its first court. */
async function pickSaturdayEvening() {
  fireEvent.press(cellOf(SAT, 'EVENING'));
  fireEvent.press(await screen.findByTestId(`slot-court-${OGRODY.id}-2026-10-03T15:00:00Z`));
  await waitFor(() => expect(screen.queryByText(COPY.sheet.freeCourts)).toBeNull());
}

// ---------------------------------------------------------------------------
// Opening, leaving, and the draft
// ---------------------------------------------------------------------------

describe('opening Post a game (mock 14, A5)', () => {
  it('is You’re in’s floating button, full screen over the group with the bar still under it', async () => {
    await openPosting();

    expect(screen.getByRole('header', { name: COPY.title })).toBeTruthy();
    expect(screen.getByLabelText('Play')).toBeTruthy();
  });

  it('is Nothing picked right now’s third door too (Q96)', async () => {
    await openPostingFromGames();

    expect(screen.getByRole('header', { name: COPY.title })).toBeTruthy();
  });
});

/**
 * **Backing out returns to the tab Post a game was opened from** (#848, PRD #844): opening it leaves
 * the page under it alone, so every way back — the chevron, and the navigator's own pop, which is
 * what the hardware back and the swipe both are — finds the page where the player left it. The
 * chevron names that tab, drawn as the chevron and spoken by its name.
 */
describe('backing out of Post a game (#848)', () => {
  it.each(DOORS)('opened from %s, the chevron is Back to %s', async (_door, origin, open) => {
    await open();

    expect(screen.getByRole('button', { name: `Back to ${origin}` })).toBeTruthy();
    expect(screen.queryByLabelText('Back to Fill in')).toBeNull();
  });

  it.each(DOORS)('opened from %s, the chevron returns to %s', async (_door, origin, open) => {
    await open();

    fireEvent.press(screen.getByLabelText(`Back to ${origin}`));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    expect(await onTab(origin)).toBeTruthy();
  });

  it.each(DOORS)(
    'opened from %s, the hardware back and the swipe return to %s',
    async (_door, origin, open) => {
      await open();

      act(() => router.back());

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      expect(await onTab(origin)).toBeTruthy();
    },
  );

  // Q125: Info is pushed over the page, so the page's tab is still the one Post a game came from.
  it.each(DOORS)(
    'opened from %s, leaves the page on %s under Info, so back from Info is there too',
    async (_door, origin, open) => {
      await open();
      act(() => router.back());
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      expect(await onTab(origin)).toBeTruthy();

      fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}/info`));
      fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.info.back }));

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      expect(await onTab(origin)).toBeTruthy();
    },
  );

  it('names the tab it came from each time it opens — Games, then You’re in', async () => {
    await openPostingFromGames();
    fireEvent.press(screen.getByLabelText('Back to Games'));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));

    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}/post`));

    expect(await screen.findByLabelText('Back to You’re in')).toBeTruthy();
    expect(screen.queryByLabelText('Back to Games')).toBeNull();
  });
});

describe('the draft', () => {
  it('keeps the draft while the player stays in the group, and forgets it once they leave', async () => {
    await openPosting();
    fireEvent.press(screen.getByRole('button', { name: 'Women' }));
    fireEvent.press(screen.getByLabelText('Back to You’re in'));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));

    expect(await screen.findByRole('button', { name: 'Women', selected: true })).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Back to You’re in'));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    fireEvent.press(await screen.findByLabelText(GROUPS_COPY.group.back));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    expect(await screen.findByRole('button', { name: /^Games/, selected: true })).toBeTruthy();
    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));

    expect(await screen.findByRole('button', { name: 'Anyone', selected: true })).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The controls
// ---------------------------------------------------------------------------

describe('rated in none of the group’s sports (Q80)', () => {
  it('asks the player to get rated, with the passport’s Add a sport for each', async () => {
    const official: Wire['GroupResponse'] = {
      ...PAGE,
      kind: 'OFFICIAL',
      sports: ['SQUASH'],
      declared_sports: ['SQUASH'],
    };
    serveTheCrew();
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(official));
    await openThePage();

    act(() => router.push(`/play/group/${CREW.id}/post`));

    expect(await screen.findByText('Get rated in squash to post here')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Rate Squash' })).toBeTruthy();
    expect(screen.queryByTestId('posting-grid-week-1')).toBeNull();
    expect(gridAsks()).toHaveLength(0);
  });
});

describe('SPORT (mock 16)', () => {
  it('chips the sports the player is rated in, each with the members rated in it', async () => {
    await openPosting();

    expect(
      screen.getByRole('button', { name: 'Padel, 10 members rated', selected: true }),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Tennis, 4 members rated', selected: false }),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Squash/ })).toBeNull();
    expect(lastGridAsk()).toMatchObject({
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      who: 'ANYONE',
      week: '1',
    });
  });

  it('reads the grid for the sport chosen, the level range back at the engine’s and the pick gone', async () => {
    await openPosting();
    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));
    await pickSaturdayEvening();

    fireEvent.press(screen.getByRole('button', { name: 'Tennis, 4 members rated' }));

    await waitFor(() => expect(lastGridAsk()?.sport).toBe('TENNIS'));
    expect(lastGridAsk()).not.toHaveProperty('level_low');
    expect(await screen.findByText(COPY.pickFirst)).toBeTruthy();
  });
});

describe('SPORT, chosen again', () => {
  it('keeps the pick and the range when the sport already chosen is pressed', async () => {
    await openPosting();
    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));
    await pickSaturdayEvening();

    fireEvent.press(screen.getByRole('button', { name: 'Padel, 10 members rated' }));

    expect(shut(postButton())).toBe(false);
    expect(bound(COPY.levelKeys.lowUp)).toBe('2,61');
  });
});

describe('KIND (mock 17)', () => {
  it('defaults to the player’s intent — a For-fun player’s switch read as For fun', async () => {
    serveTheCrew(EVERY_LOOK, groupDeck({ segments: [{ kind: 'FOR_FUN', count: 0 }] }));
    await openThePage();
    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));

    expect(
      await screen.findByRole('button', { name: 'For fun, a friendly', selected: true }),
    ).toBeTruthy();
    await waitFor(() => expect(lastGridAsk()?.kind).toBe('FOR_FUN'));
  });

  it('re-reads the grid live for the kind chosen', async () => {
    await openPosting();

    fireEvent.press(screen.getByRole('button', { name: 'For fun, a friendly' }));

    await waitFor(() => expect(lastGridAsk()?.kind).toBe('FOR_FUN'));
    expect(
      screen.getByRole('button', { name: 'For fun, a friendly', selected: true }),
    ).toBeTruthy();
  });
});

describe('WHO (mock 18)', () => {
  it('offers Mixed pairs in doubles, and asks the grid for who it is for', async () => {
    await openPosting();

    for (const who of ['Anyone', 'Men', 'Women', 'Mixed pairs']) {
      expect(screen.getByRole('button', { name: who })).toBeTruthy();
    }
    fireEvent.press(screen.getByRole('button', { name: 'Mixed pairs' }));

    await waitFor(() => expect(lastGridAsk()?.who).toBe('MIXED_PAIRS'));
  });

  it('has no Mixed pairs in a sport played one a side, and takes it back to Anyone there', async () => {
    await openPosting();
    fireEvent.press(screen.getByRole('button', { name: 'Mixed pairs' }));

    fireEvent.press(screen.getByRole('button', { name: 'Tennis, 4 members rated' }));

    expect(await screen.findByRole('button', { name: 'Anyone', selected: true })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Mixed pairs' })).toBeNull();
    await waitFor(() => expect(lastGridAsk()).toMatchObject({ sport: 'TENNIS', who: 'ANYONE' }));
  });
});

describe('LEVEL — narrow it, not widen it (mock 19, Q78)', () => {
  const LOW = COPY.levelKeys.lowUp;
  const HIGH = COPY.levelKeys.highDown;

  it('starts at the engine’s window, and sends neither bound until one is narrowed', async () => {
    await openPosting();

    expect(bound(LOW)).toBe('2,56');
    expect(bound(HIGH)).toBe('2,86');
    expect(screen.getByText('2,56', HIDDEN_TOO)).toBeTruthy();
    expect(lastGridAsk()).not.toHaveProperty('level_low');
    expect(lastGridAsk()).not.toHaveProperty('level_high');
  });

  it('narrows a bound 0,05 a press and asks the grid for it', async () => {
    await openPosting();

    fireEvent.press(screen.getByLabelText(LOW));
    await waitFor(() => expect(bound(LOW)).toBe('2,61'));
    await waitFor(() => expect(lastGridAsk()?.level_low).toBe('2.61'));

    fireEvent.press(screen.getByLabelText(HIGH));
    await waitFor(() => expect(bound(HIGH)).toBe('2,81'));
    await waitFor(() => expect(lastGridAsk()?.level_high).toBe('2.81'));
  });

  it('bounces a push past the engine’s own, says why, and asks nothing new', async () => {
    await openPosting();
    const before = gridAsks().length;

    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowDown));
    act(() => jest.advanceTimersByTime(theme.motion.bounce));

    expect(await screen.findByText(COPY.bounce)).toBeTruthy();
    expect(bound(LOW)).toBe('2,56');
    expect(gridAsks()).toHaveLength(before);
  });

  it('lets a narrowed bound back out to the engine’s, and shuts a bound that would pass the other', async () => {
    await openPosting();
    for (let press = 0; press < 3; press += 1) {
      fireEvent.press(screen.getByLabelText(LOW));
      fireEvent.press(screen.getByLabelText(HIGH));
    }

    await waitFor(() => expect([bound(LOW), bound(HIGH)]).toEqual(['2,71', '2,71']));
    expect(shut(screen.getByLabelText(LOW))).toBe(true);
    expect(shut(screen.getByLabelText(HIGH))).toBe(true);

    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowDown));
    await waitFor(() => expect(bound(LOW)).toBe('2,66'));
  });
});

describe('LEVEL, across a kind and a refusal', () => {
  it('steps against the kind’s own window — a kind chosen brings its window and starts it over', async () => {
    serveTheCrew();
    stubPostingGrid(transport, CREW.id, (request) =>
      askedOf(request).kind === 'FOR_FUN'
        ? postingGrid({
            kind: 'FOR_FUN',
            cells: EVERY_LOOK,
            engine_level_range: { low: 2.41, high: 3.01 },
            level_range: { low: 2.41, high: 3.01 },
          })
        : postingGrid({ cells: EVERY_LOOK }),
    );
    await openThePage();
    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));
    await screen.findByTestId('posting-grid-week-1');
    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));
    await waitFor(() => expect(bound(COPY.levelKeys.lowUp)).toBe('2,61'));

    fireEvent.press(screen.getByRole('button', { name: 'For fun, a friendly' }));

    await waitFor(() => expect(bound(COPY.levelKeys.lowUp)).toBe('2,41'));
    expect(bound(COPY.levelKeys.highDown)).toBe('3,01');
    expect(lastGridAsk()).not.toHaveProperty('level_low');
    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));
    await waitFor(() => expect(lastGridAsk()?.level_low).toBe('2.46'));
  });

  it('goes back to the engine’s window when the server will not take the narrowed one', async () => {
    serveTheCrew();
    stubPostingGrid(transport, CREW.id, (request) =>
      askedOf(request).level_low === undefined
        ? postingGrid({ cells: EVERY_LOOK })
        : errorResponse(400, 'level_range_too_wide'),
    );
    await openThePage();
    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));
    await screen.findByTestId('posting-grid-week-1');

    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));

    await waitFor(() => expect(gridAsks().some((ask) => ask.level_low === '2.61')).toBe(true));
    // The engine's own grid is the one already read, so it is drawn again from the cache.
    await waitFor(() => expect(bound(COPY.levelKeys.lowUp)).toBe('2,56'));
    expect(screen.getByTestId('posting-grid-week-1')).toBeTruthy();
  });
});

describe('WHEN (mocks 2-, 20–22)', () => {
  it('heads seven days from today — Today in its own colour — and the three ranges with their hours', async () => {
    await openPosting();
    const grid = screen.getByTestId('posting-grid-week-1');

    expect(within(grid).getByLabelText('Today 30 Sep')).toBeTruthy();
    expect(within(grid).getByLabelText('Sat 3 Oct')).toBeTruthy();
    expect(within(grid).getByLabelText('Tue 6 Oct')).toBeTruthy();
    expect(within(grid).getByLabelText('Morning, 07:00 to 12:00')).toBeTruthy();
    expect(within(grid).getByLabelText('Afternoon, 12:00 to 17:00')).toBeTruthy();
    expect(within(grid).getByLabelText('Evening, 17:00 to 23:00')).toBeTruthy();
  });

  it('pages to next week and back, each chevron shut at its end of the fortnight', async () => {
    await openPosting();
    expect(screen.getByRole('header', { name: 'This week' })).toBeTruthy();
    expect(shut(screen.getByLabelText(COPY.earlierWeek))).toBe(true);

    fireEvent.press(screen.getByLabelText(COPY.laterWeek));

    expect(await screen.findByTestId('posting-grid-week-2')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Next week' })).toBeTruthy();
    expect(lastGridAsk()?.week).toBe('2');
    expect(shut(screen.getByLabelText(COPY.laterWeek))).toBe(true);

    fireEvent.press(screen.getByLabelText(COPY.earlierWeek));
    expect(await screen.findByTestId('posting-grid-week-1')).toBeTruthy();
  });

  it('opens How to read the map from the ⓘ, with the happening line as A5.2 rewrote it', async () => {
    await openPosting();

    fireEvent.press(screen.getByLabelText(COPY.legend.open));

    expect(await screen.findByRole('header', { name: COPY.legend.title })).toBeTruthy();
    expect(screen.getByText(COPY.legend.happening)).toBeTruthy();
    expect(screen.getByText(COPY.legend.outside)).toBeTruthy();
    fireEvent.press(screen.getByLabelText(COPY.legend.close));
    await waitFor(() => expect(screen.queryByText(COPY.legend.happening)).toBeNull());
  });

  it('says why when the grid cannot be drawn for who it is for, in the grid’s place', async () => {
    serveTheCrew();
    stubPostingGrid(transport, CREW.id, () => errorResponse(409, 'who_leaves_you_out'));
    await openThePage();
    fireEvent.press(await screen.findByRole('button', { name: /^You’re in/ }));
    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));

    expect(await screen.findByText(COPY.gridRefused.who_leaves_you_out!)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The nine looks
// ---------------------------------------------------------------------------

describe('a cell’s nine looks (mocks 23–32)', () => {
  it('draws a dead cell with no number and no court', async () => {
    await openPosting();
    const dead = cellOf(WED, 'AFTERNOON');

    expect(within(dead).queryByTestId('posting-cell-count')).toBeNull();
    expect(within(dead).queryByTestId('posting-cell-court')).toBeNull();
    expect(dead.props.accessibilityLabel).toBe('This afternoon, nobody who fits is free');
  });

  it('draws the few and the enough with their count and no court', async () => {
    await openPosting();

    for (const [range, count, look] of [
      ['MORNING', '2', 'no court free'],
      ['AFTERNOON', '4', 'a full game free, no court'],
    ] as const) {
      const cell = cellOf(THU, range);
      expect(within(cell).getByTestId('posting-cell-count').props.children).toBe(count);
      expect(within(cell).queryByTestId('posting-cell-court')).toBeNull();
      expect(cell.props.accessibilityLabel).toContain(look);
    }
  });

  it('draws the thin and the hot with their count and the court glyph, the hot capped at 5+', async () => {
    await openPosting();

    const thin = cellOf(THU, 'EVENING');
    expect(within(thin).getByTestId('posting-cell-court')).toBeTruthy();
    expect(thin.props.accessibilityLabel).toContain('a court free, may not fill');

    const capped = cellOf(SAT, 'EVENING');
    expect(within(capped).getByTestId('posting-cell-count').props.children).toBe('5+');
    expect(within(capped).getByTestId('posting-cell-court')).toBeTruthy();
    expect(capped.props.accessibilityLabel).toContain('a court free and a full game');
  });

  it('dims a cell outside the player’s week and says so, still a door', async () => {
    await openPosting();
    const outside = cellOf(FRI, 'MORNING');

    expect(outside.props.accessibilityLabel).toContain('outside your hours');
    expect(shut(outside)).toBe(false);
  });

  it('makes a cell earlier today inert — it opens nothing', async () => {
    await openPosting();
    const past = cellOf(WED, 'MORNING');

    expect(shut(past)).toBe(true);
    expect(past.props.accessibilityLabel).toContain('earlier today');
    fireEvent.press(past);
    expect(slotAsks()).toHaveLength(0);
  });

  it('dots a cell where a game is already happening', async () => {
    await openPosting();

    expect(within(cellOf(FRI, 'EVENING')).getByTestId('posting-cell-happening')).toBeTruthy();
    expect(cellOf(FRI, 'EVENING').props.accessibilityLabel).toContain(
      'a game already happening here',
    );
    expect(within(cellOf(SAT, 'EVENING')).queryByTestId('posting-cell-happening')).toBeNull();
  });

  it('rings the picked cell with its tick, and says it is the pick', async () => {
    await openPosting();

    await pickSaturdayEvening();

    expect(screen.getByTestId('posting-cell-picked')).toBeTruthy();
    expect(cellOf(SAT, 'EVENING').props.accessibilityState).toMatchObject({ selected: true });
    expect(cellOf(SAT, 'EVENING').props.accessibilityLabel).toContain('your pick');
  });
});

// ---------------------------------------------------------------------------
// The sheet
// ---------------------------------------------------------------------------

describe('a cell’s sheet (mocks 34, 35)', () => {
  it('heads the sheet with the day’s range and the count, then the fits, then the free courts', async () => {
    await openPosting();

    fireEvent.press(cellOf(SAT, 'EVENING'));

    expect(await screen.findByRole('header', { name: 'Saturday evening' })).toBeTruthy();
    expect(await screen.findByText('5 of your best fits free then')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'karol.t, level 2,75, a 93 % even game' }),
    ).toBeTruthy();
    expect(screen.getByText('2,69 · 95')).toBeTruthy();
    expect(screen.getByText(COPY.sheet.freeCourts)).toBeTruthy();
    const court = screen.getByTestId(`slot-court-${OGRODY.id}-2026-10-03T15:00:00Z`);
    expect(within(court).getByText('17:00')).toBeTruthy();
    expect(within(court).getByText('Ogrody 33')).toBeTruthy();
    expect(within(court).getByText('4 free')).toBeTruthy();
    expect(within(court).getByText('2,4 km · 27 zł if it fills · book by Sat 15:00')).toBeTruthy();
    expect(within(court).getByText('27 zł each')).toBeTruthy();
    expect(slotAsks().at(-1)).toMatchObject({
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      who: 'ANYONE',
      day: SAT,
      range: 'EVENING',
    });
  });

  // #753 (Q68, applying since Q128): a fit who is the reader's own friend carries friend.
  it('tags the reader’s own friends among the fits, and nobody else', async () => {
    await openPosting();
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({ fits: [slotFit(KAROL({ friend: true }), 93), slotFit(ZOFIA(), 95)] }),
    );

    fireEvent.press(cellOf(SAT, 'EVENING'));

    const karol = await screen.findByTestId(`slot-fit-${KAROL().player_id}`);
    expect(within(karol).getByText(PROPOSALS_COPY.friendSpoken)).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'karol.t, friend, level 2,75, a 93 % even game' }),
    ).toBeTruthy();
    const zofia = screen.getByTestId(`slot-fit-${ZOFIA().player_id}`);
    expect(within(zofia).queryByText(PROPOSALS_COPY.friendSpoken)).toBeNull();
  });

  // #842 (ADR-0207 §5): a For-fun post's fit says the Social vibe of the poster and them.
  it('lines a For-fun post’s fits level · Social vibe, the % in its band’s ink, in the server’s order', async () => {
    await openPosting();
    // The server's order: the highest vibe first (#834) — not the Levels' (2,80 · 2,75 · 2,69 · 2,68).
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({
        kind: 'FOR_FUN',
        fits: [
          forFunFit(ZOFIA(), 83),
          forFunFit(KUBA(), 60),
          forFunFit(KAROL(), 36),
          forFunFit(ANIA(), 14),
        ],
      }),
    );
    fireEvent.press(screen.getByRole('button', { name: 'For fun, a friendly' }));
    await waitFor(() => expect(lastGridAsk()?.kind).toBe('FOR_FUN'));

    // The other kind's grid is not drawn under it: the cell is back once For fun's is read.
    fireEvent.press(await screen.findByTestId(`posting-cell-${SAT}-EVENING`));

    const fits = within(await screen.findByTestId('slot-fits'));
    expect(slotAsks().at(-1)?.kind).toBe('FOR_FUN');
    expect(
      fits.getAllByRole('button').map((fit) => fit.props.accessibilityLabel as string),
    ).toEqual([
      'zofia.b, level 2,69, Social vibe, 83 percent, Great vibe',
      'kuba.w, level 2,80, Social vibe, 60 percent, Good vibe',
      'karol.t, level 2,75, Social vibe, 36 percent, Some common ground',
      'ania.k, level 2,68, Social vibe, 14 percent, Fresh mix',
    ]);
    expect(fits.getByText('2,69 · 83%')).toBeTruthy();
    expect(fits.getByText('2,68 · 14%')).toBeTruthy();
    // The % in its band's ink on paper, the Social vibe card's; the Level stays muted.
    expect(inkOf(fits.getByText('83%'))).toBe(theme.color.oliveInk);
    expect(inkOf(fits.getByText('60%'))).toBe(theme.color.oliveInk);
    expect(inkOf(fits.getByText('36%'))).toBe(theme.color.oliveInkDim);
    expect(inkOf(fits.getByText('14%'))).toBe(theme.color.vibeGrey);
    expect(inkOf(fits.getByText('2,69 · 83%'))).toBe(theme.color.muted);
  });

  it('lines a competitive post’s fits as before — level · % even, and no Social vibe', async () => {
    await openPosting();

    fireEvent.press(cellOf(SAT, 'EVENING'));

    const fits = within(await screen.findByTestId('slot-fits'));
    expect(slotAsks().at(-1)?.kind).toBe('COMPETITIVE');
    expect(inkOf(fits.getByText('2,75 · 93'))).toBe(theme.color.muted);
    expect(
      fits.getAllByRole('button').map((fit) => fit.props.accessibilityLabel as string),
    ).toEqual([
      'karol.t, level 2,75, a 93 % even game',
      'zofia.b, level 2,69, a 95 % even game',
      'ania.k, level 2,68, a 99 % even game',
      'ewa.m, level 2,60, a 91 % even game',
      'kuba.w, level 2,80, a 96 % even game',
    ]);
    expect(fits.queryByText(/%$/)).toBeNull();
  });

  it('warns a thin cell may not fill, and says it outside the player’s hours', async () => {
    await openPosting();
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({
        day: THU,
        cell: postingCell('EVENING', THU, { ...THIN, outside_your_hours: true }),
        fits: [],
      }),
    );

    fireEvent.press(cellOf(THU, 'EVENING'));

    expect(await screen.findByText('only 2 fit · may not fill · outside your hours')).toBeTruthy();
  });

  it('says nobody fits on a dead cell, and that every game needs a court where none is free', async () => {
    await openPosting();
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({
        day: WED,
        range: 'AFTERNOON',
        cell: postingCell('AFTERNOON', WED),
        fits: [],
        free_courts: [],
      }),
    );

    fireEvent.press(cellOf(WED, 'AFTERNOON'));

    expect(await screen.findByText('Nobody who fits is free then')).toBeTruthy();
    expect(screen.getByText(COPY.sheet.noCourt)).toBeTruthy();
  });

  it('shuts a court nobody who fits is free at — a dead cell’s courts cannot be picked (§9.1)', async () => {
    await openPosting();
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({
        day: WED,
        range: 'AFTERNOON',
        cell: postingCell('AFTERNOON', WED, { court_free: true }),
        fits: [],
        free_courts: [freeCourt({ starts_at: '2026-09-30T11:00:00Z', fits_free: 0 })],
      }),
    );
    fireEvent.press(cellOf(WED, 'AFTERNOON'));

    const court = await screen.findByTestId(`slot-court-${OGRODY.id}-2026-09-30T11:00:00Z`);
    expect(within(court).getByText('0 free')).toBeTruthy();
    expect(shut(court)).toBe(true);
    fireEvent.press(court);

    expect(screen.getByText(COPY.sheet.freeCourts)).toBeTruthy();
    fireEvent.press(screen.getByLabelText(COPY.sheet.close));
    await waitFor(() => expect(screen.queryByText(COPY.sheet.freeCourts)).toBeNull());
    expect(shut(postButton())).toBe(true);
  });

  it('picks a court — the sheet down, the cell ringed, the button open and saying what it will post', async () => {
    await openPosting();
    expect(shut(postButton())).toBe(true);
    expect(screen.getByText(COPY.pickFirst)).toBeTruthy();

    await pickSaturdayEvening();

    expect(shut(postButton())).toBe(false);
    expect(screen.getByText('Saturday 17:00 · Ogrody 33 · 27 zł each if it fills')).toBeTruthy();
  });

  it('reopens the picked cell on its court, and Remove this pick takes it back', async () => {
    await openPosting();
    await pickSaturdayEvening();

    fireEvent.press(cellOf(SAT, 'EVENING'));
    const court = await screen.findByTestId(`slot-court-${OGRODY.id}-2026-10-03T15:00:00Z`);
    expect(court.props.accessibilityState).toMatchObject({ selected: true });
    fireEvent.press(screen.getByRole('button', { name: COPY.sheet.remove }));

    await waitFor(() => expect(shut(postButton())).toBe(true));
    expect(screen.queryByTestId('posting-cell-picked')).toBeNull();
  });

  it('replaces the pick with a new one', async () => {
    await openPosting();
    stubPostingSlot(
      transport,
      CREW.id,
      postingSlot({
        free_courts: [
          freeCourt(),
          freeCourt({
            club: BONARKA,
            home_club: false,
            starts_at: '2026-10-03T17:00:00Z',
            share_grosze: 3200,
          }),
        ],
      }),
    );
    await pickSaturdayEvening();

    fireEvent.press(cellOf(SAT, 'EVENING'));
    fireEvent.press(await screen.findByTestId(`slot-court-${BONARKA.id}-2026-10-03T17:00:00Z`));

    expect(
      await screen.findByText('Saturday 19:00 · Bonarka Arena · 32 zł each if it fills'),
    ).toBeTruthy();
  });

  it('opens a fit’s record in the sheet’s place, and brings the sheet back when it closes', async () => {
    await openPosting();
    fireEvent.press(cellOf(SAT, 'EVENING'));

    fireEvent.press(
      await screen.findByRole('button', {
        name: 'karol.t, level 2,75, a 93 % even game',
      }),
    );

    expect(await screen.findByText(RECORD_TITLE, HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText(COPY.sheet.freeCourts)).toBeNull();
  });

  it('lists what is already happening — rescues first, then posts still filling, each with its door', async () => {
    await openPosting();
    const rescue = seatToFill({
      starts_at: '2026-10-04T18:00:00Z',
      club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
      court_name: 'Court 2',
      share_grosze: 3000,
      open_seats: 2,
    });
    // A seat offered after its game's cut-off: paid at once (Q113).
    const late = seatToFill({ fills_by_the_cut_off: false, deadline: '2026-10-03T14:00:00Z' });
    const post = postStillFilling();
    stubPostingSlot(transport, CREW.id, postingSlot({ rescues: [rescue, late], posts: [post] }));

    fireEvent.press(cellOf(SAT, 'EVENING'));

    expect(await screen.findByText(COPY.sheet.happening)).toBeTruthy();
    const rescueRow = screen.getByTestId(`slot-rescue-${rescue.booking_id}`);
    expect(within(rescueRow).getByText('Padel · Sunday 20:00')).toBeTruthy();
    expect(within(rescueRow).getByText('Centrum Ruchu · Court 2 · 30 zł each')).toBeTruthy();
    expect(within(rescueRow).getByText('2 seats')).toBeTruthy();
    expect(within(rescueRow).getByLabelText('any level, you are free')).toBeTruthy();
    // A rescue's join moves money, so it says Pay (Q124), and aloud what the share does (Q113).
    expect(within(rescueRow).getByText('Pay 30 zł')).toBeTruthy();
    expect(
      within(rescueRow).getByRole('button', { name: 'Pay 30 zł, held until the cut-off' }),
    ).toBeTruthy();
    expect(
      within(screen.getByTestId(`slot-rescue-${late.booking_id}`)).getByRole('button', {
        name: 'Pay 27 zł, paid now',
      }),
    ).toBeTruthy();
    const postRow = screen.getByTestId(`slot-post-${post.proposal_id}`);
    expect(within(postRow).getByText('kuba.w · Bonarka Arena · 32 zł if it fills')).toBeTruthy();
    expect(within(postRow).queryByText(/Court/)).toBeNull();
    expect(within(postRow).getByRole('button', { name: PROPOSALS_COPY.yes })).toBeTruthy();
  });

  it('says Pay with the share on a post’s last seat, because the yes that takes it books the game (Q124)', async () => {
    await openPosting();
    const last = postStillFilling({ open_seats: 1 });
    const filling = postStillFilling({ open_seats: 2 });
    stubPostingSlot(transport, CREW.id, postingSlot({ posts: [last, filling] }));

    fireEvent.press(cellOf(SAT, 'EVENING'));

    const lastRow = await screen.findByTestId(`slot-post-${last.proposal_id}`);
    expect(within(lastRow).getByRole('button', { name: 'Pay 32 zł' })).toBeTruthy();
    expect(within(lastRow).queryByRole('button', { name: PROPOSALS_COPY.yes })).toBeNull();
    const fillingRow = screen.getByTestId(`slot-post-${filling.proposal_id}`);
    expect(within(fillingRow).getByRole('button', { name: PROPOSALS_COPY.yes })).toBeTruthy();
  });

  it.each(DOORS)(
    'opened from %s, joins a post still filling — a free yes — and lands on You’re in with it',
    async (_door, _origin, open) => {
      await open();
      const post = postStillFilling();
      const mine = liveYes({
        proposal_id: post.proposal_id,
        pool_id: CREW.id,
        starts_at: post.starts_at,
      });
      stubPostingSlot(transport, CREW.id, postingSlot({ posts: [post] }));
      transport.on('POST', yesPath(post.proposal_id), () => {
        stubLiveYeses(transport, [mine]);
        return json<Wire['YesAnswerResponse']>({
          proposal_id: post.proposal_id,
          open_seats: 1,
          booked: null,
          your_payment: null,
        });
      });
      stubProposal(
        transport,
        post.proposal_id,
        proposalDetails(
          deckCard({
            proposal_id: post.proposal_id,
            in_count: 2,
            sides: { yours: [youTile({ is_in: true })], theirs: [] },
          }),
        ),
      );
      fireEvent.press(cellOf(SAT, 'EVENING'));

      fireEvent.press(
        within(await screen.findByTestId(`slot-post-${post.proposal_id}`)).getByRole('button', {
          name: PROPOSALS_COPY.yes,
        }),
      );

      await waitFor(() =>
        expect(transport.requestsTo('POST', yesPath(post.proposal_id))).toHaveLength(1),
      );
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      expect(await onTab('You’re in')).toBeTruthy();
      expect(await screen.findByTestId(`youre-in-${post.proposal_id}`)).toBeTruthy();
    },
  );

  // The harness runs every pending timer on a navigation, so the ten seconds behind *Undo* are spent
  // on the way back to the page (`theFill.test.tsx` walks the window itself).
  it.each(DOORS)(
    'opened from %s, takes a rescue’s seat — paid, It’s a game! — and leaves the page under on You’re in',
    async (_door, _origin, open) => {
      await open();
      const rescue = seatToFill();
      stubPostingSlot(transport, CREW.id, postingSlot({ rescues: [rescue] }));
      transport.on('POST', seatsPath(rescue.booking_id), () =>
        json<Wire['YesAnswerResponse']>({
          proposal_id: rescue.booking_id,
          open_seats: 0,
          booked: { booking_id: rescue.booking_id, game_id: GAME_ID },
          your_payment: null,
        }),
      );
      // A sheet's rescue holds no sides, as a row's does not: the faces are the booking's.
      stubBooking(
        transport,
        bookingDetails({ booking_id: rescue.booking_id, game_id: GAME_ID, pool_id: CREW.id }),
      );
      fireEvent.press(cellOf(SAT, 'EVENING'));

      fireEvent.press(
        await screen.findByRole('button', { name: 'Pay 27 zł, held until the cut-off' }),
      );

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      act(() => jest.advanceTimersByTime(10 * SECOND));
      await waitFor(() =>
        expect(transport.requestsTo('POST', seatsPath(rescue.booking_id))).toHaveLength(1),
      );
      const [, partner] = bookedSides().yours;
      expect(
        await screen.findByRole('header', {
          name: `${FILL_COPY.itsAGame.word} You and ${partner?.nickname ?? ''} against ines.d and bartek.l`,
        }),
      ).toBeTruthy();
      expect(await onTab('You’re in')).toBeTruthy();

      fireEvent.press(screen.getByRole('button', { name: FILL_COPY.itsAGame.later }));

      await waitFor(() => expect(screen.queryByText(FILL_COPY.itsAGame.word)).toBeNull());
      expect(screen).toHavePathname(`/play/group/${CREW.id}`);
      expect(
        await screen.findByRole('button', { name: /^You’re in/, selected: true }),
      ).toBeTruthy();
    },
  );
});

// ---------------------------------------------------------------------------
// Post — you're In
// ---------------------------------------------------------------------------

describe('Post — you’re In (mock 33, A5.4)', () => {
  it.each(DOORS)(
    'opened from %s, a post lands on You’re in, with the new game there and the toast',
    async (_door, _origin, open) => {
      await open();
      const mine = liveYes({
        proposal_id: postedAnswer().proposal_id,
        pool_id: CREW.id,
        starts_at: '2026-10-03T15:00:00Z',
      });
      transport.on('POST', postsPath(CREW.id), () => {
        stubLiveYeses(transport, [mine]);
        return json(postedAnswer(), 201);
      });
      stubProposal(
        transport,
        mine.proposal_id,
        proposalDetails(
          deckCard({
            proposal_id: mine.proposal_id,
            type: 'CHALLENGE',
            challenger: { player_id: GATE_USER.id, nickname: GATE_USER.nickname ?? null },
            in_count: 1,
            sides: { yours: [youTile({ is_in: true })], theirs: [] },
          }),
        ),
      );
      await pickSaturdayEvening();

      fireEvent.press(postButton());

      await waitFor(() => expect(posts()).toHaveLength(1));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
      expect(toasts()).toContain('Posted — 5 of your best fits have it.');
      expect(await onTab('You’re in')).toBeTruthy();
      expect(await screen.findByTestId(`youre-in-${mine.proposal_id}`)).toBeTruthy();
    },
  );

  it('a post settled after the player backed out leaves the page on the tab they backed out to', async () => {
    await openPostingFromGames();
    // The post is answered at once, and settles only once the re-reads it starts have — one of
    // them held here. (A held post would be timed out by the navigation: the harness runs every
    // pending timer on one.)
    let release = () => {};
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    transport.on('POST', postsPath(CREW.id), () => {
      transport.on('GET', LIVE_YESES_PATH, async () => {
        await held;
        return json<Wire['LiveYesesResponse']>({ yeses: [] });
      });
      return json(postedAnswer(), 201);
    });
    await pickSaturdayEvening();
    fireEvent.press(postButton());
    await waitFor(() => expect(posts()).toHaveLength(1));

    fireEvent.press(screen.getByLabelText('Back to Games'));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    expect(toasts()).toEqual([]);
    release();
    await act(async () => {
      await jest.advanceTimersByTimeAsync(5 * SECOND);
    });

    await waitFor(() => expect(toasts()).toContain('Posted — 5 of your best fits have it.'));
    expect(await onTab('Games')).toBeTruthy();
    expect(screen).toHavePathname(`/play/group/${CREW.id}`);
  });

  it('posts the controls and the court picked', async () => {
    await openPosting();
    transport.on('POST', postsPath(CREW.id), () => json(postedAnswer(), 201));
    fireEvent.press(screen.getByRole('button', { name: 'Women' }));
    fireEvent.press(screen.getByLabelText(COPY.levelKeys.lowUp));
    await waitFor(() => expect(lastGridAsk()).toMatchObject({ who: 'WOMEN', level_low: '2.61' }));
    await pickSaturdayEvening();

    fireEvent.press(postButton());

    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(posts()[0]?.body).toEqual({
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      who: 'WOMEN',
      level_low: 2.61,
      club_id: OGRODY.id,
      starts_at: '2026-10-03T15:00:00Z',
    });
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  });

  it('starts the next post from nothing', async () => {
    await openPosting();
    transport.on('POST', postsPath(CREW.id), () => json(postedAnswer(), 201));
    fireEvent.press(screen.getByRole('button', { name: 'Women' }));
    await pickSaturdayEvening();
    fireEvent.press(postButton());
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));

    fireEvent.press(await screen.findByRole('button', { name: POST_A_GAME }));

    expect(await screen.findByRole('button', { name: 'Anyone', selected: true })).toBeTruthy();
    expect(screen.getByText(COPY.pickFirst)).toBeTruthy();
  });

  it.each([
    [
      'live_posts_exhausted',
      { cap: 2 },
      'You already have 2 posts live — withdraw one in You’re in to post again.',
    ],
    [
      'games_per_week_booked',
      { week: '2026-09-28' },
      'Your games for the week from 28 Sep are already booked.',
    ],
    ['you_play_then', undefined, COPY.refused.you_play_then],
    ['nobody_fits_then', undefined, COPY.refused.nobody_fits_then],
    ['court_hour_not_for_sale', undefined, COPY.refused.court_hour_not_for_sale],
  ] as const)(
    'says %s under the button, in the helper’s place, and stays',
    async (code, details, words) => {
      await openPosting();
      transport.on('POST', postsPath(CREW.id), () =>
        json<Wire['ErrorResponse']>(
          { code, message: 'refused', trace_id: 'trace-test', details: details ?? null },
          409,
        ),
      );
      await pickSaturdayEvening();

      fireEvent.press(postButton());

      expect(await screen.findByRole('alert', { name: words })).toBeTruthy();
      expect(screen).toHavePathname(`/play/group/${CREW.id}/post`);
    },
  );

  it('lets a guard go with the pick it was said about', async () => {
    await openPosting();
    transport.on('POST', postsPath(CREW.id), () => errorResponse(409, 'you_play_then'));
    await pickSaturdayEvening();
    fireEvent.press(postButton());
    expect(await screen.findByRole('alert', { name: COPY.refused.you_play_then })).toBeTruthy();

    fireEvent.press(cellOf(SAT, 'EVENING'));
    fireEvent.press(await screen.findByRole('button', { name: COPY.sheet.remove }));

    expect(await screen.findByText(COPY.pickFirst)).toBeTruthy();
    expect(screen.queryByRole('alert', { name: COPY.refused.you_play_then })).toBeNull();
  });

  it('opens the payment setup with nothing saved, and posts once a card is', async () => {
    const SETUP_PATH = '/api/v1/players/me/payment-methods/setup';
    const TERMS_PATH = '/api/v1/players/me/payment-methods/terms';
    const SAVE_PATH = '/api/v1/players/me/payment-methods/confirmation';
    stubPaymentMethod(transport, null);
    transport.on('POST', SETUP_PATH, () =>
      json<Wire['PaymentSetupResponse']>(
        {
          setup_id: 'seti_1',
          publishable_key: 'pk_test_rakieta',
          terms_version: PAYMENT_TERMS_IN_FORCE,
        },
        201,
      ),
    );
    transport.on('POST', TERMS_PATH, () =>
      json<Wire['PaymentTermsResponse']>({ client_secret: 'seti_1_secret' }),
    );
    transport.on('POST', SAVE_PATH, () => {
      stubPaymentMethod(transport, VISA_4312);
      return json<Wire['PaymentMethodResponse']>({
        method: VISA_4312,
        terms_needed: false,
        terms_version: PAYMENT_TERMS_IN_FORCE,
      });
    });
    transport.on('POST', postsPath(CREW.id), () => json(postedAnswer(), 201));
    await openPosting();
    await pickSaturdayEvening();

    fireEvent.press(postButton());

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(screen.getByText(COPY.paymentFirst)).toBeTruthy();
    expect(posts()).toHaveLength(0);

    fireEvent.press(await screen.findByLabelText('Card'));
    fireEvent.press(screen.getByLabelText(PAYMENTS_COPY.continue));
    fireEvent.changeText(await screen.findByLabelText(FAKE_CARD_NUMBER), TEST_CARDS.saves);
    fireEvent.press(screen.getByLabelText(PAYMENTS_COPY.saveTheCard));
    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.accept));

    await waitFor(() => expect(posts()).toHaveLength(1));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  });
});
