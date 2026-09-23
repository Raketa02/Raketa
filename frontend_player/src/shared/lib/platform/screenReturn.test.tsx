/**
 * Coming back to a screen, as a screen can subscribe to it.
 *
 * The navigator is the real one — `expo-router/testing-library` over a two-route stack — because
 * the fact under test is *what a pop is*: a stack keeps the screen under the top one mounted, so
 * a return is a focus after a blur and never a mount. `appState.test.tsx` pins the same three
 * rules for the app's own focus; this file pins them for the navigator's.
 */

import { Stack, router } from 'expo-router';
import { act, fireEvent, renderRouter, screen, waitFor } from 'expo-router/testing-library';
import { useState } from 'react';
import { Pressable, Text } from 'react-native';

import { useOnReturn } from './screenReturn';

const run = jest.fn();

function Home() {
  useOnReturn(run);
  return <Text>home</Text>;
}

function Pushed() {
  return <Text>pushed</Text>;
}

const first = jest.fn();
const second = jest.fn();

/** A screen whose callback changes after it mounted — a press swaps it. */
function Swapping() {
  const [swapped, setSwapped] = useState(false);
  useOnReturn(swapped ? second : first);
  return (
    <>
      <Text>home</Text>
      <Pressable onPress={() => setSwapped(true)}>
        <Text>swap</Text>
      </Pressable>
    </>
  );
}

function Root() {
  return <Stack screenOptions={{ headerShown: false }} />;
}

const ROUTES = { _layout: Root, index: Home, pushed: Pushed };

beforeEach(() => {
  run.mockClear();
  first.mockClear();
  second.mockClear();
});

/** Push a screen over the one under test, then pop back to it — the walk a return is. */
async function leaveAndReturn() {
  act(() => router.push('/pushed'));
  await waitFor(() => expect(screen).toHavePathname('/pushed'));

  act(() => router.back());
  await waitFor(() => expect(screen).toHavePathname('/'));
}

describe('coming back to a screen', () => {
  it('runs nothing on the way in — a mount is not a return', async () => {
    renderRouter(ROUTES, { initialUrl: '/' });
    await screen.findByText('home');

    expect(run).not.toHaveBeenCalled();
  });

  it('runs once each time the player comes back from a screen pushed over it', async () => {
    renderRouter(ROUTES, { initialUrl: '/' });
    await screen.findByText('home');

    await leaveAndReturn();
    expect(run).toHaveBeenCalledTimes(1);

    await leaveAndReturn();
    expect(run).toHaveBeenCalledTimes(2);
  });

  it('runs nothing when the player leaves', async () => {
    renderRouter(ROUTES, { initialUrl: '/' });
    await screen.findByText('home');

    act(() => router.push('/pushed'));
    await waitFor(() => expect(screen).toHavePathname('/pushed'));

    expect(run).not.toHaveBeenCalled();
  });

  /** The subscription outlives a render, so it has to call what the screen means *now*. */
  it('runs the callback the screen holds now, not the one it mounted with', async () => {
    renderRouter({ _layout: Root, index: Swapping, pushed: Pushed }, { initialUrl: '/' });
    await screen.findByText('home');

    fireEvent.press(screen.getByText('swap'));
    await leaveAndReturn();

    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });
});
