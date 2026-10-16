/**
 * **LIVE YESES reads again when the player comes back to it** — a game that filled because somebody
 * else's yes was the last one leaves the list on the player's next return, not only on their own
 * action or a notice's re-read.
 *
 * The navigator is the real one (`expo-router/testing-library`), because the fact under test is what
 * a pop is: the screen under a pushed one stays mounted, so a return is a focus after a blur, never
 * a mount. The read is the use case's, mocked, so the count is the requests the list made.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack, router } from 'expo-router';
import { act, renderRouter, screen, waitFor } from 'expo-router/testing-library';
import { Text } from 'react-native';

import { readLiveYeses } from '../use-cases/liveYeses';

import { LiveYeses } from './LiveYeses';

jest.mock('../use-cases/liveYeses', () => ({
  readLiveYeses: jest.fn(),
  readPaymentsToConfirm: jest.fn(),
}));

const read = readLiveYeses as jest.MockedFunction<typeof readLiveYeses>;

const client = new QueryClient();

function Payments() {
  return (
    <QueryClientProvider client={client}>
      <LiveYeses />
      <Text>payments</Text>
    </QueryClientProvider>
  );
}

function Pushed() {
  return <Text>pushed</Text>;
}

function Root() {
  return <Stack screenOptions={{ headerShown: false }} />;
}

const ROUTES = { _layout: Root, index: Payments, pushed: Pushed };

beforeEach(() => {
  read.mockReset();
  read.mockResolvedValue({ yeses: [] });
});

it('reads the live yeses again when the player returns to them, and not on the way in', async () => {
  renderRouter(ROUTES, { initialUrl: '/' });
  await waitFor(() => expect(read).toHaveBeenCalledTimes(1));

  act(() => router.push('/pushed'));
  await waitFor(() => expect(screen).toHavePathname('/pushed'));
  act(() => router.back());
  await waitFor(() => expect(screen).toHavePathname('/'));

  await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
});
