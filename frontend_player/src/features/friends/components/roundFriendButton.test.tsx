/**
 * **The round friend button's worded twin** — on a sheet's title row ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * the Home rows screens §8.2; the words §31.9): *+ Add friend*, *Request sent*, *✓ Friends*, *Accept*,
 * the same taps as the round face. The round face is walked on Home's New in Raketa row
 * (`discovery`'s `newInRaketa.test.tsx`); no sheet draws the worded one until the comparison and vibe
 * sheets (#802, #803), so it is walked here on a page of its own, over the real friends routes' fake.
 *
 * The page reads the person's relation from the fake server and hands that read in as the button's
 * `reread`, as a surface does.
 */

import Feather from '@expo/vector-icons/Feather';
import { QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { fireEvent, renderRouter, screen, waitFor, within } from 'expo-router/testing-library';
import { Text } from 'react-native';

import { beginSession, clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { httpRequest } from '@/shared/lib/http';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { OverlayHost } from '@/shared/ui';
import {
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FRIENDS_COPY, removeTitle, roundLabel } from './friendsCopy';
import { RoundFriendButton } from './RoundFriendButton';

const KAROL = 'e0000000-0000-4000-8000-000000000901';
const RELATION_PATH = '/api/v1/test/relation';
const REQUESTS_PATH = '/api/v1/friends/requests';

let transport: Transport;
let relation: Wire['FriendRelation'];

function serve(initially: Wire['FriendRelation']) {
  relation = initially;
  transport.on('GET', RELATION_PATH, () => json({ relation }));
  transport.on('POST', REQUESTS_PATH, () => {
    relation = relation === 'ASKED_YOU' ? 'FRIEND' : 'SENT';
    return json<Wire['RelationResponse']>({ relation });
  });
  transport.on('POST', `${REQUESTS_PATH}/${KAROL}/acceptance`, () => {
    relation = 'FRIEND';
    return json<Wire['RelationResponse']>({ relation });
  });
  transport.on('DELETE', `${REQUESTS_PATH}/${KAROL}`, () => {
    relation = 'NONE';
    return noContent();
  });
  transport.on('DELETE', `/api/v1/friends/${KAROL}`, () => {
    relation = 'NONE';
    return noContent();
  });
}

/** A sheet's title row, as the comparison sheet will draw one: its read of Karol, and the button. */
function Page() {
  const read = useQuery({
    queryKey: ['test', 'relation'],
    queryFn: () =>
      httpRequest<{ relation: Wire['FriendRelation'] }>({
        method: 'GET',
        path: RELATION_PATH,
        authenticated: true,
      }),
  });
  if (read.data === undefined) return <Text>reading</Text>;
  return (
    <RoundFriendButton
      variant="worded"
      playerId={KAROL}
      nickname="karol.t"
      relation={read.data.relation}
      where={{ from: 'NEW_PLAYERS' }}
      reread={() => read.refetch()}
    />
  );
}

function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <OverlayHost>
        <Stack screenOptions={{ headerShown: false }} />
      </OverlayHost>
    </QueryClientProvider>
  );
}

async function open(initially: Wire['FriendRelation']) {
  serve(initially);
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  renderRouter({ _layout: Root, index: Page }, { initialUrl: '/' });
  return screen.findByRole('button', { name: roundLabel(initially, 'karol.t') });
}

const sheet = () => within(screen.getByTestId('bottom-sheet'));
const words = (button: ReturnType<typeof screen.getByRole>) => within(button);

beforeEach(() => {
  transport = installTransport();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

describe('the worded friend button', () => {
  it('reads + Add friend, its plus drawn, and asks at once', async () => {
    const add = await open('NONE');
    expect(words(add).getByText(FRIENDS_COPY.round.worded.NONE)).toBeTruthy();
    expect(screen.UNSAFE_getAllByType(Feather).map((mark) => mark.props.name)).toEqual(['plus']);

    fireEvent.press(add);

    expect(await screen.findByRole('button', { name: roundLabel('SENT', 'karol.t') })).toBeTruthy();
    expect(transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body)).toEqual([
      { player_id: KAROL, made_from: 'NEW_PLAYERS' },
    ]);
  });

  it('reads Request sent, and opens Cancel request', async () => {
    const sent = await open('SENT');
    expect(words(sent).getByText(FRIENDS_COPY.round.worded.SENT)).toBeTruthy();

    fireEvent.press(sent);
    fireEvent.press(sheet().getByRole('button', { name: FRIENDS_COPY.round.requestSent.act }));

    expect(await screen.findByRole('button', { name: roundLabel('NONE', 'karol.t') })).toBeTruthy();
  });

  it('reads ✓ Friends, its tick drawn, and asks before removing', async () => {
    const friends = await open('FRIEND');
    expect(words(friends).getByText(FRIENDS_COPY.round.worded.FRIEND)).toBeTruthy();
    expect(screen.UNSAFE_getAllByType(Feather).map((mark) => mark.props.name)).toEqual(['check']);

    fireEvent.press(friends);
    expect(sheet().getByText(removeTitle('karol.t'))).toBeTruthy();
    fireEvent.press(sheet().getByRole('button', { name: FRIENDS_COPY.record.remove.act }));

    expect(await screen.findByRole('button', { name: roundLabel('NONE', 'karol.t') })).toBeTruthy();
  });

  it('reads Accept, and accepts at once', async () => {
    const accept = await open('ASKED_YOU');
    expect(words(accept).getByText(FRIENDS_COPY.round.worded.ASKED_YOU)).toBeTruthy();

    fireEvent.press(accept);

    expect(
      await screen.findByRole('button', { name: roundLabel('FRIEND', 'karol.t') }),
    ).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('POST', `${REQUESTS_PATH}/${KAROL}/acceptance`)).toHaveLength(1),
    );
  });
});
