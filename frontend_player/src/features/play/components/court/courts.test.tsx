/**
 * The two courts over one drawn object, and the seam between them.
 *
 * `Court.test.tsx` already holds the geometry — two children, two positions, per Sport. What
 * is asserted here is what the geometry cannot see: that the seat label truncates while the
 * sentence and the spoken name stay whole, that the swap truth table reaches the callbacks it
 * says it does, that the badge a player may not use is never drawn, that the deleted hold does
 * nothing at all, and that the read-only court draws faces and nothing else.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type TextStyle, type ViewStyle } from 'react-native';

import { useToastQueue } from '@/shared/store/toast.store';
import { courtSeatSize, theme } from '@/shared/ui';

import { seatPlaces } from '../../domain/lineup';

import { CourtBuild } from './CourtBuild';
import { CourtMini } from './CourtMini';
import { CourtSeat, type CourtSeatOccupant } from './CourtSeat';
import { seatCaptionName, SEAT_NAME_LETTERS } from './seatFace';

/** 2 to 64 characters, and the seat is 46pt. The arithmetic §5 ran, as a fixture. */
const LONG_HANDLE = 'marekwiśniewski-plays-every-tuesday-and-most-saturdays-in-warsaw';

const YOU: CourtSeatOccupant = { kind: 'you', playerId: 'me' };
const PARTNER: CourtSeatOccupant = {
  kind: 'player',
  playerId: 'player-a',
  name: LONG_HANDLE,
  level: 2.92,
  accepted: false,
};
const OPPONENT: CourtSeatOccupant = {
  kind: 'player',
  playerId: 'player-b',
  name: 'ana',
  level: 3.1,
  accepted: false,
};
const ACCEPTED: CourtSeatOccupant = { ...OPPONENT, playerId: 'player-c', accepted: true };
/** A seat the record can no longer describe: a player, and none of the card's fields. */
const WITHHELD: CourtSeatOccupant = { kind: 'player', playerId: 'player-d', accepted: false };
const EMPTY: CourtSeatOccupant = { kind: 'empty', unfilled: null };

const SUMMARY = 'Padel, 3 of 4 seats filled.';

const flatten = (style: unknown) => StyleSheet.flatten(style as TextStyle);

function build(seats: readonly CourtSeatOccupant[]) {
  const acts = { openPool: jest.fn(), swap: jest.fn(), clear: jest.fn() };

  const view = render(
    <CourtBuild
      sport="padel"
      width={196}
      summary={SUMMARY}
      seats={seats}
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

const CAPTION = seatCaptionName(LONG_HANDLE);

describe('the seat label', () => {
  it('draws three characters of the handle, on one line, and marks nothing for the rest', () => {
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
    const label = screen.getByText(CAPTION, { includeHiddenElements: true });

    expect(CAPTION).toHaveLength(SEAT_NAME_LETTERS);
    expect(label.props.numberOfLines).toBe(1);
    // Never `tail`. The cut is already made, so an ellipsis could only be an apology for a
    // word the player cannot go and read from here — a character of the four spent saying so.
    expect(label.props.ellipsizeMode).toBe('clip');
    expect(flatten(label.props.style)?.fontSize).toBe(theme.type.tag.fontSize);
    expect(screen.queryByText(LONG_HANDLE, { includeHiddenElements: true })).toBeNull();
    // Hidden: the seat's spoken name already carries this word whole and the figure beside it,
    // and a reader that walked into the drawn caption would hear three characters of a handle.
    // Asserted as **reachability** rather than as the attribute, because the hide moved onto
    // the caption box when the level joined the handle in it — where it is, is not the claim.
    expect(screen.queryByText(CAPTION)).toBeNull();
    expect(screen.queryByText('2,92')).toBeNull();
  });

  it('draws the name and the level on one line, in a box wider than the seat', () => {
    // The pair reads as one identifier — `Pau 3,23` — which is what a court is scanned by.
    // The row is inset past the face on both sides because the two together do not fit in 46pt,
    // and it is absolutely positioned, so the room it takes comes from nothing.
    render(
      <CourtSeat
        size={46}
        place="THEIR_SIDE"
        occupant={OPPONENT}
        selected={false}
        onPress={noop}
      />,
    );

    // The drawn word, then the composite `Text`, then the caption box itself.
    const caption = screen.getByText(seatCaptionName('ana'), { includeHiddenElements: true }).parent
      ?.parent;
    const box = flatten(caption?.props.style);

    expect(box?.flexDirection).toBe('row');
    expect(box?.left).toBeLessThan(0);
    expect(box?.left).toBe(box?.right);
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

    const label = screen.getByText(CAPTION, { includeHiddenElements: true });

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

  /**
   * **The level is drawn under the handle**, which reverses `the-play-components.md` §5.
   *
   * §5 took it off on §10's rule — a surface does not restate what it already renders — and the
   * card it was written against printed one percentage. The card now prints two **side
   * strengths**, which is what a half is worth and not what anybody on it is
   * ([#290](https://github.com/Raketa02/Raketa/issues/290)): looking at `3,15` against `3,15`
   * says nothing about which of the four is carrying it, and the seat is the only place that
   * question has an answer.
   *
   * Mono and tabular, because 1.4 is categorical and four of these are read down one court
   * against each other.
   */
  it('draws the level under the handle, mono and tabular', () => {
    render(
      <CourtSeat
        size={46}
        place="THEIR_SIDE"
        occupant={OPPONENT}
        selected={false}
        onPress={noop}
      />,
    );

    const level = screen.getByText('3,10', { includeHiddenElements: true });

    expect(flatten(level.props.style)?.fontFamily).toBe(theme.num.xs.fontFamily);
    expect(flatten(level.props.style)?.fontVariant).toEqual(['tabular-nums']);
  });

  /** Two seats have no figure to draw, and they are the two with no card behind them. */
  it('draws no level on an empty seat or on one the record no longer describes', () => {
    render(
      <CourtSeat
        size={46}
        place="THEIR_SIDE"
        occupant={WITHHELD}
        selected={false}
        onPress={noop}
      />,
    );

    expect(screen.queryByText(/,\d\d$/, { includeHiddenElements: true })).toBeNull();
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

  it('selects an occupied seat and then trades it — no mode, and no refusal', () => {
    const { swap, openPool } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Your side, you'));
    expect(screen.getByLabelText('Your side, you').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: true }),
    );

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));

    expect(swap).toHaveBeenCalledWith(0, 2);
    // The two rows the toggle's removal deleted: a tap on somebody no longer offers to replace
    // them, and neither locked seat has anything left to say no to.
    expect(openPool).not.toHaveBeenCalled();
    expect(useToastQueue.getState().queue).toHaveLength(0);
  });

  it('deselects the seat it is already holding, so a ring can always be cancelled', () => {
    const { swap } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Your side, you'));
    fireEvent.press(screen.getByLabelText('Your side, you'));

    expect(screen.getByLabelText('Your side, you').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: false }),
    );
    expect(swap).not.toHaveBeenCalled();
  });

  it('moves a locked seat across the net, which is what a swap is for', () => {
    const { swap } = build([YOU, PARTNER, ACCEPTED, EMPTY]);

    fireEvent.press(screen.getByLabelText('Their side, ana, level 3,10'));
    fireEvent.press(screen.getByLabelText('Your side, you'));

    expect(swap).toHaveBeenCalledWith(2, 0);
    expect(useToastQueue.getState().queue).toHaveLength(0);
  });

  it('opens the pool on a hole and drops the selection, rather than trading into it', () => {
    const { openPool, swap } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    fireEvent.press(screen.getByLabelText('Your side, you'));
    fireEvent.press(screen.getByLabelText('Their side, empty'));

    expect(openPool).toHaveBeenCalledWith(3);
    expect(swap).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Your side, you').props.accessibilityState).toEqual(
      expect.objectContaining({ selected: false }),
    );
  });
});

/**
 * **There is no hold on a seat.**
 *
 * [#285](https://github.com/Raketa02/Raketa/issues/285) put a shortcut to `SH.whyfit` on a long
 * press, beside the forecast card's names row. That row now draws each player as their own face
 * and handle — a 44pt control with a picture of the person on it — and a second way in that
 * nothing advertises, nothing announces and the accessibility API cannot perform was carrying
 * nobody the row was not.
 *
 * Asserted rather than assumed, because a deleted gesture leaves no symptom: a `longPress` on a
 * `Pressable` with no `onLongPress` is silently a no-op, so nothing else in this suite would go
 * red if the wiring came back.
 */
describe('a hold on a seat', () => {
  it('does nothing, on a seat with a Fit behind it or on any other', () => {
    const { openPool, swap, clear } = build([YOU, PARTNER, OPPONENT, EMPTY]);

    for (const seat of ['Their side, ana, level 3,10', 'Your side, you', 'Their side, empty']) {
      fireEvent(screen.getByLabelText(seat), 'longPress');
    }

    // Not merely unexplained: a hold must not fall through to the tap's own act either.
    expect(openPool).not.toHaveBeenCalled();
    expect(swap).not.toHaveBeenCalled();
    expect(clear).not.toHaveBeenCalled();
    expect(useToastQueue.getState().queue).toHaveLength(0);
  });
});

describe('the side a seat is on', () => {
  it('follows you across the net rather than staying with the index', () => {
    build([OPPONENT, PARTNER, YOU, ACCEPTED]);

    expect(screen.getByLabelText('Your side, you')).toBeTruthy();
    expect(screen.getByLabelText(`Their side, ${LONG_HANDLE}, level 2,92`)).toBeTruthy();
    expect(seatPlaces([OPPONENT, PARTNER, YOU, ACCEPTED])[3]).toBe('YOUR_PARTNER');
  });
});

/**
 * **The two widths a court is drawn at**, and the one arithmetic that ties them to the rules.
 *
 * Every argument in the specs about a seat is made about a **46pt** one — 7.12's *"sixty-four
 * characters of handle in a 46pt seat is about four"*, and the clear badge's recorded conflict
 * between a 44pt target and a 46pt face. Sized by the content width, as the builder was, that
 * seat is 81pt on a large phone and every one of those arguments is about a court nobody
 * draws.
 */
describe('the widths', () => {
  it('sizes the interactive court so its seat is the 46pt every rule is written against', () => {
    expect(courtSeatSize(theme.size.court.build)).toBe(46);
  });

  /** The thumbnail is under the width at which the share clears its floor, and says so. */
  it('draws the thumbnail at the floor face, which is what makes it a picture', () => {
    expect(courtSeatSize(theme.size.court.thumb)).toBe(theme.size.court.seatMin);
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
    build([YOU, PARTNER, OPPONENT, EMPTY]);

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
