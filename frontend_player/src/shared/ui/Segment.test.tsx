/**
 * The segmented control — the two things about it a screen cannot observe for itself.
 *
 * The words are the caller's and the routing is the caller's, so what is asserted here is the
 * **contract**: that the state is announced on every segment rather than only on the chosen
 * one, and that a press on the segment already selected is still reported. The second is not
 * a detail — Play's *Find a game* segment **re-enters the tab**, which is arriving rather
 * than doing nothing, and a control that swallowed that press would make the rule
 * unimplementable from outside.
 */

import { act, fireEvent, render, screen, userEvent } from '@testing-library/react-native';
import { StyleSheet, Text, type TextStyle, type ViewStyle } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { ReducedMotionProvider } from './overlay';
import { Segment } from './Segment';
import { theme } from './theme';

const OPTIONS = [
  { key: 'find', label: 'Find a game' },
  { key: 'match', label: 'Match me · 3' },
] as const;

function renderSegment(selected: 'find' | 'match', onSelect = jest.fn()) {
  render(<Segment options={OPTIONS} selected={selected} onSelect={onSelect} />);
  return onSelect;
}

const isSelected = (label: string) =>
  screen.getByLabelText(label).props.accessibilityState?.selected === true;

describe('what it announces', () => {
  it('states the selection on every segment, not only on the chosen one', () => {
    renderSegment('match');

    expect(isSelected('Match me · 3')).toBe(true);
    // Present and false, never absent: *not chosen* and *not a choice* are different facts.
    expect(screen.getByLabelText('Find a game').props.accessibilityState?.selected).toBe(false);
  });

  it('is a button carrying `selected`, and never a switch carrying `checked`', () => {
    renderSegment('find');

    const segment = screen.getByLabelText('Find a game');
    expect(segment.props.accessibilityRole).toBe('button');
    expect(segment.props.accessibilityState?.checked).toBeUndefined();
  });

  it('takes an accessible name of its own where the visible words are cryptic', () => {
    render(
      <Segment
        options={[
          { key: 'find', label: 'Find a game' },
          { key: 'match', label: 'Match me · 3', accessibilityLabel: 'Match me, 3 yeses waiting' },
        ]}
        selected="find"
        onSelect={() => undefined}
      />,
    );

    expect(screen.getByLabelText('Match me, 3 yeses waiting')).toBeTruthy();
  });
});

describe('what it reports', () => {
  it('reports a press on the segment that is already selected', async () => {
    const onSelect = renderSegment('find');

    await userEvent.press(screen.getByLabelText('Find a game'));

    expect(onSelect).toHaveBeenCalledWith('find');
  });

  it('reports the key rather than the label', async () => {
    const onSelect = renderSegment('find');

    await userEvent.press(screen.getByLabelText('Match me · 3'));

    expect(onSelect).toHaveBeenCalledWith('match');
  });
});

describe('the drawing', () => {
  /**
   * 6.3's inversion, and Part 13's *never colour alone* under it: the raised segment is a
   * **lightness** step on the surface and a matching one on the label, so the pairing that
   * carries the state is legible without hue — and `selected` states it besides.
   */
  it('raises the selected segment onto the surface and darkens its label', () => {
    renderSegment('match');

    expect(styleOf(screen.getByLabelText('Match me \u00b7 3'))).toMatchObject({
      backgroundColor: theme.color.surface,
    });
    expect(styleOf(screen.getByLabelText('Find a game')).backgroundColor).toBeUndefined();

    expect(labelStyle('Match me \u00b7 3')).toMatchObject({ color: theme.color.ink });
    expect(labelStyle('Find a game')).toMatchObject({ color: theme.color.muted });
  });

  /**
   * The tab's own view switch (play mocks 1, 3): the same step read from the dark side — `ink`
   * under a `surface` label — and a taller thumb, with `selected` still saying which.
   */
  it('raises the selected segment onto ink when it is the tab’s own switch', () => {
    render(<Segment options={OPTIONS} selected="find" onSelect={() => undefined} prominent />);

    expect(styleOf(screen.getByLabelText('Find a game'))).toMatchObject({
      backgroundColor: theme.color.ink,
      minHeight: theme.size.btn,
    });
    expect(labelStyle('Find a game')).toMatchObject({ color: theme.color.surface });
    expect(labelStyle('Match me · 3')).toMatchObject({ color: theme.color.muted });
    expect(isSelected('Find a game')).toBe(true);
  });

  it("reaches the touch minimum through 6.5's own slop", () => {
    renderSegment('find');

    expect(screen.getByLabelText('Find a game').props.hitSlop).toBe(theme.hit.seg);
  });
});

/**
 * **A door** (ADR-0201 §2) — a view that is not the player's yet, and whose press opens a way to
 * make it theirs. Dimmed, never disabled: the same box, the same reach, and every press reported.
 */
describe('a door', () => {
  const DOOR = [
    { key: 'competitive', label: 'Competitive · 7' },
    { key: 'forFun', label: 'For fun', door: true },
  ] as const;

  function renderDoor(onSelect = jest.fn()) {
    render(<Segment options={DOOR} selected="competitive" onSelect={onSelect} />);
    return onSelect;
  }

  it('dims its label, and only its label', () => {
    renderDoor();

    expect(labelStyle('For fun')).toMatchObject({
      color: theme.color.muted,
      opacity: theme.size.segDoorOpacity,
    });
    expect(labelStyle('Competitive · 7').opacity).toBeUndefined();
  });

  it('is the same size and as easy to press as the live segment', () => {
    renderDoor();

    const door = screen.getByLabelText('For fun');
    const live = screen.getByLabelText('Competitive · 7');
    expect(door.props.hitSlop).toBe(live.props.hitSlop);
    expect(styleOf(door)).toMatchObject({ flex: 1, minHeight: theme.size.seg });
  });

  it('is never announced as disabled, and its press is reported', async () => {
    const onSelect = renderDoor();

    const door = screen.getByLabelText('For fun');
    expect(door.props.accessibilityState).toEqual({ selected: false });

    await userEvent.press(door);

    expect(onSelect).toHaveBeenCalledWith('forFun');
  });
});

/**
 * **An option that owns a menu** (6.3 as amended 2026-11-24, #861; PRD #859) — a group page's
 * Friends tab. Selected, with its menu offered, it draws a chevron and says whether its menu is
 * open; it widens by the chevron's room, and the others share the rest. Every press is still
 * reported: the page decides that a press on the selected tab opens its menu.
 */
describe('an option that owns a menu', () => {
  type Tab = 'games' | 'fillIn' | 'friends';

  function tabs(menu: { offered: boolean; open: boolean }, friendsLabel?: string) {
    return [
      { key: 'games', label: 'Games' },
      { key: 'fillIn', label: 'Fill in' },
      {
        key: 'friends',
        label: 'Friends',
        ...(friendsLabel === undefined ? {} : { accessibilityLabel: friendsLabel }),
        menu,
      },
    ] as const;
  }

  function renderTabs(
    selected: Tab,
    menu = { offered: true, open: false },
    onSelect = jest.fn(),
    friendsLabel?: string,
  ) {
    render(<Segment options={tabs(menu, friendsLabel)} selected={selected} onSelect={onSelect} />);
    return onSelect;
  }

  const chevron = () =>
    screen.queryByTestId('segment-chevron-friends', { includeHiddenElements: true });
  const chevronTurn = () =>
    (
      getAnimatedStyle(chevron()!) as {
        readonly transform?: readonly { readonly rotate?: string }[];
      }
    ).transform?.[0]?.rotate;

  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  it('draws a chevron while it is selected and its menu is offered — a mark, never spoken', () => {
    renderTabs('friends', { offered: true, open: false }, jest.fn(), 'Friends, Competitive');

    expect(chevron()).toBeTruthy();
    expect(chevron()!.props.accessibilityElementsHidden).toBe(true);
    expect(chevronTurn()).toBe('0deg');
    const friends = screen.getByRole('button', { name: 'Friends, Competitive' });
    expect(friends.props.accessibilityState).toEqual({ selected: true, expanded: false });
  });

  it('turns the chevron over and says expanded while the menu is open', () => {
    renderTabs('friends', { offered: true, open: true });

    act(() => jest.advanceTimersByTime(theme.motion.tabMenu));
    expect(chevronTurn()).toBe('180deg');
    expect(screen.getByLabelText('Friends').props.accessibilityState).toEqual({
      selected: true,
      expanded: true,
    });
  });

  it('turns it over at once under reduced motion', () => {
    render(
      <ReducedMotionProvider value>
        <Segment
          options={tabs({ offered: true, open: true })}
          selected="friends"
          onSelect={() => undefined}
        />
      </ReducedMotionProvider>,
    );

    expect(chevronTurn()).toBe('180deg');
  });

  it('draws none, and says nothing of a menu, while another option is selected', () => {
    renderTabs('games');

    expect(chevron()).toBeNull();
    expect(screen.getByLabelText('Friends').props.accessibilityState).toEqual({ selected: false });
  });

  it('draws none while its menu is not offered, though it is selected', () => {
    renderTabs('friends', { offered: false, open: false });

    expect(chevron()).toBeNull();
    expect(screen.getByLabelText('Friends').props.accessibilityState).toEqual({ selected: true });
  });

  it('still reports a press on itself while selected — the caller opens its menu', () => {
    const onSelect = renderTabs('friends');

    fireEvent.press(screen.getByLabelText('Friends'));

    expect(onSelect).toHaveBeenCalledWith('friends');
  });

  /**
   * The selected option with its chevron takes the chevron's room beside the share every option
   * has: its basis is the room where the others' is nought, and the track shares the rest.
   */
  it('widens by the chevron’s room while it draws one, and the others share the rest', () => {
    const { gap, chevron: across, inset } = theme.size.segMenu;
    renderTabs('friends');

    expect(boxOf('friends')).toMatchObject({ flexGrow: 1, flexBasis: gap + across + inset });
    expect(boxOf('games')).toMatchObject({ flexGrow: 1, flexBasis: 0 });
    expect(boxOf('fillIn')).toMatchObject({ flexGrow: 1, flexBasis: 0 });
  });

  it('shares the track evenly while no option draws a chevron', () => {
    renderTabs('games');

    for (const key of ['games', 'fillIn', 'friends']) {
      expect(boxOf(key)).toMatchObject({ flexGrow: 1, flexBasis: 0 });
    }
  });

  /** The widths move as a layout transition on each option's box — never a width per frame. */
  it('moves the widths by a layout transition, and not under reduced motion', () => {
    renderTabs('friends');
    expect(screen.getByTestId('segment-friends').props.layout).toBeDefined();

    render(
      <ReducedMotionProvider value>
        <Segment
          options={tabs({ offered: true, open: false })}
          selected="friends"
          onSelect={() => undefined}
        />
      </ReducedMotionProvider>,
    );
    expect(screen.getAllByTestId('segment-friends').at(-1)!.props.layout).toBeUndefined();
  });

  it('raises the selected box onto the surface, as any segment', () => {
    renderTabs('friends');

    expect(boxOf('friends')).toMatchObject({ backgroundColor: theme.color.surface });
    expect(boxOf('games').backgroundColor).toBeUndefined();
    expect(labelStyle('Friends')).toMatchObject({ color: theme.color.ink });
  });

  it('reports where the selected option stands, for its menu to hang from', () => {
    const onFrame = jest.fn();
    render(
      <Segment
        options={[
          { key: 'games', label: 'Games' },
          { key: 'friends', label: 'Friends', menu: { offered: true, open: false, onFrame } },
        ]}
        selected="friends"
        onSelect={() => undefined}
      />,
    );

    const frame = { x: 90, y: 3, width: 110, height: 25 };
    fireEvent(screen.getByTestId('segment-friends'), 'layout', { nativeEvent: { layout: frame } });

    expect(onFrame).toHaveBeenLastCalledWith(frame);
  });
});

/** An option's box — the view that is laid out in the track and carries the raised surface. */
function boxOf(key: string): ViewStyle {
  return StyleSheet.flatten(screen.getByTestId(`segment-${key}`).props.style as ViewStyle);
}

/** The style a `Pressable`'s style function produces with nothing pressed. */
function styleOf(node: { readonly props: { readonly style?: unknown } }): ViewStyle {
  const style = node.props.style;
  const resolved = typeof style === 'function' ? style({ pressed: false }) : style;
  return StyleSheet.flatten(resolved as ViewStyle);
}

/** The one `Text` inside a segment, flattened. */
function labelStyle(label: string): TextStyle {
  const [text] = screen.getByLabelText(label).findAllByType(Text);
  return StyleSheet.flatten(text?.props.style as TextStyle);
}
