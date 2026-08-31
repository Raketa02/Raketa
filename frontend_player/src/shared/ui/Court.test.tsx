/**
 * The interface that made children the shape rather than a callback or a hook, tested through
 * itself: hand it two children, assert two positions, per Sport.
 *
 * **H-25 is what this file exists for.** Squash has no net — both players stand on the same
 * half — so the far side is not the near side reflected, and a court that derived one from
 * the other would draw three sports correctly and one wrongly with nothing to see. The seat
 * count and the coordinates are the two facts a screen cannot observe: a seat has whatever
 * name its child gives it, and where it sits is a style.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';
import { LinearGradient, Stop } from 'react-native-svg';

import { Court, courtSeatCount, courtSeatSize } from './Court';
import { theme, type SportKey } from './theme';

const SPORTS = ['padel', 'badminton', 'tennis', 'squash'] as const satisfies readonly SportKey[];

const WIDTH = 200;

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

function Seat({ name }: { readonly name: string }) {
  return <Text>{name}</Text>;
}

/**
 * Where each child was put, in seat order — the absolutely positioned **boxes**, which are the
 * only ones with a width of their own. The summary strip is positioned too and is not one.
 */
function seatBoxes() {
  return screen
    .UNSAFE_queryAllByType(View)
    .map((node) => flatten(node.props.style))
    .filter((style) => style?.position === 'absolute' && typeof style.width === 'number')
    .map((style) => ({ left: style.left, top: style.top }));
}

function renderCourt(sport: SportKey, seats: number) {
  render(
    <Court sport={sport} width={WIDTH} summary={`${sport}, 0 of ${seats} seats filled.`}>
      {Array.from({ length: seats }, (_, index) => (
        <Seat key={index} name={`seat ${index}`} />
      ))}
    </Court>,
  );
}

describe('the seat count', () => {
  it('is the Sport, and it is read off the coordinates rather than restated', () => {
    expect(SPORTS.map(courtSeatCount)).toEqual([4, 4, 2, 2]);
  });
});

describe('the positions', () => {
  it.each(SPORTS)('places every child of a %s court and no more', (sport) => {
    renderCourt(sport, courtSeatCount(sport));

    expect(seatBoxes()).toHaveLength(courtSeatCount(sport));
  });

  it('never leave the module — a child is given a box, not a coordinate', () => {
    renderCourt('tennis', 2);

    // Two children, two positions, and they are different ones.
    const [near, far] = seatBoxes();
    expect(near).not.toEqual(far);
  });

  /**
   * The whole of H-25 in one assertion. Three Sports have a net and put a seat on each side of
   * it; squash has neither a net nor two sides, so **nothing of it is on the far half** — and
   * a component that derived the far side by reflecting the near one would draw three courts
   * right and the fourth wrong, with nothing on screen to say so.
   */
  it('put a seat on each side of the net, in the three Sports that have one', () => {
    const middle = theme.size.court.space.height / 2;
    const halves = (sport: SportKey) => {
      const ys = theme.size.court.seats[sport].map(([, y]) => y);
      return { near: ys.some((y) => y > middle), far: ys.some((y) => y < middle) };
    };

    expect(halves('padel')).toEqual({ near: true, far: true });
    expect(halves('badminton')).toEqual({ near: true, far: true });
    expect(halves('tennis')).toEqual({ near: true, far: true });
    expect(halves('squash')).toEqual({ near: true, far: false });
  });

  it('scale with the box the caller gives, because the court has one width and no height', () => {
    renderCourt('tennis', 2);
    const wide = seatBoxes();
    screen.unmount();

    render(
      <Court sport="tennis" width={WIDTH / 2} summary="Tennis, 0 of 2 seats filled.">
        <Seat name="seat 0" />
        <Seat name="seat 1" />
      </Court>,
    );

    expect(seatBoxes()[0]?.left).not.toBe(wide[0]?.left);
  });
});

describe('the seat face', () => {
  it('is a share of the court, with a floor below which a face is a dot', () => {
    expect(courtSeatSize(WIDTH)).toBe(Math.round(WIDTH * theme.size.court.seatRatio));
    expect(courtSeatSize(10)).toBe(theme.size.court.seatMin);
  });
});

describe('the ground', () => {
  it('is the Sport hue under one pinned scrim pass, which is what bounds 2.5 to four rows', () => {
    renderCourt('padel', 4);

    const stops = screen.UNSAFE_queryAllByType(Stop).map((node) => node.props.stopColor as string);
    expect(stops).toContain(theme.sport.padel);
    expect(stops).toContain(theme.color.night);
    expect(screen.UNSAFE_queryAllByType(View).map((node) => flatten(node.props.style))).toEqual(
      expect.arrayContaining([expect.objectContaining({ borderRadius: theme.radius.court })]),
    );
  });

  it('has a per-instance gradient id, so one screen drawing two padel courts is not one', () => {
    render(
      <>
        <Court sport="padel" width={WIDTH} summary="Padel, 0 of 4 seats filled." />
        <Court sport="padel" width={WIDTH} summary="Padel, 0 of 4 seats filled." />
      </>,
    );

    const ids = screen.UNSAFE_queryAllByType(LinearGradient).map((node) => node.props.id as string);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('what it announces', () => {
  /**
   * `the-words.md` §20.4: four seats announced against nothing are four seats a listener
   * cannot place. The summary is an element of its own rather than the court's label,
   * because a container carrying one would swallow the seats.
   */
  it('is a summary that comes before the seats, and never the seats themselves', () => {
    renderCourt('padel', 4);

    expect(screen.getByLabelText('padel, 0 of 4 seats filled.')).toBeTruthy();
    expect(screen.getByText('seat 0')).toBeTruthy();
  });

  it('hides the caption and the side labels, which every seat already says', () => {
    render(
      <Court
        sport="padel"
        width={WIDTH}
        summary="Padel, 0 of 4 seats filled."
        caption="Padel"
        sideLabels={['your side', 'their side']}
      />,
    );

    for (const word of ['Padel', 'your side', 'their side']) {
      // Drawn, and unreachable: the summary names the Sport and each seat names its own
      // side, so a reader that found these would hear both facts twice.
      expect(screen.queryByText(word)).toBeNull();
      expect(screen.queryByText(word, { includeHiddenElements: true })).toBeTruthy();
    }
  });
});
