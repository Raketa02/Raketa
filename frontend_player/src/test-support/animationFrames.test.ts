/**
 * What `animationFrames.ts` buys, pinned (#787): on the suite's clock a frame comes a screen's 16 ms
 * after the last, so a move is drawn as often as a phone would draw it — the case is red with the
 * module's install taken out of `jest.setup.js`, where reanimated's mock drew one every millisecond.
 */

import { Animated } from 'react-native';

import { FRAME_MS } from './animationFrames';

/** Ten frames on a screen, and 160 on a nought-delay timer. */
const MOVE_MS = 160;

describe('animation frames on the fake clock', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  it('draws the next frame one screen frame on, and not before', () => {
    const drawn: number[] = [];
    requestAnimationFrame((at) => drawn.push(at));

    jest.advanceTimersByTime(FRAME_MS - 1);
    expect(drawn).toHaveLength(0);

    jest.advanceTimersByTime(1);
    expect(drawn).toHaveLength(1);
  });

  it('draws a JavaScript-driven move as often as a screen would, and lands it', () => {
    const value = new Animated.Value(0);
    const frames: number[] = [];
    value.addListener(({ value: at }) => frames.push(at));

    Animated.timing(value, { toValue: 1, duration: MOVE_MS, useNativeDriver: false }).start();
    jest.advanceTimersByTime(MOVE_MS + 2 * FRAME_MS);

    expect(frames.at(-1)).toBe(1);
    expect(frames.length).toBeLessThanOrEqual(MOVE_MS / FRAME_MS + 2);
  });
});
