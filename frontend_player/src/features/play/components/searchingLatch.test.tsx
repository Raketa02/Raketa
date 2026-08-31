/**
 * The searching latch — what it draws, what it refuses to draw, and what it says out loud.
 *
 * Three of the four things this component has to get right are **absences**: no count before
 * the response exists, no control of any kind, and no announcement of the stage it is in. An
 * absence is what a snapshot is worst at, so each one is asserted by name.
 */

import { render, screen } from '@testing-library/react-native';
import { AccessibilityInfo, Modal } from 'react-native';

import { ReducedMotionProvider } from '@/shared/ui';

import { poolRankingStatus } from './searchingPresentation';
import { SearchingLatch } from './SearchingLatch';

let announced: jest.SpyInstance;

beforeEach(() => {
  announced = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
});

afterEach(() => announced.mockRestore());

const asking = poolRankingStatus({ playersInRange: undefined, sportName: 'Padel' });
const answered = poolRankingStatus({ playersInRange: 41, sportName: 'Padel' });

const spoken = () => announced.mock.calls.map(([message]) => message as string);

describe('while the response has not arrived', () => {
  it('says what is happening and counts nobody', () => {
    render(<SearchingLatch visible status={asking} />);

    expect(screen.getByText(asking.headline)).toBeTruthy();
    expect(screen.queryByText(/in range/)).toBeNull();
  });

  /**
   * §20.11: *"the searching region announces the result once and never a stage."* A stage is
   * the one thing the latch has before the answer lands, so it announces nothing at all.
   */
  it('announces no stage', () => {
    render(<SearchingLatch visible status={asking} />);

    expect(spoken()).toEqual([]);
  });
});

describe('once it has', () => {
  it('prints the count off the response', () => {
    render(<SearchingLatch visible status={answered} />);

    expect(screen.getByText('41 in range for Padel')).toBeTruthy();
  });

  it('announces the result, once', () => {
    const { rerender } = render(<SearchingLatch visible status={asking} />);

    rerender(<SearchingLatch visible status={answered} />);
    rerender(<SearchingLatch visible status={answered} />);

    expect(spoken()).toEqual(['41 in range for Padel']);
  });
});

describe('the transition', () => {
  const animation = () => screen.UNSAFE_getByType(Modal).props.animationType as string;

  it('fades in, as the sheet does', () => {
    render(
      <ReducedMotionProvider value={false}>
        <SearchingLatch visible status={asking} />
      </ReducedMotionProvider>,
    );

    expect(animation()).toBe('fade');
  });

  /**
   * The transition goes and the **hold does not**, which is the split `motion.hold` argues in
   * its own docstring: nothing moves during a hold, so there is no animation to spare anybody
   * and a flash is the last thing to give a player who asked for calm (`searchingWait`).
   */
  it('does not move at all when the OS asks for calm', () => {
    render(
      <ReducedMotionProvider value>
        <SearchingLatch visible status={asking} />
      </ReducedMotionProvider>,
    );

    expect(animation()).toBe('none');
  });
});

/**
 * *"There is no back button because it is not a destination."* The prototype's dead end was a
 * screen a player could be stranded on; binding the wait to the response dissolved it, and
 * what is left must not grow a control that promises an escape it cannot give.
 */
describe('what a latch is not', () => {
  it('draws nothing to press', () => {
    render(<SearchingLatch visible status={answered} />);

    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('draws nothing at all when it is down', () => {
    render(<SearchingLatch visible={false} status={answered} />);

    expect(screen.queryByText(answered.headline)).toBeNull();
  });
});
