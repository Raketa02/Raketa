/**
 * **The iOS stage under the launch's drawn splash** (ADR-0209 §2) — `ModalStage.tsx`, the file the
 * harness resolves, since it runs as iOS.
 *
 * The splash covers everything the root draws for the first seconds of a cold open, and swallows
 * every touch. Android's stage is a layer in that tree and is covered with it. **iOS's is a native
 * window**, presented over the whole app, splash and all — so a sheet the first screen opens at once
 * (a club's invitation, a held link) would slide up over the splash and take taps. It is held back
 * while the splash covers the tree, and presented as the splash goes.
 */

import { render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';

import { ModalStage } from './ModalStage';
import { SplashCoverProvider } from './overlay';

function stage({ covered, visible = true }: { covered: boolean; visible?: boolean }) {
  return (
    <SplashCoverProvider covered={covered}>
      <ModalStage visible={visible} onRequestClose={() => {}} animationType="slide" layer="sheet">
        <Text>The sheet</Text>
      </ModalStage>
    </SplashCoverProvider>
  );
}

describe('the iOS stage, under the launch’s splash', () => {
  it('is not presented while the splash covers the tree, and is as the splash goes', () => {
    const view = render(stage({ covered: true }));

    expect(screen.queryByText('The sheet')).toBeNull();

    view.rerender(stage({ covered: false }));

    expect(screen.getByText('The sheet')).toBeTruthy();
  });

  it('is presented as it always was where nothing covers it', () => {
    render(
      <ModalStage visible onRequestClose={() => {}} animationType="slide" layer="sheet">
        <Text>The sheet</Text>
      </ModalStage>,
    );

    expect(screen.getByText('The sheet')).toBeTruthy();
  });

  it('stays closed once the splash goes, when its overlay is closed', () => {
    const view = render(stage({ covered: true, visible: false }));

    view.rerender(stage({ covered: false, visible: false }));

    expect(screen.queryByText('The sheet')).toBeNull();
  });
});
