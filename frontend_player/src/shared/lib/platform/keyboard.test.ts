/**
 * **The device's keyboard port, over React Native's own `Keyboard`** (#882, ADR-0210 §9).
 *
 * The OS's show and hide arrive as the events React Native's `Keyboard` listens for, so a suite can
 * send them the way the native side does — through the device event emitter — and watch the port
 * answer as it would on a phone. The one thing worth proving here is the order: the port reads
 * whether the keyboard is up from React Native's own record, and that record must already say the
 * new state when the port's follower is told, or a shell would redraw with the old answer and stay
 * on it.
 */

import { DeviceEventEmitter } from 'react-native';

import { deviceKeyboard } from './keyboard';

/** What the native side sends as the keyboard settles on screen — its frame, roughly an A32's. */
const SHOWN = {
  duration: 250,
  easing: 'keyboard',
  endCoordinates: { screenX: 0, screenY: 520, width: 390, height: 324 },
};

const show = () => DeviceEventEmitter.emit('keyboardDidShow', SHOWN);
const hide = () => DeviceEventEmitter.emit('keyboardDidHide', null);

afterEach(() => {
  // Leave React Native's record where every suite expects it: no keyboard.
  hide();
});

describe('the device’s keyboard', () => {
  it('is down until the OS says it came up', () => {
    expect(deviceKeyboard.isUp()).toBe(false);
  });

  it('tells a follower of each show and hide, already saying the new state', () => {
    const told: boolean[] = [];
    const stop = deviceKeyboard.follow(() => told.push(deviceKeyboard.isUp()));

    show();
    hide();

    expect(told).toEqual([true, false]);
    stop();
  });

  /**
   * A floating or split keyboard (Gboard's, a tablet's) is drawn over the window and takes no room
   * at its foot, and Android reports it shown with no height: nothing shrinks for it, so there is no
   * bar riding up over a field, and the bar has no reason to go.
   */
  it('is not up for a keyboard that takes no room at the window’s foot', () => {
    DeviceEventEmitter.emit('keyboardDidShow', {
      ...SHOWN,
      endCoordinates: { ...SHOWN.endCoordinates, height: 0 },
    });

    expect(deviceKeyboard.isUp()).toBe(false);
  });

  it('tells nobody once followed no more', () => {
    const told: boolean[] = [];
    const stop = deviceKeyboard.follow(() => told.push(deviceKeyboard.isUp()));

    stop();
    show();

    expect(told).toEqual([]);
    expect(deviceKeyboard.isUp()).toBe(true);
  });
});
