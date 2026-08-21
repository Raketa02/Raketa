/** THROWAWAY PROTOTYPE — issue #24. Not production. */

import type { Fixture, Leg } from './data';

/** The four things #24 asks to be drawn, with `asked`/`waiting` as one screen twice. */
export type Screen = 'enter' | 'asked' | 'waiting' | 'counter' | 'unscored';

export interface VariantProps {
  readonly fixture: Fixture;
  readonly screen: Screen;
  readonly draft: readonly Leg[];
  readonly setDraft: (next: readonly Leg[]) => void;
}
