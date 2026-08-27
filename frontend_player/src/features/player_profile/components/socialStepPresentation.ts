/**
 * What a social step calls itself.
 *
 * The eyebrow says the player is still setting up **and how far through they are**, which
 * part one deliberately cannot do — a questionnaire's length is decided one answer at a
 * time, so its eyebrow counts sports instead. This part is seven steps whatever anybody
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
    /**
     * **The question is about the search, not about the journey.** *How far will you travel*
     * asked a player to commit to a distance they would drive, which is not what the number
     * does: it is the edge of their search and the weighting on a proposal, and nobody is
     * ever held to it. A player who read the old title honestly would set it low.
     */
    title: 'How far should we look for players?',
    asks: 'How far out to look for other players.',
  },
  gender: {
    /**
     * **One title for two controls, because it is one decision.** The screen asks a player
     * about themselves and about who they want on the other side of the net, and those are
     * two questions only in the sense that *where* and *how far* were: the second is
     * unanswerable without the first having been put. Splitting them would be an eighth
     * step to carry a radio group.
     */
    title: 'Who do you want to play with?',
    asks: 'Your own answer, and who you are willing to be matched with.',
  },
  'opt-in': {
    title: 'May we suggest games?',
    asks: 'Whether the platform may put games in front of you.',
  },
};

export function stepCopy(step: SocialStep): StepCopy {
  return COPY[step];
}
