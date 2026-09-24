/**
 * What `nodePrinting.ts` buys, pinned (#493): a node a failing matcher prints is its element, not
 * its fiber.
 *
 * **The message is asserted, not a duration.** What the message holds is what the walk cost, and
 * a bound on milliseconds would be one more test that races the machine it runs on.
 */

import { Text, View } from 'react-native';
import { render, screen } from '@testing-library/react-native';

/** The message a failed matcher throws. */
function failureOf(assertion: () => void): string {
  try {
    assertion();
  } catch (error) {
    return (error as Error).message;
  }
  throw new Error('The assertion passed, so there is no message to read.');
}

/** A component of the app's own, rather than a host view. */
function Row({ label }: { readonly label: string }) {
  return <Text>{label}</Text>;
}

describe('a node a matcher prints', () => {
  it('is its type and its props — never its fiber, and never what is inside it', () => {
    render(
      <View accessibilityLabel="the row">
        <Text>deep inside</Text>
      </View>,
    );

    const message = failureOf(() => expect(screen.getByLabelText('the row')).toBeNull());

    expect(message).toContain('<View accessibilityLabel="the row" />');
    expect(message).not.toContain('_fiber');
    expect(message).not.toContain('deep inside');
  });

  it('names a component by its own name', () => {
    render(<Row label="tomek.p" />);

    const message = failureOf(() => expect(screen.UNSAFE_getByType(Row)).toBeNull());

    expect(message).toContain('<Row label="tomek.p" />');
    expect(message).not.toContain('_fiber');
  });
});
