/**
 * What a social step calls itself.
 *
 * The eyebrow says the player is still setting up **and how far through they are**, which
 * part one deliberately cannot do — a questionnaire's length is decided one answer at a
 * time, so its eyebrow counts sports instead. This part is six steps whatever anybody
 * answers, so the count is honest and the player can see the end.
 *
 * `asks` is one sentence about the single decision that step is for. It stays one sentence
 * on purpose: each screen asks for one thing (story 13), and a step that needed two
 * sentences to say what it wants would be two steps.
 */

import { stepPosition, type SocialStep } from '../domain/socialSteps';

export function stepEyebrow(step: SocialStep): string {
  const { index, total } = stepPosition(step);
  return `Setting up · Step ${index} of ${total}`;
}

export interface StepCopy {
  readonly title: string;
  /** The one decision this step asks for. */
  readonly asks: string;
}

const COPY: Readonly<Record<SocialStep, StepCopy>> = {
  tags: {
    title: 'What kind of player are you?',
    asks: 'The tags another player would recognise you by, from a fixed list.',
  },
  photos: {
    title: 'Your court photos',
    asks: 'Up to three photos of you on a court, or none at all.',
  },
  availability: {
    title: 'When do you usually play?',
    asks: 'Your ordinary week, as days and parts of the day.',
  },
  location: {
    title: 'Where do you play?',
    asks: 'The area you play in, read once from your device and rounded.',
  },
  radius: {
    title: 'How far will you travel?',
    asks: 'How far out to look for other players.',
  },
  'opt-in': {
    title: 'May we suggest games?',
    asks: 'Whether the platform may put games in front of you.',
  },
};

export function stepCopy(step: SocialStep): StepCopy {
  return COPY[step];
}
