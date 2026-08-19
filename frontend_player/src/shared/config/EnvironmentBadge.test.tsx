/**
 * What the badge puts on the screen.
 *
 * The identity decision itself is asserted in `appIdentity.test.ts`, against the pure
 * function. What is left here is the part only a render can answer: that the word reaches
 * the screen at all outside production, that production draws **nothing** rather than an
 * invisible node, and that the overlay cannot eat a tap.
 *
 * `jest.config.js` sets `EXPO_PUBLIC_ENV=development` and `jest.setup.js` runs `loadEnv`,
 * so the no-prop form is the real wiring rather than a stand-in for it.
 */

import { render, screen } from '@testing-library/react-native';
import { View } from 'react-native';

import { EnvironmentBadge } from './EnvironmentBadge';
import { ENVIRONMENTS, type AppEnvironment } from './env';

const BADGED: readonly AppEnvironment[] = ['local', 'development', 'staging'];

describe('what the badge renders', () => {
  it.each(BADGED)('shows the environment in %s', (environment) => {
    render(<EnvironmentBadge environment={environment} />);

    expect(screen.getByText(environment.toUpperCase())).toBeTruthy();
  });

  it('renders nothing at all in production', () => {
    render(<EnvironmentBadge environment="production" />);

    expect(screen.queryByTestId('environment-badge')).toBeNull();
    // Not merely hidden: production has no overlay node in the tree of any screen.
    expect(screen.UNSAFE_queryAllByType(View)).toHaveLength(0);
  });

  it.each(ENVIRONMENTS)('is readable to a screen reader in %s, or absent', (environment) => {
    render(<EnvironmentBadge environment={environment} />);

    const labelled = screen.queryByLabelText(`Environment: ${environment}`);

    expect(labelled === null).toBe(environment === 'production');
  });
});

describe('the overlay', () => {
  it('never intercepts a touch', () => {
    render(<EnvironmentBadge environment="local" />);

    expect(screen.getByTestId('environment-badge').props.pointerEvents).toBe('none');
  });
});

/**
 * The default parameter is what keeps the composition root from reading config a render
 * too early — `_layout.tsx` writes `<EnvironmentBadge />` and the read happens inside the
 * component, behind the bootstrap gate.
 */
describe('with no environment given', () => {
  it('reads the validated config', () => {
    render(<EnvironmentBadge />);

    expect(screen.getByText('DEVELOPMENT')).toBeTruthy();
  });
});
