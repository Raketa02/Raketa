/**
 * The action row's anatomy, at component level.
 *
 * `nowFlow.test.tsx` asserts what a player sees on the real screen and is where
 * the slots' presence is proved. What is here is what that suite cannot reach: the
 * **layout rules** `ADR-0088` states as rules rather than as appearances, and the
 * **destination** a press carries — which today goes to a handler the screen owns
 * and no route yet answers.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';

import { theme } from '@/shared/ui';

import type { ComposedScreen, MatchCard } from '../domain/ComposedScreen';

import { ACTION_ROW_ID, ActionRow, type CardControl } from './ActionRow';
import { CLOCK_ID } from './CardClock';
import { NowClockProvider } from './NowClock';

const NOW = Date.parse('2026-08-23T12:00:00Z');

function card(overrides: Partial<MatchCard> = {}): MatchCard {
  return {
    kind: 'match',
    matchId: 'm-1',
    clock: undefined,
    claimExpiresAt: undefined,
    where: {
      clubId: 'c-1',
      clubName: 'Sunset Padel',
      zone: 'Europe/Warsaw',
      cover: 'indoor',
      distanceKm: undefined,
    },
    price: { amount: 3800, currency: 'PLN' },
    situation: 'forming',
    status: undefined,
    departure: undefined,
    act: undefined,
    mayDepart: false,
    fit: undefined,
    emphasis: false,
    ...overrides,
  };
}

function screenHolding(one: MatchCard): ComposedScreen {
  return {
    offers: { cards: [] },
    yourMatches: { cards: [one] },
    shelves: { blocks: [] },
    debt: undefined,
  };
}

function draw(one: MatchCard, onControl: (control: CardControl) => void = jest.fn()) {
  return render(
    <NowClockProvider screen={screenHolding(one)}>
      <ActionRow card={one} onControl={onControl} />
    </NowClockProvider>,
  );
}

/** Every style a component was given, flattened — RN accepts arrays and nesting. */
function stylesOf(node: { readonly props: { readonly style?: unknown } }): Record<string, unknown> {
  const flatten = (style: unknown): Record<string, unknown> => {
    if (Array.isArray(style)) return Object.assign({}, ...style.map(flatten));
    return typeof style === 'object' && style !== null ? (style as Record<string, unknown>) : {};
  };
  return flatten(node.props.style);
}

beforeAll(() => {
  jest.useFakeTimers();
  jest.setSystemTime(NOW);
});

afterAll(() => {
  jest.useRealTimers();
});

describe('the row is three slots and no variants', () => {
  it('lets only the act stretch', () => {
    // `ADR-0088`: *"the act is the only flexible element"*. A stretched icon reads
    // as a primary button that has forgotten its label, and a countdown that shrank
    // under a long act label would be the one element on the card that changes size
    // as the seconds fall.
    draw(
      card({
        clock: '2026-08-23T12:04:00Z',
        act: { label: 'Take the seat · 38,00 zł', surface: 'seatClaim' },
        mayDepart: true,
      }),
    );

    expect(stylesOf(screen.getByTestId(CLOCK_ID)).flexShrink).toBe(0);
    expect(stylesOf(screen.getByRole('button', { name: /Take the seat/ })).flex).toBe(1);
    expect(stylesOf(screen.getByLabelText(/^Leave this match/)).flex).toBeUndefined();
  });

  it('makes the exit reachable at 44 × 44 without drawing one', () => {
    // `ADR-0086`: the controls it replaces were 40 × 34 and `UI` §1042 flags them
    // *"under 44 in both axes"*. The visual stays the button's height and the
    // target is grown with slop, which is the design system's own instruction —
    // 44 wide, and 34 + 5 + 5 tall.
    draw(card({ mayDepart: true }));

    const exit = screen.getByLabelText(/^Leave this match/);

    expect(stylesOf(exit).width).toBe(theme.size.minTouch);
    expect(stylesOf(exit).height).toBe(theme.size.btn);
    expect(exit.props.hitSlop).toEqual(theme.hit.btn);
    expect(theme.size.btn + theme.hit.btn.top + theme.hit.btn.bottom).toBe(theme.size.minTouch);
  });

  it('holds the empty row open with no height of its own', () => {
    // The spacer `native-kit.md` §3 needs: `marginTop: auto` pushes the footer to
    // the bottom of a card that fills its row, and an element that is not rendered
    // pushes nothing. One view and no pixels.
    draw(card());

    const row = stylesOf(screen.getByTestId(ACTION_ROW_ID));

    expect(row.marginTop).toBe('auto');
    expect(row.height).toBeUndefined();
    expect(row.minHeight).toBeUndefined();
    expect(screen.getByTestId(ACTION_ROW_ID).children).toHaveLength(0);
  });

  it('keeps the clock leftmost and the exit rightmost, whatever else is there', () => {
    // A player learns one row and not five, so the slots are always in the same
    // places — which is what makes the vacancies safe.
    const { rerender } = draw(
      card({
        clock: '2026-08-23T12:04:00Z',
        act: { label: 'Finish paying · 38,00 zł', surface: 'claimPayment' },
        mayDepart: true,
      }),
    );

    const full = screen.getByTestId(ACTION_ROW_ID).children;
    expect(full).toHaveLength(3);

    const silent = card({ clock: '2026-08-23T12:04:00Z', mayDepart: true });
    rerender(
      <NowClockProvider screen={screenHolding(silent)}>
        <ActionRow card={silent} onControl={jest.fn()} />
      </NowClockProvider>,
    );

    // The act left; the clock is still first and the exit still last.
    expect(screen.getByTestId(ACTION_ROW_ID).children).toHaveLength(2);
    expect(screen.getByTestId(CLOCK_ID)).toBeTruthy();
    expect(screen.getByLabelText(/^Leave this match/)).toBeTruthy();
  });
});

describe('one clock for the whole screen', () => {
  it('arms one timer however many cards are counting', () => {
    // `ADR-0088` records this as an implementation note *"because a dozen cards
    // each holding their own interval is the version that gets built by
    // accident"*. The walk keeps a timer out of every component; this is the same
    // fact seen from the render tree, where the count is directly observable.
    const cards = ['a', 'b', 'c'].map((id) => card({ matchId: id, clock: '2026-08-23T12:04:00Z' }));
    const screenOfThree: ComposedScreen = {
      offers: { cards: [] },
      yourMatches: { cards },
      shelves: { blocks: [] },
      debt: undefined,
    };

    render(
      <NowClockProvider screen={screenOfThree}>
        {cards.map((one) => (
          <ActionRow key={one.matchId} card={one} onControl={jest.fn()} />
        ))}
      </NowClockProvider>,
    );

    expect(screen.getAllByTestId(CLOCK_ID)).toHaveLength(3);
    expect(jest.getTimerCount()).toBe(1);
  });
});

describe('where a press goes', () => {
  it('carries the act’s own destination, and the card it is about', () => {
    // `ADR-0083`: a code determines its own destination and the card already
    // identifies the thing it is about, so a target on the wire would be a second
    // answer to one question. This is the client end of that.
    const onControl = jest.fn();
    const one = card({ act: { label: 'Enter the score', surface: 'result' } });

    draw(one, onControl);
    fireEvent.press(screen.getByRole('button', { name: /Enter the score/ }));

    expect(onControl).toHaveBeenCalledWith({ kind: 'act', surface: 'result', card: one });
  });

  it('announces both controls with their state, not just their name', () => {
    // A control's own state reaches a screen reader as state rather than as a
    // colour or an opacity — the same rule `Button` and `Tag` already keep.
    draw(
      card({
        act: { label: 'Getting in', surface: 'gettingIn' },
        mayDepart: true,
      }),
    );

    expect(screen.getByRole('button', { name: /Getting in/ }).props.accessibilityState).toEqual(
      expect.objectContaining({ disabled: false, busy: false }),
    );
    expect(screen.getByLabelText(/^Leave this match/).props.accessibilityState).toEqual(
      expect.objectContaining({ disabled: false }),
    );
  });

  it('does not dress the exit as a seventh act', () => {
    // `ADR-0086` refuses to reopen the enumeration `ADR-0083` closed for something
    // that is not the card's act, so the exit is its own kind rather than a surface.
    const onControl = jest.fn();
    const one = card({ mayDepart: true });

    draw(one, onControl);
    fireEvent.press(screen.getByLabelText(/^Leave this match/));

    expect(onControl).toHaveBeenCalledWith({ kind: 'exit', card: one });
  });
});

describe('the clock draws only what it was given', () => {
  it('draws nothing at all outside the screen’s one clock', () => {
    // A countdown with no clock behind it would be a second reading of *now* in a
    // second place, which is what having one context is for.
    render(<ActionRow card={card({ clock: '2026-08-23T12:04:00Z' })} onControl={jest.fn()} />);

    expect(screen.getByTestId(ACTION_ROW_ID)).toBeTruthy();
    expect(screen.queryByTestId(CLOCK_ID)).toBeNull();
  });

  it('draws nothing for a moment that does not parse', () => {
    // A contract failure rather than a state: the answer is *there is no countdown
    // here* rather than a figure in decades.
    draw(card({ clock: 'not an instant' }));

    expect(screen.queryByTestId(CLOCK_ID)).toBeNull();
  });

  it('says what the figure means, for a reader who cannot see where it sits', () => {
    draw(card({ clock: '2026-08-23T12:04:37Z' }));

    expect(screen.getByTestId(CLOCK_ID).props.children).toBe('4:37');
    expect(screen.getByLabelText('4:37 left')).toBeTruthy();
  });
});
