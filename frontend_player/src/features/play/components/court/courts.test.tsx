/**
 * The two courts over one drawn object, and the seam between them.
 *
 * `Court.test.tsx` already holds the geometry — two children, two positions, per Sport. What
 * is asserted here is what the geometry cannot see: that the seat label truncates while the
 * sentence and the spoken name stay whole, that the swap truth table reaches the callbacks it
 * says it does, that the badge a player may not use is never drawn, and that the read-only
 * court draws faces and nothing else.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type TextStyle, type ViewStyle } from 'react-native';

import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';

import { seatPlaces } from '../../domain/lineup';

import { CourtBuild } from './CourtBuild';
import { CourtMini } from './CourtMini';
import { CourtSeat, type CourtSeatOccupant } from './CourtSeat';

/** 2 to 64 characters, and the seat is 46pt. The arithmetic §5 ran, as a fixture. */
const LONG_HANDLE = 'marekwiśniewski-plays-every-tuesday-and-most-saturdays-in-warsaw';

const YOU: CourtSeatOccupant = { kind: 'you', playerId: 'me' };
const PARTNER: CourtSeatOccupant = {
  kind: 'player',
  playerId: 'player-a',
  nickname: LONG_HANDLE,
  level: 2.92,
  accepted: false,
};
const OPPONENT: CourtSeatOccupant = {
  kind: 'player',
  playerId: 'player-b',
  nickname: 'ana',
  level: 3.1,
  accepted: false,
};
const ACCEPTED: CourtSeatOccupant = { ...OPPONENT, playerId: 'player-c', accepted: true };
const EMPTY: CourtSeatOccupant = { kind: 'empty', unfilled: null };

const SUMMARY = 'Padel, 3 of 4 seats filled.';

const flatten = (style: unknown) => StyleSheet.flatten(style as TextStyle);

function build(seats: readonly CourtSeatOccupant[], swapping = false) {
  const acts = { openPool: jest.fn(), swap: jest.fn(), clear: jest.fn() };

  const view = render(
    <CourtBuild
      sport="padel"
      width={196}
      summary={SUMMARY}
      seats={seats}
      swapping={swapping}
      onOpenPool={acts.openPool}
      onSwap={acts.swap}
      onClear={acts.clear}
    />,
  );

  return { ...acts, view };
}

beforeEach(() => {
  useToastQueue.getState().clear();
});

describe('the seat label', () => {
  it('truncates visually, on one line, to the seat it is under', () => {
    render(
      <CourtSeat
        size={46}
        place="YOUR_PARTNER"
        occupant={PARTNER}
        selected={false}
        onPress={noop}
      />,
    );

    // Hidden by design — the seat's spoken name already carries the whole handle — so the
    // query has to ask for it. That it is hidden is the assertion two lines down in the
    // accessibility suite.
    const label = screen.getByText(LONG_HANDLE, { includeHiddenElements: true });

    expect(label.props.numberOfLines).toBe(1);
    expect(label.props.ellipsizeMode).toBe('tail');
    expect(flatten(label.props.style)?.fontSize).toBe(theme.type.tag.fontSize);
    // Hidden on both platforms: the seat's own name already carries this word whole, and a
    // reader that walked into the drawn one would hear four characters of a handle.
    expect(label.props.accessibilityElementsHidden).toBe(true);
    expect(label.props.importantForAccessibility).toBe('no-hide-descendants');
  });

  it('scales with Dynamic Type, because §20.4 refused the escape the level bar has', () => {
    render(
      <CourtSeat
        size={46}
        place="YOUR_PARTNER"
        occupant={PARTNER}
        selected={false}
        onPress={noop}
      />,
    );

    const label = screen.getByText(LONG_HANDLE, { includeHiddenElements: true });

    expect(label.props.allowFontScaling).not.toBe(false);
  });

  it('leaves the whole handle in the sentence and in the spoken name', () => {
    // ADR-0107 bites on inventing a familiar form. A visual truncation invents nothing, and
    // the two places a name is a SENTENCE carry all sixty-four characters.
    render(
      <CourtSeat
        size={46}
        place="YOUR_PARTNER"
        occupant={PARTNER}
        selected={false}
        onPress={noop}
        onClear={noop}
      />,
    );

    expect(
      screen.getByLabelText(`Your side, your partner, ${LONG_HANDLE}, level 2,92`),
    ).toBeTruthy();
    expect(screen.getByLabelText(`Remove ${LONG_HANDLE} from your side`)).toBeTruthy();
  });

  it('does not restate the level, which the card and the sheet already draw', () => {
    render(
      <CourtSeat
        size={46}
        place="THEIR_SIDE"
        occupant={OPPONENT}
        selected={false}
        onPress={noop}
      />,
    );

    expect(screen.queryByText(/3,10/, { includeHiddenElements: true })).toBeNull();
  });
});

describe('a seat', () => {
  it('says it is selected rather than looking it, because React Native has no `pressed`', () => {
    render(<CourtSeat size={46} place="THEIR_SIDE" occupant={OPPONENT} selected onPress={noop} />);

    expect(screen.getByLabelText('Their side, ana, level 3,10').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: true }),
    );
  });

  it('draws no clear badge where the seat may not be emptied', () => {
    const { view } = build([YOU, PARTNER, ACCEPTED, EMPTY]);

    expect(view.queryByLabelText(`Remove ${LONG_HANDLE} from your side`)).toBeTruthy();
    expect(view.queryByLabelText('Remove ana from their side')).toBeNull();
  });
});

describe('a tap on a seat', () => {
  it('opens the pool against an empty seat', () => {
    const { openPool } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Their side, empty'));

    expect(openPool).toHaveBeenCalledWith(3);
  });

  it('offers a replacement for somebody you may replace', () => {
    const { openPool } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));

    expect(openPool).toHaveBeenCalledWith(2);
  });

  it('refuses your own seat with the toast that names the way out', () => {
    const { openPool } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Your side, you'));

    expect(openPool).not.toHaveBeenCalled();
    expect(useToastQueue.getState().queue[0]?.message).toBe(
      'That seat is yours — turn on Swap players to change sides',
    );
  });

  it('refuses somebody who already accepted, and names them', () => {
    const { openPool } = build([YOU, PARTNER, ACCEPTED, EMPTY]);

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));

    expect(openPool).not.toHaveBeenCalled();
    expect(useToastQueue.getState().queue[0]?.message).toBe(
      'ana already accepted — they keep their place',
    );
  });

  it('selects and then trades once the toggle is on', () => {
    const { swap } = build([YOU, PARTNER, OPPONENT, EMPTY], true);

    fireEvent.press(screen.getByLabelText('Your side, you'));
    expect(screen.getByLabelText('Your side, you').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: true }),
    );

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));

    expect(swap).toHaveBeenCalledWith(0, 2);
  });

  it('moves a locked seat across the net, which is what the toggle is for', () => {
    const { swap } = build([YOU, PARTNER, ACCEPTED, EMPTY], true);

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));
    fireEvent.press(screen.getByLabelText('Your side, you'));

    expect(swap).toHaveBeenCalledWith(2, 0);
    expect(useToastQueue.getState().queue).toHaveLength(0);
  });

  it('forgets a selection when the toggle goes off, so no ring outlives the mode', () => {
    const { view } = build([YOU, PARTNER, OPPONENT, EMPTY], true);

    fireEvent.press(screen.getByLabelText('Your side, you'));

    view.rerender(
      <CourtBuild
        sport="padel"
        width={196}
        summary={SUMMARY}
        seats={[YOU, PARTNER, OPPONENT, EMPTY]}
        swapping={false}
        onOpenPool={noop}
        onSwap={noop}
        onClear={noop}
      />,
    );

    expect(screen.getByLabelText('Your side, you').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: false }),
    );
  });
});

describe('the side a seat is on', () => {
  it('follows you across the net rather than staying with the index', () => {
    build([OPPONENT, PARTNER, YOU, ACCEPTED], false);

    expect(screen.getByLabelText('Your side, you')).toBeTruthy();
    expect(screen.getByLabelText(`Their side, ${LONG_HANDLE}, level 2,92`)).toBeTruthy();
    expect(seatPlaces([OPPONENT, PARTNER, YOU, ACCEPTED])[3]).toBe('YOUR_PARTNER');
  });
});

describe('the read-only court', () => {
  it('draws faces and no labels, because both its screens print the handles in full', () => {
    render(
      <CourtMini
        sport="squash"
        width={120}
        summary="Squash, 2 of 2 seats filled."
        seats={[
          { kind: 'you', playerId: 'me' },
          { kind: 'player', playerId: 'player-b' },
        ]}
      />,
    );

    expect(screen.queryByText('You', { includeHiddenElements: true })).toBeNull();
  });

  it('rings your own face in volt, which is the one fact four faces cannot state', () => {
    render(
      <CourtMini
        sport="padel"
        width={196}
        summary="Padel, 2 of 4 seats filled."
        seats={[
          { kind: 'you', playerId: 'me' },
          { kind: 'player', playerId: 'player-b' },
          { kind: 'empty' },
          { kind: 'empty' },
        ]}
      />,
    );

    const rings = ringColours();

    // Volt once, white once, and nothing at all for the two seats nobody is in: an unfilled
    // seat on a court nobody can press is an invitation with nothing to accept.
    expect(rings.filter((colour) => colour === theme.color.volt)).toHaveLength(1);
    expect(rings.filter((colour) => colour === theme.color.surface)).toHaveLength(1);
  });

  it('spends volt on you where the interactive court spends it on a selection', () => {
    // One meaning per surface. The read-only court has no selection to confuse it with, and
    // the interactive one marks nobody — which is what keeps 1.2's single accent honest.
    build([YOU, PARTNER, OPPONENT, EMPTY], true);

    expect(ringColours()).not.toContain(theme.color.volt);
  });

  it('announces one summary and no seats, because a face has no action to navigate by', () => {
    render(
      <CourtMini
        sport="squash"
        width={120}
        summary="Squash, 1 of 2 seats filled."
        seats={[{ kind: 'you', playerId: 'me' }, { kind: 'empty' }]}
      />,
    );

    expect(screen.getAllByLabelText(/Squash/)).toHaveLength(1);
    expect(screen.queryByLabelText(/side/)).toBeNull();
  });
});

describe('the clear badge', () => {
  it('grows its target inward, bounded by the seat rather than by the 44pt floor', () => {
    // React Native never delivers a touch past a parent's bounds and `Court` sizes each seat's
    // box to the face exactly, so an outward slop would be inert. Inward it takes the seat's
    // own area, and both cannot be 44 on a 46pt face — see `CourtSeat`'s own note.
    build([YOU, PARTNER, OPPONENT, EMPTY]);

    const badge = screen.getByLabelText(`Remove ${LONG_HANDLE} from your side`);
    const size = StyleSheet.flatten(badge.props.style as TextStyle)?.width as number;
    const slop = badge.props.hitSlop as { top: number };

    expect(size + slop.top * 2).toBeLessThanOrEqual(46 / 2 + 1);
    expect(size + slop.top * 2).toBeLessThan(theme.size.minTouch);
  });

  it('declares a pressed appearance, on itself and on the seat under it', () => {
    // 6.6: touch has no hover, so every pressable says what a press looks like.
    build([YOU, PARTNER, OPPONENT, EMPTY]);

    for (const label of [`Remove ${LONG_HANDLE} from your side`, 'Their side, ana, level 3,10']) {
      const style = screen.getByLabelText(label).props.style;

      expect(StyleSheet.flatten(style as TextStyle)?.opacity).toBeUndefined();
      expect(typeof style).not.toBe('function');
    }
  });
});

/** Every ring drawn on the court, by colour — the overlay views, which are the only bordered ones. */
function ringColours(): readonly string[] {
  return screen
    .UNSAFE_queryAllByType(View)
    .map((node) => StyleSheet.flatten(node.props.style as ViewStyle))
    .filter((style) => style?.borderColor !== undefined)
    .map((style) => String(style.borderColor));
}

function noop() {}
