/**
 * **A For-fun game's details open on the Social vibe card** ([#840](https://github.com/Raketa02/Raketa/issues/840);
 * for fun 7, which leads over 5 and 6; ADR-0207 §6) — walked the way a player opens them: the real
 * route tree, the real shell, and only `fetch` faked.
 *
 * Before saying yes, Ola reads how much the whole table shares — the deck card's own %, its word and
 * the bar — and then who shares **her** tags: the faces across, her first, then the others as the
 * tiles stand; her tags down the side, each with a dot under everybody who carries it. She reads
 * across *🍻 Stays for a drink* and sees kuba.w stays for one too. A row somebody else shares is on a
 * pale volt band; a row only she has is grey. **No forecast, ever**, on For fun.
 *
 * The screen is launched at its route, as `competitiveDetails.test.tsx` launches it: what opens it —
 * the card, its **i**, a *You’re in* row — is `groups/components/groupGames.test.tsx`'s.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet, type TextStyle, type ViewStyle } from 'react-native';

import { SAVE, TAGS_TITLE, tagsLine } from '@/features/player_profile/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, SOCIAL_VIBE_CARD, theme } from '@/shared/ui';
import {
  BALANCE_FORECAST,
  COUNTED_GAME_SENTENCE,
  LOSE_TILE,
  WIN_TILE,
} from '@/shared/vocabulary/forecastPresentation';
import {
  ANIA,
  deckCard,
  DETAILS_CARD,
  DETAILS_SCREEN,
  KUBA,
  proposalDetails,
  proposalPath,
  stubProposal,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';
import {
  launchSignedIn,
  PROFILE_OPTIONS_SERVED,
  PROFILE_SURFACE_SERVED,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { inOrder, partOf } from '@/test-support/readingOrder';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { proposalKeys } from '../hooks/proposalKeys';

/** The crew the details' game is dealt in — `proposalDetails`' own pool. */
const GROUP = 'a0000000-0000-4000-8000-000000000005';

const HIDDEN = { includeHiddenElements: true } as const;

const YOU = youTile().player_id;
const KUBA_ID = KUBA().player_id;
const ZOFIA_ID = ZOFIA().player_id;
const ANIA_ID = ANIA().player_id;

/**
 * Mock 7's table: you and kuba.w against zofia.b and ania.k, who are both In — so theirs is the top
 * row of tiles, and the columns read You, zofia.b, ania.k, kuba.w.
 */
const TABLE: Wire['DeckSidesSchema'] = {
  yours: [youTile(), KUBA()],
  theirs: [ZOFIA({ is_in: true }), ANIA({ is_in: true })],
};

/** Your six tags in the vocabulary's order, each carried by you first, then the tiles' order. */
const VIBE: Wire['DetailsVibeSchema'] = {
  pct: 67,
  rows: [
    { tag: 'STAYS_FOR_A_DRINK', carried_by: [YOU, KUBA_ID] },
    { tag: 'GENEROUS_ON_LINE_CALLS', carried_by: [YOU, ZOFIA_ID] },
    { tag: 'HERE_TO_IMPROVE', carried_by: [YOU, ANIA_ID] },
    { tag: 'HERE_TO_COMPETE', carried_by: [YOU, KUBA_ID] },
    { tag: 'HERE_FOR_THE_EXERCISE', carried_by: [YOU, ANIA_ID] },
    { tag: 'HERE_FOR_A_REGULAR_GAME', carried_by: [YOU] },
  ],
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A For-fun card dealt on this table, and its details with the vibe served. */
function forFun(
  extra: Partial<Wire['ProposalDetailsResponse']> = {},
  card: Wire['DeckCardSchema'] = deckCard({
    kind: 'FOR_FUN',
    forecast: null,
    vibe: { pct: VIBE.pct },
    in_count: 2,
    sides: TABLE,
  }),
): Wire['ProposalDetailsResponse'] {
  return proposalDetails(card, { vibe: VIBE, ...extra });
}

/** In at the details, as the deck pushes them: the group, the game, the sport and the kind. */
async function openDetails(
  read: Wire['ProposalDetailsResponse'] | (() => Wire['ProposalDetailsResponse']),
  { sport = 'padel' }: { readonly sport?: string } = {},
) {
  const id = typeof read === 'function' ? read().proposal_id : read.proposal_id;
  stubProposal(transport, id, read);
  await launchSignedIn(`/play/group/${GROUP}/game/${id}?sport=${sport}&kind=forFun`);
  await screen.findByTestId(DETAILS_CARD);
}

const vibeCard = () => within(screen.getByTestId(SOCIAL_VIBE_CARD));
const columns = () =>
  screen
    .getAllByTestId('social-vibe-column', HIDDEN)
    .map((column) => within(column).getByText(/.+/, HIDDEN));
const rows = () =>
  screen.getAllByTestId('social-vibe-row').map((row) => String(row.props.accessibilityLabel));
const row = (name: string) => screen.getByLabelText(name);
/** Which columns of a row carry a dot — one cell per column, in the columns' order. */
const dotted = (name: string) =>
  within(row(name))
    .getAllByTestId('social-vibe-cell', HIDDEN)
    .map((cell) => within(cell).queryByTestId('social-vibe-dot', HIDDEN) !== null);
const viewStyle = (node: { props: { style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as ViewStyle);
const textStyle = (node: { props: { style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as TextStyle);

describe('the For-fun details’ top card', () => {
  it('opens on SOCIAL VIBE, the deck card’s %, its word and the bar', async () => {
    await openDetails(forFun());

    expect(vibeCard().getByRole('header', { name: 'Social vibe' })).toBeTruthy();
    const reading = screen.getByLabelText('Social vibe, 67 percent, Good vibe');
    expect(within(reading).getByText('67%')).toBeTruthy();
    expect(within(reading).getByText('Good vibe')).toBeTruthy();
    expect(textStyle(within(reading).getByText('67%')).color).toBe(theme.color.oliveInk);
    expect(viewStyle(screen.getByTestId('social-vibe-card-fill', HIDDEN)).width).toBe('67%');
  });

  /** For fun 5–6: the vibe card first, then the dark game card, unchanged. */
  it('is read before the game card', async () => {
    await openDetails(forFun());

    const order = [
      'header:Social vibe',
      '67%',
      'Good vibe',
      '🍻 Stays for a drink',
      '🔁 Here for a regular game',
      'header:Filling · 2 of 4 in',
    ];
    expect(inOrder(partOf(screen.toJSON(), DETAILS_SCREEN), order)).toEqual(order);
    expect(within(screen.getByTestId(DETAILS_CARD)).queryByText('Good vibe')).toBeNull();
  });

  /** Mock 7 over 5 and 6: You first, then the tiles' order — the side In on top, kuba.w last. */
  it('heads its columns with You, then the others as the tiles stand', async () => {
    await openDetails(forFun());

    expect(columns().map((name) => name.props.children)).toEqual([
      'You',
      'zofia.b',
      'ania.k',
      'kuba.w',
    ]);
  });

  it('shortens a long nickname with an ellipsis, on one line', async () => {
    const long = 'jakub.wisniewski-kowalczyk';
    await openDetails(
      forFun(
        {},
        deckCard({
          kind: 'FOR_FUN',
          forecast: null,
          vibe: { pct: VIBE.pct },
          in_count: 2,
          sides: { ...TABLE, yours: [youTile(), KUBA({ nickname: long })] },
        }),
      ),
    );

    const name = columns()[3]!;
    expect(name.props.children).toBe(long);
    expect(name.props.numberOfLines).toBe(1);
    expect(name.props.ellipsizeMode).toBe('tail');
  });

  it('draws your tags down the side, in the read’s order, each with its emoji', async () => {
    await openDetails(forFun());

    expect(rows()).toEqual([
      'Stays for a drink: you, kuba.w',
      'Generous on line calls: you, zofia.b',
      'Here to improve: you, ania.k',
      'Here to compete: you, kuba.w',
      'Here for the exercise: you, ania.k',
      'Here for a regular game: you',
    ]);
    for (const [spoken, drawn] of [
      ['Stays for a drink: you, kuba.w', '🍻 Stays for a drink'],
      ['Generous on line calls: you, zofia.b', '🤝 Generous on line calls'],
      ['Here to improve: you, ania.k', '📈 Here to improve'],
      ['Here to compete: you, kuba.w', '🔥 Here to compete'],
      ['Here for the exercise: you, ania.k', '💪 Here for the exercise'],
      ['Here for a regular game: you', '🔁 Here for a regular game'],
    ] as const) {
      expect(within(row(spoken)).getByText(drawn)).toBeTruthy();
    }
  });

  /** Ola reads across *Stays for a drink*: a dot under her, and one under kuba.w. */
  it('puts a dot under every carrier — your column on every row', async () => {
    await openDetails(forFun());

    expect(dotted('Stays for a drink: you, kuba.w')).toEqual([true, false, false, true]);
    expect(dotted('Generous on line calls: you, zofia.b')).toEqual([true, true, false, false]);
    expect(dotted('Here to improve: you, ania.k')).toEqual([true, false, true, false]);
    expect(dotted('Here for a regular game: you')).toEqual([true, false, false, false]);
    for (const spoken of rows()) expect(dotted(spoken)[0]).toBe(true);
  });

  it('bands a row somebody else shares pale volt, and greys a row only you have', async () => {
    await openDetails(forFun());

    const shared = row('Stays for a drink: you, kuba.w');
    expect(viewStyle(shared).backgroundColor).toBe(theme.color.voltPale);
    expect(textStyle(within(shared).getByText('🍻 Stays for a drink')).color).toBe(theme.color.ink);
    for (const dot of within(shared).getAllByTestId('social-vibe-dot', HIDDEN)) {
      expect(viewStyle(dot).backgroundColor).toBe(theme.color.oliveInk);
    }

    const yours = row('Here for a regular game: you');
    expect(viewStyle(yours).backgroundColor).toBeUndefined();
    expect(textStyle(within(yours).getByText('🔁 Here for a regular game')).color).toBe(
      theme.color.vibeGrey,
    );
    const [dot] = within(yours).getAllByTestId('social-vibe-dot', HIDDEN);
    expect(viewStyle(dot!).backgroundColor).toBe(theme.color.line);
  });

  it('draws 💘 like any other row', async () => {
    await openDetails(
      forFun({
        vibe: { pct: 50, rows: [{ tag: 'OPEN_TO_MEET_SOMEONE', carried_by: [YOU, ZOFIA_ID] }] },
      }),
    );

    expect(
      within(row('Open to meet someone: you, zofia.b')).getByText('💘 Open to meet someone'),
    ).toBeTruthy();
  });

  /**
   * The forecast's split row says who partners whom; the vibe card does not, so on For fun the vs
   * line is spoken instead — the top row first, as on the deck card (#838).
   */
  it('speaks who partners whom, since the vibe card does not', async () => {
    await openDetails(forFun());

    expect(screen.getByLabelText('zofia.b and ania.k against you and kuba.w')).toBeTruthy();
  });

  /** The grid is static (ADR-0207 §6): nothing in the card answers a press. */
  it('has no taps of its own', async () => {
    await openDetails(forFun());

    expect(vibeCard().queryAllByRole('button', HIDDEN)).toHaveLength(0);
  });

  it('draws two columns on a singles court', async () => {
    const singles = deckCard({
      kind: 'FOR_FUN',
      forecast: null,
      vibe: { pct: 50 },
      sides: { yours: [youTile()], theirs: [ANIA()] },
    });
    await openDetails(
      forFun(
        {
          sport: 'TENNIS',
          seats: 2,
          vibe: {
            pct: 50,
            rows: [
              { tag: 'PLAYS_TO_WIN', carried_by: [YOU, ANIA_ID] },
              { tag: 'SHARES_A_LIFT', carried_by: [YOU] },
            ],
          },
        },
        singles,
      ),
      { sport: 'tennis' },
    );

    expect(columns().map((name) => name.props.children)).toEqual(['You', 'ania.k']);
    expect(dotted('Plays to win: you, ania.k')).toEqual([true, true]);
    expect(dotted('Shares a lift: you')).toEqual([true, false]);
  });
});

describe('no forecast on For fun', () => {
  /** ADR-0207 §5: a forecast or stakes a read sent anyway are not drawn — the kind decides. */
  it('draws the Social vibe card and never the forecast or the stakes', async () => {
    await openDetails(
      forFun({
        forecast: { pct: 73, provisional: false, your_side: 2.65, their_side: 2.74, gap: -0.09 },
        at_stake: { win_delta: 0.08, loss_delta: -0.07 },
      }),
    );

    expect(screen.getByTestId(SOCIAL_VIBE_CARD)).toBeTruthy();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText('73%')).toBeNull();
    expect(screen.queryByText(COUNTED_GAME_SENTENCE)).toBeNull();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
    expect(screen.queryByText(LOSE_TILE)).toBeNull();
  });

  /** Fewer than two named, or nobody holding a tag that counts: the read sends no vibe. */
  it('draws nothing above the game card when the read sends no vibe', async () => {
    await openDetails(forFun({ vibe: null }));

    expect(screen.queryByTestId(SOCIAL_VIBE_CARD)).toBeNull();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText(/^\d+%$/)).toBeNull();
  });
});

/**
 * **Live** (ADR-0207 §2): the vibe is worked out on every read from everybody's tags now. Ola adds
 * 🔥 *Here to compete* in the You tab; the deck and the details she left open are marked stale, and
 * back on Play the details show her new row and the new number.
 */
describe('a tag edit', () => {
  const TAGS_PATH = '/api/v1/players/me/social-tags';
  const HELD = PROFILE_SURFACE_SERVED.social_tags;
  const MAXIMUM = PROFILE_OPTIONS_SERVED.social_tag_selection.maximum_tags;
  const OTHERS: Readonly<Partial<Record<Wire['SocialTag'], readonly string[]>>> = {
    STAYS_FOR_A_DRINK: [KUBA_ID],
    HERE_TO_IMPROVE: [ANIA_ID],
    HERE_TO_COMPETE: [KUBA_ID],
  };

  /** The server's read for the tags Ola holds now: her rows, and a % that moves with them. */
  const vibeOf = (tags: readonly Wire['SocialTag'][]): Wire['DetailsVibeSchema'] => ({
    pct: tags.length === HELD.length ? 40 : 72,
    rows: tags.map((tag) => ({ tag, carried_by: [YOU, ...(OTHERS[tag] ?? [])] })),
  });

  it('marks the deck and the details stale, and reopened they show the new rows and number', async () => {
    let held: readonly Wire['SocialTag'][] = HELD;
    stubProfileSurface(transport);
    stubProfileOptions(transport);
    stubOwnRecord(transport);
    transport.on('PUT', TAGS_PATH, (request) => {
      // The request spells a tag as a string; this fake serves back what it was sent.
      held = (request.body as Wire['ChangeSocialTagsRequest']).social_tags as Wire['SocialTag'][];
      return json<Wire['SocialTagsResponse']>({ social_tags: [...held] });
    });
    const shown = forFun();
    await openDetails(() => ({ ...shown, vibe: vibeOf(held) }));

    expect(screen.getByLabelText('Social vibe, 40 percent, Some common ground')).toBeTruthy();
    expect(screen.queryByLabelText('Here to compete: you, kuba.w')).toBeNull();
    const details = proposalKeys.proposal(shown.proposal_id);
    const read = queryClient.getQueryData(details);

    // To You, and its Tags: Ola adds Here to compete.
    fireEvent.press(screen.getByRole('tab', { name: 'You' }));
    fireEvent.press(
      await screen.findByLabelText(doorRowLabel(TAGS_TITLE, tagsLine(HELD, MAXIMUM))),
    );
    await screen.findByLabelText('Plays to win');
    fireEvent.press(screen.getByLabelText('Here to compete'));

    // What a phone holds a minute later: the details read, and the For-fun deck she came from. The
    // harness runs every pending timer on a navigation, the five-minute gc among them, so both are
    // put back as they were — a real phone has not collected them yet.
    const deck = proposalKeys.deck(GROUP, 'padel', 'forFun');
    queryClient.setQueryData(details, read);
    queryClient.setQueryData(deck, { held: true });
    fireEvent.press(screen.getByLabelText(SAVE));

    await waitFor(() => expect(transport.requestsTo('PUT', TAGS_PATH)).toHaveLength(1));
    await waitFor(() => expect(queryClient.getQueryState(deck)?.isInvalidated).toBe(true));
    expect(queryClient.getQueryState(details)?.isInvalidated).toBe(true);

    // Back on Play, she opens the game again: read again, her new row and the new number.
    fireEvent.press(screen.getByRole('tab', { name: 'Play' }));
    act(() =>
      router.push({
        pathname: '/play/group/[groupId]/game/[proposalId]',
        params: { groupId: GROUP, proposalId: shown.proposal_id, sport: 'padel', kind: 'forFun' },
      }),
    );
    expect(await screen.findByLabelText('Here to compete: you, kuba.w')).toBeTruthy();
    expect(transport.requestsTo('GET', proposalPath(shown.proposal_id))).toHaveLength(2);
    expect(screen.getByLabelText('Social vibe, 72 percent, Great vibe')).toBeTruthy();
    expect(dotted('Here to compete: you, kuba.w')).toEqual([true, false, false, true]);
  });
});
