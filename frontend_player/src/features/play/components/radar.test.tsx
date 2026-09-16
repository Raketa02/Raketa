/**
 * **The Radar pane**, walked the way a player walks it: the real route tree, the real shell,
 * the real stores and only `fetch` faked — and the field's touches driven at its responder.
 *
 * What is asserted here is the set of decisions a build session could quietly undo, most of
 * them [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7's:
 *
 * - **The reading is asked for on the pane, per sport, and held**: one `POST /radar` per sport,
 *   none on a flip back inside the window.
 * - **The three states at three widths**: a face at 18 km across, a face with its level at 10,
 *   the card at 5,4 — and ± walks the ladder and greys at the ends.
 * - **A tap on a face flies, lands at 3 km and selects**; the selected card survives a zoom
 *   out; the field deselects; ◉ homes.
 * - **The footer counts points in view and off screen**, switches its hint on the zoom state,
 *   and says the empty, loading and failing sentences.
 * - **The chip is the reading's own number** through the deck's own sentence.
 * - **The sport chips refetch and clear the selection**, keeping the view.
 * - **The view survives a tab switch**; a cold start opens at home.
 * - **The pinch is continuous and the next ± snaps**; a drag moves the view and recounts.
 * - **A card opens the record sheet, read-only.**
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { AccessibilityInfo } from 'react-native';

import { onlineManager } from '@tanstack/react-query';

import { theme } from '@/shared/ui';

import { RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  GATE_USER,
  PROFILE_SURFACE_SERVED,
  launchSignedIn,
  resetHaptics,
  stubGate,
  stubHaptics,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeHaptics } from '@/test-support/platform';
import { claimsThePress, drag, pinch } from '@/test-support/radarTouch';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FLY_TO_WIDTH_KM } from '../domain/radarGeometry';
import { usePlayPreferences } from '../store/playPreferences.store';
import { useRadarView } from '../store/radarView.store';
import { endPlaySession } from '../store/playSession.store';

import { radarTileLabel } from './accessibilityPresentation';
import { PANE_LABEL, WIDEN_IN_YOU, wantToPlayYouChip } from './deckPresentation';
import {
  BACK_TO_YOU_LABEL,
  LOOKING_AROUND,
  PRIVACY_LINE,
  RADAR_FAILED,
  TAP_FOR_THE_FULL_CARD,
  TRY_AGAIN,
  ZOOM_IN_LABEL,
  ZOOM_OUT_LABEL,
  cardDistance,
  emptyHint,
  nobodyInReach,
  offScreen,
  playersInView,
  radarHint,
  reliabilityChip,
  ringLabel,
  tagsInCommon,
  widthAcross,
} from './radarPresentation';

const DECK = '/api/v1/deck';
const RADAR = '/api/v1/radar';
const PLAYERS = '/api/v1/players';
const OWN_RECORD = '/api/v1/players/me/record';

const SEARCH_ID = 'd0d1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const HERE = 'A+050612+0019938';

const FILIP = 'aaaaaaaa-0000-4000-8000-000000000001';
const MAREK = 'aaaaaaaa-0000-4000-8000-000000000002';
const KAROL = 'aaaaaaaa-0000-4000-8000-000000000003';
const MAGDA = 'aaaaaaaa-0000-4000-8000-000000000004';
const PIOTR = 'aaaaaaaa-0000-4000-8000-000000000005';
const ZOFIA = 'aaaaaaaa-0000-4000-8000-000000000006';

/** The field, as the harness lays it out: a 390 × 600 box, the footer 70 pt of it. */
const FIELD = { width: 390, height: 600 } as const;
const FOOTER = 70;

function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.7,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

/** One row of a reading. The overlap term is what makes *1 tag in common* true. */
function row(
  name: string,
  playerId: string,
  distanceKm: number,
  bearingDeg: number,
  over: Partial<Wire['CandidateSchema']> = {},
): Wire['CandidateSchema'] {
  return {
    player_id: playerId,
    fit: 76,
    distance_km: distanceKm,
    bearing_deg: bearingDeg,
    ratings: [{ sport: 'PADEL', level: 2.6 }],
    player_card: {
      name,
      area_code: HERE,
      social_tags: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
      level: 2.6,
      band: 'Established',
      range: { low: 2.4, high: 2.8 },
      player_score: 88,
    },
    concerns: [],
    terms: [
      {
        term: 'PLAYING_STYLE',
        weight: 10,
        value: 0.6,
        contribution: 6,
        evidence: {
          kind: 'playing_style',
          matched: ['PLAYS_TO_WIN'],
          complementary: [],
          clashing: [],
        },
      },
    ],
    degraded_terms: [],
    modifiers: [],
    liveness_reasons: [],
    ...over,
  };
}

/** The cast, around a viewer in Kraków with a 10 km reach — six padel players, one 9,5 km out. */
const CAST: readonly Wire['CandidateSchema'][] = [
  row('Karol T.', KAROL, 1.2, 130, { fit: 97 }),
  row('Filip N.', FILIP, 1.9, 47),
  row('Magda P.', MAGDA, 2.4, 250, { fit: 59 }),
  // Rated in two sports: `card.level` is his level in the reading's sport, as the contract says.
  row('Marek Z.', MAREK, 4.8, 20, {
    ratings: [
      { sport: 'PADEL', level: 2.92 },
      { sport: 'TENNIS', level: 3.4 },
    ],
    player_card: { ...row('Marek Z.', MAREK, 4.8, 20).player_card, level: 2.92 },
  }),
  row('Piotr W.', PIOTR, 9.5, 300),
];

interface ReadingOver {
  readonly candidates?: readonly Wire['CandidateSchema'][];
  readonly wantToPlayYou?: number;
  readonly sport?: Wire['Sport'];
  readonly searchId?: string;
}

function reading({
  candidates = CAST,
  wantToPlayYou,
  sport = 'PADEL',
  searchId = SEARCH_ID,
}: ReadingOver = {}): Wire['ShortlistResponse'] {
  return {
    search: {
      search_id: searchId,
      at: '2026-09-16T18:00:00Z',
      surface: 'RADAR',
      mode: null,
      ruleset_version: 'ruleset-v1',
      engine_version: 'matchfit-v1',
      optimised_for: 'SEARCHER',
      index_stale: false,
      pool: {
        sport,
        radius_km_used: 10,
        players_in_range: candidates.length,
        window: 'THIS_WEEK',
        post_gate: true,
        ...(wantToPlayYou === undefined ? {} : { want_to_play_you: wantToPlayYou }),
      },
      radius_clamp: false,
      sorts_available: [],
      rung_offers: null,
      my_area_code: HERE,
      prompts: [],
    },
    candidates: [...candidates],
  };
}

/** Your own record, for the tile at the origin: a poster, no photograph. */
function ownRecord(): Wire['PlayerRecordResponse'] {
  return {
    is_self: true,
    name: 'ada',
    nickname: 'ada',
    area_code: HERE,
    social_tags: [],
    sports: [{ sport: 'PADEL', level: 2.7, band: 'Established' }],
  };
}

/** Filip's record, as `GET /players/{id}/record` answers when the sheet asks for it. */
function filipsRecord(): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    name: 'Filip N.',
    nickname: 'filip_n',
    area_code: HERE,
    social_tags: ['PLAYS_TO_WIN'],
    sports: [{ sport: 'PADEL', level: 2.6, band: 'Established' }],
    skill: {
      sport: 'PADEL',
      level: 2.6,
      band: 'Established',
      confidence: 40,
      counted_games: 3,
      likely_range: { low: 2.4, high: 2.8 },
      last_five: ['WIN', 'LOSS', 'WIN'],
    },
    reliability: {
      player_score: 88,
      strands: [{ strand: 'SHOWS_UP', good: 3, opportunities: 3, pct: 100 }],
    },
    variety: { distinct_opponents: 3, times_on_court: 3 },
  };
}

/** A face or a card, as it is spoken — the one name a person carries through every state. */
const tile = (name: string, distanceKm: number, level = 2.6, sportName = 'Padel') =>
  radarTileLabel({ name, distance: cardDistance(distanceKm), sportName, level });

const FILIP_TILE = tile('Filip N.', 1.9);
const MAREK_TILE = tile('Marek Z.', 4.8, 2.92);
const KAROL_TILE = tile('Karol T.', 1.2);
const PIOTR_TILE = tile('Piotr W.', 9.5);

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubHaptics(fakeHaptics());
  jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
  stubGate(transport, { ratings: [rating('PADEL'), rating('TENNIS')], hasPlayerProfile: true });
  stubProfileOptions(transport);
  // The reach: 10 km, the spec's own default — 18 km across to open, 30 at the widest.
  stubProfileSurface(transport, { ...PROFILE_SURFACE_SERVED, search_radius_km: 10 });
  stubInterest(transport, { outgoing: [], mutual: [], outstanding: [] });
  transport.on('POST', DECK, () => json(reading({ candidates: [], sport: 'PADEL' })));
  transport.on('POST', RADAR, () => json(reading({ wantToPlayYou: 3 })));
  transport.on('GET', OWN_RECORD, () => json(ownRecord()));
  transport.on('GET', `${PLAYERS}/${FILIP}/record?sport=PADEL`, () => json(filipsRecord()));
});

afterEach(async () => {
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
  jest.restoreAllMocks();
  resetHaptics();
  transport.restore();
  onlineManager.setOnline(true);
  queryClient.clear();
  useToastQueue.getState().clear();
  usePlayPreferences.getState().reset();
  useRadarView.getState().reset();
  endPlaySession();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * Lay the field out: the renderer measures nothing, so the box is handed to it — **at the
 * handler, not through `fireEvent`**, for `swipe.ts`'s reason: `fireEvent` asks the field's
 * responder whether it wants the touch before delivering any event to it, and *no on the
 * press* is exactly what the field answers, because a face and a card are doors.
 */
function layOut() {
  act(() => {
    (screen.getByTestId('radar-field').props.onLayout as (e: unknown) => void)({
      nativeEvent: { layout: { x: 0, y: 0, ...FIELD } },
    });
    (screen.getByTestId('radar-footer').props.onLayout as (e: unknown) => void)({
      nativeEvent: {
        layout: { x: 0, y: FIELD.height - FOOTER, width: FIELD.width, height: FOOTER },
      },
    });
  });
}

/** A signed-in player on the Radar pane, with the reading landed and the field laid out. */
async function openRadar() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Players'));
  await waitFor(() => expect(screen).toHavePathname('/players'));
  fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
  await screen.findByTestId('radar-field');
  layOut();
  await screen.findByLabelText(FILIP_TILE);
}

const field = () => screen.getByTestId('radar-field');
const readingBodies = () => transport.requestsTo('POST', RADAR).map((request) => request.body);
const zoomIn = () => fireEvent.press(screen.getByLabelText(ZOOM_IN_LABEL));
const zoomOut = () => fireEvent.press(screen.getByLabelText(ZOOM_OUT_LABEL));
const home = () => fireEvent.press(screen.getByLabelText(BACK_TO_YOU_LABEL));
const cards = () => screen.queryAllByText(TAP_FOR_THE_FULL_CARD);

/**
 * Let a flight, a ± or a settle run to its end — the harness's fake clock advanced past the
 * longest of them in one step, inside `act`, so every frame lands before the next line reads
 * the field. Not `waitFor`: polling a running animation under fake timers costs the harness
 * tens of megabytes a poll, and a landing is a fact the clock can be driven to rather than
 * waited on.
 */
function travelled(): void {
  act(() => {
    jest.advanceTimersByTime(theme.motion.flyTo + theme.motion.settle);
  });
}

/**
 * The view has **landed** at a width: a ±, a flight or a pinch has ended and the store holds
 * it. Read off the store rather than the counter, because the counter prints *10 km across*
 * for a fifth of a kilometre either side of ten and would let a walk assert the closer state
 * while the field is still a hair wide of it.
 */
function landedAt(km: number): void {
  travelled();
  expect(useRadarView.getState().view?.widthKm).toBe(km);
}

/** ◉ has landed: nothing kept, which is home. */
function atHome(): void {
  travelled();
  expect(useRadarView.getState().view).toBeUndefined();
}

/** Every string a node draws, in order — what a listener would hear the element say. */
function textOf(node: ReturnType<typeof screen.getByTestId>): string {
  const parts: string[] = [];
  const walk = (child: unknown) => {
    if (typeof child === 'string') parts.push(child);
    else if (Array.isArray(child)) child.forEach(walk);
    else if (child !== null && typeof child === 'object' && 'children' in child)
      walk((child as { children: unknown }).children);
  };
  walk(node.children);
  return parts.join(' ');
}

/** Whether a control announces itself disabled — the cluster's ± at the ladder's ends. */
const disabled = (label: string) =>
  screen.getByRole('button', { name: label }).props.accessibilityState?.disabled === true;

/** The viewer's tile and the rings are hidden from a listener on purpose; a walk still looks. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const you = () => screen.queryByText('you', HIDDEN_TOO);
const ring = (km: number) => screen.queryByText(ringLabel(km), HIDDEN_TOO);

describe('the reading', () => {
  it('asks for the sport the pane is on, once, and draws every row as a face', async () => {
    await openRadar();

    expect(readingBodies()).toEqual([{ sport: 'PADEL' }]);
    for (const label of [FILIP_TILE, MAREK_TILE, KAROL_TILE, PIOTR_TILE]) {
      expect(screen.getByRole('button', { name: label })).toBeTruthy();
    }
    expect(screen.getByText(widthAcross(18))).toBeTruthy();
    expect(you()).toBeTruthy();
    // 18 km across on a 390 pt field: the 2, 5 and 10 km rings are drawn, and 1 km is not.
    expect(ring(2)).toBeTruthy();
    expect(ring(5)).toBeTruthy();
    expect(ring(10)).toBeTruthy();
    expect(ring(1)).toBeNull();
  });

  it('draws the chip off the reading, through the deck’s own sentence', async () => {
    await openRadar();
    expect(screen.getByText(wantToPlayYouChip(3))).toBeTruthy();
  });

  it('draws no chip at nought — the count is omitted on a reading', async () => {
    transport.on('POST', RADAR, () => json(reading()));
    await openRadar();
    expect(screen.queryByText(/want to play you/)).toBeNull();
  });

  it('holds the reading across a flip to the deck and back inside the window', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.deck }));
    await screen.findByRole('button', { name: PANE_LABEL.deck, selected: true });
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByTestId('radar-field');

    expect(readingBodies()).toHaveLength(1);
  });

  it('refetches for a sport the player switches to, and clears the selection while keeping the view', async () => {
    transport.on('POST', RADAR, (request) =>
      json(
        (request.body as { sport: string }).sport === 'TENNIS'
          ? reading({
              sport: 'TENNIS',
              candidates: [
                row('Zofia B.', ZOFIA, 3.1, 90, {
                  ratings: [{ sport: 'TENNIS', level: 3.1 }],
                  player_card: { ...row('Zofia B.', ZOFIA, 3.1, 90).player_card, level: 3.1 },
                }),
              ],
            })
          : reading({ wantToPlayYou: 3 }),
      ),
    );
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
    // At 10 km across only the selected player is a card.
    expect(cards()).toHaveLength(1);

    fireEvent.press(screen.getByLabelText('Tennis'));
    await screen.findByRole('button', { name: tile('Zofia B.', 3.1, 3.1, 'Tennis') });

    expect(readingBodies()).toEqual([{ sport: 'PADEL' }, { sport: 'TENNIS' }]);
    // The view is kept — 10 km across, centred where the flight left it — and nobody is
    // selected on the tennis reading: Zofia is a face with her level, not a card.
    expect(screen.getByText(widthAcross(10))).toBeTruthy();
    expect(cards()).toHaveLength(0);
    expect(screen.queryByRole('button', { name: FILIP_TILE })).toBeNull();
    // The padel selection is kept for padel, and read by no other sport.
    expect(useRadarView.getState().selection).toEqual({ sport: 'padel', playerId: FILIP });
  });
});

describe('the three states by width', () => {
  it('is faces at 18, faces with their level at 10, and cards at 5,4 — and ± walks the ladder', async () => {
    await openRadar();
    // Wide: a face and nothing else. `2,60` is the level — under no face at this width.
    expect(screen.queryByText('2,60')).toBeNull();
    expect(cards()).toHaveLength(0);
    expect(screen.getByText(radarHint('wide'))).toBeTruthy();

    zoomIn();
    landedAt(10);
    expect(screen.getByText(widthAcross(10))).toBeTruthy();
    // Closer: the level under each face, in the reading's sport — Marek's padel 2,92, not
    // his tennis 3,40.
    expect(screen.getAllByText('2,60').length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText('2,92')).toBeTruthy();
    expect(screen.queryByText('3,40')).toBeNull();
    expect(cards()).toHaveLength(0);

    zoomIn();
    landedAt(5.4);
    expect(screen.getByText(widthAcross(5.4))).toBeTruthy();
    // Closest: every row is a card, and the hint says what a card leads to.
    expect(cards().length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText(radarHint('closest'))).toBeTruthy();
    expect(screen.getAllByText(reliabilityChip(88).split(' ')[1] ?? '').length).toBeGreaterThan(0);
    expect(screen.getAllByText(tagsInCommon(1)).length).toBeGreaterThan(0);
  });

  it('greys ± at the ends of the ladder: 30 at the widest for a 10 km reach, 1,5 at the floor', async () => {
    await openRadar();
    expect(disabled(ZOOM_OUT_LABEL)).toBe(false);

    zoomOut();
    landedAt(30);
    expect(screen.getByText(widthAcross(30))).toBeTruthy();
    expect(disabled(ZOOM_OUT_LABEL)).toBe(true);
    expect(disabled(ZOOM_IN_LABEL)).toBe(false);

    for (const stop of [18, 10, 5.4, 3, 1.5]) {
      zoomIn();
      landedAt(stop);
      expect(screen.getByText(widthAcross(stop))).toBeTruthy();
    }
    expect(disabled(ZOOM_IN_LABEL)).toBe(true);
    expect(disabled(ZOOM_OUT_LABEL)).toBe(false);
  });

  it('draws the card line for line: face, name, distance, one sport row per rated sport, the two scores, the tags, the door', async () => {
    await openRadar();
    zoomIn();
    landedAt(10);
    zoomIn();
    landedAt(5.4);

    const marek = textOf(screen.getByRole('button', { name: MAREK_TILE }));
    expect(marek).toContain('Marek Z.');
    expect(marek).toContain(cardDistance(4.8));
    // The reading's sport first, then tennis — every sport he is rated in.
    expect(marek).toMatch(/Padel.*2,92.*Tennis.*3,40/s);
    expect(marek).toMatch(/76 fit/);
    expect(marek).toMatch(/88 reliability/);
    expect(marek).toContain(tagsInCommon(1));
    expect(marek).toContain(TAP_FOR_THE_FULL_CARD);
  });
});

describe('tapping, flying, selecting', () => {
  it('flies to a face, lands at 3 km centred on them, and selects them', async () => {
    await openRadar();

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));

    landedAt(FLY_TO_WIDTH_KM);
    expect(screen.getByText(widthAcross(FLY_TO_WIDTH_KM))).toBeTruthy();
    expect(useRadarView.getState().selection).toEqual({ sport: 'padel', playerId: FILIP });
    // At 3 km across everybody is a card, Filip among them.
    expect(cards()).toHaveLength(CAST.length);
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    // Centred on Filip at 130 pt per km: Karol, 1,2 km from the viewer, is still inside the
    // box; Magda west, Marek north and Piotr north-west are off screen, and the count says so.
    expect(screen.getByText(offScreen(3))).toBeTruthy();
    expect(screen.getByText(playersInView(2))).toBeTruthy();
  });

  it('keeps the selected card when the view zooms back out, above every face', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
    zoomOut();
    landedAt(18);

    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    expect(textOf(screen.getByRole('button', { name: MAREK_TILE }))).not.toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    // The hint follows the zoom state, never the selection.
    expect(screen.getByText(radarHint('wide'))).toBeTruthy();
  });

  it('deselects on a tap on empty field and keeps the zoom; ◉ homes and deselects', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
    expect(cards()).toHaveLength(1);

    fireEvent.press(screen.getByTestId('radar-field-empty', HIDDEN_TOO));

    await waitFor(() => expect(cards()).toHaveLength(0));
    expect(useRadarView.getState().selection).toBeUndefined();
    // The zoom stays.
    expect(screen.getByText(widthAcross(10))).toBeTruthy();
    expect(useRadarView.getState().view?.widthKm).toBe(10);

    home();

    atHome();
    expect(screen.getByText(widthAcross(18))).toBeTruthy();
    expect(useRadarView.getState().selection).toBeUndefined();
    expect(screen.getByText(offScreen(0))).toBeTruthy();
  });

  it('switches selection and flies when another face is tapped', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
    expect(cards()).toHaveLength(1);

    fireEvent.press(screen.getByRole('button', { name: MAREK_TILE }));

    landedAt(FLY_TO_WIDTH_KM);
    expect(useRadarView.getState().selection).toEqual({ sport: 'padel', playerId: MAREK });
    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: MAREK_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).not.toContain(
      TAP_FOR_THE_FULL_CARD,
    );
  });

  it('lands at once under reduced motion', async () => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
    await openRadar();

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));

    expect(screen.getByText(widthAcross(FLY_TO_WIDTH_KM))).toBeTruthy();
    expect(useRadarView.getState().view?.widthKm).toBe(FLY_TO_WIDTH_KM);
    expect(useRadarView.getState().selection).toEqual({ sport: 'padel', playerId: FILIP });
  });

  it('opens the record sheet from a card, read-only, and closes back to the field', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Let’s play|Let's play/ })).toBeNull();
    fireEvent.press(screen.getByLabelText(recordCloseLabel(false)));
    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
  });
});

describe('the footer', () => {
  it('counts the points in view and says all of them at home, and how many are off screen after a flight', async () => {
    await openRadar();
    expect(screen.getByText(playersInView(5))).toBeTruthy();
    expect(screen.getByText(offScreen(0))).toBeTruthy();
    expect(screen.getByText(radarHint('wide'))).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    expect(screen.getByText(offScreen(3))).toBeTruthy();
    expect(screen.getByText(playersInView(2))).toBeTruthy();
    expect(screen.getByText(radarHint('closest'))).toBeTruthy();
  });

  it('says the empty reading with the reach and the sport, and still draws you and the rings', async () => {
    transport.on('POST', RADAR, () => json(reading({ candidates: [] })));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByTestId('radar-field');
    layOut();

    expect(
      await screen.findByText(nobodyInReach({ reachKm: 10, sportName: 'Padel' })),
    ).toBeTruthy();
    expect(screen.getByText(emptyHint())).toBeTruthy();
    expect(emptyHint()).toContain(WIDEN_IN_YOU);
    expect(you()).toBeTruthy();
    expect(ring(5)).toBeTruthy();
    expect(ring(10)).toBeTruthy();
  });

  it('says Looking around… over the privacy line while the reading is on its way', async () => {
    let answer: ((response: Response) => void) | undefined;
    transport.on('POST', RADAR, () => new Promise<Response>((resolve) => (answer = resolve)));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByTestId('radar-field');
    layOut();

    expect(await screen.findByText(LOOKING_AROUND)).toBeTruthy();
    expect(screen.getByText(PRIVACY_LINE)).toBeTruthy();
    expect(you()).toBeTruthy();

    await act(async () => {
      answer?.(json(reading()));
    });
    expect(await screen.findByLabelText(FILIP_TILE)).toBeTruthy();
  });

  it('says the failure and offers Try again, which reads again', async () => {
    transport.on('POST', RADAR, () => errorResponse(503, 'matchmaking_unavailable'));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByTestId('radar-field');
    layOut();

    expect(await screen.findByText(RADAR_FAILED)).toBeTruthy();
    transport.on('POST', RADAR, () => json(reading()));

    fireEvent.press(screen.getByRole('button', { name: TRY_AGAIN }));

    expect(await screen.findByLabelText(FILIP_TILE)).toBeTruthy();
    expect(readingBodies()).toHaveLength(2);
  });
});

describe('the view is kept while the app lives', () => {
  it('survives a tab switch: back on the radar, the flight’s view and the selection stand', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    zoomOut();
    landedAt(5.4);
    zoomOut();
    landedAt(10);

    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(screen.getByLabelText('Players'));
    await waitFor(() => expect(screen).toHavePathname('/players'));
    // Players opens on Deck (ADR-0169 §1); the radar is where it was left.
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
    await screen.findByTestId('radar-field');
    layOut();

    expect(await screen.findByText(widthAcross(10))).toBeTruthy();
    await waitFor(() => expect(cards()).toHaveLength(1));
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    expect(useRadarView.getState().view?.widthKm).toBe(10);
  });
});

describe('the pinch and the drag', () => {
  it('never claims the press: a face and a card are doors', async () => {
    await openRadar();
    expect(claimsThePress(field(), [200, 300])).toBe(false);
  });

  it('pinches continuously around the fingers, and the next ± snaps to the ladder', async () => {
    await openRadar();

    // Two fingers 100 pt apart spread to 200: half the width, 9 km across.
    expect(
      pinch(
        field(),
        [
          [145, 252],
          [245, 252],
        ],
        [
          [95, 252],
          [295, 252],
        ],
      ),
    ).toBe(true);

    landedAt(9);
    expect(screen.getByText(widthAcross(9))).toBeTruthy();
    expect(screen.getAllByText('2,60').length).toBeGreaterThanOrEqual(3);

    zoomIn();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
  });

  it('holds the pinch between the floor and the widest stop', async () => {
    await openRadar();
    // Fingers closing from 200 to 10 apart would ask for 360 km across; the widest is 30.
    pinch(
      field(),
      [
        [95, 252],
        [295, 252],
      ],
      [
        [190, 252],
        [200, 252],
      ],
    );
    landedAt(30);
    expect(screen.getByText(widthAcross(30))).toBeTruthy();
    expect(disabled(ZOOM_OUT_LABEL)).toBe(true);
  });

  it('drags the view with no inertia and recounts the footer', async () => {
    await openRadar();
    expect(screen.getByText(offScreen(0))).toBeTruthy();

    // The field dragged 200 pt up — the view moves south by 8,6 km, inside the reach — carries
    // Marek and Piotr, the two north of the viewer, off the top; the count says so.
    expect(drag(field(), [200, 500], [200, 300])).toBe(true);

    expect(screen.getByText(offScreen(2))).toBeTruthy();
    expect(screen.getByText(playersInView(3))).toBeTruthy();
    expect(screen.getByText(widthAcross(18))).toBeTruthy();
    const kept = useRadarView.getState().view;
    expect(kept?.widthKm).toBe(18);
    expect(kept?.centre.y).toBeLessThan(0);
  });

  it('rubber-bands at the reach’s edge: a drag past it settles back to it', async () => {
    await openRadar();

    // 600 pt of drag at 18 km across is nearly 28 km — past a 10 km reach.
    drag(field(), [200, 100], [200, 700]);

    travelled();
    const kept = useRadarView.getState().view;
    expect(kept).toBeDefined();
    expect(Math.hypot(kept?.centre.x ?? 0, kept?.centre.y ?? 0)).toBeCloseTo(10, 5);
  });
});

describe('a player rated in one sport', () => {
  it('sees no sport chips over the field', async () => {
    stubGate(transport, { ratings: [rating('PADEL')], hasPlayerProfile: true });
    await openRadar();
    expect(screen.queryByLabelText('Tennis')).toBeNull();
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
  });
});

/** The signed-in player is the viewer: the tile at the origin is theirs. */
it('draws the viewer’s tile from their own record', async () => {
  await openRadar();
  expect(transport.requestsTo('GET', OWN_RECORD)).toHaveLength(1);
  expect(GATE_USER.id).toBeTruthy();
});
