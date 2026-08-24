/**
 * Leaving standby, driven through the real route tree and the network boundary.
 *
 * The same shape as the rest of this app's flow suites: only `fetch` is faked, so
 * the http client, error mapping, the mapper, the use-case, the hook, the cache
 * write and the screen all run for real.
 *
 * Its own file rather than a section of `seatRace.test.tsx`, because the two
 * writes are about opposite things: that one **races** for something and is
 * answered by a corrected card, and this one **gives up** something that costs
 * nothing and is answered by the card going away. It is the only act in the
 * product that removes a card from Now, and the assertions are shaped around
 * that: what left the device, what left the screen, and what did **not** happen —
 * no dialog, no confirmation, no second compose.
 */

import { Alert } from 'react-native';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  cardChanged,
  cardGone,
  emptyNow,
  matchCard,
  nowPathFor,
  standbyPath,
  standbyWrite,
  stubNow,
} from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useSportFilterStore } from '../store/sportFilter.store';

import { REGION_ID } from './NowRegions';
import { TRANSIENT_LINE_ID } from './TransientLine';
import { STANDBY_LEAVE_FAILED } from './nowCopy';

const MATCH = '7c1d0000-0000-4000-8000-000000000001';

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

const LEAVE = 'Leave standby, Sunset Padel';

let transport: Transport;
let dialogs: jest.SpyInstance;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useSportFilterStore.getState().reset();
  focusManager.setFocused(true);
  // The assertion the render tree cannot make: nothing asks her to confirm.
  dialogs = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
});

afterEach(() => {
  dialogs.mockRestore();
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/**
 * The one card a queue place puts on Now.
 *
 * `waitlisted` is the single situation only a *viewer* can be in, and the strip's
 * fourth membership is what draws it (`ADR-0091`). It holds no seat, so
 * `may_depart` is false — the two acts never appear together on one card.
 */
function queued(matchId = MATCH, clubName = 'Sunset Padel'): Wire['MatchCardResponse'] {
  return matchCard({
    matchId,
    situation: 'waitlisted',
    clubName,
    act: 'leaveStandby',
    mayDepart: false,
  });
}

/** A screen holding one queue place and nothing else. */
function nowQueued(...cards: Wire['MatchCardResponse'][]): Wire['NowResponse'] {
  return { ...emptyNow(), your_matches: { stamp: 1, cards } };
}

async function launchOnNow(body: Wire['NowResponse'] = nowQueued(queued())) {
  stubGate(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByTestId(REGION_ID.yourMatches);
}

/** Answer the tap with one body, and hand back how many taps reached the socket. */
function standbyAnswers(body: Wire['StandbyWriteResponse'], matchId = MATCH): () => number {
  transport.on('DELETE', standbyPath(matchId), () => json(body));
  return () => transport.requestsTo('DELETE', standbyPath(matchId)).length;
}

const composes = () => transport.requestsTo('GET', nowPathFor('all')).length;

// ---------------------------------------------------------------------------
// What leaves the device
// ---------------------------------------------------------------------------

describe('the tap', () => {
  it('deletes the place with nothing but the address', async () => {
    // No body: there is nothing to send but which queue. No sport parameter
    // either, unlike the seat write — that one carries the chip because its answer
    // is two whole regions composed under it, and this one answers a card.
    await launchOnNow();
    const taps = standbyAnswers(standbyWrite(cardGone(MATCH)));

    fireEvent.press(screen.getByLabelText(LEAVE));
    await waitFor(() => expect(taps()).toBe(1));

    const sent = transport.requestsTo('DELETE', standbyPath(MATCH))[0];

    expect(sent?.body).toBeUndefined();
    expect(sent?.headers.Authorization).toMatch(/^Bearer /);
    expect(sent?.path).not.toMatch(/sport=/);
  });

  it('goes on the first press, with nothing asked in between', async () => {
    // `ADR-0087`: *"a confirmation here would imply a cost the model says does not
    // exist"* — nothing is lost, no money moves, and there is no place to forfeit.
    // One press, one command, and no dialog at any point.
    await launchOnNow();
    const taps = standbyAnswers(standbyWrite(cardGone(MATCH)));

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() => expect(taps()).toBe(1));
    expect(dialogs).not.toHaveBeenCalled();
  });

  it('is not sent twice while the first one is in flight', async () => {
    // There is no idempotency key, deliberately — the route is idempotent by its
    // own nature. What must still not happen is the app sending two commands for
    // one press of a thumb, and the button's own busy state is what stops it.
    await launchOnNow();

    let answer: (() => void) | undefined;
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('DELETE', standbyPath(MATCH), async () => {
      await held;
      return json(standbyWrite(cardGone(MATCH)));
    });

    fireEvent.press(screen.getByLabelText(LEAVE));
    await waitFor(() =>
      expect(screen.getByLabelText(LEAVE).props.accessibilityState.busy).toBe(true),
    );

    fireEvent.press(screen.getByLabelText(LEAVE));
    fireEvent.press(screen.getByLabelText(LEAVE));

    await act(async () => {
      answer?.();
      await held;
    });

    expect(transport.requestsTo('DELETE', standbyPath(MATCH))).toHaveLength(1);
  });

  it('blocks the card she pressed and no other', async () => {
    // The busy state names a match, never *a write is running*. A screen holding
    // three queue places must not go dead because she left one of them, and the
    // failure there is invisible from a strip holding a single card.
    const other = '7c1d0000-0000-4000-8000-000000000002';
    await launchOnNow(nowQueued(queued(), queued(other, 'Hala Wisła')));

    let answer: (() => void) | undefined;
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('DELETE', standbyPath(MATCH), async () => {
      await held;
      return json(standbyWrite(cardGone(MATCH)));
    });

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() =>
      expect(screen.getByLabelText(LEAVE).props.accessibilityState.busy).toBe(true),
    );
    expect(screen.getByLabelText('Leave standby, Hala Wisła').props.accessibilityState.busy).toBe(
      false,
    );

    await act(async () => {
      answer?.();
      await held;
    });
  });

  it('is never retried on the app’s own initiative', async () => {
    // The route being safe to repeat is not a licence to repeat it for her. A
    // second delete she did not ask for is still a command she did not give.
    await launchOnNow();
    transport.on('DELETE', standbyPath(MATCH), () => errorResponse(500, 'internal_error'));

    fireEvent.press(screen.getByLabelText(LEAVE));
    await screen.findByTestId(TRANSIENT_LINE_ID);

    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    expect(transport.requestsTo('DELETE', standbyPath(MATCH))).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// What leaves the screen
// ---------------------------------------------------------------------------

describe('a queue place she has left', () => {
  it('takes its card off the strip and asks Now for nothing', async () => {
    // The one act in the product that removes a card (`ADR-0091`), and the answer
    // is a **cache write** rather than a fetch (`ADR-0074`): the server composed
    // this at the instant of the write, so asking for the whole screen again would
    // pay the full funnel for something already in hand.
    await launchOnNow();
    standbyAnswers(standbyWrite(cardGone(MATCH)));
    const before = composes();

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() => expect(screen.queryByLabelText(LEAVE)).toBeNull());
    // The strip is present and empty, saying so in its own words.
    expect(screen.getByText('No matches booked')).toBeTruthy();
    expect(composes()).toBe(before);
  });

  it('leaves the queue places she did not tap exactly where they were', async () => {
    // Removing one card is not a licence to reorder the rest (`ADR-0032`), and it
    // is emphatically not a licence to empty the region: a player queued for three
    // matches who leaves one still holds two.
    const other = '7c1d0000-0000-4000-8000-000000000002';
    await launchOnNow(nowQueued(queued(), queued(other, 'Hala Wisła')));
    standbyAnswers(standbyWrite(cardGone(MATCH)));

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() => expect(screen.queryByLabelText(LEAVE)).toBeNull());
    expect(screen.getByLabelText('Leave standby, Hala Wisła')).toBeTruthy();
  });

  it('goes from every sport’s screen and not only the chip she was holding', async () => {
    // A card is a card whatever chip is held, which is why this hook takes no sport
    // where the seat write does. Correcting only the screen she happens to be
    // looking at leaves the other to be discovered later as a card offering an act
    // that is gone — and this one offers to leave a queue she is not on.
    await launchOnNow();
    stubNow(transport, nowQueued(queued()), 'PADEL');
    fireEvent.press(screen.getByRole('radio', { name: 'Padel' }));
    await screen.findByLabelText(LEAVE);

    standbyAnswers(standbyWrite(cardGone(MATCH)));
    fireEvent.press(screen.getByLabelText(LEAVE));
    await waitFor(() => expect(screen.queryByLabelText(LEAVE)).toBeNull());

    fireEvent.press(screen.getByRole('radio', { name: 'All' }));

    // The cached `all` screen, corrected without being asked for again.
    await waitFor(() => expect(screen.getByText('No matches booked')).toBeTruthy());
    expect(screen.queryByLabelText(LEAVE)).toBeNull();
  });

  it('says nothing at all', async () => {
    // The card leaving *is* the acknowledgement. A line saying *you have left the
    // queue* over a screen that no longer shows the queue would be the product
    // telling her something she is already looking at.
    await launchOnNow();
    standbyAnswers(standbyWrite(cardGone(MATCH)));

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() => expect(screen.queryByLabelText(LEAVE)).toBeNull());
    expect(screen.queryByTestId(TRANSIENT_LINE_ID)).toBeNull();
    expect(dialogs).not.toHaveBeenCalled();
  });

  it('is replaced rather than removed when the server says the card changed', async () => {
    // The negative control for every assertion above, and the rule underneath them:
    // the two forms are told apart by the wire's **discriminator**, never by this
    // act's usual shape. No composer answers this write with a card today; a client
    // that assumed *gone* would drop a card the server had just said was still hers.
    await launchOnNow();
    standbyAnswers(standbyWrite(cardChanged(matchCard({ matchId: MATCH, situation: 'full' }))));

    fireEvent.press(screen.getByLabelText(LEAVE));

    await waitFor(() => expect(screen.queryByLabelText(LEAVE)).toBeNull());
    expect(screen.getByTestId(REGION_ID.yourMatches)).toBeTruthy();
    expect(screen.queryByText('No matches booked')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// A tap that did not go through
// ---------------------------------------------------------------------------

describe('a tap the server never answered', () => {
  it('says one plain line and keeps the card exactly as it was', async () => {
    // Nothing can refuse this act, so a failure is a tap that never landed — and
    // the card is still right. A dialog would stop her to announce that nothing
    // happened over a screen that already says so.
    await launchOnNow();
    transport.on('DELETE', standbyPath(MATCH), () => errorResponse(500, 'internal_error'));

    fireEvent.press(screen.getByLabelText(LEAVE));

    expect(await screen.findByText(STANDBY_LEAVE_FAILED)).toBeTruthy();
    expect(screen.getByLabelText(LEAVE)).toBeTruthy();
    expect(dialogs).not.toHaveBeenCalled();
  });

  it('leaves the button pressable again', async () => {
    // The busy state is the write's, not a latch: a failed tap she can repeat is
    // the whole of the recovery here, because there is nothing else to do about it.
    await launchOnNow();
    transport.on('DELETE', standbyPath(MATCH), () => errorResponse(500, 'internal_error'));

    fireEvent.press(screen.getByLabelText(LEAVE));
    await screen.findByText(STANDBY_LEAVE_FAILED);

    await waitFor(() =>
      expect(screen.getByLabelText(LEAVE).props.accessibilityState.busy).toBe(false),
    );
  });
});
