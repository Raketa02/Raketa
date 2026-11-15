/**
 * **The sport pill on a Home row** ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home
 * rows screens §7.3; home rows 27) — the deck's pill (#774) on a row's heading line, beside the row's
 * link, and the bar it opens onto lying over the row. Top 10 draws it; its router suite walks the
 * picks end to end. `SportPill.test.tsx` holds the bar's unfold.
 *
 * The navigator is real, because leaving the screen is one of the things that folds the bar.
 */

import { Stack, router } from 'expo-router';
import { act, fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet, Text, type ViewStyle } from 'react-native';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import type { Sport } from '@/shared/vocabulary/sport';

import { HomeRow } from './HomeRow';
import { RowSportPill } from './RowSportPill';
import type { SportPillWords } from './SportPillFrame';
import { theme } from './theme';

const NAMES: Readonly<Record<Sport, string>> = {
  padel: 'Padel',
  tennis: 'Tennis',
  squash: 'Squash',
  badminton: 'Badminton',
};

const WORDS: SportPillWords = {
  sportName: (sport) => NAMES[sport],
  pillLabel: (sport) => `Sport: ${NAMES[sport]}`,
  pillHint: 'Shows the row for another sport',
};

const onPick = jest.fn();

let held: { readonly sports: readonly Sport[] | undefined; readonly sport: Sport | undefined } = {
  sports: ['padel', 'tennis', 'squash', 'badminton'],
  sport: 'padel',
};

function Screen() {
  return (
    <RowSportPill sports={held.sports} sport={held.sport} onPick={onPick} words={WORDS}>
      {(pill, over) => (
        <HomeRow
          heading="Top 10"
          control={pill}
          over={over}
          link={{ words: 'Rankings', label: 'Rankings', onPress: jest.fn() }}
          testID="row"
        >
          <Text>the cards</Text>
        </HomeRow>
      )}
    </RowSportPill>
  );
}

function Elsewhere() {
  return <Text>elsewhere</Text>;
}

function Root() {
  return <Stack screenOptions={{ headerShown: false }} />;
}

async function openRow(hand: Partial<typeof held> = {}) {
  held = { sports: ['padel', 'tennis', 'squash', 'badminton'], sport: 'padel', ...hand };
  renderRouter({ _layout: Root, index: Screen, elsewhere: Elsewhere }, { initialUrl: '/' });
  await screen.findByText('the cards');
}

const pill = () => screen.getByRole('button', { name: 'Sport: Padel' });
const bar = () => screen.queryByTestId('sport-bar');

function unfold() {
  fireEvent.press(pill());
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
}

function barOptions(): string[] {
  return within(screen.getByTestId('sport-bar'))
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

beforeEach(() => {
  jest.useFakeTimers();
  onPick.mockClear();
  watchHardwareBack();
});

afterEach(() => {
  stopWatchingHardwareBack();
  jest.useRealTimers();
});

describe('the sport pill on a row', () => {
  it('hands the row no pill until the sports and the sport are known', async () => {
    await openRow({ sport: undefined });

    expect(screen.queryByRole('button', { name: /^Sport:/ })).toBeNull();
    expect(screen.getByRole('link', { name: 'Rankings' })).toBeTruthy();
  });

  it('stands on the heading’s line, a button named in the row’s words', async () => {
    await openRow();

    expect(pill().props.accessibilityHint).toBe('Shows the row for another sport');
    expect(bar()).toBeNull();
  });

  it('opens over the row onto the other sports, the current one last', async () => {
    await openRow();
    unfold();

    expect(barOptions()).toEqual(['Tennis', 'Squash', 'Badminton', 'Padel']);
  });

  it('reports another sport picked, and folds', async () => {
    await openRow();
    unfold();

    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
    );

    expect(onPick).toHaveBeenCalledWith('squash');
    expect(bar()).toBeNull();
  });

  it('folds and reports nothing when the current sport is tapped', async () => {
    await openRow();
    unfold();

    fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Padel' }));

    expect(onPick).not.toHaveBeenCalled();
    expect(bar()).toBeNull();
  });

  it('folds and reports nothing on a tap anywhere else on the row', async () => {
    await openRow();
    unfold();

    fireEvent.press(screen.getByTestId('sport-filter-backdrop', { includeHiddenElements: true }));

    expect(onPick).not.toHaveBeenCalled();
    expect(bar()).toBeNull();
  });

  it('folds on Android’s back rather than leaving the screen', async () => {
    await openRow();
    unfold();

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);
    expect(bar()).toBeNull();
    expect(screen).toHavePathname('/');
  });

  it('is folded again when the player comes back to the screen', async () => {
    await openRow();
    unfold();

    act(() => router.push('/elsewhere'));
    await waitFor(() => expect(screen).toHavePathname('/elsewhere'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(bar()).toBeNull();
  });

  /** Home rows 27: the current sport sits at the bar's right end, exactly where the pill stood. */
  it('ends the bar where the pill ends, on the pill’s own line', async () => {
    await openRow();
    fireEvent(screen.getByTestId('row-sport-pill'), 'layout', {
      nativeEvent: { layout: { x: 200, y: 4, width: 90, height: 30 } },
    });
    unfold();

    const slot = StyleSheet.flatten(
      screen.getByTestId('row-sport-bar-slot').props.style as ViewStyle,
    );
    expect(slot).toMatchObject({
      position: 'absolute',
      left: 0,
      top: 4,
      height: 30,
      width: 200 + 90 + theme.size.groupPage.filterPad,
      alignItems: 'flex-end',
      justifyContent: 'center',
    });
  });
});
