/**
 * **The Chats inbox, walked the way a player walks it**: the real route tree, the real shell,
 * the real bar, and only `fetch` faked.
 *
 * Most of [#360](https://github.com/Raketa02/Raketa/issues/360)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the section holds both sides, an ended
 * row keeps its place and then leaves, the order is whose-turn-then-clock, the row's one line
 * has two sources, the stripe is on exactly the rows with a clock of yours, the badge counts
 * what only you can clear, and the empty state names the act instead of asserting emptiness.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { CHATS_COPY } from '@/features/shell/types';
import { theme } from '@/shared/ui';
import {
  CHALLENGES_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubGate,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { CHALLENGES_HEADING, standingLine, yourAnswerWindowLine } from './challengePresentation';

const ME = GATE_USER.id;
const EWA = 'bbbbbbbb-0000-4000-8000-000000000002';
const TOMEK = 'cccccccc-0000-4000-8000-000000000003';
const OLA = 'dddddddd-0000-4000-8000-000000000004';

const READ_AT = '2026-09-08T12:00:00Z';
const HOUR = 60 * 60 * 1000;

/** A moment measured from `read_at`, which is the only clock any of these screens reads. */
function at(hours: number): string {
  return new Date(Date.parse(READ_AT) + hours * HOUR).toISOString();
}

const PADEL_RATING: Wire['RatingResponse'] = {
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

function challenge(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return {
    challenge_id: 'aaaaaaaa-0000-4000-8000-000000000001',
    sport: 'SQUASH',
    organiser_id: EWA,
    standing: 'AWAITING_ANSWERS',
    opened_at: at(-4),
    seats: [
      { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { side: 'B', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
    ],
    ...over,
  };
}

/** A challenge **I** sent: my seat is accepted from birth and theirs is the one still open. */
function mySend(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return challenge({
    challenge_id: 'eeeeeeee-0000-4000-8000-000000000005',
    organiser_id: ME,
    seats: [
      { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
      { side: 'B', player_id: TOMEK, answer: null, answer_by: at(20), nickname: 'tomek.p' },
    ],
    ...over,
  });
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app with these challenges, and open the Chats tab. */
async function openChats(challenges: readonly Wire['ChallengeSchema'][] = []) {
  stubChallenges(transport, challenges, READ_AT);
  await launchSignedIn();

  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
}

/** The stripe has no name to query by, on purpose — so it is found by what it is drawn in. */
function stripeNodes() {
  return screen
    .UNSAFE_queryAllByType(View)
    .filter((node) => StyleSheet.flatten(node.props.style)?.backgroundColor === theme.color.amber);
}

function stripes(): ViewStyle[] {
  return stripeNodes().map((node) => StyleSheet.flatten(node.props.style));
}

describe('what the section holds', () => {
  it('holds a challenge sent to you and one you sent, under one heading', async () => {
    await openChats([challenge(), mySend()]);

    expect(await screen.findByRole('header', { name: CHALLENGES_HEADING })).toBeTruthy();
    expect(await screen.findByLabelText(/^ewa\.m, Squash/)).toBeTruthy();
    expect(await screen.findByLabelText(/^tomek\.p, Squash/)).toBeTruthy();
  });

  /**
   * The count went with the widening. `CHALLENGES FOR YOU · 1` agreed exactly with the badge,
   * which counts only what is addressed to you — and two numbers meaning different things on
   * one screen is #326's own named failure.
   */
  it('puts no count on the heading, because the badge is the only number here', async () => {
    await openChats([challenge(), mySend()]);

    const heading = await screen.findByRole('header', { name: CHALLENGES_HEADING });

    expect(heading.props.children).toBe(CHALLENGES_HEADING);
  });

  it('keeps an ended challenge, in place, while it is still news', async () => {
    const justDeclined = mySend({
      standing: 'DECLINED',
      ended_at: at(-1),
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
        { side: 'B', player_id: TOMEK, answer: 'DECLINED', answer_by: at(-1), nickname: 'tomek.p' },
      ],
    });

    await openChats([justDeclined]);

    expect(
      await screen.findByLabelText(
        new RegExp(
          standingLine({
            side: 'organiser',
            standing: 'DECLINED',
            player: { kind: 'player', nickname: 'tomek.p' },
          }),
        ),
      ),
    ).toBeTruthy();
  });

  it('lets an ended challenge go once it stops being news, so an inbox is not an archive', async () => {
    const longGone = mySend({
      standing: 'DECLINED',
      opened_at: at(-100),
      // **The row leaves because the wire dates the ending** (#388) rather than because the
      // deadlines let it be guessed at. Without this it would be an ending the app cannot date,
      // which it keeps.
      ended_at: at(-99),
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
        {
          side: 'B',
          player_id: TOMEK,
          answer: 'DECLINED',
          answer_by: at(-99),
          nickname: 'tomek.p',
        },
      ],
    });

    await openChats([longGone]);

    await screen.findByRole('header', { name: CHALLENGES_HEADING });
    expect(screen.queryByLabelText(/^tomek\.p/)).toBeNull();
  });
});

describe('the order', () => {
  /**
   * The badge's own predicate reused as a sort, so the thing the badge is counting is the thing
   * at the top of the list.
   */
  it('puts what you can clear first, least time first, then everything else newest first', async () => {
    const soon = challenge({ challenge_id: 'aaaaaaaa-0000-4000-8000-00000000000a' });
    const later = challenge({
      challenge_id: 'aaaaaaaa-0000-4000-8000-00000000000b',
      seats: [
        { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', nickname: 'tomek.p' },
        { side: 'B', player_id: ME, answer: null, answer_by: at(40), nickname: 'me_' },
      ],
    });
    const myOldSend = mySend({
      challenge_id: 'aaaaaaaa-0000-4000-8000-00000000000c',
      opened_at: at(-30),
    });
    const myNewSend = mySend({
      challenge_id: 'aaaaaaaa-0000-4000-8000-00000000000d',
      opened_at: at(-2),
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
        { side: 'B', player_id: OLA, answer: null, answer_by: at(20), nickname: 'ola.k' },
      ],
    });

    await openChats([myOldSend, later, myNewSend, soon]);

    await screen.findByLabelText(/^ewa\.m, Squash/);
    const handles = screen
      .getAllByRole('button')
      .map((row) => String(row.props.accessibilityLabel).split(',')[0]);

    expect(handles).toEqual(['ewa.m', 'tomek.p', 'ola.k', 'tomek.p']);
  });
});

describe('the row', () => {
  it('says how long you have left when the answer is yours, and never names you', async () => {
    await openChats([challenge()]);

    const row = await screen.findByLabelText(/^ewa\.m, Squash/);

    expect(row.props.accessibilityLabel).toContain(yourAnswerWindowLine('20 hours'));
    expect(row.props.accessibilityLabel).not.toContain('me_');
  });

  it('says the standing sentence on every other row', async () => {
    await openChats([mySend()]);

    const row = await screen.findByLabelText(/^tomek\.p, Squash/);

    expect(row.props.accessibilityLabel).toContain(
      standingLine({ side: 'organiser', standing: 'AWAITING_ANSWERS', awaiting: 1 }),
    );
  });

  it('is one element and one door: the whole row is the button', async () => {
    await openChats([challenge()]);

    const row = await screen.findByLabelText(/^ewa\.m, Squash/);
    fireEvent.press(row);

    await waitFor(() =>
      expect(screen).toHavePathname('/chats/challenge/aaaaaaaa-0000-4000-8000-000000000001'),
    );
  });

  /** A nickname is not shortenable, so the list gives way by dropping whole names. */
  it('drops whole handles rather than shortening one, and says how many it dropped', async () => {
    const four = challenge({
      sport: 'PADEL',
      seats: [
        { side: 'A', player_id: EWA, answer: 'ACCEPTED', nickname: 'ewa.magdalena.wisniewska' },
        { side: 'A', player_id: ME, answer: null, answer_by: at(20), nickname: 'me_' },
        { side: 'B', player_id: TOMEK, answer: 'ACCEPTED', nickname: 'tomek.przybylski' },
        { side: 'B', player_id: OLA, answer: 'ACCEPTED', nickname: 'ola.kowalczyk' },
      ],
    });

    await openChats([four]);

    // Every handle is whole for the ear; the eye loses whole names and never characters. The
    // spoken list joins with a final *and*, which is §22.6's join and what §24.2 spells the
    // conversation row beside this one with ([#363](https://github.com/Raketa02/Raketa/issues/363)).
    const row = await screen.findByLabelText(
      /^ewa\.magdalena\.wisniewska, tomek\.przybylski and ola\.kowalczyk, Padel/,
    );

    expect(row).toBeTruthy();
    expect(await screen.findByText('ewa.magdalena.wisniewska +2')).toBeTruthy();
  });
});

describe('the stripe', () => {
  it('is drawn on exactly the rows whose line is a duration', async () => {
    await openChats([challenge(), mySend()]);

    await screen.findByLabelText(/^ewa\.m, Squash/);

    // Two rows are drawn and only one of them has a clock of the reader's own: the organiser's
    // clock is live, and it is not theirs to clear.
    expect(stripes()).toHaveLength(1);
  });

  it('is amber and full height, and it is not a picture of how much time is left', async () => {
    await openChats([challenge()]);

    await screen.findByLabelText(/^ewa\.m, Squash/);
    const [stripe] = stripes();

    expect(stripe).toMatchObject({
      backgroundColor: theme.color.amber,
      width: theme.size.semanticBar,
      alignSelf: 'stretch',
    });
    // Presence, never magnitude: nothing here encodes a fraction.
    expect(stripe?.height).toBeUndefined();
    expect(stripe?.flex).toBeUndefined();
  });

  it('is hidden from the reader, because the sentence beside it carries the fact', async () => {
    await openChats([challenge()]);

    await screen.findByLabelText(/^ewa\.m, Squash/);
    const [node] = stripeNodes();

    // Both props, because half a hide is a bar announced on one platform and silent on the
    // other — which is the second spelling of the duration this stripe refuses to be.
    expect(node?.props.accessibilityElementsHidden).toBe(true);
    expect(node?.props.importantForAccessibility).toBe('no-hide-descendants');
  });
});

describe('the badge on the bar', () => {
  it('counts a challenge addressed to you and unanswered', async () => {
    await openChats([challenge()]);

    expect(await screen.findByLabelText('Chats, 1 challenge waiting')).toBeTruthy();
  });

  it('never counts your own send, and never counts what has ended', async () => {
    const ended = mySend({
      challenge_id: 'ffffffff-0000-4000-8000-000000000006',
      standing: 'ON',
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
        { side: 'B', player_id: OLA, answer: 'ACCEPTED', nickname: 'ola.k' },
      ],
    });

    await openChats([mySend(), ended]);

    await screen.findByLabelText(/^tomek\.p, Squash/);
    // The column keeps its bare name: neither row is anybody's to clear but the organiser's,
    // and the organiser is the reader.
    expect(screen.getByLabelText('Chats')).toBeTruthy();
  });

  it('draws the identical absence at zero, in flight and refused', async () => {
    transport.on('GET', CHALLENGES_PATH, () => errorResponse(500, 'boom'));
    await launchSignedIn();

    expect(await screen.findByLabelText('Chats')).toBeTruthy();
  });
});

describe('what the tab says when it holds nothing', () => {
  it('names the act instead of asserting that nothing is happening', async () => {
    await openChats([]);

    expect(await screen.findByText(CHATS_COPY.emptyChallenges)).toBeTruthy();
    expect(screen.queryByText(/nothing|empty/i)).toBeNull();
  });

  it('states the limit that makes this a sports app, and promises nothing it has not built', async () => {
    await openChats([]);

    expect(await screen.findByText(CHATS_COPY.panel.title)).toBeTruthy();
    expect(await screen.findByText(CHATS_COPY.panel.body)).toBeTruthy();
    expect(screen.queryByText(/tonight|inside a game or a plan/i)).toBeNull();
  });
});
