/**
 * The radius slider, drawn from a distance and the served bounds — **the control, without the
 * onboarding around it.**
 *
 * The radius step and the You tab's *How far to look* drive the same slider against the same
 * rules: the served minimum, maximum and step, the snapping, the figure and the plain-word
 * reading, the two accessibility actions (6.10). What differs is the chrome — the step's
 * *Continue*, the tab's *Save* — and where the number goes: the step writes every move into
 * the part's draft, the tab holds a draft of its own until the button
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). So the slider and its wiring are here once, and each screen says what a move does.
 *
 * Nothing here decides anything: the bounds, the snapping and the stepping are
 * `searchRadius`'s, the words are `radiusPresentation`'s, and the track and the thumb are the
 * design system's. Find a game drives the same slider through the same domain functions from
 * `play/`; it composes its own because its chrome is a search's, not a profile edit's.
 */

import { RadiusSlider } from '@/shared/ui';

import {
  radiusAtFraction,
  radiusFraction,
  steppedRadius,
  topOfScale,
  type SearchRadiusBounds,
} from '../domain/searchRadius';

import {
  RADIUS_LABEL,
  radiusFigure,
  radiusWords,
  spokenRadius,
  widestRadiusFigure,
} from './radiusPresentation';

export interface SearchRadiusControlProps {
  /** Whole kilometres, already inside the bounds. */
  readonly radius: number;
  readonly bounds: SearchRadiusBounds;
  /** The slider moved, or was stepped. The caller decides where the number goes. */
  readonly onChange: (radiusKm: number) => void;
}

export function SearchRadiusControl({ radius, bounds, onChange }: SearchRadiusControlProps) {
  return (
    <RadiusSlider
      value={radius}
      minimum={bounds.minimumKm}
      /* The top of the *scale*, which is the served maximum whenever the step divides the
         range and the last value on a step when it does not. What is announced has to be a
         radius the control can be driven to and the write would accept — announcing one
         neither is true of would be the screen describing a distance nobody can hold. */
      maximum={topOfScale(bounds)}
      fraction={radiusFraction(radius, bounds)}
      onSlideTo={(fraction) => onChange(radiusAtFraction(fraction, bounds))}
      onIncrement={() => onChange(steppedRadius(radius, bounds, 'increment'))}
      onDecrement={() => onChange(steppedRadius(radius, bounds, 'decrement'))}
      figure={radiusFigure(radius)}
      widestFigure={widestRadiusFigure(bounds)}
      words={radiusWords(radius)}
      accessibilityLabel={RADIUS_LABEL}
      accessibilityValueText={spokenRadius(radius)}
    />
  );
}
