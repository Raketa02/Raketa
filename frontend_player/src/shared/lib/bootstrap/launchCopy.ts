/**
 * **What a launch that could not start says** — the startup failure screen's words, the one screen
 * the launch gate draws of its own. Copy is code: kept here, beside the gate, never inlined in it.
 *
 * It says *Raketa*: the splash's drawn *Rakieta* is that picture's alone, and every string stays
 * Raketa (ADR-0209 §5).
 */
export const LAUNCH_COPY = {
  failure: {
    eyebrow: 'Startup failed',
    title: 'Raketa could not start',
    /** When what stopped the launch carried no message of its own. */
    unknownReason: 'The app could not start.',
  },
} as const;
