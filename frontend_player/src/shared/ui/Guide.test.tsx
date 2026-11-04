/**
 * **The guide on its own** (design-system 9.4) — what a screen-level suite cannot reach: the
 * device's back button counting as *Skip*, which only Android has, so the stage is Android's here
 * (imported by file, as `ModalStage.test.tsx` does, because the harness runs as iOS), and a guide
 * shown a second time starting from its first step.
 *
 * The walk itself — the count, *Next*, a tap on the dim, *Got it*, *Skip*, and nothing beneath
 * answering — is walked on *Your rating*, through the route tree, in the onboarding suite.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { useRef, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';

import { Guide } from './Guide';
import { OverlayHost, ReducedMotionProvider } from './overlay';

jest.mock('./ModalStage', () => jest.requireActual('./ModalStage.android'));

/** The dim is hidden from a listener — the bubble's controls carry the names — so a walk looks for it. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

beforeEach(() => {
  watchHardwareBack();
});

afterEach(() => {
  stopWatchingHardwareBack();
});

function App({ onDone }: { readonly onDone: () => void }) {
  const [open, setOpen] = useState(true);
  const first = useRef<View | null>(null);
  const second = useRef<View | null>(null);
  // Reduced motion, so the stage is simply there rather than fading in on a timer.
  return (
    <ReducedMotionProvider value>
      <OverlayHost>
        <View ref={first}>
          <Text>Two</Text>
        </View>
        <View ref={second}>
          <Text>Things</Text>
        </View>
        <Pressable accessibilityLabel="Show it again" onPress={() => setOpen(true)} />
        <Guide
          visible={open}
          steps={[
            { target: first, title: 'The first', body: 'What the first thing is.' },
            { target: second, title: 'The second', body: 'What the second thing is.' },
          ]}
          onDone={() => {
            setOpen(false);
            onDone();
          }}
        />
      </OverlayHost>
    </ReducedMotionProvider>
  );
}

describe('the guide', () => {
  it('counts its steps, and a tap on the dim is Next', () => {
    const onDone = jest.fn();
    render(<App onDone={onDone} />);

    expect(screen.getByText('The first')).toBeTruthy();
    expect(screen.getByText('1 of 2')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Next' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Skip the guide' })).toBeTruthy();

    fireEvent.press(screen.getByTestId('guide-dim', HIDDEN_TOO));

    expect(screen.getByText('The second')).toBeTruthy();
    expect(screen.getByText('2 of 2')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Next' })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Got it' }));

    expect(onDone).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('The second')).toBeNull();
  });

  it('takes the device’s back button as Skip, and swallows it', () => {
    const onDone = jest.fn();
    render(<App onDone={onDone} />);

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);

    expect(onDone).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('The first')).toBeNull();
  });

  it('starts from its first step when it is shown again', () => {
    render(<App onDone={() => {}} />);
    fireEvent.press(screen.getByRole('button', { name: 'Next' }));
    fireEvent.press(screen.getByRole('button', { name: 'Skip the guide' }));

    fireEvent.press(screen.getByLabelText('Show it again'));

    expect(screen.getByText('The first')).toBeTruthy();
    expect(screen.getByText('1 of 2')).toBeTruthy();
  });
});
