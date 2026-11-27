/**
 * **The sport pill, as a page holds it** — the pill in the header's slot, the bar it opens onto
 * floating over the page, and what folds it (#774). The games deck's group page and Rankings draw
 * this one control; each hands it its sports, the sport it is on and its own words, and hears back
 * a pick. `SportPill.test.tsx` holds the bar's unfold at its own seam; the group page's router suite
 * walks the deck's filter end to end.
 *
 * The navigator is real — `expo-router/testing-library` over a two-route stack — because leaving
 * the page is one of the things that folds the bar, and a blur is the navigator's to send.
 */

import { Stack, router } from 'expo-router';
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import { Text, View } from 'react-native';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  ALL_SPORTS,
  SportPillFrame,
  type AnotherSport,
  type SportChoice,
  type SportPillWords,
} from './SportPillFrame';
import { theme } from './theme';

const NAMES: Readonly<Record<Sport, string>> = {
  padel: 'Padel',
  tennis: 'Tennis',
  squash: 'Squash',
  badminton: 'Badminton',
};

/** A page's words — not any feature's: the control says only what it is handed. */
const WORDS: SportPillWords = {
  sportName: (sport) => NAMES[sport],
  pillLabel: (sport) => `Shown for ${NAMES[sport]}`,
  pillHint: 'Shows the page for another sport',
};

const ANOTHER_WORDS: Omit<AnotherSport, 'onPress'> = {
  label: 'One more sport',
  drawn: '+ One more sport',
  hint: 'Opens the sports',
  pillHint: 'Offers one more sport',
};

const onPick = jest.fn();
const onAnother = jest.fn();

/** What the page under test is handed — set before each render. */
let held: {
  readonly sports: readonly Sport[] | undefined;
  readonly sport: Sport | undefined;
  readonly another: boolean;
} = { sports: ['padel', 'tennis', 'squash'], sport: 'padel', another: false };

function Page() {
  return (
    <SportPillFrame
      sports={held.sports}
      sport={held.sport}
      onPick={onPick}
      words={WORDS}
      {...(held.another ? { another: { ...ANOTHER_WORDS, onPress: onAnother } } : {})}
      header={(pill) => <View testID="page-header">{pill ?? <Text>no pill yet</Text>}</View>}
    >
      <Text>the page</Text>
    </SportPillFrame>
  );
}

function Elsewhere() {
  return <Text>elsewhere</Text>;
}

function Root() {
  return <Stack screenOptions={{ headerShown: false }} />;
}

async function openPage(hand: Partial<typeof held> = {}) {
  held = { sports: ['padel', 'tennis', 'squash'], sport: 'padel', another: false, ...hand };
  renderRouter({ _layout: Root, index: Page, elsewhere: Elsewhere }, { initialUrl: '/' });
  await screen.findByText('the page');
}

const pill = () => within(screen.getByTestId('page-header')).getByRole('button');
const bar = () => screen.queryByTestId('sport-bar');

function unfold() {
  fireEvent.press(pill());
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
}

/** The bar's pills, left to right, as a listener meets them. */
function barOptions(): string[] {
  return within(screen.getByTestId('sport-bar'))
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

beforeEach(() => {
  jest.useFakeTimers();
  onPick.mockClear();
  onAnother.mockClear();
  watchHardwareBack();
});

afterEach(() => {
  stopWatchingHardwareBack();
  jest.useRealTimers();
});

describe('the sport pill', () => {
  it('hands the header no pill until the sports and the sport are known', async () => {
    await openPage({ sports: undefined, sport: undefined });

    expect(screen.getByText('no pill yet')).toBeTruthy();
  });

  it('is a button named in the page’s words, saying what it does', async () => {
    await openPage();

    expect(pill().props.accessibilityLabel).toBe('Shown for Padel');
    expect(pill().props.accessibilityHint).toBe(WORDS.pillHint);
    expect(bar()).toBeNull();
  });

  it('is a plain label for one sport and nothing more to offer — no choice, nothing to press', async () => {
    await openPage({ sports: ['tennis'], sport: 'tennis' });

    const header = screen.getByTestId('page-header');
    expect(within(header).queryByRole('button')).toBeNull();
    expect(within(header).getByLabelText('Shown for Tennis')).toBeTruthy();
  });

  it('opens onto the other sports in the order handed, the current one last and chosen', async () => {
    await openPage({ sports: ['padel', 'tennis', 'squash'], sport: 'tennis' });

    unfold();

    expect(barOptions()).toEqual(['Padel', 'Squash', 'Tennis']);
    expect(
      within(screen.getByTestId('sport-bar')).getByRole('button', {
        name: 'Tennis',
        selected: true,
      }),
    ).toBeTruthy();
  });

  it('reports another sport picked, and folds', async () => {
    await openPage();
    unfold();

    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
    );

    expect(onPick).toHaveBeenCalledWith('squash');
    expect(onPick).toHaveBeenCalledTimes(1);
    expect(bar()).toBeNull();
  });

  it('folds and reports nothing when the current sport is tapped', async () => {
    await openPage();
    unfold();

    fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Padel' }));

    expect(onPick).not.toHaveBeenCalled();
    expect(bar()).toBeNull();
  });

  it('folds and reports nothing on a tap anywhere else on the page', async () => {
    await openPage();
    unfold();

    fireEvent.press(screen.getByTestId('sport-filter-backdrop', { includeHiddenElements: true }));

    expect(onPick).not.toHaveBeenCalled();
    expect(bar()).toBeNull();
  });

  it('folds on Android’s back rather than leaving the page', async () => {
    await openPage();
    unfold();

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);
    expect(bar()).toBeNull();
    expect(screen).toHavePathname('/');
  });

  it('is folded again when the player comes back to the page', async () => {
    await openPage();
    unfold();

    act(() => router.push('/elsewhere'));
    await waitFor(() => expect(screen).toHavePathname('/elsewhere'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(bar()).toBeNull();
  });

  describe('with one more sport to offer', () => {
    it('opens even for one sport, saying what it offers instead', async () => {
      await openPage({ sports: ['padel'], sport: 'padel', another: true });

      expect(pill().props.accessibilityHint).toBe(ANOTHER_WORDS.pillHint);
      unfold();

      expect(barOptions()).toEqual([ANOTHER_WORDS.label, 'Padel']);
    });

    it('folds and hands the press to the page, picking nothing', async () => {
      await openPage({ another: true });
      unfold();

      fireEvent.press(
        within(screen.getByTestId('sport-bar')).getByRole('button', { name: ANOTHER_WORDS.label }),
      );

      expect(onAnother).toHaveBeenCalledTimes(1);
      expect(onPick).not.toHaveBeenCalled();
      expect(bar()).toBeNull();
    });
  });

  /** New in Rakieta's See all (#801; home rows 12, 19): *All* beside the sports, a choice like them. */
  describe('offering All', () => {
    const ALL_WORDS: SportPillWords<SportChoice> = {
      sportName: (choice) => (choice === ALL_SPORTS ? 'All' : NAMES[choice]),
      pillLabel: (choice) => `Shown for ${choice === ALL_SPORTS ? 'All' : NAMES[choice]}`,
      pillHint: 'Shows the page for another sport',
    };

    function AllPage() {
      return (
        <SportPillFrame<SportChoice>
          sports={[ALL_SPORTS, 'padel', 'tennis']}
          sport={ALL_SPORTS}
          onPick={onPick}
          words={ALL_WORDS}
          header={(shown) => <View testID="page-header">{shown}</View>}
        >
          <Text>the page</Text>
        </SportPillFrame>
      );
    }

    it('draws All with its two-toned dot, and picks a sport from it', async () => {
      renderRouter({ _layout: Root, index: AllPage }, { initialUrl: '/' });
      await screen.findByText('the page');

      expect(pill().props.accessibilityLabel).toBe('Shown for All');
      expect(screen.getByTestId('all-sports-dot', { includeHiddenElements: true })).toBeTruthy();
      unfold();

      expect(barOptions()).toEqual(['Padel', 'Tennis', 'All']);
      fireEvent.press(
        within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
      );
      expect(onPick).toHaveBeenCalledWith('tennis');
    });
  });
});
