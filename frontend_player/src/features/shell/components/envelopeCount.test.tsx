/**
 * **The envelope's count** ([#819](https://github.com/Raketa02/Raketa/issues/819); ADR-0205 §2, §3;
 * home refactor 1) — walked through the real route tree, with only `fetch` faked: the bell's count
 * mark on the header's envelope, *Needs your answer, 2 new*, and the visit that clears it when the
 * sheet goes for good.
 *
 * **The server is faked by the rules #815's routes document** (`envelopeServer`): each friend
 * request arrives when it was asked; Home counts what arrived past the last visit's watermark and
 * serves the newest arrival as its own; a visit records its watermark only when it is later than
 * the last, and answers `204` either way. So the assertions are on **what went over the wire** —
 * which watermark each close named — and on what the next read says because of it.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { notNowLabel } from '@/features/friends/types';
import { RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { CountBadge, theme } from '@/shared/ui';
import {
  closeNeedsYourAnswer,
  envelope,
  openNeedsYourAnswer,
  sheetTitle,
} from '@/test-support/needsYourAnswer';
import {
  DEVICES_PATH,
  HOME_PATH,
  NEEDS_YOUR_ANSWER_VISIT_PATH,
  launchSignedIn,
  resetPush,
  stubGate,
  stubHome,
  stubNotices,
  stubPaymentsToConfirm,
  stubPush,
} from '@/test-support/onboardingRouter';
import { fakePush, type FakePush } from '@/test-support/platform';
import { servedReliability } from '@/test-support/playerRecord';
import { pullDown } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { NEEDS_YOUR_ANSWER_COPY } from './shellCopy';

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

/** A friend request waiting on the reader, which arrived when it was asked. */
function request(
  nickname: string,
  playerId: string,
  askedAt: string,
): Wire['HomeFriendRequestSchema'] {
  return {
    player_id: playerId,
    nickname,
    photo_id: null,
    photo_url: null,
    asked_at: askedAt,
    by_link: false,
    from_ranking: false,
    from_new_players: false,
    from_same_level: false,
    from_same_vibe: false,
    group: null,
    sport: 'PADEL',
    level: 3.4,
    player_score: 98,
    reliability_band: 'VERY_HIGH',
    percent_even: null,
    in_common: null,
    levels: [],
  };
}

// Kept to the millisecond as the server serves them, so the phone must hand back exactly these.
const INES = request('ines.d', 'e0000000-0000-4000-8000-000000000819', '2026-10-01T07:00:00.120Z');
const OLA = request('ola.m', 'e0000000-0000-4000-8000-000000000820', '2026-10-01T07:40:00.450Z');
const PIOTR = request('piotr.s', 'e0000000-0000-4000-8000-000000000821', '2026-10-01T07:50:00Z');

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubNotices(transport, []);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  resetPush();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

/**
 * **#815's routes, faked by their rules** — the friend requests waiting, each new once it arrived
 * past the last visit's watermark, Home's own watermark the newest arrival, *Not now* taking a
 * request off, and a visit recorded only when later than the last. `arrives` is a request reaching
 * the server, which the phone hears of only on its next read of Home.
 */
function envelopeServer(initially: readonly Wire['HomeFriendRequestSchema'][]) {
  let waiting = [...initially];
  let seenThrough: string | null = null;
  // A visit held on the wire until the suite lets it land, so what happens before it is seen.
  let held: Promise<void> | undefined;
  const later = (one: string, than: string | null) => than === null || one > than;

  const serve = () =>
    stubHome(transport, {
      friend_requests: [...waiting],
      needs_your_answer: {
        new_count: waiting.filter((one) => later(one.asked_at, seenThrough)).length,
        watermark: waiting.reduce<string | null>(
          (newest, one) => (later(one.asked_at, newest) ? one.asked_at : newest),
          null,
        ),
      },
    });
  serve();

  transport.on('POST', NEEDS_YOUR_ANSWER_VISIT_PATH, async (sent) => {
    await held;
    const { watermark } = sent.body as Wire['NeedsYourAnswerVisitRequest'];
    if (watermark !== null && later(watermark, seenThrough)) seenThrough = watermark;
    serve();
    return noContent();
  });
  for (const one of initially) {
    transport.on('POST', `/api/v1/friends/requests/${one.player_id}/set-aside`, () => {
      waiting = waiting.filter((left) => left.player_id !== one.player_id);
      serve();
      return noContent();
    });
  }

  return {
    arrives(one: Wire['HomeFriendRequestSchema']) {
      waiting = [one, ...waiting];
      serve();
    },
    /** Hold every visit until the answer is called. */
    holdVisits(): () => void {
      let land: () => void = () => undefined;
      held = new Promise((resolve) => {
        land = resolve;
      });
      return land;
    },
  };
}

/** Every visit the phone sent, by what it named. */
const visits = () =>
  transport.requestsTo('POST', NEEDS_YOUR_ANSWER_VISIT_PATH).map((one) => one.body);

const homeReads = () => transport.requestsTo('GET', HOME_PATH).length;

/** Home, read again — what a push, a return to the app or a write does. */
const rereadHome = () =>
  act(() => queryClient.invalidateQueries({ queryKey: proposalKeys.home() }));

/** The envelope once Home has drawn it. */
async function theEnvelope() {
  return waitFor(() => {
    const found = envelope();
    expect(found).not.toBeNull();
    return found!;
  });
}

/** What the envelope's badge writes, or `undefined` while it draws none. */
function badgeOn(mark: NonNullable<ReturnType<typeof envelope>>) {
  const badges = within(mark).UNSAFE_queryAllByType(CountBadge);
  return badges.length === 0 ? undefined : badges[0]!.props;
}

describe('the envelope’s badge (#819)', () => {
  it('is the bell’s count mark — news, in ink — with the served count, said on the envelope’s name', async () => {
    envelopeServer([OLA, INES]);
    await launchSignedIn();

    const mark = await theEnvelope();
    await waitFor(() => expect(mark.props.accessibilityLabel).toBe('Needs your answer, 2 new'));
    expect(badgeOn(mark)).toEqual({ figure: '2', tone: 'news' });
    // Drawn, and hidden from a listener: the envelope's name already says it.
    expect(within(mark).getByText('2', { includeHiddenElements: true })).toBeTruthy();
    expect(within(mark).queryByText('2')).toBeNull();
  });

  it('writes 99+ above 99, and says the exact count', async () => {
    stubHome(transport, {
      friend_requests: [INES],
      needs_your_answer: { new_count: 140, watermark: INES.asked_at },
    });
    await launchSignedIn();

    const mark = await theEnvelope();
    await waitFor(() => expect(mark.props.accessibilityLabel).toBe('Needs your answer, 140 new'));
    expect(badgeOn(mark)).toEqual({ figure: '99+', tone: 'news' });
  });

  it('draws nothing at nought, and the envelope stays while anything waits', async () => {
    stubHome(transport, {
      friend_requests: [INES],
      needs_your_answer: { new_count: 0, watermark: INES.asked_at },
    });
    await launchSignedIn();

    const mark = await theEnvelope();
    expect(mark.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title);
    expect(badgeOn(mark)).toBeUndefined();
  });
});

describe('closing Needs your answer records the visit (#819)', () => {
  it('names the watermark of the read it showed on ✕ — the badge goes at once, and Home is read after it', async () => {
    const server = envelopeServer([OLA, INES]);
    const land = server.holdVisits();
    await launchSignedIn();
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe('Needs your answer, 2 new'),
    );
    await openNeedsYourAnswer();

    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
    const before = homeReads();
    // At once: the badge is gone, and the envelope stays, while the visit is still on its way.
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title),
    );
    expect(badgeOn(envelope()!)).toBeUndefined();
    expect(sheetTitle()).toBeNull();
    expect(homeReads()).toBe(before);

    await act(async () => {
      land();
      await Promise.resolve();
    });

    await waitFor(() => expect(homeReads()).toBeGreaterThan(before));
    // And the server, told, counts nothing new on it.
    expect(envelope()?.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title);
  });

  it.each<[string, () => void]>([
    ['✕', closeNeedsYourAnswer],
    [
      'the backdrop',
      () =>
        fireEvent.press(screen.getByTestId('bottom-sheet-scrim', { includeHiddenElements: true })),
    ],
    [
      'a pull down its head',
      () => expect(pullDown(sheetTitle()!, theme.size.sheetSwipe.close)).toBe(true),
    ],
  ])('is sent on %s, naming the read the sheet showed', async (_, close) => {
    envelopeServer([OLA, INES]);
    await launchSignedIn();
    await openNeedsYourAnswer();
    expect(visits()).toEqual([]);

    act(close);

    await waitFor(() => expect(sheetTitle()).toBeNull());
    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
    expect(envelope()).not.toBeNull();
  });

  it('is sent on the self-close after the last answer, naming the read that held it', async () => {
    envelopeServer([INES]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: notNowLabel(INES.nickname) }));

    await waitFor(() => expect(sheetTitle()).toBeNull());
    // The read after *Not now* holds nothing, and so no watermark: the visit names the one shown.
    await waitFor(() => expect(visits()).toEqual([{ watermark: INES.asked_at }]));
    expect(envelope()).toBeNull();
  });

  it('is not sent for stepping aside under a record — only when the sheet goes', async () => {
    envelopeServer([OLA, INES]);
    transport.on('GET', `/api/v1/players/${INES.player_id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'ASKED_YOU',
        can_add_friend: false,
        nickname: INES.nickname,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [],
        reliability: servedReliability({ player_score: 98, is_new: false }),
      }),
    );
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: INES.nickname }));
    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: recordCloseLabel(false) }));
    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());

    expect(sheetTitle()).not.toBeNull();
    expect(visits()).toEqual([]);

    closeNeedsYourAnswer();
    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
  });

  it('is sent once for a sheet a notice opened, as for one the envelope opened', async () => {
    transport.on('POST', DEVICES_PATH, () => noContent());
    const phone: FakePush = fakePush();
    stubPush(phone);
    envelopeServer([INES]);
    await launchSignedIn();
    await theEnvelope();

    act(() =>
      phone.tap({
        notice_id: 'd0000000-0000-4000-8000-000000000819',
        kind: 'FRIEND_REQUEST',
        opens: 'HOME',
      }),
    );
    expect(await screen.findByRole('header', { name: NEEDS_YOUR_ANSWER_COPY.title })).toBeTruthy();

    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: INES.asked_at }]));
  });
});

describe('what counts as seen (#819)', () => {
  it('is what arrived while the sheet was open and was shown in it: the visit names the newer read', async () => {
    const server = envelopeServer([INES]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    server.arrives(OLA);
    await rereadHome();
    expect(await screen.findByRole('button', { name: notNowLabel(OLA.nickname) })).toBeTruthy();
    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title),
    );
  });

  it('is never what reached the server after the read the sheet showed — that comes back as new', async () => {
    const server = envelopeServer([OLA, INES]);
    await launchSignedIn();
    await openNeedsYourAnswer();

    // Piotr's request reaches the server while the sheet is up, but the phone never reads it.
    server.arrives(PIOTR);
    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
    // The read after the visit counts him, and the badge is back, with the envelope.
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe('Needs your answer, 1 new'),
    );
    expect(badgeOn(envelope()!)).toEqual({ figure: '1', tone: 'news' });
  });

  it('brings the badge back for something that arrives after the close', async () => {
    const server = envelopeServer([INES]);
    await launchSignedIn();
    await openNeedsYourAnswer();
    closeNeedsYourAnswer();
    await waitFor(() => expect(visits()).toHaveLength(1));
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title),
    );

    server.arrives(OLA);
    await rereadHome();

    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe('Needs your answer, 1 new'),
    );
  });
});

/**
 * **TO CONFIRM rides on Home's read** (#819; #815's contract): the sheet is drawn from the one read
 * whose watermark the visit names, so a payment Home's read holds is in it whatever the payments to
 * confirm' own read says — and only then is everything the watermark covers on screen.
 */
describe('TO CONFIRM, from Home’s read (#819)', () => {
  const A_PAYMENT: Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'] =
    {
      seat_charge_id: 'f1000000-0000-4000-8000-000000000819',
      refusal: 'AUTHENTICATION_REQUIRED',
      proposal_id: 'f1000000-0000-4000-8000-000000000820',
      pool_id: 'f1000000-0000-4000-8000-000000000821',
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      starts_at: '2026-10-03T14:00:00Z',
      club: { id: 'f1000000-0000-4000-8000-000000000822', name: 'Bonarka Arena' },
      share_grosze: 3200,
      book_by: '2026-10-02T11:00:00Z',
      confirm_by: null,
      time_to: null,
    };

  it('draws the payments Home’s read holds, and names that read’s watermark on the close', async () => {
    // Their own read has not caught up: Home's is what the sheet shows.
    stubPaymentsToConfirm(transport, []);
    stubHome(transport, {
      needing_you: 1,
      payments_to_confirm: [A_PAYMENT],
      needs_your_answer: { new_count: 1, watermark: '2026-10-01T07:30:00Z' },
    });
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(await screen.findByTestId(`to-confirm-${A_PAYMENT.seat_charge_id}`)).toBeTruthy();
    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: '2026-10-01T07:30:00Z' }]));
  });
});

/**
 * **A hand-off to a screen is a close too** (#819; ADR-0205 §3): *Get your level* on an ask takes
 * the sheet down for good before the questionnaire starts, since nothing navigates from inside a
 * sheet — and the visit goes with it.
 */
describe('handing over to a screen (#819)', () => {
  const RUN = '4d5e6f70-8192-4a3b-8c4d-5e6f70819819';
  const QUESTION: Wire['QuestionResponse'] = {
    id: 'q-played-squash',
    category: 'Recent activity',
    tier: null,
    situation: 'Before anything else',
    text: 'Have you played squash before?',
    qualifier: 'Any level counts',
    options: [
      { id: 'never', text: 'Never played' },
      { id: 'regular', text: 'I play most weeks' },
    ],
  };
  const ASKING: Wire['AssessmentStepResponse'] = {
    assessment_id: RUN,
    status: 'in_progress',
    questions_asked: 0,
    transcript: [],
    question: QUESTION,
  };
  const KUBA_ASKS: Wire['HomeLevelAskSchema'] = {
    sport: 'SQUASH',
    askers: [
      {
        player_id: 'e0000000-0000-4000-8000-000000000822',
        nickname: 'kuba.w',
        photo_id: null,
        photo_url: null,
      },
    ],
  };

  it('sends the visit as Get your level closes the sheet and starts the questionnaire', async () => {
    stubHome(transport, {
      level_asks: [KUBA_ASKS],
      needs_your_answer: { new_count: 1, watermark: '2026-10-01T06:00:00.300Z' },
    });
    transport.on('POST', '/api/v1/assessments', () => json(ASKING, 201));
    transport.on('GET', `/api/v1/assessments/${RUN}`, () => json(ASKING));
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: 'Get your squash level' }));

    await waitFor(() => expect(sheetTitle()).toBeNull());
    await waitFor(() => expect(screen).toHavePathname(`/question/${RUN}`));
    expect(visits()).toEqual([{ watermark: '2026-10-01T06:00:00.300Z' }]);
  });
});

/**
 * **The badge after the close, whatever read lands first** (#819; `proposals`' `newCountAfter`):
 * nothing is written into Home's read, so a read that lands while the visit is on its way — a push,
 * a return to the app — keeps the badge gone, and only a visit that fails for good brings it back.
 */
describe('the badge between the close and the visit (#819)', () => {
  /** Home's read, landed again after `before` reads — and the next tick, which draws it. */
  async function homeReadAgain(before: number) {
    await waitFor(() => expect(homeReads()).toBeGreaterThan(before));
    await waitFor(() =>
      expect(queryClient.getQueryState(proposalKeys.home())?.fetchStatus).toBe('idle'),
    );
    act(() => jest.advanceTimersByTime(0));
  }

  it('stays gone for a read that lands before the visit does, though the server still counts two', async () => {
    const server = envelopeServer([OLA, INES]);
    const land = server.holdVisits();
    await launchSignedIn();
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe('Needs your answer, 2 new'),
    );
    await openNeedsYourAnswer();
    closeNeedsYourAnswer();
    await waitFor(() => expect(visits()).toHaveLength(1));
    const before = homeReads();

    await rereadHome();
    await homeReadAgain(before);

    expect(envelope()?.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title);
    await act(async () => {
      land();
      await Promise.resolve();
    });
  });

  it('comes back when the visit fails for good — nothing was recorded', async () => {
    envelopeServer([OLA, INES]);
    transport.on('POST', NEEDS_YOUR_ANSWER_VISIT_PATH, () =>
      errorResponse(400, 'watermark_in_the_future'),
    );
    await launchSignedIn();
    await openNeedsYourAnswer();
    const before = homeReads();
    closeNeedsYourAnswer();

    await waitFor(() => expect(visits()).toEqual([{ watermark: OLA.asked_at }]));
    await homeReadAgain(before);
    await waitFor(() =>
      expect(envelope()?.props.accessibilityLabel).toBe('Needs your answer, 2 new'),
    );
  });
});
