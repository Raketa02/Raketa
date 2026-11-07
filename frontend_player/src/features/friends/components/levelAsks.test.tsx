/**
 * **A friend's ask for a level, on Home** — walked through the real route tree
 * ([#765](https://github.com/Raketa02/Raketa/issues/765), PRD #762; the friends screens §6.4; the
 * mechanics §5.1; the words §29.5; Q129).
 *
 * - **The row**: *ASKED FOR A LEVEL · n* after FRIEND REQUESTS and before Your games, a card per
 *   sport, drawn only while Home's read holds one — its title for one asker, two, and three or more.
 * - **The coral button**: *Get your padel level* starts the padel questionnaire from Home, and the
 *   pass comes back to Home with the card gone; with a run left halfway it reads *Carry on*.
 * - **Not now**: the set-aside, the toast, and Home and the bell read again.
 * - **A player rated in nothing**: the ask card instead of *Get your level*, and *Get your level*
 *   back once the row is empty.
 *
 * **The routes are answered by a small fake of the server** (`askServer`): Not now takes the sport's
 * card off the next read of Home, and a completion rates the sport and takes its card too — so a card
 * that leaves is Home re-read, never this client guessing.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { RECORD_TITLE } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
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
  levelAskLine,
  levelAsksHeading,
  notNowLevelAskLabel,
  requestsHeading,
  setAsideToast,
  wantToPlay,
  youReOnQuestion,
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
        blocked_by_you: false,
        nickname: who.nickname,
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

/** The section headings Home draws, top to bottom. */
const headings = () =>
  screen
    .getAllByRole('header')
    .map((node) => node.props.children as string)
    .filter((text) => typeof text === 'string');

describe('ASKED FOR A LEVEL on Home', () => {
  it('draws a card for one asker, after FRIEND REQUESTS and before Your games', async () => {
    askServer([padel(TOMEK)], {
      friendRequests: [
        {
          player_id: KUBA.player_id,
          nickname: KUBA.nickname,
          photo_id: null,
          photo_url: null,
          asked_at: '2026-11-07T07:00:00Z',
          by_link: false,
          group: null,
          sport: null,
          level: null,
          player_score: 96,
          reliability_band: 'VERY_HIGH',
        },
      ],
    });
    await launchSignedIn();

    expect(await screen.findByRole('header', { name: levelAsksHeading(1) })).toBeTruthy();
    const one = card('padel');
    expect(one.getByText(wantToPlay(['tomek.k'], 'padel'))).toBeTruthy();
    expect(one.getByText('tomek.k wants to play padel with you')).toBeTruthy();
    expect(one.getByText('A few questions, and tomek.k can add you to a game.')).toBeTruthy();
    expect(screen.getByRole('button', { name: notNowLevelAskLabel('padel') })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Get your padel level' })).toBeTruthy();
    // No group is named, and only Tomek's face is drawn.
    expect(screen.queryByText(new RegExp(CREW.name))).toBeNull();
    expect(one.getAllByRole('button', { name: /^(tomek|kuba|ania|ewa)/ })).toHaveLength(1);

    const order = headings().filter((text) =>
      /^(Friend requests|Asked for a level|Your games)/.test(text),
    );
    expect(order[0]).toBe(requestsHeading(1));
    expect(order[1]).toBe(levelAsksHeading(1));
    expect(order[2]).toMatch(/^Your games/);
  });

  it('names two askers together and says they, with both faces', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();

    expect(await screen.findByText('tomek.k and kuba.w want to play padel with you')).toBeTruthy();
    const two = card('padel');
    expect(two.getByText('A few questions, and they can add you to a game.')).toBeTruthy();
    expect(two.getByRole('button', { name: TOMEK.nickname })).toBeTruthy();
    expect(two.getByRole('button', { name: KUBA.nickname })).toBeTruthy();
  });

  it('names the two newest of three or more, counts the rest, and draws three faces', async () => {
    askServer([padel(TOMEK, KUBA, ANIA, EWA)]);
    await launchSignedIn();

    expect(
      await screen.findByText('tomek.k, kuba.w and 2 more want to play padel with you'),
    ).toBeTruthy();
    const more = card('padel');
    expect(more.getByText(levelAskLine(['tomek.k', 'kuba.w', 'ania.m']))).toBeTruthy();
    expect(more.getByRole('button', { name: ANIA.nickname })).toBeTruthy();
    expect(more.queryByRole('button', { name: EWA.nickname })).toBeNull();
  });

  it('counts a card per sport in its title', async () => {
    askServer([padel(TOMEK), { sport: 'SQUASH', askers: [KUBA] }]);
    await launchSignedIn();

    expect(await screen.findByRole('header', { name: levelAsksHeading(2) })).toBeTruthy();
    expect(card('squash').getByText('kuba.w wants to play squash with you')).toBeTruthy();
    expect(screen.getByRole('button', { name: getYourLevelLabel('squash') })).toBeTruthy();
  });

  it('is not there while no friend’s ask waits', async () => {
    askServer([]);
    await launchSignedIn();

    await waitFor(() => expect(homeReads()).toBeGreaterThan(0));
    expect(await screen.findByRole('header', { name: /^Your games/ })).toBeTruthy();
    expect(screen.queryByTestId('level-asks')).toBeNull();
    expect(screen.queryByText(/^Asked for a level/)).toBeNull();
  });

  it('opens that friend’s record from a face', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: KUBA.nickname }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() => expect(transport.requestsTo('GET', recordPath(KUBA))).toHaveLength(1));
  });
});

describe('the coral button', () => {
  it(
    'starts the padel questionnaire from Home, and the card is gone on the way back',
    async () => {
      const server = askServer([padel(TOMEK)]);
      // The questionnaire is a sibling of the app, so Home's read is unobserved while it is up, and
      // the harness runs every pending timer on a navigation — its collection among them. Held, as a
      // walk shorter than its five minutes holds it on a phone: the card Home drew is still cached.
      queryClient.setQueryDefaults(proposalKeys.home(), { gcTime: Infinity });
      await launchSignedIn();
      await waitFor(() => expect(bellReads()).toBeGreaterThan(0));

      fireEvent.press(await screen.findByRole('button', { name: 'Get your padel level' }));

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
      // Home's read on the way back is held: only what the app itself drops can take the card.
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
      // Gone from the first frame back, though Home has not answered yet — dropped as the pass ended.
      expect(screen.queryByTestId('level-asks')).toBeNull();
      expect(screen.queryByText('tomek.k wants to play padel with you')).toBeNull();
      // And Home and the bell are read again, and the read agrees.
      await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
      await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
      await act(async () => answerHome());
      expect(screen.queryByTestId('level-asks')).toBeNull();
    },
    WALK_TIMEOUT,
  );

  it('reads Carry on, on the question she is on, with a padel questionnaire left halfway', async () => {
    askServer([padel(TOMEK)], { leftHalfway: true });
    await launchSignedIn();

    expect(await screen.findByText(youReOnQuestion(5))).toBeTruthy();
    const halfway = card('padel');
    // The title doesn't change; the line and the button do.
    expect(halfway.getByText('tomek.k wants to play padel with you')).toBeTruthy();
    expect(halfway.queryByText(levelAskLine(['tomek.k']))).toBeNull();
    expect(screen.queryByRole('button', { name: 'Get your padel level' })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.levelAsks.carryOn }));

    // The start hands the run back, where it stands.
    await waitFor(() => expect(screen).toHavePathname(`/question/${PADEL_RUN}`));
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(1);
  });

  it('says the notice’s own sentence when she has the level already, and re-reads Home', async () => {
    askServer([padel(TOMEK)]);
    transport.on('POST', ASSESSMENTS_PATH, () => errorResponse(409, 'sport_already_rated'));
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const homeBefore = homeReads();
    const bellBefore = bellReads();

    fireEvent.press(await screen.findByRole('button', { name: 'Get your padel level' }));

    await waitFor(() =>
      expect(toasts()).toEqual([['You have a padel level already.', 'base', 'read']]),
    );
    expect(screen).toHavePathname('/');
    await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
  });
});

describe('Not now', () => {
  it('sets the sport’s asks aside, says where the level still is, and re-reads Home and the bell', async () => {
    askServer([padel(TOMEK, KUBA)]);
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const bellBefore = bellReads();

    fireEvent.press(await screen.findByRole('button', { name: notNowLevelAskLabel('padel') }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', setAsidePath('PADEL'))).toHaveLength(1),
    );
    await waitFor(() => expect(toasts()).toEqual([[setAsideToast('padel'), 'base', 'read']]));
    expect(toasts()[0]?.[0]).toBe(
      'You can get your padel level any time, from You › Skill passport.',
    );
    await waitFor(() => expect(screen.queryByTestId('level-asks')).toBeNull());
    expect(screen.queryByText(/^Asked for a level/)).toBeNull();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
    // Nothing was started.
    expect(transport.requestsTo('POST', ASSESSMENTS_PATH)).toHaveLength(0);
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

    fireEvent.press(await screen.findByRole('button', { name: notNowLevelAskLabel('padel') }));

    await waitFor(() => expect(homeReads()).toBeGreaterThan(homeBefore));
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
    // The state moved: no toast, and nothing said on the card.
    expect(toasts()).toEqual([]);
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('a player rated in nothing', () => {
  it('sees the ask card in place of Get your level, and Get your level again once the row is empty', async () => {
    askServer([padel(TOMEK)], { ratings: [] });
    await launchSignedIn();

    expect(await screen.findByText('tomek.k wants to play padel with you')).toBeTruthy();
    // Every read Get your level is drawn from has answered, and it is not drawn.
    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/groups')).not.toEqual([]));
    await act(async () => jest.advanceTimersByTime(1));
    expect(screen.queryByText(HOME_CARD)).toBeNull();
    expect(screen.queryByText(HOME_CARD_LINE)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: notNowLevelAskLabel('padel') }));

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(screen.queryByTestId('level-asks')).toBeNull();
  });

  it('sees Get your level when Home’s read is refused — nothing is known to stand in its place', async () => {
    askServer([], { ratings: [] });
    transport.on('GET', HOME_PATH, () => errorResponse(404, 'not_found'));
    await launchSignedIn();

    expect(await screen.findByText(HOME_CARD)).toBeTruthy();
    expect(screen.getByText(HOME_CARD_LINE)).toBeTruthy();
    expect(screen.queryByTestId('level-asks')).toBeNull();
  });
});
