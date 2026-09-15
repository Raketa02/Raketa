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

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
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
  stubConversation,
  stubConversations,
  stubEntries,
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
      { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
      { side: 'B', player_id: ME, answer: null, answer_by: at(20), name: 'me_' },
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
      { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
      { side: 'B', player_id: TOMEK, answer: null, answer_by: at(20), name: 'tomek.p' },
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
   * **A row draws the name, space and all, and never the nickname**
   * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
   * §4): *Diego Fabregat*, whole, drawn and spoken — and no `@` anywhere on the tab, because
   * two Diegos are told apart on the record and not on a row.
   */
  it('names the people on a row by their whole names', async () => {
    await openChats([
      challenge({
        seats: [
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'Diego Fabregat' },
          { side: 'B', player_id: ME, answer: null, answer_by: at(20), name: 'Ania Kowalska' },
        ],
      }),
    ]);

    const row = await screen.findByLabelText(/^Diego Fabregat, Squash/);
    expect(within(row).getByText('Diego Fabregat')).toBeTruthy();
    expect(screen.queryByText(/@/)).toBeNull();
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
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        { side: 'B', player_id: TOMEK, answer: 'DECLINED', answer_by: at(-1), name: 'tomek.p' },
      ],
    });

    await openChats([justDeclined]);

    expect(
      await screen.findByLabelText(
        new RegExp(
          standingLine({
            side: 'organiser',
            standing: 'DECLINED',
            player: { kind: 'player', name: 'tomek.p' },
          }),
        ),
      ),
    ).toBeTruthy();
  });

  /**
   * **A no of my own leaves at once.** The row is kept a day to tell the reader something they
   * did not do; a decline is their own act, so *You said no* is not news to them — on a singles
   * court their no ended, and on a doubles court that carries on filling without them alike. The
   * organiser's row for the same no stays its day, which is the case above this one.
   */
  it('drops a challenge I said no to, whether it ended or carries on without me', async () => {
    const iEnded = challenge({
      standing: 'DECLINED',
      ended_at: at(-1),
      seats: [
        { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
        { side: 'B', player_id: ME, answer: 'DECLINED', answer_by: at(20), name: 'me_' },
      ],
    });
    const iLeft = challenge({
      challenge_id: 'bbbbbbbb-0000-4000-8000-000000000002',
      sport: 'PADEL',
      standing: 'LINE_UP_INCOMPLETE',
      seats: [
        { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
        { side: 'A', player_id: ME, answer: 'DECLINED', answer_by: at(20), name: 'me_' },
        { side: 'B' },
        { side: 'B' },
      ],
    });

    await openChats([iEnded, iLeft, mySend()]);

    await screen.findByLabelText(/^tomek\.p, Squash/);
    expect(screen.queryByLabelText(/^ewa\.m/)).toBeNull();
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
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        {
          side: 'B',
          player_id: TOMEK,
          answer: 'DECLINED',
          answer_by: at(-99),
          name: 'tomek.p',
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
        { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
        { side: 'B', player_id: ME, answer: null, answer_by: at(40), name: 'me_' },
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
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        { side: 'B', player_id: OLA, answer: null, answer_by: at(20), name: 'ola.k' },
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

  /**
   * **A court still being filled names the people still on it**
   * ([#429](https://github.com/Raketa02/Raketa/issues/429)): B said yes, C and D said no, and the
   * row drew three faces and *+2* over *2 in, 2 seats open* — a four that was a two. The seats
   * given up keep their occupants on the wire; the row is who you would play with.
   */
  it('names only the people still on a court being filled — one face, and no count', async () => {
    const oneIn = mySend({
      sport: 'PADEL',
      standing: 'LINE_UP_INCOMPLETE',
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
        { side: 'B', player_id: EWA, answer: 'DECLINED', answer_by: at(20), name: 'ewa.m' },
        { side: 'B', player_id: OLA, answer: 'DECLINED', answer_by: at(20), name: 'ola.k' },
      ],
    });

    await openChats([oneIn]);

    const row = await screen.findByLabelText(/^tomek\.p, Padel/);
    expect(row.props.accessibilityLabel).not.toContain('ewa.m');
    expect(screen.getByText('tomek.p')).toBeTruthy();
    expect(screen.queryByText(/\+\d/)).toBeNull();
  });

  /**
   * **And a court that ended on somebody leaving it, with me the one left, has no row at all**
   * ([#429](https://github.com/Raketa02/Raketa/issues/429)): B took the yes back after C and D
   * said no, so the court is over (`DECLINED` — a departure is a no) with nobody committed to it
   * but me. The room the yes opened is where that was told; the row has no news to keep a day.
   */
  it('drops a court that ended on somebody leaving, with me the one left on it', async () => {
    const theyAllWent = mySend({
      sport: 'PADEL',
      standing: 'DECLINED',
      ended_at: at(-1),
      seats: [
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        { side: 'A', player_id: TOMEK, answer: 'LEFT', answer_by: at(20), name: 'tomek.p' },
        { side: 'B', player_id: EWA, answer: 'DECLINED', answer_by: at(20), name: 'ewa.m' },
        { side: 'B', player_id: OLA, answer: 'DECLINED', answer_by: at(20), name: 'ola.k' },
      ],
    });

    await openChats([theyAllWent]);

    expect(await screen.findByText(CHATS_COPY.emptyChallenges)).toBeTruthy();
    expect(screen.queryByLabelText(/tomek\.p/)).toBeNull();
  });

  /** A name is not shortenable, so the list gives way by dropping whole names. */
  it('drops whole handles rather than shortening one, and says how many it dropped', async () => {
    const four = challenge({
      sport: 'PADEL',
      seats: [
        { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.magdalena.wisniewska' },
        { side: 'A', player_id: ME, answer: null, answer_by: at(20), name: 'me_' },
        { side: 'B', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.przybylski' },
        { side: 'B', player_id: OLA, answer: 'ACCEPTED', name: 'ola.kowalczyk' },
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

describe('coming back to the list', () => {
  /**
   * **The return re-reads the standing** ([#429](https://github.com/Raketa02/Raketa/issues/429)
   * A5, A6). The section stays mounted under the room the tab pushes over it, a room's nudge
   * never touches this list by design (`useLiveConversation`), and popping the stack is neither a
   * mount nor a foreground — so the row read *Waiting on 2 answers* under a room in which the
   * player had just read *C said no*, and only a tab switch, which remounts, repaired it. The
   * return is the moment the row is looked at again, and it is what marks the list stale.
   */
  it('re-reads the challenges when the player comes back from a room', async () => {
    const ROOM = 'eeeeeeee-0000-4000-8000-00000000000e';
    const members = [
      { player_id: ME, name: 'me_' },
      { player_id: EWA, name: 'ewa.m' },
    ];
    const four = (olaAnswer: 'DECLINED' | null) =>
      mySend({
        sport: 'PADEL',
        seats: [
          { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
          { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
          { side: 'B', player_id: TOMEK, answer: null, answer_by: at(20), name: 'tomek.p' },
          { side: 'B', player_id: OLA, answer: olaAnswer, answer_by: at(20), name: 'ola.k' },
        ],
      });
    stubConversations(transport, [
      {
        conversation_id: ROOM,
        challenge_id: four(null).challenge_id,
        game_id: null,
        sport: 'PADEL',
        members,
        people: members,
        last_entry: null,
      },
    ]);
    stubConversation(transport, {
      read_at: READ_AT,
      conversation_id: ROOM,
      challenge_id: four(null).challenge_id,
      game_id: null,
      sport: 'PADEL',
      members,
      people: members,
      entries: [],
    });
    stubEntries(transport, ROOM);
    await openChats([four(null)]);

    const waitingOnTwo = standingLine({
      side: 'organiser',
      standing: 'AWAITING_ANSWERS',
      awaiting: 2,
    });
    expect(
      (await screen.findByLabelText(/^ewa\.m, tomek\.p and ola\.k, Padel/)).props
        .accessibilityLabel,
    ).toContain(waitingOnTwo);

    fireEvent.press(screen.getByLabelText(/^ewa\.m, Padel/));
    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));

    // While the player is in the room, ola.k says no. The room hears it as a line; the list
    // will say so the next time it is asked — and nothing has asked it.
    stubChallenges(transport, [four('DECLINED')], READ_AT);
    const reads = transport.requestsTo('GET', CHALLENGES_PATH).length;

    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    // The re-read row: one fewer answer waited on, and — a seat given up is not drawn on a court
    // still being filled — ola.k no longer among the people it names.
    const waitingOnOne = standingLine({
      side: 'organiser',
      standing: 'AWAITING_ANSWERS',
      awaiting: 1,
    });
    await waitFor(() =>
      expect(
        screen.getByLabelText(/^ewa\.m and tomek\.p, Padel/).props.accessibilityLabel,
      ).toContain(waitingOnOne),
    );
    expect(screen.queryByLabelText(/ola\.k, Padel/)).toBeNull();
    expect(transport.requestsTo('GET', CHALLENGES_PATH)).toHaveLength(reads + 1);
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
        { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
        { side: 'B', player_id: OLA, answer: 'ACCEPTED', name: 'ola.k' },
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
