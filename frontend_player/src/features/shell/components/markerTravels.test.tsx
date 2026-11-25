/**
 * **The selection marker travels** (ADR-0210 §8, 10.2, [#884](https://github.com/Raketa02/Raketa/issues/884)),
 * walked through the shell: when the lit tab changes it slides to it on the 460 ms spring and the new
 * tab colours in after it, and when nothing about the lit tab changes — the dock's first draw, the
 * dock coming back, a press of the lit tab — nothing moves.
 *
 * Read off the marker and each tab's layers as their last frame drew them (`getAnimatedStyle`), on
 * the harness's fake clock. **A press's navigation runs every pending timer**, the harness's own
 * flush, so a slide starts from rest on the frame after it and is read from there; and so **a press
 * mid-flight cannot be walked here** — the second press's flush lands the first slide before the
 * second starts. `TabBar.test.tsx` turns the marker mid-flight on the bar itself, and
 * `tabMarkerMotion.test.ts` holds the turn's numbers.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { AccessibilityInfo, Platform } from 'react-native';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { HOME_GAME_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
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
import {
  launchSignedIn,
  resetKeyboard,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubKeyboard,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeKeyboard, type FakeKeyboard } from '@/test-support/platform';
import {
  colouredIn,
  markerAtRest,
  markerCentre,
  markerUnder,
  slideFromNow,
} from '@/test-support/tabBarReach';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { HOME_COPY, PLAY_COPY } from './shellCopy';

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

/** A frame, and the slide's whole length. */
const FRAME = 16;
const SLIDE = theme.motion.tabMarker.slide;
const { colourIn, colourInAfter } = theme.motion.tabMarker;

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

const advance = (ms: number) => act(() => jest.advanceTimersByTime(ms));

async function launchIntoTheApp() {
  await launchSignedIn();
  expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
}

const pressTab = (label: string) => fireEvent.press(screen.getByLabelText(label));

/** **Nothing moves**: over a slide's length the marker stands at rest under `tab`, which stays lit. */
function staysPut(tab: string) {
  for (const step of [0, FRAME, 60, SLIDE]) {
    advance(step);
    expect(markerUnder()).toBe(tab);
    expect(markerAtRest()).toBe(true);
    expect(colouredIn(tab)).toBe(1);
  }
}

describe('a press on another tab', () => {
  it('slides the marker there: between the columns mid-slide, at rest under the new tab once settled', async () => {
    await launchIntoTheApp();

    pressTab('You');
    const slide = slideFromNow();
    await waitFor(() => expect(screen).toHavePathname('/you'));

    slide(60);
    expect(markerUnder()).toBeUndefined();
    expect(markerCentre()).toBeGreaterThan(0.5);
    expect(markerCentre()).toBeLessThan(2.5);
    expect(markerAtRest()).toBe(false);

    slide(60 + SLIDE);
    expect(markerUnder()).toBe('You');
    expect(markerAtRest()).toBe(true);
  });

  it('colours the new tab in from 140 ms into the slide, whole by 440, and leaves the old one idle at once', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    const slide = slideFromNow();
    await screen.findByRole('header', { name: PLAY_COPY.title });

    slide(FRAME);
    expect(colouredIn('Home')).toBe(0);
    expect(colouredIn('Play')).toBe(0);

    slide(colourInAfter - 1);
    expect(colouredIn('Play')).toBe(0);

    slide(colourInAfter + colourIn / 2);
    expect(colouredIn('Play')).toBeGreaterThan(0);
    expect(colouredIn('Play')).toBeLessThan(1);

    // 440 into the slide, and the frame that draws it.
    slide(colourInAfter + colourIn + FRAME);
    expect(colouredIn('Play')).toBe(1);
    expect(colouredIn('Home')).toBe(0);
  });

  it('slides back the other way on the next press, once the first has settled', async () => {
    await launchIntoTheApp();
    pressTab('You');
    const there = slideFromNow();
    await waitFor(() => expect(screen).toHavePathname('/you'));
    there(SLIDE + FRAME);

    pressTab('Home');
    const back = slideFromNow();
    await waitFor(() => expect(screen).toHavePathname('/'));
    back(60);
    expect(markerCentre()).toBeGreaterThan(0.5);
    expect(markerCentre()).toBeLessThan(2.5);

    back(60 + SLIDE);
    expect(markerUnder()).toBe('Home');
    expect(markerAtRest()).toBe(true);
  });
});

describe('when the lit tab does not change, nothing moves', () => {
  it('on the dock’s first draw — the marker is simply under the tab the player lands on', async () => {
    await launchIntoTheApp();

    staysPut('Home');
  });

  it('on a press of the lit tab at its start', async () => {
    await launchIntoTheApp();

    pressTab('Home');

    staysPut('Home');
  });

  it('on a press of the lit tab from deeper in, which resets the tab to its start', async () => {
    await launchIntoTheApp();
    pressTab('Play');
    await screen.findByRole('header', { name: PLAY_COPY.title });
    advance(SLIDE + FRAME);
    fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.list.newGroupLabel }));
    await screen.findByRole('header', { name: GROUPS_COPY.newGroup.title });
    staysPut('Play');

    pressTab('Play');
    await screen.findByRole('header', { name: PLAY_COPY.title });

    staysPut('Play');
  });

  it('when the dock comes back after the chat — it is placed, not slid', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [bookedRoomRow()]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: HOME_GAME_COPY.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(screen.queryAllByRole('tab')).toHaveLength(0);

    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));

    staysPut('Home');
  });

  describe('when the dock comes back after Android’s keyboard', () => {
    let keyboard: FakeKeyboard;
    let phone: jest.ReplaceProperty<typeof Platform.OS> | undefined;

    beforeEach(() => {
      keyboard = fakeKeyboard();
      stubKeyboard(keyboard);
    });

    afterEach(() => {
      resetKeyboard();
      phone?.restore();
      phone = undefined;
    });

    it('is placed under the lit tab, not slid', async () => {
      phone = jest.replaceProperty(Platform, 'OS', 'android');
      await launchIntoTheApp();
      pressTab('Play');
      fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.list.newGroupLabel }));
      await screen.findByRole('header', { name: GROUPS_COPY.newGroup.title });
      advance(SLIDE + FRAME);
      act(() => keyboard.raise());
      expect(screen.queryAllByRole('tab')).toHaveLength(0);

      act(() => keyboard.drop());

      expect(screen.queryAllByRole('tab')).toHaveLength(3);
      staysPut('Play');
    });
  });
});

/**
 * **Reduce motion places the marker** (ADR-0210 §8): under the new tab, and the colours switched,
 * with nothing between — the frame after the press draws it there.
 */
describe('under Reduce motion', () => {
  // Answered back as the phone usually answers, never restored: `spyOn` on the preset's own mock
  // hands back that mock, and restoring it strips its answer for every suite after this one.
  beforeEach(() => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
  });
  afterEach(() => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
  });

  it('puts the marker under the new tab at once, with the colours switched', async () => {
    await launchIntoTheApp();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    advance(FRAME);

    expect(markerUnder()).toBe('You');
    expect(markerAtRest()).toBe(true);
    expect(colouredIn('You')).toBe(1);
    expect(colouredIn('Home')).toBe(0);
  });
});
