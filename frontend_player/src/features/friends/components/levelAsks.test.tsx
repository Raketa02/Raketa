/**
 * **A friend's ask for a level, in Needs your answer** — walked through the real route tree
 * ([#816](https://github.com/Raketa02/Raketa/issues/816), ADR-0205 §1, §4; #765, PRD #762; the
 * friends screens §6.4; the mechanics §5.1; the words §29.5).
 *
 * - **The section**: *ASKED FOR A LEVEL · n* behind the header's envelope, after FRIEND REQUESTS and
 *   never on Home, a tile per sport, drawn only while Home's read holds one — its title for one
 *   asker, two, and three or more, and **no line under it**.
 * - **The coral button**: *Get your padel level* closes the sheet for good and starts the padel
 *   questionnaire from Home, and the pass comes back to Home with the ask gone; with a run left
 *   halfway it reads *Carry on*.
 * - **Not now**: the set-aside, the toast, Home and the bell read again, and the sheet closing on
 *   the last.
 * - **Get your level on Home**: for a player in a group and rated in nothing, whether or not a
 *   friend asked — the ask no longer stands in its place.
 *
 * **The routes are answered by a small fake of the server** (`askServer`): Not now takes the sport's
 * tile off the next read of Home, and a completion rates the sport and takes its tile too — so a tile
 * that leaves is Home re-read, never this client guessing.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Dimensions, StyleSheet } from 'react-native';

import { RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import { envelope, openNeedsYourAnswer, sheetTitle } from '@/test-support/needsYourAnswer';
import {
  HOME_PATH,
  NOTICES_PATH,
  SPORTS_SERVED,
  launchSignedIn,
  ratingGuideAlreadyShown,
  stubGate,
  stubMyGroups,
  stubNotices,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  FRIENDS_COPY,
  getYourLevelLabel,
  levelAsksHeading,
  notNowLevelAskLabel,
  requestsHeading,
  setAsideToast,
  wantToPlay,
} from './friendsCopy';

/** A walk — Home, the questionnaire and back — is longer than jest's five seconds. */
const WALK_TIMEOUT = 30_000;

type Asker = Wire['HomeLevelAskerSchema'];

const asker = (n: number, nickname: string): Asker => ({
  player_id: `e0000000-0000-4000-8000-0000000007${String(n).padStart(2, '0')}`,
  nickname,
  photo_id: null,
  photo_url: null,
});

const TOMEK = asker(1, 'tomek.k');
const KUBA = asker(2, 'kuba.w');
const ANIA = asker(3, 'ania.m');
const EWA = asker(4, 'ewa.s');

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000765',
  kind: 'PLAYER',
  name: 'Czwartkowy padel',
  monogram: { letters: 'Cp', colour: 2 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000765', name: 'Centrum Ruchu' },
};

const ASSESSMENTS_PATH = '/api/v1/assessments';
const stepPath = (id: string) => `${ASSESSMENTS_PATH}/${id}`;
const setAsidePath = (sport: Wire['Sport']) => `/api/v1/friends/level-asks/${sport}/set-aside`;
const recordPath = (who: Asker) => `/api/v1/players/${who.player_id}/record`;

const PADEL_RUN = '4d5e6f70-8192-4a3b-8c4d-5e6f70819765';
const HOME_CARD = 'Get your level';
const HOME_CARD_LINE = "Your groups can't deal you games until you have one.";

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.7,
    confidence: 24,
    range: { low: mu - 0.7, high: mu + 0.7 },
    band: { name: 'Developing', lower: 1.6, upper: 2.6 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-11-07T09:00:00Z',
  };
}

const QUESTION: Wire['QuestionResponse'] = {
  id: 'q-played-padel',
  category: 'Recent activity',
  tier: null,
  situation: 'Before anything else',
  text: 'Have you played padel before?',
  qualifier: 'Any level counts',
  options: [
    { id: 'never', text: 'Never played' },
    { id: 'regular', text: 'I play most weeks' },
  ],
};

/** The padel run at its outstanding question, `answered` already behind it. */
function asking(answered: number): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: PADEL_RUN,
    status: 'in_progress',
    questions_asked: answered,
    transcript: Array.from({ length: answered }, (_, at) => ({
      question: { ...QUESTION, id: `q-earlier-${at}` },
      option_id: 'regular',
    })),
    question: QUESTION,
  };
}

/** One more answer in, and the engine has stopped: the review is next. */
function stopped(answered: number): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: PADEL_RUN,
    status: 'in_progress',
    questions_asked: answered,
    transcript: Array.from({ length: answered }, () => ({
      question: QUESTION,
      option_id: 'regular',
    })),
    question: null,
    result: null,
  };
}

function rated(answered: number): Wire['AssessmentStepResponse'] {
  return {
    ...stopped(answered),
    status: 'completed',
    result: {
      mu: 1.9,
      sigma: 0.7,
      confidence: 24,
      confidence_ceiling: 30,
      range: { low: 1.2, high: 2.6 },
      band: { name: 'Developing', lower: 1.6, upper: 2.6 },
      status: 'initial_estimate',
      questions_asked: answered,
      engine_version: 'racketskill-v3',
      calibration_priority: 'standard',
    },
  };
}

let transport: Transport;

interface AskServer {
  /** What `GET /home` answers now. */
  readonly home: () => Response;
}

/**
 * **Home's asks and the questionnaire, faked** — the rules the routes document: Not now takes the
 * sport's card off Home, a start opens the sport's run (or hands back the one left halfway), and a
 * completion rates the sport and takes its card. `ratings` is what she holds already.
 */
function askServer(
  initially: readonly Wire['HomeLevelAskSchema'][],
  {
    ratings = [rating('TENNIS', 3.1)],
    leftHalfway = false,
    friendRequests = [],
  }: {
    readonly ratings?: readonly Wire['RatingResponse'][];
    readonly leftHalfway?: boolean;
    readonly friendRequests?: readonly Wire['HomeFriendRequestSchema'][];
  } = {},
): AskServer {
  let asks = [...initially];
  let held = [...ratings];
  const answered = leftHalfway ? 4 : 0;

  stubGate(transport, { ratings: held, hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  transport.on('GET', '/api/v1/ratings', () => json<Wire['RatingsResponse']>({ ratings: held }));
  stubMyGroups(transport, [CREW]);
  stubNotices(transport, []);
  stubRunsInProgress(transport, leftHalfway ? [{ assessment_id: PADEL_RUN, sport: 'PADEL' }] : []);

  const home = () =>
    json<Wire['HomeResponse']>({
      read_at: '2026-11-07T08:00:00Z',
      payments_to_confirm: [],
      needs_your_answer: { new_count: 0, watermark: null },
      needing_you: 0,
      games: [],
      friend_requests: [...friendRequests],
      friends_games: [],
      level_asks: asks,
    });
  transport.on('GET', HOME_PATH, home);
  for (const sport of ['PADEL', 'SQUASH'] as const) {
    transport.on('POST', setAsidePath(sport), () => {
      asks = asks.filter((ask) => ask.sport !== sport);
      return noContent();
    });
  }

  transport.on('POST', ASSESSMENTS_PATH, () => {
    stubRunsInProgress(transport, [{ assessment_id: PADEL_RUN, sport: 'PADEL' }]);
    return json(asking(answered), leftHalfway ? 200 : 201);
  });
  transport.on('GET', stepPath(PADEL_RUN), () => json(asking(answered)));
  transport.on('POST', `${stepPath(PADEL_RUN)}/answers`, () => json(stopped(answered + 1)));
  transport.on('POST', `${stepPath(PADEL_RUN)}/completion`, () => {
    stubRunsInProgress(transport, []);
    held = [...held, rating('PADEL', 1.9)];
    asks = asks.filter((ask) => ask.sport !== 'PADEL');
    return json(rated(answered + 1));
  });

  for (const who of [TOMEK, KUBA, ANIA, EWA]) {
    transport.on('GET', recordPath(who), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'FRIEND',
        can_add_friend: true,
        nickname: who.nickname,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [],
        reliability: servedReliability({ player_score: 96, is_new: false }),
      }),
    );
  }

  return { home };
}

const padel = (...askers: Asker[]): Wire['HomeLevelAskSchema'] => ({ sport: 'PADEL', askers });

beforeEach(async () => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
  await ratingGuideAlreadyShown();
});

afterEach(async () => {
  transport.restore();
  queryClient.setQueryDefaults(proposalKeys.home(), {});
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

const card = (sport: string) => within(screen.getByTestId(`level-ask-${sport}`));
const homeReads = () => transport.requestsTo('GET', HOME_PATH).length;
const bellReads = () => transport.requestsTo('GET', NOTICES_PATH).length;
const toasts = () =>
  useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone, toast.hold]);

/** The section headings the sheet draws under its title, top to bottom. */
const sections = () =>
  within(screen.getByTestId('bottom-sheet'))
    .getAllByRole('header')
    .map((node) => node.props.children as unknown)
    .filter((text): text is string => typeof text === 'string');

/** The width the rail hands a sport's tile — read off the tile, which holds its `top`. */
function tileWidth(sport: string): unknown {
  let node = screen.getByTestId(`level-ask-${sport}`).parent;
  while (node !== null && StyleSheet.flatten(node.props.style)?.width === undefined) {
    node = node.parent;
  }
  return node === null ? undefined : StyleSheet.flatten(node.props.style)?.width;
}

const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;

/** The line under the title that #816 took away, in each of its forms. */
const SUBTITLE = /A few questions|You're on question/;

const KUBAS_REQUEST: Wire['HomeFriendRequestSchema'] = {
  player_id: KUBA.player_id,
  nickname: KUBA.nickname,
  photo_id: null,
  photo_url: null,
  asked_at: '2026-11-07T07:00:00Z',
  by_link: false,
  from_ranking: false,
  from_new_players: false,
  from_same_level: false,
  from_same_vibe: false,
  group: null,
  sport: null,
  level: null,
  player_score: 96,
  reliability_band: 'VERY_HIGH',
  percent_even: null,
  in_common: null,
  levels: [],
};

describe('ASKED FOR A LEVEL in Needs your answer', () => {
  it('waits behind the envelope, after FRIEND REQUESTS, and is no longer on Home', async () => {
    askServer([padel(TOMEK)], { friendRequests: [KUBAS_REQUEST] });
    await launchSignedIn();

    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(screen.queryByTestId('level-asks')).toBeNull();
    expect(screen.queryByText('tomek.k wants to play padel with you')).toBeNull();

    await openNeedsYourAnswer();

    expect(sections()).toEqual([requestsHeading(1), levelAsksHeading(1)]);
  });

  it('draws a tile for one asker — the face and the title in two lines at most, and nothing under it', async () => {
    askServer([padel(TOMEK)]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    const one = card('padel');
    const title = one.getByText(wantToPlay(['tomek.k'], 'padel'));
    expect(title.props.children).toBe('tomek.k wants to play padel with you');
    expect(title.props.numberOfLines).toBe(2);
    expect(screen.queryByText(SUBTITLE)).toBeNull();
    expect(screen.getByRole('button', { name: notNowLevelAskLabel('padel') })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Get your padel level' })).toBeTruthy();
    // No group is named, and only Tomek's face is drawn.
    expect(screen.queryByText(new RegExp(CREW.name))).toBeNull();
    expect(one.getAllByRole('button', { name: /^(tomek|kuba|ania|ewa)/ })).toHaveLength(1);
    // Alone, it takes the content width.
    expect(tileWidth('padel')).toBe(content());
  });

  it('names two askers together, with both faces', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(screen.getByText('tomek.k and kuba.w want to play padel with you')).toBeTruthy();
    const two = card('padel');
    expect(two.getByRole('button', { name: TOMEK.nickname })).toBeTruthy();
    expect(two.getByRole('button', { name: KUBA.nickname })).toBeTruthy();
    expect(screen.queryByText(SUBTITLE)).toBeNull();
  });

  it('names the two newest of three or more, counts the rest, and draws three faces', async () => {
    askServer([padel(TOMEK, KUBA, ANIA, EWA)]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(screen.getByText('tomek.k, kuba.w and 2 more want to play padel with you')).toBeTruthy();
    const more = card('padel');
    expect(more.getByRole('button', { name: ANIA.nickname })).toBeTruthy();
    expect(more.queryByRole('button', { name: EWA.nickname })).toBeNull();
  });

  it('counts a tile per sport, each on the wider rail', async () => {
    askServer([padel(TOMEK), { sport: 'SQUASH', askers: [KUBA] }]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: levelAsksHeading(2) })).toBeTruthy();
    expect(card('squash').getByText('kuba.w wants to play squash with you')).toBeTruthy();
    expect(screen.getByRole('button', { name: getYourLevelLabel('squash') })).toBeTruthy();
    expect(tileWidth('padel')).toBeCloseTo(content() * theme.size.requestCardRatio);
    expect(tileWidth('squash')).toBeCloseTo(content() * theme.size.requestCardRatio);
  });

  it('is not there while no friend’s ask waits — no envelope, no section', async () => {
    askServer([]);
    await launchSignedIn();

    await waitFor(() => expect(homeReads()).toBeGreaterThan(0));
    expect(await screen.findByRole('header', { name: /^Your games/ })).toBeTruthy();
    expect(envelope()).toBeNull();
    expect(screen.queryByTestId('level-asks')).toBeNull();
  });

  it('opens that friend’s record over the sheet from a face, and the sheet is there when it closes', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: KUBA.nickname }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() => expect(transport.requestsTo('GET', recordPath(KUBA))).toHaveLength(1));

    fireEvent.press(screen.getByRole('button', { name: recordCloseLabel(false) }));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId('level-ask-padel')).toBeTruthy();
  });
});

describe('the coral button', () => {
  it(
    'closes the sheet for good, starts the padel questionnaire, and the ask is gone on the way back',
    async () => {
      const server = askServer([padel(TOMEK)]);
      // The questionnaire is a sibling of the app, so Home's read is unobserved while it is up, and
      // the harness runs every pending timer on a navigation — its collection among them. Held, as a
      // walk shorter than its five minutes holds it on a phone: the tile Home drew is still cached.
      queryClient.setQueryDefaults(proposalKeys.home(), { gcTime: Infinity });
      await launchSignedIn();
      await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
      await openNeedsYourAnswer();

      fireEvent.press(screen.getByRole('button', { name: 'Get your padel level' }));

      // The sheet goes before anything navigates: a screen cannot stand behind a sheet.
      await waitFor(() => expect(sheetTitle()).toBeNull());
      await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN}`));
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH).map((one) => one.body)).toEqual([
        { sport: 'PADEL' },
      ]);
      expect(await screen.findByText(QUESTION.text)).toBeTruthy();
      fireEvent.press(screen.getByLabelText('I play most weeks'));
      fireEvent.press(screen.getByLabelText('Confirm answer'));
      await waitFor(() => expect(screen).toHavePathname(`/review/${PADEL_RUN}`));
      fireEvent.press(await screen.findByLabelText('Get my Padel level'));
      await waitFor(() => expect(screen).toHavePathname(`/result/${PADEL_RUN}`), {
        timeout: 4000,
      });
      const bellBefore = bellReads();
      const homeBefore = homeReads();
      // Home's read on the way back is held: only what the app itself drops can take the ask.
      let answerHome: () => void = () => undefined;
      const served = server.home();
      transport.on(
        'GET',
        HOME_PATH,
        () => new Promise<Response>((resolve) => (answerHome = () => resolve(served))),
      );

      // The pass began on Home, so it ends there.
      fireEvent.press(await screen.findByLabelText('Back to Home'));

      await waitFor(() => expect(screen).toHavePathname('/'));
      expect(await screen.findByRole('header', { name: /^Your games/ })).toBeTruthy();
      // Gone from the first frame back, though Home has not answered yet — dropped as the pass
      // ended: nothing waits, so no envelope, and no sheet reopens by itself.
      expect(envelope()).toBeNull();
      expect(sheetTitle()).toBeNull();
      // And Home and the bell are read again, and the read agrees.
      await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
      await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
      await act(async () => answerHome());
      expect(envelope()).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it('reads Carry on with a padel questionnaire left halfway, and says no question under the title', async () => {
    askServer([padel(TOMEK)], { leftHalfway: true });
    await launchSignedIn();
    await openNeedsYourAnswer();

    const carryOn = await screen.findByRole('button', { name: FRIENDS_COPY.levelAsks.carryOn });
    // The title doesn't change, and nothing runs under it — not the question she is on either.
    expect(card('padel').getByText('tomek.k wants to play padel with you')).toBeTruthy();
    expect(screen.queryByText(SUBTITLE)).toBeNull();
    expect(screen.queryByRole('button', { name: 'Get your padel level' })).toBeNull();

    fireEvent.press(carryOn);

    // The sheet goes, and the start hands the run back, where it stands.
    await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN}`));
    expect(sheetTitle()).toBeNull();
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
  });

  it('says the notice’s own sentence over Home when she has the level already, and re-reads Home', async () => {
    askServer([padel(TOMEK)]);
    transport.on('POST', ASSESSMENTS_PATH, () => errorResponse(409, 'sport_already_rated'));
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const homeBefore = homeReads();
    const bellBefore = bellReads();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: 'Get your padel level' }));

    await waitFor(() =>
      expect(toasts()).toEqual([['You have a padel level already.', 'base', 'read']]),
    );
    expect(screen).toHavePathname('/');
    expect(sheetTitle()).toBeNull();
    await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
  });
});

describe('Not now', () => {
  it('sets the sport’s asks aside, says where the level still is, re-reads Home and the bell, and the sheet closes on the last', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const bellBefore = bellReads();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: notNowLevelAskLabel('padel') }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', setAsidePath('PADEL'))).toHaveLength(1),
    );
    await waitFor(() => expect(toasts()).toEqual([[setAsideToast('padel'), 'base', 'read']]));
    expect(toasts()[0]?.[0]).toBe(
      'You can get your padel level any time, from You › Skill passport.',
    );
    await waitFor(() => expect(screen.queryByTestId('level-asks')).toBeNull());
    expect(sheetTitle()).toBeNull();
    expect(envelope()).toBeNull();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
    // Nothing was started.
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(0);
  });

  it('takes one sport’s tile and leaves the other, the sheet still up', async () => {
    askServer([padel(TOMEK), { sport: 'SQUASH', askers: [KUBA] }]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: notNowLevelAskLabel('padel') }));

    expect(await screen.findByRole('header', { name: levelAsksHeading(1) })).toBeTruthy();
    expect(screen.queryByTestId('level-ask-padel')).toBeNull();
    expect(screen.getByTestId('level-ask-squash')).toBeTruthy();
    expect(sheetTitle()).not.toBeNull();
  });
});

describe('Not now that lost a race', () => {
  it('says nothing, and reads Home and the bell again', async () => {
    askServer([padel(TOMEK)]);
    transport.on('POST', setAsidePath('PADEL'), () =>
      errorResponse(409, 'concurrent_modification'),
    );
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const homeBefore = homeReads();
    const bellBefore = bellReads();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: notNowLevelAskLabel('padel') }));

    await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
    // The state moved: no toast, and nothing said on the tile.
    expect(toasts()).toEqual([]);
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('Get your level on Home', () => {
  /** Where on Home a text stands, top to bottom — the card's title, or Your games' heading. */
  const homeOrder = () =>
    screen
      .getAllByText(/^(Get your level|Your games)/)
      .map((node) => (String(node.props.children).startsWith(HOME_CARD) ? 'card' : 'games'));

  it('shows above Your games for a player in a group rated in nothing, though a friend asked', async () => {
    askServer([padel(TOMEK)], { ratings: [] });
    await launchSignedIn();

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(homeOrder()).toEqual(['card', 'games']);
    // The ask waits behind the envelope, never in the card's place.
    expect(envelope()).not.toBeNull();
    expect(screen.queryByTestId('level-asks')).toBeNull();
  });

  it('shows for a player in a group rated in nothing whom nobody asked', async () => {
    askServer([], { ratings: [] });
    await launchSignedIn();

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(envelope()).toBeNull();
  });

  it('shows when Home’s read is refused', async () => {
    askServer([], { ratings: [] });
    transport.on('GET', HOME_PATH, () => errorResponse(404, 'not_found'));
    await launchSignedIn();

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(envelope()).toBeNull();
  });
});
