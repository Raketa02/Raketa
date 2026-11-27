/**
 * **The Games deck on a phone too short for its card** — the stage laid out at the card's least
 * height, and the scroller holding the ✕ · i · ball buttons under it
 * ([#865](https://github.com/Raketa02/Raketa/issues/865); the tab menu log §6.5).
 *
 * The real route tree, with the socket faked. Jest lays nothing out, so the suite plays the layout a
 * 320 × 568 phone would — the card's box, the stage's, then each of its blocks, by `onLayout` — and
 * asserts what the deck draws for it. The sizes themselves are `deckCardGeometry.test.ts`'s, which
 * holds them to the phones they were decided on; that the content then scrolls is the phone walk's
 * (#866), since a test renderer has no scroll.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet, type ViewStyle } from 'react-native';

import { PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { DECK_READ_AT, deckCard, groupDeck, noPath, stubGroupDeck } from '@/test-support/groupDeck';
import {
  GATE_USER,
  launchSignedIn,
  stubGate,
  stubMyGroups,
  stubPaymentMethod,
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

import { useGameIntent } from '../store/gameIntent.store';

const COPY = PROPOSALS_COPY;
const HIDDEN_TOO = { includeHiddenElements: true } as const;

interface Size {
  readonly width: number;
  readonly height: number;
}

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://rakieta.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [
    {
      sport: 'PADEL',
      rated_count: 5,
      first_rated: [
        { player_id: GATE_USER.id, nickname: 'ada' },
        { player_id: 'e0000000-0000-4000-8000-000000000002', nickname: 'Member 2' },
        { player_id: 'e0000000-0000-4000-8000-000000000003', nickname: 'Member 3' },
        { player_id: 'e0000000-0000-4000-8000-000000000004', nickname: 'Member 4' },
      ],
    },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

function rating(mu: number): Wire['RatingResponse'] {
  return {
    sport: 'PADEL',
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

/** A 320 × 568's stage once the row of tabs is gone (the tab menu log §2). */
const SE: Size = { width: 290, height: 276.4 };

/** The card's blocks as that phone lays them out at 1.0 — the decision log's §2 budget. */
const MEASURED = { ribbon: 30, vs: 12, headline: 22, gridWords: 42, court: 71 } as const;

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating(2.71)], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
  useGameIntent.setState({ intent: 'competitive' });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land on the crew's page, its Games tab reading this deck. */
async function openGames(deck: Parameters<typeof stubGroupDeck>[2]) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, deck);
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

const layout = (width: number, height: number) => ({
  nativeEvent: { layout: { x: 0, y: 0, width, height } },
});

/** The phone lays the top card out: its box, which is the stage's, and each block at its height. */
function layOutTheCard(
  proposalId: string,
  stage: Size,
  heights: Readonly<Record<keyof typeof MEASURED, number>> = MEASURED,
) {
  const card = screen.getByTestId(`game-card-${proposalId}`);
  const inCard = within(card);
  fireEvent(card, 'layout', layout(stage.width, stage.height));
  const blocks = {
    ribbon: inCard.getByRole('header'),
    vs: inCard.getByTestId('game-vs', HIDDEN_TOO),
    headline: inCard.getByTestId('game-forecast'),
    gridWords: inCard.getByTestId('overlap-words', HIDDEN_TOO),
    court: inCard.getByTestId('court-block-available'),
  };
  for (const [block, element] of Object.entries(blocks)) {
    fireEvent(element, 'layout', layout(stage.width, heights[block as keyof typeof MEASURED]));
  }
}

const stageStyle = () =>
  StyleSheet.flatten(screen.getByTestId('games-deck-stage').props.style as ViewStyle);

describe('a card the page cannot hold (#865)', () => {
  it('lays the stage out at the card’s least height, with the buttons under it in the scroller', async () => {
    const shown = deckCard();
    await openGames(groupDeck({ cards: [shown] }));
    await screen.findByTestId(`game-card-${shown.proposal_id}`);

    layOutTheCard(shown.proposal_id, SE);

    // The card at its least: its words, 177 and the hairline, and its boxes at rest — a 320's
    // tiles are already at their floor — the paddings 24, the gaps 12 + 18 + 9 + 9, the grid's
    // cells 39 and two tiles 128.5 / 1.75 = 73.43 each: 434.86 and the hairline, against 276.4.
    await waitFor(() =>
      expect(Number(stageStyle().minHeight)).toBeCloseTo(434.86 + StyleSheet.hairlineWidth, 2),
    );
    expect(Number(stageStyle().minHeight)).toBeGreaterThan(SE.height);

    // The buttons are the scroller's, under the stage — reached by a scroll, never laid over it.
    const body = within(screen.getByTestId('games-deck-body'));
    const stage = within(screen.getByTestId('games-deck-stage'));
    expect(stage.getByTestId(`game-card-${shown.proposal_id}`)).toBeTruthy();
    for (const name of [COPY.no, COPY.details, COPY.yes]) {
      expect(body.getByRole('button', { name })).toBeTruthy();
      expect(stage.queryByRole('button', { name })).toBeNull();
    }
  });

  it('holds the stage at its height after an answer, until the card coming up has measured', async () => {
    const first = deckCard();
    const second = deckCard();
    let dealt = [first, second];
    transport.on('POST', noPath(first.proposal_id), () => {
      dealt = dealt.filter((card) => card !== first);
      return noContent();
    });
    await openGames(() => groupDeck({ cards: dealt }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);
    layOutTheCard(first.proposal_id, SE);
    const atRest = 434.86 + StyleSheet.hairlineWidth;
    await waitFor(() => expect(Number(stageStyle().minHeight)).toBeCloseTo(atRest, 2));

    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(400));
    await waitFor(() =>
      expect(screen.queryByTestId(`game-card-${first.proposal_id}`, HIDDEN_TOO)).toBeNull(),
    );
    // The card that came up has not been laid out yet: the stage keeps its height, rather than
    // dropping to the page's and growing back under the player's thumb.
    expect(Number(stageStyle().minHeight)).toBeCloseTo(atRest, 2);

    // Laid out, with its court line wrapped: ten more points of words, and the stage takes them.
    layOutTheCard(second.proposal_id, SE, { ...MEASURED, court: 81 });
    await waitFor(() => expect(Number(stageStyle().minHeight)).toBeCloseTo(atRest + 10, 2));
  });

  it('lets a card that fits stand in the page’s height: its least is under the stage', async () => {
    const shown = deckCard();
    await openGames(groupDeck({ cards: [shown] }));
    await screen.findByTestId(`game-card-${shown.proposal_id}`);

    const a32: Size = { width: 354, height: 501.2 };
    layOutTheCard(shown.proposal_id, a32);
    await waitFor(() => expect(stageStyle().minHeight).toBeGreaterThan(0));
    expect(stageStyle().minHeight).toBeLessThan(a32.height);
  });
});
