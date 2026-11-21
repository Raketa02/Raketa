/**
 * The shell, walked the way a player walks it: through the real route tree, with the real
 * bar, and only `fetch` faked.
 *
 * **The one rule here that cannot be seen is the one this suite exists for.** A shell built
 * out of `<Tabs>` passes every visible assertion below and still fails *back goes where I
 * came from* — the tab bar looks right, every screen is reachable, nothing throws, and a
 * player who left a screen and came back lands on it. So the assertions are about the
 * **stack**: what is underneath, and whether there is anything underneath at all.
 *
 * **The bar is Home · ⚡Play · You, for good** ([#576](https://github.com/Raketa02/Raketa/issues/576)):
 * the old loop's Players and Chats columns, and the feature flag that brought them back, are gone.
 * Play's own feature flag, `explore` (#826), is walked in `theExploreGate.test.tsx`; here Play is
 * as it ships, titled *Groups*.
 */

import Feather from '@expo/vector-icons/Feather';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { AccessibilityInfo, StyleSheet, type ScrollView } from 'react-native';

import { authKeys, NICKNAME_ROW_TITLE } from '@/features/auth/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { levelAsksHeading, notNowLabel, requestsHeading } from '@/features/friends/types';
import {
  AREA_LINE,
  INTRO_TITLE,
  PHOTOS_TITLE,
  TAGS_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  introLine,
  kindOfGameLine,
  photosLine,
  tagsLine,
  weekLine,
  whoYouPlayWithLine,
} from '@/features/player_profile/types';
import {
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  OWN_RECORD_TITLE,
  PLAYER_RELIABILITY_TITLE,
  SKILL_PASSPORT_TITLE,
  passportLine,
  reliabilityLine,
  scoreRingLabel,
} from '@/features/player_record/types';
import { HOME_GAME_COPY, proposalKeys } from '@/features/proposals/types';
import { doorRowLabel, theme } from '@/shared/ui';
import {
  BOOKED_ROOM,
  BOOKING,
  bookedRoom,
  bookedRoomRow,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import { invitation } from '@/test-support/friendsGame';
import {
  closeNeedsYourAnswer,
  envelope,
  openNeedsYourAnswer,
  sheetTitle,
} from '@/test-support/needsYourAnswer';
import { scrollerOf } from '@/test-support/pinned';
import { pullDown } from '@/test-support/swipe';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import {
  DATAFILE_PATH,
  GATE_USER,
  HOME_PATH,
  launchSignedIn,
  OWN_RECORD_SERVED,
  PROFILE_OPTIONS_SERVED,
  PROFILE_SURFACE_SERVED,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubHome,
  stubNotices,
  stubOwnRecord,
  stubPaymentsToConfirm,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOME_COPY, NEEDS_YOUR_ANSWER_COPY, PLAY_COPY } from './shellCopy';
import { YOU_COPY } from './youCopy';

/** One rating and a committed profile: the gate's fourth answer is *the app*. */
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

let transport: Transport;

/**
 * *The player is on Play*: its *Groups* title — what the tab draws as it ships, with `explore` at
 * its code default, off (#826). The switcher is the gate's suite and the segment suite's.
 */
const onPlay = () => screen.findByRole('header', { name: PLAY_COPY.title });

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  // You reads the profile, its options and your own record on arrival — the rows' lines, the
  // header card's face and score, and the reliability row's line.
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  // Play's segment and the games opened are kept on the phone per account.
  await forgetPhonePreferences();
});

/** A player standing on the tab the entry gate lands them on. */
async function launchIntoTheApp() {
  await launchSignedIn();
  expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
}

/** Press one of the three columns by the name the bar gives it. */
function pressTab(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

const columns = () => screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel);

describe('what a player lands on', () => {
  it('opens on Home, with the bar under it — three columns, and no switch for more', async () => {
    await launchIntoTheApp();

    expect(screen).toHavePathname('/');
    expect(columns()).toEqual(['Home', 'Play', 'You']);
  });

  it('lights the tab the player is on, and only that one', async () => {
    await launchIntoTheApp();

    const selected = () =>
      screen
        .getAllByRole('tab')
        .filter((tab) => tab.props.accessibilityState?.selected === true)
        .map((tab) => tab.props.accessibilityLabel);

    expect(selected()).toEqual(['Home']);

    pressTab('You');
    await waitFor(() => expect(selected()).toEqual(['You']));

    pressTab('Play');
    await waitFor(() => expect(selected()).toEqual(['Play']));
  });

  /**
   * **The old loop asks the server nothing** — the bar used to hold its challenges, games and
   * plans for the session. **What the gate asks for is one datafile** (#826, ADR-0206 §6): this
   * environment's, from the features host rather than the API, with no token, read once at launch
   * and not again by Play — the gate reads what is in hand when it mounts.
   */
  it('reads none of the old loop’s lists, and the datafile once, from the features host', async () => {
    await launchIntoTheApp();
    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    pressTab('Play');
    await onPlay();

    const asked = transport.requests.map((request) => request.path);
    for (const old of [
      '/api/v1/challenges',
      '/api/v1/plans',
      '/api/v1/games',
      '/api/v1/interest',
    ]) {
      expect(asked).not.toContain(old);
    }
    expect(asked.filter((path) => path.includes('featurevisor'))).toEqual([DATAFILE_PATH]);
    const [datafile] = transport.requestsTo('GET', DATAFILE_PATH);
    expect(datafile?.url).toBe(`https://features.test.raketa.invalid${DATAFILE_PATH}`);
    expect(datafile?.headers.Authorization).toBeUndefined();
  });
});

/**
 * **Home's badge counts the booked games that need you** — a seat open, a result to enter or
 * confirm, a no-show against you, a payment to confirm
 * ([the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 * The count is the server's `needing_you` on Home's own read, which the shell holds on every
 * screen, so it is there before the player has looked at Home, and it is spoken in the column's
 * own name. Which games are counted is the server's; what is walked here is that the count reaches
 * the bar, and that nothing else is added to it.
 */
describe('Home’s badge', () => {
  it('counts the booked games that need you, on Home, wherever the player is', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })], {
      needing_you: 2,
    });
    await launchSignedIn();

    expect(await screen.findByLabelText('Home, 2 games waiting on you')).toBeTruthy();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(screen.getByLabelText('Home, 2 games waiting on you')).toBeTruthy();

    pressTab('Play');
    await onPlay();
    expect(screen.getByLabelText('Home, 2 games waiting on you')).toBeTruthy();
  });

  it('draws nothing when no game needs you', async () => {
    stubHomeGames(transport, [homeGame()], { needing_you: 0 });
    await launchSignedIn();

    await screen.findByTestId(`home-game-${BOOKING}`);
    expect(screen.getByLabelText('Home')).toBeTruthy();
    expect(screen.queryByLabelText(/^Home, /)).toBeNull();
  });
});

/**
 * **The You tab is a screen, and the last placeholder went with it**
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 * What each row's screen does is its feature's suite's; what the shell owes the tab is the
 * composition — the header card, the three groups with every row in its group, each row
 * spoken as *title, live line* off the read that carries it, the way out at the foot, and the
 * one overlay two of its parts open.
 */
describe('You', () => {
  /** The stubbed profile's one declaration, as the row says it. */
  const DECLARED_LINE = kindOfGameLine([{ sport: 'padel', intent: 'FOR_FUN' }]);
  /** The stubbed record's points and band, as the row says it — `75 · High` (#660). */
  const RELIABILITY_LINE = reliabilityLine({
    playerScore: OWN_RECORD_SERVED.reliability.player_score,
    band: OWN_RECORD_SERVED.reliability.band,
    isNew: OWN_RECORD_SERVED.reliability.is_new,
  });

  /** The tab, with its reads in — the last row's line is the last read to land. */
  async function openYou() {
    await launchIntoTheApp();
    pressTab('You');
    await screen.findByRole('header', { name: YOU_COPY.title });
    await screen.findByLabelText(
      doorRowLabel(
        YOUR_WEEK_TITLE,
        weekLine([
          { day: 2, hour: 19 },
          { day: 6, hour: 9 },
        ]),
      ),
    );
  }

  it('titles the tab as the bar does, and names the three groups over three cards', async () => {
    await openYou();

    // #529: the title stands alone — no *Player profile* over it.
    expect(screen.queryByText('Player profile')).toBeNull();
    for (const group of Object.values(YOU_COPY.groups)) {
      expect(screen.getByText(group)).toBeTruthy();
    }
  });

  it('draws every row in its group, each spoken as its title and its live line', async () => {
    await openYou();

    // Playing — the two facts a player cannot touch, and the declaration.
    expect(
      screen.getByLabelText(
        doorRowLabel(SKILL_PASSPORT_TITLE, passportLine([{ sport: 'padel', level: 2.71 }])),
      ),
    ).toBeTruthy();
    expect(
      await screen.findByLabelText(doorRowLabel(PLAYER_RELIABILITY_TITLE, RELIABILITY_LINE)),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(WHAT_KIND_OF_GAME_TITLE, DECLARED_LINE)),
    ).toBeTruthy();
    // Your games — the three declarations, each off the profile read; who they play with says
    // the preference, and never the gender.
    expect(
      screen.getByLabelText(
        doorRowLabel(
          YOUR_WEEK_TITLE,
          weekLine([
            { day: 2, hour: 19 },
            { day: 6, hour: 9 },
          ]),
        ),
      ),
    ).toBeTruthy();
    expect(screen.getByLabelText(doorRowLabel(WHERE_YOU_PLAY_TITLE, AREA_LINE))).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any'))),
    ).toBeTruthy();
    // On your card — the door to the sheet, the three social facts off the read, and the name.
    expect(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(
        doorRowLabel(
          PHOTOS_TITLE,
          photosLine([{ photoId: 'photo-held-1', review: 'allowed' }, { photoId: 'photo-held-2' }]),
        ),
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(
        doorRowLabel(
          TAGS_TITLE,
          tagsLine(
            ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'],
            PROFILE_OPTIONS_SERVED.social_tag_selection.maximum_tags,
          ),
        ),
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(INTRO_TITLE, introLine(PROFILE_SURFACE_SERVED.intro))),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(NICKNAME_ROW_TITLE, GATE_USER.nickname ?? '')),
    ).toBeTruthy();
  });

  /**
   * **Two rows left with the questions that set them** ([#582](https://github.com/Raketa02/Raketa/issues/582)):
   * *How far to look* and *Game suggestions* were read only by the old loop's ranking, so a
   * player who changed either changed nothing they would ever see. *Your games* is the week, the
   * area and who they play with — every one of them read when a game is proposed.
   */
  it('lists neither How far to look nor Game suggestions under Your games', async () => {
    await openYou();

    expect(screen.queryByText('How far to look')).toBeNull();
    expect(screen.queryByText('Game suggestions')).toBeNull();

    const drawn = screen.getAllByText(/./);
    const at = (text: string) => drawn.indexOf(screen.getByText(text));
    const finding = [
      YOU_COPY.groups.yourGames,
      YOUR_WEEK_TITLE,
      WHERE_YOU_PLAY_TITLE,
      WHO_YOU_PLAY_WITH_TITLE,
      YOU_COPY.groups.onYourCard,
    ].map(at);
    expect(finding).toEqual([...finding].sort((a, b) => a - b));
  });

  /**
   * The rows are the features' and the groups are the shell's: *which row sits in which
   * group* is the one thing this file decides, so it is asserted as an order rather than as
   * eleven presences.
   */
  it('lays the groups down in the order the three questions are asked', async () => {
    await openYou();

    const drawn = screen.getAllByText(/./);
    const at = (text: string) => drawn.indexOf(screen.getByText(text));
    expect(at(YOU_COPY.groups.playing)).toBeLessThan(at(SKILL_PASSPORT_TITLE));
    expect(at(SKILL_PASSPORT_TITLE)).toBeLessThan(at(YOU_COPY.groups.yourGames));
    expect(at(YOU_COPY.groups.yourGames)).toBeLessThan(at(YOUR_WEEK_TITLE));
    expect(at(YOUR_WEEK_TITLE)).toBeLessThan(at(YOU_COPY.groups.onYourCard));
    expect(at(YOU_COPY.groups.onYourCard)).toBeLessThan(at(NICKNAME_ROW_TITLE));
    expect(at(NICKNAME_ROW_TITLE)).toBeLessThan(at('Sign out'));
  });

  /**
   * **_Finding players_ is _Your games_** (ADR-0200 §10, #733): nothing on the tab finds players
   * any more, and the three rows hold what a game proposed to the player reads.
   */
  it('says Your games over the week, the area and who they play with — never Finding players', async () => {
    await openYou();

    expect(screen.getByText('Your games')).toBeTruthy();
    expect(screen.queryByText(/Finding players/i)).toBeNull();
  });

  it('draws the header card from the three reads, and the score in its ring', async () => {
    await openYou();

    expect(
      await screen.findByLabelText(scoreRingLabel(OWN_RECORD_SERVED.reliability.player_score)),
    ).toBeTruthy();
    // The nickname, with no handle line under it and never with an @ (ADR-0199 §1) — drawn by
    // the card and by the *Nickname* row's line — and the intro in the drawing's marks.
    expect(screen.getAllByText(GATE_USER.nickname ?? '')).toHaveLength(2);
    expect(screen.queryByText(`@${GATE_USER.nickname ?? ''}`)).toBeNull();
    // Twice on the tab: the card quotes the record's line, and the *Intro* row quotes the
    // profile read's — the same line, off two reads (#471).
    expect(screen.getAllByText(`“${OWN_RECORD_SERVED.intro ?? ''}”`)).toHaveLength(2);
  });

  it('opens your own record, retitled, from the header card and from the row', async () => {
    await openYou();

    fireEvent.press(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    );

    // The sheet is up under the server's own title for a record that is yours, and the read
    // behind it is the ungated `/me` route.
    expect(await screen.findByRole('header', { name: OWN_RECORD_TITLE })).toBeTruthy();
    expect(transport.requestsTo('GET', '/api/v1/players/me/record').length).toBeGreaterThan(0);
    fireEvent.press(screen.getByLabelText(`Close ${OWN_RECORD_TITLE.toLowerCase()}`));
    await waitFor(() =>
      expect(screen.queryByRole('header', { name: OWN_RECORD_TITLE })).toBeNull(),
    );

    // The header card is one press whose name is the identity; its hint names the door.
    fireEvent.press(screen.getByHintText(`Opens ${OWN_RECORD_TITLE.toLowerCase()}`));
    expect(await screen.findByRole('header', { name: OWN_RECORD_TITLE })).toBeTruthy();
  });

  it('never tells the player nothing is happening', async () => {
    // Home is where a game lands, so a placeholder asserting emptiness would be lying one tap
    // after one was booked. What the lines *say* is `shellCopy.test.ts`'s; this is the rendered
    // half — the tab a launch actually opens on, with the sentence on it.
    await launchIntoTheApp();

    expect(screen.queryByText(/nothing is happening/i)).toBeNull();
  });

  it('keeps the way out of a session on You, pinned at the foot', async () => {
    // The account panel outlived the screen it used to be: sign-out is the only way back
    // to the beginning, and the tab about the player is where it goes.
    await openYou();

    // #529: pinned under the page, so it is in one place however many rows are over it.
    expect(scrollerOf(screen.getByText(NICKNAME_ROW_TITLE))).toBeDefined();
    expect(scrollerOf(screen.getByLabelText('Sign out'))).toBeUndefined();
  });

  it('lets a player out of the session from inside the shell', async () => {
    // The one flow the shell moved: sign-out used to be the screen a player landed on, and
    // is now three screens inside a stack the guard has to unwind from.
    transport.on('POST', '/api/v1/auth/logout', () => json({ message: 'Logged out' }));
    await launchIntoTheApp();

    pressTab('You');
    fireEvent.press(await screen.findByLabelText('Sign out'));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

describe('⚡Play', () => {
  it('always opens Play’s root, from whichever tab the player was on', async () => {
    await launchIntoTheApp();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));

    pressTab('Play');

    expect(await onPlay()).toBeTruthy();
    expect(screen).toHavePathname('/play');
  });

  it('stays lit for the screen it opened', async () => {
    await launchIntoTheApp();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(screen.getByRole('tab', { name: 'Play', selected: true })).toBeTruthy();
  });

  it('leaves Home underneath, so back leaves Play entirely', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    // The platform's own back, which is what the rule is about: Play does not refuse to be the
    // last screen, it has Home underneath it.
    act(() => router.back());

    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('does nothing at all when the tab pressed is the one already on screen', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // And the stack has not grown a second Play to walk back through.
    expect(router.canGoBack()).toBe(true);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(router.canGoBack()).toBe(false);
  });
});

describe('the shell keeps no per-tab history', () => {
  it('lays You over Home, so back from You is Home and nothing more', async () => {
    await launchIntoTheApp();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));

    // `[Home, You]`, as Play is `[Home, Play]`: back from a tab that is not the start goes to the
    // start, and the start is the last thing there is.
    act(() => router.back());
    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(router.canGoBack()).toBe(false);
  });

  it('throws away Play depth when the player leaves, and does not restore it', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    // Play's screen went with it: only Home is underneath You. This is the assertion `<Tabs>` fails
    // silently — it would walk back into Play.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(router.canGoBack()).toBe(false);

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });
});

/**
 * **Home is drawn once and kept under every tab** — it is the heaviest screen in the app, and a
 * device spent four seconds rebuilding it on every press of every tab. The same Home is what comes
 * back, and a press that lands on it still lands at its start.
 */
describe('Home, kept', () => {
  it('is the same Home after You and after Play, never one drawn again', async () => {
    await launchIntoTheApp();
    const home = screen.getByText(HOME_COPY.empty.line);

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    pressTab('Home');
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.getByText(HOME_COPY.empty.line)).toBe(home);

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    pressTab('Home');
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.getByText(HOME_COPY.empty.line)).toBe(home);
  });

  it('keeps it under ⚡Play pressed from Home, rather than laying a second one down', async () => {
    await launchIntoTheApp();
    const home = screen.getByText(HOME_COPY.empty.line);

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    act(() => router.back());

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.getByText(HOME_COPY.empty.line)).toBe(home);
  });

  it('shows its top when a press lands on it, and not when the player comes back to it', async () => {
    await launchIntoTheApp();
    // The page's scroller, as the test instance holds it (`scrollerOf` reads only the way up).
    const page = scrollerOf(screen.getByText(HOME_COPY.empty.line)) as unknown as {
      readonly instance: ScrollView;
    };
    // The harness's `ScrollView` shares one mock `scrollTo` across instances, so it starts clean.
    const scrollTo = jest.spyOn(page.instance, 'scrollTo');
    scrollTo.mockClear();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    // Back goes where the player was, scroll and all.
    expect(scrollTo).not.toHaveBeenCalled();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    pressTab('Home');
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(scrollTo).toHaveBeenCalledWith({ y: 0, animated: false });
  });
});

/**
 * **Needs your answer** ([#816](https://github.com/Raketa02/Raketa/issues/816),
 * [#817](https://github.com/Raketa02/Raketa/issues/817), ADR-0205 §1–§2; home refactor 1 and 2): the
 * header's envelope, there only while something waits, and the sheet it opens. What each section's
 * tiles say and do is `friends`' and `proposals`' suites'; this is the frame — the header's order, the
 * sheet's title, focus and ways out, the four sections' order, and the self-close.
 */
describe('Needs your answer', () => {
  const INES: Wire['HomeFriendRequestSchema'] = {
    player_id: 'e0000000-0000-4000-8000-000000000816',
    nickname: 'ines.d',
    photo_id: null,
    photo_url: null,
    asked_at: '2026-11-17T07:00:00Z',
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
  const KUBA_ASKS: Wire['HomeLevelAskSchema'] = {
    sport: 'SQUASH',
    askers: [
      {
        player_id: 'e0000000-0000-4000-8000-000000000817',
        nickname: 'kuba.w',
        photo_id: null,
        photo_url: null,
      },
    ],
  };
  const SET_ASIDE = `/api/v1/friends/requests/${INES.player_id}/set-aside`;
  /** A share refused while the reader was elsewhere, waiting in TO CONFIRM (#817). */
  const A_PAYMENT: Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'] =
    {
      seat_charge_id: 'f1000000-0000-4000-8000-000000000001',
      refusal: 'AUTHENTICATION_REQUIRED',
      proposal_id: 'f1000000-0000-4000-8000-000000000002',
      pool_id: 'f1000000-0000-4000-8000-000000000003',
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      starts_at: '2026-10-03T14:00:00Z',
      club: { id: 'f1000000-0000-4000-8000-000000000004', name: 'Bonarka Arena' },
      share_grosze: 3200,
      book_by: '2026-10-02T11:00:00Z',
      confirm_by: null,
      time_to: null,
    };

  /** Home's read, holding `waiting` until *Not now* takes Inés's request off it. */
  function serveHome(waiting: Partial<Wire['HomeResponse']>) {
    stubHome(transport, waiting);
    transport.on('POST', SET_ASIDE, () => {
      stubHome(transport, { ...waiting, friend_requests: [] });
      return noContent();
    });
  }

  /** The header's three, left to right, by what each is. */
  const header = () =>
    screen
      .getAllByRole('button')
      .map((node) =>
        node.props.testID === 'needs-your-answer-envelope'
          ? 'envelope'
          : node.props.testID === 'ranking-trophy'
            ? 'trophy'
            : /^Recent notifications/.test(String(node.props.accessibilityLabel))
              ? 'bell'
              : undefined,
      )
      .filter((one) => one !== undefined);

  /** The section headings the sheet draws under its title, top to bottom. */
  const sections = () =>
    within(screen.getByTestId('bottom-sheet'))
      .getAllByRole('header')
      .map((node) => node.props.children as unknown)
      .filter((text): text is string => typeof text === 'string');

  it('reads envelope, bell, trophy — the trophy in the far-right corner — while something waits', async () => {
    serveHome({ friend_requests: [INES] });
    await launchIntoTheApp();

    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(header()).toEqual(['envelope', 'bell', 'trophy']);
  });

  it('is an ink Feather mail mark in a 44pt target, named Needs your answer', async () => {
    serveHome({ friend_requests: [INES] });
    await launchIntoTheApp();

    const mark = await waitFor(() => {
      const found = envelope();
      expect(found).not.toBeNull();
      return found!;
    });
    expect(mark.props.accessibilityLabel).toBe(NEEDS_YOUR_ANSWER_COPY.title);
    expect(StyleSheet.flatten(mark.props.style)).toMatchObject({
      width: theme.size.minTouch,
      height: theme.size.minTouch,
    });
    const glyph = within(mark).UNSAFE_getByType(Feather);
    expect(glyph.props.name).toBe('mail');
    expect(glyph.props.color).toBe(theme.color.ink);
  });

  it('draws no envelope while nothing waits, and the bell and the trophy keep their places', async () => {
    serveHome({});
    await launchIntoTheApp();

    await waitFor(() => expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0));
    expect(envelope()).toBeNull();
    expect(header()).toEqual(['bell', 'trophy']);
  });

  it('opens on the envelope, its title taking the focus, TO CONFIRM, FRIENDS GAME, FRIEND REQUESTS, ASKED FOR A LEVEL', async () => {
    stubPaymentsToConfirm(transport, [A_PAYMENT]);
    serveHome({
      needing_you: 1,
      friends_games: [invitation()],
      friend_requests: [INES],
      level_asks: [KUBA_ASKS],
    });
    await launchIntoTheApp();
    // Nothing that waits is on Home itself.
    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(screen.queryByTestId('to-confirm')).toBeNull();
    expect(screen.queryByTestId('friends-games')).toBeNull();
    expect(screen.queryByTestId('friend-requests')).toBeNull();
    expect(screen.queryByTestId('level-asks')).toBeNull();
    const focus = jest.spyOn(AccessibilityInfo, 'setAccessibilityFocus');

    try {
      // Only what the press moves: Home's own launch may move focus before it.
      focus.mockClear();
      await openNeedsYourAnswer();
      await screen.findByTestId('to-confirm');

      expect(focus).toHaveBeenCalledTimes(1);
      expect(sections()).toEqual([
        'To confirm · 1',
        'Friends game · 1',
        requestsHeading(1),
        levelAsksHeading(1),
      ]);
    } finally {
      focus.mockRestore();
    }
  });

  /** #817: a payment to confirm or a friends game invitation waits there too, alone. */
  it.each<[string, () => void]>([
    ['a payment to confirm', () => stubPaymentsToConfirm(transport, [A_PAYMENT])],
    ['a friends game invitation', () => serveHome({ friends_games: [invitation()] })],
  ])('draws the envelope for %s alone', async (_, waiting) => {
    serveHome({});
    waiting();
    await launchIntoTheApp();

    await waitFor(() => expect(envelope()).not.toBeNull());
    await openNeedsYourAnswer();
    expect(sections()).toHaveLength(1);
  });

  it('hides a section with nothing in it', async () => {
    serveHome({ level_asks: [KUBA_ASKS] });
    await launchIntoTheApp();

    await openNeedsYourAnswer();

    expect(sections()).toEqual([levelAsksHeading(1)]);
    expect(screen.queryByTestId('friend-requests')).toBeNull();
  });

  it('closes on ✕, on the backdrop and on a pull down its head, and the envelope stays', async () => {
    serveHome({ friend_requests: [INES] });
    await launchIntoTheApp();

    await openNeedsYourAnswer();
    closeNeedsYourAnswer();
    await waitFor(() => expect(sheetTitle()).toBeNull());

    await openNeedsYourAnswer();
    fireEvent.press(screen.getByTestId('bottom-sheet-scrim', { includeHiddenElements: true }));
    await waitFor(() => expect(sheetTitle()).toBeNull());

    await openNeedsYourAnswer();
    expect(pullDown(sheetTitle()!, theme.size.sheetSwipe.close)).toBe(true);
    await waitFor(() => expect(sheetTitle()).toBeNull());

    expect(envelope()).not.toBeNull();
  });

  it('closes itself on the last answer, and the envelope goes', async () => {
    serveHome({ friend_requests: [INES] });
    stubNotices(transport, []);
    await launchIntoTheApp();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: notNowLabel(INES.nickname) }));

    await waitFor(() => expect(transport.requestsTo('POST', SET_ASIDE)).toHaveLength(1));
    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
    expect(header()).toEqual(['bell', 'trophy']);
  });

  it('stays closed when something new arrives after the last answer — the envelope comes back', async () => {
    serveHome({ friend_requests: [INES] });
    stubNotices(transport, []);
    await launchIntoTheApp();
    await openNeedsYourAnswer();
    fireEvent.press(screen.getByRole('button', { name: notNowLabel(INES.nickname) }));
    await waitFor(() => expect(envelope()).toBeNull());

    stubHome(transport, { level_asks: [KUBA_ASKS] });
    await act(() => queryClient.invalidateQueries({ queryKey: proposalKeys.home() }));

    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(sheetTitle()).toBeNull();
  });
});

/**
 * **The shell outlives the entry gate re-reading the player, and a shell built from nothing opens
 * on Home.** Two facts, and the first press after a cold start on a device was where they were both
 * found false at once: bootstrap **seeds** the player into the cache, so the gate's own read of
 * them never fetched at mount; thirty seconds later that seed is stale, and the first screen to
 * mount `useCurrentUser()` refetches it — which the gate took for *a read this mount is in the
 * middle of replacing* and answered `pending`, rendering nothing and tearing the authenticated
 * tree down for the length of the round trip. The tree came back with a fresh stack, and a fresh
 * stack opens on the **first route name it holds**, which was `play/index` — so every first press
 * landed on Play with ⚡Play lit, whichever column had been pressed.
 *
 * `launchSignedIn` never seeded the player, which is why every suite here stayed green while a
 * device did that on every launch. The first test puts the cache the way bootstrap leaves it.
 */
describe('the shell survives the gate re-reading the player', () => {
  /** The cache as `restoreSessionStep` leaves it: the validated player, fresh, unfetched here. */
  function seedThePlayer() {
    queryClient.setQueryData(authKeys.currentUser(), {
      id: GATE_USER.id,
      email: GATE_USER.email,
      nickname: GATE_USER.nickname ?? undefined,
      hasPlayerProfile: true,
      profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
    });
  }

  it('stays on the tab the player pressed while a screen refetches the seeded player', async () => {
    seedThePlayer();
    await launchIntoTheApp();
    // The seed was honoured: the gate answered from it and asked the server nothing.
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(0);

    // The seed goes stale — on a device, thirty seconds on, the app's `staleTime` — and the next
    // screen to read the player will send for a fresh copy. That refetch is a background one: the
    // gate already has its answer, and it is not what this mount set out to replace.
    //
    // Marked stale rather than waited out: the seed is written before `renderRouter` installs its
    // fake timers, so its timestamp is on the previous test's clock, and how far that clock ran
    // decided whether thirty-one seconds were enough. They were only while the gate's two retired
    // reads (#730) spent half a minute of fake time on every launch. Nothing is refetched here —
    // the gate observes the read, and only a screen mounting one more observer sends for it.
    act(() => {
      void queryClient.invalidateQueries({
        queryKey: authKeys.currentUser(),
        refetchType: 'none',
      });
    });

    pressTab('You');

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(1));
    await waitFor(() =>
      expect(queryClient.getQueryState(authKeys.currentUser())?.fetchStatus).toBe('idle'),
    );
    // Let anything the gate might have torn down come back before looking.
    jest.advanceTimersByTime(50);
    act(() => {});

    expect(screen).toHavePathname('/you');
    expect(await screen.findByRole('header', { name: YOU_COPY.title })).toBeTruthy();
    expect(screen.queryByRole('header', { name: PLAY_COPY.title })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(3);
  });

  it('opens on Home, never on the first route it happens to list, when rebuilt from nothing', async () => {
    // The gate genuinely losing its answer is the one way the tree is rebuilt, and the stack it
    // comes back with holds no history — so what it opens on is the initial route, which has to
    // be the tab the gate lands on rather than whichever screen the shell listed first for its
    // transition. Reset rather than invalidated: an invalidated read still holds its answer.
    //
    // The re-read is **held open**, for the reason the gate's own suite holds its own: a
    // navigator torn down forgets its state one tick later, and on a device the round trip is
    // longer than that tick. Answered at once, the stack would come back rehydrated onto You
    // and prove nothing about a stack that holds no history at all.
    await launchIntoTheApp();
    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));

    // The gate's one read is the player (#730): the ratings and the run route nowhere now.
    let answerMe = () => {};
    const held = new Promise<void>((resolve) => {
      answerMe = resolve;
    });
    transport.on('GET', '/api/v1/users/me', async () => {
      await held;
      return json<Wire['MeResponse']>({ ...GATE_USER, has_player_profile: true });
    });

    act(() => {
      void queryClient.resetQueries({ queryKey: authKeys.currentUser() });
    });

    // Query tells its observers on a timer of its own, and the gate answers on the render that
    // follows: nothing, not a route tree — the bar is gone with everything under the gate.
    jest.advanceTimersByTime(10);
    act(() => {});
    expect(screen.queryAllByRole('tab')).toHaveLength(0);
    // One tick later the navigator that was under it has forgotten its state, as it would
    // have on a device long before the answer came back.
    jest.advanceTimersByTime(10);
    act(() => {});

    answerMe();

    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByRole('header', { name: PLAY_COPY.title })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(3);
  });
});

/**
 * **The bar stands down inside a booked game's chat, and nowhere else.** The composer replaces it
 * there so the keyboard and the stream get the whole screen
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)) — and it is *not rendered* rather than
 * hidden, because the bar is a flex sibling of the navigator and a hidden one would still take its
 * height and the bottom inset. The details the room is pushed over keep their bar, which is what a
 * prefix match under `/booking/…` would get wrong.
 */
describe('the bar stands down inside a booked game’s chat', () => {
  const tabs = () => screen.queryAllByRole('tab');

  it('draws no bar in the room, and draws it again on the way back to the details', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [bookedRoomRow()]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME_GAME_COPY.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(tabs()).toHaveLength(3);
    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(tabs()).toHaveLength(0);

    act(() => router.back());

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(tabs()).toHaveLength(3);
  });
});
