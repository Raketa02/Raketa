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
 * - **The three states at three widths**: a face at 18 km across, a face with its level at 10
 *   and at 5,4 — and ± walks the ladder and greys at the ends. **The card is the selection's
 *   alone** (ADR-0176 §3): nobody is a card until they are tapped, at any width.
 * - **A tap on a face flies, lands at 3 km — or the width already held if narrower — and
 *   selects**; the selected card survives a zoom out and a zoom in; the field deselects; ◉
 *   homes.
 * - **The footer counts points in view and off screen**, switches its hint on the zoom state,
 *   and says the empty, loading and failing sentences.
 * - **The chip is the reading's own number** through the deck's own sentence.
 * - **The sport chips refetch and clear the selection**, keeping the view.
 * - **The view survives a tab switch**; a cold start opens at home.
 * - **The pinch is continuous and the next ± snaps**; a drag moves the view and recounts. Both
 *   are `react-native-gesture-handler`'s, fired through its own jest utilities
 *   (`test-support/radarTouch`), and the pan claims nothing short of the intent distance.
 * - **A card opens the record sheet, with the foot the relation demands** (ADR-0174 §4,
 *   [#464](https://github.com/Raketa02/Raketa/issues/464)): the two buttons for a stranger, a
 *   liker's line above them, the reader's own yes beside *Not today*, a match with its chat
 *   door, a shared court named with no buttons. A yes and a pass post with the reading's
 *   origin, close the sheet, mark the card's last line and keep the row; a refusal takes the
 *   mark back; the outcomes are the deck's — the spoken line, the one toast, the yes screen;
 *   the cap withholds a stranger's yes with the deck's sentence; the chip counts down on a
 *   liker's mutual.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { AccessibilityInfo } from 'react-native';
import { Line } from 'react-native-svg';

import { onlineManager } from '@tanstack/react-query';

import { theme } from '@/shared/ui';

import { standingLine } from '@/features/challenges/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  CHALLENGES_PATH,
  GATE_USER,
  launchIntoClassicPlay,
  outgoingYes,
  PROFILE_SURFACE_SERVED,
  resetHaptics,
  stubChallenges,
  stubConversations,
  stubGate,
  stubHaptics,
  stubInterest,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeHaptics } from '@/test-support/platform';
import { drag, panClaimsAfter, pinch, pinchLiftingOneFingerFirst } from '@/test-support/radarTouch';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FLY_TO_WIDTH_KM, homeView, pinched, widestWidthKm } from '../domain/radarGeometry';
import { usePlayPreferences } from '../store/playPreferences.store';
import { useRadarView } from '../store/radarView.store';
import { endPlaySession } from '../store/playSession.store';

import { radarTileLabel } from './accessibilityPresentation';
import {
  PANE_LABEL,
  WIDEN_IN_YOU,
  interestAnnouncement,
  mutualToast,
  passedAnnouncement,
  wantToPlayYouChip,
} from './deckPresentation';
import { CAP_REACHED_SENTENCE, playErrorMessage } from './playErrorMessage';
import {
  ANSWERED_LINE,
  BACK_TO_YOU_LABEL,
  LOOKING_AROUND,
  PRIVACY_LINE,
  RADAR_FAILED,
  TAP_FOR_THE_FULL_CARD,
  TRY_AGAIN,
  WANTS_TO_PLAY_YOU,
  YOURE_MATCHED,
  YOU_SAID_YES,
  ZOOM_IN_LABEL,
  ZOOM_OUT_LABEL,
  cardDistance,
  emptyHint,
  footAnswerLabels,
  nobodyInReach,
  offScreen,
  playersInView,
  radarHint,
  reliabilityChip,
  ringLabel,
  stackHint,
  stackLabel,
  tagsInCommon,
  widthAcross,
} from './radarPresentation';

const DECK = '/api/v1/deck';
const RADAR = '/api/v1/radar';
const PLAYERS = '/api/v1/players';
const OWN_RECORD = '/api/v1/players/me/record';
const INTEREST = '/api/v1/interest';
const PASSES = '/api/v1/passes';

const SEARCH_ID = 'd0d1a2b3-c4d5-4e6f-8a9b-0c1d2e3f4a5b';
const HERE = 'A+050612+0019938';
const ME = GATE_USER.id;
const CHALLENGE = 'cccccccc-0000-4000-8000-00000000000c';
const ROOM = 'cccccccc-0000-4000-8000-000000000007';

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

/** A yes's reply: one-sided, or mutual — naming the court it opened, or none. */
function expressed(
  mutual: boolean,
  challengeId: string | null = null,
  outstanding = 3,
): Wire['ExpressedInterestResponse'] {
  return {
    interest: outgoingYes(FILIP, 'PADEL'),
    mutual,
    challenge_id: challengeId,
    outstanding: { sport: 'PADEL', outstanding, cap: 20, ttl_days: 21 },
  };
}

/** Where padel stands: `outstanding` of a cap of 20, with the two lists beside it. */
function interest(
  outstanding: number,
  lists: Partial<Pick<Wire['InterestListResponse'], 'outgoing' | 'mutual'>> = {},
): Wire['InterestListResponse'] {
  return {
    outgoing: [],
    mutual: [],
    outstanding: [{ sport: 'PADEL', outstanding, cap: 20, ttl_days: 21 }],
    ...lists,
  };
}

/** A court between the viewer and Filip, as `GET /challenges` lists it — ours, everybody in. */
function courtWithFilip(
  standing: Wire['Standing'] = 'ON',
  over: Partial<Wire['ChallengeSchema']> = {},
): Wire['ChallengeSchema'] {
  return {
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    organiser_id: ME,
    standing,
    opened_at: '2026-09-12T18:00:00Z',
    seats: [
      { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'ada' },
      { side: 'B', player_id: FILIP, answer: 'ACCEPTED', name: 'Filip N.' },
    ],
    ...over,
  };
}

/** The room that court opened, listed. */
function roomWithFilip(): Wire['ConversationRowSchema'] {
  const both = [
    { player_id: ME, name: 'ada' },
    { player_id: FILIP, name: 'Filip N.' },
  ];
  return {
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: null,
    sport: 'PADEL',
    members: both,
    people: both,
    last_entry: null,
  };
}

/** The challenge a mutual named, as the yes screen reads it: the two of us, `ON` from birth. */
function matchedWithFilip(): Wire['ChallengeDetailResponse'] {
  return {
    read_at: '2026-09-16T18:00:00Z',
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    mode: null,
    window: null,
    organiser_id: FILIP,
    standing: 'ON',
    opened_at: '2026-09-16T18:00:00Z',
    seats: [
      { side: 'A', player_id: FILIP, answer: 'ACCEPTED', name: 'Filip N.' },
      { side: 'B', player_id: ME, answer: 'ACCEPTED', name: 'ada' },
    ],
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
  transport.on('POST', INTEREST, () => json(expressed(false), 201));
  transport.on('POST', PASSES, () => noContent());
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
  await launchIntoClassicPlay(transport);
  fireEvent.press(await screen.findByLabelText('Players'));
  await waitFor(() => expect(screen).toHavePathname('/players'));
  fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));
  await screen.findByTestId('radar-field');
  layOut();
  await screen.findByLabelText(FILIP_TILE);
}

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
    // The landing is spoken to JavaScript through `runOnJS` — a microtask the fake clock
    // holds until it next moves, however little.
    jest.advanceTimersByTime(0);
  });
}

/**
 * The view has **landed** at a width: a ±, a flight or a pinch has run to its end, and the
 * counter says so. Only after the clock has been driven past the flight: the counter prints
 * *10 km across* for a fifth of a kilometre either side of ten, so read mid-flight it would let
 * a walk assert the closer state while the field is still a hair wide of it.
 */
function landedAt(km: number): void {
  travelled();
  expect(screen.getByText(widthAcross(km))).toBeTruthy();
}

/** ◉ has landed: the opening width, and the whole cast in view. */
function atHome(): void {
  landedAt(18);
  expect(screen.getByText(offScreen(0))).toBeTruthy();
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

    // The padel selection was kept for padel: back on it, Filip's card is the one card at 10.
    fireEvent.press(screen.getByLabelText('Padel'));
    await screen.findByRole('button', { name: FILIP_TILE });
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
  });
});

describe('the three states by width', () => {
  it('is faces at 18, faces with their level at 10 and at 5,4 — never a card untapped — and ± walks the ladder', async () => {
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
    // Closest: still faces with their level — the card is the selection's and nobody is
    // selected — and the hint says a tap is what earns one.
    expect(cards()).toHaveLength(0);
    expect(screen.getAllByText('2,60').length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText(radarHint('closest'))).toBeTruthy();
    expect(screen.queryByText(reliabilityChip(88).split(' ')[1] ?? '')).toBeNull();
    expect(screen.queryByText(tagsInCommon(1))).toBeNull();
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
    fireEvent.press(screen.getByRole('button', { name: MAREK_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    // The one card on the field is his; everybody else is a face.
    expect(cards()).toHaveLength(1);
    expect(screen.getAllByText(reliabilityChip(88).split(' ')[1] ?? '')).toHaveLength(1);
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
    // At 3 km across Filip is the one card; everybody else is a face with their level.
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    expect(textOf(screen.getByRole('button', { name: KAROL_TILE }))).not.toContain(
      TAP_FOR_THE_FULL_CARD,
    );
    // Centred on Filip at 130 pt per km: Karol, 1,2 km from the viewer, is still inside the
    // box; Magda west, Marek north and Piotr north-west are off screen, and the count says so.
    expect(screen.getByText(offScreen(3))).toBeTruthy();
    expect(screen.getByText(playersInView(2))).toBeTruthy();
  });

  it('keeps the selected card when the view zooms in and back out, above every face', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    zoomIn();
    landedAt(1.5);
    expect(cards()).toHaveLength(1);

    zoomOut();
    landedAt(3);
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
    // The zoom stays.
    expect(screen.getByText(widthAcross(10))).toBeTruthy();

    home();

    atHome();
    expect(cards()).toHaveLength(0);
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

  it('flies to a face at the width already held when that is narrower than 3 km', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    zoomIn();
    landedAt(1.5);

    // Karol is 1,2 km from the viewer and Filip 1,9: at 260 pt per km the two are 300 pt
    // apart, so Karol is on the field from Filip's spot. A tap on him centres on him and
    // stays at 1,5 — the field never zooms out to show a card.
    fireEvent.press(screen.getByRole('button', { name: KAROL_TILE }));
    landedAt(1.5);
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: KAROL_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
  });

  it('lands at once under reduced motion', async () => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
    await openRadar();

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));

    expect(screen.getByText(widthAcross(FLY_TO_WIDTH_KM))).toBeTruthy();
    // Selected at once too: zoomed out, and Filip's card is the one card.
    zoomOut();
    zoomOut();
    expect(screen.getByText(widthAcross(10))).toBeTruthy();
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: FILIP_TILE }))).toContain(
      TAP_FOR_THE_FULL_CARD,
    );
  });

  it('opens the record sheet from a card, and closes back to the field', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    fireEvent.press(screen.getByLabelText(recordCloseLabel(false)));
    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
  });
});

/**
 * **The sheet's foot** — what stands between the reader and the person on the card, and the
 * two answers where nothing does (ADR-0174 §4, `the-radar.md` §5, `the-words.md` §26).
 */
describe('the sheet’s foot', () => {
  const FILIP_LABELS = footAnswerLabels('Filip N.');
  const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);
  const spoken = () =>
    (AccessibilityInfo.announceForAccessibilityWithOptions as jest.Mock).mock.calls.map(
      ([message]) => message as string,
    );

  /** Filip's card, tapped: the sheet with his record, and the foot folded. */
  async function openFilipsSheet() {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    await screen.findByText(RECORD_TITLE);
    return within(await screen.findByTestId('radar-sheet-foot'));
  }

  const buttonsIn = (foot: ReturnType<typeof within>) =>
    foot.queryAllByRole('button').map((button) => button.props.accessibilityLabel as string);

  /** Filip's card as drawn on the field — its last line is the one thing an answer changes. */
  const filipsCard = () => textOf(screen.getByRole('button', { name: FILIP_TILE }));

  it('draws the two buttons for a stranger, in the swipe’s reading order, and no line', async () => {
    const foot = await openFilipsSheet();

    expect(buttonsIn(foot)).toEqual([FILIP_LABELS.no, FILIP_LABELS.yes]);
    expect(foot.queryByText(WANTS_TO_PLAY_YOU)).toBeNull();
    expect(foot.queryByText(YOU_SAID_YES)).toBeNull();
    expect(foot.queryByText(YOURE_MATCHED)).toBeNull();
  });

  it('says Wants to play you above the two buttons, exactly for a row carrying the admitting code', async () => {
    transport.on('POST', RADAR, () =>
      json(
        reading({
          candidates: [row('Filip N.', FILIP, 1.9, 47, { inclusion_reason: 'INTEREST_LIFT' })],
        }),
      ),
    );
    const foot = await openFilipsSheet();

    expect(foot.getByText(WANTS_TO_PLAY_YOU)).toBeTruthy();
    expect(buttonsIn(foot)).toEqual([FILIP_LABELS.no, FILIP_LABELS.yes]);
  });

  it('says You said yes beside Not today where the reader has a live yes towards them', async () => {
    stubInterest(transport, interest(1, { outgoing: [outgoingYes(FILIP, 'PADEL')] }));
    const foot = await openFilipsSheet();

    expect(foot.getByText(YOU_SAID_YES)).toBeTruthy();
    expect(buttonsIn(foot)).toEqual([FILIP_LABELS.no]);
  });

  it('says You’re matched with the chat door where their yes came back, and the door opens the room', async () => {
    stubInterest(transport, interest(0, { mutual: [outgoingYes(FILIP, 'PADEL')] }));
    stubChallenges(transport, [courtWithFilip('ON', { organiser_id: FILIP })]);
    stubConversations(transport, [roomWithFilip()]);
    const foot = await openFilipsSheet();

    expect(foot.getByText(YOURE_MATCHED)).toBeTruthy();
    // The door is a join over the rooms list, which lands a beat after the foot does.
    const door = await foot.findByRole('button', { name: OPEN_THE_CHAT });
    expect(buttonsIn(foot)).toEqual([OPEN_THE_CHAT]);

    fireEvent.press(door);

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
    expect(screen.queryByText(RECORD_TITLE)).toBeNull();
  });

  /** A mutual whose court has no room — not yet, or not any more — says so and offers no dead door. */
  it('says You’re matched and offers no door where the court has no room', async () => {
    stubInterest(transport, interest(0, { mutual: [outgoingYes(FILIP, 'PADEL')] }));
    const foot = await openFilipsSheet();

    expect(foot.getByText(YOURE_MATCHED)).toBeTruthy();
    expect(buttonsIn(foot)).toEqual([]);
  });

  it('names the court the two share, in the Chats row’s own words, and draws no buttons', async () => {
    stubChallenges(transport, [courtWithFilip('ON')]);
    const foot = await openFilipsSheet();

    expect(foot.getByText(standingLine({ side: 'organiser', standing: 'ON' }))).toBeTruthy();
    expect(buttonsIn(foot)).toEqual([]);
  });

  it('draws the two buttons again once a shared court is behind them and off the list’s shelf', async () => {
    stubChallenges(
      transport,
      [
        courtWithFilip('LAPSED', {
          ended_at: '2026-09-01T18:00:00Z',
          ended_by: FILIP,
          seats: [
            { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'ada' },
            { side: 'B', player_id: FILIP, answer: 'LAPSED', name: 'Filip N.' },
          ],
        }),
      ],
      '2026-09-16T18:00:00Z',
    );
    const foot = await openFilipsSheet();

    expect(buttonsIn(foot)).toEqual([FILIP_LABELS.no, FILIP_LABELS.yes]);
  });

  it('a yes posts with the reading’s origin, closes the sheet, marks the card and keeps the row', async () => {
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(transport.requestsTo('POST', INTEREST)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: FILIP,
      search_id: SEARCH_ID,
    });

    // Still on the radar — the radar hides nobody for an answer — with the door replaced.
    expect(filipsCard()).toContain(ANSWERED_LINE.yes);
    expect(filipsCard()).not.toContain(TAP_FOR_THE_FULL_CARD);
    // The one-sided yes is spoken and not shown, as on the deck.
    await waitFor(() => expect(spoken()).toContain(interestAnnouncement('Filip N.')));
    expect(toasts()).toEqual([]);
    expect(screen).toHavePathname('/players');
  });

  /**
   * A yes given on the radar reaches the deck **on the server's next deal** (`already_asked`),
   * and nowhere else: it mints no deal of its own, and a deal already held is found as it was
   * when the player flips back — nothing minted, nothing hidden by this side.
   */
  it('mints no deal and touches no held deal: the deck is found as it was', async () => {
    transport.on('POST', DECK, () =>
      json(reading({ candidates: [row('Marek Z.', MAREK, 4.8, 20)], searchId: 'a-deal' })),
    );
    const foot = await openFilipsSheet();
    expect(transport.requestsTo('POST', DECK)).toHaveLength(1);

    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));
    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.deck }));

    expect(await screen.findByLabelText("Let's play, Marek Z.")).toBeTruthy();
    expect(transport.requestsTo('POST', DECK)).toHaveLength(1);
  });

  /** The chip is one number on either pane, so a deck yes on a liker reaches the held reading too. */
  it('counts the reading’s chip down on a liker’s mutual given from the deck', async () => {
    const filip = row('Filip N.', FILIP, 1.9, 47, { inclusion_reason: 'INTEREST_LIFT' });
    transport.on('POST', RADAR, () => json(reading({ candidates: [filip], wantToPlayYou: 3 })));
    transport.on('POST', DECK, () =>
      json(reading({ candidates: [filip], wantToPlayYou: 3, searchId: 'a-deal' })),
    );
    transport.on('POST', INTEREST, () => json(expressed(true), 201));
    await openRadar();
    expect(screen.getByText(wantToPlayYouChip(3))).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.deck }));
    fireEvent.press(await screen.findByLabelText("Let's play, Filip N."));
    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    fireEvent.press(screen.getByRole('button', { name: PANE_LABEL.radar }));

    expect(await screen.findByText(wantToPlayYouChip(2))).toBeTruthy();
    expect(readingBodies()).toHaveLength(1);
  });

  it('reopens on a said-yes with You said yes beside Not today, off the reply and no second read', async () => {
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));
    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    const again = within(await screen.findByTestId('radar-sheet-foot'));

    expect(again.getByText(YOU_SAID_YES)).toBeTruthy();
    expect(buttonsIn(again)).toEqual([FILIP_LABELS.no]);
    expect(transport.requestsTo('GET', INTEREST)).toHaveLength(1);
  });

  it('a pass posts with the reading’s origin, marks the card Not today, and leaves the two buttons for next time', async () => {
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.no }));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    await waitFor(() => expect(transport.requestsTo('POST', PASSES)).toHaveLength(1));
    expect(transport.requestsTo('POST', PASSES)[0]?.body).toEqual({
      sport: 'PADEL',
      player_id: FILIP,
      search_id: SEARCH_ID,
    });
    expect(filipsCard()).toContain(ANSWERED_LINE.no);
    expect(spoken()).toContain(passedAnnouncement('Filip N.'));

    // A pass is nobody's to read back, so the sheet offers both again — *Let's play* lifts it.
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    const again = within(await screen.findByTestId('radar-sheet-foot'));
    expect(buttonsIn(again)).toEqual([FILIP_LABELS.no, FILIP_LABELS.yes]);
  });

  it('a refused answer takes the mark back and says why', async () => {
    transport.on('POST', INTEREST, () => errorResponse(409, 'outstanding_interest_cap_reached'));
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    expect(
      await screen.findByText(
        playErrorMessage({ code: 'outstanding_interest_cap_reached' } as never),
      ),
    ).toBeTruthy();
    expect(filipsCard()).toContain(TAP_FOR_THE_FULL_CARD);
    expect(filipsCard()).not.toContain(ANSWERED_LINE.yes);
  });

  it('a mutual naming a challenge is the yes screen, pushed after the sheet has closed', async () => {
    transport.on('POST', INTEREST, () => json(expressed(true, CHALLENGE), 201));
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () => json(matchedWithFilip()));
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE}/yes`));
    expect(screen).toHaveSearchParams(expect.objectContaining({ which: 'mutual' }));
    expect(toasts()).toEqual([]);
  });

  it('a mutual naming no chat is the one toast, and the radar stays', async () => {
    transport.on('POST', INTEREST, () => json(expressed(true), 201));
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    await waitFor(() => expect(toasts()).toEqual([mutualToast('Filip N.')]));
    expect(screen).toHavePathname('/players');
    expect(filipsCard()).toContain(ANSWERED_LINE.yes);
  });

  it('at the cap, Let’s play on a stranger settles with the deck’s sentence and sends nothing', async () => {
    stubInterest(transport, interest(20));
    const foot = await openFilipsSheet();
    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    await waitFor(() => expect(toasts()).toEqual([CAP_REACHED_SENTENCE]));
    expect(screen.queryByText(RECORD_TITLE)).toBeNull();
    expect(transport.requestsTo('POST', INTEREST)).toHaveLength(0);
    expect(filipsCard()).toContain(TAP_FOR_THE_FULL_CARD);
  });

  /** A liker's yes closes a mutual and is never outstanding, so the cap exempts it — and the chip counts them answered. */
  it('at the cap, Let’s play on a liker flies, and the chip counts down on the mutual', async () => {
    stubInterest(transport, interest(20));
    transport.on('POST', RADAR, () =>
      json(
        reading({
          candidates: [row('Filip N.', FILIP, 1.9, 47, { inclusion_reason: 'INTEREST_LIFT' })],
          wantToPlayYou: 3,
        }),
      ),
    );
    transport.on('POST', INTEREST, () => json(expressed(true), 201));
    const foot = await openFilipsSheet();
    // Under the sheet the pane is hidden from a listener; the chip is still drawn.
    expect(screen.getByText(wantToPlayYouChip(3), HIDDEN_TOO)).toBeTruthy();

    fireEvent.press(foot.getByRole('button', { name: FILIP_LABELS.yes }));

    await waitFor(() => expect(transport.requestsTo('POST', INTEREST)).toHaveLength(1));
    expect(await screen.findByText(wantToPlayYouChip(2))).toBeTruthy();
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
    await launchIntoClassicPlay(transport);
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
    await launchIntoClassicPlay(transport);
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
    await launchIntoClassicPlay(transport);
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
  });
});

describe('the pinch and the drag', () => {
  it('never claims the press: a face and a card are doors, and the pan waits the intent distance', async () => {
    await openRadar();
    expect(panClaimsAfter()).toBe(theme.size.swipeRow.intent);
  });

  it('pinches continuously around the fingers, and the next ± snaps to the ladder', async () => {
    await openRadar();

    // Two fingers 100 pt apart spread to 200: half the width, 9 km across.
    pinch(
      [
        [145, 252],
        [245, 252],
      ],
      [
        [95, 252],
        [295, 252],
      ],
    );

    landedAt(9);
    expect(screen.getByText(widthAcross(9))).toBeTruthy();
    expect(screen.getAllByText('2,60').length).toBeGreaterThanOrEqual(3);

    zoomIn();
    landedAt(5.4);
    zoomOut();
    landedAt(10);
  });

  it('lets go where it is when one finger lifts first: the finger that stays is no pinch, and moves nothing', async () => {
    await openRadar();
    const from = [
      [145, 252],
      [245, 252],
    ] as const;
    const to = [
      [95, 252],
      [295, 252],
    ] as const;

    // Android keeps the recogniser active on the finger that stays and reports that finger as
    // the focal point — a hundred points from the midpoint it was. Read as a pinch, that would
    // put the kilometre under the old midpoint under the finger: two and a bit kilometres of
    // jump at 9 km across. It is read as the end of the pinch instead.
    pinchLiftingOneFingerFirst(from, to, 0);
    landedAt(9);

    const expected = pinched(
      { spread: 1, mid: { x: 195, y: 252 }, view: homeView(10) },
      { spread: 2, mid: { x: 195, y: 252 } },
      FIELD,
      { reachKm: 10, widestKm: widestWidthKm(10) },
    );
    const landed = useRadarView.getState().view;
    expect(landed?.widthKm).toBeCloseTo(expected.widthKm, 6);
    expect(landed?.centre.x).toBeCloseTo(expected.centre.x, 6);
    expect(landed?.centre.y).toBeCloseTo(expected.centre.y, 6);
  });

  it('starts the zoom from the spread the recogniser activates at, not from 1', async () => {
    await openRadar();
    // Android activates a slop late and reports the ratio it has reached — here 1,2 — with
    // every later scale measured from the true start. Fingers 100 apart to 200 is still half
    // the width, 9 km across; measured from 1 it would have been 7,5.
    pinch(
      [
        [145, 252],
        [245, 252],
      ],
      [
        [95, 252],
        [295, 252],
      ],
      { activatesAt: 1.2 },
    );
    landedAt(9);
  });

  it('holds the pinch between the floor and the widest stop', async () => {
    await openRadar();
    // Fingers closing from 200 to 10 apart would ask for 360 km across; the widest is 30.
    pinch(
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
    drag([200, 500], [200, 300]);

    expect(screen.getByText(offScreen(2))).toBeTruthy();
    expect(screen.getByText(playersInView(3))).toBeTruthy();
    // A drag is a drag and not a zoom.
    expect(screen.getByText(widthAcross(18))).toBeTruthy();
  });

  it('rubber-bands at the reach’s edge: a drag past it settles back to it', async () => {
    await openRadar();

    // 600 pt of drag at 18 km across is nearly 28 km — past a 10 km reach. Followed all the
    // way, the whole cast would be under the footer; settled back to the edge, the viewer sits
    // 10 km below the focus and everybody is still inside the box.
    drag([200, 100], [200, 700]);

    travelled();
    expect(screen.getByText(offScreen(0))).toBeTruthy();
    expect(screen.getByText(playersInView(CAST.length))).toBeTruthy();
  });
});

/**
 * **A stack at the floor** — players too close to tell apart, folded into one marker and
 * spread out again by a tap (ADR-0177 §2, `the-radar.md` §7.10).
 */
describe('a stack at the floor', () => {
  const OLA = 'aaaaaaaa-0000-4000-8000-000000000007';
  const OLA_TILE = tile('Ola K.', 1.95);
  /** Filip and Ola are about 60 m apart — 16 pt at the floor, under one face — and Karol is 2 km off. */
  const CROWDED = [
    row('Karol T.', KAROL, 1.2, 130),
    row('Filip N.', FILIP, 1.9, 47),
    row('Ola K.', OLA, 1.95, 48),
  ];
  const marker = () => screen.queryByRole('button', { name: stackLabel(2) });
  /** The hairlines from the marker to each fanned face — SVG lines, the only ones on the field. */
  const legs = () => screen.UNSAFE_queryAllByType(Line);

  beforeEach(() => {
    transport.on('POST', RADAR, () => json(reading({ candidates: CROWDED })));
  });

  it('folds two players a face apart into one marker at the floor, and nowhere above it', async () => {
    await openRadar();
    expect(marker()).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    // At 3 km across the two are 32 pt apart: two faces, no stack, the plain hint.
    expect(marker()).toBeNull();
    expect(screen.getByRole('button', { name: OLA_TILE })).toBeTruthy();
    expect(screen.getByText(radarHint('closest'))).toBeTruthy();

    zoomIn();
    landedAt(1.5);
    // At the floor they are one marker that says two; Filip, selected, is still his card.
    expect(marker()).toBeTruthy();
    expect(screen.getByText('2')).toBeTruthy();
    expect(screen.queryByRole('button', { name: OLA_TILE })).toBeNull();
    expect(cards()).toHaveLength(1);
    expect(screen.getByText(radarHint('closest', true))).toBeTruthy();
    // Karol, 2 km off, is a face of his own.
    expect(screen.getByRole('button', { name: KAROL_TILE })).toBeTruthy();

    // Deselected, Filip folds into the marker too.
    fireEvent.press(screen.getByTestId('radar-field-empty', HIDDEN_TOO));
    await waitFor(() => expect(cards()).toHaveLength(0));
    expect(screen.queryByRole('button', { name: FILIP_TILE })).toBeNull();
    expect(marker()).toBeTruthy();

    // Off the floor the stack dissolves and the two are faces again.
    zoomOut();
    landedAt(3);
    expect(marker()).toBeNull();
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
    expect(screen.getByRole('button', { name: OLA_TILE })).toBeTruthy();
  });

  it('opens on a tap — the members fan out and can be tapped — and folds on a second tap or on empty field', async () => {
    await openRadar();
    fireEvent.press(screen.getByRole('button', { name: FILIP_TILE }));
    landedAt(FLY_TO_WIDTH_KM);
    fireEvent.press(screen.getByTestId('radar-field-empty', HIDDEN_TOO));
    await waitFor(() => expect(cards()).toHaveLength(0));
    zoomIn();
    landedAt(1.5);
    expect(marker()!.props.accessibilityHint).toBe(stackHint(false));
    expect(marker()!.props.accessibilityState).toEqual({ expanded: false });

    expect(legs()).toHaveLength(0);

    fireEvent.press(marker()!);

    // Spread: both faces are back, each a button, a leg from the marker to each, with the
    // marker saying it is open.
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
    expect(screen.getByRole('button', { name: OLA_TILE })).toBeTruthy();
    expect(legs()).toHaveLength(2);
    expect(marker()!.props.accessibilityState).toEqual({ expanded: true });
    expect(marker()!.props.accessibilityHint).toBe(stackHint(true));

    // A fanned face flies to where it is drawn, at the floor, and is selected there: the one
    // card, with the fan still standing.
    fireEvent.press(screen.getByRole('button', { name: OLA_TILE }));
    landedAt(1.5);
    expect(cards()).toHaveLength(1);
    expect(textOf(screen.getByRole('button', { name: OLA_TILE }))).toContain(TAP_FOR_THE_FULL_CARD);
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
    expect(marker()!.props.accessibilityState).toEqual({ expanded: true });

    // A second tap folds them back: Ola, selected, stays her card; Filip is the marker's.
    fireEvent.press(marker()!);
    expect(legs()).toHaveLength(0);
    expect(screen.queryByRole('button', { name: FILIP_TILE })).toBeNull();
    expect(cards()).toHaveLength(1);
    expect(marker()!.props.accessibilityState).toEqual({ expanded: false });

    // Open again, then a tap on empty field folds it and deselects.
    fireEvent.press(marker()!);
    expect(screen.getByRole('button', { name: FILIP_TILE })).toBeTruthy();
    fireEvent.press(screen.getByTestId('radar-field-empty', HIDDEN_TOO));
    await waitFor(() => expect(cards()).toHaveLength(0));
    expect(screen.queryByRole('button', { name: FILIP_TILE })).toBeNull();
    expect(marker()!.props.accessibilityState).toEqual({ expanded: false });
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
