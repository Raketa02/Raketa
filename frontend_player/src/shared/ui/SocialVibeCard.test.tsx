import { render, screen, within } from '@testing-library/react-native';
import { StyleSheet, type TextStyle, type ViewStyle } from 'react-native';

import type { SocialVibeGrid } from '@/shared/vocabulary/socialVibeGrid';

import { SOCIAL_VIBE_CARD_FILL, SOCIAL_VIBE_CARD_FIGURE, SocialVibeCard } from './SocialVibeCard';
import { theme } from './theme';

const HIDDEN = { includeHiddenElements: true } as const;

const viewStyle = (node: { props: { style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as ViewStyle);
const textStyle = (node: { props: { style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as TextStyle);

/** Mock 7's table — you, Magda and Filip (In, so their row is the tiles' top one), then Kuba. */
const GRID: SocialVibeGrid = {
  pct: 67,
  columns: [
    { playerId: 'me', isYou: true, name: 'ola.k' },
    { playerId: 'magda', isYou: false, name: 'magda.p', photoUrl: 'https://photo.test/magda' },
    { playerId: 'filip', isYou: false, name: 'filip.n' },
    { playerId: 'kuba', isYou: false, name: 'kuba.w' },
  ],
  rows: [
    { tag: 'STAYS_FOR_A_DRINK', dots: [true, false, false, true], shared: true },
    { tag: 'HERE_TO_IMPROVE', dots: [true, false, true, false], shared: true },
    { tag: 'HERE_FOR_A_REGULAR_GAME', dots: [true, false, false, false], shared: false },
  ],
};

const row = (name: string) => screen.getByLabelText(name);
const dotsIn = (name: string) => within(row(name)).queryAllByTestId('social-vibe-dot', HIDDEN);

describe('SocialVibeCard (7.39)', () => {
  it('opens on the eyebrow, then the % and its word as one reading', () => {
    render(<SocialVibeCard grid={GRID} />);

    expect(screen.getByRole('header', { name: 'Social vibe' })).toBeTruthy();
    const reading = screen.getByLabelText('Social vibe, 67 percent, Good vibe');
    expect(within(reading).getByText('67%')).toBeTruthy();
    expect(within(reading).getByText('Good vibe')).toBeTruthy();
  });

  it('fills the bar below to the same value, 0 to 100, and draws no fill at nought', () => {
    render(<SocialVibeCard grid={GRID} />);
    expect(viewStyle(screen.getByTestId('social-vibe-card-fill', HIDDEN)).width).toBe('67%');

    screen.rerender(<SocialVibeCard grid={{ ...GRID, pct: 0 }} />);
    expect(screen.queryByTestId('social-vibe-card-fill', HIDDEN)).toBeNull();
    expect(screen.getByLabelText('Social vibe, 0 percent, Fresh mix')).toBeTruthy();
  });

  /** ADR-0207 §8: olive ink on paper for the two upper bands, dimmed, then grey; the fill one hue family. */
  it.each([
    [82, theme.color.oliveInk, theme.color.volt],
    [60, theme.color.oliveInk, theme.color.volt],
    [35, theme.color.oliveInkDim, theme.color.gameVoltDim],
    [10, theme.color.vibeGrey, theme.color.gameGrey],
  ])('inks %i%% by its band on paper, and fills the bar by it', (pct, figure, fill) => {
    render(<SocialVibeCard grid={{ ...GRID, pct }} />);
    expect(textStyle(screen.getByText(`${pct}%`)).color).toBe(figure);
    expect(viewStyle(screen.getByTestId('social-vibe-card-fill', HIDDEN)).backgroundColor).toBe(
      fill,
    );
  });

  it('never inks or fills with the forecast’s green, amber or red', () => {
    const forecast: readonly string[] = [
      theme.color.gameGreen,
      theme.color.gameAmber,
      theme.color.gameRed,
      theme.color.mintInk,
      theme.color.amber,
      theme.color.red,
    ];
    for (const colour of [
      ...Object.values(SOCIAL_VIBE_CARD_FIGURE),
      ...Object.values(SOCIAL_VIBE_CARD_FILL),
    ]) {
      expect(forecast).not.toContain(colour);
    }
  });

  it('heads its columns with faces and names — You first, then as handed', () => {
    render(<SocialVibeCard grid={GRID} />);
    const names = screen
      .getAllByTestId('social-vibe-column', HIDDEN)
      .map((column) => within(column).getByText(/.+/, HIDDEN).props.children as string);
    expect(names).toEqual(['You', 'magda.p', 'filip.n', 'kuba.w']);
  });

  it('shortens a long nickname with an ellipsis, on one line', () => {
    const long = 'magdalena.pietrzak-wisniewska';
    render(
      <SocialVibeCard
        grid={{
          ...GRID,
          columns: [GRID.columns[0]!, { playerId: 'magda', isYou: false, name: long }],
          rows: [],
        }}
      />,
    );
    const name = screen.getByText(long, HIDDEN);
    expect(name.props.numberOfLines).toBe(1);
    expect(name.props.ellipsizeMode).toBe('tail');
  });

  /** The rows are spoken whole; the column heads add nothing a row's name doesn't say. */
  it('hides the column heads from a listener', () => {
    render(<SocialVibeCard grid={GRID} />);
    expect(screen.queryByText('kuba.w')).toBeNull();
    expect(screen.getByText('kuba.w', HIDDEN)).toBeTruthy();
  });

  it('draws each row with its emoji and label, in the order handed, spoken as tag: you, names', () => {
    render(<SocialVibeCard grid={GRID} />);

    expect(
      within(row('Stays for a drink: you, kuba.w')).getByText('🍻 Stays for a drink'),
    ).toBeTruthy();
    expect(
      within(row('Here to improve: you, filip.n')).getByText('📈 Here to improve'),
    ).toBeTruthy();
    expect(
      within(row('Here for a regular game: you')).getByText('🔁 Here for a regular game'),
    ).toBeTruthy();
    const order = screen
      .getAllByTestId('social-vibe-row')
      .map((one) => String(one.props.accessibilityLabel));
    expect(order).toEqual([
      'Stays for a drink: you, kuba.w',
      'Here to improve: you, filip.n',
      'Here for a regular game: you',
    ]);
  });

  it('puts a dot under every carrier, in their columns', () => {
    render(<SocialVibeCard grid={GRID} />);

    expect(dotsIn('Stays for a drink: you, kuba.w')).toHaveLength(2);
    expect(dotsIn('Here to improve: you, filip.n')).toHaveLength(2);
    expect(dotsIn('Here for a regular game: you')).toHaveLength(1);
    // Every row has one cell per column, a dot or nothing, so the dots stand under their faces.
    for (const one of screen.getAllByTestId('social-vibe-row')) {
      expect(within(one).getAllByTestId('social-vibe-cell', HIDDEN)).toHaveLength(4);
    }
  });

  it('bands a shared row pale volt, its words ink and its dots olive', () => {
    render(<SocialVibeCard grid={GRID} />);
    const shared = row('Stays for a drink: you, kuba.w');

    expect(viewStyle(shared).backgroundColor).toBe(theme.color.voltPale);
    expect(textStyle(within(shared).getByText('🍻 Stays for a drink')).color).toBe(theme.color.ink);
    for (const dot of dotsIn('Stays for a drink: you, kuba.w')) {
      expect(viewStyle(dot).backgroundColor).toBe(theme.color.oliveInk);
    }
  });

  it('leaves a row only you have unbanded, its words grey and its dot grey', () => {
    render(<SocialVibeCard grid={GRID} />);
    const yours = row('Here for a regular game: you');

    expect(viewStyle(yours).backgroundColor).toBeUndefined();
    expect(textStyle(within(yours).getByText('🔁 Here for a regular game')).color).toBe(
      theme.color.vibeGrey,
    );
    expect(viewStyle(dotsIn('Here for a regular game: you')[0]!).backgroundColor).toBe(
      theme.color.line,
    );
  });

  it('draws 💘 like any other row', () => {
    render(
      <SocialVibeCard
        grid={{
          ...GRID,
          rows: [{ tag: 'OPEN_TO_MEET_SOMEONE', dots: [true, true, false, false], shared: true }],
        }}
      />,
    );
    expect(
      within(row('Open to meet someone: you, magda.p')).getByText('💘 Open to meet someone'),
    ).toBeTruthy();
  });

  it('draws two columns for a singles table', () => {
    render(
      <SocialVibeCard
        grid={{
          pct: 50,
          columns: GRID.columns.slice(0, 2),
          rows: [{ tag: 'PLAYS_TO_WIN', dots: [true, true], shared: true }],
        }}
      />,
    );
    expect(screen.getAllByTestId('social-vibe-column', HIDDEN)).toHaveLength(2);
    expect(
      within(row('Plays to win: you, magda.p')).getAllByTestId('social-vibe-cell', HIDDEN),
    ).toHaveLength(2);
  });

  /** ADR-0207 §6: static — the grid has no taps of its own. */
  it('has nothing to press', () => {
    render(<SocialVibeCard grid={GRID} />);
    expect(screen.queryAllByRole('button', HIDDEN)).toHaveLength(0);
    expect(
      screen.UNSAFE_root.findAll(
        (node: { readonly props: Readonly<Record<string, unknown>> }) =>
          node.props.onPress !== undefined,
      ),
    ).toHaveLength(0);
  });
});
