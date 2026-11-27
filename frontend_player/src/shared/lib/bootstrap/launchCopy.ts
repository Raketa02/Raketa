/**
 * **What a launch that could not start says** — the startup failure screen's words, the one screen
 * the launch gate draws of its own. Copy is code: kept here, beside the gate, never inlined in it.
 *
 * It says *Rakieta*, as the splash's drawn wordmark and the launcher's name do: one spelling on
 * every frame (ADR-0211).
 */
export const LAUNCH_COPY = {
  failure: {
    eyebrow: 'Startup failed',
    title: 'Rakieta could not start',
    /** When what stopped the launch carried no message of its own. */
    unknownReason: 'The app could not start.',
  },
} as const;
