/**
 * Returning to the app, as a screen can subscribe to it.
 *
 * `AppState` itself is not driven here — it is a native module with no JS implementation,
 * which is the same reason the two ports exist. What is driven is the thing this app
 * already treats as *the* answer to "are we at the front": the focus manager
 * `wireFocusManager` feeds from `AppState`. A test moves that, exactly as a player
 * returning to the app moves it.
 */

import { focusManager } from '@tanstack/react-query';
import { render, act } from '@testing-library/react-native';
import { Text } from 'react-native';

import { moveAppTo, stopWatchingAppState, watchAppState } from '@/test-support/appState';

import { useAppInBackground, useOnForeground } from './appState';

function Screen({ onForeground }: { readonly onForeground: () => void }) {
  useOnForeground(onForeground);
  return <Text>a screen that cares where the app is</Text>;
}

/** What the OS does when the player leaves and comes back. */
function leaveAndReturn() {
  act(() => focusManager.setFocused(false));
  act(() => focusManager.setFocused(true));
}

beforeEach(() => {
  focusManager.setFocused(true);
});

describe('coming back to the app', () => {
  it('runs nothing on the way in — a mount is not a return', () => {
    const run = jest.fn();

    render(<Screen onForeground={run} />);

    expect(run).not.toHaveBeenCalled();
  });

  it('runs once each time the app comes back to the front', () => {
    const run = jest.fn();
    render(<Screen onForeground={run} />);

    leaveAndReturn();
    expect(run).toHaveBeenCalledTimes(1);

    leaveAndReturn();
    expect(run).toHaveBeenCalledTimes(2);
  });

  it('runs nothing when the app goes away', () => {
    const run = jest.fn();
    render(<Screen onForeground={run} />);

    act(() => focusManager.setFocused(false));

    expect(run).not.toHaveBeenCalled();
  });

  /**
   * A screen that has been left cannot ask the device for anything — the subscription goes
   * with it. Otherwise every step walked past in the part would still be reading a fix on
   * every return to the app.
   */
  it('stops when the screen goes', () => {
    const run = jest.fn();
    const screen = render(<Screen onForeground={run} />);

    screen.unmount();
    leaveAndReturn();

    expect(run).not.toHaveBeenCalled();
  });

  /** The subscription outlives a render, so it has to call what the screen means *now*. */
  it('runs the callback the screen holds now, not the one it mounted with', () => {
    const first = jest.fn();
    const second = jest.fn();
    const screen = render(<Screen onForeground={first} />);

    screen.rerender(<Screen onForeground={second} />);
    leaveAndReturn();

    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });
});

/** Whether the app has gone to the background, followed — what a screen that keeps something running reads. */
function Away() {
  return <Text>{useAppInBackground() ? 'in the background' : 'in view'}</Text>;
}

describe('the app in the background', () => {
  beforeEach(() => watchAppState());
  afterEach(() => stopWatchingAppState());

  it('follows the app to the background and back', () => {
    const view = render(<Away />);
    expect(view.getByText('in view')).toBeTruthy();

    act(() => moveAppTo('background'));
    expect(view.getByText('in the background')).toBeTruthy();

    act(() => moveAppTo('active'));
    expect(view.getByText('in view')).toBeTruthy();
  });

  /** Face ID behind the keychain's autofill makes the app `inactive` on iOS; it is still in view. */
  it('does not count iOS’s inactive as the background', () => {
    const view = render(<Away />);

    act(() => moveAppTo('inactive'));

    expect(view.getByText('in view')).toBeTruthy();
  });

  it('stops listening when the screen goes', () => {
    const view = render(<Away />);

    view.unmount();

    expect(() => act(() => moveAppTo('background'))).not.toThrow();
  });
});
