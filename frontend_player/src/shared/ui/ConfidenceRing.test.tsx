/**
 * The ceiling tick, which is the one thing this component draws conditionally.
 *
 * **Asserted against the drawing, which is the declared exception to "assert what the player
 * can observe".** A tick is a two-point line inside an SVG: it has no text, no role and no
 * accessible name of its own — the ring's name states the numbers instead, and that name is
 * the *caller's* copy. So a suite that only went through a screen could not tell a ring that
 * drew no tick from one that drew a tick at a number the screen happened not to mention, and
 * a default tick would slip through. Reaching for the primitive is what makes the absence
 * observable at all.
 *
 * Everything else about the ring — the scale it draws on, the value it reports — is asserted
 * where a player meets it, in `features/onboarding/components/resultScreen.test.tsx`.
 */

import { render, screen } from '@testing-library/react-native';
import { Line } from 'react-native-svg';

import { ConfidenceRing } from './ConfidenceRing';

const ticks = () => screen.UNSAFE_queryAllByType(Line);

describe('the ceiling tick', () => {
  it('is drawn where the caller says the ceiling sits', () => {
    render(
      <ConfidenceRing
        value={28}
        ceiling={30}
        label="Confidence"
        accessibilityLabel="Confidence 28%, out of the 30% a questionnaire can prove"
      />,
    );

    expect(ticks()).toHaveLength(1);
  });

  it('is not drawn at all when there is no ceiling to draw', () => {
    // A rating whose engine has been retired: what that engine could have proved is not
    // knowable, so there is no mark to make. A default tick would be the component
    // asserting a limit on the caller's behalf — and it would be wrong in the one case it
    // fired, since the whole reason the ceiling is served is that it moves between engine
    // versions.
    render(<ConfidenceRing value={28} label="Confidence" accessibilityLabel="Confidence 28%" />);

    expect(ticks()).toHaveLength(0);

    // The ring itself is unaffected: losing the ceiling is not losing the Confidence.
    const ring = screen.getByRole('progressbar', { name: 'Confidence 28%' });
    expect(ring.props.accessibilityValue).toEqual({ min: 0, max: 100, now: 28 });
    expect(screen.getByText('28%')).toBeTruthy();
  });

  it('is drawn for a ceiling of zero, which is a ceiling like any other', () => {
    // The one falsy value in range. A truthiness check here would silently drop it, and
    // "this engine can prove nothing" is a claim that has a mark.
    render(
      <ConfidenceRing
        value={0}
        ceiling={0}
        label="Confidence"
        accessibilityLabel="Confidence 0%, out of the 0% a questionnaire can prove"
      />,
    );

    expect(ticks()).toHaveLength(1);
  });
});
