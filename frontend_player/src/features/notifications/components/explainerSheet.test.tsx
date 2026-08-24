/**
 * The second occasion: the sheet a standby join raises, and the rule that
 * decides whether it is raised at all.
 *
 * **Asserted as a rendering and as a rule, never as a flow, and that is a fact
 * about the build rather than a shortcut.** No surface in v1 joins a standby
 * queue — the contract carries a `DELETE` for a queue place and nothing that
 * takes one — so there is no tap anywhere in this app that reaches the sheet.
 * The missing act is `Raketa02/Raketa#132`; what is here is everything the day
 * it lands will need.
 *
 * The hook is driven through a component rather than through `renderHook`,
 * because what it produces *is* a sheet: the two are one thing, and a test that
 * held them apart would be asserting a boolean rather than a screen.
 */

import { Pressable, Text } from 'react-native';
import { act, fireEvent, render, screen } from '@testing-library/react-native';

import { osMock, resetPhone, stubPhone } from '@/test-support/notifications';

import { useStandbyJoinExplainer } from '../hooks/useStandbyJoinExplainer';
import { useStandbyAskStore } from '../store/standbyAsk.store';

import { NotificationExplainerSheet } from './NotificationExplainerSheet';

beforeEach(() => {
  resetPhone();
  useStandbyAskStore.getState().reset();
});

/**
 * A screen that has just put somebody on a standby queue.
 *
 * This is the whole of what the act that raises the sheet has to do — call
 * `afterJoin` once the join has landed, and render the sheet at the boolean it
 * answers.
 */
function AfterAJoin() {
  const explainer = useStandbyJoinExplainer();

  return (
    <>
      <TapToJoin onJoin={() => void explainer.afterJoin()} />
      <NotificationExplainerSheet visible={explainer.visible} onDismiss={explainer.dismiss} />
    </>
  );
}

function TapToJoin({ onJoin }: { readonly onJoin: () => void }) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel="Join standby" onPress={onJoin}>
      <Text>Join standby</Text>
    </Pressable>
  );
}

/** Press the join and let the OS read behind it settle. */
async function join() {
  fireEvent.press(screen.getByLabelText('Join standby'));
  await act(async () => {});
}

describe('the sheet a standby join raises', () => {
  it('is not on screen before a join', () => {
    render(<AfterAJoin />);

    expect(screen.queryByText('When a seat opens up')).toBeNull();
  });

  it('carries the same explanation and the same two controls as the screen', async () => {
    render(<AfterAJoin />);
    await join();

    expect(screen.getByText('When a seat opens up')).toBeTruthy();
    expect(screen.getByText('Matches lose players at short notice')).toBeTruthy();
    expect(screen.getByText('Saying no costs you nothing here')).toBeTruthy();
    expect(screen.getByLabelText('Turn on')).toBeTruthy();
    expect(screen.getByLabelText('Not now')).toBeTruthy();
  });

  /** Dismissal is *Not now*, so it must spend nothing either. */
  it('asks the phone nothing when it is dismissed', async () => {
    render(<AfterAJoin />);
    await join();

    fireEvent.press(screen.getByLabelText('Not now'));

    expect(screen.queryByText('When a seat opens up')).toBeNull();
    expect(osMock().requestPermissionsAsync).not.toHaveBeenCalled();
  });

  it('fires the OS prompt from its Turn on, exactly as the screen does', async () => {
    stubPhone({ answersPrompt: 'granted', token: undefined });
    render(<AfterAJoin />);
    await join();

    fireEvent.press(screen.getByLabelText('Turn on'));
    await act(async () => {});

    expect(osMock().requestPermissionsAsync).toHaveBeenCalledTimes(1);
  });
});

describe('the first join, and not every join', () => {
  it('does not come back at the second join of a session', async () => {
    render(<AfterAJoin />);
    await join();

    fireEvent.press(screen.getByLabelText('Not now'));
    await join();

    expect(screen.queryByText('When a seat opens up')).toBeNull();
  });

  /**
   * The durable half of the answer is the OS's: a player who said yes never
   * meets this again on any launch, because the prompt is spent.
   */
  it('never appears for a player who already said yes', async () => {
    stubPhone({ granted: true, canAskAgain: false });
    render(<AfterAJoin />);
    await join();

    expect(screen.queryByText('When a seat opens up')).toBeNull();
  });

  it('never appears once the dialog has been spent', async () => {
    stubPhone({ granted: false, canAskAgain: false });
    render(<AfterAJoin />);
    await join();

    expect(screen.queryByText('When a seat opens up')).toBeNull();
  });
});
